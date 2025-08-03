from fastapi import FastAPI, HTTPException, Request
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
    try:
        # Extract headers for iPhone device authentication
        headers = dict(http_request.headers)
        
        # Authenticate request - iPhone devices get automatic priority
        auth_result = auth_manager.authenticate_request(headers, request.message, request.user_id)
        
        # Check access permissions
        access_info = access_controller.check_message_access(auth_result, request.message)
        
        if not access_info["allowed"]:
            # Use cinematic response for Siri
            cinematic_response = access_info.get("cinematic_response", "Authentication required. Please use the passphrase.")
            return {"speak": cinematic_response}
        
        # Check for admin commands
        admin_response = access_controller.process_admin_command(auth_result, request.message)
        if admin_response:
            return {"speak": admin_response}
        
        # Process normal message with sophisticated conversation flow
        response = await buddy.process_message(request.message, auth_result.user_id, auth_result)
        
        # Check if response already came from conversation manager or self-improvement
        is_special_response = any(phrase in response for phrase in [
            "Welcome back, Arindam", "daily briefing", "Session expired", 
            "Would you like me to give you your daily briefing", "I'd love to improve",
            "Analysis Complete", "Implementation Plan", "Improvement Complete"
        ])
        
        if is_special_response:
            # Use special response directly for Siri (clean up debug info)
            clean_response = response.split(" [Session:")[0]  # Remove debug info
            return {"speak": clean_response}
        else:
            # Filter response for voice - no auth prefixes for Siri
            filtered_response = access_controller.filter_response_for_access_level(response, auth_result)
            
            # Add cinematic authentication confirmation for voice
            if auth_result.authenticated and auth_result.method == "cinematic_passphrase":
                filtered_response = "Welcome back, Arindam. All systems are now at your command. " + filtered_response
            elif auth_result.authenticated and auth_result.method == "jwt_token":
                # Get time-based greeting
                current_hour = datetime.now().hour
                if current_hour < 12:
                    greeting = "morning"
                elif current_hour < 17:
                    greeting = "afternoon"
                else:
                    greeting = "evening"
                filtered_response = f"Good {greeting}, {auth_result.user_id}. " + filtered_response
            
            return {"speak": filtered_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )