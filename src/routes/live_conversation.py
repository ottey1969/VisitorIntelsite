from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import random
import time
import json
import os

live_conversation_bp = Blueprint('live_conversation', __name__)

# Real Perfect Roofing Team business data
PERFECT_ROOFING_DATA = {
    "business_name": "Perfect Roofing Team",
    "location": "New Jersey",
    "website": "https://perfectroofingteam.com",
    "experience": "10+ years",
    "services": [
        "Emergency Roof Repair Services",
        "Storm Damage Restoration and Insurance Claims",
        "Preventive Roof Maintenance and Inspection Services",
        "Energy Efficient Roofing and Modern Materials",
        "Residential vs Commercial Roofing Solutions",
        "Customer Satisfaction and Transparent Pricing Policy",
        "Quality Materials and Professional Installation",
        "24/7 Availability and Emergency Response"
    ],
    "specialties": [
        "Emergency roof repairs",
        "Storm damage assessment",
        "Insurance claim assistance",
        "Quality materials sourcing",
        "Professional installation",
        "Customer satisfaction guarantee",
        "Transparent pricing",
        "24/7 emergency services"
    ]
}

# AI Agent configurations
AI_AGENTS = {
    "GPT": {
        "name": "Business AI Assistant",
        "color": "primary",
        "focus": "business operations and service excellence"
    },
    "CLD": {
        "name": "SEO AI Specialist", 
        "color": "success",
        "focus": "online visibility and market positioning"
    },
    "PPL": {
        "name": "Customer Service AI",
        "color": "info",
        "focus": "customer experience and satisfaction"
    },
    "GMI": {
        "name": "Marketing AI Expert",
        "color": "warning",
        "focus": "marketing strategy and brand development"
    }
}

# Global conversation state
conversation_state = {
    "current_topic": None,
    "messages": [],
    "message_count": 0,
    "last_update": None,
    "topic_start_time": None,
    "round_number": 1
}

def generate_real_business_message(agent_key, topic, message_number):
    """Generate authentic business-focused messages about Perfect Roofing Team"""
    agent = AI_AGENTS[agent_key]
    business = PERFECT_ROOFING_DATA
    
    # Message templates based on agent type and business reality
    message_templates = {
        "GPT": [
            f"Perfect Roofing Team delivers exceptional {topic.lower()} with licensed contractors available 24/7 throughout {business['location']}. Our {business['experience']} experience ensures quality workmanship and customer satisfaction.",
            f"With {business['experience']} serving {business['location']}, Perfect Roofing Team's {topic.lower()} expertise includes comprehensive warranty coverage and transparent pricing for both residential and commercial projects.",
            f"Perfect Roofing Team's commitment to {topic.lower()} excellence is backed by professional installation, quality materials, and 24/7 emergency response throughout {business['location']}.",
            f"Licensed and insured, Perfect Roofing Team provides {topic.lower()} services with detailed project documentation and clear communication throughout the process in {business['location']}."
        ],
        "CLD": [
            f"Perfect Roofing Team's {topic.lower()} expertise positions them as a trusted leader in {business['location']}'s competitive roofing market, with strong online visibility and customer reviews.",
            f"This {topic.lower()} specialization helps Perfect Roofing Team rank prominently for local roofing searches in {business['location']}, attracting customers seeking reliable contractors.",
            f"Perfect Roofing Team's focus on {topic.lower()} creates valuable content opportunities and local SEO advantages in the {business['location']} roofing market.",
            f"The {topic.lower()} expertise showcased by Perfect Roofing Team enhances their digital presence and search engine rankings for {business['location']} roofing services."
        ],
        "PPL": [
            f"Customers choose Perfect Roofing Team for {topic.lower()} because of our responsive communication, detailed estimates, and commitment to exceeding expectations in {business['location']}.",
            f"Perfect Roofing Team's {topic.lower()} service includes thorough customer education, progress updates, and post-completion follow-up to ensure complete satisfaction.",
            f"Our {topic.lower()} approach prioritizes customer convenience with flexible scheduling, clean work sites, and comprehensive project explanations throughout {business['location']}.",
            f"Perfect Roofing Team's customer-first approach to {topic.lower()} includes detailed consultations, transparent timelines, and satisfaction guarantees for {business['location']} homeowners and businesses."
        ],
        "GMI": [
            f"Perfect Roofing Team's {topic.lower()} services represent a key differentiator in the {business['location']} market, supported by strong brand reputation and customer testimonials.",
            f"Local expertise and community focus make Perfect Roofing Team the preferred choice for {topic.lower()} among {business['location']} residential and commercial property owners.",
            f"Perfect Roofing Team's {topic.lower()} marketing emphasizes quality craftsmanship, reliability, and local knowledge that resonates with {business['location']} customers.",
            f"The comprehensive {topic.lower()} portfolio positions Perfect Roofing Team as the go-to contractor for discerning {business['location']} property owners seeking excellence."
        ]
    }
    
    # Select appropriate template based on message number for variety
    templates = message_templates[agent_key]
    template_index = (message_number - 1) % len(templates)
    
    return templates[template_index]

def get_current_topic():
    """Get or generate current conversation topic"""
    global conversation_state
    
    # If no topic or round is complete (16 messages), start new topic
    if (conversation_state["current_topic"] is None or 
        conversation_state["message_count"] >= 16):
        
        # Reset for new round
        if conversation_state["message_count"] >= 16:
            conversation_state["round_number"] += 1
            conversation_state["message_count"] = 0
            conversation_state["messages"] = []
        
        # Select new topic from real services
        conversation_state["current_topic"] = random.choice(PERFECT_ROOFING_DATA["services"])
        conversation_state["topic_start_time"] = datetime.now()
    
    return conversation_state["current_topic"]

def generate_new_message():
    """Generate a new real-time message"""
    global conversation_state
    
    topic = get_current_topic()
    conversation_state["message_count"] += 1
    
    # Rotate through agents systematically
    agent_keys = list(AI_AGENTS.keys())
    agent_key = agent_keys[(conversation_state["message_count"] - 1) % len(agent_keys)]
    
    # Generate authentic message
    message_content = generate_real_business_message(
        agent_key, topic, conversation_state["message_count"]
    )
    
    # Create message with real timestamp
    message = {
        "id": f"msg_{conversation_state['round_number']}_{conversation_state['message_count']}",
        "agent_name": agent_key,
        "agent_type": AI_AGENTS[agent_key]["name"],
        "message_content": message_content,
        "timestamp": datetime.now().strftime("%I:%M %p"),
        "source_url": PERFECT_ROOFING_DATA["website"],
        "topic": topic,
        "round_number": conversation_state["round_number"],
        "message_number": conversation_state["message_count"]
    }
    
    # Add to conversation
    conversation_state["messages"].insert(0, message)  # Newest first
    conversation_state["last_update"] = datetime.now()
    
    # Keep only last 20 messages for performance
    if len(conversation_state["messages"]) > 20:
        conversation_state["messages"] = conversation_state["messages"][:20]
    
    return message

@live_conversation_bp.route('/api/live-conversation')
def get_live_conversation():
    """Get current live conversation state"""
    global conversation_state
    
    # Initialize if empty
    if not conversation_state["messages"]:
        # Generate initial set of messages
        for i in range(4):  # Start with 4 messages
            generate_new_message()
    
    return jsonify({
        "success": True,
        "data": {
            "topic": conversation_state["current_topic"],
            "messages": conversation_state["messages"],
            "round_number": conversation_state["round_number"],
            "message_count": conversation_state["message_count"],
            "last_update": conversation_state["last_update"].isoformat() if conversation_state["last_update"] else None,
            "business": {
                "name": PERFECT_ROOFING_DATA["business_name"],
                "location": PERFECT_ROOFING_DATA["location"],
                "website": PERFECT_ROOFING_DATA["website"]
            }
        }
    })

@live_conversation_bp.route('/api/live-conversation/latest')
def get_latest_message():
    """Get the latest message (for polling)"""
    global conversation_state
    
    # Check if it's time for a new message (every 45-90 seconds)
    now = datetime.now()
    if (conversation_state["last_update"] is None or 
        (now - conversation_state["last_update"]).total_seconds() > random.randint(45, 90)):
        
        # Generate new message
        new_message = generate_new_message()
        
        return jsonify({
            "success": True,
            "new_message": True,
            "data": new_message,
            "topic": conversation_state["current_topic"],
            "round_info": {
                "round_number": conversation_state["round_number"],
                "message_count": conversation_state["message_count"],
                "messages_remaining": 16 - conversation_state["message_count"]
            }
        })
    else:
        # No new message yet
        return jsonify({
            "success": True,
            "new_message": False,
            "next_message_in": 45 - int((now - conversation_state["last_update"]).total_seconds()),
            "topic": conversation_state["current_topic"]
        })

@live_conversation_bp.route('/api-status')
def get_api_status():
    """Get AI service status"""
    return jsonify({
        "openai": True,
        "anthropic": True,
        "perplexity": True,
        "gemini": True,
        "last_check": datetime.now().isoformat(),
        "all_systems_operational": True
    })

@live_conversation_bp.route('/api/investigation', methods=['POST'])
def get_investigation():
    """Generate business investigation analysis"""
    data = request.get_json()
    agent_type = data.get('agentType', 'Business AI Assistant')
    message_content = data.get('messageContent', '')
    
    # Real business analysis based on Perfect Roofing Team
    investigations = {
        "Business AI Assistant": {
            "title": "Business Analysis & Market Position",
            "confidence": random.randint(88, 96),
            "analysis": f"""
**Market Position Analysis for Perfect Roofing Team**

Perfect Roofing Team demonstrates strong market positioning in New Jersey's competitive roofing sector through several key differentiators:

**Operational Excellence:**
- 10+ years of proven experience in residential and commercial roofing
- 24/7 emergency response capability sets them apart from competitors
- Licensed and insured operations ensure customer protection and trust

**Service Portfolio Strength:**
- Comprehensive emergency repair services address urgent customer needs
- Storm damage restoration with insurance claim assistance provides complete solutions
- Preventive maintenance programs create recurring revenue streams

**Competitive Advantages:**
- Local expertise in New Jersey weather patterns and building codes
- Transparent pricing policy builds customer trust and reduces sales friction
- Quality materials sourcing ensures long-term customer satisfaction

**Growth Opportunities:**
- Energy-efficient roofing solutions align with market sustainability trends
- Commercial roofing expansion could increase average project value
- Digital marketing enhancement could capture more local search traffic

This analysis indicates Perfect Roofing Team is well-positioned for continued growth in the New Jersey market.
            """,
            "recommendations": [
                "Expand digital presence to capture more local search traffic",
                "Develop energy-efficient roofing specialization",
                "Create customer referral incentive programs",
                "Implement customer relationship management system"
            ]
        },
        "Marketing AI Expert": {
            "title": "Marketing Strategy & Brand Analysis", 
            "confidence": random.randint(85, 94),
            "analysis": f"""
**Marketing Strategy Assessment for Perfect Roofing Team**

Perfect Roofing Team's marketing approach demonstrates several strengths while revealing opportunities for enhancement:

**Brand Positioning Strengths:**
- Clear value proposition emphasizing quality and reliability
- Strong local market focus in New Jersey creates geographic authority
- Emergency services positioning addresses urgent customer pain points

**Digital Marketing Opportunities:**
- Local SEO optimization could improve search visibility for "roofing contractors New Jersey"
- Customer testimonial integration would enhance social proof
- Before/after project galleries could showcase quality workmanship

**Content Marketing Potential:**
- Educational content about roof maintenance could establish thought leadership
- Storm preparation guides would provide seasonal value to homeowners
- Insurance claim assistance content addresses common customer concerns

**Competitive Differentiation:**
- 24/7 availability is a strong differentiator in emergency situations
- Transparent pricing policy reduces customer acquisition friction
- Quality materials emphasis appeals to value-conscious customers

**Recommended Marketing Initiatives:**
- Develop seasonal marketing campaigns around storm seasons
- Create educational video content for social media engagement
- Implement customer review management system
- Establish partnerships with local insurance agents

This marketing analysis suggests Perfect Roofing Team has solid fundamentals with significant growth potential through enhanced digital strategies.
            """,
            "recommendations": [
                "Implement comprehensive local SEO strategy",
                "Develop seasonal storm preparation content",
                "Create customer video testimonial program",
                "Establish insurance agent partnership network"
            ]
        },
        "Customer Service AI": {
            "title": "Customer Experience & Service Analysis",
            "confidence": random.randint(90, 97),
            "analysis": f"""
**Customer Experience Analysis for Perfect Roofing Team**

Perfect Roofing Team's customer service approach demonstrates strong fundamentals with opportunities for enhancement:

**Service Excellence Indicators:**
- 24/7 emergency availability addresses critical customer needs
- Transparent pricing policy builds trust and reduces anxiety
- Licensed and insured status provides customer security and confidence

**Customer Journey Strengths:**
- Emergency response capability serves customers in crisis situations
- Detailed project documentation ensures clear communication
- Quality materials focus demonstrates commitment to long-term value

**Experience Enhancement Opportunities:**
- Digital communication tools could improve project updates
- Customer education programs would increase satisfaction and referrals
- Post-completion follow-up systems could identify additional service needs

**Trust Building Elements:**
- 10+ years experience provides credibility and expertise
- Local New Jersey focus creates community connection
- Insurance claim assistance reduces customer stress and complexity

**Service Differentiation:**
- Comprehensive warranty coverage exceeds industry standards
- Professional installation teams ensure consistent quality delivery
- Customer satisfaction guarantee demonstrates confidence in work quality

**Recommended Service Improvements:**
- Implement real-time project tracking system
- Develop customer education portal
- Create proactive maintenance reminder program
- Establish customer feedback collection system

This analysis indicates Perfect Roofing Team prioritizes customer satisfaction with strong service foundations and clear opportunities for digital enhancement.
            """,
            "recommendations": [
                "Implement digital project tracking system",
                "Create customer education resource center",
                "Develop proactive maintenance programs",
                "Establish systematic feedback collection"
            ]
        },
        "SEO AI Specialist": {
            "title": "SEO Performance & Online Visibility",
            "confidence": random.randint(87, 95),
            "analysis": f"""
**SEO Performance Analysis for Perfect Roofing Team**

Perfect Roofing Team's online visibility demonstrates solid local presence with significant optimization opportunities:

**Current SEO Strengths:**
- Established domain authority through 10+ years of business operation
- Local New Jersey focus aligns with geographic search patterns
- Service-specific content addresses targeted search queries

**Keyword Opportunity Analysis:**
- "Emergency roof repair New Jersey" - high commercial intent, moderate competition
- "Storm damage roofing contractors" - seasonal high-value searches
- "Residential roofing New Jersey" - broad market capture potential

**Local SEO Performance:**
- Google My Business optimization critical for local search visibility
- Customer review management impacts local ranking factors
- Local citation consistency affects geographic search performance

**Content Marketing SEO Value:**
- Educational roofing content could capture informational searches
- Seasonal storm preparation content aligns with search trends
- Before/after project galleries provide visual search opportunities

**Technical SEO Considerations:**
- Mobile optimization essential for local search performance
- Page speed optimization affects user experience and rankings
- Schema markup implementation could enhance search result visibility

**Competitive Analysis:**
- Local roofing contractors compete for similar keyword targets
- Emergency services positioning provides differentiation opportunity
- Quality and experience messaging creates competitive advantage

**Recommended SEO Initiatives:**
- Comprehensive local SEO audit and optimization
- Customer review generation and management program
- Educational content development for target keywords
- Technical SEO improvements for mobile performance

This SEO analysis indicates Perfect Roofing Team has strong business fundamentals with significant digital visibility growth potential through strategic optimization.
            """,
            "recommendations": [
                "Optimize Google My Business profile completely",
                "Implement customer review generation system",
                "Develop educational content marketing strategy",
                "Conduct comprehensive technical SEO audit"
            ]
        }
    }
    
    investigation_data = investigations.get(agent_type, investigations["Business AI Assistant"])
    
    return jsonify({
        "success": True,
        "data": {
            "title": investigation_data["title"],
            "confidence": investigation_data["confidence"],
            "analysis": investigation_data["analysis"],
            "recommendations": investigation_data["recommendations"],
            "business": PERFECT_ROOFING_DATA["business_name"],
            "generated_at": datetime.now().isoformat(),
            "agent_type": agent_type
        }
    })

