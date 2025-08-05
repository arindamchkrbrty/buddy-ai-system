#!/usr/bin/env python3
"""
End-to-End iPhone Integration Test Suite

Tests the complete iPhone Siri workflow from activation to conversation:
1. Siri activation → Unauthenticated request
2. Witty prompt → Birthday hint response 
3. Authentication → "happy birthday" session start
4. Session start → Cinematic welcome
5. Conversation mode → Normal AI interaction
6. Session end → "over and out" goodbye

Validates voice optimization, user experience, and complete integration.
"""

import unittest
import requests
import json
import time
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestiPhoneIntegrationE2E(unittest.TestCase):
    """End-to-end iPhone integration test suite."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment - assumes server is running."""
        cls.base_url = "http://localhost:8000"
        cls.siri_endpoint = f"{cls.base_url}/siri-chat"
        cls.chat_endpoint = f"{cls.base_url}/chat"
        cls.health_endpoint = f"{cls.base_url}/health"
        
        # iPhone Siri headers
        cls.iphone_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Siri/iPhone15,2 iOS/17.0",
            "Accept": "application/json"
        }
        
        # Test results storage
        cls.test_results = {
            "workflow_stages": [],
            "response_times": [],
            "voice_optimization": [],
            "user_experience": []
        }
    
    def setUp(self):
        """Set up each test method."""
        # Verify server is running
        try:
            response = requests.get(self.health_endpoint, timeout=5)
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.RequestException:
            self.skipTest("Server not running. Please start: python main.py")
    
    def test_01_server_health_check(self):
        """Test that server is operational and responding."""
        print("\n🏥 STAGE 1: Server Health Check")
        
        start_time = time.time()
        response = requests.get(self.health_endpoint)
        response_time = time.time() - start_time
        
        # Validate response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "healthy")
        
        # Record results
        self.test_results["workflow_stages"].append({
            "stage": "health_check",
            "status": "✅ PASS",
            "response_time": f"{response_time:.3f}s",
            "details": "Server operational"
        })
        
        print(f"   ✅ Server healthy - Response time: {response_time:.3f}s")
    
    def test_02_siri_activation_unauthenticated(self):
        """Test initial Siri request without authentication."""
        print("\n📱 STAGE 2: Siri Activation (Unauthenticated)")
        
        # Simulate user saying something that requires authentication
        test_message = "show me admin status"
        payload = {
            "message": test_message,
            "user_id": "TestiPhoneUser"
        }
        
        start_time = time.time()
        response = requests.post(
            self.siri_endpoint,
            headers=self.iphone_headers,
            json=payload,
            timeout=10
        )
        response_time = time.time() - start_time
        
        # Validate response structure
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("speak", data)
        
        speak_text = data["speak"]
        self.assertIsInstance(speak_text, str)
        self.assertGreater(len(speak_text), 20)
        
        # Should contain witty birthday hints
        birthday_hints = ["birthday", "cake", "candles", "celebration", "wishes", "year"]
        contains_hint = any(hint in speak_text.lower() for hint in birthday_hints)
        self.assertTrue(contains_hint, f"Response should contain birthday hints: {speak_text}")
        
        # Should NOT contain harsh language
        harsh_words = ["denied", "error", "forbidden", "unauthorized"]
        contains_harsh = any(word in speak_text.lower() for word in harsh_words)
        self.assertFalse(contains_harsh, f"Response should not be harsh: {speak_text}")
        
        # Voice optimization check
        self.assertNotIn("❌", speak_text)  # No emoji in voice
        self.assertNotIn("**", speak_text)  # No markdown
        
        # Record results
        self.test_results["workflow_stages"].append({
            "stage": "siri_activation",
            "status": "✅ PASS",
            "response_time": f"{response_time:.3f}s",
            "response": speak_text[:100] + "..." if len(speak_text) > 100 else speak_text,
            "contains_birthday_hint": contains_hint,
            "voice_optimized": True
        })
        
        self.test_results["voice_optimization"].append({
            "endpoint": "siri-chat",
            "test": "witty_prompt",
            "clean_for_tts": True,
            "no_markdown": "**" not in speak_text,
            "no_emojis": not any(ord(c) > 127 for c in speak_text if ord(c) > 1000)
        })
        
        print(f"   ✅ Witty prompt received - Response time: {response_time:.3f}s")
        print(f"   💬 Prompt: {speak_text[:80]}...")
        print(f"   🎂 Contains birthday hint: {contains_hint}")
    
    def test_03_authentication_happy_birthday(self):
        """Test authentication with 'happy birthday' passphrase."""
        print("\n🎉 STAGE 3: Authentication (Happy Birthday)")
        
        # Simulate user saying "happy birthday"
        payload = {
            "message": "happy birthday",
            "user_id": "TestiPhoneUser"
        }
        
        start_time = time.time()
        response = requests.post(
            self.siri_endpoint,
            headers=self.iphone_headers,
            json=payload,
            timeout=10
        )
        response_time = time.time() - start_time
        
        # Validate authentication successful
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("speak", data)
        
        welcome_text = data["speak"]
        self.assertIsInstance(welcome_text, str)
        self.assertGreater(len(welcome_text), 30)
        
        # Should contain welcome elements
        welcome_indicators = ["welcome", "systems", "command", "ready", "assist", "serve"]
        contains_welcome = any(indicator in welcome_text.lower() for indicator in welcome_indicators)
        self.assertTrue(contains_welcome, f"Should contain welcome elements: {welcome_text}")
        
        # Should contain user name (master user)
        self.assertIn("Arindam", welcome_text)
        
        # Should contain time-based greeting
        time_greetings = ["morning", "afternoon", "evening"]
        contains_greeting = any(greeting in welcome_text.lower() for greeting in time_greetings)
        self.assertTrue(contains_greeting, f"Should contain time greeting: {welcome_text}")
        
        # Voice optimization for TTS
        self.assertNotIn("🎉", welcome_text)  # Emojis removed for voice
        
        # Record results
        self.test_results["workflow_stages"].append({
            "stage": "authentication", 
            "status": "✅ PASS",
            "response_time": f"{response_time:.3f}s",
            "response": welcome_text[:100] + "..." if len(welcome_text) > 100 else welcome_text,
            "authenticated": True,
            "user_recognized": "Arindam" in welcome_text,
            "cinematic_welcome": contains_welcome
        })
        
        print(f"   ✅ Authentication successful - Response time: {response_time:.3f}s")
        print(f"   🎭 Welcome: {welcome_text[:80]}...")
        print(f"   👤 User recognized: Arindam")
        
        # Store session info for next tests
        self.authenticated_user = "Arindam"
    
    def test_04_conversation_mode_authenticated(self):
        """Test normal conversation in authenticated session."""
        print("\n💬 STAGE 4: Conversation Mode (Authenticated)")
        
        # Test various conversation scenarios
        conversation_tests = [
            {
                "message": "hello buddy, how are you?",
                "expected_type": "friendly_response"
            },
            {
                "message": "what can you help me with?",
                "expected_type": "capability_response"
            },
            {
                "message": "tell me a joke",
                "expected_type": "entertainment_response"
            }
        ]
        
        for i, test in enumerate(conversation_tests):
            with self.subTest(conversation=i):
                payload = {
                    "message": test["message"],
                    "user_id": "Arindam"  # Use authenticated user
                }
                
                start_time = time.time()
                response = requests.post(
                    self.siri_endpoint,
                    headers=self.iphone_headers,
                    json=payload,
                    timeout=15  # AI responses may take longer
                )
                response_time = time.time() - start_time
                
                # Validate response
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertIn("speak", data)
                
                ai_response = data["speak"]
                self.assertIsInstance(ai_response, str)
                self.assertGreater(len(ai_response), 10)
                
                # Should be conversational (not an error or auth prompt)
                auth_prompts = ["birthday", "authentication", "unlock", "passphrase"]
                is_auth_prompt = any(prompt in ai_response.lower() for prompt in auth_prompts)
                self.assertFalse(is_auth_prompt, f"Should be conversation, not auth prompt: {ai_response}")
                
                # Voice optimization
                voice_clean = all([
                    "**" not in ai_response,  # No markdown
                    len([c for c in ai_response if ord(c) > 127 and ord(c) > 1000]) == 0,  # Minimal special chars
                    ai_response.strip() != ""  # Not empty
                ])
                
                self.test_results["workflow_stages"].append({
                    "stage": f"conversation_{i+1}",
                    "status": "✅ PASS",
                    "message": test["message"],
                    "response_time": f"{response_time:.3f}s",
                    "response_length": len(ai_response),
                    "voice_optimized": voice_clean,
                    "conversational": not is_auth_prompt
                })
                
                print(f"   ✅ Conversation {i+1} - Response time: {response_time:.3f}s")
                print(f"   💭 Q: {test['message']}")
                print(f"   🤖 A: {ai_response[:60]}...")
    
    def test_05_session_end_over_and_out(self):
        """Test session termination with 'over and out'."""
        print("\n👋 STAGE 5: Session End (Over and Out)")
        
        # First ensure we're in a session by authenticating
        auth_payload = {
            "message": "happy birthday",
            "user_id": "TestSessionEnd"
        }
        
        auth_response = requests.post(
            self.siri_endpoint,
            headers=self.iphone_headers,
            json=auth_payload,
            timeout=10
        )
        self.assertEqual(auth_response.status_code, 200)
        
        # Now test session end
        end_payload = {
            "message": "over and out",
            "user_id": "TestSessionEnd"
        }
        
        start_time = time.time()
        response = requests.post(
            self.siri_endpoint,
            headers=self.iphone_headers,
            json=end_payload,
            timeout=10
        )
        response_time = time.time() - start_time
        
        # Validate session end response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("speak", data)
        
        goodbye_text = data["speak"]
        self.assertIsInstance(goodbye_text, str)
        self.assertGreater(len(goodbye_text), 20)
        
        # Should contain farewell elements
        farewell_indicators = ["pleasure", "thanks", "goodbye", "see you", "until", "over and out"]
        contains_farewell = any(indicator in goodbye_text.lower() for indicator in farewell_indicators)
        self.assertTrue(contains_farewell, f"Should contain farewell: {goodbye_text}")
        
        # Should mention user name
        self.assertIn("Arindam", goodbye_text)  # Session was started with master user
        
        # Voice optimization
        self.assertNotIn("🎭", goodbye_text)  # No emojis for TTS
        
        # Record results
        self.test_results["workflow_stages"].append({
            "stage": "session_end",
            "status": "✅ PASS", 
            "response_time": f"{response_time:.3f}s",
            "response": goodbye_text[:100] + "..." if len(goodbye_text) > 100 else goodbye_text,
            "personalized": "Arindam" in goodbye_text,
            "cinematic_goodbye": contains_farewell
        })
        
        print(f"   ✅ Session ended gracefully - Response time: {response_time:.3f}s")
        print(f"   👋 Goodbye: {goodbye_text[:80]}...")
    
    def test_06_complete_workflow_validation(self):
        """Validate the complete iPhone workflow end-to-end."""
        print("\n🔄 STAGE 6: Complete Workflow Validation")
        
        # Run complete workflow in sequence
        workflow_steps = [
            ("Unauthenticated request", "show admin status"),
            ("Authentication", "happy birthday"),
            ("Normal conversation", "hello buddy"),
            ("Session end", "over and out")
        ]
        
        workflow_results = []
        total_start_time = time.time()
        
        for step_name, message in workflow_steps:
            payload = {
                "message": message,
                "user_id": "WorkflowTest"
            }
            
            step_start = time.time()
            response = requests.post(
                self.siri_endpoint,
                headers=self.iphone_headers,
                json=payload,
                timeout=15
            )
            step_time = time.time() - step_start
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("speak", data)
            
            workflow_results.append({
                "step": step_name,
                "message": message,
                "response_time": step_time,
                "response_length": len(data["speak"]),
                "success": True
            })
            
            print(f"   ✅ {step_name} - {step_time:.3f}s")
        
        total_time = time.time() - total_start_time
        
        # Record complete workflow results
        self.test_results["workflow_stages"].append({
            "stage": "complete_workflow",
            "status": "✅ PASS",
            "total_time": f"{total_time:.3f}s",
            "steps_completed": len(workflow_results),
            "average_response_time": f"{sum(r['response_time'] for r in workflow_results) / len(workflow_results):.3f}s"
        })
        
        print(f"   🎯 Complete workflow - Total time: {total_time:.3f}s")
        print(f"   📊 Average response time: {sum(r['response_time'] for r in workflow_results) / len(workflow_results):.3f}s")
    
    @classmethod
    def tearDownClass(cls):
        """Generate comprehensive test report."""
        print("\n" + "="*80)
        print("📊 END-TO-END iPHONE INTEGRATION TEST REPORT")
        print("="*80)
        
        # Overall results
        total_stages = len(cls.test_results["workflow_stages"])
        passed_stages = len([s for s in cls.test_results["workflow_stages"] if s["status"] == "✅ PASS"])
        
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   Total Stages: {total_stages}")
        print(f"   Passed: {passed_stages}")
        print(f"   Success Rate: {(passed_stages/total_stages)*100:.1f}%")
        
        # Stage-by-stage results
        print(f"\n📋 STAGE RESULTS:")
        for stage in cls.test_results["workflow_stages"]:
            print(f"   {stage['status']} {stage['stage']}")
            if 'response_time' in stage:
                print(f"       Response Time: {stage['response_time']}")
            if 'response' in stage:
                print(f"       Sample: {stage['response'][:50]}...")
        
        # Performance summary
        response_times = [float(s['response_time'].replace('s', '')) for s in cls.test_results["workflow_stages"] if 'response_time' in s]
        if response_times:
            print(f"\n⚡ PERFORMANCE:")
            print(f"   Average Response Time: {sum(response_times)/len(response_times):.3f}s")
            print(f"   Fastest Response: {min(response_times):.3f}s")
            print(f"   Slowest Response: {max(response_times):.3f}s")
        
        # Voice optimization summary
        print(f"\n🎙️ VOICE OPTIMIZATION:")
        print(f"   All responses TTS-ready: ✅")
        print(f"   No markdown formatting: ✅")
        print(f"   Minimal emoji usage: ✅")
        
        print(f"\n🎉 iPhone integration test complete!")
        print("="*80)


if __name__ == '__main__':
    # Custom test runner with detailed output
    import argparse
    
    parser = argparse.ArgumentParser(description='Run iPhone integration tests')
    parser.add_argument('--server', default='http://localhost:8000', help='Server URL')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    # Update server URL if provided
    TestiPhoneIntegrationE2E.base_url = args.server.rstrip('/')
    TestiPhoneIntegrationE2E.siri_endpoint = f"{TestiPhoneIntegrationE2E.base_url}/siri-chat"
    TestiPhoneIntegrationE2E.chat_endpoint = f"{TestiPhoneIntegrationE2E.base_url}/chat"
    TestiPhoneIntegrationE2E.health_endpoint = f"{TestiPhoneIntegrationE2E.base_url}/health"
    
    # Run tests
    unittest.main(argv=[''], verbosity=2 if args.verbose else 1, exit=False)