# WayFinder - AI Travel Assistant for India

An intelligent travel assistant chatbot powered by Google's Gemini API, specialized in providing comprehensive travel information about India.

## Features

✅ **Real-time Chat Interface** - Interactive conversation with AI assistant  
✅ **Multiple Personas** - Tourist, Travel Agent, Local Guide, Backpacker  
✅ **India-Focused Knowledge** - Destinations, cuisine, culture, transport, visas  
✅ **Session Management** - Maintains conversation history  
✅ **Text-to-Speech** - Listen to assistant responses  
✅ **Copy & Share** - Easy content sharing  
✅ **Responsive Design** - Works on desktop and mobile  

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **AI API**: Google Gemini API
- **Security**: CORS, Rate Limiting, Input Validation
- **Logging**: Python logging module

## Setup Instructions

### Prerequisites
- Python 3.8+
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Siva-Pavan02/Travel-Assistant-ai.git
cd Travel-Assistant-ai
```

2. **Create and activate virtual environment**
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-pro-latest
FLASK_ENV=development
```

5. **Run the application**
```bash
python app.py
```

6. **Access the app**
Open your browser and go to: `http://localhost:5000`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serve main page |
| POST | `/api/chat` | Send message and get response |
| GET | `/api/validate-key` | Validate Gemini API key |
| GET | `/api/models` | Get available models |
| GET | `/api/roles` | Get available assistant roles |

### Example Chat Request
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Best time to visit Goa?",
    "role": "Tourist",
    "session_id": "session_123"
  }'
```

## Configuration

Edit `config.py` to customize:
- Debug mode
- CORS origins
- Max message length
- Chat timeout
- API model selection

## Rate Limiting

- Default: 10 requests per minute to `/api/chat`
- Customize in `app.py` using `@limiter.limit()` decorator

## Error Handling

The app includes comprehensive error handling for:
- Invalid API keys
- Network timeouts
- Malformed requests
- Rate limiting (429 errors)
- Server errors (500)

## Security Features

✅ Input validation (message length, content)  
✅ CORS protection (configurable origins)  
✅ Rate limiting to prevent abuse  
✅ Environment variable management  
✅ Secure API key handling  
✅ XSS protection in frontend  

## Project Structure
```
TravelAssistantAI/
├── app.py                 # Main Flask application
├── config.py              # Configuration management
├── travel_assistant.py    # AI prompts & system context
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in git)
├── .gitignore             # Git ignore file
├── templates/
│   └── index.html         # Main HTML page
└── static/
    ├── css/
    │   └── styles.css     # Styling
    └── js/
        └── app.js         # Frontend logic
```

## Development Notes

### Logging
All requests and errors are logged to stdout. Check the terminal for detailed logs.

### Chat History
- Stored in-memory per session
- Persists for session duration only
- Automatically limited to 10 messages (configurable)

### Production Deployment
For production:
1. Set `FLASK_ENV=production` in `.env`
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Configure allowed CORS origins
4. Use database for session persistence
5. Enable HTTPS

Example with Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Troubleshooting

**Issue: "API key not configured"**
- Verify `.env` file exists in project root
- Ensure `GEMINI_API_KEY` is set correctly

**Issue: CORS errors**
- Check `config.py` CORS_ORIGINS setting
- For development, CORS_ORIGINS is set to "*" (allow all)

**Issue: Rate limit exceeded**
- Wait 1 minute or adjust rate limit in `app.py`

**Issue: No response from API**
- Check internet connection
- Verify API key is valid
- Check Gemini API status

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details.


## Acknowledgments

- Google Gemini API
- Flask community
- FontAwesome for icons

---

**Made with ❤️ for India travelers**
