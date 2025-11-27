from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

#Estructura de Kapso

# =========================================================
# Message
# =========================================================

class MessageText(BaseModel):
    body: str


class MessageKapso(BaseModel):
    origin: str
    status: str
    direction: str
    has_media: bool
    processing_status: str


class Message(BaseModel):
    id: str
    from_: str = Field(alias="from")
    text: MessageText
    type: str
    kapso: MessageKapso
    context: Optional[Any]
    timestamp: str


# =========================================================
# Conversation
# =========================================================

class ConversationKapso(BaseModel):
    messages_count: int
    last_inbound_at: Optional[str]
    last_message_id: Optional[str]
    last_message_text: Optional[str]
    last_message_type: Optional[str]
    last_message_timestamp: Optional[str]


class Conversation(BaseModel):
    id: str
    kapso: ConversationKapso
    status: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    contact_name: Optional[str]
    phone_number: str
    last_active_at: str
    phone_number_id: str


# =========================================================
# Data wrapper inside "data": [...]
# =========================================================

class WebhookDataItem(BaseModel):
    message: Message
    conversation: Conversation
    phone_number_id: str
    is_new_conversation: bool


# =========================================================
# Batch info
# =========================================================

class BatchInfo(BaseModel):
    size: int
    window_ms: int
    last_sequence: int
    first_sequence: int
    conversation_id: Optional[str]


# =========================================================
# Root Payload
# =========================================================

class WebhookPayload(BaseModel):
    data: List[WebhookDataItem]
    type: str
    batch: bool
    batch_info: BatchInfo
