#!/usr/bin/env python3
"""
Test network requests to ensure proper JSON responses.
Tests both localhost and network access scenarios.
"""

import requests
import json
import subprocess
import time
import socket
import signal
import os
from threading import Thread

def get_local_ip():
    """Get the local IP address for network testing."""
    try:
        # Connect to a remote server to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def start_server_background():
    """Start the server in background for testing."""
    try:
        # Start the server process
        process = subprocess.Popen(
            ["python", "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create process group for clean shutdown
        )
        
        # Give server time to start
        time.sleep(5)
        
        return process
    except Exception as e:
        print(f"Failed to start server: {e}")
        return None

def test_endpoint(url, test_name, headers=None):
    """Test a specific endpoint and return results."""
    
    if headers is None:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    test_data = {
        "message": "hello buddy",
        "user_id": "TestUser"
    }
    
    print(f"\n🧪 Testing {test_name}")
    print(f"   URL: {url}")
    print(f"   Headers: {headers}")
    
    try:
        response = requests.post(url, json=test_data, headers=headers, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                print(f"   ✅ SUCCESS: Got JSON response")
                print(f"   Response Keys: {list(json_data.keys())}")
                print(f"   Response Sample: {str(json_data)[:200]}...")
                return True
            except json.JSONDecodeError:
                print(f"   ❌ FAILED: Response is not valid JSON")
                print(f"   Raw Response: {response.text[:200]}...")
                return False
        else:
            print(f"   ❌ FAILED: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ FAILED: Connection refused - server not running?")
        return False
    except requests.exceptions.Timeout:
        print(f"   ❌ FAILED: Request timeout")
        return False
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

def test_network_requests():
    """Test network requests for JSON responses."""
    
    print("🌐 Testing Network Request JSON Responses")
    print("=" * 60)
    
    # Get network configuration
    local_ip = get_local_ip()
    port = 8000
    
    print(f"📋 Network Configuration:")
    print(f"   Local IP: {local_ip}")
    print(f"   Port: {port}")
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Localhost /chat",
            "url": f"http://localhost:{port}/chat",
            "headers": {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        },
        {
            "name": "Network IP /chat", 
            "url": f"http://{local_ip}:{port}/chat",
            "headers": {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        },
        {
            "name": "Localhost /siri-chat",
            "url": f"http://localhost:{port}/siri-chat",
            "headers": {
                'Content-Type': 'application/json',
                'User-Agent': 'Siri/iPhone15,2 iOS/17.0'
            }
        },
        {
            "name": "Network IP /siri-chat (iPhone simulation)",
            "url": f"http://{local_ip}:{port}/siri-chat", 
            "headers": {
                'Content-Type': 'application/json',
                'User-Agent': 'Siri/iPhone15,2 iOS/17.0',
                'Accept': 'application/json'
            }
        }
    ]
    
    # Check if server is already running
    server_process = None
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server already running")
        else:
            raise requests.exceptions.ConnectionError()
    except:
        print("⏳ Starting server for testing...")
        server_process = start_server_background()
        
        if not server_process:
            print("❌ Failed to start server")
            return False
    
    # Run tests
    results = []
    try:
        for scenario in test_scenarios:
            result = test_endpoint(
                scenario["url"], 
                scenario["name"], 
                scenario["headers"]
            )
            results.append(result)
            time.sleep(1)  # Brief pause between tests
        
        # Summary
        print(f"\n" + "=" * 60)
        passed = sum(results)
        total = len(results)
        
        if passed == total:
            print(f"🎉 ALL TESTS PASSED! ({passed}/{total})")
            print(f"✅ Network requests return proper JSON responses")
            print(f"✅ Both localhost and network access working")
            print(f"✅ iPhone/Siri integration ready")
        else:
            print(f"❌ SOME TESTS FAILED! ({passed}/{total})")
            print(f"❌ Network request issues detected")
        
        print(f"\n📱 iPhone Connection URLs:")
        print(f"   Siri Endpoint: http://{local_ip}:{port}/siri-chat")
        print(f"   Voice Endpoint: http://{local_ip}:{port}/voice")
        
        return passed == total
        
    finally:
        # Clean up server if we started it
        if server_process:
            print(f"\n🛑 Shutting down test server...")
            try:
                os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
                server_process.wait(timeout=5)
            except:
                try:
                    os.killpg(os.getpgid(server_process.pid), signal.SIGKILL)
                except:
                    pass

if __name__ == "__main__":
    success = test_network_requests()
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: Network request testing complete!")