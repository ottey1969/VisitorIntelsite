"""
Enterprise Content Ecosystem Generator
Generates complete SEO content systems for Enterprise businesses including:
- FAQ pages
- Local SEO pages  
- Voice search optimization
- Knowledge base articles
"""

import os
import re
from typing import Dict, List, Tuple
from openai import OpenAI
from anthropic import Anthropic

class ContentEcosystemManager:
    """Generates complete content ecosystems for Enterprise businesses"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self.anthropic_client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        
    def generate_business_ecosystem(self, business) -> Dict[str, List[Dict]]:
        """Generate complete content ecosystem for a business"""
        industry = business.industry or "service business"
        location = business.location or "local area"
        
        ecosystem = {
            'faq_pages': self._generate_faq_pages(business, industry),
            'local_pages': self._generate_local_pages(business, location),
            'voice_search': self._generate_voice_search_content(business, industry),
            'knowledge_base': self._generate_knowledge_base(business, industry)
        }
        
        return ecosystem
    
    def _generate_faq_pages(self, business, industry: str) -> List[Dict]:
        """Generate FAQ pages targeting search queries"""
        
        # Industry-specific FAQ topics
        industry_faqs = {
            'roofing': [
                'How much does roof replacement cost',
                'What are signs of roof damage',
                'How long does roof installation take',
                'What roofing materials are best',
                'When should I replace my roof',
                'Do you provide emergency roof repair',
                'What does roof inspection include',
                'How to choose roofing contractor'
            ],
            'law': [
                'How much does a lawyer cost',
                'What should I do after car accident',
                'How long does personal injury case take',
                'What is my case worth',
                'Do I need a lawyer for insurance claim',
                'What documents do I need',
                'How to find best lawyer near me',
                'What happens during consultation'
            ],
            'medical': [
                'What insurance do you accept',
                'How to schedule appointment',
                'What to expect during visit',
                'How to prepare for procedure',
                'What are payment options',
                'Do you offer emergency services',
                'How long is recovery time',
                'What are side effects'
            ],
            'home services': [
                'How much does service cost',
                'Do you provide emergency service',
                'What areas do you serve',
                'How quickly can you respond',
                'Do you offer warranties',
                'What payment methods accepted',
                'Are you licensed and insured',
                'How to schedule service'
            ]
        }
        
        # Get relevant FAQ topics
        topics = industry_faqs.get(industry.lower(), industry_faqs['home services'])
        
        faq_pages = []
        for topic in topics:
            faq_content = self._generate_faq_content(business, topic)
            faq_pages.append({
                'title': topic,
                'slug': self._create_slug(topic),
                'content': faq_content,
                'meta_description': f"{topic} - Expert answers from {business.name}",
                'keywords': self._extract_keywords(topic)
            })
            
        return faq_pages
    
    def _generate_local_pages(self, business, location: str) -> List[Dict]:
        """Generate location-specific SEO pages"""
        
        # Extract cities/areas from location
        base_cities = self._extract_cities_from_location(location)
        
        local_pages = []
        for city in base_cities:
            local_content = self._generate_local_content(business, city)
            local_pages.append({
                'title': f"{business.name} Services in {city}",
                'slug': self._create_slug(city),
                'content': local_content,
                'meta_description': f"Professional {business.industry} services in {city}. Contact {business.name} for expert solutions.",
                'keywords': [city.lower(), business.industry, 'near me', 'local']
            })
            
        return local_pages
    
    def _generate_voice_search_content(self, business, industry: str) -> List[Dict]:
        """Generate voice search optimized content"""
        
        voice_queries = [
            f"Hey Google, what's the best {industry} company near me",
            f"Alexa, find {industry} services in my area", 
            f"Who does {industry} work near me",
            f"What does {industry} service cost",
            f"How to contact {industry} company"
        ]
        
        voice_pages = []
        for query in voice_queries:
            voice_content = self._generate_voice_optimized_content(business, query)
            voice_pages.append({
                'title': f"Voice Search: {query}",
                'slug': self._create_slug(query),
                'content': voice_content,
                'meta_description': f"Voice search optimized answers about {business.name}",
                'keywords': ['voice search', 'near me', business.industry]
            })
            
        return voice_pages
    
    def _generate_knowledge_base(self, business, industry: str) -> List[Dict]:
        """Generate industry expertise knowledge base"""
        
        # Industry-specific knowledge topics
        knowledge_topics = {
            'roofing': [
                'Types of Roofing Materials Guide',
                'Storm Damage Assessment Process',
                'Roof Maintenance Best Practices',
                'Emergency Repair Procedures',
                'Insurance Claims Process'
            ],
            'law': [
                'Personal Injury Law Guide',
                'Insurance Claim Process',
                'Legal Rights After Accident',
                'Court Procedures Explained',
                'Settlement Negotiations'
            ],
            'medical': [
                'Treatment Options Overview',
                'Insurance Coverage Guide',
                'Preparation Instructions',
                'Recovery Guidelines',
                'Follow-up Care'
            ]
        }
        
        topics = knowledge_topics.get(industry.lower(), [
            f'{industry.title()} Best Practices',
            f'{industry.title()} Process Overview',
            f'{industry.title()} Quality Standards'
        ])
        
        knowledge_pages = []
        for topic in topics:
            knowledge_content = self._generate_knowledge_content(business, topic)
            knowledge_pages.append({
                'title': topic,
                'slug': self._create_slug(topic),
                'content': knowledge_content,
                'meta_description': f"Expert guide: {topic} from {business.name}",
                'keywords': self._extract_keywords(topic) + [business.industry]
            })
            
        return knowledge_pages
    
    def _generate_faq_content(self, business, question: str) -> str:
        """Generate FAQ content using AI (simplified for immediate response)"""
        
        # For demo purposes, return immediate content with business-specific details
        content = f"""
        <h3>{question}?</h3>
        <p>Yes, {business.name} provides comprehensive {business.industry.lower()} services with professional expertise and customer satisfaction as our top priorities.</p>
        
        <h4>Our Service Details:</h4>
        <ul>
            <li>Professional {business.industry.lower()} solutions</li>
            <li>Experienced team serving {business.location or 'the local area'}</li>
            <li>Quality workmanship and materials</li>
            <li>Customer satisfaction guarantee</li>
        </ul>
        
        <p>At {business.name}, we understand the importance of reliable service. Our skilled professionals are ready to help with all your {business.industry.lower()} needs.</p>
        
        <div class="alert alert-info">
            <h5>Ready to get started?</h5>
            <p>Contact {business.name} today for professional {business.industry.lower()} services. Visit <a href="{business.website}" target="_blank">{business.website}</a> or call us to schedule a consultation.</p>
        </div>
        """
        
        return content
    
    def _generate_local_content(self, business, city: str) -> str:
        """Generate location-specific content"""
        content = f"""
        <h3>{business.name} Services in {city}</h3>
        <p>{business.name} proudly serves the {city} community with professional {business.industry.lower()} services. Our local expertise and commitment to quality make us the preferred choice for residents and businesses in {city}.</p>
        
        <h4>Why Choose {business.name} in {city}?</h4>
        <ul>
            <li>Local {city} expertise and knowledge</li>
            <li>Rapid response times for {city} customers</li>
            <li>Licensed and insured {business.industry.lower()} professionals</li>
            <li>Community-focused service approach</li>
            <li>Comprehensive {business.industry.lower()} solutions</li>
        </ul>
        
        <p>Our team understands the unique needs of {city} properties and provides tailored {business.industry.lower()} solutions that meet local standards and requirements.</p>
        
        <div class="alert alert-success">
            <h5>Serving {city} and Surrounding Areas</h5>
            <p>Contact {business.name} today for reliable {business.industry.lower()} services in {city}. We're your trusted local partner for all {business.industry.lower()} needs.</p>
            <p><strong>Call now or visit <a href="{business.website}" target="_blank">{business.website}</a> to get started!</strong></p>
        </div>
        """
        return content
    
    def _generate_voice_optimized_content(self, business, query: str) -> str:
        """Generate voice search optimized content"""
        content = f"""
        <h3>Voice Search: {query}</h3>
        <div class="voice-answer">
            <p><strong>The answer is {business.name}!</strong></p>
            
            <p>When you ask "{query.lower()}", {business.name} is your best choice for {business.industry.lower()} services in {business.location or 'the local area'}.</p>
            
            <h4>Why {business.name}?</h4>
            <ul>
                <li>Professional {business.industry.lower()} expertise</li>
                <li>Serving {business.location or 'local communities'} with pride</li>
                <li>Quality workmanship and customer satisfaction</li>
                <li>Licensed and experienced team</li>
            </ul>
            
            <p>You can contact {business.name} easily by visiting <a href="{business.website}" target="_blank">{business.website}</a> or calling for immediate assistance.</p>
            
            <div class="voice-cta alert alert-primary">
                <p><strong>Voice Search Tip:</strong> Next time, just say "Call {business.name}" to connect directly with our team!</p>
            </div>
        </div>
        """
        return content
    
    def _generate_knowledge_content(self, business, topic: str) -> str:
        """Generate knowledge base content"""
        content = f"""
        <h3>{topic}</h3>
        <p class="lead">Expert insights from {business.name} - your trusted {business.industry.lower()} professionals.</p>
        
        <h4>Professional Overview</h4>
        <p>At {business.name}, we've helped countless customers understand the importance of {topic.lower()}. Our experience in the {business.industry.lower()} industry has shown us the key factors that matter most to our clients.</p>
        
        <h4>Key Considerations</h4>
        <ul>
            <li><strong>Quality:</strong> Always prioritize quality materials and workmanship</li>
            <li><strong>Experience:</strong> Work with experienced professionals like {business.name}</li>
            <li><strong>Local Knowledge:</strong> Choose providers familiar with {business.location or 'local'} requirements</li>
            <li><strong>Customer Service:</strong> Ensure clear communication throughout the process</li>
            <li><strong>Value:</strong> Balance cost with long-term benefits</li>
        </ul>
        
        <h4>Best Practices</h4>
        <p>Based on our experience at {business.name}, we recommend:</p>
        <ol>
            <li>Research and planning before starting any project</li>
            <li>Obtaining proper permits and following local regulations</li>
            <li>Using quality materials appropriate for your specific needs</li>
            <li>Regular maintenance to ensure longevity</li>
            <li>Working with licensed and insured professionals</li>
        </ol>
        
        <div class="alert alert-info">
            <h5>Expert Consultation Available</h5>
            <p>Need personalized advice about {topic.lower()}? The experts at {business.name} are here to help. Contact us at <a href="{business.website}" target="_blank">{business.website}</a> for professional guidance tailored to your specific needs.</p>
        </div>
        """
        return content
    
    def _extract_cities_from_location(self, location: str) -> List[str]:
        """Extract cities from location string"""
        if not location:
            return ['Local Area']
            
        # Common patterns for extracting cities
        cities = []
        
        # If location contains state, extract cities
        if 'NJ' in location or 'New Jersey' in location:
            cities = ['Newark', 'Jersey City', 'Paterson', 'Elizabeth', 'Edison']
        elif 'NY' in location or 'New York' in location:
            cities = ['Brooklyn', 'Queens', 'Manhattan', 'Bronx', 'Staten Island']
        elif 'PA' in location or 'Pennsylvania' in location:
            cities = ['Philadelphia', 'Pittsburgh', 'Allentown', 'Erie', 'Reading']
        else:
            # Extract city name from location
            city_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', location)
            if city_match:
                cities = [city_match.group(1)]
            else:
                cities = ['Local Area']
                
        return cities[:5]  # Limit to 5 cities
    
    def _create_slug(self, text: str) -> str:
        """Create URL-friendly slug"""
        slug = text.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_-]+', '-', slug)
        return slug.strip('-')
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'how', 'what', 'when', 'where', 'why', 'which', 'who'}
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords[:5]  # Return top 5 keywords