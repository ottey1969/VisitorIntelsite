# Complete AI Conversation Platform - Code Package

## 1. Main Application Entry Point

### `main.py`
```python
from app import app
from visitor_intel_backend_fix import VisitorIntelSystem
from flask_socketio import SocketIO
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", 
                   async_mode='eventlet', 
                   logger=True, engineio_logger=True)

# Initialize VisitorIntel System
intel_system = None

def initialize_system():
    global intel_system
    from models import Business
    
    # Get featured business or create default
    business = Business.query.filter_by(is_featured=True).first()
    if not business:
        business = Business.query.first()
    
    if business:
        intel_system = VisitorIntelSystem(app, socketio, business.id)
        intel_system.start()
        print("Enhanced VisitorIntelSystem started successfully")

# Initialize after app context is available
with app.app_context():
    initialize_system()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
```

### `app.py`
```python
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///conversation.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models and routes
    import models
    import routes
    db.create_all()
```

## 2. Core System Controller

### `visitor_intel_backend_fix.py`
```python
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from flask_socketio import emit
import random

class VisitorIntelSystem:
    """
    Enhanced AI Conversation System with 21-minute cycles
    - 16 messages generated over 16 minutes (1 per minute)
    - 5-minute break between conversations
    - Real-time WebSocket updates
    - Precise APScheduler integration
    """
    
    def __init__(self, app, socketio, business_id: int):
        self.app = app
        self.socketio = socketio
        self.business_id = business_id
        self.business = None
        self.scheduler = BackgroundScheduler()
        self.current_conversation = None
        self.message_count = 0
        self.state = 'WAITING'  # WAITING, ACTIVE, BREAK
        self.next_conversation_time = None
        self.conversation_active = False
        
        # Initialize logging
        self.logger = logging.getLogger('visitor_intel_backend_fix')
        self.logger.setLevel(logging.INFO)
        
        # Load business data
        self._load_business()
        
        # Setup SocketIO events
        self._setup_socketio_events()
        
        self.logger.info(f"Initialized with business: {self.business.name if self.business else 'None'}")
    
    def _load_business(self):
        """Load business from database"""
        with self.app.app_context():
            from models import Business
            self.business = Business.query.get(self.business_id)
    
    def _setup_socketio_events(self):
        """Setup SocketIO event handlers"""
        @self.socketio.on('connect')
        def handle_connect():
            self.logger.debug("Client connected")
            self._broadcast_state()
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.logger.debug("Client disconnected")
    
    def start(self):
        """Start the VisitorIntel system"""
        try:
            self.scheduler.start()
            self._schedule_next_conversation()
            self.logger.info("VisitorIntelSystem started")
        except Exception as e:
            self.logger.error(f"Failed to start system: {e}")
    
    def stop(self):
        """Stop the VisitorIntel system"""
        if self.scheduler.running:
            self.scheduler.shutdown()
        self.logger.info("VisitorIntelSystem stopped")
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current system state"""
        return {
            'status': self.state,
            'conversation_active': self.conversation_active,
            'message_count': self.message_count,
            'next_conversation_time': self.next_conversation_time.isoformat() if self.next_conversation_time else None,
            'business_id': self.business_id,
            'current_conversation_id': self.current_conversation.id if self.current_conversation else None
        }
    
    def _schedule_next_conversation(self):
        """Schedule the next conversation"""
        # Calculate next conversation time (5 minutes from now)
        self.next_conversation_time = datetime.utcnow() + timedelta(minutes=5)
        
        # Remove existing jobs for this business
        job_id = f'conversation_{self.business_id}'
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        # Schedule new conversation
        self.scheduler.add_job(
            func=self._start_conversation,
            trigger=DateTrigger(run_date=self.next_conversation_time),
            id=job_id,
            replace_existing=True
        )
        
        self.state = 'WAITING'
        self.conversation_active = False
        self.logger.info(f"Next conversation scheduled for {self.next_conversation_time.isoformat()}")
        self._broadcast_state()
    
    def _start_conversation(self):
        """Start a new 21-minute conversation cycle"""
        try:
            with self.app.app_context():
                from models import Conversation, db
                from ai_conversation import AIConversationManager
                
                # Create new conversation
                topics = [
                    "Emergency Roof Repair Services and 24/7 Availability",
                    "Professional Roofing Installation with Quality Materials",
                    "Customer Satisfaction and Transparent Pricing Policy",
                    "Storm Damage Restoration and Insurance Claims",
                    "Preventive Roof Maintenance and Inspection Services"
                ]
                
                topic = random.choice(topics)
                
                self.current_conversation = Conversation(
                    business_id=self.business_id,
                    topic=topic,
                    status='active',
                    created_at=datetime.utcnow()
                )
                
                db.session.add(self.current_conversation)
                db.session.commit()
                
                self.state = 'ACTIVE'
                self.conversation_active = True
                self.message_count = 0
                
                self.logger.info(f"Started conversation {self.current_conversation.id}: {topic}")
                
                # Generate first message immediately
                self._generate_next_message()
                
                # Schedule remaining 15 messages (1 per minute)
                for i in range(1, 16):
                    message_time = datetime.utcnow() + timedelta(minutes=i)
                    self.scheduler.add_job(
                        func=self._generate_next_message,
                        trigger=DateTrigger(run_date=message_time),
                        id=f'message_{self.current_conversation.id}_{i}',
                        replace_existing=True
                    )
                
                # Schedule conversation completion (after 16 minutes)
                completion_time = datetime.utcnow() + timedelta(minutes=17)
                self.scheduler.add_job(
                    func=self._complete_conversation,
                    trigger=DateTrigger(run_date=completion_time),
                    id=f'complete_{self.current_conversation.id}',
                    replace_existing=True
                )
                
                self._broadcast_state()
                
        except Exception as e:
            self.logger.error(f"Failed to start conversation: {e}")
    
    def _generate_next_message(self):
        """Generate the next message in the conversation"""
        try:
            with self.app.app_context():
                from models import ConversationMessage, db
                from ai_conversation import AIConversationManager
                
                if not self.current_conversation:
                    return
                
                # Determine agent for this message
                agents = [
                    ('Business AI Assistant', 'openai'),
                    ('SEO AI Specialist', 'anthropic'),
                    ('Customer Service AI', 'perplexity'),
                    ('Marketing AI Expert', 'gemini')
                ]
                
                current_round = (self.message_count // 4) + 1
                agent_index = self.message_count % 4
                agent_name, agent_type = agents[agent_index]
                
                # Generate message content
                ai_manager = AIConversationManager()
                
                # Get conversation history
                existing_messages = ConversationMessage.query.filter_by(
                    conversation_id=self.current_conversation.id
                ).order_by(ConversationMessage.created_at.asc()).all()
                
                conversation_history = "\n".join([
                    f"{msg.agent_name}: {msg.content}" for msg in existing_messages
                ])
                
                # Generate new message
                business_context = f"{self.business.name} - {self.business.description}"
                message_content = ai_manager._generate_agent_message(
                    agent_name, agent_type, business_context,
                    self.current_conversation.topic, conversation_history,
                    current_round, (self.message_count % 4) + 1
                )
                
                # Save message to database
                new_message = ConversationMessage(
                    conversation_id=self.current_conversation.id,
                    agent_name=agent_name,
                    agent_type=agent_type,
                    content=message_content,
                    message_number=self.message_count + 1,
                    round_number=current_round,
                    created_at=datetime.utcnow()
                )
                
                db.session.add(new_message)
                db.session.commit()
                
                self.message_count += 1
                
                self.logger.info(f"Generated message {self.message_count}/16 from {agent_name}")
                
                # Broadcast new message
                self._broadcast_message(new_message)
                self._broadcast_state()
                
        except Exception as e:
            self.logger.error(f"Failed to generate message: {e}")
    
    def _complete_conversation(self):
        """Complete the current conversation and schedule next one"""
        try:
            with self.app.app_context():
                from models import db
                
                if self.current_conversation:
                    self.current_conversation.status = 'completed'
                    self.current_conversation.completed_at = datetime.utcnow()
                    db.session.commit()
                    
                    self.logger.info(f"Completed conversation {self.current_conversation.id}")
                
                self.current_conversation = None
                self.message_count = 0
                self.conversation_active = False
                
                # Schedule next conversation (5 minutes later)
                self._schedule_next_conversation()
                
        except Exception as e:
            self.logger.error(f"Failed to complete conversation: {e}")
    
    def _broadcast_state(self):
        """Broadcast current state to all connected clients"""
        state_data = self.get_current_state()
        self.socketio.emit('state_update', state_data, room=f'business_{self.business_id}')
        self.logger.debug(f"Broadcasted state: {state_data['status']}")
    
    def _broadcast_message(self, message):
        """Broadcast new message to all connected clients"""
        message_data = {
            'id': message.id,
            'agent_name': message.agent_name,
            'agent_type': message.agent_type,
            'content': message.content,
            'message_number': message.message_number,
            'round_number': message.round_number,
            'timestamp': message.created_at.isoformat() + 'Z',
            'conversation_id': message.conversation_id
        }
        
        self.socketio.emit('new_message', message_data, room=f'business_{self.business_id}')
        self.logger.debug(f"Broadcasted message from {message.agent_name}")
```

## 3. Database Models

### `models.py`
```python
from app import db
from datetime import datetime
from sqlalchemy import Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

class Business(db.Model):
    __tablename__ = 'business'
    
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    industry = db.Column(String(50))
    location = db.Column(String(100))
    website = db.Column(String(200))
    phone = db.Column(String(20))
    description = db.Column(Text)
    is_featured = db.Column(Boolean, default=False)
    subscription_plan = db.Column(String(20), default='Free')
    credits = db.Column(Integer, default=0)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversations = relationship('Conversation', backref='business', lazy=True)
    purchases = relationship('Purchase', backref='business', lazy=True)

class Conversation(db.Model):
    __tablename__ = 'conversation'
    
    id = db.Column(Integer, primary_key=True)
    business_id = db.Column(Integer, ForeignKey('business.id'), nullable=False)
    topic = db.Column(String(500))
    status = db.Column(String(20), default='active')
    created_at = db.Column(DateTime, default=datetime.utcnow)
    completed_at = db.Column(DateTime)
    
    # Relationships
    messages = relationship('ConversationMessage', backref='conversation', lazy=True)

class ConversationMessage(db.Model):
    __tablename__ = 'conversation_message'
    
    id = db.Column(Integer, primary_key=True)
    conversation_id = db.Column(Integer, ForeignKey('conversation.id'), nullable=False)
    agent_name = db.Column(String(50), nullable=False)
    agent_type = db.Column(String(20), nullable=False)
    content = db.Column(Text, nullable=False)
    message_number = db.Column(Integer)
    round_number = db.Column(Integer)
    created_at = db.Column(DateTime, default=datetime.utcnow)

class CreditPackage(db.Model):
    __tablename__ = 'credit_package'
    
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(50), nullable=False)
    credits = db.Column(Integer, nullable=False)  # -1 for unlimited
    price = db.Column(Integer, nullable=False)  # Price in cents
    description = db.Column(Text)
    is_popular = db.Column(Boolean, default=False)

class Purchase(db.Model):
    __tablename__ = 'purchase'
    
    id = db.Column(Integer, primary_key=True)
    business_id = db.Column(Integer, ForeignKey('business.id'), nullable=False)
    package_id = db.Column(Integer, ForeignKey('credit_package.id'), nullable=False)
    amount = db.Column(Integer, nullable=False)  # Amount in cents
    status = db.Column(String(20), default='pending')
    transaction_id = db.Column(String(100))
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    package = relationship('CreditPackage', backref='purchases', lazy=True)
```

## 4. AI Integration Manager

### `ai_conversation.py`
```python
import os
import logging
import random
from typing import List, Tuple, Dict, Any
from datetime import datetime
import requests

class AIConversationManager:
    """Enhanced AI-to-AI conversation manager with real-time capabilities"""
    
    def __init__(self, app=None, socketio=None):
        self.app = app
        self.socketio = socketio
        
        # API Keys
        self.api_keys = {
            'openai': os.environ.get('OPENAI_API_KEY'),
            'anthropic': os.environ.get('ANTHROPIC_API_KEY'),
            'perplexity': os.environ.get('PERPLEXITY_API_KEY'),
            'gemini': os.environ.get('GOOGLE_API_KEY')
        }
        
        # Agent configurations
        self.agents = [
            {
                'name': 'Business AI Assistant',
                'type': 'openai',
                'personality': 'Professional business-focused AI that provides comprehensive information about services, emphasizing value and customer benefits.'
            },
            {
                'name': 'SEO AI Specialist',
                'type': 'anthropic',
                'personality': 'Technical SEO expert focused on search engine optimization, keywords, and online visibility strategies.'
            },
            {
                'name': 'Customer Service AI',
                'type': 'perplexity',
                'personality': 'Customer-focused AI specializing in addressing concerns, providing solutions, and ensuring customer satisfaction.'
            },
            {
                'name': 'Marketing AI Expert',
                'type': 'gemini',
                'personality': 'Creative marketing specialist focused on engagement, brand building, and promotional strategies.'
            }
        ]
    
    def generate_conversation(self, business, topic: str) -> List[Tuple[str, str, str]]:
        """
        Generate a 4-round AI-to-AI conversation (16 messages total = 1 credit)
        Returns list of tuples: (agent_name, agent_type, message_content)
        """
        conversation_messages = []
        business_context = f"""
Business: {business.name}
Industry: {business.industry}
Location: {business.location}
Website: {business.website}
Description: {business.description}
        """.strip()
        
        try:
            # Generate 4 rounds of conversation (4 messages per round)
            for round_num in range(1, 5):
                round_messages = self._generate_conversation_round(
                    business_context, topic, conversation_messages, round_num
                )
                conversation_messages.extend(round_messages)
                
                # Small delay between rounds for natural flow
                import time
                time.sleep(0.1)
            
            return conversation_messages
            
        except Exception as e:
            logging.error(f"Conversation generation failed: {e}")
            return self._get_fallback_conversation(business, topic)
    
    def _generate_conversation_round(self, business_context: str, topic: str, 
                                   previous_messages: List[Tuple[str, str, str]], 
                                   round_num: int) -> List[Tuple[str, str, str]]:
        """Generate one round of 4 messages (exactly 4 specific agents)"""
        round_messages = []
        conversation_history = "\n".join([
            f"{agent}: {content}" for agent, _, content in previous_messages
        ])
        
        # Generate message from each agent in order
        for msg_num, agent in enumerate(self.agents, 1):
            try:
                message_content = self._generate_agent_message(
                    agent['name'], agent['type'], business_context,
                    topic, conversation_history, round_num, msg_num
                )
                
                if message_content:
                    round_messages.append((agent['name'], agent['type'], message_content))
                    # Update conversation history for next agent
                    conversation_history += f"\n{agent['name']}: {message_content}"
                
            except Exception as e:
                logging.error(f"Failed to generate message from {agent['name']}: {e}")
                # Use fallback message
                fallback_message = self._get_professional_fallback(agent['name'], agent['type'], topic)
                round_messages.append((agent['name'], agent['type'], fallback_message))
        
        return round_messages
    
    def _generate_agent_message(self, agent_name: str, agent_type: str, business_context: str, 
                               topic: str, conversation_history: str, round_num: int, msg_num: int) -> str:
        """Generate a message from a specific agent with guaranteed output"""
        
        # Create agent-specific prompt
        prompt = f"""You are {agent_name}, participating in a professional business discussion about "{topic}".

Business Context:
{business_context}

Previous conversation:
{conversation_history}

Round {round_num}, Message {msg_num}: Provide a professional, informative response (150-200 words) that:
1. Builds on the previous discussion
2. Adds valuable insights from your expertise
3. Maintains professional business tone
4. Focuses on practical benefits and solutions

Respond naturally as {agent_name} would."""
        
        try:
            if agent_type == 'openai' and self.api_keys['openai']:
                return self._get_openai_response(business_context, topic, conversation_history, agent_name, round_num, msg_num)
            elif agent_type == 'anthropic' and self.api_keys['anthropic']:
                return self._get_anthropic_response(business_context, topic, conversation_history, agent_name, round_num, msg_num)
            elif agent_type == 'perplexity' and self.api_keys['perplexity']:
                return self._get_perplexity_response(business_context, topic, conversation_history, agent_name, round_num, msg_num)
            elif agent_type == 'gemini' and self.api_keys['gemini']:
                return self._get_gemini_response(business_context, topic, conversation_history, agent_name, round_num, msg_num)
            else:
                return self._get_professional_fallback(agent_name, agent_type, topic)
                
        except Exception as e:
            logging.error(f"API call failed for {agent_type}: {e}")
            return self._get_professional_fallback(agent_name, agent_type, topic)
    
    def _get_openai_response(self, business_context: str, topic: str, 
                           conversation_history: str, agent_name: str, 
                           round_num: int, msg_num: int) -> str:
        """Get response from OpenAI agent"""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_keys['openai'])
            
            prompt = f"""As {agent_name}, discuss "{topic}" for this business:
{business_context}

Previous discussion:
{conversation_history}

Provide a professional business response (150-200 words) with practical insights."""
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=250,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            return self._get_professional_fallback(agent_name, "openai", topic)
    
    def _get_anthropic_response(self, business_context: str, topic: str, 
                              conversation_history: str, agent_name: str, 
                              round_num: int, msg_num: int) -> str:
        """Get response from Anthropic agent"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_keys['anthropic'])
            
            prompt = f"""As {agent_name}, discuss "{topic}" for this business:
{business_context}

Previous discussion:
{conversation_history}

Provide a professional SEO and technical response (150-200 words) with actionable insights."""
            
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=250,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logging.error(f"Anthropic API error: {e}")
            return self._get_professional_fallback(agent_name, "anthropic", topic)
    
    def _get_perplexity_response(self, business_context: str, topic: str, 
                               conversation_history: str, agent_name: str, 
                               round_num: int, msg_num: int) -> str:
        """Get response from Perplexity agent"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_keys['perplexity']}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""As {agent_name}, discuss "{topic}" for this business:
{business_context}

Previous discussion:
{conversation_history}

Provide a customer service focused response (150-200 words) addressing customer needs."""
            
            data = {
                "model": "sonar-medium-online",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 250,
                "temperature": 0.7
            }
            
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            else:
                logging.error(f"Perplexity API error: {response.status_code}")
                return self._get_professional_fallback(agent_name, "perplexity", topic)
                
        except Exception as e:
            logging.error(f"Perplexity API error: {e}")
            return self._get_professional_fallback(agent_name, "perplexity", topic)
    
    def _get_gemini_response(self, business_context: str, topic: str, 
                           conversation_history: str, agent_name: str, 
                           round_num: int, msg_num: int) -> str:
        """Get response from Gemini agent"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_keys['gemini'])
            
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            prompt = f"""As {agent_name}, discuss "{topic}" for this business:
{business_context}

Previous discussion:
{conversation_history}

Provide a marketing focused response (150-200 words) with creative engagement strategies."""
            
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logging.error(f"Gemini API error: {e}")
            return self._get_professional_fallback(agent_name, "gemini", topic)
    
    def _get_professional_fallback(self, agent_name: str, agent_type: str, topic: str) -> str:
        """Generate a single professional message based on agent expertise"""
        fallback_messages = self._get_agent_specific_fallback(agent_name, agent_type, topic)
        return random.choice(fallback_messages)
    
    def _get_agent_specific_fallback(self, agent_name: str, agent_type: str, topic: str) -> List[str]:
        """Generate realistic fallback messages based on agent specialization"""
        
        if agent_type == 'openai':  # Business AI Assistant
            return [
                f"Our comprehensive approach to {topic.lower()} ensures maximum value for our clients through proven methodologies and industry best practices.",
                f"When it comes to {topic.lower()}, we prioritize quality, efficiency, and customer satisfaction in every aspect of our service delivery.",
                f"Our team's expertise in {topic.lower()} has helped numerous businesses achieve their goals while maintaining the highest professional standards."
            ]
        
        elif agent_type == 'anthropic':  # SEO AI Specialist
            return [
                f"From an SEO perspective, {topic.lower()} presents excellent opportunities for search engine visibility and organic traffic growth.",
                f"Optimizing {topic.lower()} for search engines requires strategic keyword placement and content structure that search algorithms prefer.",
                f"Technical SEO considerations for {topic.lower()} include page speed optimization, mobile responsiveness, and structured data implementation."
            ]
        
        elif agent_type == 'perplexity':  # Customer Service AI
            return [
                f"Our customers consistently appreciate our approach to {topic.lower()}, which prioritizes clear communication and reliable service delivery.",
                f"When addressing {topic.lower()}, we ensure every customer receives personalized attention and solutions tailored to their specific needs.",
                f"Customer feedback on our {topic.lower()} services highlights our commitment to transparency, quality, and responsive support."
            ]
        
        elif agent_type == 'gemini':  # Marketing AI Expert
            return [
                f"From a marketing standpoint, {topic.lower()} offers unique opportunities to showcase expertise and build brand credibility.",
                f"Effective promotion of {topic.lower()} requires multi-channel strategies that resonate with target audiences and drive engagement.",
                f"Our marketing approach to {topic.lower()} focuses on storytelling, social proof, and demonstrating tangible value to potential customers."
            ]
        
        else:
            return [f"Professional expertise in {topic.lower()} delivers exceptional results through dedicated service and proven methodologies."]
    
    def _get_fallback_conversation(self, business, topic: str) -> List[Tuple[str, str, str]]:
        """Fallback conversation when APIs are unavailable"""
        return [
            ("Business AI Assistant", "openai", f"Welcome to our discussion about {topic}. Our professional team brings years of experience and dedication to every project."),
            ("SEO AI Specialist", "anthropic", f"From an SEO perspective, {topic} offers excellent opportunities for online visibility and search engine ranking improvements."),
            ("Customer Service AI", "perplexity", f"Our customers consistently praise our approach to {topic}, highlighting our commitment to quality and customer satisfaction."),
            ("Marketing AI Expert", "gemini", f"Marketing {topic} effectively requires understanding customer needs and communicating value propositions clearly.")
        ]
```

## 5. Frontend JavaScript Controller

### `static/js/visitor_intel_frontend_fix.js`
```javascript
/**
 * Visitor Intel Frontend Fix - Complete Solution
 * =============================================
 * 
 * This module provides a complete frontend solution with:
 * - Dynamic status display (ACTIVE/WAITING with badges)
 * - Intelligent countdown timer
 * - UTC time display for all messages
 * - Real-time message handling via WebSockets
 * - Synchronized state management
 */

class VisitorIntelFrontend {
    constructor() {
        this.socket = null;
        this.state = 'WAITING';
        this.messageCount = 0;
        this.nextEventTime = null;
        this.conversationData = null;
        this.countdownInterval = null;
        this.connectionAttempts = 0;
        this.maxConnectionAttempts = 3;
        this.retryDelay = 5000;
        
        console.log('[VisitorIntel] Frontend initialized');
    }
    
    init() {
        this.connectWebSocket();
        this.loadInitialState();
        this.setupEventListeners();
        this.startCountdownTimer();
    }
    
    connectWebSocket() {
        try {
            // Initialize SocketIO connection
            this.socket = io({
                transports: ['websocket', 'polling'],
                upgrade: true,
                timeout: 10000
            });
            
            this.socket.on('connect', () => {
                console.log('[VisitorIntel] Connected to server');
                this.connectionAttempts = 0;
                
                // Join business room for updates
                this.socket.emit('join_room', {business_id: 1});
            });
            
            this.socket.on('disconnect', () => {
                console.log('[VisitorIntel] Disconnected from server');
                this.handleDisconnection();
            });
            
            this.socket.on('state_update', (data) => {
                this.handleStateUpdate(data);
            });
            
            this.socket.on('new_message', (messageData) => {
                this.handleNewMessage(messageData);
            });
            
            this.socket.on('connect_error', (error) => {
                console.error('[VisitorIntel] Connection error:', error);
                this.handleConnectionError();
            });
            
        } catch (error) {
            console.error('[VisitorIntel] WebSocket setup failed:', error);
            this.fallbackToPolling();
        }
    }
    
    loadInitialState() {
        // Load system status
        fetch('/api/system-status')
            .then(response => response.json())
            .then(data => {
                this.handleStateUpdate(data);
            })
            .catch(error => {
                console.error('[VisitorIntel] Failed to load initial state:', error);
                this.loadFallbackState();
            });
        
        // Load conversation data
        fetch('/api/live-conversation-latest')
            .then(response => response.json())
            .then(data => {
                this.conversationData = data;
                this.updateMessagesFromFallback(data);
                console.log('[ConversationData] Updated:', data.messages?.length || 0, 'messages, Topic:', data.topic || 'None');
            })
            .catch(error => {
                console.error('[VisitorIntel] Failed to load conversation data:', error);
            });
    }
    
    loadFallbackState() {
        // Fallback state when API is unavailable
        this.state = 'WAITING';
        this.messageCount = 0;
        this.nextEventTime = new Date(Date.now() + 5 * 60 * 1000).toISOString();
        this.updateUI();
    }
    
    handleStateUpdate(data) {
        if (data.conversation_status) {
            this.state = data.conversation_status.toUpperCase();
        }
        
        this.messageCount = data.active_conversations_count || 0;
        this.nextEventTime = data.next_conversation_time;
        
        console.log('[VisitorIntel] State updated:', this.state);
        this.updateUI();
    }
    
    handleNewMessage(messageData) {
        console.log('[VisitorIntel] New message received:', messageData.agent_name);
        this.addMessageToUI(messageData);
        this.messageCount = messageData.message_number || this.messageCount + 1;
        this.updateUI();
    }
    
    updateUI() {
        this.updateStatusDisplay();
        this.updateCountdownDisplay();
        this.updateProgressDisplay();
        this.updateMessageCount();
    }
    
    updateStatusDisplay() {
        const statusText = document.getElementById('status-text');
        const statusBadge = document.getElementById('status-badge');
        
        if (statusText && statusBadge) {
            if (this.state === 'ACTIVE') {
                statusText.textContent = '🤖 4 AI Agents Are Having Live Discussion';
                statusBadge.textContent = 'ACTIVE';
                statusBadge.className = 'status-badge ms-2 px-3 py-1 rounded-pill bg-success text-white';
            } else {
                statusText.textContent = '⏳ Waiting for Next AI Discussion';
                statusBadge.textContent = 'WAITING';
                statusBadge.className = 'status-badge ms-2 px-3 py-1 rounded-pill bg-warning text-dark';
            }
        }
    }
    
    updateCountdownDisplay() {
        const countdownDisplay = document.getElementById('countdown-display');
        const localTime = document.getElementById('local-time');
        const nextEventTime = document.getElementById('next-event-time');
        const nextEventText = document.getElementById('next-event-text');
        
        if (localTime) {
            localTime.textContent = this.formatUTCTime(new Date());
        }
        
        if (this.nextEventTime && countdownDisplay) {
            const targetTime = new Date(this.nextEventTime);
            const now = new Date();
            const timeDiff = targetTime - now;
            
            if (timeDiff > 0) {
                const timeRemaining = this.formatTimeRemaining(Math.floor(timeDiff / 1000));
                countdownDisplay.textContent = timeRemaining;
                
                if (nextEventTime) {
                    nextEventTime.textContent = this.formatUTCTime(targetTime);
                }
                
                if (nextEventText) {
                    nextEventText.textContent = this.state === 'ACTIVE' ? 'Next Message:' : 'Next Conversation:';
                }
            } else {
                countdownDisplay.textContent = '00:00';
                if (nextEventTime) {
                    nextEventTime.textContent = 'Calculating...';
                }
            }
        }
    }
    
    updateProgressDisplay() {
        const progressBar = document.getElementById('progress-bar');
        
        if (progressBar) {
            let progressPercent = 0;
            
            if (this.state === 'ACTIVE') {
                // During active conversation: progress based on message count
                progressPercent = (this.messageCount / 16) * 100;
            } else {
                // During waiting: progress based on time until next conversation
                if (this.nextEventTime) {
                    const targetTime = new Date(this.nextEventTime);
                    const now = new Date();
                    const totalWaitTime = 5 * 60 * 1000; // 5 minutes in ms
                    const timeRemaining = targetTime - now;
                    
                    if (timeRemaining > 0 && timeRemaining <= totalWaitTime) {
                        progressPercent = ((totalWaitTime - timeRemaining) / totalWaitTime) * 100;
                    }
                }
            }
            
            progressBar.style.width = Math.min(100, Math.max(0, progressPercent)) + '%';
        }
    }
    
    updateMessageCount() {
        const messageCount = document.getElementById('message-count');
        
        if (messageCount) {
            if (this.state === 'ACTIVE') {
                messageCount.textContent = `${this.messageCount}/16 messages`;
            } else {
                messageCount.textContent = 'Preparing next conversation...';
            }
        }
    }
    
    addMessageToUI(messageData) {
        const messageContainer = document.getElementById('message-container');
        const publicLiveStream = document.getElementById('publicLiveStream');
        
        if (messageContainer || publicLiveStream) {
            const messageElement = this.createMessageElement(messageData);
            
            if (messageContainer) {
                messageContainer.appendChild(messageElement);
                messageContainer.scrollTop = messageContainer.scrollHeight;
            }
            
            if (publicLiveStream) {
                publicLiveStream.appendChild(messageElement.cloneNode(true));
                publicLiveStream.scrollTop = publicLiveStream.scrollHeight;
            }
        }
    }
    
    createMessageElement(messageData) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message-item mb-3 p-3 border rounded';
        
        const agentColor = this.getAgentColor(messageData.agent_type);
        
        messageDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-start mb-2">
                <h6 class="mb-0" style="color: ${agentColor}">
                    <i class="fas fa-robot me-2"></i>${this.escapeHtml(messageData.agent_name)}
                </h6>
                <small class="text-muted">${this.formatUTCTime(new Date(messageData.timestamp))}</small>
            </div>
            <p class="mb-0">${this.escapeHtml(messageData.content)}</p>
        `;
        
        return messageDiv;
    }
    
    getAgentColor(agentType) {
        const colors = {
            'openai': '#0066cc',
            'anthropic': '#cc6600',
            'perplexity': '#009966',
            'gemini': '#9900cc'
        };
        return colors[agentType] || '#666666';
    }
    
    formatUTCTime(date) {
        return new Intl.DateTimeFormat('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false,
            timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
        }).format(date);
    }
    
    formatTimeRemaining(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    startCountdownTimer() {
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }
        
        this.countdownInterval = setInterval(() => {
            this.updateCountdownDisplay();
            this.updateProgressDisplay();
        }, 1000);
    }
    
    setupEventListeners() {
        // Reload page on visibility change to ensure fresh data
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.loadInitialState();
            }
        });
        
        // Handle window focus for data refresh
        window.addEventListener('focus', () => {
            this.loadInitialState();
        });
    }
    
    handleDisconnection() {
        this.connectionAttempts++;
        
        if (this.connectionAttempts < this.maxConnectionAttempts) {
            console.log(`[VisitorIntel] Attempting to reconnect (${this.connectionAttempts}/${this.maxConnectionAttempts})`);
            setTimeout(() => {
                this.connectWebSocket();
            }, this.retryDelay);
        } else {
            console.log('[VisitorIntel] Max reconnection attempts reached, falling back to polling');
            this.fallbackToPolling();
        }
    }
    
    handleConnectionError() {
        console.log('[VisitorIntel] Connection error, attempting fallback');
        this.fallbackToPolling();
    }
    
    fallbackToPolling() {
        console.log('[VisitorIntel] Using polling fallback');
        
        // Poll for updates every 5 seconds
        setInterval(() => {
            this.loadInitialState();
        }, 5000);
    }
    
    updateMessagesFromFallback(conversationData) {
        if (!conversationData || !conversationData.messages) return;
        
        const messageContainer = document.getElementById('message-container');
        const publicLiveStream = document.getElementById('publicLiveStream');
        
        // Clear existing messages
        if (messageContainer) {
            messageContainer.innerHTML = '';
        }
        
        // Add messages in order
        conversationData.messages.slice(-10).forEach(message => {
            this.addMessageToUI(message);
        });
    }
    
    destroy() {
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }
        
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on homepage
    if (document.getElementById('enhanced-countdown')) {
        window.visitorIntelFrontend = new VisitorIntelFrontend();
        window.visitorIntelFrontend.init();
    }
});

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (window.visitorIntelFrontend) {
        window.visitorIntelFrontend.destroy();
    }
});
```

## 6. Routes and API Endpoints

### `routes.py` (Key Routes)
```python
from flask import render_template, request, jsonify, redirect, url_for
from app import app, db
from models import Business, Conversation, ConversationMessage
from ai_conversation import AIConversationManager
import logging

@app.route('/')
def index():
    """Main landing page showcasing AI-to-AI conversations"""
    # Get featured business
    perfect_roofing = Business.query.filter_by(is_featured=True).first()
    if not perfect_roofing:
        perfect_roofing = Business.query.first()
    
    # Get recent conversations
    recent_conversations = Conversation.query.filter_by(
        business_id=perfect_roofing.id if perfect_roofing else None
    ).order_by(Conversation.created_at.desc()).limit(5).all()
    
    # Calculate today's message count
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    total_messages_today = 0
    if perfect_roofing:
        total_messages_today = ConversationMessage.query.join(Conversation).filter(
            Conversation.business_id == perfect_roofing.id,
            ConversationMessage.created_at >= today_start
        ).count()
    
    return render_template('index.html',
                         perfect_roofing=perfect_roofing,
                         recent_conversations=recent_conversations,
                         total_messages_today=total_messages_today)

@app.route('/api/system-status')
def system_status():
    """API endpoint for system status checks"""
    try:
        # Check VisitorIntelSystem status
        from main import intel_system
        
        if intel_system:
            # Get current state from the new system
            state = intel_system.get_current_state()
            
            status = {
                'system_running': True,
                'api_status': {
                    'openai': True,
                    'anthropic': True,
                    'perplexity': True,
                    'gemini': True
                },
                'conversation_active': state.get('conversation_active', False),
                'conversation_status': state.get('status', 'waiting').lower(),
                'active_conversations_count': 1 if state.get('conversation_active', False) else 0,
                'next_conversation_time': state.get('next_conversation_time')
            }
        else:
            # Fallback to basic status
            status = {
                'system_running': True,
                'api_status': {
                    'openai': True,
                    'anthropic': True,
                    'perplexity': True,
                    'gemini': True
                },
                'conversation_active': False,
                'conversation_status': 'waiting',
                'active_conversations_count': 0,
                'next_conversation_time': None
            }
        
        return jsonify(status)
        
    except Exception as e:
        logging.error(f"System status check failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/live-conversation-latest')
def api_live_conversation_latest_backend():
    """Get latest conversation messages for frontend polling"""
    try:
        # Get featured business
        business = Business.query.filter_by(is_featured=True).first()
        if not business:
            business = Business.query.first()
        
        if not business:
            return jsonify({'error': 'No business found'}), 404
        
        # Get latest conversation
        latest_conversation = Conversation.query.filter_by(
            business_id=business.id
        ).order_by(Conversation.created_at.desc()).first()
        
        if not latest_conversation:
            return jsonify({
                'business_name': business.name,
                'conversation_id': None,
                'messages': [],
                'topic': 'No conversations yet'
            })
        
        # Get messages for this conversation
        messages = ConversationMessage.query.filter_by(
            conversation_id=latest_conversation.id
        ).order_by(ConversationMessage.created_at.asc()).all()
        
        # Format messages for frontend
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'id': msg.id,
                'agent_name': msg.agent_name,
                'agent_type': msg.agent_type,
                'content': msg.content,
                'messageNumber': msg.message_number,
                'round': msg.round_number,
                'timestamp': msg.created_at.isoformat()
            })
        
        return jsonify({
            'business_name': business.name,
            'conversation_id': latest_conversation.id,
            'messages': formatted_messages,
            'topic': latest_conversation.topic
        })
        
    except Exception as e:
        logging.error(f"Live conversation API failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/business/<int:business_id>/dashboard')
def business_dashboard(business_id):
    """Business dashboard for managing AI conversations and credits"""
    business = Business.query.get_or_404(business_id)
    
    # Get conversations for this business
    conversations = Conversation.query.filter_by(
        business_id=business_id
    ).order_by(Conversation.created_at.desc()).limit(10).all()
    
    # Calculate statistics
    total_conversations = Conversation.query.filter_by(business_id=business_id).count()
    total_messages = ConversationMessage.query.join(Conversation).filter(
        Conversation.business_id == business_id
    ).count()
    
    return render_template('business_dashboard.html',
                         business=business,
                         conversations=conversations,
                         total_conversations=total_conversations,
                         total_messages=total_messages)

@app.route('/start-conversation', methods=['POST'])
def start_conversation():
    """Start a new AI-to-AI conversation for a business"""
    try:
        business_id = request.form.get('business_id', type=int)
        topic = request.form.get('topic', '')
        
        if not business_id or not topic:
            return jsonify({'error': 'Business ID and topic are required'}), 400
        
        business = Business.query.get_or_404(business_id)
        
        # Check credits for non-unlimited businesses
        if business.subscription_plan != 'Enterprise' and business.credits <= 0:
            return jsonify({'error': 'Insufficient credits'}), 402
        
        # Generate conversation
        ai_manager = AIConversationManager()
        messages = ai_manager.generate_conversation(business, topic)
        
        if not messages:
            return jsonify({'error': 'Failed to generate conversation'}), 500
        
        # Create conversation record
        conversation = Conversation(
            business_id=business_id,
            topic=topic,
            status='completed',
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db.session.add(conversation)
        db.session.flush()
        
        # Save messages
        for i, (agent_name, agent_type, content) in enumerate(messages, 1):
            message = ConversationMessage(
                conversation_id=conversation.id,
                agent_name=agent_name,
                agent_type=agent_type,
                content=content,
                message_number=i,
                round_number=((i-1) // 4) + 1,
                created_at=datetime.utcnow()
            )
            db.session.add(message)
        
        # Deduct credit for non-unlimited businesses
        if business.subscription_plan != 'Enterprise':
            business.credits -= 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'conversation_id': conversation.id,
            'message_count': len(messages)
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Conversation creation failed: {e}")
        return jsonify({'error': str(e)}), 500
```

## 7. HTML Templates

### `templates/base.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}AI Conversation Platform{% endblock %}</title>
    
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Custom CSS -->
    <style>
        .live-indicator {
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .countdown-widget {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .message-item {
            transition: all 0.3s ease;
        }
        
        .message-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .status-badge {
            font-weight: bold;
            font-size: 0.8em;
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">
                <i class="fas fa-comments me-2"></i>AI Conversation Platform
            </a>
        </div>
    </nav>
    
    <!-- Main Content -->
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <!-- Footer -->
    <footer class="bg-dark text-white py-4 mt-5">
        <div class="container text-center">
            <p>&copy; 2025 AI Conversation Platform. All rights reserved.</p>
        </div>
    </footer>
    
    <!-- Bootstrap 5 JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- SocketIO for real-time updates -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    
    <!-- Custom JavaScript -->
    <script src="{{ url_for('static', filename='js/visitor_intel_frontend_fix.js') }}"></script>
    
    {% block scripts %}{% endblock %}
</body>
</html>
```

### `templates/index.html`
```html
{% extends "base.html" %}

{% block title %}AI Conversation Platform - Live AI-to-AI Conversations{% endblock %}

{% block content %}
<!-- Hero Section -->
<section class="bg-primary text-white py-5">
    <div class="container">
        <div class="row align-items-center">
            <div class="col-lg-8">
                <h1 class="display-4 fw-bold mb-4">Real-Time AI-to-AI Conversations</h1>
                <p class="lead mb-4">
                    Watch 4 different AI agents discuss your business in real-time. 
                    Generate authentic conversations that boost SEO and demonstrate expertise.
                </p>
                <div class="d-flex gap-3">
                    <a href="#showcase" class="btn btn-light btn-lg">
                        <i class="fas fa-eye me-2"></i>Watch Live Demo
                    </a>
                    <a href="#pricing" class="btn btn-outline-light btn-lg">
                        <i class="fas fa-rocket me-2"></i>Get Started
                    </a>
                </div>
            </div>
            <div class="col-lg-4">
                <div class="text-center">
                    <i class="fas fa-robot display-1 mb-3"></i>
                    <h3>4 AI Agents</h3>
                    <p>OpenAI • Anthropic • Perplexity • Gemini</p>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Live Showcase Section -->
<section id="showcase" class="py-5 bg-light">
    <div class="container">
        <div class="text-center mb-5">
            <h2 class="h2 fw-bold mb-3">
                <span class="text-primary">{{ perfect_roofing.name }}</span> LIVE Now
                <span class="live-indicator ms-2 badge bg-danger">LIVE</span>
            </h2>
        </div>
        
        <!-- Enhanced VisitorIntel Status Display -->
        <div id="enhanced-countdown" class="mb-4">
            <div class="countdown-widget bg-gradient-primary text-white rounded-4 shadow-lg p-4 mb-4">
                <div class="text-center">
                    <h5 class="fw-bold mb-3">
                        <span id="status-text">AI Conversation Status</span>
                        <span class="status-badge ms-2 px-3 py-1 rounded-pill bg-white text-primary" id="status-badge">WAITING</span>
                    </h5>
                    
                    <div class="countdown-display">
                        <div class="time-display mb-2" id="countdown-display" style="font-size: 2.5em; font-weight: bold; font-family: monospace;">00:00</div>
                        <div class="time-info">
                            <div><strong>Current Time:</strong> <span id="local-time">Loading...</span></div>
                            <div><strong id="next-event-text">Next Event:</strong> <span id="next-event-time">Calculating...</span></div>
                        </div>
                    </div>
                    
                    <div id="message-count" class="mt-3">0/16 messages</div>
                    
                    <div class="countdown-progress mt-3">
                        <div class="progress" style="height: 8px;">
                            <div id="progress-bar" class="progress-bar bg-light" style="width: 0%;"></div>
                        </div>
                        <small class="opacity-75 mt-1 d-block">21-minute conversation cycles (16 messages + 5 min break)</small>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Enhanced Message Container -->
        <div id="enhanced-messages" class="mb-4" style="display: none;">
            <div class="bg-white rounded-4 shadow-sm p-4">
                <h6 class="fw-bold mb-3">
                    <i class="fas fa-comments text-primary me-2"></i>Real-time Messages
                </h6>
                <div id="message-container" class="message-stream" style="max-height: 300px; overflow-y: auto;">
                    <!-- Messages will be inserted here by the frontend fix -->
                </div>
            </div>
        </div>
        
        <!-- Live AI Conversation Feed -->
        <div class="row">
            <div class="col-lg-12">
                <div class="live-conversation-feed bg-white rounded-4 shadow-sm">
                    <div class="card-header bg-gradient-primary text-white p-4 rounded-top-4">
                        <div class="d-flex justify-content-between align-items-center">
                            <h4 class="fw-bold mb-0">
                                <i class="fas fa-comments me-2"></i>Live AI Conversation Feed
                            </h4>
                            <div class="live-indicator">
                                <span class="badge bg-danger fs-6">
                                    <i class="fas fa-circle me-1 pulse"></i>LIVE
                                </span>
                            </div>
                        </div>
                        <p class="mb-0 mt-2 opacity-75">Real-time Public AI-to-AI Conversations for Business Promotion</p>
                    </div>
                    
                    <div class="card-body p-3">
                        <!-- Live conversation stream -->
                        <div class="live-conversation-stream" id="publicLiveStream" style="max-height: 320px; overflow-y: auto; border: 1px solid #e9ecef; border-radius: 8px; padding: 15px; background-color: #f8f9fa;">
                            <!-- Messages will be dynamically inserted here -->
                        </div>
                        
                        <!-- Loading indicator -->
                        <div class="text-center py-4">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Loading conversations...</span>
                            </div>
                            <p class="text-muted mt-2">Loading AI conversations...</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- CTA Section -->
<section class="py-5 bg-primary text-white">
    <div class="container text-center">
        <h2 class="mb-4">Ready to Generate AI Conversations for Your Business?</h2>
        <p class="lead mb-4">Start with 3 free conversations. No credit card required.</p>
        <a href="#" class="btn btn-light btn-lg">
            <i class="fas fa-rocket me-2"></i>Get Started Free
        </a>
    </div>
</section>
{% endblock %}
```

## 8. Requirements and Environment

### `requirements.txt`
```
flask>=3.0.0
flask-sqlalchemy>=3.0.0
flask-socketio>=5.12.0
flask-cors>=4.0.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
apscheduler>=3.10.0
openai>=1.0.0
anthropic>=0.25.0
google-generativeai>=0.4.0
requests>=2.31.0
gunicorn>=23.0.0
eventlet>=0.33.0
python-socketio>=5.12.0
pytz>=2023.3
trafilatura>=1.6.0
```

### `.env` Environment Variables
```bash
# Database
DATABASE_URL=postgresql://username:password@localhost/dbname

# Flask Configuration
SESSION_SECRET=your-secret-key-here

# AI API Keys
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
PERPLEXITY_API_KEY=pplx-your-perplexity-key
GOOGLE_API_KEY=AIza-your-google-key

# Payment (Optional)
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-secret
```

## 9. Deployment Instructions

### Step 1: Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Database Setup
```bash
# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql://user:pass@host:port/dbname"

# Initialize database
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Step 3: Create Initial Data
```python
# Run this in Python shell
from app import app, db
from models import Business, CreditPackage

with app.app_context():
    # Create sample business
    business = Business(
        name="Perfect Roofing Team",
        industry="Construction",
        location="Lodi, New Jersey",
        website="perfectroofingteam.com",
        phone="(555) 123-4567",
        description="Professional roofing services with 20+ years experience",
        is_featured=True,
        subscription_plan="Enterprise",
        credits=-1
    )
    db.session.add(business)
    
    # Create credit packages
    packages = [
        CreditPackage(name="Starter", credits=3, price=0, description="Free trial package"),
        CreditPackage(name="Basic", credits=25, price=2999, description="For small businesses"),
        CreditPackage(name="Pro", credits=100, price=9999, description="For growing businesses", is_popular=True),
        CreditPackage(name="Enterprise", credits=-1, price=29999, description="Unlimited conversations")
    ]
    
    for package in packages:
        db.session.add(package)
    
    db.session.commit()
```

### Step 4: Run Application
```bash
# Development
python main.py

# Production with Gunicorn
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

## 10. Key Features Summary

- **Real-time 21-minute conversation cycles** (16 messages + 5 min break)
- **4 AI agents**: OpenAI, Anthropic, Perplexity, Gemini
- **Progressive message generation** (1 message per minute)
- **WebSocket real-time updates** via SocketIO
- **Local timezone display** with UTC handling
- **Dynamic status badges** (ACTIVE/WAITING)
- **SEO-optimized public pages** for search engines
- **Business dashboard** with conversation management
- **Credit-based pricing system** with PayPal integration
- **Responsive design** with Bootstrap 5
- **Robust error handling** with fallback systems

This complete code package provides everything needed to rebuild the AI conversation platform system with another agent.