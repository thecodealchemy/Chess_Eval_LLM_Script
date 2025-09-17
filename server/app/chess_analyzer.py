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
        if groq_api_key and groq_api_key != "your_groq_api_key_here":
            try:
                self.groq_client = Groq(api_key=groq_api_key)
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
        """Get position evaluation from Lichess cloud eval"""
        # Check cache first
        if fen in self.cache:
            return self.cache[fen]
            
        try:
            response = requests.get(
                self.lichess_api_base,
                params={"fen": fen, "multiPv": 3},  # Request top 3 variations like CloudReviews.py
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse multiple PVs based on CloudReviews.py approach
                pvs = data.get("pvs", [])
                variations = []
                
                if pvs and len(pvs) > 0:
                    # Process up to 3 variations from Lichess API
                    for pv_data in pvs[:3]:
                        # Handle both 'moves' and 'pv' fields from Lichess response
                        pv_moves = None
                        if "moves" in pv_data and pv_data["moves"]:
                            pv_moves = pv_data["moves"]
                        elif "pv" in pv_data and pv_data["pv"]:
                            pv_moves = pv_data["pv"]
                        
                        if pv_moves:
                            # Ensure moves are space-separated string
                            if isinstance(pv_moves, list):
                                pv_moves = " ".join(str(m) for m in pv_moves)
                            variations.append(str(pv_moves))
                
                # Fallback to single PV if no multi-PV available
                if not variations and data.get("pv"):
                    variations = [data.get("pv", "")]
                
                result = {
                    "eval": data.get("cp", 0) / 100.0 if data.get("cp") else None,
                    "best_move": data.get("pv", "").split()[0] if data.get("pv") else None,
                    "variations": variations
                }
                
                # Cache the result
                self.cache[fen] = result
                return result
                
        except Exception as e:
            print(f"Error getting evaluation for {fen}: {e}")
            
        return {"eval": None, "best_move": None, "variations": []}
    
    async def _get_llm_explanation(self, fen: str, move_number: int, evaluation: dict) -> Optional[str]:
        """Get LLM explanation for a position (placeholder - integrate with Groq/OpenAI)"""
        # This is a placeholder - you can integrate with Groq or OpenAI here
        # For now, return a simple explanation based on evaluation
        eval_score = evaluation.get("eval")
        
        # Handle None evaluation
        if eval_score is None:
            return f"Move {move_number}: Position evaluation unavailable"
        
        # Ensure eval_score is a number before comparison
        try:
            eval_score = float(eval_score)
        except (TypeError, ValueError):
            return f"Move {move_number}: Position evaluation unavailable"
        
        if eval_score > 2:
            return f"Move {move_number}: White has a significant advantage (+{eval_score:.1f})"
        elif eval_score < -2:
            return f"Move {move_number}: Black has a significant advantage ({eval_score:.1f})"
        elif eval_score > 0.5:
            return f"Move {move_number}: White is slightly better (+{eval_score:.1f})"
        elif eval_score < -0.5:
            return f"Move {move_number}: Black is slightly better ({eval_score:.1f})"
        else:
            return f"Move {move_number}: Position is roughly equal ({eval_score:.1f})"
    
    async def analyze_single_move(self, game_id: str, move_index: int, position_fen: str) -> dict:
        """Analyze a single move using Lichess API and Groq LLM"""
        # Get position evaluation from Lichess
        evaluation = await self._get_position_evaluation(position_fen)
        
        # Get LLM explanation
        explanation = await self._get_groq_explanation(position_fen, move_index, evaluation)
        
        return {
            "eval": evaluation.get("eval"),
            "explanation": explanation,
            "variations": evaluation.get("variations", [])
        }
    
    async def _get_groq_explanation(self, fen: str, move_index: int, evaluation: dict) -> Optional[str]:
        """Get move explanation from Groq LLM"""
        if not self.groq_client:
            # Fallback to simple explanation if Groq is not available
            fallback_explanation = await self._get_llm_explanation(fen, move_index, evaluation)
            return f"{fallback_explanation} (Note: Set GROQ_API_KEY for AI analysis)"
        
        try:
            eval_score = evaluation.get("eval")
            best_move = evaluation.get("best_move", "")
            
            # Handle None evaluation
            if eval_score is None:
                eval_score = 0.0
            
            # Ensure eval_score is a number
            try:
                eval_score = float(eval_score)
            except (TypeError, ValueError):
                eval_score = 0.0
            
            prompt = f"""
You are a chess expert. Analyze this position and provide a brief explanation (2-3 sentences max).

Position FEN: {fen}
Move number: {move_index}
Engine evaluation: {eval_score:.2f} (positive = White advantage, negative = Black advantage)
Best move: {best_move}

Provide a concise explanation focusing on:
1. What the evaluation means
2. Key tactical or positional factors
3. The significance of the best move if applicable

Keep it under 150 characters for brevity.
"""
            
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama3-8b-8192",  # Using Llama 3 8B model
                max_tokens=100,
                temperature=0.3
            )
            
            response_content = response.choices[0].message.content
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