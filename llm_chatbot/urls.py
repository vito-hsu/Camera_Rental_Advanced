# llm_chatbot/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.chat_view, name='llm_chat'), # 例如，聊天介面的 URL
    path('api/llm-query/', views.llm_api_view, name='llm_api'), # 如果有 API endpoint
]