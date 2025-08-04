from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uvicorn
import logging

from core.buddy import Buddy
from config.settings import settings
from auth.authentication import AuthenticationManager
from auth.access_control import AccessController

# Configure logging for the main application
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI application with metadata
app = FastAPI(
    title="Buddy AI Agent",
    description="A master AI agent with modular architecture, voice optimization, and self-improvement capabilities",
    version="1.0.0"
)

# Configure CORS middleware to allow cross-origin requests
# This enables web clients, mobile apps, and iPhone network requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins including network clients
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers including custom iPhone headers
    expose_headers=["*"],  # Expose all response headers to clients
    allow_origin_regex=r"https?://.*",  # Allow any HTTP/HTTPS origin for network access
)

# Configure trusted host middleware for network access
# Note: Some network configurations may require disabling this for debugging
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Allow all hosts for network access (customize for production)
)

# Initialize core application components
# - Buddy: Main AI agent with conversation management and voice processing
# - AuthenticationManager: Handles iPhone authentication and session management  
# - AccessController: Manages access permissions and security levels
buddy = Buddy()
auth_manager = AuthenticationManager()
access_controller = AccessController(auth_manager)

class ChatRequest(BaseModel):
    """Request model for chat endpoints.
    
    Attributes:
        message (str): User's message or command to process
        user_id (Optional[str]): User identifier, defaults to "default"
    """
    message: str
    user_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    """Response model for chat endpoints.
    
    Attributes:
        response (str): AI agent's response to the user
        user_id (str): User identifier from the request
        auth_status (Optional[str]): Authentication status (authenticated/unauthenticated/denied)
        security_level (Optional[str]): User's security level (guest/user/master)
        session_token (Optional[str]): JWT session token for authenticated sessions
    """
    response: str
    user_id: str
    auth_status: Optional[str] = None
    security_level: Optional[str] = None
    session_token: Optional[str] = None

@app.get("/")
async def root():
    """Root endpoint providing basic API information.
    
    Returns:
        dict: Welcome message confirming the API is running
    """
    return {"message": "Buddy AI Agent is running!"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers.
    
    Returns:
        dict: Health status and agent identification
    """
    return {"status": "healthy", "agent": "buddy"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request):
    """Main chat endpoint for web clients and general API access.
    
    This endpoint handles the complete authentication and conversation flow:
    1. Extracts request headers for device identification
    2. Authenticates the user (iPhone priority, voice passphrase, session tokens)
    3. Checks access permissions based on user role
    4. Processes admin commands if applicable
    5. Routes to conversation manager, self-improvement, or AI processing
    6. Applies security filtering based on user access level
    7. Generates session tokens for new master authentications
    
    Args:
        request (ChatRequest): User message and identifier
        http_request (Request): FastAPI request object containing headers
        
    Returns:
        ChatResponse: AI response with authentication status and session info
        
    Raises:
        HTTPException: 500 if processing fails
        
    Example Usage:
        POST /chat
        {
            "message": "happy birthday",
            "user_id": "Arindam"
        }
        
        Response:
        {
            "response": "Welcome back, Arindam. All systems are now at your command.",
            "user_id": "Arindam",
            "auth_status": "authenticated",
            "security_level": "master",
            "session_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        }
    """
    try:
        # STEP 1: Extract HTTP headers for authentication analysis
        # Headers contain User-Agent (iPhone detection), session tokens, etc.
        headers = dict(http_request.headers)
        
        # STEP 2: Authenticate the request using multiple methods
        # Priority: iPhone devices > Voice passphrase > Session tokens > Guest access
        auth_result = auth_manager.authenticate_request(headers, request.message, request.user_id)
        
        # STEP 3: Check if user has permission to send this specific message
        # Some commands require master-level authentication
        access_info = access_controller.check_message_access(auth_result, request.message)
        
        if not access_info["allowed"]:
            # STEP 3a: Access denied - return cinematic denial response
            cinematic_response = access_info.get("cinematic_response", "Access denied")
            return ChatResponse(
                response=cinematic_response,
                user_id=request.user_id,
                auth_status="denied",
                security_level=auth_result.role.value
            )
        
        # STEP 4: Check for admin commands (system status, logs, improvements)
        admin_response = access_controller.process_admin_command(auth_result, request.message)
        if admin_response:
            # STEP 4a: Admin command processed - add security prefix and return
            prefix = access_controller.get_response_prefix(auth_result)
            return ChatResponse(
                response=prefix + admin_response,
                user_id=auth_result.user_id,
                auth_status="authenticated" if auth_result.authenticated else "unauthenticated",
                security_level=auth_result.role.value
            )
        
        # STEP 5: Process normal conversation message
        # Routes through: Self-improvement -> Conversation manager -> AI provider
        response = await buddy.process_message(request.message, auth_result.user_id, auth_result)
        
        # STEP 6: Determine if this is a special system response
        # Special responses bypass security filtering and prefixes
        is_special_response = any(phrase in response for phrase in [
            "Welcome back, Arindam", "daily briefing", "Session expired", 
            "Would you like me to give you your daily briefing", "I'd love to improve",
            "Analysis Complete", "Implementation Plan", "Improvement Complete",
            "Should I proceed"
        ])
        
        if is_special_response:
            # STEP 6a: Special system response - use as-is without filtering
            final_response = response
        else:
            # STEP 6b: Regular AI response - apply security filtering
            filtered_response = access_controller.filter_response_for_access_level(response, auth_result)
            
            # Add authentication status prefix to regular responses
            prefix = access_controller.get_response_prefix(auth_result)
            final_response = prefix + filtered_response
        
        # STEP 7: Generate session token for new master authentications
        # Tokens allow subsequent requests without re-authentication
        session_token = None
        if auth_result.authenticated and auth_result.role.value == "master" and auth_result.method == "cinematic_passphrase":
            session_token = auth_manager.generate_session_token(auth_result)
        
        # STEP 8: Return complete response with authentication metadata
        return ChatResponse(
            response=final_response,
            user_id=auth_result.user_id,
            auth_status="authenticated" if auth_result.authenticated else "unauthenticated",
            security_level=auth_result.role.value,
            session_token=session_token
        )
    except Exception as e:
        # Log error for debugging but don't expose internal details to client
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/siri-chat")
async def siri_chat(request: ChatRequest, http_request: Request):
    """iPhone/Siri-optimized endpoint for voice interaction.
    
    This endpoint is specifically designed for iPhone Siri Shortcuts integration:
    1. Automatically detects iPhone devices and prioritizes authentication
    2. Processes voice input with speech-to-text corrections
    3. Optimizes responses for text-to-speech synthesis
    4. Returns clean, natural speech without visual formatting
    5. Handles voice command recognition and context
    
    Key differences from /chat:
    - Returns {"speak": "text"} instead of full ChatResponse
    - Optimizes all responses through voice processor
    - No visual elements (emojis, markdown, debug info)
    - Enhanced iPhone device authentication
    - Voice-specific error handling
    
    Args:
        request (ChatRequest): User voice message and identifier
        http_request (Request): FastAPI request with iPhone headers
        
    Returns:
        dict: {"speak": "clean text for TTS"} - ready for Siri speech synthesis
        
    Example Siri Shortcut Usage:
        POST /siri-chat
        Headers: User-Agent: Siri/iPhone15,2 iOS/17.0
        {
            "message": "happy birthday",
            "user_id": "Arindam"
        }
        
        Response:
        {
            "speak": "Welcome back, Arindam. Good evening! How may I assist you today?"
        }
        
    Voice Commands Supported:
        - "happy birthday" - Authentication
        - "good morning buddy" - Daily briefing
        - "improve yourself" - Self-improvement
        - "hey buddy" - General conversation
    """
    try:
        # STEP 1: Extract headers for iPhone device authentication and voice processing
        headers = dict(http_request.headers)
        
        # STEP 2: Authenticate with iPhone priority
        # iPhone devices automatically get higher trust and faster authentication
        auth_result = auth_manager.authenticate_request(headers, request.message, request.user_id)
        
        # STEP 3: Check access permissions for voice commands
        access_info = access_controller.check_message_access(auth_result, request.message)
        
        if not access_info["allowed"]:
            # STEP 3a: Access denied - return voice-optimized cinematic response
            cinematic_response = access_info.get("cinematic_response", "Authentication required. Please say happy birthday.")
            clean_response = buddy.voice_processor.optimize_for_voice(cinematic_response)
            return {"speak": clean_response}
        
        # STEP 4: Process admin commands with voice optimization
        admin_response = access_controller.process_admin_command(auth_result, request.message)
        if admin_response:
            # STEP 4a: Admin command - optimize for speech and return
            clean_admin_response = buddy.voice_processor.optimize_for_voice(admin_response)
            return {"speak": clean_admin_response}
        
        # STEP 5: Process voice message with full conversation flow
        # Voice processing includes: input cleaning, command detection, context handling
        is_iphone = buddy.voice_processor.is_iphone_request(headers)
        
        response = await buddy.process_message(
            request.message, 
            auth_result.user_id, 
            auth_result, 
            is_voice=True,  # Enable voice processing pipeline
            headers=headers  # Pass headers for device-specific optimizations
        )
        
        # STEP 6: Ensure we have a valid response for TTS
        if not response or response.strip() == "":
            response = "I'm ready to help. What can I do for you?"
        
        # STEP 7: Final voice optimization pass
        # Removes: emojis, markdown, escape sequences, debug info
        # Optimizes: abbreviations, technical terms, speech patterns
        clean_response = buddy.voice_processor.optimize_for_voice(response)
        
        # Debug logging for voice response quality monitoring
        logger.info(f"Siri response optimized: '{clean_response[:100]}...'")  
        
        # STEP 8: Return Siri-ready response
        return {"speak": clean_response}
        
    except Exception as e:
        # Voice-specific error handling with TTS-friendly error messages
        logger.error(f"Siri chat endpoint error: {e}")
        error_response = buddy.voice_processor.create_voice_confirmation("error")
        return {"speak": error_response}

@app.get("/personality")
async def get_personality(http_request: Request):
    """Get Buddy's personality information and capabilities.
    
    Returns detailed information about Buddy's traits, capabilities,
    and current system status including authentication state.
    
    Args:
        http_request (Request): FastAPI request for authentication analysis
        
    Returns:
        dict: Personality traits, capabilities, self-improvement status,
              and current security/authentication information
              
    Example Response:
        {
            "name": "Buddy",
            "personality": {
                "traits": ["helpful", "friendly", "curious"],
                "communication_style": "conversational and warm"
            },
            "capabilities": ["General conversation", "Task assistance"],
            "security_status": {
                "authenticated": false,
                "user_role": "guest"
            }
        }
    """
    # Extract headers for authentication check
    headers = dict(http_request.headers)
    
    # Check current authentication status for this request
    auth_result = auth_manager.authenticate_request(headers, "", "anonymous")
    
    # Get base personality information from Buddy
    personality_info = buddy.get_personality_info()
    
    # Add current security context to the response
    personality_info["security_status"] = {
        "authenticated": auth_result.authenticated,
        "user_role": auth_result.role.value,
        "auth_method": auth_result.method
    }
    
    return personality_info

@app.get("/security/status")
async def security_status(http_request: Request):
    """Get comprehensive security system status (Master authentication required).
    
    Provides detailed security metrics, authentication logs, session status,
    and system security configuration. Only accessible to master-level users.
    
    Args:
        http_request (Request): FastAPI request with authentication headers
        
    Returns:
        dict: Complete security system status and metrics
        
    Raises:
        HTTPException: 403 if user is not authenticated as master
        
    Example Response:
        {
            "active_sessions": 1,
            "failed_attempts": 0,
            "security_level": "high",
            "authentication_methods": ["iPhone", "voice_passphrase", "session_token"]
        }
    """
    # Extract headers and authenticate request
    headers = dict(http_request.headers)
    auth_result = auth_manager.authenticate_request(headers, "", "anonymous")
    
    # Verify master-level authentication required for security information
    if auth_result.role.value != "master":
        logger.warning(f"Unauthorized security status access attempt from {auth_result.role.value}")
        raise HTTPException(status_code=403, detail="Master authentication required")
    
    logger.info(f"Security status accessed by master user: {auth_result.user_id}")
    return auth_manager.get_security_status()

@app.get("/admin/logs")
async def admin_logs(http_request: Request, limit: int = 50):
    """Get system authentication logs (Master authentication required).
    
    Retrieves recent authentication attempts, session activities,
    and security events for system monitoring and debugging.
    
    Args:
        http_request (Request): FastAPI request with master authentication
        limit (int): Maximum number of log entries to return (default 50)
        
    Returns:
        dict: {"logs": [list of authentication log entries]}
        
    Raises:
        HTTPException: 403 if user is not authenticated as master
    """
    # Extract headers and authenticate as admin/master
    headers = dict(http_request.headers)
    auth_result = auth_manager.authenticate_request(headers, "", "admin")
    
    # Verify master-level authentication for sensitive log access
    if auth_result.role.value != "master":
        logger.warning(f"Unauthorized admin logs access attempt from {auth_result.role.value}")
        raise HTTPException(status_code=403, detail="Master authentication required")
    
    logger.info(f"Admin logs accessed by master user: {auth_result.user_id}, limit: {limit}")
    return {"logs": auth_manager.get_authentication_logs(limit)}

@app.get("/admin/improvements")
async def get_improvements(http_request: Request):
    """Get self-improvement system status and history (Master authentication required).
    
    Provides current status of self-improvement processes, improvement history,
    pending changes, and system modification capabilities.
    
    Args:
        http_request (Request): FastAPI request with master authentication
        
    Returns:
        dict: Self-improvement status and complete modification history
        
    Raises:
        HTTPException: 403 if user is not authenticated as master
        
    Example Response:
        {
            "status": {
                "active": false,
                "pending_improvements": 0,
                "last_improvement": "2024-01-15T10:30:00Z"
            },
            "history": [
                {
                    "timestamp": "2024-01-15T10:30:00Z",
                    "type": "conversation_enhancement",
                    "description": "Added natural language processing improvement",
                    "status": "completed"
                }
            ]
        }
    """
    # Extract headers and authenticate as admin/master
    headers = dict(http_request.headers)
    auth_result = auth_manager.authenticate_request(headers, "", "admin")
    
    # Verify master-level authentication for self-improvement system access
    if auth_result.role.value != "master":
        logger.warning(f"Unauthorized improvements access attempt from {auth_result.role.value}")
        raise HTTPException(status_code=403, detail="Master authentication required")
    
    logger.info(f"Self-improvement status accessed by master user: {auth_result.user_id}")
    return {
        "status": buddy.self_improvement.get_improvement_status(),
        "history": buddy.self_improvement.get_improvement_history()
    }

@app.post("/voice")
async def voice_endpoint(message: str = Form(...), user_id: str = Form("Arindam"), http_request: Request = None):
    """Form-based voice endpoint for alternative integration methods.
    
    This endpoint accepts form data instead of JSON, making it suitable for:
    - Simple HTTP form submissions
    - Legacy voice integration systems
    - Direct URL-encoded POST requests
    - Testing and debugging with curl/Postman
    
    Functionally identical to /siri-chat but with form-based input.
    
    Args:
        message (str): Voice message or command (form field)
        user_id (str): User identifier (form field, defaults to "Arindam")
        http_request (Request): FastAPI request with headers
        
    Returns:
        dict: {"response": "clean text for TTS"} - voice-optimized response
        
    Example cURL Usage:
        curl -X POST http://localhost:8000/voice \\
             -H "User-Agent: iPhone" \\
             -d "message=happy birthday" \\
             -d "user_id=Arindam"
             
        Response:
        {
            "response": "Welcome back, Arindam. Good evening!"
        }
    """
    try:
        # STEP 1: Convert form data to internal ChatRequest format
        request = ChatRequest(message=message, user_id=user_id)
        
        # STEP 2: Use identical logic to /siri-chat for consistency
        headers = dict(http_request.headers)
        auth_result = auth_manager.authenticate_request(headers, request.message, request.user_id)
        
        # STEP 3: Check access permissions
        access_info = access_controller.check_message_access(auth_result, request.message)
        
        if not access_info["allowed"]:
            # STEP 3a: Access denied - return voice-optimized response
            cinematic_response = access_info.get("cinematic_response", "Authentication required. Please say happy birthday.")
            clean_response = buddy.voice_processor.optimize_for_voice(cinematic_response)
            return {"response": clean_response}
        
        # STEP 4: Process admin commands
        admin_response = access_controller.process_admin_command(auth_result, request.message)
        if admin_response:
            # STEP 4a: Admin command - voice optimize and return
            clean_admin_response = buddy.voice_processor.optimize_for_voice(admin_response)
            return {"response": clean_admin_response}
        
        # STEP 5: Process normal voice message through full pipeline
        response = await buddy.process_message(
            request.message, 
            auth_result.user_id, 
            auth_result, 
            is_voice=True,  # Enable voice processing
            headers=headers
        )
        
        # STEP 6: Final voice optimization
        clean_response = buddy.voice_processor.optimize_for_voice(response)
        
        # Debug logging for voice endpoint monitoring
        logger.info(f"Voice endpoint response: '{clean_response[:50]}...'")
        
        return {"response": clean_response}
        
    except Exception as e:
        # Voice-specific error handling
        logger.error(f"Voice endpoint error: {e}")
        error_response = buddy.voice_processor.create_voice_confirmation("error")
        return {"response": error_response}

if __name__ == "__main__":
    """Main entry point for running the Buddy AI Agent server.
    
    Starts the FastAPI application using Uvicorn ASGI server with
    configuration from settings. Enables hot reload in debug mode
    for development.
    
    Server Configuration:
        - Host: Configurable via settings.HOST (default: 0.0.0.0 for network access)
        - Port: Configurable via settings.PORT (default: 8000)
        - Reload: Enabled when settings.DEBUG is True
        
    Usage:
        python main.py
        
    Access Points:
        - Web API: http://0.0.0.0:8000 (accessible from iPhone/network)
        - Local access: http://localhost:8000
        - Docs: http://localhost:8000/docs
        - Health: http://localhost:8000/health
    """
    logger.info(f"Starting Buddy AI Agent server on {settings.HOST}:{settings.PORT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info("Available endpoints: /chat, /siri-chat, /voice, /personality")
    
    # Configure uvicorn for network access with optimal settings
    uvicorn.run(
        app,  # Direct app object for better performance and reliability
        host=settings.HOST,  # 0.0.0.0 allows iPhone network access
        port=settings.PORT,
        reload=settings.DEBUG,
        access_log=True,  # Enable access logging for network debugging
        server_header=False,  # Remove server header for security
        date_header=False,  # Remove date header for performance
    )
