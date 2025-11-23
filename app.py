import os
import logging
import time
import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import config
from travel_assistant import get_travel_assistant_prompt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Initialize CORS with restricted origins
CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Store chat sessions in memory
chat_sessions = {}

# API constants
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiAPI:

    def __init__(self, api_key, model="gemini-1.5-pro-latest"):
        """Initialize the Gemini API client"""
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def generate_content(self, prompt, max_retries=2):
        """Generate content using the Gemini API"""
        if not self.api_key or self.api_key == 'your_actual_gemini_api_key_here':
            raise Exception("Invalid API key. Please set GEMINI_API_KEY in .env file")
        
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        retries = 0
        last_error = None
        
        while retries <= max_retries:
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=app.config['CHAT_TIMEOUT'])
                
                if response.status_code == 429:  # Rate limited
                    if retries < max_retries:
                        wait_time = 2 ** retries
                        logger.warning(f"Rate limited. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        retries += 1
                        continue
                    else:
                        raise Exception("Rate limit exceeded. Please try again later.")
                
                if response.status_code == 401:
                    raise Exception("Invalid API key. Please check your GEMINI_API_KEY in .env")
                
                if response.status_code == 403:
                    raise Exception("API key doesn't have permission. Check your API key setup.")
                
                if response.status_code >= 500:
                    raise Exception(f"Gemini API server error ({response.status_code}). Try again later.")
                
                if response.status_code != 200:
                    error_detail = response.text[:200] if response.text else "Unknown error"
                    raise Exception(f"API error: {response.status_code} - {error_detail}")
                
                response_data = response.json()
                
                # Check for API errors in response
                if 'error' in response_data:
                    error_msg = response_data['error'].get('message', 'Unknown error')
                    raise Exception(f"Gemini API error: {error_msg}")
                
                # Extract generated text
                try:
                    generated_text = response_data['candidates'][0]['content']['parts'][0]['text']
                except (KeyError, IndexError, TypeError):
                    logger.error(f"Failed to parse response: {response_data}")
                    raise Exception("Could not parse API response. Invalid format.")
                
                if not generated_text or not generated_text.strip():
                    raise Exception("API returned empty response")
                
                logger.info("Successfully generated content")
                return generated_text
            
            except requests.exceptions.Timeout:
                last_error = "API request timeout (30s exceeded)"
                logger.error(last_error)
                if retries < max_retries:
                    retries += 1
                    continue
                raise Exception(last_error)
            
            except requests.exceptions.ConnectionError:
                last_error = "Connection error. Check your internet connection."
                logger.error(last_error)
                if retries < max_retries:
                    wait_time = 2 ** retries
                    time.sleep(wait_time)
                    retries += 1
                    continue
                raise Exception(last_error)
            
            except Exception as e:
                last_error = str(e)
                logger.error(f"API call failed: {last_error}")
                raise
        
        raise Exception(last_error or "Max retries reached")

# Routes

@app.route('/')
def index():
    """Serve the main page"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index: {str(e)}")
        return jsonify({'error': 'Failed to load page'}), 500

@app.route('/api/chat', methods=['POST'])
@limiter.limit("10 per minute")
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        role = data.get('role', 'Tourist')
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        if len(user_message) > app.config['MAX_MESSAGE_LENGTH']:
            return jsonify({'error': f'Message exceeds {app.config["MAX_MESSAGE_LENGTH"]} characters'}), 400
        
        api_key = app.config['GEMINI_API_KEY']
        if not api_key:
            logger.error("Gemini API key not configured")
            return jsonify({'error': 'API key not configured'}), 500
        
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {'history': [], 'role': role}
        
        session = chat_sessions[session_id]
        session['history'].append({'role': 'user', 'content': user_message})
        
        if len(session['history']) > app.config['MAX_CHAT_HISTORY']:
            session['history'] = session['history'][-app.config['MAX_CHAT_HISTORY']:]
        
        system_prompt = get_travel_assistant_prompt(role, user_message, session['history'])
        
        try:
            gemini = GeminiAPI(api_key, app.config['GEMINI_MODEL'])
            assistant_message = gemini.generate_content(system_prompt)
            session['history'].append({'role': 'assistant', 'content': assistant_message})
            
            logger.info(f"Chat response generated for session {session_id}")
            return jsonify({
                'success': True,
                'response': assistant_message,
                'message': assistant_message,
                'session_id': session_id
            })
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating response: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
    
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500

@app.route('/api/validate-key', methods=['GET'])
def validate_key():
    """Validate Gemini API key"""
    try:
        api_key = app.config['GEMINI_API_KEY']
        if not api_key or api_key == 'your_actual_gemini_api_key_here':
            return jsonify({'success': False, 'error': 'API key not configured'}), 400
        
        # Quick check: just verify we can reach the API
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                logger.info("API key validation successful")
                return jsonify({'success': True, 'message': 'API key is valid'})
            elif response.status_code == 401:
                return jsonify({'success': False, 'error': 'Invalid API key (401)'}), 401
            else:
                return jsonify({'success': False, 'error': f'API returned status {response.status_code}'}), response.status_code
        
        except requests.exceptions.Timeout:
            logger.warning("API validation timeout - assuming key is valid for now")
            return jsonify({'success': True, 'message': 'API key appears valid (timeout)'})
        
        except Exception as e:
            logger.error(f"API key validation error: {str(e)}")
            return jsonify({'success': False, 'error': f'Connection error: {str(e)}'}), 500
    
    except Exception as e:
        logger.error(f"Unexpected error in validate_key: {str(e)}")
        return jsonify({'success': False, 'error': 'Validation error'}), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    """List available models"""
    models = ['gemini-pro-latest', 'gemini-2.5-flash', 'gemini-flash-latest']
    return jsonify({'success': True, 'models': models})

@app.route('/api/roles', methods=['GET'])
def get_roles():
    """List available assistant roles"""
    roles = ['Tourist', 'Travel Agent', 'Local Guide', 'Backpacker']
    return jsonify({'success': True, 'roles': roles})

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info(f"Starting Flask app in {env} mode")
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
    