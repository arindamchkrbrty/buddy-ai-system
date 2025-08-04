#!/usr/bin/env python3
"""
Test script to verify the voice response bug fix.
This script tests the voice_processor to ensure clean text output.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.voice_processor import VoiceProcessor

def test_voice_processor():
    """Test voice processor with various problematic inputs."""
    
    processor = VoiceProcessor()
    
    # Test cases that might cause \1 issues
    test_cases = [
        # Markdown formatting
        "**Welcome back, Arindam**. Good afternoon! How may I assist you today?",
        "*This is italic text* and **this is bold**.",
        
        # Technical terms
        "Your API authentication was successful. The JSON response is ready.",
        
        # Lists and formatting
        "• First item\n• Second item\n• Third item",
        "1. First step\n2. Second step\n3. Third step",
        
        # Mixed problematic content
        "🎉 **Welcome back, Arindam**. Your *authentication* was successful! How may I assist you today?",
        
        # Code blocks
        "Here's the code: `print('hello')` and more text.",
        
        # Headers
        "# Welcome\nThis is content under the header.",
        
        # Empty/problematic responses
        "",
        "\\1\\1\\1",  # Direct problematic characters
        "\\n\\t\\r",  # Escape sequences
        
        # Real Buddy responses that might be problematic
        "🎉 Welcome back, Arindam. All systems are now at your command. Good afternoon! How may I assist you today?",
    ]
    
    print("🧪 Testing Voice Processor Fix...")
    print("=" * 60)
    
    all_passed = True
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {repr(test_input[:50])}...")
        
        try:
            result = processor.optimize_for_voice(test_input)
            
            # Check for problematic characters
            has_backslash_digits = "\\1" in result or "\\2" in result or "\\3" in result
            has_other_escapes = "\\" in result and any(c in result for c in "nrt")
            has_emojis = any(ord(c) > 127 and not c.isalpha() for c in result)
            
            print(f"   Input:  {repr(test_input)}")
            print(f"   Output: {repr(result)}")
            
            if has_backslash_digits:
                print("   ❌ FAIL: Contains \\1, \\2, or \\3 characters")
                all_passed = False
            elif has_other_escapes:
                print("   ❌ FAIL: Contains escape sequences")
                all_passed = False
            elif has_emojis:
                print("   ❌ FAIL: Contains emojis or special characters")
                all_passed = False
            elif len(result.strip()) == 0:
                print("   ❌ FAIL: Empty result")
                all_passed = False
            else:
                print("   ✅ PASS: Clean text output")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Voice processor is working correctly.")
        print("✅ No \\1 characters or problematic output detected.")
    else:
        print("❌ SOME TESTS FAILED! Voice processor needs more fixes.")
    
    return all_passed

def test_specific_cases():
    """Test specific problematic cases from Siri integration."""
    
    processor = VoiceProcessor()
    
    print("\n🎯 Testing Specific Siri Integration Cases...")
    print("=" * 60)
    
    # Simulate actual Buddy responses
    buddy_responses = [
        "🎉 Welcome back, Arindam. Good afternoon! How may I assist you today? [Session: Active - 30s remaining]",
        "Good afternoon, Arindam! Would you like me to give you your **daily briefing**? I can share weather, upcoming meetings, and traffic updates.",
        "🚀 I'd love to improve! What specific capability would you like me to develop or enhance?\\n\\n• **Conversation features**\\n• **Personality traits**",
        "✅ **Improvement Complete!**\\n\\nStatus: Successfully implemented\\nTry chatting with me now! 🎉"
    ]
    
    for i, response in enumerate(buddy_responses, 1):
        print(f"\n🤖 Buddy Response {i}:")
        print(f"   Raw: {repr(response)}")
        
        cleaned = processor.optimize_for_voice(response)
        print(f"   Clean: {repr(cleaned)}")
        
        # This should be suitable for Siri TTS
        print(f"   For Siri: \"{cleaned}\"")
        
        # Check if it looks like valid speech
        if cleaned and len(cleaned.strip()) > 0 and "\\" not in cleaned:
            print("   ✅ Ready for Siri TTS")
        else:
            print("   ❌ Not suitable for TTS")

if __name__ == "__main__":
    print("🔧 Voice Response Bug Fix Test")
    print("Testing for \\1 character issues and clean text output")
    print()
    
    # Run main tests
    success = test_voice_processor()
    
    # Run specific cases
    test_specific_cases()
    
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: Voice processor testing complete!")