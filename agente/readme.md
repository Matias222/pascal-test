# Agente Conversacional - Pascal Inmobiliaria

Sistema de agente conversacional multi-agente para asistencia inmobiliaria, construido con FastAPI y Claude AI (Anthropic).

## 🏗️ Arquitectura del Sistema

### Patrón de Orquestación Multi-Agente

El sistema utiliza un **patrón de orquestación** donde múltiples agentes especializados manejan diferentes aspectos de la conversación:

```
┌─────────────────┐
│  ORQUESTADOR    │ ← Agente principal, maneja conversaciones generales
└────────┬────────┘
         │
         ├──────► ┌─────────────┐
         │        │  BUSCADOR   │ ← Búsqueda semántica de proyectos/propiedades
         │        └─────────────┘
         │
         └──────► ┌─────────────┐
                  │  AGENDADOR  │ ← Agendamiento de visitas
                  └─────────────┘
```

**Decisión clave**: Separación por responsabilidad única
- Cada agente tiene un conjunto específico de herramientas (tools)
- Transiciones fluidas entre agentes mediante `cambiar_flujo_agente`
- Estado conversacional compartido a través de `ApiState`

### Estructura de Agentes

Cada agente sigue la misma estructura modular:

```
app/agentes/{nombre_agente}/
├── __init__.py
├── funciones.py      # Definición de tools y ejecución
└── todo.py           # System prompt y user prompt
```

**Componentes de cada agente:**

1. **`funciones.py`**:
   - Lista de `tools` (herramientas disponibles)
   - Función `ejecucion()` que maneja la lógica de cada tool
   - Llamadas a APIs externas (DB, búsquedas, etc.)

2. **`todo.py`**:
   - `sistema_prompt()`: Instrucciones base del agente (siguiendo mejores prácticas de Claude 4.5)
   - `usuario_prompt()`: Contexto dinámico (historial, estado actual, información temporal)
   - Configuración de modelos (principal/backup)

## 🔄 Flujo de Datos y Asincronismo

### Arquitectura Asíncrona

El sistema está completamente construido con `async/await` para maximizar el rendimiento:

```python
async def principal(user_phone: str, mensaje: str):
    # 1. Cargar datos en paralelo
    tasks = [
        db_api.leer_mensajes(lead.id),
        db_api.leer_ultima_conversacion(lead.id),
        db_api.leer_ultima_cita(lead.id)
    ]

    # 2. Procesamiento del agente
    await agents_main.carla(api_state)

    # 3. Guardado asíncrono
    await agregados.guardar_conversacion_y_mensajes(api_state)
```

**Beneficios del asincronismo:**
- Llamadas a API en paralelo cuando no hay dependencias
- Mejor utilización de recursos durante I/O (DB, Claude API)
- Timeouts configurables con retry automático

### Manejo de Estado: `ApiState`

Modelo centralizado que fluye a través de todo el sistema:

```python
class ApiState:
    lead: Lead              # Información del usuario
    ejecucion: Ejecucion    # Mensaje actual y respuestas
    conversa: Conversation  # Contexto conversacional
```

**Decisión arquitectónica**: Single source of truth
- Evita inconsistencias entre componentes
- Facilita el traspaso de información entre agentes
- Simplifica debugging y logging

## 🧠 Gestión de Conversaciones

### Lógica de Conversaciones

```
┌─────────────────────────────────────────────────────────┐
│  Conversación = Contexto de búsqueda/agendamiento      │
│                                                          │
│  • most_recent_project_id: Proyecto en foco            │
│  • funciones: Historial de herramientas usadas         │
└─────────────────────────────────────────────────────────┘
```

**Regla importante**: Las conversaciones se cierran al completar una agenda.

Cuando el agente AGENDADOR ejecuta `realizar_agenda` exitosamente:
1. Se crea la cita en la base de datos
2. **Automáticamente se crea una nueva conversación** (líneas 132-136 en `agendador/funciones.py`)
3. La próxima interacción comienza en una conversación limpia

**Razón**: Separar contextos de búsqueda diferentes. Si el usuario agendó visita al proyecto X, y luego busca proyecto Y, son conversaciones distintas.

### Buffer de Mensajes

```python
lead.buffer: list[Chat]  # Historial completo de mensajes
```

**Decisión clave**: Los últimos K mensajes siempre se cargan, incluso en conversaciones nuevas.

¿Por qué?
- El usuario puede referenciar búsquedas anteriores
- Mantiene contexto humano aunque técnicamente sea nueva conversación
- Permite personalización continua

Ejemplo:
```
Conversación 1:
Usuario: "Busco depa en Miraflores"
Carla: [Muestra proyectos]
Usuario: "Agenda visita al Ocean View"
Carla: [Crea cita] ✅ Nueva conversación creada

Conversación 2 (pero con buffer previo):
Usuario: "Y ese proyecto que vimos antes tenía piscina?"
Carla: [Puede responder porque tiene el buffer de mensajes anteriores]
```

## 🛠️ Agentes Especializados

### 1. ORQUESTADOR

**Responsabilidad**: Punto de entrada, conversaciones generales, ruteo

**Tools**:
- `cambiar_flujo_agente`: Deriva a agentes especializados

**Cuándo se activa**:
- Usuario nuevo (estado por defecto)
- Conversación general no relacionada con búsqueda/agendamiento

### 2. BUSCADOR

**Responsabilidad**: Búsqueda semántica de proyectos y propiedades

**Tools**:
- `busqueda_semantica_proyectos`: RAG sobre proyectos (SIEMPRE primero)
- `seleccionar_proyecto`: Guarda proyecto seleccionado + obtiene todas sus propiedades
- `busqueda_semantica_propiedades`: RAG sobre propiedades (apoyo)
- `filtrar_propiedades`: Filtros estructurados (habitaciones, precio, etc.)
- `cambiar_flujo_agente`: Transición a otros agentes

**Flujo obligatorio** (project-first):
1. Usuario busca → `busqueda_semantica_proyectos`
2. Usuario selecciona proyecto → `seleccionar_proyecto` (auto-fetch de propiedades)
3. Refinar búsqueda → `filtrar_propiedades` o `busqueda_semantica_propiedades`

**Decisión clave**: Búsqueda jerárquica (proyecto → propiedades)
- Los usuarios piensan en ubicaciones/edificios primero, luego en unidades específicas
- Mejora UX al mostrar contexto del proyecto antes de propiedades
- `seleccionar_proyecto` automáticamente trae todas las propiedades (no requiere call adicional del agente)

### 3. AGENDADOR

**Responsabilidad**: Coordinar visitas a propiedades/proyectos

**Tools**:
- `buscar_propiedades_proyecto`: Obtiene propiedades para identificar IDs
- `realizar_agenda`: Crea la cita (requiere: proyecto, fecha/hora, nombre, email)
- `cambiar_flujo_agente`: Transición a otros agentes

**Datos obligatorios**:
- ✅ `project_id`
- ✅ `scheduled_for` (ISO 8601)
- ✅ `nombre`
- ✅ `email`

**Datos opcionales**:
- ⚪ `property_id` (solo si el usuario especificó una propiedad)

**Decisión**: property_id opcional
- Permite agendar visitas generales al proyecto (showroom, tour)
- Si el usuario menciona "quiero ver el depa 301" → usa `buscar_propiedades_proyecto` para obtener el ID
- Si el usuario dice "quiero visitar el Ocean View" → solo `project_id` necesario

**Cierre automático de conversación**:
Cuando `realizar_agenda` tiene éxito, se crea una nueva conversación inmediatamente para comenzar limpio.

## 📦 Modelos de Datos

### Lead (Usuario)

```python
class Lead:
    id: str
    phone: str
    name: str | None
    email: str | None
    estado_agentico: str        # ORQUESTADOR | BUSCADOR | AGENDADOR
    buffer: list[Chat]           # Historial de mensajes
    cita: Appointment | None     # Última cita agendada
```

### Conversation (Contexto de búsqueda)

```python
class Conversation:
    id: str
    most_recent_project_id: str | None  # Proyecto en foco
    funciones: list                      # Tools usadas en esta conversación
```

### Appointment (Cita)

```python
class Appointment:
    id: str
    project_id: str              # Obligatorio
    property_id: str | None      # Opcional
    scheduled_for: datetime      # ISO 8601
```

## 🔌 Integraciones Externas

### APIs Consumidas

1. **API DB** (`db_api.py`):
   - `leer_lead()`, `crear_lead()`, `actualizar_lead()`
   - `leer_mensajes()`, `crear_mensaje()`
   - `leer_ultima_conversacion()`, `crear_conversacion()`, `actualizar_conversation()`
   - `leer_ultima_cita()`, `crear_cita()`

2. **API Búsquedas** (`busquedas.py`):
   - `buscar_proyectos_semantica()`: RAG con embeddings
   - `buscar_propiedades_semantica()`: RAG con embeddings
   - `filtrar_propiedades()`: Filtros estructurados
   - `obtener_propiedades_por_proyecto()`: Get all properties

3. **Claude API** (Anthropic):
   - Modelo principal: `claude-sonnet-4-5`
   - Modelo backup: `claude-sonnet-4-5` (Haiku no soporta structured outputs aún)
   - Structured outputs (JSON schema validation)
   - Tool calling (function calling)

4. **WhatsApp** (`whatsapp.py`):
   - `enviar_mensaje()`: Envío de respuestas

### Retry y Timeouts

```python
@retry_on_failure()  # 2 intentos, 5s entre intentos
async def call_claude(...):
    await asyncio.wait_for(..., timeout=45s)  # Principal
    # Si falla → timeout=60s con modelo backup
```

**Decisión**: Timeouts generosos + retry automático
- Prompts largos del agendador requieren más tiempo de procesamiento
- Retry transparente mejora confiabilidad sin cambios en lógica

## 🎯 Prompt Engineering (Claude 4.5)

### Mejores Prácticas Aplicadas

1. **XML tags para estructura**:
```xml
<tu_rol>...</tu_rol>
<herramientas_disponibles>...</herramientas_disponibles>
<estrategia_busqueda>...</estrategia_busqueda>
<reglas_importantes>...</reglas_importantes>
<ejemplos_comportamiento>...</ejemplos_comportamiento>
```

2. **Instrucciones explícitas y directas**:
   - Qué hacer, cuándo hacerlo, cómo hacerlo
   - Pasos numerados para flujos complejos
   - Ejemplos concretos de entrada/salida

3. **Contexto y motivación clara**:
   - Por qué existe cada herramienta
   - Cuándo NO usarla
   - Consecuencias de decisiones incorrectas

4. **Cache control**:
```python
{"type": "text", "text": usuario_prompt, "cache_control": {"type": "ephemeral"}}
```
- El prompt estático se cachea
- Solo el contexto dinámico cambia en cada mensaje
- Reduce latencia y costos

5. **Structured outputs**:
```python
output_format={
    "type": "json_schema",
    "schema": transform_schema(Response)
}
```
- Garantiza respuestas válidas
- `respuesta_final_usuario` y `razonamiento` siempre presentes

## 📂 Estructura del Proyecto

```
app/
├── agentes/
│   ├── orquestador/
│   │   ├── funciones.py
│   │   └── todo.py
│   ├── buscador/
│   │   ├── funciones.py
│   │   └── todo.py
│   └── agendador/
│       ├── funciones.py
│       └── todo.py
├── api_calls/
│   ├── db_api.py        # Llamadas a base de datos
│   ├── busquedas.py     # RAG y filtros
│   └── whatsapp.py      # Integración WhatsApp
├── models/
│   ├── api_models.py    # Modelos de datos (Lead, Conversation, etc.)
│   └── agent_models.py  # Modelos para agentes (Agente, Response)
├── agents_main.py       # Orquestación principal de agentes
├── agregados.py         # Guardado de conversaciones y mensajes
├── auxiliares.py        # Utilidades (retry, formateo, fechas)
├── desacople.py         # Flujo principal (entrada del sistema)
└── main.py              # FastAPI app
```

## 🚀 Flujo Completo de una Petición

1. **Entrada** (`main.py`):
   - Usuario envía mensaje vía API
   - FastAPI recibe request → ejecuta `desacople.principal()` en background

2. **Carga de datos** (`desacople.py`):
   - Lee lead (o crea si no existe)
   - Carga últimos mensajes, conversación, y cita en paralelo
   - Construye `ApiState`

3. **Procesamiento del agente** (`agents_main.py`):
   - Determina agente según `estado_agentico`
   - Loop de hasta 7 iteraciones:
     - Llama a Claude con tools disponibles
     - Si usa tool → ejecuta y vuelve a llamar a Claude con resultado
     - Si responde texto → termina loop

4. **Ejecución de tools** (`funciones.py`):
   - Cada agente ejecuta su lógica específica
   - Llama a APIs externas (DB, búsquedas)
   - Actualiza `ApiState` si es necesario

5. **Respuesta** (`whatsapp.py`):
   - Envía respuesta final al usuario vía WhatsApp

6. **Persistencia** (`agregados.py`):
   - Guarda mensaje del usuario
   - Guarda respuesta de la IA
   - Actualiza lead (nombre, email, estado)
   - Actualiza conversación (proyecto seleccionado, funciones usadas)

## 🔑 Decisiones Técnicas Clave

### 1. Asincronismo total
- Todo el flujo es async para maximizar throughput
- Llamadas paralelas donde no hay dependencias
- Timeouts configurables con retry automático

### 2. Estado inmutable durante ejecución
- `ApiState` se pasa por referencia pero no se recrea
- Modificaciones en-place para mantener consistencia
- Un solo objeto viaja a través de todo el sistema

### 3. Separación de agentes por responsabilidad
- Cada agente es experto en su dominio
- Transiciones explícitas mediante tools
- No hay overlap de responsabilidades

### 4. Conversaciones cerradas vs Buffer continuo
- Conversación = contexto de búsqueda actual
- Buffer = memoria completa del usuario
- Al agendar → nueva conversación, pero buffer se mantiene

### 5. Retry transparente
- `@retry_on_failure()` en todas las llamadas de red
- Usuario no ve fallos transitorios
- Logs completos para debugging

### 6. Project-first en búsqueda
- Usuario piensa en ubicación/edificio primero
- Luego refina a unidad específica
- Mejora UX y reduce calls innecesarias

### 7. property_id opcional en agenda
- Flexibilidad para visitas generales vs específicas
- Agente detecta intención y usa tool apropiada
- Simplifica experiencia del usuario

## 🛡️ Manejo de Errores

- **Timeout en Claude**: Retry automático con modelo backup
- **API DB down**: Retry con wait de 5s entre intentos
- **Tool execution error**: Se propaga al loop del agente para retry
- **JSON serialization**: Conversión automática de datetime a ISO 8601
- **Missing data**: Validación en Pydantic models

## 📝 Notas Importantes

- **Haiku no soporta structured outputs** → Se usa Sonnet para backup también
- **Helicone** como proxy para logging de Claude API (comentado por defecto)
- **Cache control** reduce costos en prompts largos
- **Disable parallel tool use** para mayor control de flujo
- **Max 7 iteraciones** por conversación para prevenir loops infinitos

---

**Desarrollado para Pascal Inmobiliaria**
