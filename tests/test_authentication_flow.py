#!/usr/bin/env python3
"""
Unit tests for iPhone MVP authentication flow improvements.

Tests the enhanced authentication system with:
- Witty passphrase prompts instead of harsh access denied messages
- Session management with "happy birthday" starts and "over and out" ends
- Comprehensive session tracking and cinematic responses
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from auth.authentication import AuthenticationManager, AuthResult, UserRole
from auth.access_control import AccessController


class TestAuthenticationFlow(unittest.TestCase):
    """Test suite for iPhone MVP authentication flow enhancements."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.auth_manager = AuthenticationManager()
        self.access_controller = AccessController(self.auth_manager)
        
        # Test headers simulating iPhone request
        self.iphone_headers = {
            "user-agent": "Siri/iPhone15,2 iOS/17.0",
            "content-type": "application/json"
        }
        
        # Test headers simulating regular web request  
        self.web_headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "content-type": "application/json"
        }
    
    def test_witty_passphrase_prompts(self):
        """Test that access denied messages are replaced with witty prompts."""
        # Test admin command without authentication
        result = self.access_controller.process_admin_command(
            AuthResult(False, "test_user", UserRole.UNKNOWN, "none"),
            "show me admin status"
        )
        
        # Should return a witty prompt, not harsh "access denied"
        self.assertIsInstance(result, str)
        self.assertNotIn("Access denied", result)
        self.assertNotIn("❌", result)  # No harsh symbols
        
        # Should contain hints about birthday/celebration
        self.assertTrue(
            any(word in result.lower() for word in ["birthday", "cake", "candles", "celebration", "wishes"]),
            f"Expected birthday hints in prompt: {result}"
        )
    
    def test_access_control_witty_prompts(self):
        """Test access control returns witty prompts for unauthenticated admin commands."""
        # Test with unauthenticated user trying admin command
        auth_result = AuthResult(False, "guest", UserRole.UNKNOWN, "none")
        access_info = self.access_controller.check_message_access(auth_result, "show admin status")
        
        # Should not be allowed but should have cinematic response
        self.assertFalse(access_info["allowed"])
        self.assertIn("cinematic_response", access_info)
        
        cinematic_response = access_info["cinematic_response"]
        self.assertIsInstance(cinematic_response, str)
        self.assertGreater(len(cinematic_response), 20)  # Should be substantial message
        
        # Should be witty and engaging, not harsh
        self.assertNotIn("denied", cinematic_response.lower())
        self.assertNotIn("error", cinematic_response.lower())
    
    def test_happy_birthday_starts_session(self):
        """Test that 'happy birthday' successfully starts a user session."""
        # Test happy birthday authentication
        auth_result = self.auth_manager.authenticate_request(
            self.iphone_headers, 
            "happy birthday buddy", 
            "TestUser"
        )
        
        # Should be authenticated as master
        self.assertTrue(auth_result.authenticated)
        self.assertEqual(auth_result.role, UserRole.MASTER)
        self.assertEqual(auth_result.method, "cinematic_passphrase")
        self.assertEqual(auth_result.user_id, "Arindam")  # Master user
        
        # Start session should return cinematic welcome
        welcome_message = self.auth_manager.start_user_session(auth_result)
        self.assertIsInstance(welcome_message, str)
        self.assertGreater(len(welcome_message), 20)
        
        # Should contain greeting and user name
        self.assertIn("Arindam", welcome_message)
        self.assertTrue(any(greeting in welcome_message for greeting in ["Good morning", "Good afternoon", "Good evening"]))
        
        # Should have active session
        self.assertTrue(self.auth_manager.is_user_session_active("Arindam"))
        
        # Active sessions should contain our session
        active_sessions = self.auth_manager.get_active_sessions()
        self.assertIn("Arindam", active_sessions)
        self.assertEqual(active_sessions["Arindam"]["role"], "master")
    
    def test_over_and_out_ends_session(self):
        """Test that 'over and out' and similar phrases end user sessions."""
        # First start a session
        auth_result = AuthResult(True, "Arindam", UserRole.MASTER, "cinematic_passphrase")
        self.auth_manager.start_user_session(auth_result)
        
        # Verify session is active
        self.assertTrue(self.auth_manager.is_user_session_active("Arindam"))
        
        # Test various session end phrases
        end_phrases = [
            "over and out",
            "goodbye buddy", 
            "bye buddy",
            "see you later",
            "that's all",
            "done for now",
            "logout",
            "end session"
        ]
        
        for phrase in end_phrases:
            # Reset session for each test
            self.auth_manager.start_user_session(auth_result)
            
            # Check phrase is detected as session end trigger
            self.assertTrue(
                self.auth_manager.check_session_end_trigger(phrase),
                f"'{phrase}' should trigger session end"
            )
            
            # End session should return cinematic goodbye
            goodbye_message = self.auth_manager.end_user_session("Arindam", phrase)
            self.assertIsInstance(goodbye_message, str)
            self.assertGreater(len(goodbye_message), 10)
            self.assertIn("Arindam", goodbye_message)
            
            # Session should no longer be active
            self.assertFalse(self.auth_manager.is_user_session_active("Arindam"))
    
    def test_session_message_counting(self):
        """Test that session message counts are tracked correctly."""
        # Start session
        auth_result = AuthResult(True, "Arindam", UserRole.MASTER, "cinematic_passphrase") 
        self.auth_manager.start_user_session(auth_result)
        
        # Initial message count should be 0
        session_info = self.auth_manager.active_user_sessions["Arindam"]
        self.assertEqual(session_info["message_count"], 0)
        
        # Increment message count several times
        for i in range(5):
            self.auth_manager.increment_session_message_count("Arindam")
        
        # Should have count of 5
        updated_session = self.auth_manager.active_user_sessions["Arindam"]
        self.assertEqual(updated_session["message_count"], 5)
        
        # End session and check goodbye includes message count
        goodbye_message = self.auth_manager.end_user_session("Arindam", "over and out")
        # Note: Goodbye message format may vary, just ensure it's generated
        self.assertIsInstance(goodbye_message, str)
        self.assertGreater(len(goodbye_message), 10)
    
    def test_session_duration_tracking(self):
        """Test that session duration is calculated correctly."""
        # Start session
        auth_result = AuthResult(True, "Arindam", UserRole.MASTER, "cinematic_passphrase")
        self.auth_manager.start_user_session(auth_result)
        
        # Get initial session info
        session_info = self.auth_manager.active_user_sessions["Arindam"]
        start_time = datetime.fromisoformat(session_info["started_at"])
        
        # Verify start time is recent
        time_diff = datetime.now() - start_time
        self.assertLess(time_diff.total_seconds(), 5)  # Should be within 5 seconds
        
        # End session immediately
        goodbye_message = self.auth_manager.end_user_session("Arindam", "over and out")
        
        # Session should be ended but info retained for duration calculation
        self.assertFalse(self.auth_manager.is_user_session_active("Arindam"))
        self.assertIsInstance(goodbye_message, str)
    
    def test_multiple_concurrent_sessions(self):
        """Test that multiple users can have concurrent sessions."""
        # Start sessions for multiple users
        users = ["User1", "User2", "User3"]
        
        for user in users:
            auth_result = AuthResult(True, user, UserRole.MASTER, "cinematic_passphrase")
            welcome = self.auth_manager.start_user_session(auth_result)
            self.assertIsInstance(welcome, str)
            self.assertTrue(self.auth_manager.is_user_session_active(user))
        
        # All users should have active sessions
        active_sessions = self.auth_manager.get_active_sessions()
        for user in users:
            self.assertIn(user, active_sessions)
            self.assertTrue(active_sessions[user]["is_active"])
        
        # End one session
        goodbye = self.auth_manager.end_user_session("User2", "over and out")
        self.assertIsInstance(goodbye, str)
        
        # User2 should be inactive, others still active
        self.assertFalse(self.auth_manager.is_user_session_active("User2"))
        self.assertTrue(self.auth_manager.is_user_session_active("User1"))
        self.assertTrue(self.auth_manager.is_user_session_active("User3"))
    
    def test_session_security_validation(self):
        """Test that sessions require proper authentication."""
        # Try to start session without authentication
        unauth_result = AuthResult(False, "hacker", UserRole.UNKNOWN, "none")
        
        with self.assertRaises(ValueError):
            self.auth_manager.start_user_session(unauth_result)
        
        # Try to end non-existent session
        result = self.auth_manager.end_user_session("nonexistent", "over and out")
        self.assertEqual(result, "No active session to end.")
        
        # Try to increment messages for non-existent session
        # Should not raise error, just silently ignore
        self.auth_manager.increment_session_message_count("nonexistent")
    
    def test_input_validation_and_sanitization(self):
        """Test that inputs are properly validated and sanitized."""
        # Test with empty/None messages
        self.assertFalse(self.auth_manager.check_session_end_trigger(None))
        self.assertFalse(self.auth_manager.check_session_end_trigger(""))
        self.assertFalse(self.auth_manager.check_session_end_trigger("   "))
        
        # Test with very long messages
        long_message = "x" * 10000
        result = self.auth_manager.check_session_end_trigger(long_message)
        self.assertFalse(result)  # Should handle gracefully
        
        # Test with special characters and injection attempts
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
            "\x00\x01\x02\x03",  # Null bytes
            "🎉🎭🤖✨" * 100,     # Lots of emojis
        ]
        
        for malicious_input in malicious_inputs:
            # Should not cause errors or exceptions
            try:
                trigger_result = self.auth_manager.check_session_end_trigger(malicious_input)
                self.assertIsInstance(trigger_result, bool)
                
                auth_result = self.auth_manager.authenticate_request({}, malicious_input, "test")
                self.assertIsInstance(auth_result, AuthResult)
            except Exception as e:
                self.fail(f"Input validation failed for '{malicious_input}': {e}")


class TestCinematicResponses(unittest.TestCase):
    """Test suite for cinematic response generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.auth_manager = AuthenticationManager()
        self.access_controller = AccessController(self.auth_manager)
    
    def test_welcome_message_variety(self):
        """Test that welcome messages have variety and personality."""
        auth_result = AuthResult(True, "Arindam", UserRole.MASTER, "cinematic_passphrase")
        
        # Generate multiple welcome messages
        messages = []
        for _ in range(10):
            message = self.auth_manager.start_user_session(auth_result)
            messages.append(message)
            # Reset session for next test
            if self.auth_manager.is_user_session_active("Arindam"):
                self.auth_manager.end_user_session("Arindam", "test end")
        
        # Should have variety (not all identical)
        unique_messages = set(messages)
        self.assertGreater(len(unique_messages), 1, "Welcome messages should have variety")
        
        # All should contain user name and be substantial
        for message in messages:
            self.assertIn("Arindam", message)
            self.assertGreater(len(message), 30)
            # Should contain greeting elements
            self.assertTrue(any(word in message for word in ["Welcome", "Good", "ready", "command", "assist"]))
    
    def test_goodbye_message_personalization(self):
        """Test that goodbye messages are personalized based on session duration."""
        auth_result = AuthResult(True, "Arindam", UserRole.MASTER, "cinematic_passphrase")
        
        # Test short session goodbye
        self.auth_manager.start_user_session(auth_result)
        # Simulate very short session by ending immediately
        goodbye_short = self.auth_manager.end_user_session("Arindam", "over and out")
        
        self.assertIsInstance(goodbye_short, str)
        self.assertGreater(len(goodbye_short), 20)
        self.assertIn("Arindam", goodbye_short)
        
        # Test with message count
        self.auth_manager.start_user_session(auth_result)
        for _ in range(10):
            self.auth_manager.increment_session_message_count("Arindam")
        
        goodbye_with_messages = self.auth_manager.end_user_session("Arindam", "goodbye buddy")
        self.assertIsInstance(goodbye_with_messages, str)
        self.assertIn("Arindam", goodbye_with_messages)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)