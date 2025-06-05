import json
import os
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch

class TranslateTextViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('translate_text')  # Adjust URL name as necessary



    @patch('translator.views.get_lokalise_key')
    def test_translate_text_key_not_found(self, mock_get_lokalise_key):
        mock_get_lokalise_key.return_value = {'error': 'Key not found'}

        response = self.client.post(self.url, json.dumps({'key_id': 'invalid_key_id'}),
                                     content_type='application/json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'error': 'Key not found'})

    def test_translate_text_invalid_json(self):
        response = self.client.post(self.url, 'invalid_json', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'Invalid JSON'})

class FetchKeysViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('fetch_keys')  # Adjust URL name as necessary

    @patch('translator.views.fetch_keys')  # Adjust import path
    def test_fetch_keys_success(self, mock_fetch_keys):
        mock_fetch_keys.return_value = {'keys': [{'key_id': '659360626', 'name': 'Test Key'}]}

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('keys', response.json())

    def test_fetch_keys_request_failure(self):
        # Assuming you handle request failures in your fetch_keys view
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

class UpdateLokaliseKeyTranslationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('update_lokalise_key_translation')  # Adjust URL name as necessary

    @patch('translator.views.update_lokalise_key_translation')  # Adjust import path
    def test_update_translation_success(self, mock_update_translation):
        mock_update_translation.return_value = {'translation_id': '5905818962', 'translation': 'Bonjour'}

        response = self.client.post(self.url, json.dumps({
            'key_id': '659360626',
            'language_iso': 'fr',
            'translated_texts': 'Bonjour',
            'translation_id': '5905818962'
        }), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('translation_id', response.json()["translation"])

    def test_update_translation_invalid_method(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {'error': 'Invalid request method.'})

    def test_update_translation_missing_fields(self):
        response = self.client.post(self.url, json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'translation_id, language ISO, and translation are required.'})