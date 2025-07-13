"""
Real-time Progressive Conversation Generator
Generates messages one by one with 1-minute intervals
"""

import threading
import time
import logging
from datetime import datetime, timedelta, timezone
from app import app, db
from models import Business, Conversation, ConversationMessage
from ai_conversation import AIConversationManager

class RealtimeConversationManager:
    """Manages real-time progressive conversation generation"""
    
    def __init__(self):
        self.ai_manager = AIConversationManager()
        self.active_conversations = {}  # Track ongoing conversations
        self.running = True
        self.thread = None
        
    def start(self):
        """Start the background conversation manager"""
        if self.thread is None or not self.thread.is_alive():
            self.running = True
            
            # Restore any active conversations from database first
            self._restore_active_conversations()
            
            self.thread = threading.Thread(target=self._run_background_manager, daemon=True)
            self.thread.start()
            logging.info("Real-time conversation manager started")
    
    def stop(self):
        """Stop the background conversation manager"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        logging.info("Real-time conversation manager stopped")
    
    def _restore_active_conversations(self):
        """Restore active conversations from database on startup"""
        try:
            with app.app_context():
                # Find conversations that are still active
                active_conversations = Conversation.query.filter_by(status='active').all()
                
                for conversation in active_conversations:
                    # Count existing messages
                    message_count = ConversationMessage.query.filter_by(
                        conversation_id=conversation.id
                    ).count()
                    
                    # Only restore if less than 16 messages (incomplete)
                    if message_count < 16:
                        # Restore conversation to tracking
                        self.active_conversations[conversation.id] = {
                            'conversation_id': conversation.id,
                            'business_id': conversation.business_id,
                            'topic': conversation.topic,
                            'messages': [],  # Will be generated progressively
                            'current_message': message_count,
                            'next_message_time': datetime.now(timezone.utc),  # Generate next message immediately
                            'total_messages': 16,
                            'agents': [
                                {'name': 'Business AI Assistant', 'type': 'openai'},
                                {'name': 'SEO AI Specialist', 'type': 'anthropic'},
                                {'name': 'Customer Service AI', 'type': 'perplexity'},
                                {'name': 'Marketing AI Expert', 'type': 'gemini'}
                            ] * 4  # 4 rounds of 4 agents each
                        }
                        
                        logging.info(f"Restored active conversation {conversation.id}: {conversation.topic} ({message_count}/16 messages)")
                    else:
                        # Mark as completed if all messages are present
                        conversation.status = 'completed'
                        db.session.commit()
                        logging.info(f"Marked conversation {conversation.id} as completed")
                        
                logging.info(f"Restored {len(self.active_conversations)} active conversations")
                
        except Exception as e:
            logging.error(f"Failed to restore active conversations: {e}")
    
    def start_progressive_conversation(self, business, topic):
        """Start a new progressive conversation that generates messages over time"""
        try:
            with app.app_context():
                # Create conversation record
                conversation = Conversation(
                    business_id=business.id,
                    topic=topic,
                    status='active'
                )
                db.session.add(conversation)
                db.session.flush()
                
                # Create conversation entry for progressive generation (no messages yet)
                self.active_conversations[conversation.id] = {
                    'conversation_id': conversation.id,
                    'business_id': business.id,
                    'topic': topic,
                    'messages': [],  # Will be generated progressively
                    'current_message': 0,
                    'next_message_time': datetime.now(timezone.utc),
                    'total_messages': 16,  # Standard 16-message conversation
                    'agents': [
                        {'name': 'Business AI Assistant', 'type': 'openai'},
                        {'name': 'SEO AI Specialist', 'type': 'anthropic'},
                        {'name': 'Customer Service AI', 'type': 'perplexity'},
                        {'name': 'Marketing AI Expert', 'type': 'gemini'}
                    ] * 4  # 4 rounds of 4 agents each
                }
                
                db.session.commit()
                
                logging.info(f"Started progressive conversation {conversation.id}: {topic}")
                return conversation.id
                
        except Exception as e:
            logging.error(f"Failed to start progressive conversation: {e}")
            return None
    
    def _run_background_manager(self):
        """Background thread that processes progressive conversations"""
        logging.info("Real-time conversation background manager started")
        while self.running:
            try:
                with app.app_context():
                    current_time = datetime.now()
                    
                    logging.info(f"Background manager checking {len(self.active_conversations)} active conversations")
                    
                    # Process each active conversation
                    conversations_to_remove = []
                    
                    for conv_id, conv_data in self.active_conversations.items():
                        logging.info(f"Checking conversation {conv_id}: message {conv_data['current_message']}/{conv_data['total_messages']}, next time: {conv_data['next_message_time']}")
                        
                        if self._should_generate_next_message(conv_data, current_time):
                            logging.info(f"Generating next message for conversation {conv_id}")
                            success = self._generate_next_message(conv_data)
                            
                            if not success or conv_data['current_message'] >= conv_data['total_messages']:
                                conversations_to_remove.append(conv_id)
                    
                    # Remove completed conversations
                    for conv_id in conversations_to_remove:
                        self._complete_conversation(conv_id)
                        del self.active_conversations[conv_id]
                        logging.info(f"Completed and removed conversation {conv_id}")
                
                # Sleep for 30 seconds before next check
                time.sleep(30)
                
            except Exception as e:
                logging.error(f"Background conversation manager error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _should_generate_next_message(self, conv_data, current_time):
        """Check if it's time to generate the next message"""
        return (conv_data['current_message'] < conv_data['total_messages'] and 
                current_time >= conv_data['next_message_time'])
    
    def _generate_next_message(self, conv_data):
        """Generate and save the next message in the conversation"""
        try:
            message_index = conv_data['current_message']
            
            if message_index >= conv_data['total_messages']:
                return False
            
            # Get the agent for this message
            agent = conv_data['agents'][message_index]
            agent_name = agent['name']
            agent_type = agent['type']
            
            # Get business context
            business = Business.query.get(conv_data['business_id'])
            if not business:
                logging.error(f"Business {conv_data['business_id']} not found")
                return False
            
            # Build conversation history for context
            existing_messages = ConversationMessage.query.filter_by(
                conversation_id=conv_data['conversation_id']
            ).order_by(ConversationMessage.message_order).all()
            
            conversation_history = ""
            for msg in existing_messages:
                conversation_history += f"{msg.ai_agent_name}: {msg.content}\n"
            
            # Generate message content using AI
            round_num = (message_index // 4) + 1
            msg_in_round = (message_index % 4) + 1
            
            content = self.ai_manager._generate_agent_message(
                agent_name=agent_name,
                agent_type=agent_type,
                business_context=f"{business.name} in {business.location}, Industry: {business.industry}",
                topic=conv_data['topic'],
                conversation_history=conversation_history,
                round_num=round_num,
                msg_num=msg_in_round
            )
            
            if not content:
                logging.error(f"Failed to generate content for message {message_index + 1}")
                return False
            
            # Calculate the intended timestamp (start + message number * 1 minute)
            intended_timestamp = conv_data['conversation_start_time'] + timedelta(minutes=message_index)
            
            # Create and save the message with intended timestamp
            message = ConversationMessage(
                conversation_id=conv_data['conversation_id'],
                ai_agent_name=agent_name,
                ai_agent_type=agent_type,
                content=content,
                message_order=message_index + 1
            )
            
            # Set the timestamp to the intended time (not current server time)
            message.created_at = intended_timestamp
            
            db.session.add(message)
            db.session.commit()
            
            # Update conversation data
            conv_data['current_message'] += 1
            conv_data['next_message_time'] = intended_timestamp + timedelta(minutes=1)
            
            logging.info(f"Generated message {message_index + 1}/{conv_data['total_messages']} for conversation {conv_data['conversation_id']}: {agent_name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to generate next message: {e}")
            return False
    
    def _complete_conversation(self, conversation_id):
        """Mark conversation as completed"""
        try:
            conversation = Conversation.query.get(conversation_id)
            if conversation:
                conversation.status = 'completed'
                conversation.credits_used = 1
                
                # Deduct credits if not unlimited
                business = Business.query.get(conversation.business_id)
                if business and not business.is_unlimited:
                    business.credits_remaining = max(0, business.credits_remaining - 1)
                
                db.session.commit()
                logging.info(f"Completed conversation {conversation_id}")
                
        except Exception as e:
            logging.error(f"Failed to complete conversation {conversation_id}: {e}")
    
    def get_active_conversation_count(self):
        """Get number of active conversations"""
        return len(self.active_conversations)
    
    def get_conversation_status(self, conversation_id):
        """Get status of a specific conversation"""
        if conversation_id in self.active_conversations:
            conv_data = self.active_conversations[conversation_id]
            return {
                'active': True,
                'current_message': conv_data['current_message'],
                'total_messages': conv_data['total_messages'],
                'next_message_time': conv_data['next_message_time'].isoformat()
            }
        return {'active': False}

# Global instance
realtime_manager = RealtimeConversationManager()