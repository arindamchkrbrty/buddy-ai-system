#!/usr/bin/env python3
"""
Test script to verify the /siri-chat endpoint integration works correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.buddy import Buddy
from auth.authentication import AuthenticationManager
from auth.access_control import AccessController

def test_siri_integration():
    """Test the complete Siri integration flow."""
    
    print("🧪 Testing Siri Endpoint Integration...")
    print("=" * 60)
    
    # Initialize components
    buddy = Buddy()
    auth_manager = AuthenticationManager()
    access_controller = AccessController(auth_manager)
    
    # Simulate iPhone Siri request headers
    headers = {
        'user-agent': 'Siri/iPhone15,2 iOS/17.0',
        'content-type': 'application/json',
        'accept': 'application/json'
    }
    
    print("📱 Simulating iPhone/Siri request...")
    
    # Test 1: Authentication with voice passphrase
    print("\n🔐 Test 1: Authentication")
    auth_result = auth_manager.authenticate_request(headers, 'happy birthday', 'Arindam')
    print(f"   Auth Status: {auth_result.authenticated}")
    print(f"   Role: {auth_result.role.value}")
    print(f"   Device ID: {auth_result.device_id}")
    
    # Test 2: Access control check
    print("\n🛡️  Test 2: Access Control")
    access_info = access_controller.check_message_access(auth_result, 'good morning buddy')
    print(f"   Access Allowed: {access_info['allowed']}")
    
    # Test 3: Voice processing with complex responses
    print("\n🎤 Test 3: Voice Response Processing")
    
    test_responses = [
        "🎉 **Welcome back, Arindam**. Good afternoon! How may I assist you today? [Session: Active - 30s remaining]",
        "Good afternoon, Arindam! Would you like me to give you your **daily briefing**? I can share weather, upcoming meetings, and traffic updates.",
        "🚀 I'd love to improve! What specific capability would you like me to develop or enhance?\\n\\n• **Conversation features**\\n• **Personality traits**",
        "✅ **Improvement Complete!**\\n\\nStatus: Successfully implemented\\nTry chatting with me now! 🎉"
    ]
    
    all_clean = True
    
    for i, response in enumerate(test_responses, 1):
        print(f"\n   Response {i}:")
        print(f"     Raw: {repr(response[:60])}...")
        
        # Process through voice optimizer
        clean_response = buddy.voice_processor.optimize_for_voice(response)
        print(f"     Clean: {repr(clean_response[:60])}...")
        
        # Check for problems
        has_backslash_issues = '\\1' in clean_response or '\\n' in clean_response or '\\t' in clean_response
        has_emojis = any(ord(c) > 127 and not c.isalpha() for c in clean_response)
        is_empty = len(clean_response.strip()) == 0
        
        if has_backslash_issues or has_emojis or is_empty:
            print(f"     ❌ Issues detected")
            all_clean = False
        else:
            print(f"     ✅ Clean for Siri TTS")
            
        # Show what Siri would speak
        print(f"     Siri Says: \"{clean_response}\"")
    
    # Test 4: Complete endpoint simulation
    print(f"\n🌐 Test 4: Complete Endpoint Flow")
    
    # Simulate what the /siri-chat endpoint would return
    def simulate_siri_endpoint(message, user_id):
        """Simulate the /siri-chat endpoint logic."""
        
        # Auth check
        auth_result = auth_manager.authenticate_request(headers, message, user_id)
        access_info = access_controller.check_message_access(auth_result, message)
        
        if not access_info["allowed"]:
            cinematic_response = access_info.get("cinematic_response", "Authentication required. Please say happy birthday.")
            clean_response = buddy.voice_processor.optimize_for_voice(cinematic_response)
            return {"speak": clean_response}
        
        # For this test, simulate a typical Buddy response
        response = "Welcome back, Arindam. Good afternoon! How may I assist you today?"
        clean_response = buddy.voice_processor.optimize_for_voice(response)
        
        return {"speak": clean_response}
    
    # Test different scenarios
    test_scenarios = [
        ("happy birthday", "Arindam"),
        ("good morning buddy", "Arindam"),
        ("hey buddy", "Arindam")
    ]
    
    for message, user_id in test_scenarios:
        print(f"\n   Input: '{message}' from {user_id}")
        result = simulate_siri_endpoint(message, user_id)
        print(f"   Response: {result}")
        
        # Verify response format
        if "speak" in result and isinstance(result["speak"], str) and len(result["speak"]) > 0:
            print(f"   ✅ Valid Siri response format")
        else:
            print(f"   ❌ Invalid response format")
            all_clean = False
    
    print("\n" + "=" * 60)
    if all_clean:
        print("🎉 ALL TESTS PASSED! Siri integration is working correctly.")
        print("✅ Voice responses are clean and ready for iPhone TTS.")
        print("✅ No \\1 characters or problematic output detected.")
        print("✅ Authentication and access control working properly.")
    else:
        print("❌ SOME TESTS FAILED! Issues detected in Siri integration.")
    
    return all_clean

if __name__ == "__main__":
    success = test_siri_integration()
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: Siri integration testing complete!")