
from adrf.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from proyectos.models import Project
from proyectos.serializers import ProjectSerializer
from proyectos.busqueda_apis import helpers
from django.db.models import Q
from django.core.cache import cache
from asgiref.sync import sync_to_async
import os


@api_view(['POST'])
async def search_projects_by_similarity(request):
    """
    Search projects using cosine similarity (ASYNC)
    Body: {"query": "texto de búsqueda", "limit": 10}
    """
    query_text = request.data.get('query')
    limit = request.data.get('limit', 10)

    # Enforce maximum limit of 15
    limit = min(limit, 15)

    if not query_text:
        return Response(
            {"error": "El campo 'query' es requerido"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Generate embedding for the query (async)
    query_embedding = await helpers.generate_query_embedding_async(query_text)

    if not query_embedding:
        return Response(
            {"error": "Error al generar el embedding de búsqueda"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Perform cosine similarity search using pgvector (sync to async)
    @sync_to_async
    def get_similar_projects():
        projects = Project.objects.raw(
            '''
            SELECT *, 1 - (busqueda <=> %s::vector) as similarity
            FROM projects
            WHERE busqueda IS NOT NULL
            ORDER BY busqueda <=> %s::vector
            LIMIT %s
            ''',
            [query_embedding, query_embedding, limit]
        )

        # Serialize results and add similarity score
        results = []
        for project in projects:
            serializer = ProjectSerializer(project)
            project_data = serializer.data
            project_data['similarity'] = project.similarity
            results.append(project_data)

        return results

    results = await get_similar_projects()
    return Response(results)


@api_view(['GET'])
def filter_projects(request):
    """
    Filter projects by various criteria (SYNC - no AWS calls)
    Query params: district, has_showroom, includes_parking
    """
    projects = Project.objects.all()

    # Filter by district
    district = request.query_params.get('district')
    if district:
        projects = projects.filter(district__icontains=district)

    # Filter by has_showroom
    has_showroom = request.query_params.get('has_showroom')
    if has_showroom is not None:
        has_showroom_bool = has_showroom.lower() in ['true', '1', 'yes']
        projects = projects.filter(has_showroom=has_showroom_bool)

    # Filter by includes_parking
    includes_parking = request.query_params.get('includes_parking')
    if includes_parking is not None:
        includes_parking_bool = includes_parking.lower() in ['true', '1', 'yes']
        projects = projects.filter(includes_parking=includes_parking_bool)

    # Search by name or description
    search = request.query_params.get('search')
    if search:
        projects = projects.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(details__icontains=search)
        )

    # Limit to maximum 15 results
    projects = projects[:15]

    serializer = ProjectSerializer(projects, many=True)
    return Response(serializer.data)
