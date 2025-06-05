import os
import requests
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # You can change the level to INFO or ERROR as needed
logger = logging.getLogger(__name__)

@csrf_exempt
def translate_text(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            key_id = body.get('key_id', '')
            logger.debug(f'Received request to translate text for key_id: {key_id}')

            api_token = os.getenv('LOKALISE_API_TOKEN')
            project_id = os.getenv('LOKALISE_PROJECT_ID')

            headers = {
                'X-Api-Token': api_token,
            }

            # Fetch the key details from Lokalise
            keyresult = get_lokalise_key(key_id)
            if not keyresult or 'error' in keyresult:
                logger.error(f'Key not found: {key_id}')
                return JsonResponse({'error': 'Key not found'}, status=404)

            # Extract the English translation
            text = ''
            for translation in keyresult['key']['translations']:
                if translation['language_iso'] == 'en':
                    text = translation['translation']
                    break

            if not text:
                logger.error(f'No English translation found for key_id: {key_id}')
                return JsonResponse({'error': 'No English translation found'}, status=404)

            glossary_dict = fetch_glossary_terms()
            translated_key_obj_list = []
            llm_api_url = 'https://openrouter.ai/api/v1/chat/completions'
            llm_api_key = os.getenv('OPENAI_API_KEY')

            # Apply glossary terms if available
            if glossary_dict:
                text = apply_glossary(text, glossary_dict)

            # Call the LLM API for each language
            for translation in keyresult['key']['translations']:
                language = translation['language_iso']
                if language != 'en':   
                    logger.debug(f'Translating to language: {language}')
                    try:
                        if language == "fr_ca":
                            content = f"Translate this to language French Canada: {text}. Just the translation only"
                        elif language == "ko":
                            content = f"Translate this to language Korean: {text}. Just the translation only"
                        else:
                            content = f"Translate this to language {language}: {text}. Just the translation only"
                        
                        llm_response = requests.post(
                            llm_api_url,
                            headers={
                                'Authorization': f'Bearer {llm_api_key}', 
                                'Content-Type': 'application/json'
                            },
                            json={
                                'model': 'meta-llama/llama-3.3-8b-instruct:free',
                                'messages': [{'role': 'user', 'content': f'{content}'}]
                            }
                        )
                        llm_response.raise_for_status()  # Raise an error for bad responses
                        translated_text = llm_response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
                        translation_id = translation['translation_id']

                        translated_key_obj = {
                            'translation_id': translation_id,
                            'translated_texts': translated_text,
                            'key_id': key_id,
                            'language_iso': language
                        }
                        translated_key_obj_list.append(translated_key_obj)

                    except requests.exceptions.RequestException as e:
                        logger.error(f'Request failed for language {language} with error: {str(e)}')
                        return JsonResponse(
                            {
                                'translation_id': translation_id,
                                'translated_texts': '',
                                'key_id': key_id,
                                'language_iso': language,
                                'error': str(e)
                            }, 
                            status=500
                        )

            return JsonResponse(translated_key_obj_list, safe=False)

        except json.JSONDecodeError:
            logger.error('Invalid JSON in request body')
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.exception('An unexpected error occurred')
            return JsonResponse({'error': str(e)}, status=500)

    logger.error('Invalid request method')
    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_lokalise_key(key_id):
    api_token = os.getenv('LOKALISE_API_TOKEN')
    project_id = os.getenv('LOKALISE_PROJECT_ID')
    
    url = f'https://api.lokalise.com/api2/projects/{project_id}/keys/{key_id}'
    
    headers = {
        'X-Api-Token': api_token,
        'Content-Type': 'application/json',
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()  # Return the JSON response if successful
    except requests.exceptions.HTTPError as err:
        logger.error(f'HTTP error occurred: {str(err)}')
        return {'error': str(err)}  # Return error message
    except Exception as e:
        logger.exception('An unexpected error occurred while fetching key')
        return {'error': str(e)}  # Return any other error

@csrf_exempt
def fetch_keys(request):
    try:
        api_token = os.getenv('LOKALISE_API_TOKEN')
        project_id = os.getenv('LOKALISE_PROJECT_ID')
        lokalise_url = f'https://api.lokalise.com/api2/projects/{project_id}/keys?include_translations=1'
        headers = {
            'X-Api-Token': api_token,
        }

        response = requests.get(lokalise_url, headers=headers)
        
        if response.status_code == 200:
            keys = response.json().get('keys', [])
            logger.debug('Fetched keys successfully')
            return JsonResponse({'keys': keys})  # Return as JsonResponse
        else:
            logger.error(f'Failed to fetch keys: {response.status_code}')
            return JsonResponse({'error': 'Failed to fetch keys'}, status=response.status_code)

    except requests.exceptions.RequestException as e:
        logger.error(f'Request failed: {str(e)}')
        return JsonResponse({'error': 'Request failed'}, status=500)
    except Exception as e:
        logger.exception('An unexpected error occurred while fetching keys')
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

def apply_glossary(text, glossary_dict):
    for term, translation in glossary_dict.items():
        text = text.replace(term, translation)
    return text

def fetch_glossary_terms():
    api_token = os.getenv('LOKALISE_API_TOKEN')
    project_id = os.getenv('LOKALISE_PROJECT_ID')

    url = f'https://api.lokalise.com/api2/projects/{project_id}/glossary-terms'

    headers = {
        'X-Api-Token': api_token,
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        glossary = response.json().get('glossaries', [])
        logger.debug('Fetched glossary terms successfully')
        return glossary
    else:
        logger.error(f'Failed to fetch glossary terms: {response.status_code}')
        return []

@csrf_exempt
def update_lokalise_key_translation(request):
    if request.method != 'POST':
        logger.error('Invalid request method for updating translation')
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    try:
        body = json.loads(request.body)
        key_id = body.get('key_id', '')
        lang = body.get('language_iso', '')
        translation = body.get('translated_texts', '')
        translation_id = body.get('translation_id', '')

        # Validate input
        if not translation_id or not lang or not translation:
            logger.error('Missing required fields for translation update')
            return JsonResponse({'error': 'translation_id, language ISO, and translation are required.'}, status=400)

        api_token = os.getenv('LOKALISE_API_TOKEN')
        project_id = os.getenv('LOKALISE_PROJECT_ID')

        url = f'https://api.lokalise.com/api2/projects/{project_id}/translations/{translation_id}'

        headers = {
            'X-Api-Token': api_token,
            'Content-Type': 'application/json',
        }

        data = {
            "translation": translation,
        }

        # Make the request to update the translation
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an error for bad responses
        logger.debug('Translation updated successfully')
        return JsonResponse(response.json())  # Return the JSON response if successful

    except requests.exceptions.HTTPError as err:
        logger.error(f'Error updating translation: {str(err)}')
        return JsonResponse({'error': str(err)}, status=response.status_code)
    except json.JSONDecodeError:
        logger.error('Invalid JSON in request body for updating translation')
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.exception('An unexpected error occurred while updating translation')
        return JsonResponse({'error': str(e)}, status=500)