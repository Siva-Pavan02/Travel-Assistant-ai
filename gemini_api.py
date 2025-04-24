# Load environment variables (and fallback to hardcoded key if not set)
from dotenv import load_dotenv
import os

load_dotenv()

# Your Gemini API key (fallback if .env not provided)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyB29uug9ludMKWa0O08S51Fd1EWcA6ji1Y"

from flask import Flask, render_template, request, jsonify
import requests
import json
import time

app = Flask(__name__)

class GeminiAPI:
    def __init__(self, api_key, model="gemini-1.5-pro-latest"):
        """
        Initialize the Gemini API client
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        # Validate API key by listing models
        self.list_models()

    def list_models(self):
        url = f"{self.base_url}/models?key={self.api_key}"
        response = requests.get(url)
        if response.status_code != 200:
            error_message = f"Failed to list models. Status code: {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_message = f"API Error: {error_data['error'].get('message', 'Unknown error')}"
            except:
                pass
            raise Exception(error_message)
        return response.json()

    def generate_content(self, prompt, max_retries=3):
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        retries = 0
        while retries < max_retries:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code == 429:
                retries += 1
                time.sleep(2 ** retries)
                continue
            if response.status_code != 200:
                error_message = f"Failed to generate content. Status code: {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_message = f"API Error: {error_data['error'].get('message', 'Unknown error')}"
                except:
                    pass
                raise Exception(error_message)
            break
        if retries == max_retries:
            raise Exception("Maximum retries reached due to rate limiting")
        response_data = response.json()
        generated_text = ""
        if "candidates" in response_data:
            for candidate in response_data["candidates"]:
                if "content" in candidate:
                    for part in candidate["content"]["parts"]:
                        generated_text += part.get("text", "")
        if not generated_text:
            raise Exception("No text was generated in the response")
        return generated_text

# Flask routes below
@app.route('/')
def index():
    return render_template('index.html')

chat_histories = {}

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '')
    role = data.get('role', 'Tourist')
    model = data.get('model', 'gemini-1.5-pro-latest')
    session_id = data.get('session_id', 'default')
    chat_history = data.get('chat_history', [])

    if session_id not in chat_histories:
        chat_histories[session_id] = []
    chat_histories[session_id].append({"role": "user", "content": user_input})

    try:
        gemini = GeminiAPI(GEMINI_API_KEY, model)
        prompt = get_travel_assistant_prompt_with_history(role, user_input, chat_histories[session_id])
        response = gemini.generate_content(prompt)
        chat_histories[session_id].append({"role": "assistant", "content": response})
        if len(chat_histories[session_id]) > 10:
            chat_histories[session_id] = chat_histories[session_id][-10:]
        return jsonify({'success': True, 'response': response, 'session_id': session_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/validate-key', methods=['GET'])
def validate_key():
    try:
        gemini = GeminiAPI(GEMINI_API_KEY)
        models = gemini.list_models()
        return jsonify({'success': True, 'message': 'API key is valid', 'models': models})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    model_options = {
        "gemini-1.5-pro-latest": "Gemini 1.5 Pro (Recommended)",
        "gemini-1.5-flash": "Gemini 1.5 Flash (Faster)",
        "gemini-pro-vision": "Gemini Pro Vision (Image + Text)",
        "gemini-1.0-pro-vision-latest": "Gemini 1.0 Pro Vision"
    }
    return jsonify({'success': True, 'models': model_options})

@app.route('/api/roles', methods=['GET'])
def get_roles():
    role_options = {
        "Tourist": "General tourist looking for recommendations",
        "Travel Agent": "Professional travel advisor",
        "Local Guide": "Local with deep cultural knowledge",
        "Backpacker": "Budget-conscious adventurer"
    }
    return jsonify({'success': True, 'roles': role_options})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
