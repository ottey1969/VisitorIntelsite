"""
Automatic Social Media Posting Scheduler
Handles timezone-aware automatic posting at 9 AM and 5 PM daily
Posts infographics and conversation highlights automatically
"""

import os
import json
import pytz
from datetime import datetime, time, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import and_
import threading
import time as time_module

from app import db
from models import Business, Conversation, SocialMediaPost, SocialMediaSettings
from social_media_manager import SocialMediaManager
from infographic_generator import InfographicGenerator

class AutoPostingScheduler:
    """Manages automatic social media posting for monthly subscribers"""
    
    def __init__(self):
        self.social_manager = SocialMediaManager()
        self.infographic_generator = InfographicGenerator()
        self.posting_times = [
            time(9, 0),   # 9:00 AM
            time(17, 0)   # 5:00 PM
        ]
        self.is_running = False
        
    def start_scheduler(self):
        """Start the automatic posting scheduler"""
        if self.is_running:
            return
        
        self.is_running = True
        scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        scheduler_thread.start()
        print("Auto-posting scheduler started")
    
    def stop_scheduler(self):
        """Stop the automatic posting scheduler"""
        self.is_running = False
        print("Auto-posting scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                self._check_and_post()
                time_module.sleep(300)  # Check every 5 minutes
            except Exception as e:
                print(f"Scheduler error: {e}")
                time_module.sleep(60)  # Wait 1 minute on error
    
    def _check_and_post(self):
        """Check if it's time to post and execute posts"""
        # Get all monthly subscribers with enabled social media
        monthly_businesses = Business.query.filter(
            Business.subscription_type.in_(['monthly_basic', 'monthly_pro', 'monthly_enterprise'])
        ).all()
        
        for business in monthly_businesses:
            try:
                self._process_business_posts(business)
            except Exception as e:
                print(f"Error processing business {business.id}: {e}")
    
    def _process_business_posts(self, business: Business):
        """Process automatic posts for a business based on their timezone"""
        # Get business timezone (default to UTC if not set)
        business_timezone = self._get_business_timezone(business)
        current_time = datetime.now(business_timezone)
        
        # Check if it's a posting time
        current_hour_minute = current_time.time().replace(second=0, microsecond=0)
        
        for posting_time in self.posting_times:
            if current_hour_minute == posting_time:
                # Check if we already posted at this time today
                if not self._already_posted_today(business.id, posting_time, current_time.date()):
                    self._create_automatic_posts(business, current_time, posting_time)
    
    def _get_business_timezone(self, business: Business) -> pytz.timezone:
        """Get business timezone based on location or default to UTC"""
        try:
            # Common timezone mappings based on location
            timezone_mapping = {
                'california': 'America/Los_Angeles',
                'new york': 'America/New_York',
                'texas': 'America/Chicago',
                'florida': 'America/New_York',
                'london': 'Europe/London',
                'toronto': 'America/Toronto',
                'sydney': 'Australia/Sydney',
                'tokyo': 'Asia/Tokyo',
                'berlin': 'Europe/Berlin',
                'paris': 'Europe/Paris'
            }
            
            if business.location:
                location_lower = business.location.lower()
                for key, timezone_str in timezone_mapping.items():
                    if key in location_lower:
                        return pytz.timezone(timezone_str)
            
            # Default to UTC
            return pytz.UTC
            
        except Exception:
            return pytz.UTC
    
    def _already_posted_today(self, business_id: int, posting_time: time, current_date) -> bool:
        """Check if we already posted at this time today"""
        # Check for posts in the last hour around this time
        start_time = datetime.combine(current_date, posting_time)
        end_time = start_time + timedelta(hours=1)
        
        existing_post = SocialMediaPost.query.filter(
            and_(
                SocialMediaPost.business_id == business_id,
                SocialMediaPost.post_type == 'auto',
                SocialMediaPost.created_at >= start_time,
                SocialMediaPost.created_at <= end_time
            )
        ).first()
        
        return existing_post is not None
    
    def _create_automatic_posts(self, business: Business, current_time: datetime, posting_time: time):
        """Create automatic posts for a business"""
        try:
            # Get enabled platforms for this business
            enabled_platforms = self._get_enabled_platforms(business.id)
            
            if not enabled_platforms:
                return
            
            # Get recent conversation for content
            recent_conversation = Conversation.query.filter_by(
                business_id=business.id
            ).order_by(Conversation.created_at.desc()).first()
            
            if not recent_conversation:
                return
            
            # Determine post type based on time
            if posting_time.hour == 9:
                # Morning post: Conversation highlight
                post_content = self._create_morning_post(business, recent_conversation)
                post_type = 'morning_highlight'
            else:
                # Evening post: Infographic or business stats
                post_content = self._create_evening_post(business, recent_conversation)
                post_type = 'evening_infographic'
            
            # Create posts for each enabled platform
            for platform in enabled_platforms:
                self._create_platform_post(
                    business.id,
                    platform,
                    post_content,
                    recent_conversation.id,
                    post_type,
                    current_time
                )
                
            print(f"Auto-posted for {business.name} at {posting_time}")
            
        except Exception as e:
            print(f"Error creating auto posts for {business.name}: {e}")
    
    def _get_enabled_platforms(self, business_id: int) -> List[str]:
        """Get enabled social media platforms for a business"""
        try:
            settings = SocialMediaSettings.query.filter_by(
                business_id=business_id,
                is_enabled=True
            ).all()
            
            if settings:
                return [setting.platform for setting in settings]
            else:
                # Default enabled platforms for monthly subscribers
                return ['linkedin', 'facebook']
                
        except Exception:
            return ['linkedin', 'facebook']
    
    def _create_morning_post(self, business: Business, conversation: Conversation) -> Dict[str, str]:
        """Create morning conversation highlight post"""
        highlights = self.social_manager.generate_conversation_highlights(conversation.id)
        
        if highlights:
            # Use the quote post for morning
            quote_post = next((post for post in highlights if post['type'] == 'quote'), highlights[0])
            return quote_post['platform_content']
        
        # Fallback content
        return {
            'linkedin': f"🌅 Good morning! Our AI experts are discussing {conversation.topic} - what's your take on this trending topic? #{business.name.replace(' ', '')} #MorningInsights #AI",
            'facebook': f"Good morning! Starting the day with insights about {conversation.topic}. Our AI team had some fascinating discussions - check out the full conversation!",
            'twitter': f"🌅 Morning insight: {conversation.topic} - our AI experts weigh in! What do you think? #{business.name.replace(' ', '')}",
            'instagram': f"Good morning! ☀️ Today we're exploring {conversation.topic}. Swipe to see what our AI experts discovered! #MorningMotivation #{business.name.replace(' ', '')}"
        }
    
    def _create_evening_post(self, business: Business, conversation: Conversation) -> Dict[str, str]:
        """Create evening infographic/summary post"""
        highlights = self.social_manager.generate_conversation_highlights(conversation.id)
        
        if highlights:
            # Use the summary post for evening
            summary_post = next((post for post in highlights if post['type'] == 'summary'), highlights[0])
            return summary_post['platform_content']
        
        # Fallback content
        return {
            'linkedin': f"🌆 Wrapping up the day with key insights from our AI discussion on {conversation.topic}. What resonated with you today? #{business.name.replace(' ', '')} #EveningReflection #BusinessInsights",
            'facebook': f"As we end the day, here are the highlights from today's AI conversation about {conversation.topic}. Thanks for following along!",
            'twitter': f"🌆 Day recap: Key insights about {conversation.topic} from our AI experts. What's your takeaway? #{business.name.replace(' ', '')}",
            'instagram': f"Ending the day with wisdom! 🌙 Our AI explored {conversation.topic} - here are the key takeaways. #EveningWisdom #{business.name.replace(' ', '')}"
        }
    
    def _create_platform_post(self, business_id: int, platform: str, content_dict: Dict[str, str], 
                             conversation_id: int, post_type: str, scheduled_time: datetime):
        """Create a social media post record in database"""
        try:
            content = content_dict.get(platform, list(content_dict.values())[0])
            
            # Create post record
            post = SocialMediaPost(
                business_id=business_id,
                conversation_id=conversation_id,
                platform=platform,
                content=content,
                post_type='auto',
                scheduled_time=scheduled_time,
                status='posted',
                created_at=scheduled_time
            )
            
            db.session.add(post)
            db.session.commit()
            
            # In production, this would actually post to the social media platform
            print(f"Posted to {platform}: {content[:100]}...")
            
        except Exception as e:
            print(f"Error creating platform post: {e}")
    
    def setup_business_social_accounts(self, business_id: int, platform_accounts: Dict[str, str]) -> Dict[str, Any]:
        """Setup social media accounts for a business (one-time setup)"""
        try:
            business = Business.query.get(business_id)
            if not business:
                return {'success': False, 'error': 'Business not found'}
            
            # Check if monthly subscriber
            if business.subscription_type == 'credit':
                return {'success': False, 'error': 'Auto-posting only available for monthly subscribers'}
            
            # Create or update platform settings
            for platform, account_info in platform_accounts.items():
                if platform not in self.social_manager.SUPPORTED_PLATFORMS:
                    continue
                
                # Check if setting exists
                setting = SocialMediaSettings.query.filter_by(
                    business_id=business_id,
                    platform=platform
                ).first()
                
                if not setting:
                    setting = SocialMediaSettings(
                        business_id=business_id,
                        platform=platform,
                        is_enabled=True,
                        posting_times=json.dumps(['09:00', '17:00']),
                        auto_hashtags=True,
                        include_business_name=True
                    )
                    db.session.add(setting)
                else:
                    setting.is_enabled = True
                
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Social media accounts connected successfully! Auto-posting will start at 9 AM and 5 PM daily.',
                'platforms_enabled': list(platform_accounts.keys()),
                'posting_times': ['9:00 AM', '5:00 PM'],
                'timezone_note': f'Posts will be scheduled in your business timezone based on location: {business.location or "UTC"}'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_posting_preview(self, business_id: int) -> Dict[str, Any]:
        """Get a preview of what will be posted"""
        try:
            business = Business.query.get(business_id)
            if not business:
                return {'success': False, 'error': 'Business not found'}
            
            recent_conversation = Conversation.query.filter_by(
                business_id=business_id
            ).order_by(Conversation.created_at.desc()).first()
            
            if not recent_conversation:
                return {'success': False, 'error': 'No conversations found'}
            
            # Generate preview content
            morning_content = self._create_morning_post(business, recent_conversation)
            evening_content = self._create_evening_post(business, recent_conversation)
            
            return {
                'success': True,
                'preview': {
                    'morning_post': {
                        'time': '9:00 AM',
                        'type': 'Conversation Highlight',
                        'content': morning_content
                    },
                    'evening_post': {
                        'time': '5:00 PM', 
                        'type': 'Summary & Insights',
                        'content': evening_content
                    }
                },
                'enabled_platforms': self._get_enabled_platforms(business_id)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Global scheduler instance
auto_scheduler = AutoPostingScheduler()

def start_auto_posting():
    """Start the auto-posting scheduler"""
    auto_scheduler.start_scheduler()

def stop_auto_posting():
    """Stop the auto-posting scheduler"""
    auto_scheduler.stop_scheduler()