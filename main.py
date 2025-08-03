from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uvicorn

from core.buddy import Buddy
from config.settings import settings
from auth.authentication import AuthenticationManager
from auth.access_control import AccessController

app = FastAPI(
    title="Buddy AI Agent",
    description="A master AI agent with modular architecture",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

buddy = Buddy()
auth_manager = AuthenticationManager()
access_controller = AccessController(auth_manager)

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    response: str
    user_id: str
    auth_status: Optional[str] = None
    security_level: Optional[str] = None
    session_token: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "Buddy AI Agent is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "buddy"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request):
    try:
        # Extract headers for authentication
        headers = dict(http_request.headers)
        
        # Authenticate request
        auth_result = auth_manager.authenticate_request(headers, request.message, request.user_id)
        
        # Check access permissions
        access_info = access_controller.check_message_access(auth_result, request.message)
        
        if not access_info["allowed"]:
            # Use cinematic response if available
            cinematic_response = access_info.get("cinematic_response", "Access denied")
            return ChatResponse(
                response=cinematic_response,
                user_id=request.user_id,
                auth_status="denied",
                security_level=auth_result.role.value
            )
        
        # Check for admin commands
        admin_response = access_controller.process_admin_command(auth_result, request.message)
        if admin_response:
            prefix = access_controller.get_response_prefix(auth_result)
            return ChatResponse(
                response=prefix + admin_response,
                user_id=auth_result.user_id,
                auth_status="authenticated" if auth_result.authenticated else "unauthenticated",
                security_level=auth_result.role.value
            )
        
        # Process normal message with sophisticated conversation flow
        response = await buddy.process_message(request.message, auth_result.user_id, auth_result)
        
        # Check if response already came from conversation manager or self-improvement (contains specific patterns)
        is_special_response = any(phrase in response for phrase in [
            "Welcome back, Arindam", "daily briefing", "Session expired", 
            "Would you like me to give you your daily briefing", "I'd love to improve",
            "Analysis Complete", "Implementation Plan", "Improvement Complete",
            "Should I proceed"
        ])
        
        if is_special_response:
            # Don't add prefix or filter for conversation manager or self-improvement responses
            final_response = response
        else:
            # Filter response based on access level
            filtered_response = access_controller.filter_response_for_access_level(response, auth_result)
            
            # Add authentication prefix for regular responses
            prefix = access_controller.get_response_prefix(auth_result)
            final_response = prefix + filtered_response
        
        # Generate session token for new master authentication
        session_token = None
        if auth_result.authenticated and auth_result.role.value == "master" and auth_result.method == "cinematic_passphrase":
            session_token = auth_manager.generate_session_token(auth_result)
        
        return ChatResponse(
            response=final_response,
            user_id=auth_result.user_id,
            auth_status="authenticated" if auth_result.authenticated else "unauthenticated",
            security_level=auth_result.role.value,
            session_token=session_token
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/siri-chat")
async def siri_chat(request: ChatRequest, http_request: Request):
    """Enhanced Siri-optimized endpoint with voice processing."""
    try:
        # Extract headers for iPhone device authentication
        headers = dict(http_request.headers)
        
        # Authenticate request - iPhone devices get automatic priority
        auth_result = auth_manager.authenticate_request(headers, request.message, request.user_id)
        
        # Check access permissions
        access_info = access_controller.check_message_access(auth_result, request.message)
        
        if not access_info["allowed"]:
            # Use cinematic response for Siri, optimized for voice
            cinematic_response = access_info.get("cinematic_response", "Authentication required. Please say happy birthday.")
            clean_response = buddy.voice_processor.optimize_for_voice(cinematic_response)
            return {"speak": clean_response}
        
        # Check for admin commands
        admin_response = access_controller.process_admin_command(auth_result, request.message)
        if admin_response:
            clean_admin_response = buddy.voice_processor.optimize_for_voice(admin_response)
            return {"speak": clean_admin_response}
        
        # Process voice-optimized message with sophisticated conversation flow
        headers = dict(http_request.headers)
        is_iphone = buddy.voice_processor.is_iphone_request(headers)
        
        response = await buddy.process_message(
            request.message, 
            auth_result.user_id, 
            auth_result, 
            is_voice=True, 
            headers=headers
        )
        
        # Response is already optimized for voice in buddy.process_message
        return {"speak": response}
        
    except Exception as e:
        error_response = buddy.voice_processor.create_voice_confirmation("error")
        return {"speak": error_response}

@app.get("/personality")
async def get_personality(http_request: Request):
    headers = dict(http_request.headers)
    auth_result = auth_manager.authenticate_request(headers, "", "anonymous")
    
    personality_info = buddy.get_personality_info()
    personality_info["security_status"] = {
        "authenticated": auth_result.authenticated,
        "user_role": auth_result.role.value,
        "auth_method": auth_result.method
    }
    
    return personality_info

@app.get("/security/status")
async def security_status(http_request: Request):
    headers = dict(http_request.headers)
    auth_result = auth_manager.authenticate_request(headers, "", "anonymous")
    
    if auth_result.role.value != "master":
        raise HTTPException(status_code=403, detail="Master authentication required")
    
    return auth_manager.get_security_status()

@app.get("/admin/logs")
async def admin_logs(http_request: Request, limit: int = 50):
    headers = dict(http_request.headers)
    auth_result = auth_manager.authenticate_request(headers, "", "admin")
    
    if auth_result.role.value != "master":
        raise HTTPException(status_code=403, detail="Master authentication required")
    
    return {"logs": auth_manager.get_authentication_logs(limit)}

@app.get("/admin/improvements")
async def get_improvements(http_request: Request):
    headers = dict(http_request.headers)
    auth_result = auth_manager.authenticate_request(headers, "", "admin")
    
    if auth_result.role.value != "master":
        raise HTTPException(status_code=403, detail="Master authentication required")
    
    return {
        "status": buddy.self_improvement.get_improvement_status(),
        "history": buddy.self_improvement.get_improvement_history()
    }

@app.post("/voice")
async def voice_endpoint(message: str = Form(...), user_id: str = Form("Arindam"), http_request: Request = None):
    """Plain text endpoint for direct voice integration (alternative to JSON)."""
    try:
        # Convert to ChatRequest format
        request = ChatRequest(message=message, user_id=user_id)
        
        # Use the same logic as siri_chat
        headers = dict(http_request.headers)
        auth_result = auth_manager.authenticate_request(headers, request.message, request.user_id)
        
        access_info = access_controller.check_message_access(auth_result, request.message)
        
        if not access_info["allowed"]:
            cinematic_response = access_info.get("cinematic_response", "Authentication required. Please say happy birthday.")
            clean_response = buddy.voice_processor.optimize_for_voice(cinematic_response)
            return {"response": clean_response}
        
        admin_response = access_controller.process_admin_command(auth_result, request.message)
        if admin_response:
            clean_admin_response = buddy.voice_processor.optimize_for_voice(admin_response)
            return {"response": clean_admin_response}
        
        response = await buddy.process_message(
            request.message, 
            auth_result.user_id, 
            auth_result, 
            is_voice=True, 
            headers=headers
        )
        
        return {"response": response}
        
    except Exception as e:
        error_response = buddy.voice_processor.create_voice_confirmation("error")
        return {"response": error_response}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )