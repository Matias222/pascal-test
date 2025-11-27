from collections import deque
from datetime import datetime, time, date
from typing import Literal, Callable, Any, Awaitable
from fastapi import WebSocket, BackgroundTasks
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

class Agente(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    messages: list = [{}]
    funciones: list = []
    temperatura: float = 0.3
    tipo_funciones: str = "auto"
    tools: list = []
    timeout_seconds: int = 30
    modelo_principal: str = ""
    modelo_backup: str = ""
    sistema: str = ""
    ejecucion: Callable[..., Awaitable[str]] | None = None

class Response(BaseModel):

    respuesta_final_usuario: str=Field("Respuesta final al usuario")
    razonamiento: str=Field("Razonamiento justificando la respuesta")