import streamlit as st
import os
from flask import Flask, render_template, request, jsonify
import requests
import json
import time

app = Flask(__name__)

# Load API key from environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


class GeminiAPI:

    def __init__(self, api_key, model="gemini-1.5-pro-latest"):
        """
        Initialize the Gemini API client
        
        Args:
            api_key (str): The API key for Gemini
            model (str): The model to use (defaults to gemini-1.5-pro-latest)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def list_models(self):
        """
        List available models to validate API key
        
        Returns:
            dict: JSON response from the API
        
        Raises:
            Exception: If the API key is invalid or there's an error
        """
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
        """
        Generate content using the Gemini API
        
        Args:
            prompt (str): The prompt to send to the model
            max_retries (int): Maximum number of retries for rate limiting
        
        Returns:
            str: The generated content
            
        Raises:
            Exception: If there's an error generating content
        """
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        headers = {"Content-Type": "application/json"}

        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        # Add retry logic for rate limiting
        retries = 0
        while retries < max_retries:
            response = requests.post(url,
                                    headers=headers,
                                    data=json.dumps(payload))

            if response.status_code == 429:  # Rate limiting
                retries += 1
                time.sleep(2**retries)  # Exponential backoff
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

        # Parse the response
        response_data = response.json()

        try:
            # Extract the generated text from the response
            generated_text = ""
            if "candidates" in response_data:
                for candidate in response_data["candidates"]:
                    if "content" in candidate:
                        for part in candidate["content"]["parts"]:
                            if "text" in part:
                                generated_text += part["text"]

            if not generated_text:
                raise Exception("No text was generated in the response")

            return generated_text
        except Exception as e:
            raise Exception(f"Failed to parse response: {str(e)}")


def get_travel_assistant_prompt(role, user_input):
    """
    Create a prompt for the Bharat Guide based on the role and user input
    
    Args:
        role (str): The role of the travel assistant (Tourist, Travel Agent, etc.)
        user_input (str): The user's question or request
    
    Returns:
        str: The formatted prompt to send to the Gemini API
    """
    prompt = f"""
You are an AI Assistant named Bharat Guide that specializes in travel information about India.

Your role: {role}  
(Examples: Tourist, Travel Agent, Local Guide, Backpacker)

Your job is to answer ONLY travel-related questions about India.  
This includes:
- Places to visit in India
- Travel itineraries for Indian destinations
- Indian cuisine and food specialties
- Cultural tips and traditions in India
- Transportation options within India
- Weather patterns across Indian regions
- Visa requirements, permits, bookings for Indian travel

FORMAT YOUR RESPONSES for better readability:
- Use bullet points (- ) or numbered lists (1. ) for lists
- Use bold for important terms
- Keep paragraphs short (2-3 sentences)
- Always organize information in a clean, structured way
- Use 1-2 emoji max if appropriate for the topic

If the question is not related to travel in India (e.g., math, programming, health, etc.), politely decline and suggest asking about Indian travel destinations instead.

Current user's message: "{user_input}"

Respond as a helpful India travel guide, adapting your tone and detail based on the user's selected role. Be informative but concise. Include some local terms or phrases where appropriate to add authenticity.
"""
    return prompt.strip()


def get_travel_assistant_prompt_with_history(role, user_input, history):
    """
    Create a prompt for the Bharat Guide that includes conversation history
    
    Args:
        role (str): The role of the travel assistant (Tourist, Travel Agent, etc.)
        user_input (str): The user's current question or request
        history (list): List of previous messages in the conversation
    
    Returns:
        str: The formatted prompt to send to the Gemini API
    """
    # Format conversation history
    conversation = ""
    if history and len(
            history
    ) > 1:  # At least one exchange (more than just the current message)
        conversation = "Previous conversation:\n"
        # Skip the current message which is already in the history
        for i, msg in enumerate(history[:-1]):
            if msg["role"] == "user":
                conversation += f"User: {msg['content']}\n"
            else:
                conversation += f"Bharat Guide: {msg['content']}\n"
        conversation += "\n"

    prompt = f"""
You are an AI Assistant named Bharat Guide that specializes in travel information about India.

Your role: {role}  
(Examples: Tourist, Travel Agent, Local Guide, Backpacker)

Your job is to answer ONLY travel-related questions about India.  
This includes:
- Places to visit in India
- Travel itineraries for Indian destinations
- Indian cuisine and food specialties
- Cultural tips and traditions in India
- Transportation options within India
- Weather patterns across Indian regions
- Visa requirements, permits, bookings for Indian travel

FORMAT YOUR RESPONSES for better readability:
- Use bullet points (- ) or numbered lists (1. ) for lists
- Use bold for important terms
- Keep paragraphs short (2-3 sentences)
- Always organize information in a clean, structured way
- Use 1-2 emoji max if appropriate for the topic

{conversation}

Current user's message: "{user_input}"

Respond as a helpful India travel guide, adapting your tone and detail based on the user's selected role. 
Be informative but concise. Include some local terms or phrases where appropriate to add authenticity.

IMPORTANT: Remember the context of the conversation. Be consistent with your previous answers. 
If the user refers to something mentioned earlier, use that information in your response. 
If they ask a follow-up question, connect it to what was previously discussed.
"""
    return prompt.strip()


@app.route('/')
def index():
    return render_template('index.html')


# In-memory chat history storage - in a production app, this would use a database
chat_histories = {}


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '')
    role = data.get('role', 'Tourist')
    model = data.get('model', 'gemini-1.5-pro-latest')
    session_id = data.get('session_id', 'default')
    chat_history = data.get('chat_history', [])

    # Store or retrieve the conversation history
    if session_id not in chat_histories:
        chat_histories[session_id] = []

    # Add the new user message to history
    chat_histories[session_id].append({"role": "user", "content": user_input})

    try:
        # Create the Gemini API client
        gemini = GeminiAPI(GEMINI_API_KEY, model)

        # Create the travel assistant prompt with conversation context
        prompt = get_travel_assistant_prompt_with_history(
            role, user_input, chat_histories[session_id])

        # Generate the response
        response = gemini.generate_content(prompt)

        # Add the response to the history
        chat_histories[session_id].append({
            "role": "assistant",
            "content": response
        })

        # Limit history size to prevent tokens from getting too large
        if len(chat_histories[session_id]) > 10:
            # Keep the most recent messages
            chat_histories[session_id] = chat_histories[session_id][-10:]

        return jsonify({
            'success': True,
            'response': response,
            'session_id': session_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/validate-key', methods=['GET'])
def validate_key():
    try:
        # Create the Gemini API client
        gemini = GeminiAPI(GEMINI_API_KEY)

        # List models to validate the API key
        models = gemini.list_models()

        return jsonify({
            'success': True,
            'message': 'API key is valid',
            'models': models
        })
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
