"""Pydantic schemas for API requests and responses."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class WatchCoreResponse(BaseModel):
    watch_id: int
    source: str
    product_url: str
    image_url: Optional[str]
    brand: Optional[str]
    product_name: str
    sku: Optional[str]
    price_raw: Optional[str]
    price_value: Optional[Decimal]
    currency: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WatchSpecStateResponse(BaseModel):
    id: int
    watch_id: int
    spec_key: str
    spec_value: Optional[str]
    unit: Optional[str]
    source_type: str
    confidence: Optional[Decimal]
    resolved_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WatchSpecSourceResponse(BaseModel):
    id: int
    watch_id: int
    spec_key: str
    spec_value: str
    unit: Optional[str]
    source_type: str
    source_name: str
    source_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: UUID
    username: Optional[str]
    display_name: Optional[str]
    avatar_url: Optional[str]

    class Config:
        from_attributes = True


class ProfileMeResponse(BaseModel):
    id: UUID
    username: Optional[str]
    display_name: Optional[str]
    avatar_url: Optional[str]
    is_admin: bool

    class Config:
        from_attributes = True


class WatchCommentResponse(BaseModel):
    id: int
    watch_id: int
    user_id: UUID
    content: str
    rating: Optional[int]
    created_at: datetime
    updated_at: datetime
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class CreateCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    rating: Optional[int] = Field(None, ge=1, le=5)


class WatchUserContributionResponse(BaseModel):
    id: int
    watch_id: int
    user_id: UUID
    spec_key: str
    proposed_value: str
    unit: Optional[str]
    note: Optional[str]
    evidence_url: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    user: Optional[UserResponse] = None
    votes: Optional[dict] = None

    class Config:
        from_attributes = True


class CreateContributionRequest(BaseModel):
    spec_key: str = Field(..., min_length=1, max_length=100)
    proposed_value: str = Field(..., min_length=1)
    unit: Optional[str] = Field(None, max_length=50)
    note: Optional[str] = Field(None, max_length=1000)
    evidence_url: Optional[str] = None


class VoteRequest(BaseModel):
    vote_type: str = Field(..., pattern="^(confirm|reject)$")


class WatchListResponse(BaseModel):
    watches: List[WatchCoreResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class WatchDetailResponse(WatchCoreResponse):
    specs: List[WatchSpecStateResponse] = []
    comments_count: int = 0


class WatchSpecsResponse(BaseModel):
    specs: List[WatchSpecStateResponse]
    sources: dict[str, List[WatchSpecSourceResponse]]


class AIIdentifyCandidate(BaseModel):
    watch_id: int
    brand: Optional[str]
    product_name: str
    image_url: Optional[str]
    similarity_score: float


class VLMAttributes(BaseModel):
    brand_guess: Optional[str]
    dial_color: Optional[str]
    bracelet_material: Optional[str]
    confidence: float
    short_explanation: str


class DetectionCrop(BaseModel):
    label: str
    image_url: str
    box: List[float] = []
    score: float = 0.0


class DebugInfo(BaseModel):
    request_id: str
    annotated_image_url: Optional[str] = None
    debug_json_url: Optional[str] = None
    detector_used: bool = False
    models: dict = {}
    timing: dict = {}


class AIIdentifyResponse(BaseModel):
    candidates: List[AIIdentifyCandidate]
    vlm_attributes: Optional[VLMAttributes] = None
    is_unknown: bool = False
    retrieval_time_ms: Optional[int] = None
    vlm_time_ms: Optional[int] = None
    detection_crops: Optional[List[DetectionCrop]] = None
    detected_text: Optional[dict] = None
    debug_info: Optional[DebugInfo] = None


class UserCollectionResponse(BaseModel):
    id: int
    user_id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserCollectionItemResponse(BaseModel):
    id: int
    collection_id: int
    status: str

    sku: Optional[str] = None
    source: Optional[str] = None
    product_url: Optional[str] = None
    product_name: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None

    watch_id: Optional[int] = None
    suggestion_id: Optional[int] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateUserCollectionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)


class AdminApproveSuggestionRequest(BaseModel):
    admin_notes: Optional[str] = Field(None, max_length=5000)


class WatchSuggestionResponse(BaseModel):
    id: int
    submitted_by: UUID
    status: str

    sku: Optional[str] = None
    source: Optional[str] = None
    product_url: Optional[str] = None
    product_name: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None

    ai_output_json: Optional[dict] = None
    admin_notes: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

