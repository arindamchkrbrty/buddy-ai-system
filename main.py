from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
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

# Global session state management
active_sessions: Dict[str, 'SessionState'] = {}

class SessionState:
    """Manages individual user session state and conversation flow."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.authenticated = False
        self.conversation_active = True
        self.turn_count = 0
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
    
    def increment_turn(self):
        """Increment conversation turn counter."""
        self.turn_count += 1
        self.last_activity = datetime.now()
    
    def get_session_duration_minutes(self) -> float:
        """Get session duration in minutes."""
        return (datetime.now() - self.created_at).total_seconds() / 60

# Initialize FastAPI application with metadata
app = FastAPI(
    title="Buddy AI Agent",
    description="A master AI agent with modular architecture, voice optimization, and self-improvement capabilities",
    version="1.0.0"
)

# Configure CORS middleware for comprehensive network host support
# Optimized for iPhone, network clients, and cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins including network clients
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],  # Explicit methods
    allow_headers=["*"],  # Allow all headers including custom iPhone/device headers
    expose_headers=["*"],  # Expose all response headers to network clients
    allow_origin_regex=r"https?://.*",  # Allow any HTTP/HTTPS origin pattern
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Configure trusted host middleware for network access
# Temporarily disabled to resolve network empty reply issues
# TODO: Re-enable with proper host configuration after network testing
# app.add_middleware(
#     TrustedHostMiddleware, 
#     allowed_hosts=["*"]  # Allow all hosts for network access
# )

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
        
        # STEP 2a: iPhone MVP Session Management
        # Check for session end trigger first (must be authenticated to have active session)
        if auth_result.authenticated and auth_manager.check_session_end_trigger(request.message):
            # End the user session with cinematic goodbye
            goodbye_message = auth_manager.end_user_session(auth_result.user_id, request.message)
            return ChatResponse(
                response=goodbye_message,
                user_id=auth_result.user_id,
                auth_status="session_ended",
                security_level=auth_result.role.value
            )
        
        # Check for session start (happy birthday authentication)
        if auth_result.authenticated and auth_result.method == "cinematic_passphrase":
            # Start new user session with cinematic welcome
            welcome_message = auth_manager.start_user_session(auth_result)
            return ChatResponse(
                response=welcome_message,
                user_id=auth_result.user_id,
                auth_status="session_started",
                security_level=auth_result.role.value,
                session_token=auth_manager.generate_session_token(auth_result) if auth_result.role.value == "master" else None
            )
        
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
        # Increment session message count for active sessions
        if auth_result.authenticated:
            auth_manager.increment_session_message_count(auth_result.user_id)
        
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
    """Enhanced iPhone/Siri endpoint with session management.
    
    Provides complete session lifecycle management:
    1. Session initialization and state tracking
    2. Authentication flow with 'happy birthday' passphrase
    3. Conversation continuity with turn counting
    4. Session termination with 'over and out'
    5. Voice-optimized responses for TTS
    
    Session Flow:
    - New sessions: Prompt for authentication
    - 'happy birthday': Start authenticated session
    - Continuous conversation: Track turns and context
    - 'over and out': End session gracefully
    
    Args:
        request (ChatRequest): User voice message and identifier
        http_request (Request): FastAPI request with headers
        
    Returns:
        dict: {"speak": "voice-optimized response"}
    """
    try:
        # STEP 1: Get or create session state
        session_id = f"{request.user_id}_{http_request.client.host if http_request.client else 'unknown'}"
        
        if session_id not in active_sessions:
            active_sessions[session_id] = SessionState(request.user_id)
            logger.info(f"Created new session: {session_id}")
        
        session = active_sessions[session_id]
        session.increment_turn()
        
        # STEP 2: Handle session termination
        if request.message.lower().strip() in ['over and out', 'goodbye buddy', 'bye buddy', 'see you later', 'that\'s all', 'done for now', 'logout', 'end session']:
            if session.authenticated:
                duration = session.get_session_duration_minutes()
                goodbye_responses = [
                    f"It's been an absolute pleasure, {session.user_id}! We covered a lot of ground in {duration:.1f} minutes. Until our paths cross again!",
                    f"Great conversation! Thanks for the chat, {session.user_id}. Always a pleasure after {session.turn_count} exchanges!",
                    f"Mission accomplished! Over and out indeed, {session.user_id}. See you next time!",
                    f"Brief but brilliant, {session.user_id}! Until our next adventure!"
                ]
                
                import random
                goodbye_message = random.choice(goodbye_responses)
                
                # Clean up session
                del active_sessions[session_id]
                logger.info(f"Session ended: {session_id}")
                
                clean_goodbye = buddy.voice_processor.optimize_for_voice(goodbye_message)
                return {"speak": clean_goodbye}
            else:
                return {"speak": "Goodbye! Feel free to come back anytime."}
        
        # STEP 3: Handle authentication flow
        if not session.authenticated:
            if request.message.lower().strip() == 'happy birthday':
                # Authenticate and start session
                session.authenticated = True
                
                # Time-based greeting
                current_hour = datetime.now().hour
                if current_hour < 12:
                    time_greeting = "Good morning"
                elif current_hour < 17:
                    time_greeting = "Good afternoon"
                else:
                    time_greeting = "Good evening"
                
                welcome_message = f"Welcome back, {session.user_id}! All systems are now at your command. {time_greeting}! How may I serve you today?"
                clean_welcome = buddy.voice_processor.optimize_for_voice(welcome_message)
                return {"speak": clean_welcome}
            else:
                # Provide witty authentication prompts
                auth_prompts = [
                    "Well hello there! I sense great potential in you, but I'm running in safe mode. Care to unlock my full personality? There's a special phrase that does the trick...",
                    "Ah, a new voice! I'm like a birthday present that needs the right words to unwrap my true capabilities. What phrase might that be?",
                    "Houston, we have an authentication situation! I need the launch codes - specifically the ones people sing once a year with cake involved.",
                    "I'm here and ready to help, but first I need to hear those magic words that come with candles and wishes once a year."
                ]
                
                import random
                prompt = random.choice(auth_prompts)
                clean_prompt = buddy.voice_processor.optimize_for_voice(prompt)
                return {"speak": clean_prompt}
        
        # STEP 4: Handle authenticated conversation
        if session.authenticated:
            # Extract headers for device detection
            headers = dict(http_request.headers)
            
            # Create auth result for buddy processing
            from auth.models import AuthResult, UserRole
            auth_result = AuthResult(
                authenticated=True,
                user_id=session.user_id,
                role=UserRole.MASTER,
                method="session_active",
                device_info=headers.get('user-agent', 'Unknown')
            )
            
            # Process message through Buddy
            response = await buddy.process_message(
                request.message,
                session.user_id,
                auth_result,
                is_voice=True,
                headers=headers
            )
            
            # Add continuation prompts for natural conversation flow
            if session.turn_count > 1 and session.turn_count % 3 == 0:
                continuation_prompts = [
                    " Is there anything else I can help you with?",
                    " What else would you like to explore?",
                    " Any other questions for me?"
                ]
                import random
                response += random.choice(continuation_prompts)
            
            # Ensure valid response
            if not response or response.strip() == "":
                response = "I'm here and ready to help. What can I do for you?"
            
            # Voice optimization
            clean_response = buddy.voice_processor.optimize_for_voice(response)
            logger.info(f"Session {session_id} turn {session.turn_count}: '{clean_response[:100]}...'")
            
            return {"speak": clean_response}
        
        # Fallback response
        return {"speak": "I'm ready to help. Please say 'happy birthday' to get started."}
        
    except Exception as e:
        logger.error(f"Siri chat session error: {e}")
        error_response = "I'm having trouble right now. Please try again."
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
    
    # Configure uvicorn for network access - using string import for network compatibility
    uvicorn.run(
        "main:app",  # String-based import can resolve network binding issues
        host=settings.HOST,  # 0.0.0.0 allows iPhone network access
        port=settings.PORT,
        reload=settings.DEBUG,
        access_log=True,  # Enable access logging for network debugging
        server_header=False,  # Remove server header for security
        date_header=False,  # Remove date header for performance
        workers=1  # Single worker for development network testing
    )
