from django.urls import path

from . import views
from .crud_apis import lead, conversation, message, appointment

leadspatterns = [
    path('leads/', lead.get_all_leads, name='get_all_leads'),
    path('leads/create', lead.create_lead, name='create_lead'),
    path('leads/<str:pk>/update', lead.update_lead, name='update_lead'),
    path('leads/<str:pk>', lead.read_lead, name='read_lead'),
    path('leads/phone/<str:phone>', lead.read_lead_by_phone, name='read_lead_by_phone'),
    path('leads/<str:pk>/delete', lead.delete_lead, name='delete_lead')
]

conversationspatterns = [
    path('conversations/', conversation.get_all_conversations, name='get_all_conversations'),
    path('conversations/create', conversation.create_conversation, name='create_conversation'),
    path('conversations/lead/<str:lead_id>/latest', conversation.get_latest_conversation_by_lead, name='get_latest_conversation_by_lead'),
    path('conversations/<str:pk>/update', conversation.update_conversation, name='update_conversation'),
    path('conversations/<str:pk>', conversation.read_conversation, name='read_conversation'),
    path('conversations/<str:pk>/delete', conversation.delete_conversation, name='delete_conversation')
]

messagespatterns = [
    path('messages/', message.get_all_messages, name='get_all_messages'),
    path('messages/create', message.create_message, name='create_message'),
    path('messages/lead/<str:lead_id>', message.get_messages_by_lead, name='get_messages_by_lead'),
    path('messages/<str:pk>/update', message.update_message, name='update_message'),
    path('messages/<str:pk>', message.read_message, name='read_message'),
    path('messages/<str:pk>/delete', message.delete_message, name='delete_message')
]

appointmentspatterns = [
    path('appointments/', appointment.get_all_appointments, name='get_all_appointments'),
    path('appointments/create', appointment.create_appointment, name='create_appointment'),
    path('appointments/lead/<str:lead_id>/latest', appointment.get_latest_appointment_by_lead, name='get_latest_conversation_by_lead'),
    path('appointments/<str:pk>/update', appointment.update_appointment, name='update_appointment'),
    path('appointments/<str:pk>', appointment.read_appointment, name='read_appointment'),
    path('appointments/<str:pk>/delete', appointment.delete_appointment, name='delete_appointment')
]

urlpatterns = [
    path("", views.apiOverview, name="api-overview"),
]+leadspatterns+conversationspatterns+messagespatterns+appointmentspatterns