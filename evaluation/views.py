import os
import requests
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from typing import Dict
import evaluate

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Set to INFO or ERROR as needed
logger = logging.getLogger(__name__)

def predictTER(translations, references):
    # Load the TER evaluation metric
    ter = evaluate.load("ter")
    
    # Prepare the input as a dictionary
    results = ter.compute(
        predictions=translations,
        references=references
    )
    logger.debug(f'TER results: {results}')
    return results

def predictBLEU(translations, references):
    bleu = evaluate.load("bleu")
    
    # Prepare the input as a dictionary
    results = bleu.compute(
        predictions=translations,
        references=references
    )
    logger.debug(f'BLEU results: {results}')
    return results

def analyze_results(evaluation_results: Dict) -> str:
    suggestions = []
    bleu = evaluation_results.get("overall_bleu", 0)
    if bleu < 0.4:
        suggestions.append("The BLEU score suggests significant room for improvement...")
    
    ter = evaluation_results.get("overall_ter", 0)
    if ter > 0.4:
        suggestions.append("The high TER score indicates many edits are needed...")

    return "\n".join(suggestions)

@csrf_exempt
def evaluate_translation(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            translations = body.get('translations', [])
            logger.debug(f'Received translations: {translations}')

            # Reference translations (if needed)
            references = [
                'Get a Welcome Bonus worth up to 1 BTC by trading at least [$1].',
                "Obtenez un bonus d'accueil d'une valeur allant jusqu'à 1 BTC en effectuant des transactions d'au moins [$1].",
                "Obtenez une prime d'accueil d'une valeur pouvant atteindre 1 BTC en négociant au moins [1 $].",
                'Obtenga un Bonus de Bienvenida válido hasta 1 BTC realizando al menos [$1] en operaciones.',
                'Obtén un Bonus de Bienvenida válido hasta 1 BTC al comerciar por al menos [$1].',
                'Obtenga una pronta bienvenida de hasta 1 BTC mediante el intercambio de al menos [$1].',
                '獲得至多1 BTC的歡迎獎金，只需交易至少[$1]。',
                '获得最高1 个比特币的欢迎奖励，只需交易至少[$1]。',
                '1호 환영 보너스는 [$1] 이상의 거래로 최대 1 BTC 값을 가집니다.'
            ]
            
            # Fetch the evaluation results from BLEU and TER functions
            ter_results = predictTER(translations, references)
            bleu_results = predictBLEU(translations, references)

            evaluations = {
                'BLEU': f"{float(bleu_results.get('bleu', 0)):.4f}",
                'TER': f"{float(ter_results.get('score', 0)):.4f}",
                'Suggestions': analyze_results({'overall_bleu': bleu_results['bleu'], 'overall_ter': ter_results['score']}),
            }
            
            logger.info(f'Evaluation results: {evaluations}')
            return JsonResponse(evaluations)
        
        except json.JSONDecodeError:
            logger.error('Invalid JSON in request body')
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.exception('An unexpected error occurred')
            return JsonResponse({'error': str(e)}, status=500)

    logger.error('Invalid request method')
    return JsonResponse({'error': 'Invalid request method'}, status=400)