# Buddy AI Agent

A modular master AI agent with a friendly personality, designed for easy expansion and AI model swapping.

## Features

- **Friendly Personality**: Buddy is designed to be helpful, friendly, curious, patient, and encouraging
- **Modular Architecture**: Easy to swap AI providers and memory backends
- **FastAPI Web Server**: RESTful API with automatic documentation
- **Siri Shortcuts Integration**: Dedicated endpoint for voice interactions
- **Memory Management**: Conversation history and user preferences
- **Future-Ready**: Designed for expansion with specialist agents

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd jarvis-ai-system
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
python main.py
```

The server will start at `http://localhost:8000`

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## API Endpoints

### Core Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /chat` - Main chat interface
- `POST /siri-chat` - Siri Shortcuts optimized endpoint
- `GET /personality` - Get Buddy's personality information

### Chat Request Format

```json
{
  "message": "Hello, Buddy!",
  "user_id": "optional-user-id"
}
```

### Chat Response Format

```json
{
  "response": "Hello! I'm Buddy, your friendly AI assistant. How can I help you today?",
  "user_id": "user-123"
}
```

## Architecture

### Core Components

- **main.py**: FastAPI web server and API endpoints
- **core/buddy.py**: Master agent logic and personality system
- **providers/**: Abstract interfaces for AI and memory providers
- **config/settings.py**: Configuration management

### Provider System

The modular provider system allows easy swapping of:

- **AI Providers**: Different AI models/services (currently includes mock provider)
- **Memory Providers**: Different storage backends (currently includes mock provider)

## Configuration

Set environment variables to configure Buddy:

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# AI Provider
AI_PROVIDER=mock
AI_PROVIDER_API_KEY=your-api-key
AI_PROVIDER_MODEL=default

# Memory Provider
MEMORY_PROVIDER=mock
MAX_CONVERSATION_HISTORY=50

# Buddy Configuration
BUDDY_NAME=Buddy
BUDDY_PERSONALITY_LEVEL=friendly
```

## Siri Shortcuts Integration

Use the `/siri-chat` endpoint for voice integration:

1. Create a new Siri Shortcut
2. Add "Get Contents of URL" action
3. Set URL to: `http://your-server:8000/siri-chat`
4. Set Method to POST
5. Add JSON body with your message
6. Add "Speak Text" action with the response

## Development

### Adding New AI Providers

1. Create a new class inheriting from `AIProvider`
2. Implement all abstract methods
3. Register in `core/buddy.py`

### Adding New Memory Providers

1. Create a new class inheriting from `MemoryProvider`
2. Implement all abstract methods
3. Register in `core/buddy.py`

## Future Enhancements

- Specialist agent integration
- Advanced memory management
- Multi-modal capabilities
- Tool usage and function calling
- Real AI provider integrations (OpenAI, Anthropic, etc.)
- Persistent memory backends (PostgreSQL, Redis, etc.)

## Project Structure

```
jarvis-ai-system/
├── main.py                 # FastAPI web server
├── core/
│   └── buddy.py           # Master agent logic
├── providers/
│   ├── ai_provider.py     # Abstract AI interface
│   ├── memory_provider.py # Abstract memory interface
│   ├── mock_ai_provider.py
│   └── mock_memory_provider.py
├── config/
│   └── settings.py        # Configuration management
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## License

MIT License - See LICENSE file for details