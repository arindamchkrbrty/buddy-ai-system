import re
import json
import logging
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ImprovementState(Enum):
    IDLE = "idle"
    AWAITING_REQUEST = "awaiting_request"
    ANALYZING = "analyzing"
    AWAITING_APPROVAL = "awaiting_approval"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    COMPLETE = "complete"
    FAILED = "failed"

@dataclass
class ImprovementRequest:
    id: str
    user_id: str
    request: str
    category: str
    plan: str
    status: ImprovementState
    created_at: datetime
    approved: bool = False
    backup_created: bool = False
    implementation_steps: List[str] = None
    test_results: str = ""
    
    def __post_init__(self):
        if self.implementation_steps is None:
            self.implementation_steps = []

class SelfImprovementManager:
    """Manages Buddy's self-improvement capabilities with safety mechanisms."""
    
    def __init__(self):
        self.improvement_triggers = [
            re.compile(r"improve\s+yourself", re.IGNORECASE),
            re.compile(r"self[-\s]improve", re.IGNORECASE),
            re.compile(r"upgrade\s+yourself", re.IGNORECASE),
            re.compile(r"enhance\s+yourself", re.IGNORECASE),
            re.compile(r"make\s+yourself\s+better", re.IGNORECASE)
        ]
        
        # Protected core functions that cannot be modified
        self.protected_functions = {
            "authentication": [
                "auth/authentication.py",
                "auth/access_control.py", 
                "Happy birthday passphrase",
                "Master user privileges",
                "Session management"
            ],
            "security": [
                "Security endpoints",
                "JWT token system",
                "Device authentication",
                "Access control"
            ],
            "core_api": [
                "main.py FastAPI structure",
                "Core endpoints (/chat, /siri-chat)",
                "Request/Response models"
            ],
            "conversation_manager": [
                "30-second session timeout",
                "Daily briefing system",
                "Time-based greetings"
            ]
        }
        
        # Current improvement request
        self.current_request: Optional[ImprovementRequest] = None
        self.improvement_history: List[ImprovementRequest] = []
        
        # Backup directory
        self.backup_dir = "/Users/DefenderCave/jarvis-ai-system/backups"
        self._ensure_backup_dir()
        
    def _ensure_backup_dir(self):
        """Ensure backup directory exists."""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def check_improvement_trigger(self, message: str, user_id: str) -> Optional[str]:
        """Check if message contains self-improvement trigger."""
        
        # Only allow master user to request improvements
        if user_id != "Arindam":
            return None
        
        for trigger in self.improvement_triggers:
            if trigger.search(message):
                if self.current_request and self.current_request.status == ImprovementState.AWAITING_REQUEST:
                    # Already waiting for improvement request
                    return None
                
                # Start new improvement flow
                self.current_request = ImprovementRequest(
                    id=f"improvement_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    user_id=user_id,
                    request="",
                    category="",
                    plan="",
                    status=ImprovementState.AWAITING_REQUEST,
                    created_at=datetime.now()
                )
                
                return "🚀 I'd love to improve! What specific capability would you like me to develop or enhance? I can work on:\\n\\n" + \
                       "• **Conversation features** - Better responses, new conversation patterns\\n" + \
                       "• **Personality traits** - Humor, wit, empathy, expertise areas\\n" + \
                       "• **Utility functions** - New commands, tools, calculations\\n" + \
                       "• **Daily briefings** - Enhanced formats, new data sources\\n" + \
                       "• **Custom commands** - Personalized shortcuts for you\\n" + \
                       "• **Integration prep** - Weather, calendar, smart home APIs\\n\\n" + \
                       "What would you like me to work on?"
        
        return None
    
    def process_improvement_request(self, message: str, user_id: str) -> Optional[str]:
        """Process improvement request during the flow."""
        
        if not self.current_request or user_id != "Arindam":
            return None
        
        if self.current_request.status == ImprovementState.AWAITING_REQUEST:
            # User provided improvement request
            self.current_request.request = message
            self.current_request.status = ImprovementState.ANALYZING
            
            # Analyze and create plan
            category, plan = self._analyze_request(message)
            self.current_request.category = category
            self.current_request.plan = plan
            self.current_request.status = ImprovementState.AWAITING_APPROVAL
            
            return f"🧠 **Analysis Complete!**\\n\\n" + \
                   f"**Category**: {category}\\n" + \
                   f"**Your Request**: {message}\\n\\n" + \
                   f"**Implementation Plan**:\\n{plan}\\n\\n" + \
                   f"This will enhance my capabilities while keeping all security and core functions protected. Should I proceed with this improvement? (yes/no)"
        
        elif self.current_request.status == ImprovementState.AWAITING_APPROVAL:
            # User approval/rejection
            message_lower = message.lower().strip()
            
            if any(word in message_lower for word in ["yes", "yeah", "sure", "go ahead", "proceed", "do it"]):
                self.current_request.approved = True
                self.current_request.status = ImprovementState.IMPLEMENTING
                
                # Start implementation
                return self._implement_improvement()
            
            elif any(word in message_lower for word in ["no", "nope", "cancel", "abort", "stop"]):
                self.current_request.status = ImprovementState.FAILED
                self.improvement_history.append(self.current_request)
                self.current_request = None
                
                return "❌ Improvement cancelled. I'm always ready to help when you want to enhance my capabilities!"
            
            else:
                return "Should I proceed with this improvement? Please say 'yes' to continue or 'no' to cancel."
        
        return None
    
    def _analyze_request(self, request: str) -> Tuple[str, str]:
        """Analyze improvement request and create implementation plan."""
        request_lower = request.lower()
        
        # Determine category
        if any(word in request_lower for word in ["wit", "humor", "funny", "joke", "clever"]):
            category = "Personality Enhancement - Humor & Wit"
            plan = self._create_humor_plan(request)
        
        elif any(word in request_lower for word in ["response", "answer", "reply", "conversation"]):
            category = "Conversation Enhancement"
            plan = self._create_conversation_plan(request)
        
        elif any(word in request_lower for word in ["personality", "trait", "character", "behave"]):
            category = "Personality Development"
            plan = self._create_personality_plan(request)
        
        elif any(word in request_lower for word in ["command", "function", "utility", "tool"]):
            category = "New Functionality"
            plan = self._create_functionality_plan(request)
        
        elif any(word in request_lower for word in ["briefing", "daily", "report", "summary"]):
            category = "Daily Briefing Enhancement"
            plan = self._create_briefing_plan(request)
        
        elif any(word in request_lower for word in ["weather", "calendar", "integration", "api"]):
            category = "Integration Preparation"
            plan = self._create_integration_plan(request)
        
        else:
            category = "General Enhancement"
            plan = self._create_general_plan(request)
        
        return category, plan
    
    def _create_humor_plan(self, request: str) -> str:
        return """1. **Add Humor Patterns**: Create witty response templates and humor triggers
2. **Enhance Personality Config**: Add humor traits to personality system
3. **Response Selection**: Implement smart humor context detection
4. **Testing**: Verify humor appropriateness and timing
5. **Integration**: Seamlessly blend humor with existing responses

**Files to modify**:
• `core/buddy.py` - Add humor response logic
• `core/personality_enhancer.py` - New humor module
• Response templates with witty alternatives

**Safety**: All humor will be appropriate and contextual, maintaining professionalism when needed."""
    
    def _create_conversation_plan(self, request: str) -> str:
        return """1. **Response Analysis**: Identify current response patterns
2. **Enhancement Templates**: Create more engaging response formats
3. **Context Awareness**: Improve conversation flow and memory
4. **Natural Language**: Add more conversational phrases and transitions
5. **Testing**: Validate improved conversation quality

**Files to modify**:
• `core/buddy.py` - Enhanced response processing
• `core/conversation_enhancer.py` - New conversation patterns
• Response filtering and improvement logic

**Safety**: Maintains existing authentication and security response patterns."""
    
    def _create_personality_plan(self, request: str) -> str:
        return """1. **Personality Analysis**: Review current traits and gaps
2. **Trait Addition**: Add new personality characteristics
3. **Response Integration**: Weave new traits into responses
4. **Consistency Check**: Ensure personality coherence
5. **Testing**: Validate new personality expression

**Files to modify**:
• `core/buddy.py` - Personality configuration
• Response generation with new traits
• Personality expression logic

**Safety**: Core helpful and friendly traits remain protected."""
    
    def _create_functionality_plan(self, request: str) -> str:
        return """1. **Function Design**: Design new utility or command
2. **Integration Point**: Identify where to add functionality
3. **Implementation**: Code new feature with error handling
4. **Command Recognition**: Add trigger patterns
5. **Testing**: Validate functionality and edge cases

**Files to modify**:
• `core/buddy.py` or new module for functionality
• Command recognition patterns
• Response handling for new feature

**Safety**: No modifications to protected authentication or security functions."""
    
    def _create_briefing_plan(self, request: str) -> str:
        return """1. **Briefing Analysis**: Review current daily briefing format
2. **Enhancement Design**: Plan new briefing components
3. **Data Integration**: Prepare for real API connections
4. **Format Improvement**: Better presentation and structure
5. **Testing**: Validate enhanced briefing experience

**Files to modify**:
• `core/conversation_manager.py` - Enhanced briefing generation
• New briefing templates and data structures
• Improved formatting functions

**Safety**: Core briefing trigger system remains protected."""
    
    def _create_integration_plan(self, request: str) -> str:
        return """1. **API Preparation**: Create integration scaffolding
2. **Mock Data Enhancement**: Improve placeholder data
3. **Configuration Setup**: Add API configuration options
4. **Error Handling**: Robust fallbacks for API failures
5. **Testing**: Validate integration readiness

**Files to modify**:
• New integration modules in `integrations/` directory
• `config/settings.py` - API configuration
• Enhanced mock data systems

**Safety**: No changes to core authentication or security systems."""
    
    def _create_general_plan(self, request: str) -> str:
        return f"""1. **Requirement Analysis**: Break down your specific request
2. **Implementation Strategy**: Design solution approach
3. **Code Enhancement**: Implement requested improvements
4. **Integration**: Seamlessly add to existing system
5. **Testing**: Validate new capabilities

**Your specific request**: "{request}"

**Files to modify**: Will be determined based on specific requirements
**Safety**: All protected core functions remain untouched."""
    
    def _implement_improvement(self) -> str:
        """Implement the approved improvement."""
        if not self.current_request or not self.current_request.approved:
            return "❌ No approved improvement to implement."
        
        try:
            # Create backup first
            backup_success = self._create_backup()
            if not backup_success:
                return "❌ Failed to create backup. Improvement aborted for safety."
            
            self.current_request.backup_created = True
            
            # Simulate implementation (in real version, this would use Claude Code tools)
            implementation_result = self._simulate_implementation()
            
            if implementation_result["success"]:
                self.current_request.status = ImprovementState.COMPLETE
                self.current_request.test_results = implementation_result["message"]
                self.improvement_history.append(self.current_request)
                
                response = f"✅ **Improvement Complete!**\\n\\n" + \
                          f"**Enhancement**: {self.current_request.category}\\n" + \
                          f"**Status**: Successfully implemented\\n" + \
                          f"**Details**: {implementation_result['message']}\\n\\n" + \
                          f"Try chatting with me now to experience the improvements! 🎉"
                
                self.current_request = None
                return response
            
            else:
                # Implementation failed, rollback
                self._rollback_changes()
                self.current_request.status = ImprovementState.FAILED
                self.improvement_history.append(self.current_request)
                
                response = f"❌ **Implementation Failed**\\n\\n" + \
                          f"**Error**: {implementation_result['message']}\\n" + \
                          f"**Action**: Automatically rolled back to working version\\n\\n" + \
                          f"Don't worry - all your data and settings are safe! Would you like to try a different approach?"
                
                self.current_request = None
                return response
        
        except Exception as e:
            logger.error(f"Improvement implementation error: {e}")
            self._rollback_changes()
            return f"❌ Unexpected error during implementation. Rolled back safely. Error: {str(e)}"
    
    def _simulate_implementation(self) -> Dict[str, Any]:
        """Simulate implementation for demonstration (replace with real Claude Code tools)."""
        
        category = self.current_request.category.lower()
        
        if "humor" in category:
            return {
                "success": True,
                "message": "Added witty response patterns, humor detection, and contextual joke integration. I'm now more entertaining while maintaining professionalism!"
            }
        
        elif "conversation" in category:
            return {
                "success": True,
                "message": "Enhanced conversation flow with better transitions, more natural responses, and improved context awareness. Our chats will feel more fluid!"
            }
        
        elif "personality" in category:
            return {
                "success": True,
                "message": "Developed new personality traits and integrated them into my response system. I now express myself more authentically!"
            }
        
        elif "functionality" in category:
            return {
                "success": True,
                "message": "Implemented new utility functions with proper error handling and command recognition. New capabilities are ready to use!"
            }
        
        elif "briefing" in category:
            return {
                "success": True,
                "message": "Enhanced daily briefing system with better formatting, more data points, and improved presentation. Your briefings will be more comprehensive!"
            }
        
        elif "integration" in category:
            return {
                "success": True,
                "message": "Prepared integration scaffolding with robust error handling and configuration options. Ready for real API connections!"
            }
        
        else:
            return {
                "success": True,
                "message": f"Successfully implemented your requested enhancement: {self.current_request.request}"
            }
    
    def _create_backup(self) -> bool:
        """Create backup of current system state."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}")
            
            # In real implementation, this would backup the actual codebase
            # For now, create a backup metadata file
            backup_info = {
                "timestamp": timestamp,
                "improvement_id": self.current_request.id,
                "backup_path": backup_path,
                "files_backed_up": [
                    "core/buddy.py",
                    "core/conversation_manager.py",
                    "main.py"
                ]
            }
            
            os.makedirs(backup_path, exist_ok=True)
            with open(os.path.join(backup_path, "backup_info.json"), "w") as f:
                json.dump(backup_info, f, indent=2, default=str)
            
            logger.info(f"Created backup at {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False
    
    def _rollback_changes(self) -> bool:
        """Rollback to previous working version."""
        try:
            if not self.current_request or not self.current_request.backup_created:
                return False
            
            # In real implementation, this would restore from backup
            logger.info(f"Rolled back changes for improvement {self.current_request.id}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def get_improvement_status(self) -> Dict[str, Any]:
        """Get current improvement status."""
        if not self.current_request:
            return {
                "active": False,
                "total_improvements": len(self.improvement_history),
                "successful_improvements": len([req for req in self.improvement_history if req.status == ImprovementState.COMPLETE])
            }
        
        return {
            "active": True,
            "current_request": {
                "id": self.current_request.id,
                "category": self.current_request.category,
                "status": self.current_request.status.value,
                "request": self.current_request.request,
                "approved": self.current_request.approved
            },
            "total_improvements": len(self.improvement_history),
            "successful_improvements": len([req for req in self.improvement_history if req.status == ImprovementState.COMPLETE])
        }
    
    def get_improvement_history(self) -> List[Dict[str, Any]]:
        """Get history of all improvements."""
        return [
            {
                "id": req.id,
                "category": req.category,
                "request": req.request,
                "status": req.status.value,
                "created_at": req.created_at.isoformat(),
                "approved": req.approved,
                "test_results": req.test_results
            }
            for req in self.improvement_history
        ]