# translator/urls.py
from django.urls import path
from .views import translate_text , fetch_keys,update_lokalise_key_translation

urlpatterns = [
    path('translate/', translate_text, name='translate_text'),
    path('keys/', fetch_keys, name='fetch_keys'),
    path('update_translation/', update_lokalise_key_translation, name='update_lokalise_key_translation'),
]