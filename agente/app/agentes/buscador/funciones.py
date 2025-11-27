from app.models import api_models, agent_models
from app import auxiliares, agents_main
from app.api_calls import busquedas
import json, asyncio

# =========================================================
# TOOLS PARA EL AGENTE BUSCADOR
# =========================================================

tools = [
    {
        "name": "busqueda_semantica_proyectos",
        "description": """Realiza una búsqueda semántica de PROYECTOS inmobiliarios usando embeddings (RAG).

IMPORTANTE: Esta debe ser la PRIMERA herramienta que uses cuando el usuario exprese interés en buscar propiedades. El flujo de búsqueda SIEMPRE comienza con proyectos.

Es ideal cuando el usuario describe lo que busca de manera natural o abstracta.

Casos de uso:
- "Busco algo moderno y luminoso"
- "Proyectos en zonas exclusivas"
- "Algo tranquilo para familia"
- "Edificios nuevos con buenas amenidades"

La búsqueda usa inteligencia artificial para encontrar proyectos similares semánticamente a la descripción del usuario.

Returns: Lista de proyectos ordenados por relevancia semántica.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Descripción natural de lo que busca el usuario."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "busqueda_semantica_propiedades",
        "description": """Realiza una búsqueda semántica de PROPIEDADES individuales usando embeddings (RAG).

IMPORTANTE: Solo usa esta herramienta como APOYO cuando:
1. El usuario ya seleccionó un proyecto Y quiere refinar la búsqueda dentro de ese proyecto
2. El usuario busca una propiedad MUY específica desde el inicio (ej: "el depa 301 del edificio X")

En caso 2, debes obtener el proyecto de esa propiedad y llamar a seleccionar_proyecto automáticamente.

Casos de uso secundarios:
- "Dentro del proyecto X, busco algo con vista"
- "El departamento 503 que vimos antes"
- "La propiedad específica en piso 12"

Returns: Lista de propiedades ordenadas por relevancia semántica.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Descripción de la propiedad específica que busca."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "obtener_informacion_proyecto",
        "description": """Obtiene toda la información de un proyecto específico, incluyendo TODAS sus propiedades disponibles.

Usa esta herramienta cuando:
1. El usuario quiere ver las propiedades de un proyecto específico
2. El usuario pregunta "qué propiedades tiene el proyecto X?"
3. Necesitas mostrar información detallada de un proyecto antes de que el usuario decida

Esta herramienta:
- Obtiene todas las propiedades del proyecto
- Retorna información completa para presentar al usuario
- NO modifica el contexto de la conversación (solo lectura)

IMPORTANTE: Esta herramienta es solo para CONSULTAR información. Para marcar un proyecto como seleccionado, usa seleccionar_proyecto después.

Ejemplos de uso:
- Usuario: "Qué propiedades tiene el Ocean View?" → obtener_informacion_proyecto
- Usuario: "Muéstrame las unidades del primer proyecto" → obtener_informacion_proyecto
- Usuario: "Cuánto cuestan los depas del Sky Tower?" → obtener_informacion_proyecto""",
        "input_schema": {
            "type": "object",
            "properties": {
                "proyecto_id": {
                    "type": "string",
                    "description": "ID del proyecto (UUID)"
                },
                "proyecto_nombre": {
                    "type": "string",
                    "description": "Nombre del proyecto para referencia"
                }
            },
            "required": ["proyecto_id", "proyecto_nombre"]
        }
    },
    {
        "name": "seleccionar_proyecto",
        "description": """MARCA un proyecto como SELECCIONADO en el contexto de la conversación.

CRÍTICO: Esta herramienta es OBLIGATORIA antes de que el usuario pueda pasar al agente AGENDADOR.

Usa esta herramienta cuando:
1. El usuario confirma que quiere ese proyecto ("me interesa", "quiero ese", "vamos con el Ocean View")
2. El usuario está listo para agendar una visita a un proyecto específico
3. El usuario ha visto las propiedades y decidió que le gusta el proyecto

Esta herramienta:
- Guarda el proyecto_id en el contexto (most_recent_project_id)
- NO retorna propiedades (usa obtener_informacion_proyecto para eso)
- Es un paso de confirmación/selección

FLUJO CORRECTO:
1. Mostrar proyectos → busqueda_semantica_proyectos
2. Usuario elige uno → obtener_informacion_proyecto (para ver propiedades)
3. Usuario confirma interés → seleccionar_proyecto (marcar como seleccionado)
4. Usuario quiere agendar → cambiar_flujo_agente a AGENDADOR

Ejemplos de uso:
- Usuario: "Me interesa el Ocean View, quiero agendar" → seleccionar_proyecto + cambiar_flujo_agente
- Usuario: "Sí, vamos con ese proyecto" → seleccionar_proyecto
- Usuario: "Perfecto, ese me gusta" → seleccionar_proyecto""",
        "input_schema": {
            "type": "object",
            "properties": {
                "proyecto_id": {
                    "type": "string",
                    "description": "ID del proyecto seleccionado (UUID)"
                },
                "proyecto_nombre": {
                    "type": "string",
                    "description": "Nombre del proyecto para referencia"
                }
            },
            "required": ["proyecto_id", "proyecto_nombre"]
        }
    },
    {
        "name": "filtrar_propiedades",
        "description": """Filtra propiedades por criterios específicos y estructurados.

Usa esta herramienta cuando el usuario mencione características específicas medibles:

Filtros disponibles:
- num_bedrooms: Número de habitaciones (int)
- num_bathrooms: Número de baños (int)
- min_price: Precio mínimo en USD (int)
- max_price: Precio máximo en USD (int)
- property_type: Tipo de propiedad ("departamento", "casa", "oficina", etc.)
- floor_no: Número de piso (str, ej: "5", "10-15")
- view_type: Tipo de vista (str, ej: "mar", "ciudad", "parque")
- search: Búsqueda de texto en título y descripción (str)

Ejemplos de uso:
- "Busco 3 habitaciones y 2 baños" → num_bedrooms=3, num_bathrooms=2
- "Entre 100 mil y 200 mil dólares" → min_price=100000, max_price=200000
- "Departamento en piso alto" → property_type="departamento", search="piso alto"

IMPORTANTE: Solo incluye los filtros que el usuario mencionó explícitamente.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "num_bedrooms": {
                    "type": "integer",
                    "description": "Número de habitaciones"
                },
                "num_bathrooms": {
                    "type": "integer",
                    "description": "Número de baños"
                },
                "min_price": {
                    "type": "integer",
                    "description": "Precio mínimo en USD"
                },
                "max_price": {
                    "type": "integer",
                    "description": "Precio máximo en USD"
                },
                "property_type": {
                    "type": "string",
                    "description": "Tipo de propiedad (departamento, casa, oficina, etc.)"
                },
                "floor_no": {
                    "type": "string",
                    "description": "Número de piso o rango de pisos"
                },
                "view_type": {
                    "type": "string",
                    "description": "Tipo de vista (mar, ciudad, parque, etc.)"
                },
                "search": {
                    "type": "string",
                    "description": "Búsqueda de texto libre en título y descripción"
                }
            },
            "required": []
        }
    },
    {
        "name": "cambiar_flujo_agente",
        "description": """Cambia el flujo de conversación a otro agente especializado.

Usa esta herramienta cuando:

- AGENDADOR: El usuario quiere agendar una visita, programar cita, o preguntar disponibilidad.
  Ejemplos: "Quiero agendar una visita", "Puedo ir el sábado?", "Cuando puedo visitarlos?"

- ORQUESTADOR: El usuario hace preguntas generales no relacionadas con búsqueda de propiedades.
  Ejemplos: "Qué servicios tienen?", "Cómo funciona esto?", "Quiero hablar de otra cosa"

IMPORTANTE: NO uses esta herramienta si el usuario sigue buscando propiedades o preguntando por características.""",
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

    if tool_name == "busqueda_semantica_proyectos":
    
        query = function_args.get("query")

        proyectos_data, proyectos_status = await busquedas.buscar_proyectos_semantica(query)

        if proyectos_status == 200:
            print(f"Proyectos encontrados: {len(proyectos_data)}")

            response = json.dumps({
                "status": "success",
                "query": query,
                "total": len(proyectos_data),
                "proyectos": proyectos_data,
                "instruccion": "Presenta estos proyectos al usuario y pídele que seleccione uno para explorar sus propiedades."
            }, ensure_ascii=False)
        else:
            print(f"Error en búsqueda de proyectos: {proyectos_status}")
            response = json.dumps({
                "status": "error",
                "mensaje": f"Error en búsqueda de proyectos (status: {proyectos_status})"
            }, ensure_ascii=False)

    elif tool_name == "busqueda_semantica_propiedades": # Búsqueda semántica SOLO de propiedades (apoyo)

        query = function_args.get("query")

        propiedades_data, propiedades_status = await busquedas.buscar_propiedades_semantica(query)

        if propiedades_status == 200:
            print(f"Propiedades encontradas: {len(propiedades_data)}")

            response = json.dumps({
                "status": "success",
                "query": query,
                "total": len(propiedades_data),
                "propiedades": propiedades_data,
                "instruccion": "Si estas propiedades pertenecen a proyectos y no hay proyecto seleccionado, debes identificar el proyecto y usar seleccionar_proyecto."
            }, ensure_ascii=False)
        else:
            print(f"Error en búsqueda de propiedades: {propiedades_status}")
            response = json.dumps({
                "status": "error",
                "mensaje": f"Error en búsqueda de propiedades (status: {propiedades_status})"
            }, ensure_ascii=False)

    elif tool_name == "obtener_informacion_proyecto":

        proyecto_id = function_args.get("proyecto_id")
        proyecto_nombre = function_args.get("proyecto_nombre")

        propiedades_data, propiedades_status = await busquedas.obtener_propiedades_por_proyecto(proyecto_id)

        if propiedades_status == 200:
            print(f"Propiedades encontradas para {proyecto_nombre}: {len(propiedades_data)}")

            response = json.dumps({
                "status": "success",
                "proyecto_id": proyecto_id,
                "proyecto_nombre": proyecto_nombre,
                "total_propiedades": len(propiedades_data),
                "propiedades": propiedades_data,
                "mensaje": f"Información del proyecto '{proyecto_nombre}' obtenida. Presenta las {len(propiedades_data)} propiedades al usuario mostrando 3-4 ejemplos destacados. IMPORTANTE: Si el usuario confirma interés en este proyecto, debes usar seleccionar_proyecto antes de cambiar a AGENDADOR."
            }, ensure_ascii=False)
        else:
            print(f"Error al obtener propiedades: {propiedades_status}")
            response = json.dumps({
                "status": "error",
                "proyecto_id": proyecto_id,
                "proyecto_nombre": proyecto_nombre,
                "total_propiedades": 0,
                "propiedades": [],
                "mensaje": f"No se pudieron obtener las propiedades del proyecto '{proyecto_nombre}' en este momento."
            }, ensure_ascii=False)

    elif tool_name == "seleccionar_proyecto":

        proyecto_id = function_args.get("proyecto_id")
        proyecto_nombre = function_args.get("proyecto_nombre")

        # SOLO setea el proyecto_id en el contexto, NO obtiene propiedades
        api_state.conversa.most_recent_project_id = proyecto_id

        print(f"✅ Proyecto '{proyecto_nombre}' SELECCIONADO (ID: {proyecto_id})")

        response = json.dumps({
            "status": "success",
            "proyecto_id": proyecto_id,
            "proyecto_nombre": proyecto_nombre,
            "mensaje": f"Proyecto '{proyecto_nombre}' ha sido marcado como seleccionado. El usuario ahora puede pasar al agente AGENDADOR para programar su visita."
        }, ensure_ascii=False)

    elif tool_name == "filtrar_propiedades":
        # Filtrado de propiedades por criterios
        filtros = {k: v for k, v in function_args.items() if v is not None}

        resultados, status_code = await busquedas.filtrar_propiedades(filtros)

        if status_code == 200:
            print(f"✅ Encontradas {len(resultados)} propiedades")

            response = json.dumps({
                "status": "success",
                "filtros": filtros,
                "total": len(resultados),
                "propiedades": resultados
            }, ensure_ascii=False)
        else:
            response = json.dumps({
                "status": "error",
                "mensaje": f"Error en filtrado (status: {status_code})"
            }, ensure_ascii=False)

    elif tool_name == "cambiar_flujo_agente":
        # Cambio de agente
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
