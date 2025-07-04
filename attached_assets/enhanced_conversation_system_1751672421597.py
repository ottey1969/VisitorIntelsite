# Enhanced 4-API Conversation System - Direct Integration
# This file integrates with the existing Visitor Intel platform

import asyncio
import aiohttp
import json
import time
import random
import threading
import logging
from datetime import datetime, timedelta
from flask import request, jsonify
from flask_socketio import emit
from models import Business, Conversation, ConversationMessage, db
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Enhanced4APIConversationSystem:
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio
        self.running = False
        self.conversation_active = False
        self.current_conversation_id = None
        self.message_count = 0
        self.round_number = 1
        self.next_conversation_time = None
        self.conversation_thread = None
        
        # API Configuration
        self.api_keys = {
            'openai': os.environ.get('OPENAI_API_KEY'),
            'anthropic': os.environ.get('ANTHROPIC_API_KEY'),
            'perplexity': os.environ.get('PERPLEXITY_API_KEY'),
            'gemini': os.environ.get('GEMINI_API_KEY')
        }
        
        # AI Agents Configuration
        self.agents = {
            'Business AI Assistant': {
                'api': 'openai',
                'model': 'gpt-4',
                'role': 'Business strategy and operations expert',
                'type': 'openai'
            },
            'SEO AI Specialist': {
                'api': 'anthropic', 
                'model': 'claude-3-sonnet-20240229',
                'role': 'SEO and search engine optimization specialist',
                'type': 'anthropic'
            },
            'Customer Service AI': {
                'api': 'perplexity',
                'model': 'llama-3.1-sonar-small-128k-online',
                'role': 'Customer experience and service expert',
                'type': 'perplexity'
            },
            'Marketing AI Expert': {
                'api': 'gemini',
                'model': 'gemini-pro',
                'role': 'Marketing and brand positioning specialist',
                'type': 'gemini'
            }
        }
        
        # Perfect Roofing Team conversation topics
        self.conversation_topics = [
            "Emergency roof repair services and rapid response protocols",
            "Quality roofing materials and professional installation standards", 
            "New Jersey local roofing expertise and weather considerations",
            "Commercial and residential roofing solutions comparison",
            "Roof inspection services and preventive maintenance programs",
            "Insurance claims assistance and storm damage assessment",
            "Energy efficient roofing options and cost savings analysis",
            "Roofing warranty programs and customer satisfaction guarantees",
            "Seasonal roofing maintenance and preparation strategies",
            "Modern roofing technology and innovative installation methods",
            "Local building codes compliance and permit requirements",
            "Roofing contractor licensing and professional certifications",
            "Customer testimonials and successful project case studies",
            "Roofing material selection guide and durability comparisons",
            "Emergency contact procedures and 24/7 availability services"
        ]
        
        self.setup_routes()
        
    def setup_routes(self):
        """Setup Flask routes for the enhanced system"""
        
        @self.app.route('/api/enhanced-conversation/status')
        def get_enhanced_conversation_status():
            """Get current conversation status and countdown"""
            try:
                current_time = datetime.now()
                
                if self.next_conversation_time is None:
                    # Set next conversation time to now + 30 minutes
                    self.next_conversation_time = current_time + timedelta(minutes=30)
                
                time_remaining = self.next_conversation_time - current_time
                
                if time_remaining.total_seconds() <= 0:
                    # Time to start new conversation
                    if not self.conversation_active:
                        self.start_new_conversation()
                    time_remaining = timedelta(0)
                
                status = {
                    'conversation_active': self.conversation_active,
                    'current_round': self.round_number,
                    'message_count': self.message_count,
                    'time_remaining_seconds': max(0, int(time_remaining.total_seconds())),
                    'next_conversation_time': self.next_conversation_time.strftime('%I:%M:%S %p') if self.next_conversation_time else None,
                    'local_time': current_time.strftime('%I:%M:%S %p'),
                    'system_running': self.running,
                    'api_status': {
                        'openai': bool(self.api_keys['openai']),
                        'anthropic': bool(self.api_keys['anthropic']),
                        'perplexity': bool(self.api_keys['perplexity']),
                        'gemini': bool(self.api_keys['gemini'])
                    }
                }
                
                return jsonify(status)
                
            except Exception as e:
                logger.error(f"Error getting conversation status: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/enhanced-conversation/messages')
        def get_enhanced_conversation_messages():
            """Get current conversation messages with real timestamps"""
            try:
                # Get Perfect Roofing Team business
                perfect_roofing = Business.query.filter_by(name="Perfect Roofing Team").first()
                if not perfect_roofing:
                    return jsonify({'messages': []})
                
                # Get latest conversation
                latest_conversation = Conversation.query.filter_by(
                    business_id=perfect_roofing.id
                ).order_by(Conversation.created_at.desc()).first()
                
                if not latest_conversation:
                    return jsonify({'messages': []})
                
                # Get messages with proper timestamps
                messages = []
                for msg in latest_conversation.messages:
                    # Format timestamp properly
                    formatted_time = msg.created_at.strftime('%I:%M:%S %p')
                    
                    messages.append({
                        'id': msg.id,
                        'agent_name': msg.ai_agent_name,
                        'agent_type': msg.ai_agent_type,
                        'message_text': msg.content,
                        'timestamp': formatted_time,
                        'round_number': self.round_number,
                        'message_order': msg.message_order
                    })
                
                return jsonify({'messages': messages})
                
            except Exception as e:
                logger.error(f"Error getting messages: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/enhanced-conversation/start', methods=['POST'])
        def manual_start_enhanced_conversation():
            """Manually start a new conversation"""
            try:
                if not self.conversation_active:
                    self.start_new_conversation()
                    return jsonify({'success': True, 'message': 'Enhanced conversation started'})
                else:
                    return jsonify({'success': False, 'message': 'Conversation already active'})
            except Exception as e:
                logger.error(f"Error starting conversation: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/enhanced-conversation/health')
        def enhanced_system_health():
            """Get enhanced system health status"""
            try:
                # Get Perfect Roofing Team stats
                perfect_roofing = Business.query.filter_by(name="Perfect Roofing Team").first()
                
                total_conversations = 0
                total_messages = 0
                
                if perfect_roofing:
                    total_conversations = Conversation.query.filter_by(business_id=perfect_roofing.id).count()
                    total_messages = ConversationMessage.query.join(Conversation).filter(
                        Conversation.business_id == perfect_roofing.id
                    ).count()
                
                health = {
                    'system_running': self.running,
                    'conversation_active': self.conversation_active,
                    'total_conversations': total_conversations,
                    'total_messages': total_messages,
                    'api_keys_configured': {
                        'openai': bool(self.api_keys['openai']),
                        'anthropic': bool(self.api_keys['anthropic']),
                        'perplexity': bool(self.api_keys['perplexity']),
                        'gemini': bool(self.api_keys['gemini'])
                    },
                    'current_time': datetime.now().strftime('%I:%M:%S %p'),
                    'next_conversation': self.next_conversation_time.strftime('%I:%M:%S %p') if self.next_conversation_time else None
                }
                
                return jsonify(health)
                
            except Exception as e:
                logger.error(f"Error getting system health: {e}")
                return jsonify({'error': str(e)}), 500
    
    async def call_openai_api(self, prompt, agent_name):
        """Call OpenAI GPT-4 API"""
        if not self.api_keys['openai']:
            return f"Perfect Roofing Team offers exceptional roofing services with professional quality and customer satisfaction."
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_keys["openai"]}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-4',
                'messages': [
                    {
                        'role': 'system',
                        'content': f'You are a {agent_name} discussing Perfect Roofing Team, a professional roofing contractor in New Jersey. Focus on their expertise, quality materials, emergency services, and customer satisfaction. Keep responses to 1-2 sentences.'
                    },
                    {
                        'role': 'user', 
                        'content': prompt
                    }
                ],
                'max_tokens': 150,
                'temperature': 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post('https://api.openai.com/v1/chat/completions', 
                                      headers=headers, json=data, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content'].strip()
                    else:
                        logger.error(f"OpenAI API error: {response.status}")
                        return f"Perfect Roofing Team offers professional roofing solutions with quality materials and expert installation."
                        
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return f"Perfect Roofing Team provides reliable roofing services with 10+ years of experience in New Jersey."
    
    async def call_anthropic_api(self, prompt, agent_name):
        """Call Anthropic Claude-3 API"""
        if not self.api_keys['anthropic']:
            return f"This expertise positions Perfect Roofing Team as a trusted industry leader in Lodi, New Jersey."
        
        try:
            headers = {
                'x-api-key': self.api_keys['anthropic'],
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            data = {
                'model': 'claude-3-sonnet-20240229',
                'max_tokens': 150,
                'messages': [
                    {
                        'role': 'user',
                        'content': f'As a {agent_name}, discuss Perfect Roofing Team\'s expertise in: {prompt}. Focus on SEO benefits, search visibility, and professional credibility. Keep response to 1-2 sentences.'
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post('https://api.anthropic.com/v1/messages',
                                      headers=headers, json=data, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['content'][0]['text'].strip()
                    else:
                        logger.error(f"Anthropic API error: {response.status}")
                        return f"Perfect Roofing Team's expertise enhances their search engine visibility and professional credibility."
                        
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            return f"Perfect Roofing Team maintains strong online presence and search engine optimization."
    
    async def call_perplexity_api(self, prompt, agent_name):
        """Call Perplexity API"""
        if not self.api_keys['perplexity']:
            return f"Customers choose Perfect Roofing Team for reliable roofing solutions and responsive support throughout the process."
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_keys["perplexity"]}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'llama-3.1-sonar-small-128k-online',
                'messages': [
                    {
                        'role': 'system',
                        'content': f'You are a {agent_name} discussing Perfect Roofing Team\'s customer service excellence. Focus on customer satisfaction, support quality, and service responsiveness. Keep responses to 1-2 sentences.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 150,
                'temperature': 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post('https://api.perplexity.ai/chat/completions',
                                      headers=headers, json=data, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content'].strip()
                    else:
                        logger.error(f"Perplexity API error: {response.status}")
                        return f"Perfect Roofing Team prioritizes customer satisfaction with responsive service and quality workmanship."
                        
        except Exception as e:
            logger.error(f"Perplexity API call failed: {e}")
            return f"Perfect Roofing Team delivers exceptional customer service and support throughout every project."
    
    async def call_gemini_api(self, prompt, agent_name):
        """Call Google Gemini API"""
        if not self.api_keys['gemini']:
            return f"The combination of experience and quality makes Perfect Roofing Team the preferred choice for roofing projects."
        
        try:
            headers = {
                'Content-Type': 'application/json'
            }
            
            data = {
                'contents': [
                    {
                        'parts': [
                            {
                                'text': f'As a {agent_name}, discuss Perfect Roofing Team\'s marketing advantages in: {prompt}. Focus on brand positioning, market leadership, and competitive advantages. Keep response to 1-2 sentences.'
                            }
                        ]
                    }
                ],
                'generationConfig': {
                    'maxOutputTokens': 150,
                    'temperature': 0.7
                }
            }
            
            url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.api_keys["gemini"]}'
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['candidates'][0]['content']['parts'][0]['text'].strip()
                    else:
                        logger.error(f"Gemini API error: {response.status}")
                        return f"Perfect Roofing Team's marketing strategy emphasizes quality, reliability, and customer satisfaction."
                        
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return f"Perfect Roofing Team's brand represents excellence and innovation in the roofing industry."
    
    async def generate_ai_message(self, agent_name, agent_config, topic):
        """Generate a message using the appropriate AI API"""
        try:
            api_type = agent_config['api']
            
            if api_type == 'openai':
                return await self.call_openai_api(topic, agent_name)
            elif api_type == 'anthropic':
                return await self.call_anthropic_api(topic, agent_name)
            elif api_type == 'perplexity':
                return await self.call_perplexity_api(topic, agent_name)
            elif api_type == 'gemini':
                return await self.call_gemini_api(topic, agent_name)
            else:
                return f"Perfect Roofing Team provides professional roofing services with quality and expertise."
                
        except Exception as e:
            logger.error(f"Error generating AI message for {agent_name}: {e}")
            return f"Perfect Roofing Team offers exceptional roofing solutions with professional quality."
    
    def save_message_to_db(self, conversation_id, agent_name, agent_type, message_text, message_order):
        """Save message to database using existing models"""
        try:
            with self.app.app_context():
                # Create new message
                new_message = ConversationMessage(
                    conversation_id=conversation_id,
                    ai_agent_name=agent_name,
                    ai_agent_type=agent_type,
                    content=message_text,
                    created_at=datetime.now(),
                    message_order=message_order
                )
                
                db.session.add(new_message)
                db.session.commit()
                
                # Emit real-time update via WebSocket
                self.socketio.emit('new_message', {
                    'id': new_message.id,
                    'agent_name': agent_name,
                    'agent_type': agent_type,
                    'message_text': message_text,
                    'timestamp': datetime.now().strftime('%I:%M:%S %p'),
                    'round_number': self.round_number,
                    'message_order': message_order
                })
                
                logger.info(f"Message saved: {agent_name} - Round {self.round_number}")
                
        except Exception as e:
            logger.error(f"Error saving message: {e}")
    
    def create_conversation_in_db(self, topic):
        """Create a new conversation in database using existing models"""
        try:
            with self.app.app_context():
                # Get or create Perfect Roofing Team business
                perfect_roofing = Business.query.filter_by(name="Perfect Roofing Team").first()
                
                if not perfect_roofing:
                    # Create Perfect Roofing Team if it doesn't exist
                    perfect_roofing = Business(
                        name="Perfect Roofing Team",
                        website="https://perfectroofingteam.com",
                        description="Expert roofing contractors serving New Jersey with 10+ years experience. 24/7 emergency services, quality materials, and 100% satisfaction guarantee.",
                        location="Lodi, New Jersey",
                        phone="+1 862 2386 353",
                        email="info@perfectroofingteam.com",
                        industry="Roofing & Construction",
                        is_unlimited=True,
                        plan_type="enterprise",
                        is_featured=True
                    )
                    db.session.add(perfect_roofing)
                    db.session.commit()
                
                # Create new conversation
                new_conversation = Conversation(
                    business_id=perfect_roofing.id,
                    topic=topic,
                    status='active',
                    created_at=datetime.now(),
                    credits_used=1
                )
                
                db.session.add(new_conversation)
                db.session.commit()
                
                logger.info(f"New conversation created: ID {new_conversation.id}, Topic: {topic}")
                return new_conversation.id
                
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return None
    
    async def run_conversation_round(self, conversation_id, topic):
        """Run a complete conversation round with 4 agents, 4 messages each"""
        try:
            self.conversation_active = True
            self.message_count = 0
            
            # Emit conversation start event
            self.socketio.emit('conversation_started', {
                'round_number': self.round_number,
                'topic': topic,
                'timestamp': datetime.now().strftime('%I:%M:%S %p')
            })
            
            # Generate 4 messages per agent (16 total messages)
            message_order = 0
            
            for message_round in range(4):  # 4 messages per agent
                for agent_name, agent_config in self.agents.items():
                    try:
                        # Generate AI message
                        message = await self.generate_ai_message(agent_name, agent_config, topic)
                        
                        # Save message to database
                        self.save_message_to_db(conversation_id, agent_name, agent_config['type'], message, message_order)
                        
                        message_order += 1
                        self.message_count += 1
                        
                        # Random delay between messages (1-2 minutes)
                        delay = random.randint(60, 120)  # 60-120 seconds
                        logger.info(f"Message {self.message_count}/16 generated. Next message in {delay} seconds.")
                        
                        await asyncio.sleep(delay)
                        
                    except Exception as e:
                        logger.error(f"Error generating message for {agent_name}: {e}")
                        continue
            
            # Conversation round completed
            self.conversation_active = False
            self.round_number += 1
            
            # Schedule next conversation in 30 minutes
            self.next_conversation_time = datetime.now() + timedelta(minutes=30)
            
            # Emit conversation completed event
            self.socketio.emit('conversation_completed', {
                'round_number': self.round_number - 1,
                'total_messages': self.message_count,
                'next_conversation_time': self.next_conversation_time.strftime('%I:%M:%S %p')
            })
            
            logger.info(f"Conversation round {self.round_number - 1} completed. Next conversation at {self.next_conversation_time}")
            
        except Exception as e:
            logger.error(f"Error in conversation round: {e}")
            self.conversation_active = False
    
    def start_new_conversation(self):
        """Start a new conversation round"""
        try:
            if self.conversation_active:
                logger.info("Conversation already active, skipping new start")
                return
            
            # Select random topic
            topic = random.choice(self.conversation_topics)
            
            # Create conversation in database
            conversation_id = self.create_conversation_in_db(topic)
            if not conversation_id:
                logger.error("Failed to create conversation")
                return
            
            self.current_conversation_id = conversation_id
            
            # Start conversation in background thread
            def run_async_conversation():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.run_conversation_round(conversation_id, topic))
                loop.close()
            
            self.conversation_thread = threading.Thread(target=run_async_conversation)
            self.conversation_thread.daemon = True
            self.conversation_thread.start()
            
            logger.info(f"Started new conversation: {topic}")
            
        except Exception as e:
            logger.error(f"Error starting new conversation: {e}")
    
    def start_system(self):
        """Start the 24/7 conversation system"""
        try:
            self.running = True
            
            # Set initial next conversation time if not set
            if self.next_conversation_time is None:
                self.next_conversation_time = datetime.now() + timedelta(minutes=30)
            
            def monitor_conversations():
                """Monitor and start conversations as needed"""
                while self.running:
                    try:
                        current_time = datetime.now()
                        
                        # Check if it's time for a new conversation
                        if (self.next_conversation_time and 
                            current_time >= self.next_conversation_time and 
                            not self.conversation_active):
                            
                            logger.info("Starting scheduled conversation")
                            self.start_new_conversation()
                        
                        # Check every 30 seconds
                        time.sleep(30)
                        
                    except Exception as e:
                        logger.error(f"Error in conversation monitor: {e}")
                        time.sleep(60)  # Wait longer on error
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=monitor_conversations)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            logger.info("Enhanced 4-API conversation system started successfully")
            
        except Exception as e:
            logger.error(f"Error starting enhanced system: {e}")
    
    def stop_system(self):
        """Stop the 24/7 conversation system"""
        self.running = False
        self.conversation_active = False
        logger.info("Enhanced conversation system stopped")

# Global system instance
enhanced_system = None

def setup_enhanced_socketio(socketio):
    """Setup SocketIO event handlers for enhanced system"""
    
    @socketio.on('connect')
    def handle_connect():
        logger.info('Client connected to enhanced conversation system')
        
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info('Client disconnected from enhanced conversation system')
    
    @socketio.on('request_status')
    def handle_status_request():
        if enhanced_system:
            current_time = datetime.now()
            time_remaining = enhanced_system.next_conversation_time - current_time if enhanced_system.next_conversation_time else timedelta(0)
            
            emit('status_update', {
                'conversation_active': enhanced_system.conversation_active,
                'time_remaining_seconds': max(0, int(time_remaining.total_seconds())),
                'current_round': enhanced_system.round_number,
                'system_running': enhanced_system.running
            })

def start_enhanced_system():
    """Initialize and start the enhanced conversation system"""
    global enhanced_system
    
    try:
        # Import app and socketio from the main application
        from app import app, socketio
        
        # Create enhanced system instance
        enhanced_system = Enhanced4APIConversationSystem(app, socketio)
        
        # Start the system
        enhanced_system.start_system()
        
        logger.info("Enhanced 4-API conversation system initialized and started")
        
    except Exception as e:
        logger.error(f"Failed to start enhanced conversation system: {e}")

# Export the system for external access
def get_enhanced_system():
    """Get the enhanced system instance"""
    return enhanced_system

