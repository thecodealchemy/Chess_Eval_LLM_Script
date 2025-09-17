from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List, Annotated, Union
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")
        return field_schema

class GameModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    title: str
    pgn_content: str
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    white_player: Optional[str] = None
    black_player: Optional[str] = None
    result: Optional[str] = None
    date_played: Optional[str] = None
    event: Optional[str] = None
    user_id: str  # Add user association

class AnalysisModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    game_id: str
    move_number: int
    position_fen: str
    evaluation: Optional[float] = None
    best_move: Optional[str] = None
    analysis_engine: str = "lichess"
    variations: List[str] = []
    explanation: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PGNUploadRequest(BaseModel):
    title: str
    pgn_content: str

class AnalysisRequest(BaseModel):
    game_id: str
    use_llm: bool = False

class GameAnalysisRequest(BaseModel):
    use_llm: bool = False

class LimitedAnalysisRequest(BaseModel):
    start_move: int
    use_llm: bool = False

class GameResponse(BaseModel):
    id: str
    title: str
    pgn_content: str  # Add PGN content for move loading
    white_player: Optional[str]
    black_player: Optional[str]
    result: Optional[str]
    date_played: Optional[str]
    event: Optional[str]
    upload_date: datetime
    move_count: Optional[int] = None

class AnalysisResponse(BaseModel):
    id: str
    game_id: str
    move_number: int
    position_fen: str
    evaluation: Optional[float]
    best_move: Optional[str]
    variations: List[str]
    explanation: Optional[str]
    created_at: datetime

# New models for /upload_pgn endpoint
class PGNStringRequest(BaseModel):
    pgn: str

class MoveInfo(BaseModel):
    move_number: int
    san: str
    fen: str

class GameMetadata(BaseModel):
    white_player: Optional[str] = None
    black_player: Optional[str] = None
    event: Optional[str] = None
    result: Optional[str] = None
    date: Optional[str] = None
    site: Optional[str] = None
    round: Optional[str] = None
    eco: Optional[str] = None

class PGNUploadResponse(BaseModel):
    game_id: str
    metadata: GameMetadata
    moves: List[MoveInfo]

# New models for /analyse_move endpoint
class MoveAnalysisRequest(BaseModel):
    game_id: str
    move_index: int

class MoveAnalysisResponse(BaseModel):
    eval: Optional[Union[float, str]]  # Can be float for centipawn or string for mate
    explanation: Optional[str]
    variations: List[str]

class MoveAnalysisCache(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    game_id: str
    move_index: int
    position_fen: str
    evaluation: Optional[float] = None
    explanation: Optional[str] = None
    variations: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

# New models for variation exploration
class VariationExploreRequest(BaseModel):
    start_fen: str
    variation_moves: str

class VariationMoveAnalysis(BaseModel):
    move_number: int
    san: str
    fen: str
    eval: Optional[float]
    explanation: Optional[str]
    best_move: Optional[str]
    variations: List[str]

class VariationExploreResponse(BaseModel):
    variation_analysis: List[VariationMoveAnalysis]

# Authentication models
class UserModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    google_id: str
    email: EmailStr
    name: str
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

class GoogleTokenRequest(BaseModel):
    token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime