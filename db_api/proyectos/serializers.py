from rest_framework import serializers
from .models import Property, Project, Typology

class PropertySerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project_id.name', read_only=True)

    class Meta:
        model = Property
        exclude = ['busqueda']

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        exclude = ['busqueda']

class TypologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Typology
        exclude = ['busqueda']
