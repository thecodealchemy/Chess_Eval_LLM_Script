import os
import asyncio
import json
import chess
import chess.pgn
import requests
from pathlib import Path
import threading

from dotenv import load_dotenv
load_dotenv()

# ==== CONFIG ====
PGN_FILE = r"myGame.pgn"
SKIP_BOOK_MOVES = 6          # skip LLM/engine commentary for the first N moves
SEARCH_DEPTH = 15            # Lichess cloud eval target depth (best-effort)
WAIT_FOR_ENTER = True        # pause after every printed move
SHOW_ASCII_BOARD = False     # print the board in ASCII after each move

# APIs
LICHESS_API = "https://lichess.org/api/cloud-eval"
LLM_API = "https://api.groq.com/openai/v1/chat/completions"  # Groq OpenAI-compatible
LLM_MODEL = "llama3-70b-8192"
LLM_KEY = os.getenv("GROQ_API_KEY") # set in .env or environment
# =================

# Cache settings
ENABLE_EVAL_CACHE = True
# simple thread-safe in-memory cache: cache_key -> result_dict (no TTL / persistent for process lifetime)
EVAL_CACHE = {}
CACHE_LOCK = threading.Lock()


def format_eval(eval_json, board: chess.Board) -> str:
    """
    Convert Lichess Cloud eval JSON into a display string like '+0.34' or '#3'.
    Score is White's POV; invert if it's Black to move for readability.
    """
    try:
        pvs = eval_json.get("pvs", [])
        if not pvs:
            return "N/A"
        pv = pvs[0]
        if "mate" in pv and pv["mate"] is not None:
            # Sign indicates side delivering mate from White POV.
            mate = pv["mate"]
            if not board.turn:  # black to move -> invert for display as side-to-move POV
                mate = -mate
            sign = "" if mate < 0 else "+"
            return f"#{sign}{abs(mate)}"
        if "cp" in pv and pv["cp"] is not None:
            cp = pv["cp"]
            # cp is always from White POV per API docs.
            if not board.turn:  # Black to move -> invert for side-to-move POV
                cp = -cp
            return f"{cp/100:+.2f}"
    except Exception:
        pass
    return "N/A"


async def analyse_with_lichess(board: chess.Board) -> str:
    """Query Lichess Cloud Eval API safely with params (handles URL encoding).
    This kept for backward compatibility (returns top eval string only)."""
    fen = board.fen()
    try:
        r = await asyncio.to_thread(
            requests.get,
            LICHESS_API,
            params={"fen": fen, "multiPv": 1, "depth": SEARCH_DEPTH},
            timeout=15,
        )
        if r.status_code != 200:
            return f"N/A (HTTP {r.status_code})"
        return format_eval(r.json(), board)
    except requests.RequestException as e:
        return f"N/A ({e.__class__.__name__})"
    except json.JSONDecodeError:
        return "N/A (bad JSON)"


# New helper: fetch raw lichess JSON with multiPv (used to show variations)
async def fetch_lichess_eval_json(board: chess.Board, multi_pv: int = 3):
    fen = board.fen()
    cache_key = f"{fen}|pv={multi_pv}|d={SEARCH_DEPTH}"

    if ENABLE_EVAL_CACHE:
        with CACHE_LOCK:
            cached = EVAL_CACHE.get(cache_key)
            if cached is not None:
                return cached

    try:
        r = await asyncio.to_thread(
            requests.get,
            LICHESS_API,
            params={"fen": fen, "multiPv": multi_pv, "depth": SEARCH_DEPTH},
            timeout=15,
        )
        if r.status_code != 200:
            result = {"error": f"HTTP {r.status_code}"}
        else:
            try:
                result = {"json": r.json()}
            except json.JSONDecodeError:
                result = {"error": "bad JSON"}
    except requests.RequestException as e:
        result = {"error": e.__class__.__name__}

    if ENABLE_EVAL_CACHE and "error" not in result:
        with CACHE_LOCK:
            EVAL_CACHE[cache_key] = result

    return result


def _extract_pvs(eval_json):
    """Return first 3 PV dicts (as-is) from lichess eval json."""
    pvs = eval_json.get("pvs", [])
    return pvs[:3]


def _uci_list_from_pv(pv):
    """Try to extract a list of UCI moves from a PV entry robustly."""
    # Lichess cloud-eval may return moves as a space-separated string in 'moves' or 'pv',
    # or as a list of dicts. Handle common formats.
    moves = []
    if not pv:
        return moves
    if "moves" in pv:
        mv = pv["moves"]
        if isinstance(mv, str):
            moves = [m for m in mv.split() if m]
        elif isinstance(mv, list):
            for item in mv:
                if isinstance(item, str):
                    moves.append(item)
                elif isinstance(item, dict):
                    # dict may contain 'uci' or 'san'
                    uci = item.get("uci") or item.get("move") or item.get("fromTo")
                    if uci:
                        moves.append(uci)
    elif "pv" in pv and isinstance(pv["pv"], str):
        moves = [m for m in pv["pv"].split() if m]
    # Filter out obviously wrong entries
    moves = [m for m in moves if isinstance(m, str) and len(m) >= 4]
    return moves


def uci_moves_to_san_list(board: chess.Board, uci_moves, max_moves=8):
    """Convert a list of UCI moves into SANs from the given board.
    Stop after max_moves or when move parsing fails."""
    san_list = []
    temp = board.copy()
    count = 0
    for uci in uci_moves:
        if count >= max_moves:
            break
        try:
            mv = chess.Move.from_uci(uci)
        except Exception:
            # Could be SAN already; try parsing SAN
            try:
                mv = temp.parse_san(uci)
            except Exception:
                break
        try:
            san = temp.san(mv)
        except Exception:
            # Fallback to UCI string if SAN generation fails
            san = uci
        san_list.append(san)
        try:
            temp.push(mv)
        except Exception:
            break
        count += 1
    return san_list


def print_header(game):
    headers = game.headers
    white = headers.get("White", "?")
    black = headers.get("Black", "?")
    result = headers.get("Result", "*")
    event = headers.get("Event", "")
    site = headers.get("Site", "")
    date = headers.get("Date", "")
    print("=== Chess Game Review (Terminal) ===")
    parts = [p for p in [event, site, date] if p]
    if parts:
        print(" | ".join(parts))
    print(f"White: {white}  vs  Black: {black}   Result: {result}")
    print("------------------------------------\n")


async def explain_with_llm(move_idx: int, san: str, eval_str: str) -> str:
    """Query Groq/OpenAI-compatible chat completions for a short explanation."""
    if not LLM_KEY:
        return "LLM disabled (no GROQ_API_KEY set)."

    prompt = (
        f"Move {move_idx}: {san} | Eval: {eval_str}\n"
        "Explain this move in at most 2 concise sentences (≤40 words total). "
        "If a clearly better idea existed, mention it briefly."
    )
    headers = {
        "Authorization": f"Bearer {LLM_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }
    try:
        r = await asyncio.to_thread(requests.post, LLM_API, headers=headers, json=data, timeout=20)
        j = r.json()
        return j["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"LLM error: {e.__class__.__name__}"


async def run():
    # Load PGN
    if not Path(PGN_FILE).exists():
        raise FileNotFoundError(f"PGN not found: {PGN_FILE}")

    with open(PGN_FILE, "r", encoding="utf-8") as f:
        game = chess.pgn.read_game(f)
    if game is None:
        raise ValueError("No game found in PGN file.")

    print_header(game)

    # Precompute SAN list (so SAN is correct for each ply)
    moves = list(game.mainline_moves())
    board_for_san = chess.Board()
    san_moves = []
    for mv in moves:
        san_moves.append(board_for_san.san(mv))
        board_for_san.push(mv)

    # helper: build board up to (but not including) ply `n` (1-based)
    def board_up_to_ply(moves_list, n):
        b = chess.Board()
        for m in moves_list[: max(0, n - 1)]:
            b.push(m)
        return b

    # interactive helper to step through a chosen variation (uci_list) from the pre_board
    async def analyse_variation_from(pre_board: chess.Board, uci_list, max_moves=8):
        if not uci_list:
            print("  Variation has no moves.")
            return
        temp = pre_board.copy()
        print("  === Entering variation analysis mode ===")
        for i, uci in enumerate(uci_list[:max_moves], start=1):
            try:
                mv = chess.Move.from_uci(uci)
            except Exception:
                try:
                    mv = temp.parse_san(uci)
                except Exception:
                    print(f"   Skipping unknown move: {uci}")
                    break
            # fetch eval for position BEFORE this variation move
            pve = await fetch_lichess_eval_json(temp, multi_pv=3)
            if "error" in pve:
                ev = f"N/A ({pve['error']})"
                pvs = []
            else:
                ej = pve.get("json", {})
                ev = format_eval(ej, temp)
                pvs = _extract_pvs(ej)
            san = temp.san(mv) if True else uci
            print(f"   Var move {i}: {san}   Eval (pre-move): {ev}")
            # show top PVs for this variation position (short)
            if pvs:
                for vi, pv in enumerate(pvs, start=1):
                    ulist = _uci_list_from_pv(pv)
                    san_list = uci_moves_to_san_list(temp, ulist, max_moves=6)
                    pv_eval_str = format_eval({"pvs":[pv]}, temp)
                    seq = "  ".join(san_list) if san_list else "(no moves)"
                    print(f"     {vi}. {pv_eval_str}  {seq}")
            else:
                print("     No variations returned by Lichess.")
            # push the move into the temp line
            try:
                temp.push(mv)
            except Exception:
                break

            # wait for user to continue inside variation
            try:
                cmd = input("   Press Enter for next move in variation, 'q' to quit variation: ").strip()
            except EOFError:
                cmd = ""
            if cmd.lower() == "q":
                break
        print("  === Exiting variation analysis mode ===\n")

    # Iterate and print one move at a time (manual index so we can skip)
    idx = 1
    total = len(moves)
    while idx <= total:
        # build pre-move board for this ply (robust to skips)
        pre_board = board_up_to_ply(moves, idx)

        # Skip calling Lichess for the first SKIP_BOOK_MOVES plies (opening/book)
        if idx <= SKIP_BOOK_MOVES:
            eval_str = "skipped (opening/book)"
            pvs = []
        else:
            pve = await fetch_lichess_eval_json(pre_board, multi_pv=3)
            pvs = []
            if "error" in pve:
                eval_str = f"N/A ({pve['error']})"
            else:
                eval_json = pve.get("json", {})
                eval_str = format_eval(eval_json, pre_board)
                pvs = _extract_pvs(eval_json)

        # The actual move to display (played in the game)
        move = moves[idx - 1]
        post_board = pre_board.copy()
        try:
            post_board.push(move)
        except Exception:
            pass
        san = san_moves[idx - 1]

        # Show board (after the move)
        if SHOW_ASCII_BOARD:
            print(post_board, "\n")
        else:
            # print FEN for compactness if ASCII disabled
            print(post_board, "\n")

        if idx <= SKIP_BOOK_MOVES:
            explanation = "Opening theory, skipping detailed commentary."
            print(f"Move {idx:>3} ({'White' if idx % 2 == 1 else 'Black'}): {san}")
            print(f"  Eval (pre-move): {eval_str}")
            print(f"  Note: {explanation}\n")
        else:
            # Determine if the played move matched the best variation's first move
            played_uci = move.uci()
            best_played = False
            variations_output = []
            for i, pv in enumerate(pvs):
                uci_list = _uci_list_from_pv(pv)
                san_list = uci_moves_to_san_list(pre_board, uci_list, max_moves=8)
                pv_eval_str = format_eval({"pvs": [pv]}, pre_board)
                variations_output.append((i + 1, pv_eval_str, uci_list, san_list))
                if i == 0 and uci_list:
                    if uci_list[0] == played_uci:
                        best_played = True

            ply_side = "White" if idx % 2 == 1 else "Black"
            print(f"Move {idx:>3} ({ply_side}): {san}")
            print(f"  Eval (pre-move): {eval_str}")
            print(f"  Played best move? {'YES' if best_played else 'NO'}")

            if variations_output:
                print("  Top variations (up to 3):")
                for var_idx, pv_eval_str, uci_list, san_list in variations_output:
                    seq = "  ".join(san_list) if san_list else "(no moves)"
                    print(f"    {var_idx}. {pv_eval_str}  {seq}")
            else:
                print("  No variations returned by Lichess.")

            # Ask LLM for short explanation
            explanation = await explain_with_llm(idx, san, eval_str)
            print(f"  Note: {explanation}\n")

        # Interactive prompt — supports:
        #   Enter -> next move
        #   s N  -> skip to move N (1-based)
        #   l N  -> analyse variation number N interactively now
        #   q    -> quit program
        if WAIT_FOR_ENTER and idx > 0:
            try:
                cmd = input("Press Enter for next move, 's N' to skip, 'l N' to analyse variation N, 'q' to quit: ").strip()
            except EOFError:
                cmd = ""
            if not cmd:
                idx += 1
            else:
                parts = cmd.split()
                if parts[0].lower() in ("q", "quit", "exit"):
                    print("User requested exit.")
                    return
                elif parts[0].lower() in ("s", "skip") and len(parts) >= 2:
                    try:
                        target = int(parts[1])
                        if 1 <= target <= total:
                            idx = target
                        else:
                            print("  Invalid move number. Continuing to next move.")
                            idx += 1
                    except ValueError:
                        print("  Invalid number. Continuing to next move.")
                        idx += 1
                elif parts[0].lower() in ("l", "line", "v", "var") and len(parts) >= 2:
                    try:
                        varnum = int(parts[1])
                        found = None
                        for tup in variations_output:
                            if tup[0] == varnum:
                                found = tup
                                break
                        if not found:
                            print("  Variation not found. Returning.")
                        else:
                            _, pv_eval_str, uci_list, san_list = found
                            # run interactive analysis of that variation from pre_board
                            await analyse_variation_from(pre_board, uci_list, max_moves=16)
                    except ValueError:
                        print("  Invalid variation number.")
                    # after variation analysis stay at same game move (do not auto-advance)
                else:
                    print("  Unknown command, continuing to next move.")
                    idx += 1
        else:
            idx += 1

        # Be polite to the APIs if hitting many moves
        await asyncio.sleep(0.1)

    print("\n✅ Review complete.")


if __name__ == "__main__":
    asyncio.run(run())
