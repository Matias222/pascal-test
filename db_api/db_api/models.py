from django.db import models
import uuid
from proyectos.models import Project, Property

class Lead(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(null=True, blank=True)
    email = models.TextField(null=True, blank=True)
    phone = models.TextField(null=True, blank=True, unique=True)
    estado_agentico = models.TextField(default="onboarding") #Atributo agregado para manejar el state
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leads'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name or 'Sin nombre'} - {self.email or 'Sin email'}"


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    most_recent_project_id = models.ForeignKey(Project, on_delete=models.SET_NULL, db_column='most_recent_project_id', null=True, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    is_answered_by_lead = models.BooleanField(null=True, blank=True, default=False)
    lead_id = models.ForeignKey(Lead, on_delete=models.CASCADE, db_column='lead_id', null=True, blank=True)
    funciones_empleadas = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'conversations'
        ordering = ['-created_at']

    def __str__(self):
        return f"Conversation {self.id} - Lead: {self.lead_id}"


class Message(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('human', 'Human'),
        ('ai-assistant', 'AI Assistant'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES)
    content = models.TextField()
    conversation_id = models.ForeignKey(Conversation, on_delete=models.CASCADE, db_column='conversation_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['-created_at']

    def __str__(self):
        return f"Message {self.type} - {self.content[:50]}"


class Appointment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead_id = models.ForeignKey(Lead, on_delete=models.SET_NULL, db_column='lead_id', null=True, blank=True)
    conversation_id = models.ForeignKey(Conversation, on_delete=models.SET_NULL, db_column='conversation_id', null=True, blank=True)
    project_id = models.ForeignKey(Project, on_delete=models.SET_NULL, db_column='project_id', null=True, blank=True)
    property_id = models.ForeignKey(Property, on_delete=models.SET_NULL, db_column='property_id', null=True, blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'appointments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Appointment {self.id} - Lead: {self.lead_id}"
