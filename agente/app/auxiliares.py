import json
import re
import asyncio
import xml.etree.ElementTree as ET
import app.models.api_models as api_models

from httpx import Response
from datetime import datetime, timedelta
from rapidfuzz import process
from tenacity import retry, stop_after_attempt, wait_fixed
import pytz

peru_tz=pytz.timezone("America/Lima")

def print_info_api_call(response:Response):

    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

def excluir_buffer_schedules(obj):
    data = {key: value for key, value in obj.__dict__.items() if (key != 'buffer')}    
    return data

def retry_on_failure(): #Retryes en toda las calls que requieran network

  return retry(stop=stop_after_attempt(2), wait=wait_fixed(5))

def datetime_peru():
    
    peru_time = datetime.now(peru_tz)

    return peru_time.isoformat()

def dia_semana(peru_time:str="Default"):

    if(peru_time=="Default"): peru_time = datetime.now(peru_tz)
    else:  peru_time=datetime.strptime(peru_time, "%Y-%m-%d").date()

    weekday_number = peru_time.weekday()

    days_in_spanish = {
        0: "Lunes",
        1: "Martes",
        2: "Miercoles",
        3: "Jueves",
        4: "Viernes",
        5: "Sabado",
        6: "Domingo"
    }
    
    return days_in_spanish[weekday_number]

def _formatear_historial(buffer: list[api_models.Chat]) -> str:
    """
    Formatea el historial de conversación de manera legible para Claude.

    Args:
        buffer: Lista de mensajes Chat

    Returns:
        String formateado con el historial
    """
    if not buffer or len(buffer) == 0:
        return "No hay historial previo. Este es el primer mensaje del usuario."

    historial_texto = []

    for chat in buffer[:-1]:  # Excluimos el último mensaje (es el actual)
        if chat.tipo == api_models.TipoChat.HUMANO:
            historial_texto.append(f"Usuario: {chat.blob}")
        elif chat.tipo == api_models.TipoChat.AI: historial_texto.append(f"Carla: {chat.blob.respuesta_al_lead}")

    return "\n\n".join(historial_texto)

def revisar_existe_respuesta(api_state:api_models.ApiState):

    for i in api_state.ejecucion.claude_respuestas:

        if(i["respuesta_al_paciente"]!="" or i["respuesta_doctor"]!=""): return True

    return False