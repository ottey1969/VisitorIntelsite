from app import db
from datetime import datetime
from sqlalchemy import Text, Boolean, Integer, String, DateTime, Float

class Business(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    website = db.Column(db.String(500))
    description = db.Column(Text)
    location = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(200))
    industry = db.Column(db.String(100))
    is_unlimited = db.Column(Boolean, default=False)
    credits_remaining = db.Column(Integer, default=0)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    share_url = db.Column(String(500))
    plan_type = db.Column(String(50), default='basic')  # basic, enterprise
    custom_domain = db.Column(String(200))  # For enterprise customers
    
    # Relationship to conversations
    conversations = db.relationship('Conversation', backref='business', lazy=True)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)
    topic = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), default='active')  # active, completed, paused
    created_at = db.Column(DateTime, default=datetime.utcnow)
    credits_used = db.Column(Integer, default=0)
    
    # Relationship to messages
    messages = db.relationship('ConversationMessage', backref='conversation', lazy=True, order_by='ConversationMessage.created_at')

class ConversationMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    ai_agent_name = db.Column(db.String(100), nullable=False)
    ai_agent_type = db.Column(db.String(50), nullable=False)  # openai, anthropic
    content = db.Column(Text, nullable=False)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    message_order = db.Column(Integer, nullable=False)

class CreditPackage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    credits = db.Column(Integer, nullable=False)
    price = db.Column(Float, nullable=False)
    is_popular = db.Column(Boolean, default=False)
    description = db.Column(Text)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('credit_package.id'), nullable=False)
    credits_purchased = db.Column(Integer, nullable=False)
    amount_paid = db.Column(Float, nullable=False)
    payment_id = db.Column(db.String(200))  # PayPal transaction ID
    status = db.Column(db.String(50), default='pending')  # pending, completed, failed
    created_at = db.Column(DateTime, default=datetime.utcnow)
