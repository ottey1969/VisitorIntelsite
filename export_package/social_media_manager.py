"""
Social Media Auto-Posting Manager
Handles social media posting, scheduling, and content management for monthly subscribers
"""

import os
import json
import base64
import random
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
    
    # Professional content templates for different industries and contexts
    CONTENT_TEMPLATES = {
        'roofing': {
            'opening_hooks': [
                "🏠 Protecting your home with premium roofing excellence!",
                "⚡ Emergency roofing services available 24/7!",
                "🔧 Expert roofing contractors delivering quality results!",
                "🌟 Industry-leading roofing solutions for your peace of mind!",
                "💪 Trusted roofing professionals with proven track records!",
                "🛡️ Your roof, our expertise - unmatched protection guaranteed!",
                "🎯 Precision roofing services that exceed expectations!",
                "🏆 Award-winning roofing contractors serving your community!"
            ],
            'value_propositions': [
                "Licensed, insured, and dedicated to exceptional craftsmanship.",
                "Years of experience delivering reliable roofing solutions.",
                "Emergency response team ready when you need us most.",
                "Quality materials and professional installation guaranteed.",
                "Local expertise with industry-leading certifications.",
                "Comprehensive roofing services from repair to replacement.",
                "Customer satisfaction backed by solid warranties.",
                "Advanced roofing technology for modern home protection."
            ],
            'call_to_actions': [
                "Contact us today for your free roofing consultation!",
                "Get your professional roof inspection scheduled now!",
                "Don't wait - protect your investment with expert roofing!",
                "Ready to experience the difference? Call us today!",
                "Schedule your roofing assessment with our experts!",
                "Transform your roof with professional quality service!",
                "Get started with New Jersey's trusted roofing team!",
                "Secure your home's future with our roofing experts!"
            ],
            'hashtags': {
                'general': ['#RoofingExperts', '#QualityRoofing', '#ProfessionalService', '#HomeProtection'],
                'emergency': ['#EmergencyRoofing', '#StormDamage', '#RoofRepair', '#24x7Service'],
                'location': ['#NewJerseyRoofing', '#LodRoofing', '#LocalContractors', '#NJHomelimprovement'],
                'quality': ['#LicensedRoofers', '#InsuredContractors', '#WarrantyBacked', '#CertifiedProfessionals']
            }
        },
        'general': {
            'opening_hooks': [
                "🚀 Excellence in service, innovation in approach!",
                "💼 Professional solutions tailored to your needs!",
                "⭐ Delivering exceptional results every single time!",
                "🎯 Your success is our commitment and priority!",
                "🏆 Industry leaders with proven track records!",
                "💪 Dedicated professionals exceeding expectations!",
                "🔥 Innovation meets expertise in every project!",
                "✨ Premium service quality you can trust completely!"
            ],
            'value_propositions': [
                "Certified professionals delivering outstanding results.",
                "Years of experience serving satisfied customers.",
                "Quality service backed by comprehensive warranties.",
                "Local expertise with industry-leading standards.",
                "Customer-focused approach with personalized solutions.",
                "Reliable service you can count on every time.",
                "Professional excellence in everything we do.",
                "Innovative solutions for modern challenges."
            ],
            'call_to_actions': [
                "Contact us today for your free consultation!",
                "Ready to get started? Reach out now!",
                "Experience the difference - call us today!",
                "Let's discuss your project requirements!",
                "Schedule your consultation with our experts!",
                "Get your personalized quote today!",
                "Don't wait - contact our team now!",
                "Ready to see exceptional results? Call us!"
            ],
            'hashtags': {
                'general': ['#ProfessionalService', '#QualityWork', '#CustomerFirst', '#TrustedExperts'],
                'local': ['#LocalBusiness', '#CommunityTrusted', '#LocalExperts', '#YourNeighborhood'],
                'quality': ['#QualityGuaranteed', '#ProfessionalStandards', '#ExcellentService', '#ReliableResults']
            }
        }
    }
    
    EMOJI_SETS = {
        'professional': ['💼', '🏆', '⭐', '✅', '🎯', '💪', '🔧', '📞'],
        'service': ['🛠️', '🔨', '⚡', '🚀', '💡', '🏠', '🔑', '📋'],
        'quality': ['🌟', '🥇', '👍', '✨', '💎', '🛡️', '🎖️', '🏅'],
        'communication': ['📞', '💬', '📧', '📱', '💻', '🗣️', '📝', '📞']
    }
    
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
        """Generate social media posts from conversation highlights using professional content templates"""
        try:
            conversation = Conversation.query.get(conversation_id)
            if not conversation:
                return []
            
            business = conversation.business
            
            # Generate different types of professional posts
            posts = []
            
            # 1. Conversation highlight post with AI quote
            highlight_content = self._generate_professional_content(conversation, business, 'conversation_highlight')
            posts.append({
                'type': 'conversation_highlight',
                'content': highlight_content,
                'platform_content': self._adapt_for_platforms_professional(highlight_content)
            })
            
            # 2. Conversation summary post with statistics
            summary_content = self._generate_professional_content(conversation, business, 'summary')
            posts.append({
                'type': 'summary',
                'content': summary_content,
                'platform_content': self._adapt_for_platforms_professional(summary_content)
            })
            
            # 3. Question/engagement post to drive interaction
            question_content = self._generate_professional_content(conversation, business, 'question_engagement')
            posts.append({
                'type': 'question_engagement',
                'content': question_content,
                'platform_content': self._adapt_for_platforms_professional(question_content)
            })
            
            # 4. Service showcase post (bonus content)
            showcase_content = self._generate_professional_content(conversation, business, 'service_showcase')
            posts.append({
                'type': 'service_showcase',
                'content': showcase_content,
                'platform_content': self._adapt_for_platforms_professional(showcase_content)
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
    
    def _get_industry_content(self, business):
        """Get industry-specific content templates"""
        industry_key = 'roofing' if 'roof' in business.industry.lower() else 'general'
        return self.CONTENT_TEMPLATES.get(industry_key, self.CONTENT_TEMPLATES['general'])
    
    def _generate_professional_content(self, conversation, business, post_type='highlight'):
        """Generate professional social media content with proper emojis and hashtags"""
        content_templates = self._get_industry_content(business)
        
        # Get random content elements to ensure variety
        hook = random.choice(content_templates['opening_hooks'])
        value_prop = random.choice(content_templates['value_propositions'])
        cta = random.choice(content_templates['call_to_actions'])
        
        # Get relevant hashtags
        hashtag_categories = ['general', 'quality']
        if business.location and 'new jersey' in business.location.lower():
            hashtag_categories.append('location')
        
        hashtags = []
        for category in hashtag_categories:
            if category in content_templates['hashtags']:
                hashtags.extend(content_templates['hashtags'][category])
        
        # Add business-specific hashtags
        business_hashtag = f"#{business.name.replace(' ', '')}"
        hashtags.insert(0, business_hashtag)
        
        # Limit to 6-8 hashtags for optimal engagement
        hashtags = hashtags[:8]
        hashtag_string = ' '.join(hashtags)
        
        if post_type == 'conversation_highlight':
            # Get the best message from conversation
            best_message = self._find_best_message(conversation.messages)
            message_content = best_message.content if best_message else "Expert insights from our AI discussion"
            
            content = f"""{hook}
            
💬 "{message_content[:120]}..."

✅ {value_prop}
🎯 AI experts discussing {conversation.topic.lower()}
⚡ Real-time insights about our services
📞 {cta}

{hashtag_string}"""
            
        elif post_type == 'summary':
            message_count = len(conversation.messages)
            agent_count = len(set(msg.agent_name for msg in conversation.messages))
            
            content = f"""{hook}

🤖 Latest AI conversation: {conversation.topic}
📊 {message_count} expert messages exchanged
👥 {agent_count} AI specialists discussing our services
⭐ {value_prop}

Key highlights:
🔧 Professional expertise and quality standards
🏠 Customer-focused service delivery
📈 Industry-leading solutions and results

{cta}

{hashtag_string}"""
            
        elif post_type == 'question_engagement':
            content = f"""{hook}

❓ What matters most when choosing a {business.industry.lower()} professional?

Our AI experts just discussed:
🎯 Quality materials and craftsmanship
⚡ Emergency response capabilities  
🏆 Industry certifications and experience
📞 Customer service excellence

✅ {value_prop}

Drop a comment - what's your top priority? 👇

{cta}

{hashtag_string}"""
            
        else:  # Default service showcase
            content = f"""{hook}

🌟 Serving {business.location} with professional excellence!

Why choose {business.name}:
✅ {value_prop}
🏆 Years of proven industry experience
🔧 Quality materials and expert installation
📞 Responsive customer service team

{cta}

{hashtag_string}"""
        
        return content.strip()
    
    def _create_platform_specific_content(self, base_content, platform):
        """Adapt content for specific platform requirements"""
        max_chars = self.SUPPORTED_PLATFORMS[platform]['max_chars']
        
        if platform == 'twitter' and len(base_content) > max_chars:
            # For Twitter, create a shorter version
            lines = base_content.split('\n')
            # Keep hook, one key point, and hashtags
            short_content = []
            short_content.append(lines[0])  # Hook
            
            # Find the most important content line
            for line in lines[1:]:
                if any(emoji in line for emoji in ['✅', '🎯', '⚡', '📞']) and len(' '.join(short_content + [line])) < max_chars - 50:
                    short_content.append(line)
                    break
            
            # Add hashtags (last lines usually)
            hashtag_line = next((line for line in reversed(lines) if line.startswith('#')), '')
            if hashtag_line:
                # Limit hashtags for Twitter
                hashtags = hashtag_line.split()[:5]
                short_content.append(' '.join(hashtags))
            
            return '\n'.join(short_content)
        
        elif platform == 'linkedin':
            # LinkedIn prefers more professional tone
            professional_content = base_content.replace('🔥', '💼').replace('🚀', '📈')
            return professional_content
        
        elif platform == 'instagram':
            # Instagram can use more emojis and visual language
            visual_content = base_content
            # Could add more visual elements here
            return visual_content
        
        return base_content
    
    def _adapt_for_platforms_professional(self, base_content):
        """Create platform-specific adaptations of professional content"""
        adapted = {}
        
        for platform in self.SUPPORTED_PLATFORMS.keys():
            adapted[platform] = self._create_platform_specific_content(base_content, platform)
        
        return adapted
    
    def _find_best_message(self, messages):
        """Find the most engaging message from conversation"""
        if not messages:
            return None
        
        # Prioritize messages that mention key business terms
        business_terms = ['quality', 'professional', 'expert', 'service', 'customer', 'experience']
        
        scored_messages = []
        for message in messages:
            score = 0
            content_lower = message.content.lower()
            
            # Score based on business terms
            for term in business_terms:
                if term in content_lower:
                    score += 1
            
            # Prefer messages of good length (not too short or long)
            if 50 <= len(message.content) <= 200:
                score += 2
            
            # Prefer certain agent types
            if message.agent_type in ['openai', 'anthropic']:
                score += 1
            
            scored_messages.append((score, message))
        
        # Return highest scoring message
        scored_messages.sort(key=lambda x: x[0], reverse=True)
        return scored_messages[0][1] if scored_messages else messages[0]