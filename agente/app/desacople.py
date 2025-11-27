from app import agents_main, agregados
from app.api_calls import db_api, whatsapp

from fastapi import HTTPException
import json
import asyncio
import traceback

from app.models import api_models


async def principal(user_phone: str, mensaje: str):

    """
    Flujo principal del agente inmobiliario
    1. Leer/crear lead
    2. Leer historial de mensajes
    3. Procesar mensaje y generar respuesta
    4. Guardar mensaje
    """

    try:
                
        lead_json, status_code = await db_api.leer_lead(user_phone)

        lead = api_models.Lead(phone=user_phone)
        ejecucion = api_models.Ejecucion(mensaje=mensaje)
        conversacion = None

        if status_code == 200:

            lead.id = lead_json["id"]
            lead.name = lead_json.get("name")
            lead.email = lead_json.get("email")
            lead.estado_agentico = lead_json.get("estado_agentico")

            print(f"Lead encontrado: {lead.name} ({lead.phone})")

            tasks = []
            tasks.append(asyncio.create_task(db_api.leer_mensajes(lead.id)))
            tasks.append(asyncio.create_task(db_api.leer_ultima_conversacion(lead.id)))
            tasks.append(asyncio.create_task(db_api.leer_ultima_cita(lead.id)))


            mensajes_response, msg_status = await tasks[0]
            conversacion_response, conv_status = await tasks[1]
            cita_response, cita_status = await tasks[2]

            if conv_status == 200:
                conversacion = api_models.Conversation(
                    id=conversacion_response["id"],
                    most_recent_project_id=conversacion_response.get("most_recent_project_id"),
                    funciones=conversacion_response.get("funciones_empleadas")
                )
                print(f"Conversación encontrada: {conversacion.id}")

            if msg_status == 200:

                mensajes_json = mensajes_response.get("messages", [])

                for msg in reversed(mensajes_json):
                    if msg["type"] == "human":
                        lead.buffer.append(api_models.Chat(tipo=api_models.TipoChat.HUMANO, blob=msg["content"]))
                    elif msg["type"] == "ai-assistant":
                        lead.buffer.append(api_models.Chat(
                            tipo=api_models.TipoChat.AI,
                            blob=api_models.AIResponse(
                                respuesta_al_lead=msg["content"],
                                razonamiento=None,
                                herramientas_usadas=None
                            )
                        ))

            if cita_status == 200:
                lead.cita = api_models.Appointment(
                    project_id=cita_response.get("project_id"),
                    property_id=cita_response.get("property_id"),
                    scheduled_for=cita_response.get("scheduled_for")
                )
                print(f"Cita encontrada: {lead.cita.scheduled_for}")

        elif status_code == 404:
            
            print(f"Lead no encontrado, creando nuevo: {user_phone}")
            new_lead_json, create_status = await db_api.crear_lead(user_phone)

            if create_status == 201:
                lead.id = new_lead_json["id"]
                lead.name = new_lead_json.get("name")
                lead.email = new_lead_json.get("email")
                lead.estado_agentico = new_lead_json.get("estado_agentico")

            else:
                raise HTTPException(status_code=500, detail="Error al crear lead")
                
            new_conversation_json, conv_create_status = await db_api.crear_conversacion(lead.id)

            if conv_create_status == 201:
                conversacion = api_models.Conversation(
                    id=new_conversation_json["id"],
                    most_recent_project_id=new_conversation_json.get("most_recent_project_id")
                )
            else:
                raise HTTPException(status_code=500, detail="Error al crear conversa")
            
        lead.buffer.append(api_models.Chat(tipo=api_models.TipoChat.HUMANO, blob=mensaje))

        api_state = api_models.ApiState(lead=lead, ejecucion=ejecucion, conversa=conversacion)
        
        print("=" * 50)
        print(api_state)
        print(f"Lead: {api_state.lead.name or 'Sin nombre'} - {api_state.lead.phone}")
        print(f"Mensaje: {api_state.ejecucion.mensaje}")
        print(f"Buffer size: {len(api_state.lead.buffer)}")
        print("=" * 50)

        await agents_main.carla(api_state)

        await whatsapp.enviar_mensaje(api_state)
    
        await agregados.guardar_conversacion_y_mensajes(api_state)

        return api_state

    except Exception as e:
        print(f"Error en principal: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
