"""
Conversation Intelligence System
Tracks conversation history and suggests new, non-repetitive topics
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Set
from collections import Counter
from models import Business, Conversation, ConversationMessage
from app import db


class ConversationIntelligence:
    """Analyzes conversation history and suggests fresh topics"""
    
    def __init__(self):
        pass
    
    def analyze_business_conversations(self, business_id: int) -> Dict[str, any]:
        """Analyze all conversations for a business to understand patterns"""
        conversations = Conversation.query.filter_by(business_id=business_id).all()
        
        if not conversations:
            return {
                'total_conversations': 0,
                'topics_covered': [],
                'common_themes': [],
                'suggested_topics': self._get_fresh_topics_for_business(business_id),
                'conversation_frequency': {},
                'topic_diversity_score': 0
            }
        
        # Extract topics and themes
        topics_covered = [conv.topic for conv in conversations]
        all_messages = []
        
        for conv in conversations:
            all_messages.extend([msg.content for msg in conv.messages])
        
        # Analyze content patterns
        common_themes = self._extract_themes(all_messages)
        topic_keywords = self._extract_keywords_from_topics(topics_covered)
        
        # Calculate conversation frequency by time periods
        frequency = self._calculate_conversation_frequency(conversations)
        
        # Calculate topic diversity score (0-100)
        diversity_score = self._calculate_topic_diversity(topics_covered)
        
        # Generate fresh topic suggestions
        suggested_topics = self._generate_fresh_topics(business_id, topic_keywords, common_themes)
        
        return {
            'total_conversations': len(conversations),
            'topics_covered': topics_covered,
            'common_themes': common_themes,
            'suggested_topics': suggested_topics,
            'conversation_frequency': frequency,
            'topic_diversity_score': diversity_score
        }
    
    def _extract_themes(self, messages: List[str]) -> List[str]:
        """Extract common themes from conversation messages"""
        if not messages:
            return []
        
        # Combine all messages
        text = ' '.join(messages).lower()
        
        # Common business themes to look for
        theme_patterns = {
            'customer_service': ['customer', 'service', 'support', 'help', 'satisfaction'],
            'pricing': ['price', 'cost', 'pricing', 'rate', 'fee', 'expensive', 'affordable'],
            'quality': ['quality', 'excellence', 'professional', 'expert', 'skilled'],
            'technology': ['technology', 'digital', 'online', 'software', 'app', 'website'],
            'local_service': ['local', 'area', 'neighborhood', 'community', 'nearby'],
            'experience': ['experience', 'years', 'established', 'trusted', 'proven'],
            'materials': ['materials', 'products', 'supplies', 'equipment', 'tools'],
            'safety': ['safety', 'insurance', 'licensed', 'certified', 'secure'],
            'timeline': ['time', 'schedule', 'deadline', 'urgent', 'fast', 'quick'],
            'warranty': ['warranty', 'guarantee', 'protection', 'coverage']
        }
        
        themes_found = []
        for theme, keywords in theme_patterns.items():
            if any(keyword in text for keyword in keywords):
                themes_found.append(theme.replace('_', ' ').title())
        
        return themes_found[:5]  # Return top 5 themes
    
    def _extract_keywords_from_topics(self, topics: List[str]) -> Set[str]:
        """Extract keywords from conversation topics"""
        keywords = set()
        
        for topic in topics:
            # Clean and split topic into words
            words = re.findall(r'\w+', topic.lower())
            # Filter out common words
            common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
            topic_keywords = [word for word in words if word not in common_words and len(word) > 2]
            keywords.update(topic_keywords)
        
        return keywords
    
    def _calculate_conversation_frequency(self, conversations: List[Conversation]) -> Dict[str, int]:
        """Calculate how often conversations happen by time period"""
        if not conversations:
            return {}
        
        now = datetime.utcnow()
        frequency = {
            'last_7_days': 0,
            'last_30_days': 0,
            'last_90_days': 0
        }
        
        for conv in conversations:
            days_ago = (now - conv.created_at).days
            
            if days_ago <= 7:
                frequency['last_7_days'] += 1
            if days_ago <= 30:
                frequency['last_30_days'] += 1
            if days_ago <= 90:
                frequency['last_90_days'] += 1
        
        return frequency
    
    def _calculate_topic_diversity(self, topics: List[str]) -> int:
        """Calculate topic diversity score (0-100)"""
        if not topics:
            return 0
        
        # Count unique words across all topics
        all_words = []
        for topic in topics:
            words = re.findall(r'\w+', topic.lower())
            all_words.extend(words)
        
        if not all_words:
            return 0
        
        # Calculate uniqueness ratio
        unique_words = len(set(all_words))
        total_words = len(all_words)
        
        diversity_ratio = unique_words / total_words
        return min(100, int(diversity_ratio * 100))
    
    def _generate_fresh_topics(self, business_id: int, used_keywords: Set[str], themes: List[str]) -> List[str]:
        """Generate fresh topic suggestions avoiding repetition"""
        business = Business.query.get(business_id)
        if not business:
            return []
        
        # Base topic templates for different industries
        industry_topics = {
            'roofing': [
                "Emergency roof repair response times during severe weather",
                "Solar panel installation compatibility with different roof types",
                "Energy efficiency improvements through modern roofing materials",
                "Storm damage assessment and insurance claim assistance",
                "Preventive maintenance schedules for commercial properties",
                "Green roofing solutions for environmental sustainability",
                "Winter preparation and ice dam prevention strategies",
                "Cost comparison: repair vs full roof replacement",
                "Smart home integration with roofing monitoring systems",
                "Historical building roof restoration techniques"
            ],
            'construction': [
                "Sustainable building practices and green certifications",
                "Smart home technology integration in new construction",
                "Project timeline management and milestone tracking",
                "Material supply chain challenges and solutions",
                "Safety protocols and worker protection measures",
                "Building code compliance and permit processes",
                "Cost estimation accuracy and budget management",
                "Custom design vs modular construction approaches",
                "Weather-related construction delays and mitigation",
                "Quality control inspection procedures"
            ],
            'healthcare': [
                "Telemedicine adoption and patient experience",
                "Preventive care vs treatment cost comparisons",
                "Patient data privacy and security measures",
                "Emergency response procedures and protocols",
                "Staff training and certification requirements",
                "Technology upgrades and equipment modernization",
                "Patient satisfaction measurement and improvement",
                "Insurance coverage and billing transparency",
                "Community health outreach programs",
                "Specialized treatment options and referral networks"
            ]
        }
        
        # Get industry-specific topics
        industry = business.industry.lower() if business.industry else 'general'
        base_topics = industry_topics.get(industry, industry_topics['construction'])
        
        # Filter out topics that might be too similar to existing ones
        fresh_topics = []
        for topic in base_topics:
            topic_words = set(re.findall(r'\w+', topic.lower()))
            # Check if topic has significant overlap with used keywords
            overlap = len(topic_words.intersection(used_keywords))
            if overlap < 3:  # Allow some overlap but not too much
                fresh_topics.append(topic)
        
        # Add business-specific customizations
        business_name = business.name.split()[0]  # First word of business name
        customized_topics = []
        
        for topic in fresh_topics[:5]:
            # Sometimes customize with business name
            if len(customized_topics) < 2:
                customized_topic = f"{business_name}'s approach to {topic.lower()}"
                customized_topics.append(customized_topic)
            else:
                customized_topics.append(topic)
        
        return customized_topics
    
    def _get_fresh_topics_for_business(self, business_id: int) -> List[str]:
        """Get fresh topics for a business with no conversation history"""
        business = Business.query.get(business_id)
        if not business:
            return []
        
        # Default fresh topics for new businesses
        return [
            f"Why choose {business.name} for your next project",
            f"Service area coverage and response times",
            f"Quality assurance and customer satisfaction guarantee",
            f"Pricing transparency and free consultation process",
            f"Technology and innovation in modern service delivery"
        ]
    
    def get_smart_topic_suggestion(self, business_id: int) -> str:
        """Get one smart topic suggestion based on conversation history"""
        analysis = self.analyze_business_conversations(business_id)
        
        if analysis['suggested_topics']:
            return analysis['suggested_topics'][0]
        
        # Fallback for businesses with no history
        business = Business.query.get(business_id)
        if business:
            return f"What makes {business.name} different from competitors in {business.location or 'the area'}"
        
        return "Industry expertise and professional service quality"
    
    def should_generate_conversation(self, business_id: int) -> bool:
        """Determine if it's a good time to generate a new conversation"""
        analysis = self.analyze_business_conversations(business_id)
        
        # For unlimited businesses, check frequency to avoid spam
        business = Business.query.get(business_id)
        if business and business.is_unlimited:
            recent_conversations = analysis['conversation_frequency'].get('last_7_days', 0)
            # Limit to 2 conversations per day for unlimited accounts
            if recent_conversations > 14:  # 2 per day * 7 days
                return False
        
        # Always allow if diversity score is high (good variety)
        if analysis['topic_diversity_score'] > 70:
            return True
        
        # Allow if no recent conversations
        if analysis['conversation_frequency'].get('last_7_days', 0) == 0:
            return True
        
        return True  # Default to allowing conversations