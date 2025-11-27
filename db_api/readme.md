# DB API - Sistema de Gestión Inmobiliaria

API REST para gestión de leads, propiedades y búsqueda semántica con embeddings para un agente conversacional de WhatsApp en el sector inmobiliario.

## 🏗️ Arquitectura

El proyecto está dividido en **dos apps principales de Django**:

### 1. **`db_api`** - Gestión de Leads y Conversaciones
Maneja la interacción con usuarios de WhatsApp:
- **Lead**: Usuario único identificado por teléfono
- **Conversation**: Sesiones de chat (un lead puede tener múltiples conversaciones)
- **Message**: Mensajes individuales (`human` o `ai-assistant`) con timestamps
- **Appointment**: Agendamiento de citas vinculadas a leads, conversaciones, proyectos y propiedades

**Endpoint destacado:**
- `GET /messages/lead/{lead_id}?limit=20` - Obtiene últimos k mensajes de un lead a través de todas sus conversaciones

### 2. **`proyectos`** - Catálogo Inmobiliario
Gestiona el inventario de propiedades:
- **Project**: Proyectos inmobiliarios (edificios, condominios, etc.)
- **Property**: Propiedades individuales dentro de proyectos
- **Typology**: Tipologías (num_bedrooms, num_bathrooms, area_m2)
---

## 🔍 Búsqueda Semántica (RAG)

Implementa **Retrieval Augmented Generation** usando:
- **Vector Embeddings**: AWS Bedrock `amazon.nova-2-multimodal-embeddings-v1:0` (3072 dimensiones)
- **Vector Database**: PostgreSQL con extensión `pgvector`
- **Búsqueda por similitud de coseno**: Operador `<=>` de pgvector

### Embeddings Generados:
- **Projects**: `name + description + details + district`
- **Properties**: `title + description + view_type`
- **Typologies**: ❌ No requieren embeddings (búsqueda estructurada)

### Endpoints de Búsqueda:

#### Búsqueda Semántica (Async):

```
POST /proyectos/search/projects
Body: {"query": "departamento moderno con vista al mar", "limit": 10}
```
```
POST /proyectos/search/properties
Body: {"query": "penthouse con piscina", "limit": 10}
```

#### Filtros Estructurados:
```
GET /proyectos/filter/projects?district=San%20Isidro&has_showroom=true
GET /proyectos/filter/properties?min_price=300000&max_price=500000&num_bedrooms=3
```

**Límites:** Todos los endpoints de búsqueda retornan máximo **15 resultados**.

---

## ⚡ Asincronismo

### Decisión: Híbrido (Sync + Async)

**Endpoints Asíncronos (ASGI con Uvicorn):**
- `search_projects_by_similarity`
- `search_properties_by_similarity`

**Razón:** Generación de embeddings con AWS Bedrock toma ~500ms-2s. Sin async, múltiples búsquedas simultáneas bloquearían el servidor.

**Endpoints Síncronos (tradicionales):**
- Todos los CRUDs (leads, messages, conversations, properties, projects)
- Filtros estructurados (no hacen llamadas a AWS)

### Stack Async:
```python
# Servidor
uvicorn api.asgi:application --workers 4

# Librerías
aioboto3==13.3.0  # Cliente async para AWS Bedrock
adrf==0.1.7       # Async Django REST Framework
uvicorn[standard]==0.34.0
```

### Cache de Embeddings:
- **Key**: MD5 hash del texto normalizado (`emb_{hash}`)
- **TTL**: 24 horas
- **Backend**: Django Cache (Redis/Memcached en producción)
- **Beneficio**: Queries repetidos son instantáneos

```python
# Ejemplo
"departamento con vista al mar" → emb_a3f8b9c2d1e4f5a6b7c8d9e0f1a2b3c4
```

---

## 🗄️ Base de Datos

### PostgreSQL + pgvector

**Tablas principales:**
```
leads (phone unique, name, email)
  └── conversations (lead_id FK, last_message_at, funciones_empleadas JSONB)
       └── messages (conversation_id FK, type, content, created_at)

projects (name, description, district, busqueda vector(3072))
  └── properties (project_id FK, typology_id FK, busqueda vector(3072))

typologies (name, num_bedrooms, num_bathrooms, area_m2)
```

**Campo especial - `funciones_empleadas`:**
```python
# JSONField para trackear herramientas usadas por el agente
funciones_empleadas = models.JSONField(default=list, blank=True)

# Ejemplo
["buscar_proyectos", "filtrar_propiedades", "agendar_cita"]
```

---

## 📐 Decisiones de Diseño

### 1. **Separación de Apps**
- `db_api`: Lógica conversacional (efímera, alta escritura)
- `proyectos`: Catálogo inmobiliario (estable, alta lectura)
- **Ventaja**: Deploy independiente, escalado diferenciado

### 2. **UUID como PK**
- Todas las tablas usan `UUIDField` con `default=uuid.uuid4`
- **Ventaja**: Generación distribuida, no hay colisiones, seguridad

### 3. **Timestamps Automáticos**
```python
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
```

### 4. **ForeignKeys con SET_NULL**
- Mayoría de FKs usan `on_delete=models.SET_NULL`
- **Razón**: Evitar eliminaciones en cascada accidentales
- **Excepción**: `Message.conversation_id` usa `CASCADE` (mensajes sin conversación no tienen sentido)

### 5. **Serializers Simples**
```python
class PropertySerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project_id.name', read_only=True)

    class Meta:
        model = Property
        exclude = ['busqueda']  # No exponer vectores de 3072 dims
```

### 6. **Conversaciones Múltiples**
Un Lead puede tener múltiples Conversations:
- **Conversación 1**: Búsqueda de departamento en San Isidro
- **Conversación 2**: Nueva búsqueda de casa de playa (semanas después)
- **Endpoint clave**: `GET /conversations/lead/{lead_id}/latest` obtiene la conversación más reciente

---

## 🚀 Comandos de Gestión

### Seed Database
```bash
python manage.py seed_data --clear
```
- Carga 30 proyectos realistas con 93 propiedades
- Carga 100 tipologías variadas
- Asigna tipologías apropiadas automáticamente

### Generar Embeddings
```bash
python manage.py generate_embeddings --model=all
python manage.py generate_embeddings --model=projects
python manage.py generate_embeddings --model=properties
```
- Usa AWS Bedrock Nova Embeddings (3072 dims)
- Rate limiting: 0.5s entre requests
- Guarda en campo `busqueda` (VectorField)

---
## 📋 Assumptions

### Reglas de Negocio:
1. **Todas las propiedades requieren un proyecto** (`project_id` es FK obligatorio)
2. Un Lead se identifica únicamente por `phone` (campo unique)
3. Los mensajes siempre pertenecen a una conversación
4. Las búsquedas semánticas y filtros retornan máximo 15 resultados
5. El campo `busqueda` (vector) nunca se expone en APIs (excluido en serializers)
