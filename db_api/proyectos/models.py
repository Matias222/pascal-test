from django.db import models
from pgvector.django import VectorField
import uuid


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    district = models.TextField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    reference = models.TextField(null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    video_url = models.TextField(null=True, blank=True)
    brochure_url = models.TextField(null=True, blank=True)
    includes_parking = models.BooleanField(null=True, blank=True, default=False)
    has_showroom = models.BooleanField(null=True, blank=True, default=False)
    busqueda = VectorField(dimensions=3072, null=True, blank=True)

    class Meta:
        db_table = 'projects'

    def __str__(self):
        return f"{self.name or 'Sin nombre'}"


class Typology(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    type = models.TextField(null=True, blank=True)
    num_bedrooms = models.SmallIntegerField(null=True, blank=True)
    num_bathrooms = models.SmallIntegerField(null=True, blank=True)
    area_m2 = models.TextField(null=True, blank=True)
    busqueda = VectorField(dimensions=3072, null=True, blank=True)

    class Meta:
        db_table = 'typologies'

    def __str__(self):
        return f"{self.name or 'Sin nombre'}"


class Property(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.TextField(null=True, blank=True)
    type = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    pricing = models.IntegerField(null=True, blank=True)
    view_type = models.TextField(null=True, blank=True)
    floor_no = models.TextField(null=True, blank=True)
    project_id = models.ForeignKey(Project, on_delete=models.SET_NULL, db_column='project_id', null=True, blank=True)
    typology_id = models.ForeignKey(Typology, on_delete=models.SET_NULL, db_column='typology_id', null=True, blank=True)
    busqueda = VectorField(dimensions=3072, null=True, blank=True)

    class Meta:
        db_table = 'properties'

    def __str__(self):
        return f"{self.title or 'Sin título'} - {self.type or 'Sin tipo'}"
