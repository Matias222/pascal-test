import os, json

from app.models import api_models
from app.auxiliares import print_info_api_call, retry_on_failure
from dotenv import load_dotenv
from httpx import AsyncClient, Response, Timeout
from fastapi import HTTPException

load_dotenv()

timeout = Timeout(20.0)

API_DB = os.getenv('API_DB')
SETUP = os.getenv('SETUP')

print(API_DB)

@retry_on_failure()
async def leer_lead(user_phone: str) -> tuple[dict, int]:
    """
    Lee un lead por número de teléfono
    Returns: (lead_json, status_code)
    """
    async with AsyncClient(timeout=timeout) as client:
        response = await client.get(f"{API_DB}/db_api/leads/phone/{user_phone}")
        print(response)
        print_info_api_call(response)
        return response.json(), response.status_code


@retry_on_failure()
async def crear_lead(user_phone: str, name: str = None, email: str = None) -> tuple[dict, int]:
    """
    Crea un nuevo lead
    """
    async with AsyncClient(timeout=timeout) as client:
        payload = {
            "phone": user_phone,
            "name": name,
            "email": email
        }
        response = await client.post(f"{API_DB}/db_api/leads/create", json=payload)
        print_info_api_call(response)
        return response.json(), response.status_code

@retry_on_failure()
async def crear_cita(api_state:api_models.ApiState) -> tuple[dict, int]:
    """
    Crea una cita
    """
    async with AsyncClient(timeout=timeout) as client:
        # Convertir datetime a string ISO 8601 si es necesario
        scheduled_for_str = api_state.lead.cita.scheduled_for
        if hasattr(scheduled_for_str, 'isoformat'):
            scheduled_for_str = scheduled_for_str.isoformat()

        payload = {
            "lead_id": api_state.lead.id,
            "conversation_id": api_state.conversa.id,
            "project_id": api_state.lead.cita.project_id,
            "scheduled_for": scheduled_for_str
        }

        # Agregar property_id solo si existe (es opcional)
        if api_state.lead.cita.property_id:
            payload["property_id"] = api_state.lead.cita.property_id

        response = await client.post(f"{API_DB}/db_api/appointments/create", json=payload)
        print_info_api_call(response)
        return response.json(), response.status_code

@retry_on_failure()
async def leer_mensajes(lead_id: str, limit: int = 6) -> tuple[dict, int]:
    """
    Lee los últimos k mensajes de un lead
    Returns: (mensajes_json, status_code)
    """
    async with AsyncClient(timeout=timeout) as client:
        response = await client.get(f"{API_DB}/db_api/messages/lead/{lead_id}?limit={limit}")
        print_info_api_call(response)
        return response.json(), response.status_code


@retry_on_failure()
async def crear_mensaje(conversation_id: str, message_type: str, content: str) -> tuple[dict, int]:
    """
    Crea un nuevo mensaje en una conversación
    message_type: 'human' o 'ai-assistant'
    """
    async with AsyncClient(timeout=timeout) as client:
        payload = {
            "conversation_id": conversation_id,
            "type": message_type,
            "content": content
        }
        response = await client.post(f"{API_DB}/db_api/messages/create", json=payload)
        print_info_api_call(response)
        return response.json(), response.status_code


@retry_on_failure()
async def crear_conversacion(lead_id: str) -> tuple[dict, int]:
    """
    Crea una nueva conversación para un lead
    """
    async with AsyncClient(timeout=timeout) as client:
        payload = {
            "lead_id": lead_id,
            "is_answered_by_lead": False
        }
        response = await client.post(f"{API_DB}/db_api/conversations/create", json=payload)
        print_info_api_call(response)
        return response.json(), response.status_code


@retry_on_failure()
async def leer_ultima_conversacion(lead_id: str) -> tuple[dict, int]:
    """
    Lee la última conversación de un lead (la más reciente por last_message_at)
    """
    async with AsyncClient(timeout=timeout) as client:
        response = await client.get(f"{API_DB}/db_api/conversations/lead/{lead_id}/latest")
        print_info_api_call(response)
        return response.json(), response.status_code


@retry_on_failure()
async def actualizar_lead(lead: api_models.Lead) -> tuple[dict, int]:
    """
    Actualiza un lead existente con toda su información.

    Args:
        lead: Objeto Lead con toda la información actualizada

    Returns:
        tuple: (lead_json, status_code)
    """
    async with AsyncClient(timeout=timeout) as client:
        payload = {
            "name": lead.name,
            "email": lead.email,
            "phone": lead.phone,
            "estado_agentico": lead.estado_agentico
        }

        # Filtrar valores None para no sobrescribir con nulls
        payload = {k: v for k, v in payload.items() if v is not None}

        response = await client.put(f"{API_DB}/db_api/leads/{lead.id}/update", json=payload)
        print_info_api_call(response)
        return response.json(), response.status_code


@retry_on_failure()
async def actualizar_conversation(conversa: api_models.Conversation) -> tuple[dict, int]:
    """
    Actualiza una conversa existente con toda su información.

    Args:
        conversa: Objeto Conversation con toda la información actualizada

    Returns:
        tuple: (lead_json, status_code)
    """
    async with AsyncClient(timeout=timeout) as client:
        payload = {
            "most_recent_project_id": conversa.most_recent_project_id,
            "funciones_empleadas": conversa.funciones
        }

        # Filtrar valores None para no sobrescribir con nulls
        payload = {k: v for k, v in payload.items() if v is not None}

        response = await client.put(f"{API_DB}/db_api/conversations/{conversa.id}/update", json=payload)
        print_info_api_call(response)
        return response.json(), response.status_code


@retry_on_failure()
async def leer_ultima_cita(lead_id: str) -> tuple[dict, int]:
    """
    Lee la última cita de un lead (la más reciente por scheduled_for)

    Args:
        lead_id: ID del lead

    Returns:
        tuple: (appointment_json, status_code)
    """
    async with AsyncClient(timeout=timeout) as client:
        response = await client.get(f"{API_DB}/db_api/appointments/lead/{lead_id}/latest")
        print_info_api_call(response)
        return response.json(), response.status_code
