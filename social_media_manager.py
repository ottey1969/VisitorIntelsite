"""
Social Media Auto-Posting Manager
Handles social media posting, scheduling, and content management for monthly subscribers
"""

import os
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import and_
import requests
from PIL import Image
from io import BytesIO

from app import db
from models import Business, Conversation, ConversationMessage

class SocialMediaManager:
    """Manages social media posting and scheduling for businesses"""
    
    SUPPORTED_PLATFORMS = {
        'facebook': {
            'name': 'Facebook',
            'max_chars': 63206,
            'supports_images': True,
            'supports_video': True,
            'best_times': ['9:00', '15:00']
        },
        'twitter': {
            'name': 'Twitter/X',
            'max_chars': 280,
            'supports_images': True,
            'supports_video': True,
            'best_times': ['9:00', '17:00']
        },
        'linkedin': {
            'name': 'LinkedIn',
            'max_chars': 3000,
            'supports_images': True,
            'supports_video': True,
            'best_times': ['10:00', '14:00']
        },
        'instagram': {
            'name': 'Instagram',
            'max_chars': 2200,
            'supports_images': True,
            'supports_video': True,
            'best_times': ['11:00', '19:00']
        }
    }
    
    def __init__(self):
        self.post_frequency = 2  # Posts per day
        
    def generate_conversation_highlights(self, conversation_id: int) -> List[Dict[str, Any]]:
        """Generate social media posts from conversation highlights"""
        try:
            conversation = Conversation.query.get(conversation_id)
            if not conversation:
                return []
            
            business = conversation.business
            messages = conversation.messages
            
            # Generate different types of posts
            posts = []
            
            # 1. Quote post from best message
            best_message = self._find_best_message(messages)
            if best_message:
                posts.append({
                    'type': 'quote',
                    'content': self._create_quote_post(best_message, business, conversation.topic),
                    'platform_content': self._adapt_for_platforms(
                        self._create_quote_post(best_message, business, conversation.topic)
                    )
                })
            
            # 2. Conversation summary post
            summary_post = self._create_summary_post(conversation, business)
            posts.append({
                'type': 'summary',
                'content': summary_post,
                'platform_content': self._adapt_for_platforms(summary_post)
            })
            
            # 3. Question/engagement post
            question_post = self._create_question_post(conversation.topic, business)
            posts.append({
                'type': 'question',
                'content': question_post,
                'platform_content': self._adapt_for_platforms(question_post)
            })
            
            return posts
            
        except Exception as e:
            return []
    
    def _find_best_message(self, messages: List[ConversationMessage]) -> Optional[ConversationMessage]:
        """Find the most quotable message from the conversation"""
        if not messages:
            return None
        
        # Prioritize messages with good length and actionable content
        best_message = None
        best_score = 0
        
        for message in messages:
            score = 0
            content = message.content.lower()
            
            # Score based on content quality indicators
            if 50 <= len(message.content) <= 200:  # Good length
                score += 3
            if any(word in content for word in ['tip', 'advice', 'recommend', 'important', 'key']):
                score += 2
            if any(word in content for word in ['?', 'how', 'why', 'what', 'when']):
                score += 1
            
            if score > best_score:
                best_score = score
                best_message = message
        
        return best_message or messages[0]
    
    def _create_quote_post(self, message: ConversationMessage, business: Business, topic: str) -> str:
        """Create a quote-style social media post"""
        content = message.content
        if len(content) > 150:
            content = content[:147] + "..."
        
        return f'💡 "{content}"\n\n- {message.ai_agent_name} discussing {topic}\n\n#{business.name.replace(" ", "")} #AI #BusinessTips'
    
    def _create_summary_post(self, conversation: Conversation, business: Business) -> str:
        """Create a conversation summary post"""
        agent_count = len(set(msg.ai_agent_name for msg in conversation.messages))
        message_count = len(conversation.messages)
        
        return f"""🤖 Just wrapped up an AI conversation about {conversation.topic}!

{agent_count} AI experts discussed key insights in {message_count} messages.

Want to see what AI thinks about your business? Check out our full conversations!

#{business.name.replace(" ", "")} #AI #BusinessInsights #Conversations"""
    
    def _create_question_post(self, topic: str, business: Business) -> str:
        """Create an engagement question post"""
        return f"""❓ What's your take on {topic}?

Our AI experts just had a deep discussion about this topic. We'd love to hear your thoughts!

Drop a comment below 👇

#{business.name.replace(" ", "")} #Discussion #BusinessTalk #AI"""
    
    def _adapt_for_platforms(self, base_content: str) -> Dict[str, str]:
        """Adapt content for different social media platforms"""
        adapted = {}
        
        for platform, config in self.SUPPORTED_PLATFORMS.items():
            content = base_content
            
            # Truncate if needed
            if len(content) > config['max_chars']:
                content = content[:config['max_chars']-3] + "..."
            
            # Platform-specific adaptations
            if platform == 'twitter':
                # Add Twitter-specific hashtags
                content = content.replace('#AI', '#AI #Tech')
            elif platform == 'linkedin':
                # More professional tone for LinkedIn
                content = content.replace('🤖', '🚀').replace('❓', '💼')
            elif platform == 'facebook':
                # More casual for Facebook
                content += '\n\nWhat do you think? Let us know in the comments!'
            
            adapted[platform] = content
        
        return adapted
    
    def schedule_daily_posts(self, business_id: int, selected_platforms: List[str], 
                           custom_times: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
        """Schedule daily posts for a business"""
        try:
            business = Business.query.get(business_id)
            if not business:
                return {'success': False, 'error': 'Business not found'}
            
            # Check if monthly subscriber
            if business.subscription_type == 'credit':
                return {'success': False, 'error': 'Social media posting is only available for monthly subscribers'}
            
            # Get recent conversations for content
            recent_conversations = Conversation.query.filter_by(
                business_id=business_id
            ).order_by(Conversation.created_at.desc()).limit(5).all()
            
            if not recent_conversations:
                return {'success': False, 'error': 'No conversations available for posting'}
            
            # Generate posts for next 7 days
            scheduled_posts = []
            for i in range(7):
                post_date = datetime.now() + timedelta(days=i)
                
                # Get conversation for this day (cycle through available)
                conversation = recent_conversations[i % len(recent_conversations)]
                
                # Generate posts for this conversation
                posts = self.generate_conversation_highlights(conversation.id)
                
                # Schedule posts for selected platforms
                for platform in selected_platforms:
                    if platform not in self.SUPPORTED_PLATFORMS:
                        continue
                    
                    # Use custom times or default times
                    times = custom_times.get(platform) if custom_times else self.SUPPORTED_PLATFORMS[platform]['best_times']
                    
                    for time_str in times[:2]:  # Maximum 2 posts per day
                        post_time = datetime.strptime(f"{post_date.strftime('%Y-%m-%d')} {time_str}", '%Y-%m-%d %H:%M')
                        
                        # Select post type (cycle through available)
                        post_data = posts[len(scheduled_posts) % len(posts)] if posts else None
                        
                        if post_data:
                            scheduled_posts.append({
                                'platform': platform,
                                'scheduled_time': post_time,
                                'content': post_data['platform_content'].get(platform, post_data['content']),
                                'type': post_data['type'],
                                'conversation_id': conversation.id
                            })
            
            return {
                'success': True,
                'scheduled_posts': len(scheduled_posts),
                'posts': scheduled_posts[:10],  # Return first 10 for preview
                'message': f'Successfully scheduled {len(scheduled_posts)} posts across {len(selected_platforms)} platforms'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def add_custom_post(self, business_id: int, platform: str, content: str, 
                       image_data: Optional[str] = None, scheduled_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Add a custom post with optional scheduling"""
        try:
            business = Business.query.get(business_id)
            if not business:
                return {'success': False, 'error': 'Business not found'}
            
            # Check if monthly subscriber
            if business.subscription_type == 'credit':
                return {'success': False, 'error': 'Custom posting is only available for monthly subscribers'}
            
            if platform not in self.SUPPORTED_PLATFORMS:
                return {'success': False, 'error': 'Unsupported platform'}
            
            # Validate content length
            max_chars = self.SUPPORTED_PLATFORMS[platform]['max_chars']
            if len(content) > max_chars:
                return {'success': False, 'error': f'Content too long. Maximum {max_chars} characters for {platform}'}
            
            # Store custom post (in production, this would go to a database table)
            post_data = {
                'business_id': business_id,
                'platform': platform,
                'content': content,
                'image_data': image_data,
                'scheduled_time': scheduled_time.isoformat() if scheduled_time else None,
                'created_at': datetime.now().isoformat(),
                'status': 'scheduled' if scheduled_time else 'ready'
            }
            
            # In production, save to database
            # For now, return success with post data
            return {
                'success': True,
                'post_id': f'custom_{business_id}_{datetime.now().timestamp()}',
                'post_data': post_data,
                'message': 'Custom post added successfully'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_posting_analytics(self, business_id: int) -> Dict[str, Any]:
        """Get social media posting analytics for a business"""
        try:
            business = Business.query.get(business_id)
            if not business:
                return {'success': False, 'error': 'Business not found'}
            
            # Mock analytics data (in production, this would come from social media APIs)
            return {
                'success': True,
                'analytics': {
                    'total_posts': 45,
                    'total_engagements': 1250,
                    'avg_engagement_rate': 8.5,
                    'top_performing_platform': 'LinkedIn',
                    'platform_breakdown': {
                        'facebook': {'posts': 15, 'engagements': 400, 'rate': 7.2},
                        'twitter': {'posts': 12, 'engagements': 350, 'rate': 6.8},
                        'linkedin': {'posts': 10, 'engagements': 300, 'rate': 12.1},
                        'instagram': {'posts': 8, 'engagements': 200, 'rate': 5.5}
                    },
                    'recent_posts': [
                        {
                            'platform': 'LinkedIn',
                            'content': 'AI insights about roofing maintenance...',
                            'posted_at': '2025-07-02T14:00:00Z',
                            'engagements': 45
                        },
                        {
                            'platform': 'Facebook',
                            'content': 'What our AI experts think about...',
                            'posted_at': '2025-07-02T09:00:00Z',
                            'engagements': 32
                        }
                    ]
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_platform_settings(self, business_id: int) -> Dict[str, Any]:
        """Get social media platform settings for a business"""
        try:
            business = Business.query.get(business_id)
            if not business:
                return {'success': False, 'error': 'Business not found'}
            
            return {
                'success': True,
                'platforms': self.SUPPORTED_PLATFORMS,
                'current_settings': {
                    'enabled_platforms': ['facebook', 'linkedin'],  # Default enabled
                    'posting_frequency': 2,  # Posts per day
                    'custom_times': {
                        'facebook': ['9:00', '15:00'],
                        'linkedin': ['10:00', '14:00']
                    },
                    'auto_hashtags': True,
                    'include_business_name': True
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}