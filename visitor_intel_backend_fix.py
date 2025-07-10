"""
Visitor Intel Backend Fix - Complete Solution
============================================

This module provides a robust state machine for managing AI conversations with:
- UTC timestamps exclusively
- Clear ACTIVE/WAITING states
- Synchronized state broadcasting via WebSockets
- Reliable scheduling with apscheduler
- 16-message conversations over ~16 minutes
- 5-minute waiting periods between conversations
"""

import logging
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from flask import current_app
from flask_socketio import emit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from models import Business, Conversation, ConversationMessage, db
from ai_conversation import AIConversationManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisitorIntelSystem:
    """
    Main system class that manages the entire conversation lifecycle
    """
    
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.ai_manager = AIConversationManager()
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # System state
        self.state = "WAITING"  # ACTIVE or WAITING
        self.current_conversation_id = None
        self.messages_generated = 0
        self.conversation_start_time = None
        self.next_conversation_time = None
        self.active_business = None
        
        # Configuration
        self.MESSAGES_PER_CONVERSATION = 16
        self.MESSAGE_INTERVAL_SECONDS = 60  # 1 minute between messages
        self.WAITING_PERIOD_MINUTES = 5
        
        # Initialize with Perfect Roofing Team as default business
        self._initialize_default_business()
        
        # Schedule first conversation
        self._schedule_next_conversation()
        
        logger.info("VisitorIntelSystem initialized")
    
    def _initialize_default_business(self):
        """Initialize with Perfect Roofing Team as the default business"""
        try:
            from app import app
            with app.app_context():
                business = Business.query.filter_by(name="Perfect Roofing Team").first()
                if business:
                    self.active_business = business
                    logger.info(f"Initialized with business: {business.name}")
                else:
                    logger.warning("Perfect Roofing Team not found in database")
        except Exception as e:
            logger.error(f"Error initializing default business: {e}")
    
    def start(self):
        """Start the system"""
        logger.info("VisitorIntelSystem started")
        self._broadcast_state()
    
    def stop(self):
        """Stop the system"""
        self.scheduler.shutdown()
        logger.info("VisitorIntelSystem stopped")
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current system state for API endpoints"""
        now_utc = datetime.now(timezone.utc)
        
        state_data = {
            "status": self.state,
            "system_running": True,
            "conversation_active": self.state == "ACTIVE",
            "conversation_status": self.state.lower(),
            "messages_generated": self.messages_generated,
            "total_messages": self.MESSAGES_PER_CONVERSATION,
            "current_conversation_id": self.current_conversation_id,
            "timestamp": now_utc.isoformat(),
        }
        
        # Add timing information
        if self.state == "ACTIVE" and self.conversation_start_time:
            elapsed = (now_utc - self.conversation_start_time).total_seconds()
            estimated_completion = self.conversation_start_time + timedelta(
                seconds=self.MESSAGES_PER_CONVERSATION * self.MESSAGE_INTERVAL_SECONDS
            )
            state_data.update({
                "conversation_started": self.conversation_start_time.isoformat(),
                "estimated_completion": estimated_completion.isoformat(),
                "elapsed_seconds": int(elapsed),
                "progress_percentage": min(100, int((elapsed / (self.MESSAGES_PER_CONVERSATION * self.MESSAGE_INTERVAL_SECONDS)) * 100))
            })
        
        if self.next_conversation_time:
            remaining = (self.next_conversation_time - now_utc).total_seconds()
            state_data.update({
                "next_conversation_time": self.next_conversation_time.isoformat(),
                "seconds_until_next": max(0, int(remaining))
            })
        
        return state_data
    
    def _broadcast_state(self):
        """Broadcast current state to all connected clients"""
        if self.socketio:
            try:
                state_data = self.get_current_state()
                self.socketio.emit('system_state_update', state_data)
                logger.debug(f"Broadcasted state: {self.state}")
            except Exception as e:
                logger.error(f"Error broadcasting state: {e}")
    
    def _schedule_next_conversation(self):
        """Schedule the next conversation to start"""
        if self.state == "ACTIVE":
            return  # Don't schedule if already active
        
        now_utc = datetime.now(timezone.utc)
        self.next_conversation_time = now_utc + timedelta(minutes=self.WAITING_PERIOD_MINUTES)
        
        # Cancel any existing jobs
        for job in self.scheduler.get_jobs():
            if job.id == 'start_conversation':
                job.remove()
        
        # Schedule new conversation
        self.scheduler.add_job(
            func=self._start_conversation,
            trigger=DateTrigger(run_date=self.next_conversation_time),
            id='start_conversation',
            replace_existing=True
        )
        
        logger.info(f"Next conversation scheduled for {self.next_conversation_time.isoformat()}")
        self._broadcast_state()
    
    def _start_conversation(self):
        """Start a new conversation"""
        try:
            if not self.active_business:
                logger.error("No active business found, cannot start conversation")
                self._schedule_next_conversation()
                return
            
            # Create new conversation
            from app import app
            with app.app_context():
                conversation = Conversation(
                    business_id=self.active_business.id,
                    topic=self._get_conversation_topic(),
                    status='active',
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(conversation)
                db.session.commit()
                
                self.current_conversation_id = conversation.id
                self.state = "ACTIVE"
                self.messages_generated = 0
                self.conversation_start_time = datetime.now(timezone.utc)
                
                logger.info(f"Started conversation {conversation.id} with topic: {conversation.topic}")
                self._broadcast_state()
                
                # Schedule first message immediately
                self._schedule_next_message()
                
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            self._schedule_next_conversation()
    
    def _get_conversation_topic(self) -> str:
        """Get a topic for the conversation"""
        topics = [
            "Professional Roofing Installation Services",
            "Emergency Roof Repair Solutions",
            "Preventive Roof Maintenance Programs",
            "Commercial Roofing Excellence",
            "Residential Roofing Expertise",
            "Storm Damage Restoration",
            "Energy-Efficient Roofing Systems",
            "Gutter Installation and Maintenance",
            "Roof Inspection Services",
            "Sustainable Roofing Solutions"
        ]
        import random
        return random.choice(topics)
    
    def _schedule_next_message(self):
        """Schedule the next message in the current conversation"""
        if self.state != "ACTIVE" or not self.current_conversation_id:
            return
        
        if self.messages_generated >= self.MESSAGES_PER_CONVERSATION:
            self._complete_conversation()
            return
        
        # Schedule next message
        next_message_time = datetime.now(timezone.utc) + timedelta(seconds=self.MESSAGE_INTERVAL_SECONDS)
        
        self.scheduler.add_job(
            func=self._generate_message,
            trigger=DateTrigger(run_date=next_message_time),
            id=f'message_{self.messages_generated + 1}',
            replace_existing=True
        )
        
        logger.debug(f"Scheduled message {self.messages_generated + 1} for {next_message_time.isoformat()}")
    
    def _generate_message(self):
        """Generate a single message for the active conversation"""
        try:
            if self.state != "ACTIVE" or not self.current_conversation_id:
                return
            
            from app import app
            with app.app_context():
                conversation = Conversation.query.get(self.current_conversation_id)
                if not conversation:
                    logger.error(f"Conversation {self.current_conversation_id} not found")
                    return
                
                # Generate message using AI
                message_content = self._generate_ai_message(conversation)
                
                # Determine agent for this message
                agent_info = self._get_agent_for_message(self.messages_generated + 1)
                
                # Create message
                message = ConversationMessage(
                    conversation_id=conversation.id,
                    agent_name=agent_info['name'],
                    agent_type=agent_info['type'],
                    content=message_content,
                    messageNumber=self.messages_generated + 1,
                    round=((self.messages_generated) // 4) + 1,
                    timestamp=datetime.now(timezone.utc)
                )
                
                db.session.add(message)
                db.session.commit()
                
                self.messages_generated += 1
                
                logger.info(f"Generated message {self.messages_generated} for conversation {conversation.id}")
                
                # Broadcast message to clients
                self._broadcast_new_message(message)
                self._broadcast_state()
                
                # Schedule next message
                self._schedule_next_message()
                
        except Exception as e:
            logger.error(f"Error generating message: {e}")
            self._schedule_next_message()  # Try to continue
    
    def _generate_ai_message(self, conversation) -> str:
        """Generate AI message content"""
        try:
            # Use existing AI conversation manager
            messages = self.ai_manager.generate_smart_conversation(self.active_business)
            if messages and len(messages) > self.messages_generated:
                return messages[self.messages_generated][2]  # content
            else:
                return f"Professional insight {self.messages_generated + 1} about {conversation.topic}"
        except Exception as e:
            logger.error(f"Error generating AI message: {e}")
            return f"Professional insight {self.messages_generated + 1} about {conversation.topic}"
    
    def _get_agent_for_message(self, message_number: int) -> Dict[str, str]:
        """Get agent info for a specific message number"""
        agents = [
            {"name": "Business AI Assistant", "type": "openai"},
            {"name": "SEO AI Specialist", "type": "anthropic"},
            {"name": "Customer Service AI", "type": "perplexity"},
            {"name": "Marketing AI Expert", "type": "gemini"}
        ]
        return agents[(message_number - 1) % 4]
    
    def _broadcast_new_message(self, message):
        """Broadcast new message to all connected clients"""
        if self.socketio:
            try:
                message_data = {
                    "id": message.id,
                    "agent_name": message.agent_name,
                    "agent_type": message.agent_type,
                    "content": message.content,
                    "messageNumber": message.messageNumber,
                    "round": message.round,
                    "timestamp": message.timestamp.isoformat(),
                    "conversation_id": message.conversation_id
                }
                self.socketio.emit('new_message', message_data)
                logger.debug(f"Broadcasted new message {message.id}")
            except Exception as e:
                logger.error(f"Error broadcasting new message: {e}")
    
    def _complete_conversation(self):
        """Complete the current conversation and schedule next one"""
        try:
            from app import app
            with app.app_context():
                if self.current_conversation_id:
                    conversation = Conversation.query.get(self.current_conversation_id)
                    if conversation:
                        conversation.status = 'completed'
                        conversation.completed_at = datetime.now(timezone.utc)
                        db.session.commit()
                        
                        logger.info(f"Completed conversation {conversation.id}")
                
                # Reset state
                self.state = "WAITING"
                self.current_conversation_id = None
                self.messages_generated = 0
                self.conversation_start_time = None
                
                # Clear scheduled message jobs
                for job in self.scheduler.get_jobs():
                    if job.id.startswith('message_'):
                        job.remove()
                
                self._broadcast_state()
                self._schedule_next_conversation()
                
        except Exception as e:
            logger.error(f"Error completing conversation: {e}")
            self._schedule_next_conversation()