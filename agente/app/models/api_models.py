from collections import deque
from datetime import datetime, time, date
from typing import Literal
from fastapi import WebSocket, BackgroundTasks
from pydantic import BaseModel, Field
from enum import Enum

class TipoEstado(str,Enum):
    ORQUESTADOR = "orquestador" 
    BUSCADOR = "buscador"
    AGENDADOR = "agendador"

class TipoChat(str, Enum):
    AI = "ai-assistant"
    HUMANO = "human"

class AIResponse(BaseModel):
    respuesta_al_lead: str
    razonamiento: str | None

class Chat(BaseModel):
    tipo: TipoChat 
    blob: str|AIResponse

class Appointment(BaseModel):
    project_id : str
    property_id : str|None=None
    scheduled_for : datetime

class Lead(BaseModel):
    id: str | None = None
    phone: str
    name: str | None = None
    email: str | None = None
    estado_agentico: str|None = None
    buffer: list[Chat] | None = Field(default_factory=list)
    cita: Appointment|None = None

class Conversation(BaseModel):

    id:str
    most_recent_project_id: str|None
    funciones: list = []

class Ejecucion(BaseModel):
    mensaje: str
    claude_respuestas: list[dict] = Field(default_factory=list)

class ApiState(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    lead: Lead | None
    ejecucion: Ejecucion | None
    conversa: Conversation | None

class Request(BaseModel):
    message: str
    user_phone: str
