from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

class Mode(str, Enum):
    code = 'code'
    framework = 'framework'

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    mode: Mode = Mode.code
    model: str = Field(default='llama-3.3-70b-versatile')
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    max_tokens: int = Field(default=800, ge=1, le=2000)
    explain: bool = Field(default=True)
    verify: bool = Field(default=True)

class ResponsibleAIResponse(BaseModel):
    privacy: dict = Field(default_factory=dict)
    safety: dict = Field(default_factory=dict)
    fairness: dict = Field(default_factory=dict)
    explainability: dict = Field(default_factory=dict)
    verifiability: dict = Field(default_factory=dict)
    transparency: dict = Field(default_factory=dict)
    governance: dict = Field(default_factory=dict)
    controllability: dict = Field(default_factory=dict)

class MetadataResponse(BaseModel):
    model: str
    provider: str
    mode: Mode
    request_id: str
    timestamp: datetime

class ChatResponse(BaseModel):
    answer: str
    responsible_ai: ResponsibleAIResponse
    metadata: MetadataResponse

class AuditEvent(BaseModel):
    request_id: str
    timestamp: datetime
    mode: Mode
    model: str
    provider: str
    is_cached: bool = False
    summary: str = ''
    responsible_ai: dict = Field(default_factory=dict)

class PolicyResponse(BaseModel):
    policy: dict
