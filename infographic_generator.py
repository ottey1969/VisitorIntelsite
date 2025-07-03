"""
Infographic Generator for AI Conversations
Creates visual content from conversation data for social media posting
"""

import os
import json
import base64
from datetime import datetime
from typing import Dict, List, Any
from PIL import Image, ImageDraw, ImageFont
import textwrap
import requests
from io import BytesIO

from app import db
from models import Conversation, ConversationMessage, Business

class InfographicGenerator:
    """Generates infographics from AI conversation data"""
    
    def __init__(self):
        self.width = 1080
        self.height = 1080
        self.background_colors = {
            'primary': '#2563eb',
            'secondary': '#1e40af', 
            'accent': '#f59e0b',
            'text': '#1f2937',
            'light': '#f8fafc'
        }
    
    def generate_conversation_infographic(self, conversation_id: int) -> Dict[str, Any]:
        """Generate an infographic from a conversation"""
        try:
            conversation = Conversation.query.get(conversation_id)
            if not conversation:
                return {'success': False, 'error': 'Conversation not found'}
            
            business = conversation.business
            messages = conversation.messages[:4]  # Get first 4 messages for infographic
            
            # Create infographic image
            img = Image.new('RGB', (self.width, self.height), self.background_colors['light'])
            draw = ImageDraw.Draw(img)
            
            # Add header
            self._add_header(draw, business.name, conversation.topic)
            
            # Add conversation highlights
            self._add_conversation_highlights(draw, messages)
            
            # Add footer with branding
            self._add_footer(draw, business.name)
            
            # Save to bytes
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG', quality=95)
            img_bytes = img_buffer.getvalue()
            
            # Encode to base64 for storage
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            return {
                'success': True,
                'image_data': img_base64,
                'filename': f'conversation_{conversation_id}_infographic.png',
                'title': f'{business.name} - {conversation.topic}',
                'description': f'AI conversation insights about {conversation.topic}'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _add_header(self, draw, business_name: str, topic: str):
        """Add header section to infographic"""
        try:
            # Use default font since custom fonts might not be available
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            
            # Business name
            draw.text((50, 50), business_name, fill=self.background_colors['primary'], font=title_font)
            
            # Topic
            wrapped_topic = textwrap.fill(topic, width=40)
            draw.text((50, 100), wrapped_topic, fill=self.background_colors['text'], font=subtitle_font)
            
            # Separator line
            draw.line([(50, 180), (self.width-50, 180)], fill=self.background_colors['accent'], width=3)
            
        except Exception as e:
            # Fallback to basic text
            draw.text((50, 50), business_name, fill=self.background_colors['primary'])
            draw.text((50, 100), topic[:50], fill=self.background_colors['text'])
    
    def _add_conversation_highlights(self, draw, messages: List[ConversationMessage]):
        """Add conversation highlights to infographic"""
        try:
            y_position = 220
            font = ImageFont.load_default()
            
            for i, message in enumerate(messages):
                if y_position > self.height - 200:  # Leave space for footer
                    break
                
                # Agent name
                agent_text = f"💬 {message.ai_agent_name}"
                draw.text((50, y_position), agent_text, fill=self.background_colors['primary'], font=font)
                y_position += 30
                
                # Message content (truncated)
                content = message.content[:150] + "..." if len(message.content) > 150 else message.content
                wrapped_content = textwrap.fill(content, width=60)
                
                for line in wrapped_content.split('\n'):
                    draw.text((70, y_position), line, fill=self.background_colors['text'], font=font)
                    y_position += 25
                
                y_position += 20  # Space between messages
                
        except Exception as e:
            # Fallback
            draw.text((50, 220), "AI Conversation Highlights", fill=self.background_colors['text'])
    
    def _add_footer(self, draw, business_name: str):
        """Add footer with branding"""
        try:
            font = ImageFont.load_default()
            
            # Footer background
            footer_y = self.height - 120
            draw.rectangle([(0, footer_y), (self.width, self.height)], fill=self.background_colors['primary'])
            
            # Footer text
            footer_text = f"Generated by AI for {business_name}"
            draw.text((50, footer_y + 30), footer_text, fill='white', font=font)
            
            # Timestamp
            timestamp = datetime.now().strftime("%B %d, %Y")
            draw.text((50, footer_y + 60), timestamp, fill='white', font=font)
            
        except Exception as e:
            # Fallback
            draw.text((50, self.height - 100), f"AI Generated - {business_name}", fill=self.background_colors['primary'])
    
    def generate_business_stats_infographic(self, business_id: int) -> Dict[str, Any]:
        """Generate business statistics infographic"""
        try:
            business = Business.query.get(business_id)
            if not business:
                return {'success': False, 'error': 'Business not found'}
            
            conversations = Conversation.query.filter_by(business_id=business_id).all()
            total_messages = sum(len(conv.messages) for conv in conversations)
            
            # Create stats infographic
            img = Image.new('RGB', (self.width, self.height), self.background_colors['light'])
            draw = ImageDraw.Draw(img)
            
            # Add business stats
            self._add_stats_content(draw, business, len(conversations), total_messages)
            
            # Save to bytes
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG', quality=95)
            img_bytes = img_buffer.getvalue()
            
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            return {
                'success': True,
                'image_data': img_base64,
                'filename': f'business_{business_id}_stats.png',
                'title': f'{business.name} - AI Conversation Stats',
                'description': f'Monthly AI conversation statistics for {business.name}'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _add_stats_content(self, draw, business: Business, conversation_count: int, message_count: int):
        """Add statistics content to infographic"""
        try:
            font = ImageFont.load_default()
            
            # Title
            draw.text((50, 50), f"{business.name} Stats", fill=self.background_colors['primary'], font=font)
            
            # Stats
            stats = [
                f"📊 Total Conversations: {conversation_count}",
                f"💬 Total Messages: {message_count}",
                f"🏢 Industry: {business.industry or 'General'}",
                f"📍 Location: {business.location or 'Not specified'}",
                f"📅 Member since: {business.created_at.strftime('%B %Y') if business.created_at else 'Unknown'}"
            ]
            
            y_pos = 150
            for stat in stats:
                draw.text((50, y_pos), stat, fill=self.background_colors['text'], font=font)
                y_pos += 50
            
            # Footer
            draw.text((50, self.height - 100), "Powered by AI Conversations", fill=self.background_colors['primary'], font=font)
            
        except Exception as e:
            # Fallback
            draw.text((50, 150), "Business Statistics", fill=self.background_colors['text'])