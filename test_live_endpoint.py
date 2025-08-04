#!/usr/bin/env python3
"""
Test the live /siri-chat endpoint to verify the fix works in production.
"""

import requests
import json
import subprocess
import time
import signal
import os
from threading import Thread

def start_server():
    """Start the FastAPI server in the background."""
    try:
        # Start server process
        process = subprocess.Popen([
            'python', 'main.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Give server time to start
        time.sleep(3)
        
        return process
    except Exception as e:
        print(f"Failed to start server: {e}")
        return None

def test_endpoint():
    """Test the /siri-chat endpoint."""
    
    url = "http://localhost:8000/siri-chat"
    
    # Test cases
    test_cases = [
        {
            "message": "happy birthday",
            "user_id": "Arindam"
        },
        {
            "message": "good morning buddy", 
            "user_id": "Arindam"
        },
        {
            "message": "hey buddy how are you",
            "user_id": "Arindam"
        }
    ]
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Siri/iPhone15,2 iOS/17.0',
        'Accept': 'application/json'
    }
    
    print("🧪 Testing Live /siri-chat Endpoint...")
    print("=" * 60)
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📱 Test {i}: '{test_case['message']}'")
        
        try:
            response = requests.post(url, json=test_case, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if "speak" in data:
                    speak_text = data["speak"]
                    
                    # Check for problematic characters
                    has_backslash_issues = '\\1' in speak_text or '\\n' in speak_text or '\\t' in speak_text
                    has_emojis = any(ord(c) > 127 and not c.isalpha() for c in speak_text)
                    is_empty = len(speak_text.strip()) == 0
                    
                    print(f"   Response: {json.dumps(data, indent=2)}")
                    print(f"   Speak Text: \"{speak_text}\"")
                    
                    if has_backslash_issues:
                        print(f"   ❌ FAIL: Contains escape sequences")
                        all_passed = False
                    elif has_emojis:
                        print(f"   ❌ FAIL: Contains emojis")
                        all_passed = False
                    elif is_empty:
                        print(f"   ❌ FAIL: Empty response")
                        all_passed = False
                    else:
                        print(f"   ✅ PASS: Clean voice response ready for Siri")
                        
                else:
                    print(f"   ❌ FAIL: No 'speak' field in response")
                    all_passed = False
                    
            else:
                print(f"   ❌ FAIL: HTTP {response.status_code}: {response.text}")
                all_passed = False
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ FAIL: Could not connect to server")
            all_passed = False
        except requests.exceptions.Timeout:
            print(f"   ❌ FAIL: Request timeout")
            all_passed = False
        except Exception as e:
            print(f"   ❌ FAIL: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL LIVE TESTS PASSED!")
        print("✅ /siri-chat endpoint is working correctly")
        print("✅ Voice responses are clean and Siri-ready")
        print("✅ No \\1 characters or escape sequences detected")
    else:
        print("❌ SOME LIVE TESTS FAILED!")
    
    return all_passed

if __name__ == "__main__":
    print("🚀 Starting FastAPI server for live testing...")
    
    # Check if server is already running
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server already running")
            server_process = None
        else:
            raise requests.exceptions.ConnectionError()
    except:
        print("⏳ Starting server...")
        server_process = start_server()
        
        if not server_process:
            print("❌ Failed to start server")
            exit(1)
    
    try:
        # Test the endpoint
        success = test_endpoint()
        
        print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: Live endpoint testing complete!")
        
    finally:
        # Clean up server if we started it
        if server_process:
            print("\n🛑 Shutting down server...")
            server_process.terminate()
            server_process.wait()