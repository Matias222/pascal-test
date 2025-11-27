from django.contrib import admin
from .models import Lead, Conversation, Message, Appointment

admin.site.register(Lead)
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(Appointment)
