# Django Project

## Overview
This is a Django web application that serves LLM translation and upload translated content to platform LOKALISE.

## Prerequisites
- Python 3.13
- pip
- lokalise API key 
1.	Register lokalise account
2.	After registerd Lokalise account, go to profile setting https://app.lokalise.com/profile
3.	Go to API Tokens page in profile setting 
https://app.lokalise.com/profile#apitokens
4.	Generate a new token with permission (Read and write access)
 
- lokalise project-id
1.	Create new project on project page https://app.lokalise.com/projects
2.	Go to setting in project details page to get project ID
	 
- openrouter.ai API key
1.	Register account in openrouter.ai
2.	Create API keys in API keys
https://openrouter.ai/settings/keys
 
## Setup Instructions
1.	Clone the repository:
   git clone https://github.com/Richtestapi/ctranslation.git
2.	Install dependencies:
pip install -r requirements.txt
3.	Set up environment variables or use .env:
LOKALISE_API_TOKEN=[your_API_LOKEN]
LOKALISE_PROJECT_ID=[YOUR_PROJ_ID]
OPENAI_API_KEY=[YOUR_ROUTEROPENAI_API_KEY]
4.	Run migrations:
python manage.py migrate
5.	Run the development server:
python manage.py runserver
6.	Update CORS allow origin in settings.py (backend\settings.py)
# Alternatively, specify allowed origins
CORS_ALLOWED_ORIGINS = [
     "http://localhost:8081",  # Add your Vue.js app's URL
 ]

