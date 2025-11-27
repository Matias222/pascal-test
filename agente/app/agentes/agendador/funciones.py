from app.models import api_models, agent_models
from app import auxiliares, agents_main
from app.api_calls import db_api, busquedas
import json

# =========================================================
# TOOLS PARA EL AGENTE AGENDADOR
# =========================================================

tools = [
    {
        "name": "buscar_propiedades_proyecto",
        "description": """Obtiene todas las propiedades disponibles de un proyecto específico.

Usa esta herramienta cuando:
1. El usuario menciona una propiedad específica que quiere visitar (ej: "quiero ver el depa 301")
2. Necesitas identificar el property_id de una propiedad mencionada por el usuario
3. El usuario quiere ver qué propiedades están disponibles en un proyecto antes de agendar

IMPORTANTE: Usa esta tool cuando el usuario mencione una propiedad específica para extraer su property_id.

Ejemplos de uso:
- Usuario: "Quiero agendar visita al depa 301" → Usar buscar_propiedades_proyecto para encontrar el property_id del depa 301
- Usuario: "Me interesa visitar la propiedad del piso 5" → Buscar propiedades y filtrar por descripción/piso
- Usuario: "Qué propiedades tiene el Ocean View?" → Mostrar todas las propiedades del proyecto

Returns: Lista de todas las propiedades del proyecto con sus IDs, nombres, características.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "ID del proyecto (UUID)"
                }
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "realizar_agenda",
        "description": """Agenda una cita/visita para el lead a un proyecto inmobiliario.

Esta herramienta se usa cuando el usuario quiere agendar una visita.

IMPORTANTE: Antes de agendar, DEBES tener OBLIGATORIAMENTE:
1. project_id - ID del proyecto (si el usuario ya seleccionó uno, estará en api_state.conversa.most_recent_project_id)
2. scheduled_for - Fecha y hora de la cita en formato ISO 8601
3. nombre - Nombre completo del usuario
4. email - Correo electrónico del usuario

OPCIONAL:
- property_id - ID de la propiedad específica (solo si el usuario mencionó una propiedad en particular)

Si el usuario menciona una propiedad específica (ej: "quiero ver el depa 301"), primero usa buscar_propiedades_proyecto para obtener su property_id.

Si el usuario solo quiere visitar el proyecto en general sin especificar propiedad, NO necesitas property_id.

Si falta información, pregunta al usuario:
- Sin proyecto: "¿A qué proyecto te gustaría agendar la visita?"
- Sin fecha/hora: "¿Qué día y hora te gustaría agendar?"
- Sin nombre: "¿Cuál es tu nombre completo?"
- Sin email: "¿Cuál es tu correo electrónico?"

IMPORTANTE: Siempre pregunta por nombre y email antes de agendar, a menos que ya estén en api_state.lead.name y api_state.lead.email.

Ejemplos de uso:
- Usuario: "Quiero visitar el Ocean View el sábado a las 3pm" → Solo project_id + scheduled_for + nombre + email
- Usuario: "Agendar visita al depa 301 del Ocean View el lunes 10am" → Usar buscar_propiedades_proyecto primero, luego realizar_agenda con property_id
- Usuario: "Quiero conocer el proyecto mañana a las 2pm" → Solo project_id + scheduled_for + nombre + email

Returns: Confirmación de la cita agendada con ID y detalles.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "ID del proyecto (UUID)"
                },
                "property_id": {
                    "type": "string",
                    "description": "ID de la propiedad a visitar (UUID). OPCIONAL: solo incluir si el usuario especificó una propiedad en particular."
                },
                "scheduled_for": {
                    "type": "string",
                    "description": "Fecha y hora de la cita en formato ISO 8601 (ej: '2024-03-15T15:00:00')"
                },
                "nombre": {
                    "type": "string",
                    "description": "Nombre completo del usuario"
                },
                "email": {
                    "type": "string",
                    "description": "Correo electrónico del usuario"
                }
            },
            "required": ["project_id", "scheduled_for", "nombre", "email"]
        }
    },
    {
        "name": "cambiar_flujo_agente",
        "description": """Cambia el flujo de conversación a otro agente especializado.

Usa esta herramienta cuando:

- BUSCADOR: El usuario quiere buscar propiedades o proyectos.
  Ejemplos: "Quiero ver departamentos", "Busco algo en Miraflores", "Qué propiedades tienen?"

- ORQUESTADOR: El usuario hace preguntas generales o quiere información no relacionada con agendar.
  Ejemplos: "Qué servicios tienen?", "Cómo funciona esto?", "Quiero saber más de Pascal"

IMPORTANTE: NO uses esta herramienta si el usuario sigue discutiendo temas de agendamiento (horarios, disponibilidad, cambios de cita).""",
        "input_schema": {
            "type": "object",
            "properties": {
                "nuevo_estado": {
                    "type": "string",
                    "enum": [estado.value for estado in api_models.TipoEstado],
                    "description": "El tipo de agente al que se debe cambiar el flujo"
                },
                "razonamiento": {
                    "type": "string",
                    "description": "Breve explicación de por qué se está cambiando a este agente"
                }
            },
            "required": ["nuevo_estado", "razonamiento"]
        }
    }
]


# =========================================================
# EJECUCIÓN DE TOOLS
# =========================================================

async def ejecucion(api_state: api_models.ApiState, agente: agent_models.Agente, function_args: dict, tool_name: str):

    response = None

    if tool_name == "buscar_propiedades_proyecto":

        project_id = function_args.get("project_id")

        propiedades_data, propiedades_status = await busquedas.obtener_propiedades_por_proyecto(project_id)

        if propiedades_status == 200:

            response = json.dumps({
                "status": "success",
                "project_id": project_id,
                "total_propiedades": len(propiedades_data),
                "propiedades": propiedades_data,
                "mensaje": f"Encontradas {len(propiedades_data)} propiedades en el proyecto. Si el usuario mencionó una propiedad específica, identifica su property_id de esta lista para usarlo en realizar_agenda."
            }, ensure_ascii=False)
        else:
            response = json.dumps({
                "status": "error",
                "mensaje": f"No se pudieron obtener las propiedades del proyecto (status: {propiedades_status})"
            }, ensure_ascii=False)

    elif tool_name == "realizar_agenda":

        project_id = function_args.get("project_id")
        property_id = function_args.get("property_id")
        scheduled_for = function_args.get("scheduled_for")
        nombre = function_args.get("nombre")
        email = function_args.get("email")

        # Actualizar información del lead
        api_state.lead.name = nombre
        api_state.lead.email = email

        api_state.lead.cita=api_models.Appointment(project_id=project_id,property_id=property_id,scheduled_for=scheduled_for)

        appointment_result, status_code = await db_api.crear_cita(api_state)

        if status_code == 201:
            response = json.dumps({
                "status": "success",
                "appointment_id": appointment_result.get("id"),
                "project_id": project_id,
                "property_id": property_id,
                "scheduled_for": scheduled_for,
                "mensaje": f"Cita agendada exitosamente para {scheduled_for}. Confirmale al usuario la visita."
            }, ensure_ascii=False)

            #Ya se cerro un flujo, la conversacion a partir de ahora es nueva
            nueva_conversacion_json, nueva_conv_status = await db_api.crear_conversacion(api_state.lead.id)

            if nueva_conv_status == 201: print(f"✅ Nueva conversación creada (ID: {nueva_conversacion_json.get('id')})")
                

        else:
            response = json.dumps({
                "status": "error",
                "mensaje": f"Hubo un problema al agendar la cita (status: {status_code}). Pide al usuario que intente nuevamente o contacte soporte."
            }, ensure_ascii=False)

    elif tool_name == "cambiar_flujo_agente":

        api_state.lead.estado_agentico = function_args["nuevo_estado"]

        agents_main.asignacion(api_state, agente)
        response = json.dumps({
            "status": "success",
            "mensaje": f"Cambio exitoso a {api_state.lead.estado_agentico}, continua con el proceso"
        })
        agente.funciones=[] #Cuando cambiamos de agente se reinicia el tool trace

    else:
        raise Exception(f"La IA se equivocó con el nombre de la función: {tool_name}")

    return response
