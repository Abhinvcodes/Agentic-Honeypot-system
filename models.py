from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

class Message(BaseModel):
    sender: str
    text: str
    timestamp: Optional[str] = Field(default=None)

class Metadata(BaseModel):
    channel: Optional[str] = Field(default=None)
    language: Optional[str] = Field(default=None)
    locale: Optional[str] = Field(default=None)

    @field_validator("channel", mode="before")
    @classmethod
    def normalize_channel(cls, v):
        if not isinstance(v, str):
            return v
        channel_map = {
            "sms": "SMS",
            "whatsapp": "WhatsApp",
            "email": "Email",
            "chat": "Chat",
        }
        return channel_map.get(v.lower(), v)

class IncomingRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Message] = Field(default_factory=list)
    metadata: Optional[Metadata] = Field(default=None)

class ExtractedIntelligence(BaseModel):
    bankAccounts: List[str] = Field(default_factory=list)
    upiIds: List[str] = Field(default_factory=list)
    phishingLinks: List[str] = Field(default_factory=list)
    phoneNumbers: List[str] = Field(default_factory=list)
    suspiciousKeywords: List[str] = Field(default_factory=list)

class EngagementMetrics(BaseModel):
    engagementDurationSeconds: int
    totalMessagesExchanged: int

class APIResponse(BaseModel):
    status: str
    reply: str
    scamDetected: bool
    engagementMetrics: Optional[EngagementMetrics] = Field(default=None)
    extractedIntelligence: Optional[ExtractedIntelligence] = Field(default=None)
    agentNotes: Optional[str] = Field(default=None)