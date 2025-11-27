from django.urls import path

from . import views
from .crud_apis import property, project, typology
from .busqueda_apis import property_search, project_search

propertiespatterns = [
    path('properties/', property.get_all_properties, name='get_all_properties'),
    path('properties/create', property.create_property, name='create_property'),
    path('properties/project/<str:project_id>', property.get_properties_by_project, name='get_properties_by_project'),
    path('properties/<str:pk>/update', property.update_property, name='update_property'),
    path('properties/<str:pk>', property.read_property, name='read_property'),
    path('properties/<str:pk>/delete', property.delete_property, name='delete_property')
]

projectspatterns = [
    path('projects/', project.get_all_projects, name='get_all_projects'),
    path('projects/create', project.create_project, name='create_project'),
    path('projects/<str:pk>/update', project.update_project, name='update_project'),
    path('projects/<str:pk>', project.read_project, name='read_project'),
    path('projects/<str:pk>/delete', project.delete_project, name='delete_project')
]

typologiespatterns = [
    path('typologies/', typology.get_all_typologies, name='get_all_typologies'),
    path('typologies/create', typology.create_typology, name='create_typology'),
    path('typologies/<str:pk>/update', typology.update_typology, name='update_typology'),
    path('typologies/<str:pk>', typology.read_typology, name='read_typology'),
    path('typologies/<str:pk>/delete', typology.delete_typology, name='delete_typology')
]

searchpatterns = [
    # Cosine similarity search endpoints
    path('search/projects', project_search.search_projects_by_similarity, name='search_projects_similarity'),
    path('search/properties', property_search.search_properties_by_similarity, name='search_properties_similarity'),

    # Filter endpoints
    path('filter/projects', project_search.filter_projects, name='filter_projects'),
    path('filter/properties', property_search.filter_properties, name='filter_properties'),
]

urlpatterns = [
    path("", views.apiOverview, name="api-overview"),
]+propertiespatterns+projectspatterns+typologiespatterns+searchpatterns
