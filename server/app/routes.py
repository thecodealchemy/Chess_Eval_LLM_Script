from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List
from bson import ObjectId
from datetime import datetime

from .database import get_database
from .models import (
    GameModel, AnalysisModel, PGNUploadRequest, AnalysisRequest,
    GameResponse, AnalysisResponse, PGNStringRequest, MoveInfo, 
    GameMetadata, PGNUploadResponse, MoveAnalysisRequest, MoveAnalysisResponse,
    MoveAnalysisCache, VariationExploreRequest, VariationExploreResponse,
    VariationMoveAnalysis, GoogleTokenRequest, TokenResponse, UserResponse,
    GameAnalysisRequest, LimitedAnalysisRequest
)
from .chess_analyzer import ChessAnalyzer
from .auth import (
    verify_google_token, get_or_create_user, create_access_token, 
    get_current_user, get_current_user_optional
)

router = APIRouter()
analyzer = ChessAnalyzer()

# Authentication routes
@router.post("/auth/google", response_model=TokenResponse)
async def google_auth(request: GoogleTokenRequest, db=Depends(get_database)):
    """Authenticate user with Google OAuth token"""
    try:
        # Verify Google token
        google_user_data = await verify_google_token(request.token)
        
        # Get or create user
        user = await get_or_create_user(google_user_data, db)
        
        # Create JWT token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return TokenResponse(
            access_token=access_token,
            user={
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "picture": user.picture
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
        created_at=current_user.created_at
    )

@router.post("/games/upload", response_model=GameResponse)
async def upload_pgn(request: PGNUploadRequest, current_user = Depends(get_current_user_optional), db=Depends(get_database)):
    """Upload a new PGN game (authentication optional)"""
    try:
        # Extract game information
        game_info = analyzer.extract_game_info(request.pgn_content)
        
        # Create game document with optional user association
        game_data = {
            "title": request.title,
            "pgn_content": request.pgn_content,
            "upload_date": datetime.utcnow(),
            "user_id": str(current_user.id) if current_user else None,
            **game_info
        }
        
        # Insert into database
        result = await db.games.insert_one(game_data)
        game_data["_id"] = result.inserted_id
        
        # Count moves for response
        import chess.pgn
        from io import StringIO
        game = chess.pgn.read_game(StringIO(request.pgn_content))
        move_count = len(list(game.mainline_moves())) if game else 0
        
        return GameResponse(
            id=str(game_data["_id"]),
            title=game_data["title"],
            pgn_content=game_data["pgn_content"],  # Include PGN content
            white_player=game_data.get("white_player"),
            black_player=game_data.get("black_player"),
            result=game_data.get("result"),
            date_played=game_data.get("date_played"),
            event=game_data.get("event"),
            upload_date=game_data["upload_date"],
            move_count=move_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing PGN: {str(e)}")

@router.post("/upload_pgn", response_model=PGNUploadResponse)
async def upload_pgn_string(request: PGNStringRequest, current_user = Depends(get_current_user_optional), db=Depends(get_database)):
    """Upload a PGN string, parse it, and return metadata with moves list (authentication optional)"""
    try:
        import chess.pgn
        from io import StringIO
        
        # Parse PGN with python-chess (use cleaned PGN)
        cleaned_pgn = analyzer._clean_pgn_content(request.pgn)
        pgn_io = StringIO(cleaned_pgn)
        game = chess.pgn.read_game(pgn_io)
        
        if not game:
            raise HTTPException(status_code=400, detail="Invalid PGN format")
        
        # Extract game metadata
        headers = game.headers
        metadata = GameMetadata(
            white_player=headers.get("White"),
            black_player=headers.get("Black"),
            event=headers.get("Event"),
            result=headers.get("Result"),
            date=headers.get("Date"),
            site=headers.get("Site"),
            round=headers.get("Round"),
            eco=headers.get("ECO")
        )
        
        # Generate moves list with SAN and FEN at each step
        board = game.board()
        moves = []
        move_number = 0
        
        # Add starting position
        moves.append(MoveInfo(
            move_number=0,
            san="Starting position",
            fen=board.fen()
        ))
        
        # Process each move
        for move in game.mainline_moves():
            move_number += 1
            san = board.san(move)
            board.push(move)
            
            moves.append(MoveInfo(
                move_number=move_number,
                san=san,
                fen=board.fen()
            ))
        
        # Store parsed game in MongoDB with optional user association
        game_data = {
            "title": f"{metadata.white_player or 'White'} vs {metadata.black_player or 'Black'}",  # Generate title from players
            "pgn_content": cleaned_pgn,  # Store the cleaned PGN
            "upload_date": datetime.utcnow(),
            "user_id": str(current_user.id) if current_user else None,
            "white_player": metadata.white_player,
            "black_player": metadata.black_player,
            "result": metadata.result,
            "date_played": metadata.date,
            "event": metadata.event,
            "site": metadata.site,
            "round": metadata.round,
            "eco": metadata.eco,
            "move_count": move_number
        }
        
        # Insert into database
        result = await db.games.insert_one(game_data)
        game_id = str(result.inserted_id)
        
        return PGNUploadResponse(
            game_id=game_id,
            metadata=metadata,
            moves=moves
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing PGN: {str(e)}")

@router.post("/analyse_move", response_model=MoveAnalysisResponse)
async def analyze_move(request: MoveAnalysisRequest, db=Depends(get_database)):
    """Analyze a specific move using Lichess Cloud Eval and Groq LLM with MongoDB caching"""
    try:
        import chess.pgn
        from io import StringIO
        
        # Validate game_id
        if not ObjectId.is_valid(request.game_id):
            raise HTTPException(status_code=400, detail="Invalid game ID")
        
        # Check cache first
        cached_analysis = await db.move_analysis_cache.find_one({
            "game_id": request.game_id,
            "move_index": request.move_index
        })
        
        if cached_analysis:
            return MoveAnalysisResponse(
                eval=cached_analysis.get("evaluation"),
                explanation=cached_analysis.get("explanation"),
                variations=cached_analysis.get("variations", [])
            )
        
        # Get game from database
        game = await db.games.find_one({"_id": ObjectId(request.game_id)})
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Parse PGN and navigate to the requested move
        pgn_io = StringIO(game["pgn_content"])
        chess_game = chess.pgn.read_game(pgn_io)
        
        if not chess_game:
            raise HTTPException(status_code=400, detail="Invalid PGN in stored game")
        
        # Navigate to the specific move
        board = chess_game.board()
        moves = list(chess_game.mainline_moves())
        
        if request.move_index < 0 or request.move_index > len(moves):
            raise HTTPException(status_code=400, detail="Invalid move index")
        
        # Apply moves up to the requested index
        for i in range(request.move_index):
            board.push(moves[i])
        
        position_fen = board.fen()
        
        # Analyze the position
        analysis = await analyzer.analyze_single_move(
            request.game_id, 
            request.move_index, 
            position_fen
        )
        
        # Cache the result in MongoDB
        cache_doc = {
            "game_id": request.game_id,
            "move_index": request.move_index,
            "position_fen": position_fen,
            "evaluation": analysis["eval"],
            "explanation": analysis["explanation"],
            "variations": analysis["variations"],
            "created_at": datetime.utcnow()
        }
        
        try:
            await db.move_analysis_cache.insert_one(cache_doc)
        except Exception as cache_error:
            print(f"Warning: Failed to cache analysis: {cache_error}")
        
        return MoveAnalysisResponse(
            eval=analysis["eval"],
            explanation=analysis["explanation"],
            variations=analysis["variations"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing move: {str(e)}")

@router.post("/games/{game_id}/analyze")
async def analyze_game(
    game_id: str, 
    request: GameAnalysisRequest,
    db=Depends(get_database)
):
    """Analyze a specific game"""
    try:
        # Validate game_id
        if not ObjectId.is_valid(game_id):
            raise HTTPException(status_code=400, detail="Invalid game ID")
            
        # Get game from database
        game = await db.games.find_one({"_id": ObjectId(game_id)})
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Check if analysis already exists
        existing_analysis = await db.analyses.find_one({"game_id": game_id})
        if existing_analysis:
            # Return existing analysis count
            count = await db.analyses.count_documents({"game_id": game_id})
            return {"message": f"Game already analyzed ({count} positions)", "analysis_count": count}
        
        # Perform analysis
        analyses = await analyzer.analyze_pgn(game["pgn_content"], request.use_llm)
        
        # Store analyses in database
        analysis_docs = []
        for analysis in analyses:
            doc = {
                "game_id": game_id,
                "move_number": analysis["move_number"],
                "position_fen": analysis["position_fen"],
                "evaluation": analysis["evaluation"],
                "best_move": analysis["best_move"],
                "analysis_engine": "lichess",
                "variations": analysis["variations"],
                "explanation": analysis["explanation"],
                "created_at": datetime.utcnow()
            }
            analysis_docs.append(doc)
        
        if analysis_docs:
            await db.analyses.insert_many(analysis_docs)
        
        return {
            "message": f"Analysis completed for {len(analyses)} positions", 
            "analysis_count": len(analyses)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing game: {str(e)}")

@router.post("/games/{game_id}/analyze_limited")
async def analyze_game_limited(
    game_id: str, 
    request: LimitedAnalysisRequest,
    db=Depends(get_database)
):
    """Analyze only current and next 2 positions to avoid rate limits"""
    try:
        # Validate game_id
        if not ObjectId.is_valid(game_id):
            raise HTTPException(status_code=400, detail="Invalid game ID")
            
        # Get game from database
        game = await db.games.find_one({"_id": ObjectId(game_id)})
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Perform limited analysis
        analyses = await analyzer.analyze_limited_positions(
            game["pgn_content"], 
            request.start_move, 
            request.use_llm
        )
        
        # Store analyses in database (only new ones)
        analysis_docs = []
        for analysis in analyses:
            # Check if analysis already exists
            existing = await db.analyses.find_one({
                "game_id": game_id,
                "move_number": analysis["move_number"]
            })
            
            if not existing:
                doc = {
                    "game_id": game_id,
                    "move_number": analysis["move_number"],
                    "position_fen": analysis["position_fen"],
                    "evaluation": analysis["evaluation"],
                    "best_move": analysis["best_move"],
                    "analysis_engine": "lichess",
                    "variations": analysis["variations"],
                    "explanation": analysis["explanation"],
                    "created_at": datetime.utcnow()
                }
                analysis_docs.append(doc)
        
        if analysis_docs:
            await db.analyses.insert_many(analysis_docs)
        
        return {
            "message": f"Limited analysis completed for {len(analyses)} positions", 
            "analysis_count": len(analyses),
            "new_analyses": len(analysis_docs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing game: {str(e)}")

@router.get("/games", response_model=List[GameResponse])
async def get_games(skip: int = 0, limit: int = 10, current_user = Depends(get_current_user_optional), db=Depends(get_database)):
    """Get list of uploaded games (user's games if authenticated, all games if not)"""
    try:
        # If user is authenticated, show only their games; otherwise show all games
        query = {"user_id": str(current_user.id)} if current_user else {}
        cursor = db.games.find(query).sort("upload_date", -1).skip(skip).limit(limit)
        games = await cursor.to_list(length=limit)
        
        result = []
        for game in games:
            # Count moves for each game
            import chess.pgn
            from io import StringIO
            pgn_game = chess.pgn.read_game(StringIO(game["pgn_content"]))
            move_count = len(list(pgn_game.mainline_moves())) if pgn_game else 0
            
            result.append(GameResponse(
                id=str(game["_id"]),
                title=game.get("title", "Chess Game"),  # Default title if not present
                pgn_content=game.get("pgn_content", ""),  # Include PGN content
                white_player=game.get("white_player"),
                black_player=game.get("black_player"),
                result=game.get("result"),
                date_played=game.get("date_played"),
                event=game.get("event"),
                upload_date=game["upload_date"],
                move_count=move_count
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving games: {str(e)}")

@router.get("/games/{game_id}", response_model=GameResponse)
async def get_game(game_id: str, current_user = Depends(get_current_user_optional), db=Depends(get_database)):
    """Get specific game details (user's games if authenticated, all games if not)"""
    try:
        if not ObjectId.is_valid(game_id):
            raise HTTPException(status_code=400, detail="Invalid game ID")
            
        # If user is authenticated, check they own the game; otherwise allow access to any game
        query = {"_id": ObjectId(game_id)}
        if current_user:
            query["user_id"] = current_user.id
            
        game = await db.games.find_one(query)
        if not game:
            error_msg = "Game not found or access denied" if current_user else "Game not found"
            raise HTTPException(status_code=404, detail=error_msg)
        
        # Count moves
        import chess.pgn
        from io import StringIO
        pgn_game = chess.pgn.read_game(StringIO(game["pgn_content"]))
        move_count = len(list(pgn_game.mainline_moves())) if pgn_game else 0
        
        return GameResponse(
            id=str(game["_id"]),
            title=game.get("title", "Chess Game"),  # Default title if not present
            pgn_content=game.get("pgn_content", ""),  # Include PGN content
            white_player=game.get("white_player"),
            black_player=game.get("black_player"),
            result=game.get("result"),
            date_played=game.get("date_played"),
            event=game.get("event"),
            upload_date=game["upload_date"],
            move_count=move_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving game: {str(e)}")

@router.get("/games/{game_id}/analysis", response_model=List[AnalysisResponse])
async def get_game_analysis(game_id: str, db=Depends(get_database)):
    """Get analysis for a specific game"""
    try:
        if not ObjectId.is_valid(game_id):
            raise HTTPException(status_code=400, detail="Invalid game ID")
        
        cursor = db.analyses.find({"game_id": game_id}).sort("move_number", 1)
        analyses = await cursor.to_list(length=None)
        
        result = []
        for analysis in analyses:
            result.append(AnalysisResponse(
                id=str(analysis["_id"]),
                game_id=analysis["game_id"],
                move_number=analysis["move_number"],
                position_fen=analysis["position_fen"],
                evaluation=analysis["evaluation"],
                best_move=analysis["best_move"],
                variations=analysis["variations"],
                explanation=analysis["explanation"],
                created_at=analysis["created_at"]
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving analysis: {str(e)}")

@router.delete("/games/{game_id}")
async def delete_game(game_id: str, db=Depends(get_database)):
    """Delete a game and its analysis"""
    try:
        if not ObjectId.is_valid(game_id):
            raise HTTPException(status_code=400, detail="Invalid game ID")
        
        # Delete game
        game_result = await db.games.delete_one({"_id": ObjectId(game_id)})
        if game_result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Delete associated analyses
        await db.analyses.delete_many({"game_id": game_id})
        
        return {"message": "Game and analysis deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting game: {str(e)}")

@router.post("/explore_variation", response_model=VariationExploreResponse)
async def explore_variation(request: VariationExploreRequest, db=Depends(get_database)):
    """Analyze a variation line move by move with evaluations and commentary"""
    try:
        # Use the chess analyzer to analyze the variation
        variation_analysis = await analyzer.analyze_variation(
            request.start_fen, 
            request.variation_moves
        )
        
        # Convert to response format
        analysis_list = []
        for move_analysis in variation_analysis:
            analysis_list.append(VariationMoveAnalysis(
                move_number=move_analysis["move_number"],
                san=move_analysis["san"],
                fen=move_analysis["fen"],
                eval=move_analysis["eval"],
                explanation=move_analysis["explanation"],
                best_move=move_analysis["best_move"],
                variations=move_analysis["variations"]
            ))
        
        return VariationExploreResponse(
            variation_analysis=analysis_list
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exploring variation: {str(e)}")

@router.get("/games/{game_id}/export", response_model=dict)
async def export_annotated_pgn(game_id: str, current_user = Depends(get_current_user_optional), db=Depends(get_database)):
    """Export game as PGN with analysis annotations (user's games if authenticated, all games if not)"""
    try:
        if not ObjectId.is_valid(game_id):
            raise HTTPException(status_code=400, detail="Invalid game ID")
            
        # Get game (check ownership if user is authenticated)
        query = {"_id": ObjectId(game_id)}
        if current_user:
            query["user_id"] = current_user.id
            
        game = await db.games.find_one(query)
        if not game:
            error_msg = "Game not found or access denied" if current_user else "Game not found"
            raise HTTPException(status_code=404, detail=error_msg)
        
        # Get analysis
        cursor = db.analyses.find({"game_id": game_id}).sort("move_number", 1)
        analyses = await cursor.to_list(length=None)
        
        # Parse original PGN
        import chess.pgn
        from io import StringIO
        
        pgn_io = StringIO(game["pgn_content"])
        chess_game = chess.pgn.read_game(pgn_io)
        
        if not chess_game:
            raise HTTPException(status_code=400, detail="Invalid PGN in stored game")
        
        # Add analysis comments to the game
        board = chess_game.board()
        node = chess_game
        
        # Create analysis lookup
        analysis_by_move = {a["move_number"]: a for a in analyses}
        
        move_number = 0
        for move in chess_game.mainline_moves():
            move_number += 1
            board.push(move)
            
            # Find the node for this move
            if node.variations:
                node = node.variations[0]
            
            # Add analysis comment if available
            if move_number in analysis_by_move:
                analysis = analysis_by_move[move_number]
                comment_parts = []
                
                if analysis.get("evaluation") is not None:
                    eval_str = f"+{analysis['evaluation']:.2f}" if analysis['evaluation'] > 0 else f"{analysis['evaluation']:.2f}"
                    comment_parts.append(f"[Eval: {eval_str}]")
                
                if analysis.get("explanation"):
                    comment_parts.append(analysis["explanation"])
                
                if analysis.get("best_move"):
                    comment_parts.append(f"Best: {analysis['best_move']}")
                
                if comment_parts:
                    node.comment = " ".join(comment_parts)
        
        # Convert back to PGN string
        output = StringIO()
        exporter = chess.pgn.FileExporter(output)
        chess_game.accept(exporter)
        annotated_pgn = output.getvalue()
        
        return {
            "pgn": annotated_pgn,
            "filename": f"analyzed_{game.get('white_player', 'Unknown')}_vs_{game.get('black_player', 'Unknown')}.pgn"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting PGN: {str(e)}")