from app.api_calls import db_api
from app.models import api_models
from fastapi import HTTPException
import asyncio


async def guardar_conversacion_y_mensajes(api_state: api_models.ApiState):
    """
    Guarda la conversación y los mensajes en la base de datos.

    1. Verifica si existe una conversación activa (hace una nueva call a DB)
    2. Si no existe, crea una nueva conversación
    3. Guarda los dos últimos mensajes del buffer (humano + AI) en paralelo

    Args:
        api_state: Estado actual de la API con lead, ejecución y conversación

    Returns:
        api_state actualizado con la conversación
    """

    lead = api_state.lead

    # =========================================================
    # 1. GUARDAR MENSAJES DEL BUFFER EN DB
    # =========================================================

    # Verificar que haya al menos 2 mensajes (humano + AI)
    if len(lead.buffer) < 2:
        print("Buffer insuficiente, no hay mensajes para guardar")
        return api_state

    # El penúltimo es el mensaje del humano, el último es la respuesta de AI
    mensaje_humano = lead.buffer[-2]
    mensaje_ai = lead.buffer[-1]

    # Guardar mensaje del usuario PRIMERO (secuencial)
    contenido_humano = mensaje_humano.blob if isinstance(mensaje_humano.blob, str) else str(mensaje_humano.blob)

    msg_humano_response, msg_humano_status = await db_api.crear_mensaje(
        conversation_id=api_state.conversa.id,
        message_type="human",
        content=contenido_humano
    )

    if msg_humano_status == 201:
        print(f"✅ Mensaje humano guardado exitosamente (ID: {msg_humano_response.get('id')})")
    else:
        print(f"⚠️ Error al guardar mensaje humano: status {msg_humano_status}")

    # Guardar mensaje de la AI DESPUÉS (secuencial)
    if isinstance(mensaje_ai.blob, api_models.AIResponse):
        contenido_ai = mensaje_ai.blob.respuesta_al_lead
    else:
        contenido_ai = str(mensaje_ai.blob)

    msg_ai_response, msg_ai_status = await db_api.crear_mensaje(
        conversation_id=api_state.conversa.id,
        message_type="ai-assistant",
        content=contenido_ai
    )

    if msg_ai_status == 201:
        print(f"✅ Mensaje AI guardado exitosamente (ID: {msg_ai_response.get('id')})")
    else:
        print(f"⚠️ Error al guardar mensaje AI: status {msg_ai_status}")

    # =========================================================
    # 3. ACTUALIZAR LEAD CON TODA LA INFORMACIÓN
    # =========================================================

    print("Actualizando lead en DB...")
    lead_actualizado_json, update_status = await db_api.actualizar_lead(lead)

    if update_status == 200: print(f"✅ Lead actualizado exitosamente (ID: {lead.id})")
    else: print(f"⚠️ Error al actualizar lead: status {update_status}")

    conversa_actualizado_json, update_status = await db_api.actualizar_conversation(api_state.conversa)

    if update_status == 200: print(f"✅ Conversa actualizado exitosamente (ID: {api_state.conversa.id})")
    else: print(f"⚠️ Error al actualizar conversa: status {update_status}")

    return api_state
