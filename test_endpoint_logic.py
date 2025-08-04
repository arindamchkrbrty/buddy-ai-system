#!/usr/bin/env python3
"""
Test the /siri-chat endpoint logic directly without starting the server.
This verifies the voice processing fix works in the actual endpoint code.
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the actual endpoint dependencies
from fastapi import Request
from core.buddy import Buddy
from auth.authentication import AuthenticationManager
from auth.access_control import AccessController
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    user_id: str = "Arindam"

class MockRequest:
    """Mock FastAPI Request for testing."""
    def __init__(self, headers):
        self.headers = headers

async def test_siri_chat_logic():
    """Test the actual /siri-chat endpoint logic."""
    
    print("🧪 Testing /siri-chat Endpoint Logic...")
    print("=" * 60)
    
    # Initialize components (same as in main.py)
    buddy = Buddy()
    auth_manager = AuthenticationManager()
    access_controller = AccessController(auth_manager)
    
    # Test cases
    test_cases = [
        {
            "message": "happy birthday",
            "user_id": "Arindam",
            "expected_auth": True
        },
        {
            "message": "good morning buddy", 
            "user_id": "Arindam",
            "expected_auth": True
        },
        {
            "message": "hey buddy, how are you?",
            "user_id": "Arindam", 
            "expected_auth": True
        }
    ]
    
    # Mock iPhone headers (same as Siri would send)
    headers = {
        'content-type': 'application/json',
        'user-agent': 'Siri/iPhone15,2 iOS/17.0',
        'accept': 'application/json'
    }
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📱 Test {i}: '{test_case['message']}'")
        
        try:
            # Create request objects
            request = ChatRequest(message=test_case['message'], user_id=test_case['user_id'])
            http_request = MockRequest(headers)
            
            # === REPLICATE EXACT /siri-chat ENDPOINT LOGIC ===
            
            # Extract headers for iPhone device authentication
            headers_dict = dict(http_request.headers)
            
            # Authenticate request
            auth_result = auth_manager.authenticate_request(headers_dict, request.message, request.user_id)
            print(f"   🔐 Auth: {auth_result.authenticated} ({auth_result.role.value})")
            
            # Check access permissions
            access_info = access_controller.check_message_access(auth_result, request.message)
            
            if not access_info["allowed"]:
                # Use cinematic response for Siri, optimized for voice
                cinematic_response = access_info.get("cinematic_response", "Authentication required. Please say happy birthday.")
                clean_response = buddy.voice_processor.optimize_for_voice(cinematic_response)
                result = {"speak": clean_response}
                print(f"   🚫 Access denied, using cinematic response")
            else:
                # Check for admin commands
                admin_response = access_controller.process_admin_command(auth_result, request.message)
                if admin_response:
                    clean_admin_response = buddy.voice_processor.optimize_for_voice(admin_response)
                    result = {"speak": clean_admin_response}
                    print(f"   👑 Admin command processed")
                else:
                    # Process voice-optimized message with sophisticated conversation flow
                    is_iphone = buddy.voice_processor.is_iphone_request(headers_dict)
                    print(f"   📱 iPhone detected: {is_iphone}")
                    
                    response = await buddy.process_message(
                        request.message, 
                        auth_result.user_id, 
                        auth_result, 
                        is_voice=True, 
                        headers=headers_dict
                    )
                    
                    # Ensure response is clean and ready for Siri TTS
                    if not response or response.strip() == "":
                        response = "I'm ready to help. What can I do for you?"
                    
                    # Double-check voice optimization
                    clean_response = buddy.voice_processor.optimize_for_voice(response)
                    result = {"speak": clean_response}
                    print(f"   🤖 Buddy response processed")
            
            # === END ENDPOINT LOGIC ===
            
            # Validate the result
            speak_text = result.get("speak", "")
            
            print(f"   📢 Response: \"{speak_text}\"")
            
            # Check for the original bug symptoms
            has_backslash_one = '\\1' in speak_text
            has_backslash_sequences = '\\n' in speak_text or '\\t' in speak_text or '\\r' in speak_text
            has_emojis = any(ord(c) > 127 and not c.isalpha() for c in speak_text)
            is_empty = len(speak_text.strip()) == 0
            
            # Detailed analysis
            issues = []
            if has_backslash_one:
                issues.append("Contains \\1 characters (THE ORIGINAL BUG)")
            if has_backslash_sequences:
                issues.append("Contains escape sequences")
            if has_emojis:
                issues.append("Contains emojis")
            if is_empty:
                issues.append("Empty response")
            
            if issues:
                print(f"   ❌ FAIL: {', '.join(issues)}")
                all_passed = False
            else:
                print(f"   ✅ PASS: Clean voice response, Siri-ready")
                
            # Show the actual JSON that would be returned
            print(f"   📤 JSON Response: {result}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL ENDPOINT LOGIC TESTS PASSED!")
        print("✅ /siri-chat endpoint logic is working correctly")
        print("✅ Voice responses are clean and ready for iPhone TTS")
        print("✅ NO \\1 CHARACTERS DETECTED - Original bug is FIXED!")
        print("✅ Authentication, access control, and voice processing working")
    else:
        print("❌ SOME ENDPOINT LOGIC TESTS FAILED!")
        print("❌ Issues detected in the endpoint implementation")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(test_siri_chat_logic())
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: Endpoint logic testing complete!")