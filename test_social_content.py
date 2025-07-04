#!/usr/bin/env python3
"""Test the enhanced social media content generation"""

from social_media_manager import SocialMediaManager
from models import Business, Conversation, ConversationMessage
from app import app, db

def test_enhanced_content():
    """Test the new professional content generation"""
    with app.app_context():
        # Get Perfect Roofing Team business
        business = Business.query.get(5)
        if not business:
            print("Business not found")
            return
        
        # Get latest conversation
        conversation = Conversation.query.filter_by(business_id=5).order_by(Conversation.created_at.desc()).first()
        if not conversation:
            print("No conversation found")
            return
            
        print(f"Testing enhanced content for: {business.name}")
        print(f"Conversation topic: {conversation.topic}")
        print(f"Messages count: {len(conversation.messages)}")
        print("=" * 60)
        
        # Create social media manager
        sm_manager = SocialMediaManager()
        
        # Generate professional content highlights
        posts = sm_manager.generate_conversation_highlights(conversation.id)
        
        for i, post in enumerate(posts, 1):
            print(f"\n--- POST {i}: {post['type'].upper()} ---")
            print(post['content'])
            print("\nPlatform adaptations:")
            for platform, adapted_content in post['platform_content'].items():
                print(f"\n{platform.upper()}:")
                print(adapted_content)
                print(f"Length: {len(adapted_content)} chars")
            print("-" * 60)

if __name__ == "__main__":
    test_enhanced_content()