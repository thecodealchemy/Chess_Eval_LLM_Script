import chess
import chess.pgn
import requests
import asyncio
from typing import Optional, List, Tuple
from io import StringIO
import os
from groq import Groq

class ChessAnalyzer:
    def __init__(self):
        self.lichess_api_base = "https://lichess.org/api/cloud-eval"
        self.cache = {}  # Simple in-memory cache
        self.groq_client = None
        
        # Initialize Groq client if API key is available
        groq_api_key = os.getenv("GROQ_API_KEY")
        
        # Check if API key exists and is not a placeholder
        if groq_api_key and groq_api_key.strip() and not groq_api_key.strip().startswith("your_groq_api_key"):
            try:
                self.groq_client = Groq(api_key=groq_api_key.strip())
                print("✓ Groq client initialized successfully")
            except Exception as e:
                print(f"Warning: Failed to initialize Groq client: {e}")
        else:
            print("Warning: GROQ_API_KEY not set or using placeholder value. AI explanations will use fallback mode.")
        
    async def analyze_pgn(self, pgn_content: str, use_llm: bool = False) -> List[dict]:
        """Analyze a complete PGN game"""
        game = chess.pgn.read_game(StringIO(pgn_content))
        if not game:
            raise ValueError("Invalid PGN content")
            
        board = game.board()
        analyses = []
        move_number = 0
        
        for move in game.mainline_moves():
            move_number += 1
            
            # Get SAN notation BEFORE pushing the move
            move_san = board.san(move)
            
            # Push the move to update the board
            board.push(move)
            
            # Get position analysis after the move
            fen = board.fen()
            evaluation = await self._get_position_evaluation(fen)
            
            analysis = {
                "move_number": move_number,
                "position_fen": fen,
                "move_san": move_san,
                "evaluation": evaluation.get("eval"),
                "best_move": evaluation.get("best_move"),
                "variations": evaluation.get("variations", []),
                "explanation": None
            }
            
            # Add LLM explanation if requested
            if use_llm and evaluation.get("eval") is not None:
                explanation = await self._get_llm_explanation(
                    fen, move_number, evaluation
                )
                analysis["explanation"] = explanation
                
            analyses.append(analysis)
            
        return analyses

    async def analyze_limited_positions(self, pgn_content: str, start_move: int, use_llm: bool = False) -> List[dict]:
        """Analyze only current position and next 2 positions to avoid rate limits"""
        game = chess.pgn.read_game(StringIO(pgn_content))
        if not game:
            raise ValueError("Invalid PGN content")
            
        board = game.board()
        analyses = []
        move_number = 0
        all_moves = list(game.mainline_moves())
        
        # Calculate which moves to analyze (current + next 2)
        moves_to_analyze = range(max(1, start_move), min(len(all_moves) + 1, start_move + 3))
        
        for move in all_moves:
            move_number += 1
            
            # Get SAN notation BEFORE pushing the move
            move_san = board.san(move)
            
            # Push the move to update the board
            board.push(move)
            
            # Only analyze if this move is in our target range
            if move_number in moves_to_analyze:
                # Get position analysis after the move
                fen = board.fen()
                evaluation = await self._get_position_evaluation(fen)
                
                analysis = {
                    "move_number": move_number,
                    "position_fen": fen,
                    "move_san": move_san,
                    "evaluation": evaluation.get("eval"),
                    "best_move": evaluation.get("best_move"),
                    "variations": evaluation.get("variations", []),
                    "explanation": None
                }
                
                # Add LLM explanation if requested
                if use_llm and evaluation.get("eval") is not None:
                    explanation = await self._get_llm_explanation(
                        fen, move_number, evaluation
                    )
                    analysis["explanation"] = explanation
                    
                analyses.append(analysis)
            
        return analyses
    
    async def _get_position_evaluation(self, fen: str) -> dict:
        """Get position evaluation from Lichess cloud eval with robust error handling"""
        # Check cache first
        if fen in self.cache:
            return self.cache[fen]
            
        # First, validate the FEN position
        try:
            import chess
            test_board = chess.Board(fen)
            if test_board.is_game_over():
                # Position is terminal (checkmate, stalemate, etc.)
                result = self._handle_terminal_position(test_board)
                self.cache[fen] = result
                return result
        except ValueError as e:
            print(f"Invalid FEN: {fen} - {e}")
            return {"eval": None, "best_move": None, "variations": [], "pvs": [], "error": "Invalid FEN"}
            
        try:
            # Use similar parameters as CloudReviews.py
            response = requests.get(
                self.lichess_api_base,
                params={"fen": fen, "multiPv": 3, "depth": 15},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse according to CloudReviews.py format
                pvs = data.get("pvs", [])
                variations = []
                eval_score = None
                best_move = None
                
                if pvs and len(pvs) > 0:
                    # Get evaluation from first PV
                    first_pv = pvs[0]
                    
                    # Handle mate scores
                    if "mate" in first_pv and first_pv["mate"] is not None:
                        mate_score = first_pv["mate"]
                        eval_score = f"#{'+' if mate_score > 0 else ''}{mate_score}"
                    # Handle centipawn scores
                    elif "cp" in first_pv and first_pv["cp"] is not None:
                        eval_score = first_pv["cp"] / 100.0
                    
                    # Extract variations from all PVs
                    for i, pv_data in enumerate(pvs[:3]):
                        pv_moves = self._extract_moves_from_pv(pv_data)
                        print(f"PV {i+1}: extracted_moves={pv_moves}")
                        if pv_moves:
                            variation_str = " ".join(pv_moves[:8])  # Limit to 8 moves
                            variations.append(variation_str)
                            print(f"Added variation {i+1}: {variation_str}")
                    
                    # Get best move from first variation
                    if variations and variations[0]:
                        best_move = variations[0].split()[0] if variations[0].split() else None
                
                print(f"Lichess API success for {fen[:20]}...: found {len(pvs)} PVs, {len(variations)} variations")
                result = {
                    "eval": eval_score,
                    "best_move": best_move,
                    "variations": variations,
                    "pvs": pvs  # Keep raw PVs for detailed analysis
                }
                
                # Cache the result
                self.cache[fen] = result
                return result
                
            elif response.status_code == 404:
                # Position not found in Lichess database - provide fallback
                print(f"Lichess API: Position not in database (404) - {fen[:20]}...")
                fallback_result = self._provide_fallback_evaluation(fen)
                self.cache[fen] = fallback_result
                return fallback_result
                
            else:
                print(f"Lichess API error: HTTP {response.status_code} for {fen[:20]}...")
                
        except requests.exceptions.Timeout:
            print(f"Lichess API timeout for {fen[:20]}...")
        except requests.exceptions.RequestException as e:
            print(f"Lichess API connection error: {e.__class__.__name__}")
        except Exception as e:
            print(f"Error getting evaluation for {fen[:20]}...: {e}")
            
        # Return fallback when API fails
        fallback_result = self._provide_fallback_evaluation(fen)
        self.cache[fen] = fallback_result
        return fallback_result
    
    def _extract_moves_from_pv(self, pv_data: dict) -> List[str]:
        """Extract UCI moves from PV data based on CloudReviews.py logic"""
        moves = []
        if not pv_data:
            return moves
            
        # Try 'moves' field first
        if "moves" in pv_data:
            mv = pv_data["moves"]
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
        # Try 'pv' field as fallback
        elif "pv" in pv_data and isinstance(pv_data["pv"], str):
            moves = [m for m in pv_data["pv"].split() if m]
            
        # Filter out obviously wrong entries
        moves = [m for m in moves if isinstance(m, str) and len(m) >= 4]
        return moves
    
    def _handle_terminal_position(self, board) -> dict:
        """Handle terminal positions (checkmate, stalemate, etc.)"""
        if board.is_checkmate():
            # Determine who is checkmated
            if board.turn:  # White to move but checkmated
                eval_score = "#-0"  # Black wins
            else:  # Black to move but checkmated
                eval_score = "#+0"  # White wins
        elif board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition():
            eval_score = 0.0  # Draw
        else:
            eval_score = None
            
        return {
            "eval": eval_score,
            "best_move": None,
            "variations": [],
            "pvs": [],
            "terminal": True
        }
    
    def _provide_fallback_evaluation(self, fen: str) -> dict:
        """Provide basic evaluation when Lichess API is unavailable"""
        try:
            import chess
            board = chess.Board(fen)
            
            # Basic material count evaluation
            material_balance = self._calculate_material_balance(board)
            
            # Simple positional factors
            positional_score = self._calculate_basic_positional_score(board)
            
            # Combine for rough evaluation
            total_eval = material_balance + positional_score
            
            # Generate basic "variations" by suggesting common good moves
            basic_variations = self._generate_basic_move_suggestions(board)
            
            return {
                "eval": round(total_eval, 2),
                "best_move": basic_variations[0].split()[0] if basic_variations else None,
                "variations": basic_variations,
                "pvs": [],
                "fallback": True,
                "note": "Basic evaluation (Lichess cloud eval unavailable)"
            }
            
        except Exception as e:
            print(f"Error in fallback evaluation: {e}")
            return {
                "eval": 0.0,
                "best_move": None,
                "variations": ["No analysis available"],
                "pvs": [],
                "fallback": True,
                "error": "Evaluation unavailable"
            }
    
    def _calculate_material_balance(self, board) -> float:
        """Calculate material balance in pawns"""
        piece_values = {
            chess.PAWN: 1.0,
            chess.KNIGHT: 3.0,
            chess.BISHOP: 3.0,
            chess.ROOK: 5.0,
            chess.QUEEN: 9.0,
            chess.KING: 0.0
        }
        
        white_material = 0
        black_material = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = piece_values.get(piece.piece_type, 0)
                if piece.color == chess.WHITE:
                    white_material += value
                else:
                    black_material += value
                    
        return white_material - black_material
    
    def _calculate_basic_positional_score(self, board) -> float:
        """Calculate basic positional factors"""
        score = 0.0
        
        # Center control (very basic)
        center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
        for square in center_squares:
            piece = board.piece_at(square)
            if piece:
                if piece.color == chess.WHITE:
                    score += 0.1
                else:
                    score -= 0.1
        
        # King safety (very basic - penalize exposed king)
        white_king_square = board.king(chess.WHITE)
        black_king_square = board.king(chess.BLACK)
        
        if white_king_square and board.is_attacked_by(chess.BLACK, white_king_square):
            score -= 0.2
        if black_king_square and board.is_attacked_by(chess.WHITE, black_king_square):
            score += 0.2
            
        return score
    
    def _generate_basic_move_suggestions(self, board) -> List[str]:
        """Generate basic move suggestions when engine analysis is unavailable"""
        import chess
        suggestions = []
        
        try:
            legal_moves = list(board.legal_moves)
            if not legal_moves:
                return ["No legal moves"]
            
            # Prioritize captures, checks, and central moves
            good_moves = []
            
            for move in legal_moves[:20]:  # Limit to first 20 moves for performance
                move_san = board.san(move)
                
                # Prioritize captures
                if board.is_capture(move):
                    good_moves.append((move_san, 3))
                # Prioritize checks
                elif board.gives_check(move):
                    good_moves.append((move_san, 2))
                # Prioritize central moves
                elif move.to_square in [chess.E4, chess.E5, chess.D4, chess.D5]:
                    good_moves.append((move_san, 1))
                else:
                    good_moves.append((move_san, 0))
            
            # Sort by priority and take top 3
            good_moves.sort(key=lambda x: x[1], reverse=True)
            top_moves = [move[0] for move in good_moves[:3]]
            
            # Format as variation strings
            for i, move in enumerate(top_moves):
                if i == 0:
                    suggestions.append(f"{move} (capture/check priority)")
                elif i == 1:
                    suggestions.append(f"{move} (tactical option)")
                else:
                    suggestions.append(f"{move} (alternative)")
            
            return suggestions if suggestions else ["Analysis limited"]
            
        except Exception as e:
            print(f"Error generating move suggestions: {e}")
            return ["Basic analysis available"]
    
    async def _get_llm_explanation(self, fen: str, move_number: int, evaluation: dict) -> Optional[str]:
        """Get LLM explanation for a position (fallback method)"""
        eval_score = evaluation.get("eval")
        best_move = evaluation.get("best_move", "")
        variations = evaluation.get("variations", [])
        is_fallback = evaluation.get("fallback", False)
        is_terminal = evaluation.get("terminal", False)
        
        # Handle terminal positions
        if is_terminal:
            if isinstance(eval_score, str) and "#" in eval_score:
                return "Checkmate position reached."
            else:
                return "Game ended in a draw (stalemate, insufficient material, or repetition)."
        
        # Handle None evaluation
        if eval_score is None:
            return f"Position analysis unavailable. Engine unable to evaluate this position."
        
        # Handle mate scores
        if isinstance(eval_score, str) and eval_score.startswith("#"):
            mate_num = eval_score[1:] if eval_score[1:].isdigit() else eval_score[2:]
            return f"Mate in {mate_num} moves detected! The position shows a forced checkmate sequence."
        
        # Ensure eval_score is a number before comparison
        try:
            eval_score = float(eval_score)
        except (TypeError, ValueError):
            return f"Position evaluation unavailable due to analysis error."
        
        # Build explanation based on evaluation
        if eval_score > 2:
            explanation = f"White has a significant advantage (+{eval_score:.1f}). "
        elif eval_score < -2:
            explanation = f"Black has a significant advantage ({eval_score:.1f}). "
        elif eval_score > 0.5:
            explanation = f"White is slightly better (+{eval_score:.1f}). "
        elif eval_score < -0.5:
            explanation = f"Black is slightly better ({eval_score:.1f}). "
        else:
            explanation = f"Position is roughly equal ({eval_score:.1f}). "
        
        # Add best move info if available
        if best_move:
            explanation += f"Best move: {best_move}."
        
        # Add appropriate note based on evaluation source
        if is_fallback:
            explanation += " (Basic analysis - cloud evaluation unavailable)"
        else:
            explanation += " (Enable GROQ_API_KEY for detailed AI analysis)"
        
        return explanation
    
    async def analyze_single_move(self, game_id: str, move_index: int, position_fen: str, played_move: Optional[str] = None) -> dict:
        """Analyze a single move using Lichess API and Groq LLM"""
        # Get position evaluation from Lichess (this should be the position BEFORE the move)
        evaluation = await self._get_position_evaluation(position_fen)
        
        # Get LLM explanation with played move context
        explanation = await self._get_groq_explanation(position_fen, move_index, evaluation, played_move)
        
        return {
            "eval": evaluation.get("eval"),
            "explanation": explanation,
            "variations": evaluation.get("variations", []),
            "played_best": self._check_if_best_move(played_move, evaluation.get("best_move"))
        }
    
    def _check_if_best_move(self, played_move: Optional[str], best_move: Optional[str]) -> bool:
        """Check if the played move matches the best move"""
        if not played_move or not best_move:
            return False
        return played_move.lower() == best_move.lower()

    async def _get_groq_explanation(self, fen: str, move_index: int, evaluation: dict, played_move: Optional[str] = None) -> Optional[str]:
        """Get move explanation from Groq LLM with better analysis and fallback handling"""
        if not self.groq_client:
            # Fallback to simple explanation if Groq is not available
            fallback_explanation = await self._get_llm_explanation(fen, move_index, evaluation)
            return f"{fallback_explanation} (Note: Set GROQ_API_KEY for AI analysis)"
        
        try:
            eval_score = evaluation.get("eval")
            best_move = evaluation.get("best_move", "")
            variations = evaluation.get("variations", [])
            is_fallback = evaluation.get("fallback", False)
            is_terminal = evaluation.get("terminal", False)
            
            # Handle terminal positions
            if is_terminal:
                return "Game over position - no further analysis needed."
            
            # Handle None evaluation
            if eval_score is None:
                eval_score = 0.0
                eval_str = "N/A"
            elif isinstance(eval_score, str) and eval_score.startswith("#"):
                eval_str = eval_score  # Mate score
            else:
                # Ensure eval_score is a number
                try:
                    eval_score = float(eval_score)
                    eval_str = f"{eval_score:+.2f}"
                except (TypeError, ValueError):
                    eval_score = 0.0
                    eval_str = "N/A"
            
            # Determine if played move was best
            played_best = False
            if played_move and best_move:
                played_best = played_move.lower() == best_move.lower()
            
            # Build variation info for context - improved for fallback scenarios
            variation_context = ""
            analysis_source = ""
            
            if variations and not is_fallback:
                # Real Lichess engine variations
                top_variation = variations[0].split()[:4]  # First 4 moves
                variation_context = f"Engine best line: {' '.join(top_variation)}"
                analysis_source = "Lichess engine analysis"
            elif variations and is_fallback:
                # Basic move suggestions from fallback
                variation_context = f"Suggested moves: {', '.join(variations[:2])}"
                analysis_source = "Basic position analysis"
            elif is_fallback:
                variation_context = "Cloud evaluation unavailable - using basic analysis"
                analysis_source = "Basic material/positional analysis"
            else:
                variation_context = "No engine lines available"
                analysis_source = "Limited analysis"
            
            # Adjust prompt based on evaluation source with more detailed context
            if is_fallback:
                prompt = f"""Chess position analysis using basic evaluation (≤40 words):

Move {move_index}: {played_move or 'Unknown'}
Material evaluation: {eval_str}
{variation_context}
Source: {analysis_source}

Analyze: 1) Material balance, 2) Basic tactical/positional factors, 3) General move assessment."""
            else:
                prompt = f"""Chess expert analysis with engine data (≤40 words):

Position: {fen}
Move {move_index}: {played_move or 'Unknown'}
Engine evaluation: {eval_str}
Played best move: {'YES' if played_best else 'NO'}
{variation_context}
Source: {analysis_source}

Explain: 1) What this evaluation means, 2) Key factors, 3) Better alternatives if applicable."""
            
            print(f"LLM prompt for move {move_index}: {prompt[:100]}...")  # Debug log
            
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.1-8b-instant",  # Updated to current model
                max_tokens=80,  # Reduced for conciseness
                temperature=0.2  # Lower temperature for more consistent analysis
            )
            
            response_content = response.choices[0].message.content
            
            # Add note about evaluation source if using fallback with more context
            if is_fallback and response_content:
                if "Basic analysis" not in response_content:
                    response_content += f" [Source: {analysis_source}]"
            elif not is_fallback and response_content:
                if "Engine analysis" not in response_content:
                    response_content += f" [Source: {analysis_source}]"
            
            return response_content.strip() if response_content else "Analysis unavailable"
            
        except Exception as e:
            print(f"Error getting Groq explanation: {e}")
            # Fallback to simple explanation
            return await self._get_llm_explanation(fen, move_index, evaluation)

    def extract_game_info(self, pgn_content: str) -> dict:
        """Extract game metadata from PGN"""
        try:
            # Clean the PGN content first
            cleaned_pgn = self._clean_pgn_content(pgn_content)
            
            game = chess.pgn.read_game(StringIO(cleaned_pgn))
            if not game:
                return {}
                
            headers = game.headers
            return {
                "white_player": headers.get("White"),
                "black_player": headers.get("Black"),
                "result": headers.get("Result"),
                "date_played": headers.get("Date"),
                "event": headers.get("Event"),
                "site": headers.get("Site"),
                "round": headers.get("Round"),
                "eco": headers.get("ECO")
            }
        except Exception as e:
            print(f"Error extracting game info: {e}")
            return {}
    
    def _clean_pgn_content(self, pgn_content: str) -> str:
        """Clean and normalize PGN content with robust header separation"""
        try:
            # First, handle concatenated headers by adding newlines between ] and [
            cleaned = pgn_content.replace("] [", "]\n[")
            
            # Split into lines and process each line
            lines = cleaned.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                if line:
                    cleaned_lines.append(line)
                    
            # Join lines and ensure proper structure
            result = '\n'.join(cleaned_lines)
            
            # Add a blank line between headers and moves if not present
            if ']\n1.' in result and not ']\n\n1.' in result:
                result = result.replace(']\n1.', ']\n\n1.')
                
            return result
        except Exception as e:
            print(f"Error in PGN cleaning: {e}")
            return pgn_content
    
    async def analyze_variation(self, start_fen: str, variation_moves: str) -> List[dict]:
        """Analyze a variation line move by move"""
        if not variation_moves.strip():
            return []
            
        try:
            # Create a board from the starting position
            board = chess.Board(start_fen)
            variation_analysis = []
            
            # Parse the variation moves
            moves = variation_moves.strip().split()
            
            for i, move_str in enumerate(moves[:10]):  # Limit to first 10 moves
                try:
                    # Try to parse the move
                    move = board.parse_san(move_str) if move_str else None
                    if not move:
                        continue
                        
                    # Get SAN notation before making the move
                    san = board.san(move)
                    
                    # Make the move
                    board.push(move)
                    
                    # Get position evaluation
                    fen = board.fen()
                    evaluation = await self._get_position_evaluation(fen)
                    
                    # Get LLM explanation for the move
                    explanation = await self._get_groq_explanation(fen, i + 1, evaluation)
                    
                    variation_analysis.append({
                        "move_number": i + 1,
                        "san": san,
                        "fen": fen,
                        "eval": evaluation.get("eval"),
                        "explanation": explanation,
                        "best_move": evaluation.get("best_move"),
                        "variations": evaluation.get("variations", [])
                    })
                    
                except (chess.InvalidMoveError, chess.IllegalMoveError) as e:
                    print(f"Invalid move in variation: {move_str} - {e}")
                    continue
                    
            return variation_analysis
            
        except Exception as e:
            print(f"Error analyzing variation: {e}")
            return []