"""
Example of Siri Shortcuts integration with Buddy AI Agent.

This file shows how to set up Siri Shortcuts to work with Buddy's voice-optimized endpoints.

SIRI SHORTCUT SETUP:
1. Open Shortcuts app on iPhone
2. Create new shortcut called "Talk to Buddy"
3. Add actions in this order:

ACTION 1: Get Text from Input
- Source: Ask for Input
- Prompt: "What would you like to say to Buddy?"
- Input Type: Text

ACTION 2: Get Contents of URL
- URL: http://your-server:8000/siri-chat
- Method: POST
- Headers: 
  - Content-Type: application/json
  - User-Agent: Siri/iPhone
- Request Body (JSON):
  {
    "message": [Text from previous action],
    "user_id": "Arindam"
  }

ACTION 3: Get Value for Dictionary
- Dictionary: Contents of URL (from previous action)
- Key: speak

ACTION 4: Speak Text
- Text: Dictionary Value (from previous action)
- Rate: Normal
- Pitch: Normal
- Language: Same as System

ADVANCED SETUP - Authentication:
For first-time setup, say "Happy birthday" to authenticate.
Buddy will remember your iPhone and maintain session.

VOICE COMMANDS TO TRY:
- "Happy birthday" (authentication)
- "Good morning Buddy" (daily briefing)
- "Improve yourself" (self-improvement)
- "Hey Buddy, how are you?" (general chat)
- "What's my schedule?" (briefing request)

TROUBLESHOOTING:
- If Buddy doesn't understand, speak more clearly
- Common words are automatically corrected (body → buddy)
- Session expires after 30 seconds of inactivity
- Use "Happy birthday" to re-authenticate
"""

# Example HTTP request that Siri would make:
example_request = {
    "method": "POST",
    "url": "http://localhost:8000/siri-chat",
    "headers": {
        "Content-Type": "application/json",
        "User-Agent": "Siri/iPhone15,2 iOS/17.0",
        "Accept": "application/json"
    },
    "body": {
        "message": "Good morning Buddy",
        "user_id": "Arindam"
    }
}

example_response = {
    "speak": "Good morning, Arindam! Would you like me to give you your daily briefing? I can share weather, upcoming meetings, and traffic updates."
}

# Voice input variations that work:
voice_variations = {
    "authentication": [
        "Happy birthday",
        "Say happy birthday", 
        "Happy birthday buddy"
    ],
    "greetings": [
        "Hey buddy",
        "Good morning body",  # Auto-corrected to "buddy"
        "Talk to buddy",
        "Hey body are you there"
    ],
    "briefings": [
        "Good morning buddy",
        "Morning briefing",
        "What's my schedule",
        "Daily update"
    ],
    "improvements": [
        "Improve yourself",
        "Make yourself better",
        "Upgrade your abilities"
    ]
}

print("Siri integration example loaded. Use the setup guide above to connect your iPhone!")