import logging
import torch
from typing import Dict, Any, List
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from .ai_provider import AIProvider

logger = logging.getLogger(__name__)

class HuggingFaceProvider(AIProvider):
    """Hugging Face Transformers AI provider using DialoGPT for conversational AI."""
    
    def __init__(self):
        self.name = "Hugging Face DialoGPT Provider"
        self.version = "1.0.0"
        self.model_name = "microsoft/DialoGPT-medium"
        self.initialized = False
        
        self.tokenizer = None
        self.model = None
        self.chat_pipeline = None
        self.conversation_history = {}
        
        # Model configuration
        self.max_length = 1000
        self.max_new_tokens = 100
        self.temperature = 0.7
        self.do_sample = True
        self.pad_token_id = None
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the Hugging Face model and tokenizer."""
        try:
            logger.info(f"Initializing {self.name} with model: {self.model_name}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Set pad token if not available
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.pad_token_id = self.tokenizer.pad_token_id
            
            # Load model
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading model on device: {device}")
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto" if device == "cuda" else None
            )
            
            if device == "cpu":
                self.model = self.model.to(device)
            
            # Create text generation pipeline
            self.chat_pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if device == "cuda" else -1,
                return_full_text=False,
                do_sample=self.do_sample,
                temperature=self.temperature,
                pad_token_id=self.pad_token_id
            )
            
            self.initialized = True
            logger.info("HuggingFace provider initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize HuggingFace provider: {e}")
            self.initialized = False
            return False
    
    async def generate_response(self, message: str, context: Dict[str, Any]) -> str:
        """Generate a response using DialoGPT."""
        if not self.initialized:
            logger.error("HuggingFace provider not initialized")
            return "I'm sorry, but I'm having trouble processing your request right now."
        
        try:
            user_id = context.get("user_id", "default")
            
            # Build conversation context
            conversation_context = self._build_conversation_context(user_id, message, context)
            
            # Generate response
            logger.debug(f"Generating response for: {message[:50]}...")
            
            response = self.chat_pipeline(
                conversation_context,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
                do_sample=self.do_sample,
                pad_token_id=self.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
            
            # Extract the generated text
            if response and len(response) > 0:
                generated_text = response[0]["generated_text"].strip()
                
                # Clean up the response
                cleaned_response = self._clean_response(generated_text, message)
                
                # Update conversation history
                self._update_conversation_history(user_id, message, cleaned_response)
                
                return cleaned_response
            else:
                return "I'm having trouble generating a response. Could you try rephrasing your question?"
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I encountered an error while processing your request. Please try again."
    
    def _build_conversation_context(self, user_id: str, message: str, context: Dict[str, Any]) -> str:
        """Build conversation context for DialoGPT."""
        
        # Get recent conversation history
        history = context.get("conversation_history", [])
        
        # Build context string
        context_parts = []
        
        # Add recent history (last 3-4 exchanges to keep context manageable)
        recent_history = history[-6:] if len(history) > 6 else history
        
        for interaction in recent_history:
            if interaction.get("message"):
                context_parts.append(f"Human: {interaction['message']}")
            if interaction.get("response"):
                context_parts.append(f"Assistant: {interaction['response']}")
        
        # Add current message
        context_parts.append(f"Human: {message}")
        context_parts.append("Assistant:")
        
        conversation_context = "\n".join(context_parts)
        
        # Ensure we don't exceed token limits
        if len(conversation_context) > 800:  # Conservative limit
            # Keep only the current message if context is too long
            conversation_context = f"Human: {message}\nAssistant:"
        
        return conversation_context
    
    def _clean_response(self, generated_text: str, original_message: str) -> str:
        """Clean up the generated response."""
        
        # Remove any repetition of the input
        if original_message.lower() in generated_text.lower():
            # Try to extract just the response part
            parts = generated_text.split("Assistant:")
            if len(parts) > 1:
                generated_text = parts[-1].strip()
        
        # Remove common artifacts
        generated_text = generated_text.replace("Human:", "").strip()
        generated_text = generated_text.replace("Assistant:", "").strip()
        
        # Remove excessive repetition
        words = generated_text.split()
        if len(words) > 3:
            # Check for repetitive patterns
            unique_words = []
            for word in words:
                if len(unique_words) < 2 or word not in unique_words[-2:]:
                    unique_words.append(word)
                else:
                    break  # Stop at repetition
            generated_text = " ".join(unique_words)
        
        # Ensure reasonable length
        if len(generated_text) > 200:
            sentences = generated_text.split(".")
            if len(sentences) > 1:
                generated_text = ". ".join(sentences[:2]) + "."
        
        # Fallback for empty or very short responses
        if len(generated_text.strip()) < 5:
            return "I understand. Could you tell me more about what you're thinking?"
        
        return generated_text.strip()
    
    def _update_conversation_history(self, user_id: str, message: str, response: str):
        """Update conversation history for context."""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({
            "message": message,
            "response": response
        })
        
        # Keep only last 10 exchanges per user
        if len(self.conversation_history[user_id]) > 10:
            self.conversation_history[user_id] = self.conversation_history[user_id][-10:]
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about this provider."""
        return {
            "name": self.name,
            "version": self.version,
            "model": self.model_name,
            "type": "huggingface_transformers",
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "capabilities": [
                "Conversational AI",
                "Context awareness",
                "Multi-turn dialogue",
                "Personality-based responses"
            ],
            "limitations": [
                "Limited by model size",
                "Context length restrictions",
                "No real-time learning"
            ],
            "initialized": self.initialized
        }
    
    async def health_check(self) -> bool:
        """Check if the provider is healthy."""
        if not self.initialized:
            return False
        
        try:
            # Simple test generation
            test_response = self.chat_pipeline(
                "Hello",
                max_new_tokens=10,
                do_sample=False
            )
            return test_response is not None and len(test_response) > 0
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False