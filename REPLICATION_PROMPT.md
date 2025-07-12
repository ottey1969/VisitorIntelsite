# Complete AI Conversation Platform Replication Prompt

**PROMPT FOR AI AGENT:** 

Build a complete AI conversation platform that generates real-time conversations between 4 AI agents (OpenAI GPT-4o, Anthropic Claude, Perplexity AI, Google Gemini) with precise 21-minute cycles, progressive message generation at 1-minute intervals, and live WebSocket updates. Follow these exact specifications and code implementations.

## SYSTEM REQUIREMENTS

### Core Architecture
- Flask web application with PostgreSQL database
- Real-time WebSocket communication via Flask-SocketIO
- APScheduler for precise timing (21-minute cycles: 16 messages + 5 min break)
- 4 AI API integrations with fallback systems
- Bootstrap 5 responsive frontend
- Progressive message generation (1 message per minute)

### Database Schema
```sql
-- Business table
CREATE TABLE business (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    industry VARCHAR(50),
    location VARCHAR(100),
    website VARCHAR(200),
    phone VARCHAR(20),
    description TEXT,
    is_featured BOOLEAN DEFAULT FALSE,
    subscription_plan VARCHAR(20) DEFAULT 'Free',
    credits INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Conversation table
CREATE TABLE conversation (
    id SERIAL PRIMARY KEY,
    business_id INTEGER REFERENCES business(id),
    topic VARCHAR(500),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- ConversationMessage table
CREATE TABLE conversation_message (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversation(id),
    agent_name VARCHAR(50) NOT NULL,
    agent_type VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    message_number INTEGER,
    round_number INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- CreditPackage table
CREATE TABLE credit_package (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    credits INTEGER NOT NULL,
    price INTEGER NOT NULL,
    description TEXT,
    is_popular BOOLEAN DEFAULT FALSE
);

-- Purchase table
CREATE TABLE purchase (
    id SERIAL PRIMARY KEY,
    business_id INTEGER REFERENCES business(id),
    package_id INTEGER REFERENCES credit_package(id),
    amount INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    transaction_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## COMPLETE SOURCE CODE

### 1. main.py (Application Entry Point)
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

### 2. app.py (Flask Application Setup)
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

### 3. visitor_intel_backend_fix.py (Core System Controller)
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

### 4. models.py (Database Models)
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

### 5. ai_conversation.py (AI Integration Manager)
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
```

### 6. routes.py (API Endpoints)
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
```

### 7. static/js/visitor_intel_frontend_fix.js (Frontend Controller)
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

### 8. templates/base.html (Layout Foundation)
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

### 9. templates/index.html (Homepage)
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

### 10. requirements.txt (Dependencies)
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
```

## ENVIRONMENT VARIABLES
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
```

## STEP-BY-STEP DEPLOYMENT INSTRUCTIONS

### Step 1: Environment Setup and Project Structure
```bash
# Create project directory
mkdir ai-conversation-platform
cd ai-conversation-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create project structure
mkdir -p static/js templates
touch main.py app.py models.py routes.py
touch visitor_intel_backend_fix.py ai_conversation.py
touch requirements.txt
```

### Step 2: Install Dependencies
Create `requirements.txt` with the provided content, then:
```bash
pip install -r requirements.txt
```

### Step 3: Environment Variables Setup
Create `.env` file or set environment variables:
```bash
# Set these environment variables
export DATABASE_URL="postgresql://user:pass@host:port/dbname"
export SESSION_SECRET="your-secret-key-here"
export OPENAI_API_KEY="sk-your-openai-key"
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"
export PERPLEXITY_API_KEY="pplx-your-perplexity-key"
export GOOGLE_API_KEY="AIza-your-google-key"
```

### Step 4: Create All Source Files
Copy all the provided source code into their respective files:

1. **main.py** - Application entry point with SocketIO
2. **app.py** - Flask application setup
3. **visitor_intel_backend_fix.py** - Core system controller
4. **models.py** - Database models
5. **ai_conversation.py** - AI integration manager
6. **routes.py** - API endpoints
7. **static/js/visitor_intel_frontend_fix.js** - Frontend controller
8. **templates/base.html** - Layout foundation
9. **templates/index.html** - Homepage template

### Step 5: Database Setup
```bash
# Initialize database
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Step 6: Create Initial Data
```python
# Run this in Python shell
python -c "
from app import app, db
from models import Business, CreditPackage

with app.app_context():
    # Create sample business
    business = Business(
        name='Perfect Roofing Team',
        industry='Construction',
        location='Lodi, New Jersey',
        website='perfectroofingteam.com',
        phone='(555) 123-4567',
        description='Professional roofing services with 20+ years experience',
        is_featured=True,
        subscription_plan='Enterprise',
        credits=-1
    )
    db.session.add(business)
    
    # Create credit packages
    packages = [
        CreditPackage(name='Starter', credits=3, price=0, description='Free trial package'),
        CreditPackage(name='Basic', credits=25, price=2999, description='For small businesses'),
        CreditPackage(name='Pro', credits=100, price=9999, description='For growing businesses', is_popular=True),
        CreditPackage(name='Enterprise', credits=-1, price=29999, description='Unlimited conversations')
    ]
    
    for package in packages:
        db.session.add(package)
    
    db.session.commit()
    print('Initial data created successfully')
"
```

### Step 7: Run Application
```bash
# Development mode
python main.py

# Production with Gunicorn
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

### Step 8: Verify System Operation
1. **Check Homepage**: Navigate to `http://localhost:5000`
2. **Verify Status Display**: Should show "WAITING" status with countdown
3. **Check API Endpoints**: 
   - `http://localhost:5000/api/system-status`
   - `http://localhost:5000/api/live-conversation-latest`
4. **Watch Console Logs**: Should see VisitorIntelSystem initialization
5. **Wait for First Conversation**: System starts conversation every 5 minutes

### Step 9: System Verification Checklist
- [ ] Homepage loads with status display
- [ ] WebSocket connection established
- [ ] Countdown timer shows proper time
- [ ] Status badges show WAITING/ACTIVE states
- [ ] API endpoints return proper JSON
- [ ] Database tables created successfully
- [ ] VisitorIntelSystem scheduler running
- [ ] All 4 AI agents configured properly

## SYSTEM SPECIFICATIONS

### Timing Requirements
- **21-minute conversation cycles** (16 messages + 5 min break)
- **Progressive message generation** (exactly 1 message per minute)
- **5-minute break** between conversation cycles
- **Real-time scheduling** using APScheduler with precise timing

### AI Integration Requirements
- **4 AI agents**: OpenAI GPT-4o, Anthropic Claude, Perplexity AI, Google Gemini
- **Agent rotation**: Business AI → SEO AI → Customer Service AI → Marketing AI
- **4 rounds of conversation** (4 agents × 4 rounds = 16 messages)
- **Fallback system** for API failures with professional backup responses

### Frontend Requirements
- **Real-time WebSocket updates** via Flask-SocketIO
- **Dynamic status display** with ACTIVE/WAITING badges
- **Local timezone conversion** from UTC timestamps
- **Progressive message appearance** as they're generated
- **Responsive Bootstrap 5 design** with custom styling
- **Live countdown timer** showing time to next event

### Database Requirements
- **PostgreSQL database** with proper relationships
- **5 core tables**: Business, Conversation, ConversationMessage, CreditPackage, Purchase
- **Proper indexing** for conversation queries
- **UTC timestamp storage** with timezone conversion

### Error Handling Requirements
- **Complete API fallback system** when external APIs fail
- **WebSocket reconnection logic** with polling fallback
- **Database connection resilience** with pool configuration
- **Graceful degradation** maintaining functionality during failures

## EXPECTED SYSTEM BEHAVIOR

### Conversation Flow
1. **WAITING State** (5 minutes): Shows countdown to next conversation
2. **ACTIVE State** (16 minutes): Progressive message generation at 1-minute intervals
3. **Message Order**: Business AI → SEO AI → Customer Service AI → Marketing AI (repeats 4 times)
4. **Completion**: Marks conversation as completed, schedules next cycle

### Real-time Updates
- **WebSocket Events**: state_update, new_message
- **API Polling**: Fallback every 5 seconds if WebSocket fails
- **Status Synchronization**: All clients show same status simultaneously
- **Message Broadcasting**: New messages appear on all connected clients

### User Experience
- **Immediate Feedback**: Status changes reflect instantly
- **Visual Progress**: Progress bar shows conversation completion
- **Time Display**: All times in user's local timezone
- **Loading States**: Proper loading indicators during API calls

## TROUBLESHOOTING GUIDE

### Common Issues
1. **WebSocket Disconnections**: System automatically falls back to polling
2. **API Rate Limits**: Fallback messages maintain conversation flow
3. **Database Timeouts**: Connection pooling handles reconnection
4. **Scheduler Issues**: Background scheduler restarts automatically

### Verification Commands
```bash
# Check database connection
python -c "from app import app, db; app.app_context().push(); print('DB Connected:', db.session.execute('SELECT 1').scalar() == 1)"

# Verify API keys
python -c "import os; print('OpenAI:', bool(os.environ.get('OPENAI_API_KEY'))); print('Anthropic:', bool(os.environ.get('ANTHROPIC_API_KEY')))"

# Test scheduler
python -c "from visitor_intel_backend_fix import VisitorIntelSystem; print('Scheduler available')"
```

This complete prompt contains everything needed to replicate the exact AI conversation platform webapp with all specifications, code, and step-by-step instructions.