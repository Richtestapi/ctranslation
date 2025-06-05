# translator/urls.py
from django.urls import path
from .views import evaluate_translation

urlpatterns = [
    path('evaluate_translation/', evaluate_translation, name='evaluate_translation'),
]