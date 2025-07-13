from app import db
from datetime import datetime, timezone
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
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))
    share_url = db.Column(String(500))
    plan_type = db.Column(String(50), default='basic')  # basic, enterprise
    custom_domain = db.Column(String(200))  # For enterprise customers
    is_featured = db.Column(Boolean, default=False)  # Featured on homepage
    
    # Monthly subscription fields
    subscription_type = db.Column(String(50), default='credit')  # credit, monthly_basic, monthly_pro, monthly_enterprise
    monthly_conversation_limit = db.Column(Integer, default=0)  # Monthly conversation allowance
    conversations_used_this_month = db.Column(Integer, default=0)  # Conversations used in current month
    subscription_start_date = db.Column(DateTime)  # When current subscription started
    subscription_end_date = db.Column(DateTime)  # When current subscription ends
    auto_renew = db.Column(Boolean, default=True)  # Auto-renewal setting
    
    # Relationship to conversations
    conversations = db.relationship('Conversation', backref='business', lazy=True)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)
    topic = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), default='active')  # active, completed, paused
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))
    credits_used = db.Column(Integer, default=0)
    
    # Relationship to messages
    messages = db.relationship('ConversationMessage', backref='conversation', lazy=True, order_by='ConversationMessage.created_at')

class ConversationMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    ai_agent_name = db.Column(db.String(100), nullable=False)
    ai_agent_type = db.Column(db.String(50), nullable=False)  # openai, anthropic
    content = db.Column(Text, nullable=False)
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))
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
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SocialMediaPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=True)
    platform = db.Column(db.String(50), nullable=False)  # facebook, twitter, linkedin, instagram
    content = db.Column(Text, nullable=False)
    image_data = db.Column(Text)  # Base64 encoded image data
    post_type = db.Column(db.String(50), default='auto')  # auto, custom, scheduled
    scheduled_time = db.Column(DateTime)
    posted_time = db.Column(DateTime)
    status = db.Column(db.String(50), default='scheduled')  # scheduled, posted, failed
    engagement_count = db.Column(Integer, default=0)
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    business = db.relationship('Business', backref='social_posts')
    conversation = db.relationship('Conversation', backref='social_posts')

class SocialMediaSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # facebook, twitter, linkedin, instagram
    is_enabled = db.Column(Boolean, default=True)
    posting_times = db.Column(Text)  # JSON string of posting times
    auto_hashtags = db.Column(Boolean, default=True)
    include_business_name = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    business = db.relationship('Business', backref='social_settings')
