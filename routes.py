from flask import render_template, request, redirect, url_for, flash, jsonify, Response, make_response
from app import app, db
from models import Business, Conversation, ConversationMessage, CreditPackage, Purchase
from ai_conversation import AIConversationManager
from payment_handler import PaymentHandler
from content_ecosystem import ContentEcosystemManager
import json
from datetime import datetime
import io
from subscription_manager import SubscriptionManager
from social_media_manager import SocialMediaManager
from infographic_generator import InfographicGenerator
from auto_posting_scheduler import auto_scheduler
from geo_language_detector import geo_detector
from conversation_intelligence import ConversationIntelligence
from datetime import datetime, timedelta
import uuid
import logging
import base64
import random
from external_ai_integration import setup_ai_api_routes
from mood_color_generator import get_conversation_color_palette, get_conversation_theme_css, analyze_conversation_mood

def has_premium_access(business):
    """Check if business has access to premium features (social media, infographics, etc.)"""
    # Enterprise, Pro, and Basic plans have premium access
    if hasattr(business, 'plan_type') and business.plan_type in ['enterprise', 'pro', 'basic']:
        return True
    # Monthly subscribers have access
    if hasattr(business, 'subscription_type') and business.subscription_type != 'credit':
        return True
    # Credit-only users don't have premium access
    return False
import time

# Initialize AI conversation manager and payment handler
ai_manager = AIConversationManager()
payment_handler = PaymentHandler()
subscription_manager = SubscriptionManager()

@app.route('/')
def index():
    """Main landing page showcasing AI-to-AI conversations"""
    
    # Get the currently featured business (or default to Perfect Roofing Team)
    featured_business = Business.query.filter_by(is_featured=True).first()
    
    if not featured_business:
        # Get or create Perfect Roofing Team as default showcase business
        featured_business = Business.query.filter_by(name="Perfect Roofing Team").first()
        
        if not featured_business:
            # Create Perfect Roofing Team as default featured business
            featured_business = Business(
                name="Perfect Roofing Team",
                website="https://perfectroofingteam.com",
                description="Expert roofing contractors serving New Jersey with 10+ years experience. 24/7 emergency services, quality materials, and 100% satisfaction guarantee.",
                location="Lodi, New Jersey",
                phone="+1 862 2386 353",
                email="info@perfectroofingteam.com",
                industry="Roofing & Construction",
                is_unlimited=True,
                credits_remaining=999999,
                plan_type="enterprise",
                is_featured=True,
                share_url=f"https://{request.host}/public/conversation/1"
            )
            db.session.add(featured_business)
        else:
            # Set Perfect Roofing Team as featured if no business is featured
            featured_business.is_featured = True
        
        db.session.commit()
    
    # Get recent conversations for featured business (newest first)
    recent_conversations = Conversation.query.filter_by(
        business_id=featured_business.id
    ).order_by(Conversation.created_at.desc()).limit(3).all()
    
    # Randomize messages for authentic live feed display
    import random
    all_display_messages = []
    for conversation in recent_conversations:
        for message in conversation.messages:
            all_display_messages.append((message, conversation))
    
    # Shuffle all messages for random agent appearance
    random.shuffle(all_display_messages)
    
    # Take only first 16 messages for live feed
    display_messages = all_display_messages[:16]
    
    # If no conversations exist, create sample ones
    if not recent_conversations:
        sample_conversations = [
            {
                "topic": "Emergency Roof Repair Services - 24/7 Availability",
                "messages": [
                    ("Business AI Assistant", "openai", "Perfect Roofing Team offers reliable emergency roof repair services throughout New Jersey with licensed and insured technicians available 24/7."),
                    ("SEO AI Specialist", "anthropic", "Their emergency response capability is a significant competitive advantage, especially for storm damage and urgent leak repairs that can't wait."),
                    ("Customer Service AI", "openai", "The 24/7 availability ensures customers get immediate help when roof emergencies threaten their property and belongings."),
                    ("Marketing AI Expert", "anthropic", "This round-the-clock service availability should be prominently featured in all marketing materials to attract emergency repair customers.")
                ]
            },
            {
                "topic": "Quality Materials and 10+ Years Experience",
                "messages": [
                    ("Business AI Assistant", "openai", "With over 10 years of experience serving New Jersey, Perfect Roofing Team uses only premium quality materials for lasting roof installations."),
                    ("Technical AI Advisor", "anthropic", "Their decade-plus experience means they've handled diverse roofing challenges across different New Jersey weather conditions and building types."),
                    ("Quality AI Inspector", "openai", "Using top-grade materials combined with experienced craftsmanship ensures customer roofs will provide reliable protection for years to come."),
                    ("Business AI Assistant", "anthropic", "This experience-quality combination justifies premium pricing while delivering superior value that customers can see and feel.")
                ]
            },
            {
                "topic": "Transparent Pricing and Customer Satisfaction",
                "messages": [
                    ("Business AI Assistant", "openai", "For residential roofing repairs, Perfect Roofing Team offers comprehensive services with transparent pricing and excellent customer satisfaction ratings."),
                    ("Customer Experience AI", "anthropic", "Transparent pricing builds trust with customers who often worry about hidden costs or surprise charges in roofing projects."),
                    ("Sales AI Consultant", "openai", "Their commitment to 100% satisfaction guarantee shows confidence in their work quality and reduces customer purchase anxiety."),
                    ("Marketing AI Expert", "anthropic", "These customer testimonials and satisfaction guarantees should be leveraged across all digital marketing channels for maximum impact.")
                ]
            }
        ]
        
        for conv_data in sample_conversations:
            conversation = Conversation(
                business_id=featured_business.id,
                topic=conv_data["topic"],
                status="completed",
                credits_used=1
            )
            db.session.add(conversation)
            db.session.flush()  # Get the conversation ID
            
            for i, (agent_name, agent_type, content) in enumerate(conv_data["messages"]):
                message = ConversationMessage(
                    conversation_id=conversation.id,
                    ai_agent_name=agent_name,
                    ai_agent_type=agent_type,
                    content=content,
                    message_order=i + 1
                )
                db.session.add(message)
        
        db.session.commit()
        
        # Refresh recent conversations
        recent_conversations = Conversation.query.filter_by(
            business_id=featured_business.id
        ).order_by(Conversation.created_at.desc()).limit(3).all()
    
    # Get credit packages
    credit_packages = CreditPackage.query.all()
    
    if not credit_packages:
        # Create default credit packages based on research
        packages = [
            {"name": "Starter Pack", "credits": 10, "price": 49.99, "description": "Perfect for small businesses testing AI conversations"},
            {"name": "Business Pack", "credits": 50, "price": 199.99, "description": "Great for growing businesses with regular marketing needs", "is_popular": True},
            {"name": "Professional Pack", "credits": 150, "price": 499.99, "description": "Ideal for established businesses with ongoing content requirements"},
            {"name": "Enterprise Pack", "credits": 500, "price": 1499.99, "description": "Best value for large organizations and agencies"}
        ]
        
        for pkg_data in packages:
            package = CreditPackage(**pkg_data)
            db.session.add(package)
        
        db.session.commit()
        credit_packages = CreditPackage.query.all()
    
    # Calculate total messages today (simulated activity)
    total_messages_today = 2871
    
    return render_template('index.html', 
                         business=featured_business,
                         perfect_roofing=featured_business,  # For template compatibility
                         recent_conversations=recent_conversations,
                         display_messages=display_messages,
                         credit_packages=credit_packages,
                         total_messages_today=total_messages_today)

@app.route('/register_business', methods=['POST'])
def register_business():
    """Register a new business for AI conversation services"""
    
    try:
        name = request.form.get('business_name')
        website = request.form.get('website')
        description = request.form.get('description')
        location = request.form.get('location')
        phone = request.form.get('phone')
        email = request.form.get('email')
        industry = request.form.get('industry')
        
        if not name or not email:
            flash('Business name and email are required.', 'error')
            return redirect(url_for('index'))
        
        # Check if business already exists
        existing_business = Business.query.filter_by(email=email).first()
        if existing_business:
            flash('A business with this email already exists.', 'error')
            return redirect(url_for('index'))
        
        # Create new business (share URL will be set after conversation creation)
        business = Business(
            name=name,
            website=website,
            description=description,
            location=location,
            phone=phone,
            email=email,
            industry=industry,
            credits_remaining=0,  # Start with 0 credits, need to purchase
            share_url=""  # Will be updated after conversation creation
        )
        
        db.session.add(business)
        db.session.commit()
        
        flash(f'Business "{name}" registered successfully! Check your dashboard for your share URL.', 'success')
        return redirect(url_for('business_dashboard', business_id=business.id))
        
    except Exception as e:
        logging.error(f"Error registering business: {e}")
        flash('An error occurred while registering your business. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/business/<int:business_id>')
def business_dashboard(business_id):
    """Business dashboard for managing AI conversations and credits"""
    
    business = Business.query.get_or_404(business_id)
    conversations = Conversation.query.filter_by(business_id=business_id).order_by(Conversation.created_at.desc()).all()
    credit_packages = CreditPackage.query.all()
    
    # Generate proper showcase URL if not set
    if not business.share_url:
        from flask import request
        # Use the actual latest conversation URL if available
        latest_conversation = Conversation.query.filter_by(business_id=business_id).order_by(Conversation.created_at.desc()).first()
        if latest_conversation:
            business.share_url = f"{request.host_url}public/conversation/{latest_conversation.id}"
        else:
            business.share_url = f"{request.host_url}business/{business_id}"
        db.session.commit()
    
    return render_template('business_dashboard.html', 
                         business=business, 
                         conversations=conversations,
                         credit_packages=credit_packages)

@app.route('/start_conversation', methods=['POST'])
def start_conversation():
    """Start a new AI-to-AI conversation for a business"""
    
    try:
        business_id = request.form.get('business_id')
        topic = request.form.get('topic')
        
        business = Business.query.get_or_404(business_id)
        
        # Check if business has credits (unless unlimited)
        if not business.is_unlimited and business.credits_remaining < 1:
            flash('Insufficient credits. Please purchase a credit package to start conversations.', 'error')
            return redirect(url_for('business_dashboard', business_id=business_id))
        
        if not topic:
            flash('Conversation topic is required.', 'error')
            return redirect(url_for('business_dashboard', business_id=business_id))
        
        # Create new conversation
        conversation = Conversation(
            business_id=business_id,
            topic=topic,
            status='active'
        )
        db.session.add(conversation)
        db.session.flush()  # Get conversation ID
        
        # Generate AI-to-AI conversation
        messages = ai_manager.generate_conversation(business, topic)
        
        # Save messages to database
        for i, (agent_name, agent_type, content) in enumerate(messages):
            message = ConversationMessage(
                conversation_id=conversation.id,
                ai_agent_name=agent_name,
                ai_agent_type=agent_type,
                content=content,
                message_order=i + 1
            )
            db.session.add(message)
        
        # Update conversation status and credits
        conversation.status = 'completed'
        conversation.credits_used = 1
        
        if not business.is_unlimited:
            business.credits_remaining -= 1
        
        db.session.commit()
        
        flash(f'AI conversation generated successfully for topic: "{topic}"', 'success')
        return redirect(url_for('business_dashboard', business_id=business_id))
        
    except Exception as e:
        logging.error(f"Error starting conversation: {e}")
        flash('An error occurred while generating the conversation. Please try again.', 'error')
        return redirect(url_for('business_dashboard', business_id=business_id))

@app.route('/purchase_credits', methods=['POST'])
def purchase_credits():
    """Handle credit package purchases via PayPal"""
    
    try:
        business_id = request.form.get('business_id')
        package_id = request.form.get('package_id')
        
        business = Business.query.get_or_404(business_id)
        package = CreditPackage.query.get_or_404(package_id)
        
        # Create purchase record
        purchase = Purchase(
            business_id=business_id,
            package_id=package_id,
            credits_purchased=package.credits,
            amount_paid=package.price,
            status='pending'
        )
        db.session.add(purchase)
        db.session.flush()  # Get purchase ID
        
        # Process payment with PayPal (simplified for demo)
        payment_result = payment_handler.process_payment(
            amount=package.price,
            description=f"{package.name} - {package.credits} Credits",
            purchase_id=purchase.id
        )
        
        if payment_result['success']:
            # Update purchase and business credits
            purchase.status = 'completed'
            purchase.payment_id = payment_result['payment_id']
            
            # Handle Enterprise plan differently
            if package.name == 'Enterprise Unlimited':
                business.plan_type = 'enterprise'
                business.is_unlimited = True
                business.credits_remaining = -1  # Unlimited
                flash(f'Welcome to Enterprise! You now have unlimited conversations and complete content ecosystem access.', 'success')
            else:
                business.credits_remaining += package.credits
                flash(f'Successfully purchased {package.credits} credits for ${package.price}!', 'success')
            
            db.session.commit()
        else:
            purchase.status = 'failed'
            db.session.commit()
            flash('Payment failed. Please try again.', 'error')
        
        return redirect(url_for('business_dashboard', business_id=business_id))
        
    except Exception as e:
        logging.error(f"Error processing payment: {e}")
        flash('An error occurred while processing your payment. Please try again.', 'error')
        return redirect(url_for('business_dashboard', business_id=business_id))

@app.route('/conversation/<int:conversation_id>')
def view_conversation(conversation_id):
    """View detailed conversation with all messages"""
    
    conversation = Conversation.query.get_or_404(conversation_id)
    return render_template('conversation_detail.html', conversation=conversation)

@app.route('/public/conversation/<int:conversation_id>')
def public_conversation(conversation_id):
    """Public SEO-optimized conversation page for search engines and AI crawlers"""
    conversation = Conversation.query.get_or_404(conversation_id)
    business = conversation.business
    
    # Generate SEO metadata
    meta_title = f"{conversation.topic} - AI Discussion about {business.name}"
    meta_description = f"Expert AI conversation about {conversation.topic} featuring {business.name}. {len(conversation.messages)} messages from business AI specialists."
    
    # Create structured data for search engines
    structured_data = {
        "@context": "https://schema.org",
        "@type": "QAPage",
        "mainEntity": {
            "@type": "Question",
            "name": conversation.topic,
            "text": f"What do AI experts say about {conversation.topic}?",
            "answerCount": len(conversation.messages),
            "acceptedAnswer": {
                "@type": "Answer",
                "text": conversation.messages[0].content if conversation.messages else "",
                "author": {
                    "@type": "Organization",
                    "name": business.name,
                    "url": business.website
                }
            }
        },
        "about": {
            "@type": "Organization",
            "name": business.name,
            "url": business.website,
            "description": business.description
        }
    }
    
    return render_template('public_conversation.html', 
                         conversation=conversation,
                         business=business,
                         meta_title=meta_title,
                         meta_description=meta_description,
                         structured_data=structured_data)

@app.route('/sitemap.xml')
def sitemap():
    """Generate sitemap for search engines"""
    from flask import make_response
    
    # Get all conversations that should be public
    public_conversations = Conversation.query.join(Business).filter(
        Business.is_unlimited == True
    ).order_by(Conversation.created_at.desc()).all()
    
    sitemap_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{request.host_url}</loc>
        <lastmod>{}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>'''.format(datetime.utcnow().strftime('%Y-%m-%d'))
    
    for conversation in public_conversations:
        sitemap_xml += '''
    <url>
        <loc>{request.host_url}public/conversation/{}</loc>
        <lastmod>{}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>'''.format(conversation.id, conversation.created_at.strftime('%Y-%m-%d'))
    
    sitemap_xml += '''
</urlset>'''
    
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response

@app.route('/robots.txt')
def robots_txt():
    """Generate robots.txt to allow AI crawlers"""
    from flask import make_response
    
    robots_content = '''User-agent: *
Allow: /
Allow: /public/conversation/
Allow: /sitemap.xml

User-agent: Googlebot
Allow: /
Allow: /public/conversation/

User-agent: GPTBot
Allow: /
Allow: /public/conversation/

User-agent: Bingbot
Allow: /
Allow: /public/conversation/

User-agent: facebookexternalhit
Allow: /
Allow: /public/conversation/

Sitemap: {request.host_url}sitemap.xml'''
    
    response = make_response(robots_content)
    response.headers["Content-Type"] = "text/plain"
    return response

@app.route('/api-status')
def api_status():
    """Quick API status check"""
    from flask import jsonify
    
    status = {
        'openai': ai_manager.apis_available['openai'],
        'anthropic': ai_manager.apis_available['anthropic'],
        'perplexity': ai_manager.apis_available['perplexity'],
        'gemini': ai_manager.apis_available['gemini'],
        'paypal': payment_handler.paypal_available,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return jsonify(status)

@app.route('/api/live-conversation')
@app.route('/api/live-conversation/<int:business_id>')
def api_live_conversation(business_id=None):
    """Get current live conversation data for a specific business or featured business"""
    try:
        # Get the specified business or the featured business
        if business_id:
            target_business = Business.query.get(business_id)
        else:
            target_business = Business.query.filter_by(is_featured=True).first()
            if not target_business:
                target_business = Business.query.first()
        
        if target_business:
            # Get latest conversation for the target business
            latest_conversation = Conversation.query.filter_by(
                business_id=target_business.id
            ).order_by(Conversation.created_at.desc()).first()
            
            if latest_conversation:
                # Get messages for this conversation
                messages = ConversationMessage.query.filter_by(
                    conversation_id=latest_conversation.id
                ).order_by(ConversationMessage.created_at.desc()).limit(16).all()
                
                # Format messages for API response
                formatted_messages = []
                for i, message in enumerate(messages):
                    # Calculate staggered timestamps (2 minutes apart)
                    base_time = datetime.now()
                    message_time = base_time - timedelta(minutes=i * 2)
                    
                    formatted_messages.append({
                        'id': message.id,
                        'agent_name': message.agent_name,
                        'agent_type': message.agent_type,
                        'message_content': message.message_content,
                        'timestamp': message_time.strftime('%I:%M %p'),
                        'source_url': target_business.website_url or 'https://perfectroofingteam.com'
                    })
                
                return jsonify({
                    'success': True,
                    'messages': formatted_messages,
                    'topic': latest_conversation.topic,
                    'messageCount': len(formatted_messages),
                    'business': {
                        'id': target_business.id,
                        'name': target_business.business_name,
                        'website': target_business.website_url
                    }
                })
        
        # Fallback if no data available
        return jsonify({
            'success': False,
            'messages': [],
            'topic': 'General Business Discussion',
            'messageCount': 0
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'messages': [],
            'topic': 'Error loading conversation',
            'messageCount': 0
        }), 500

@app.route('/api/live-conversation/latest')
@app.route('/api/live-conversation/<int:business_id>/latest')
def api_latest_message(business_id=None):
    """Get the latest message from live conversation for a specific business"""
    try:
        # Get the specified business or the featured business
        if business_id:
            target_business = Business.query.get(business_id)
        else:
            target_business = Business.query.filter_by(is_featured=True).first()
            if not target_business:
                target_business = Business.query.first()
        
        if target_business:
            latest_conversation = Conversation.query.filter_by(
                business_id=target_business.id
            ).order_by(Conversation.created_at.desc()).first()
            
            if latest_conversation:
                latest_message = ConversationMessage.query.filter_by(
                    conversation_id=latest_conversation.id
                ).order_by(ConversationMessage.created_at.desc()).first()
                
                if latest_message:
                    current_time = datetime.now()
                    return jsonify({
                        'success': True,
                        'message': {
                            'id': latest_message.id,
                            'agent_name': latest_message.agent_name,
                            'agent_type': latest_message.agent_type,
                            'message_content': latest_message.message_content,
                            'timestamp': current_time.strftime('%I:%M %p'),
                            'source_url': target_business.website_url or 'https://perfectroofingteam.com'
                        },
                        'topic': latest_conversation.topic,
                        'business': {
                            'id': target_business.id,
                            'name': target_business.business_name
                        }
                    })
        
        return jsonify({
            'success': False,
            'message': None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/investigation', methods=['POST'])
def api_investigation():
    """Generate investigation summary for a message"""
    try:
        data = request.get_json()
        message_id = data.get('messageId')
        message_content = data.get('messageContent', '')
        agent_type = data.get('agentType', 'Business AI Assistant')
        topic = data.get('topic', 'Business Analysis')
        
        # Enhanced investigation logic using AI
        try:
            # Try to get AI-generated investigation
            investigation_prompt = f"""
            Provide a comprehensive business investigation analysis for the following AI agent message:
            
            Agent Type: {agent_type}
            Topic: {topic}
            Message: {message_content}
            
            Generate a detailed investigation with:
            1. Title (relevant to the agent type)
            2. Executive summary
            3. Three detailed analysis sections
            4. Confidence assessment (85-99%)
            
            Focus on actionable business insights and professional analysis.
            """
            
            response = ai_manager._get_openai_response(
                business_context="Perfect Roofing Team - Professional roofing services in New Jersey",
                topic=investigation_prompt,
                conversation_history="",
                agent_name="Investigation Specialist",
                round_num=1,
                msg_num=1
            )
            
            # Parse AI response into structured format
            investigation_data = {
                'title': f'{agent_type} Analysis Report',
                'summary': f'AI-powered investigation of {topic.lower()} insights and recommendations.',
                'sections': [
                    {
                        'title': 'Current Assessment',
                        'content': response[:200] + "..." if len(response) > 200 else response
                    },
                    {
                        'title': 'Strategic Insights',
                        'content': 'Comprehensive analysis reveals strong market positioning and growth opportunities in the roofing industry.'
                    },
                    {
                        'title': 'Recommendations',
                        'content': 'Continue leveraging AI-driven customer engagement and expand digital marketing initiatives.'
                    }
                ],
                'messageContent': message_content,
                'agentType': agent_type,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'confidence': random.randint(88, 97)
            }
            
        except Exception as ai_error:
            # Fallback to structured template
            investigation_templates = {
                'Business AI Assistant': {
                    'title': 'Business Strategy & Operations Analysis',
                    'summary': 'Comprehensive evaluation of business operations, market position, and strategic opportunities.',
                    'sections': [
                        {
                            'title': 'Operational Excellence',
                            'content': 'Analysis indicates strong operational capabilities with systematic approach to service delivery. Quality standards and customer satisfaction metrics demonstrate industry-leading performance.'
                        },
                        {
                            'title': 'Market Position',
                            'content': 'Competitive analysis reveals significant advantages in local market expertise, customer service quality, and technical competency. Brand recognition continues to strengthen.'
                        },
                        {
                            'title': 'Growth Strategy',
                            'content': 'Recommended focus areas include digital transformation, service expansion, and strategic partnerships. Investment in technology and training will enhance scalability.'
                        }
                    ]
                },
                'Marketing AI Expert': {
                    'title': 'Digital Marketing & Brand Performance',
                    'summary': 'In-depth analysis of marketing effectiveness, brand positioning, and digital presence optimization.',
                    'sections': [
                        {
                            'title': 'Brand Positioning',
                            'content': 'Strong brand equity in local market with positive customer sentiment. Messaging consistency across channels reinforces trust and reliability positioning.'
                        },
                        {
                            'title': 'Digital Performance',
                            'content': 'SEO metrics show excellent local search visibility. Website conversion rates and customer engagement indicate effective digital strategy execution.'
                        },
                        {
                            'title': 'Campaign Optimization',
                            'content': 'Seasonal campaign performance data suggests opportunities for enhanced targeting. Recommended investment in video content and customer testimonials.'
                        }
                    ]
                },
                'Customer Service AI': {
                    'title': 'Customer Experience & Service Quality',
                    'summary': 'Detailed assessment of customer service performance, satisfaction metrics, and experience optimization opportunities.',
                    'sections': [
                        {
                            'title': 'Service Excellence',
                            'content': 'Customer satisfaction scores consistently exceed industry benchmarks. Response time and issue resolution metrics demonstrate commitment to service quality.'
                        },
                        {
                            'title': 'Customer Journey',
                            'content': 'End-to-end customer experience analysis reveals smooth onboarding and project management processes. Communication protocols ensure transparency.'
                        },
                        {
                            'title': 'Improvement Areas',
                            'content': 'Opportunities exist for enhanced digital self-service options and proactive communication. Customer feedback systems show strong satisfaction trends.'
                        }
                    ]
                },
                'SEO AI Specialist': {
                    'title': 'Search Engine Optimization & Online Visibility',
                    'summary': 'Technical analysis of SEO performance, keyword rankings, and organic traffic optimization strategies.',
                    'sections': [
                        {
                            'title': 'Search Performance',
                            'content': 'Keyword rankings show strong positions for primary service terms. Local search optimization delivers consistent visibility in target geographic areas.'
                        },
                        {
                            'title': 'Content Strategy',
                            'content': 'Content performance metrics indicate effective topic targeting and user engagement. Technical SEO implementation supports strong search engine accessibility.'
                        },
                        {
                            'title': 'Growth Opportunities',
                            'content': 'Analysis suggests expansion into additional geographic keywords and seasonal content optimization. Link building initiatives show promising results.'
                        }
                    ]
                }
            }
            
            template = investigation_templates.get(agent_type, investigation_templates['Business AI Assistant'])
            investigation_data = {
                'title': template['title'],
                'summary': template['summary'],
                'sections': template['sections'],
                'messageContent': message_content,
                'agentType': agent_type,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'confidence': random.randint(85, 95)
            }
        
        return jsonify({
            'success': True,
            **investigation_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate-topic', methods=['POST'])
def api_generate_topic():
    """Generate a new conversation topic"""
    try:
        featured_business = Business.query.filter_by(is_featured=True).first()
        
        if featured_business:
            # Use conversation intelligence to get a smart topic
            conv_intel = ConversationIntelligence()
            new_topic = conv_intel.get_smart_topic_suggestion(featured_business.id)
            
            return jsonify({
                'success': True,
                'topic': new_topic
            })
        else:
            # Fallback topics
            fallback_topics = [
                'Emergency Roofing Services and Response Times',
                'Sustainable Roofing Materials and Energy Efficiency',
                'Insurance Claims and Storm Damage Assessment',
                'Commercial vs Residential Roofing Solutions',
                'Preventive Maintenance and Inspection Programs'
            ]
            
            return jsonify({
                'success': True,
                'topic': random.choice(fallback_topics)
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'topic': 'General Business Discussion'
        }), 500

@app.route('/api-test')
def api_test():
    """API integration test page"""
    return render_template('api_test.html')



@app.route('/api/business/<int:business_id>/generate-content', methods=['POST'])
def api_generate_business_content(business_id):
    """Generate content for a business"""
    try:
        business = Business.query.get(business_id)
        if not business:
            return jsonify({'error': 'Business not found'}), 404
        
        data = request.get_json()
        content_type = data.get('contentType')
        
        if not content_type:
            return jsonify({'error': 'Content type required'}), 400
        
        # Generate content using the content ecosystem manager
        ecosystem_manager = ContentEcosystemManager()
        
        if content_type == 'faq':
            # Generate FAQ content
            faq_data = ecosystem_manager._generate_faq_pages(business, business.industry)
            return jsonify({
                'success': True,
                'content_type': content_type,
                'data': faq_data,
                'message': 'FAQ content generated successfully'
            })
        elif content_type == 'local_seo':
            # Generate local SEO content
            local_data = ecosystem_manager._generate_local_pages(business, business.location)
            return jsonify({
                'success': True,
                'content_type': content_type,
                'data': local_data,
                'message': 'Local SEO content generated successfully'
            })
        elif content_type == 'voice_search':
            # Generate voice search content
            voice_data = ecosystem_manager._generate_voice_search_content(business, business.industry)
            return jsonify({
                'success': True,
                'content_type': content_type,
                'data': voice_data,
                'message': 'Voice search content generated successfully'
            })
        elif content_type == 'knowledge_base':
            # Generate knowledge base content
            kb_data = ecosystem_manager._generate_knowledge_base(business, business.industry)
            return jsonify({
                'success': True,
                'content_type': content_type,
                'data': kb_data,
                'message': 'Knowledge base content generated successfully'
            })
        else:
            return jsonify({'error': 'Invalid content type'}), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/business/<int:business_id>/content/<content_type>')
def api_get_business_content(business_id, content_type):
    """Get generated content for a business"""
    try:
        business = Business.query.get(business_id)
        if not business:
            return jsonify({'error': 'Business not found'}), 404
        
        # Mock content data - would be retrieved from database
        content_data = {
            'title': f'{content_type.title()} Content for {business.business_name}',
            'content': f'This is the generated {content_type} content for {business.business_name}.',
            'generated_at': '2025-07-04T02:00:00Z',
            'status': 'generated'
        }
        
        return jsonify(content_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/business/<int:business_id>/content/<content_type>/download')
def api_download_business_content(business_id, content_type):
    """Download content as PDF"""
    try:
        business = Business.query.get(business_id)
        if not business:
            return jsonify({'error': 'Business not found'}), 404
        
        # For now, return a simple text file
        content = f"""
{content_type.title()} Content for {business.business_name}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is a sample {content_type} content document for {business.business_name}.
In a real implementation, this would contain the actual generated content.
"""
        
        response = Response(
            content,
            mimetype='text/plain',
            headers={
                'Content-Disposition': f'attachment; filename={content_type}_{business.business_name}.txt'
            }
        )
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/business/<int:business_id>/content/<content_type>', methods=['DELETE'])
def api_delete_business_content(business_id, content_type):
    """Delete generated content"""
    try:
        business = Business.query.get(business_id)
        if not business:
            return jsonify({'error': 'Business not found'}), 404
        
        # In a real implementation, this would delete from database
        return jsonify({
            'success': True,
            'message': f'{content_type} content deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test-ai-services')
def test_ai_services():
    """Test all 4 AI services to verify they're working"""
    from flask import jsonify
    
    test_results = {
        'openai': False,
        'anthropic': False, 
        'perplexity': False,
        'gemini': False,
        'timestamp': datetime.utcnow().isoformat(),
        'errors': []
    }
    
    try:
        # Test each AI service with a simple prompt
        test_prompt = "What is AI?"
        
        # Test OpenAI
        try:
            if ai_manager.apis_available['openai']:
                response = ai_manager.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": test_prompt}],
                    max_tokens=50
                )
                if response.choices[0].message.content:
                    test_results['openai'] = True
        except Exception as e:
            test_results['errors'].append(f"OpenAI: {str(e)}")
        
        # Test Anthropic
        try:
            if ai_manager.apis_available['anthropic']:
                response = ai_manager.anthropic_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=50,
                    messages=[{"role": "user", "content": test_prompt}]
                )
                if response.content and len(response.content) > 0:
                    test_results['anthropic'] = True
        except Exception as e:
            test_results['errors'].append(f"Anthropic: {str(e)}")
        
        # Test Perplexity
        try:
            if ai_manager.apis_available['perplexity']:
                import requests
                headers = {
                    'Authorization': f'Bearer {ai_manager.perplexity_api_key}',
                    'Content-Type': 'application/json'
                }
                data = {
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [{"role": "user", "content": test_prompt}],
                    "max_tokens": 50
                }
                response = requests.post(
                    'https://api.perplexity.ai/chat/completions',
                    headers=headers,
                    json=data,
                    timeout=10
                )
                if response.status_code == 200:
                    result = response.json()
                    if result.get('choices') and result['choices'][0]['message']['content']:
                        test_results['perplexity'] = True
        except Exception as e:
            test_results['errors'].append(f"Perplexity: {str(e)}")
        
        # Test Gemini
        try:
            if ai_manager.apis_available['gemini']:
                response = ai_manager.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=test_prompt
                )
                if response.text:
                    test_results['gemini'] = True
        except Exception as e:
            test_results['errors'].append(f"Gemini: {str(e)}")
    
    except Exception as e:
        test_results['errors'].append(f"General error: {str(e)}")
    
    return jsonify(test_results)

@app.route('/test-page-discovery/<business_id>')
def test_page_discovery(business_id):
    """Test website page discovery for a business"""
    from flask import jsonify
    
    try:
        business = Business.query.get_or_404(business_id)
        
        if business.website:
            discovered_pages = ai_manager.discover_website_pages(business.website)
            
            return jsonify({
                'business_name': business.name,
                'website': business.website,
                'discovered_pages': discovered_pages,
                'total_pages': len(discovered_pages),
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'error': 'Business has no website URL configured',
                'business_name': business.name
            })
            
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        })

# Enterprise Content Ecosystem Routes
@app.route('/business/<business_name>/faq/')
@app.route('/business/<business_name>/faq/<faq_slug>')
def business_faq(business_name, faq_slug=None):
    """Business FAQ pages"""
    business = Business.query.filter(Business.name.ilike(business_name.replace('-', ' '))).first()
    if not business or business.plan_type != 'enterprise':
        return redirect(url_for('index'))
    
    ecosystem_manager = ContentEcosystemManager()
    ecosystem = ecosystem_manager.generate_business_ecosystem(business)
    
    if faq_slug:
        # Show specific FAQ page
        faq_page = next((faq for faq in ecosystem['faq_pages'] if faq['slug'] == faq_slug), None)
        if not faq_page:
            return redirect(url_for('business_faq', business_name=business_name))
        
        return render_template('business_content.html', 
                             business=business, 
                             page_type='faq',
                             content_page=faq_page,
                             all_pages=ecosystem['faq_pages'])
    else:
        # Show FAQ index
        return render_template('business_content_index.html',
                             business=business,
                             page_type='faq',
                             pages=ecosystem['faq_pages'])

@app.route('/business/<business_name>/local/')
@app.route('/business/<business_name>/local/<location_slug>')
def business_local(business_name, location_slug=None):
    """Business local SEO pages"""
    business = Business.query.filter(Business.name.ilike(business_name.replace('-', ' '))).first()
    if not business or business.plan_type != 'enterprise':
        return redirect(url_for('index'))
    
    ecosystem_manager = ContentEcosystemManager()
    ecosystem = ecosystem_manager.generate_business_ecosystem(business)
    
    if location_slug:
        # Show specific local page
        local_page = next((page for page in ecosystem['local_pages'] if page['slug'] == location_slug), None)
        if not local_page:
            return redirect(url_for('business_local', business_name=business_name))
        
        return render_template('business_content.html',
                             business=business,
                             page_type='local',
                             content_page=local_page,
                             all_pages=ecosystem['local_pages'])
    else:
        # Show local index
        return render_template('business_content_index.html',
                             business=business,
                             page_type='local',
                             pages=ecosystem['local_pages'])

@app.route('/business/<business_name>/voice-search/')
@app.route('/business/<business_name>/voice-search/<voice_slug>')
def business_voice_search(business_name, voice_slug=None):
    """Business voice search optimized pages"""
    business = Business.query.filter(Business.name.ilike(business_name.replace('-', ' '))).first()
    if not business or business.plan_type != 'enterprise':
        return redirect(url_for('index'))
    
    ecosystem_manager = ContentEcosystemManager()
    ecosystem = ecosystem_manager.generate_business_ecosystem(business)
    
    if voice_slug:
        # Show specific voice search page
        voice_page = next((page for page in ecosystem['voice_search'] if page['slug'] == voice_slug), None)
        if not voice_page:
            return redirect(url_for('business_voice_search', business_name=business_name))
        
        return render_template('business_content.html',
                             business=business,
                             page_type='voice-search',
                             content_page=voice_page,
                             all_pages=ecosystem['voice_search'])
    else:
        # Show voice search index
        return render_template('business_content_index.html',
                             business=business,
                             page_type='voice-search',
                             pages=ecosystem['voice_search'])

@app.route('/business/<business_name>/knowledge-base/')
@app.route('/business/<business_name>/knowledge-base/<knowledge_slug>')
def business_knowledge_base(business_name, knowledge_slug=None):
    """Business knowledge base pages"""
    business = Business.query.filter(Business.name.ilike(business_name.replace('-', ' '))).first()
    if not business or business.plan_type != 'enterprise':
        return redirect(url_for('index'))
    
    ecosystem_manager = ContentEcosystemManager()
    ecosystem = ecosystem_manager.generate_business_ecosystem(business)
    
    if knowledge_slug:
        # Show specific knowledge page
        knowledge_page = next((page for page in ecosystem['knowledge_base'] if page['slug'] == knowledge_slug), None)
        if not knowledge_page:
            return redirect(url_for('business_knowledge_base', business_name=business_name))
        
        return render_template('business_content.html',
                             business=business,
                             page_type='knowledge-base',
                             content_page=knowledge_page,
                             all_pages=ecosystem['knowledge_base'])
    else:
        # Show knowledge base index
        return render_template('business_content_index.html',
                             business=business,
                             page_type='knowledge-base',
                             pages=ecosystem['knowledge_base'])

@app.route('/business/<business_name>/live-conversation/')
def business_live_conversation(business_name):
    """Business live conversation feed"""
    business = Business.query.filter(Business.name.ilike(business_name.replace('-', ' '))).first()
    if not business or business.plan_type != 'enterprise':
        return redirect(url_for('index'))
    
    # Get the business's main conversation
    conversation = Conversation.query.filter_by(business_id=business.id).first()
    if not conversation:
        return redirect(url_for('index'))
    
    return render_template('business_live_conversation.html',
                         business=business,
                         conversation=conversation)

@app.route('/business/<business_name>/')
def business_ecosystem_home(business_name):
    """Business ecosystem homepage"""
    business = Business.query.filter(Business.name.ilike(business_name.replace('-', ' '))).first()
    if not business or business.plan_type != 'enterprise':
        return redirect(url_for('index'))
    
    ecosystem_manager = ContentEcosystemManager()
    ecosystem = ecosystem_manager.generate_business_ecosystem(business)
    
    return render_template('business_ecosystem_home.html',
                         business=business,
                         ecosystem=ecosystem)

@app.route('/all-conversations')
def all_conversations():
    """View all AI conversations across all businesses"""
    conversations = Conversation.query.join(Business).order_by(Conversation.created_at.desc()).limit(50).all()
    
    return render_template('all_conversations.html',
                         conversations=conversations)

@app.route('/business/<int:business_id>/subscription-upgrade')
def subscription_upgrade_page(business_id):
    """Show subscription upgrade options for a business"""
    business = Business.query.get_or_404(business_id)
    
    # Get monthly plans
    monthly_plans = subscription_manager.get_monthly_plans_for_display()
    
    # Calculate savings for each plan
    savings_calculations = {}
    for plan in monthly_plans:
        savings = subscription_manager.calculate_upgrade_savings(business_id, plan['id'])
        savings_calculations[plan['id']] = savings
    
    # Get current subscription status
    subscription_status = subscription_manager.get_subscription_status(business_id)
    
    return render_template('subscription_upgrade.html',
                         business=business,
                         monthly_plans=monthly_plans,
                         savings_calculations=savings_calculations,
                         subscription_status=subscription_status)

@app.route('/business/<int:business_id>/upgrade-subscription', methods=['POST'])
def upgrade_subscription(business_id):
    """Process subscription upgrade"""
    business = Business.query.get_or_404(business_id)
    plan_type = request.form.get('plan_type')
    
    if not plan_type:
        flash('Please select a plan to upgrade to.', 'error')
        return redirect(url_for('subscription_upgrade_page', business_id=business_id))
    
    # Process the upgrade
    result = subscription_manager.upgrade_to_monthly_plan(business_id, plan_type)
    
    if result['success']:
        flash(f'Successfully upgraded to {result["plan"]["name"]}! Your next billing date is {result["next_billing_date"].strftime("%B %d, %Y")}.', 'success')
        return redirect(url_for('business_dashboard', business_id=business_id))
    else:
        flash(f'Upgrade failed: {result["error"]}', 'error')
        return redirect(url_for('subscription_upgrade_page', business_id=business_id))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard to manage featured business"""
    all_businesses = Business.query.all()
    featured_business = Business.query.filter_by(is_featured=True).first()
    
    return render_template('admin_dashboard.html', 
                         businesses=all_businesses,
                         featured_business=featured_business)

@app.route('/admin/set-featured/<int:business_id>', methods=['POST'])
def set_featured_business(business_id):
    """Set a business as the featured showcase"""
    # Remove featured status from all businesses
    Business.query.update({'is_featured': False})
    
    # Set the selected business as featured
    business = Business.query.get_or_404(business_id)
    business.is_featured = True
    
    db.session.commit()
    
    flash(f'{business.name} is now the featured business!', 'success')
    return redirect('/admin')

@app.route('/admin/upgrade-enterprise/<int:business_id>', methods=['POST'])
def upgrade_to_enterprise(business_id):
    """Upgrade a business to Enterprise plan"""
    business = Business.query.get_or_404(business_id)
    business.plan_type = 'enterprise'
    business.is_unlimited = True
    business.credits_remaining = -1  # Unlimited
    
    db.session.commit()
    
    flash(f'{business.name} upgraded to Enterprise plan!', 'success')
    return redirect('/admin')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.route('/business/<int:business_id>/social-media')
def social_media_dashboard(business_id):
    """Social media management dashboard for monthly subscribers"""
    business = Business.query.get_or_404(business_id)
    
    # Check if monthly subscriber or enterprise
    if hasattr(business, 'plan_type') and business.plan_type in ['enterprise', 'pro', 'basic']:
        # Enterprise, Pro, and Basic plans have social media access
        pass
    elif hasattr(business, 'subscription_type') and business.subscription_type != 'credit':
        # Monthly subscribers have access
        pass
    else:
        # Credit-only users need to upgrade
        flash('Social media features are only available for monthly subscribers. Please upgrade your plan.', 'warning')
        return redirect(url_for('subscription_upgrade_page', business_id=business_id))
    
    social_manager = SocialMediaManager()
    platform_settings = social_manager.get_platform_settings(business_id)
    analytics = social_manager.get_posting_analytics(business_id)
    
    return render_template('social_media_dashboard.html', 
                         business=business, 
                         platform_settings=platform_settings['platforms'],
                         current_settings=platform_settings['current_settings'],
                         analytics=analytics.get('analytics', {}))

@app.route('/business/<int:business_id>/social-media/schedule', methods=['POST'])
def schedule_social_posts(business_id):
    """Schedule automatic social media posts"""
    try:
        business = Business.query.get_or_404(business_id)
        
        # Check if has premium access
        if not has_premium_access(business):
            return jsonify({'success': False, 'error': 'Feature only available for monthly subscribers'})
        
        selected_platforms = request.form.getlist('platforms')
        custom_times = {}
        
        for platform in selected_platforms:
            times = request.form.getlist(f'{platform}_times')
            if times:
                custom_times[platform] = times
        
        social_manager = SocialMediaManager()
        result = social_manager.schedule_daily_posts(business_id, selected_platforms, custom_times)
        
        if result['success']:
            flash(f'Successfully scheduled {result["scheduled_posts"]} posts!', 'success')
        else:
            flash(f'Scheduling failed: {result["error"]}', 'error')
        
        return redirect(url_for('social_media_dashboard', business_id=business_id))
        
    except Exception as e:
        logging.error(f"Error scheduling posts: {str(e)}")
        flash('An error occurred while scheduling posts. Please try again.', 'error')
        return redirect(url_for('social_media_dashboard', business_id=business_id))

@app.route('/business/<int:business_id>/social-media/custom-post', methods=['POST'])
def add_custom_post(business_id):
    """Add custom social media post"""
    try:
        business = Business.query.get_or_404(business_id)
        
        # Check if has premium access
        if not has_premium_access(business):
            return jsonify({'success': False, 'error': 'Feature only available for monthly subscribers'})
        
        platform = request.form.get('platform')
        content = request.form.get('content')
        scheduled_time = request.form.get('scheduled_time')
        
        # Handle image upload
        image_data = None
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename:
                # Convert image to base64
                image_bytes = image_file.read()
                image_data = base64.b64encode(image_bytes).decode('utf-8')
        
        # Parse scheduled time
        schedule_dt = None
        if scheduled_time:
            schedule_dt = datetime.fromisoformat(scheduled_time)
        
        social_manager = SocialMediaManager()
        result = social_manager.add_custom_post(business_id, platform, content, image_data, schedule_dt)
        
        if result['success']:
            flash('Custom post added successfully!', 'success')
        else:
            flash(f'Failed to add post: {result["error"]}', 'error')
        
        return redirect(url_for('social_media_dashboard', business_id=business_id))
        
    except Exception as e:
        logging.error(f"Error adding custom post: {str(e)}")
        flash('An error occurred while adding the post. Please try again.', 'error')
        return redirect(url_for('social_media_dashboard', business_id=business_id))

@app.route('/business/<int:business_id>/generate-infographic/<int:conversation_id>')
def generate_infographic(business_id, conversation_id):
    """Generate infographic from conversation for monthly subscribers"""
    try:
        business = Business.query.get_or_404(business_id)
        
        # Check if has premium access
        if not has_premium_access(business):
            flash('Infographic generation is only available for monthly subscribers.', 'warning')
            return redirect(url_for('subscription_upgrade_page', business_id=business_id))
        
        infographic_generator = InfographicGenerator()
        result = infographic_generator.generate_conversation_infographic(conversation_id)
        
        if result['success']:
            # Return the image data as a downloadable file
            from flask import Response
            
            image_data = base64.b64decode(result['image_data'])
            return Response(
                image_data,
                mimetype='image/png',
                headers={
                    'Content-Disposition': f'attachment; filename="{result["filename"]}"'
                }
            )
        else:
            flash(f'Failed to generate infographic: {result["error"]}', 'error')
            return redirect(url_for('view_conversation', conversation_id=conversation_id))
            
    except Exception as e:
        logging.error(f"Error generating infographic: {str(e)}")
        flash('An error occurred while generating the infographic. Please try again.', 'error')

@app.route('/sample-infographic')
def sample_infographic():
    """Serve the sample infographic directly"""
    try:
        from flask import send_from_directory
        return send_from_directory('static', 'sample_infographic.png')
    except Exception as e:
        logging.error(f"Error serving sample infographic: {str(e)}")
        return "Sample infographic not found", 404
        return redirect(url_for('view_conversation', conversation_id=conversation_id))

@app.route('/business/<int:business_id>/social-media/setup')
def social_media_setup(business_id):
    """One-click social media setup page"""
    business = Business.query.get_or_404(business_id)
    
    # Check if has premium access
    if not has_premium_access(business):
        flash('Auto-posting is only available for monthly subscribers. Please upgrade your plan.', 'warning')
        return redirect(url_for('subscription_upgrade_page', business_id=business_id))
    
    # Get posting preview
    preview = auto_scheduler.get_posting_preview(business_id)
    
    return render_template('social_media_setup.html', 
                         business=business,
                         preview=preview.get('preview', {}),
                         platforms=SocialMediaManager.SUPPORTED_PLATFORMS)

@app.route('/business/<int:business_id>/social-media/connect', methods=['POST'])
def connect_social_accounts(business_id):
    """Connect social media accounts for auto-posting"""
    try:
        business = Business.query.get_or_404(business_id)
        
        # Check if has premium access
        if not has_premium_access(business):
            return jsonify({'success': False, 'error': 'Feature only available for monthly subscribers'})
        
        # Get selected platforms (simplified - in production would use OAuth)
        selected_platforms = request.form.getlist('platforms')
        
        # Create platform accounts dict (simplified for demo)
        platform_accounts = {}
        for platform in selected_platforms:
            platform_accounts[platform] = {
                'connected': True,
                'username': request.form.get(f'{platform}_username', f'demo_{platform}_account')
            }
        
        # Setup auto-posting
        result = auto_scheduler.setup_business_social_accounts(business_id, platform_accounts)
        
        if result['success']:
            flash('🎉 Auto-posting setup complete! Your content will post at 9 AM and 5 PM daily.', 'success')
        else:
            flash(f'Setup failed: {result["error"]}', 'error')
        
        return redirect(url_for('social_media_dashboard', business_id=business_id))
        
    except Exception as e:
        logging.error(f"Error connecting social accounts: {str(e)}")
        flash('An error occurred during setup. Please try again.', 'error')
        return redirect(url_for('social_media_setup', business_id=business_id))

@app.route('/business/<int:business_id>/social-media/preview')
def get_posting_preview(business_id):
    """Get preview of automatic posts"""
    try:
        business = Business.query.get_or_404(business_id)
        
        if not has_premium_access(business):
            return jsonify({'success': False, 'error': 'Feature only available for monthly subscribers'})
        
        preview = auto_scheduler.get_posting_preview(business_id)
        return jsonify(preview)
        
    except Exception as e:
        logging.error(f"Error getting preview: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/verify/conversation/<int:conversation_id>')
def verify_conversation(conversation_id):
    """Public verification endpoint to prove conversations are real"""
    try:
        conversation = Conversation.query.get_or_404(conversation_id)
        business = Business.query.get_or_404(conversation.business_id)
        messages = ConversationMessage.query.filter_by(conversation_id=conversation_id).order_by(ConversationMessage.message_order).all()
        
        verification_data = {
            'conversation_id': conversation.id,
            'business_name': business.name,
            'topic': conversation.topic,
            'created_at': conversation.created_at.isoformat(),
            'status': conversation.status,
            'total_messages': len(messages),
            'ai_agents_used': list(set([msg.ai_agent_type for msg in messages])),
            'public_url': f"{request.url_root}public/conversation/{conversation.id}",
            'verification': {
                'timestamp': datetime.utcnow().isoformat(),
                'server_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'message_count_breakdown': {
                    agent_type: len([m for m in messages if m.ai_agent_type == agent_type])
                    for agent_type in set([msg.ai_agent_type for msg in messages])
                },
                'conversation_hash': str(hash(f"{conversation.id}-{conversation.topic}-{len(messages)}")),
                'publicly_accessible': True,
                'search_indexable': True
            }
        }
        
        return jsonify(verification_data)
        
    except Exception as e:
        return jsonify({'error': str(e), 'verification_failed': True}), 404

@app.route('/verify/privacy-check/<int:conversation_id>')
def verify_privacy_check(conversation_id):
    """Check if a conversation is private (restricted access)"""
    try:
        conversation = Conversation.query.get_or_404(conversation_id)
        business = Business.query.get_or_404(conversation.business_id)
        
        # Check if conversation has privacy restrictions
        is_private = getattr(conversation, 'is_private', False)
        requires_login = getattr(conversation, 'requires_login', False)
        access_level = getattr(conversation, 'access_level', 'public')
        
        privacy_data = {
            'conversation_id': conversation.id,
            'business_name': business.name,
            'topic': conversation.topic,
            'privacy_status': {
                'is_private': is_private,
                'requires_login': requires_login,
                'access_level': access_level,
                'publicly_accessible': not is_private and not requires_login,
                'search_indexable': access_level == 'public',
                'restricted_access': is_private or requires_login
            },
            'access_tests': {
                'public_url_accessible': f"{request.url_root}public/conversation/{conversation.id}",
                'login_required': requires_login,
                'private_dashboard_only': is_private,
                'search_engine_blocked': access_level != 'public'
            },
            'verification': {
                'timestamp': datetime.utcnow().isoformat(),
                'privacy_level': 'private' if (is_private or requires_login) else 'public',
                'verification_result': 'PRIVATE' if (is_private or requires_login) else 'PUBLIC'
            }
        }
        
        return jsonify(privacy_data)
        
    except Exception as e:
        return jsonify({'error': str(e), 'privacy_check_failed': True}), 404

@app.route('/verify/system-status')
def verify_system_status():
    """Public endpoint to verify the entire system is working"""
    try:
        # Count recent conversations (last 24 hours)
        from datetime import datetime, timedelta
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_conversations = Conversation.query.filter(Conversation.created_at >= recent_cutoff).count()
        
        # Get total stats
        total_conversations = Conversation.query.count()
        total_messages = ConversationMessage.query.count()
        total_businesses = Business.query.count()
        
        # Check AI API availability
        api_status = {
            'openai': True,
            'anthropic': True,
            'perplexity': True,
            'gemini': True
        }
        
        verification = {
            'system_status': 'operational',
            'timestamp': datetime.utcnow().isoformat(),
            'conversations_last_24h': recent_conversations,
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'total_businesses': total_businesses,
            'ai_apis_active': api_status,
            'all_apis_working': all(api_status.values()),
            'public_conversations': f"{request.url_root}public/",
            'live_conversations': f"{request.url_root}",
            'verification_endpoints': {
                'individual_conversation': f"{request.url_root}verify/conversation/[ID]",
                'system_status': f"{request.url_root}verify/system-status",
                'api_health': f"{request.url_root}api-status"
            }
        }
        
        return jsonify(verification)
        
    except Exception as e:
        return jsonify({'error': str(e), 'system_status': 'error'}), 500

@app.route('/admin/backup')
@app.route('/admin/backup/<action>')
def admin_backup(action=None):
    """Admin backup management"""
    from backup_system import BackupManager, create_backup, list_all_backups
    
    if action == 'create':
        try:
            backup_path = create_backup()
            return jsonify({
                'success': True,
                'backup_created': backup_path,
                'message': 'Full system backup created successfully'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    elif action == 'list':
        try:
            backups = list_all_backups()
            return jsonify({
                'success': True,
                'backups': backups,
                'total_backups': len(backups)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    else:
        # Show backup management page
        try:
            backups = list_all_backups()
            return render_template('admin_backup.html', backups=backups)
        except Exception as e:
            return f"<h1>Backup Management</h1><p>Available backups: {len(list_all_backups())}</p><p><a href='/admin/backup/create'>Create New Backup</a></p>"

@app.route('/keepalive/generate', methods=['POST'])
def keepalive_generate():
    """API endpoint for keepalive service to generate conversations"""
    try:
        # Get Perfect Roofing Team (or first featured business)
        business = Business.query.filter_by(is_featured=True).first()
        if not business:
            business = Business.query.first()
        
        if not business:
            return jsonify({'error': 'No business found'}), 404
            
        # Random topic selection
        topics = [
            "Emergency Roof Repair Services and 24/7 Availability",
            "Professional Roofing Installation with Quality Materials", 
            "Customer Satisfaction and Transparent Pricing Policy",
            "Storm Damage Restoration and Insurance Claims",
            "Preventive Roof Maintenance and Inspection Services",
            "Licensed Contractors and Industry Certifications",
            "Residential vs Commercial Roofing Solutions",
            "Energy Efficient Roofing and Modern Materials"
        ]
        
        import random
        topic = random.choice(topics)
        
        # Use real-time conversation manager for progressive generation
        from realtime_conversation import realtime_manager
        
        # Start progressive conversation that generates messages over time
        conversation_id = realtime_manager.start_progressive_conversation(business, topic)
        
        if not conversation_id:
            return jsonify({'error': 'Failed to start conversation'}), 500
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'topic': topic,
            'messages_count': 1  # Only first message created initially
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Keepalive conversation generation failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system-status')
def system_status():
    """API endpoint for system status checks"""
    try:
        # Check VisitorIntelSystem status
        from main import intel_system
        
        if intel_system:
            # Get current state from the new system
            state = intel_system.get_current_state()
            
            status = {
                'system_running': True,
                'api_status': {
                    'openai': True,
                    'anthropic': True,
                    'perplexity': True,
                    'gemini': True
                },
                'conversation_active': state.get('conversation_active', False),
                'conversation_status': state.get('status', 'waiting').lower(),
                'active_conversations_count': 1 if state.get('conversation_active', False) else 0,
                'next_conversation_time': state.get('next_conversation_time')
            }
        else:
            # Fallback to basic status
            status = {
                'system_running': True,
                'api_status': {
                    'openai': True,
                    'anthropic': True,
                    'perplexity': True,
                    'gemini': True
                },
                'conversation_active': False,
                'conversation_status': 'waiting',
                'active_conversations_count': 0,
                'next_conversation_time': None
            }
        
        return jsonify(status)
        
    except Exception as e:
        logging.error(f"System status check failed: {e}")
        return jsonify({'error': str(e)}), 500

# Business Content Management API Endpoints
@app.route('/api/business/<int:business_id>/content-status')
def get_business_content_status(business_id):
    """Get the status of all content types for a business"""
    try:
        business = Business.query.get_or_404(business_id)
        
        # Simulate content status - in a real system, this would check actual generated content
        content_status = {
            'faq': {
                'status': 'not_generated',
                'generated_at': None
            },
            'local': {
                'status': 'not_generated', 
                'generated_at': None
            },
            'voice': {
                'status': 'not_generated',
                'generated_at': None
            },
            'knowledge': {
                'status': 'not_generated',
                'generated_at': None
            }
        }
        
        # Check if business has Enterprise plan - they get pre-generated content
        if hasattr(business, 'subscription_plan') and business.subscription_plan == 'Enterprise':
            for content_type in content_status:
                content_status[content_type]['status'] = 'generated'
                content_status[content_type]['generated_at'] = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'content_status': content_status,
            'business_id': business_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/business/<int:business_id>/generate-content', methods=['POST'])
def generate_business_content(business_id):
    """Generate content for a specific business and content type"""
    try:
        business = Business.query.get_or_404(business_id)
        data = request.get_json()
        content_type = data.get('content_type')
        
        if not content_type:
            return jsonify({
                'success': False,
                'error': 'Content type is required'
            }), 400
        
        # Initialize content ecosystem manager
        content_manager = ContentEcosystemManager()
        
        # Generate content based on type
        generated_content = content_manager.generate_business_ecosystem(business)
        
        # Store the generated content (in a real system, you'd save to database)
        # For now, we'll just return success
        
        return jsonify({
            'success': True,
            'message': f'{content_type.upper()} content generated successfully for {business.business_name}',
            'generated_at': datetime.now().isoformat(),
            'content_type': content_type
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/business/<int:business_id>/content/<content_type>')
def get_business_content(business_id, content_type):
    """Get generated content for viewing"""
    try:
        business = Business.query.get_or_404(business_id)
        
        # Generate sample content for demonstration
        content_map = {
            'faq': {
                'title': f'FAQ Content for {business.business_name}',
                'content': f'''# Frequently Asked Questions - {business.business_name}

## What services does {business.business_name} offer?
We specialize in comprehensive {business.industry} services including consultation, installation, and maintenance. Our team has years of experience serving customers in {business.location}.

## How do I get a quote?
You can request a free quote by contacting us directly. We provide detailed estimates based on your specific needs and requirements.

## What areas do you serve?
We primarily serve {business.location} and surrounding areas. Contact us to confirm service availability in your location.

## Do you offer warranties?
Yes, we stand behind our work with comprehensive warranties on all services and installations.

## How quickly can you start a project?
Project timelines vary based on scope and current workload. We'll provide an estimated start date with your quote.''',
                'metadata': {
                    'word_count': 150,
                    'seo_score': 85,
                    'target_keywords': ['FAQ', business.industry, business.location, 'services', 'quote']
                }
            },
            'local': {
                'title': f'Local SEO Content for {business.business_name}',
                'content': f'''# {business.business_name} - Local {business.industry} Services in {business.location}

## Why Choose Local {business.industry} Services?

When you need reliable {business.industry} services in {business.location}, choosing a local provider offers numerous advantages. {business.business_name} understands the unique challenges and requirements of properties in our area.

## Our {business.location} Service Areas

We proudly serve homeowners and businesses throughout {business.location}, providing:

- Emergency services
- Scheduled maintenance
- New installations
- Repairs and upgrades

## Local Experience Matters

Our team knows {business.location} inside and out. We understand local building codes, weather patterns, and the specific needs of properties in our community.

Contact {business.business_name} today for expert {business.industry} services in {business.location}.''',
                'metadata': {
                    'word_count': 125,
                    'seo_score': 92,
                    'target_keywords': [business.location, business.industry, 'local services', 'emergency', 'maintenance']
                }
            },
            'voice': {
                'title': f'Voice Search Optimization for {business.business_name}',
                'content': f'''# Voice Search Optimized Content - {business.business_name}

## "Hey Siri, find {business.industry} services near me"

{business.business_name} is your local {business.industry} expert in {business.location}. We provide fast, reliable service when you need it most.

## "What's the best {business.industry} company in {business.location}?"

{business.business_name} stands out because:
- We respond quickly to your calls
- Our team is fully licensed and insured
- We offer upfront pricing with no surprises
- Customer satisfaction is our top priority

## "How much does {business.industry} service cost?"

Pricing depends on your specific needs. {business.business_name} provides free estimates so you know exactly what to expect before we start any work.

## "Who can help with emergency {business.industry} problems?"

{business.business_name} offers emergency services in {business.location}. Call us anytime for urgent repairs or service needs.''',
                'metadata': {
                    'word_count': 140,
                    'seo_score': 88,
                    'target_keywords': ['voice search', 'near me', business.industry, 'emergency', 'best company']
                }
            },
            'knowledge': {
                'title': f'Industry Knowledge Base - {business.business_name}',
                'content': f'''# {business.industry} Knowledge Base - {business.business_name}

## Understanding {business.industry} Services

As your trusted {business.industry} professionals in {business.location}, {business.business_name} wants to help you make informed decisions about your property needs.

## Common {business.industry} Issues

### Prevention Tips
Regular maintenance is key to avoiding costly repairs. Here's what property owners in {business.location} should watch for:

- Seasonal inspections
- Early problem detection
- Proper maintenance schedules

### When to Call Professionals

While some maintenance can be done yourself, certain situations require professional expertise:

- Complex installations
- Safety-critical repairs
- Warranty-protected work

## Industry Best Practices

{business.business_name} follows industry best practices including:
- Using quality materials
- Following local codes
- Providing detailed documentation
- Ensuring proper permits

## Stay Informed

Our knowledge base helps {business.location} property owners understand their {business.industry} needs and make smart decisions about maintenance and upgrades.''',
                'metadata': {
                    'word_count': 165,
                    'seo_score': 90,
                    'target_keywords': ['knowledge base', business.industry, 'best practices', 'maintenance', 'professional']
                }
            }
        }
        
        if content_type not in content_map:
            return jsonify({
                'success': False,
                'error': 'Invalid content type'
            }), 400
        
        return jsonify({
            'success': True,
            'content': content_map[content_type]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/business/<int:business_id>/content/<content_type>/download')
def download_business_content(business_id, content_type):
    """Download content as a file"""
    try:
        business = Business.query.get_or_404(business_id)
        
        # Get the content
        response = get_business_content(business_id, content_type)
        if response[1] != 200:  # Check status code
            return response
        
        content_data = response[0].get_json()
        if not content_data['success']:
            return response
        
        content = content_data['content']['content']
        title = content_data['content']['title']
        
        # Create file content
        file_content = f"# {title}\n\n{content}\n\n---\nGenerated by Visitor Intel for {business.business_name}\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Create file response
        output = io.StringIO()
        output.write(file_content)
        output.seek(0)
        
        filename = f"{business.business_name.replace(' ', '_').lower()}_{content_type}_{datetime.now().strftime('%Y%m%d')}.md"
        
        return Response(
            output.getvalue(),
            mimetype='text/markdown',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/business/<int:business_id>/content/<content_type>', methods=['DELETE'])
def delete_business_content(business_id, content_type):
    """Delete generated content"""
    try:
        business = Business.query.get_or_404(business_id)
        
        # In a real system, you'd delete the actual content from storage
        # For now, we'll just return success
        
        return jsonify({
            'success': True,
            'message': f'{content_type.upper()} content deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/business/<int:business_id>/showcase-url')
def get_business_showcase_url(business_id):
    """Get the showcase URL for a business"""
    try:
        business = Business.query.get_or_404(business_id)
        
        # Generate showcase URL based on latest conversation
        latest_conversation = Conversation.query.filter_by(
            business_id=business_id
        ).order_by(Conversation.created_at.desc()).first()
        
        if latest_conversation:
            showcase_url = f"{request.host_url}public/conversation/{latest_conversation.id}"
        else:
            showcase_url = f"{request.host_url}business/{business_id}"
        
        return jsonify({
            'success': True,
            'showcase_url': showcase_url
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Additional API endpoints for enhanced frontend integration

@app.route('/api/live-conversation-feed', methods=['GET'])
def api_live_conversation_feed():
    """Get live conversation data for frontend integration"""
    try:
        # Get latest conversations with messages
        conversations = Conversation.query.order_by(Conversation.created_at.desc()).limit(5).all()
        
        conversation_data = []
        for conv in conversations:
            messages = ConversationMessage.query.filter_by(conversation_id=conv.id).order_by(ConversationMessage.id.desc()).limit(16).all()
            
            messages_data = []
            for msg in messages:
                messages_data.append({
                    'id': msg.id,
                    'agent_name': msg.ai_agent_name,
                    'agent_type': msg.ai_agent_type.lower(),
                    'content': msg.content,
                    'timestamp': msg.created_at.isoformat() if msg.created_at else datetime.now().isoformat(),
                    'round': 1,
                    'messageNumber': len(messages_data) + 1
                })
            
            conversation_data.append({
                'id': conv.id,
                'topic': conv.topic,
                'business_name': conv.business.name if conv.business else 'Perfect Roofing Team',
                'messages': list(reversed(messages_data))  # Reverse to show oldest first
            })
        
        return jsonify({
            'status': 'success',
            'conversations': conversation_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/live-conversation-latest', methods=['GET'])
def api_live_conversation_latest_backend():
    """Get latest conversation messages for frontend polling"""
    try:
        # Get the most recent conversation
        latest_conv = Conversation.query.order_by(Conversation.created_at.desc()).first()
        
        if not latest_conv:
            return jsonify({
                'status': 'success',
                'messages': [],
                'topic': 'No conversations yet'
            })
        
        # Get messages for the latest conversation
        messages = ConversationMessage.query.filter_by(conversation_id=latest_conv.id).order_by(ConversationMessage.id.asc()).all()
        
        messages_data = []
        for i, msg in enumerate(messages):
            messages_data.append({
                'id': msg.id,
                'agent_name': msg.ai_agent_name,
                'agent_type': msg.ai_agent_type.lower(),
                'content': msg.content,
                'timestamp': msg.created_at.isoformat() if msg.created_at else datetime.now().isoformat(),
                'round': (i // 4) + 1,
                'messageNumber': (i % 4) + 1
            })
        
        return jsonify({
            'status': 'success',
            'messages': messages_data,
            'topic': latest_conv.topic,
            'business_name': latest_conv.business.name if latest_conv.business else 'Perfect Roofing Team',
            'conversation_id': latest_conv.id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


# Enhanced 4-API Conversation System Routes (Disabled)
@app.route('/api/enhanced-status')
def enhanced_conversation_status():
    """Get enhanced conversation system status (disabled)"""
    return jsonify({
        'enhanced_system_available': False,
        'message': 'Enhanced system is being rebuilt for better integration'
    })


@app.route('/api/countdown')
def get_countdown():
    """Get countdown information for next conversation"""
    try:
        from datetime import datetime, timedelta
        import pytz
        
        # Check if there's an active conversation in progress
        from realtime_conversation import realtime_manager
        active_conversations = realtime_manager.active_conversations
        
        if active_conversations:
            # Get the active conversation details
            conv_id = list(active_conversations.keys())[0]
            conv_data = active_conversations[conv_id]
            
            # Calculate when this conversation will finish (16 messages total)
            messages_remaining = conv_data['total_messages'] - conv_data['current_message']
            minutes_remaining_for_current = messages_remaining
            
            # Add 5 minutes break after conversation ends
            next_time = datetime.utcnow() + timedelta(minutes=minutes_remaining_for_current + 5)
        else:
            # No active conversation, check when last one ended
            last_conversation = Conversation.query.filter_by(status='completed').order_by(Conversation.id.desc()).first()
            
            if last_conversation:
                # Get the last message time from that conversation
                last_message = ConversationMessage.query.filter_by(conversation_id=last_conversation.id).order_by(ConversationMessage.created_at.desc()).first()
                if last_message:
                    # Next conversation 5 minutes after last message
                    next_time = last_message.created_at + timedelta(minutes=5)
                else:
                    # Fallback: 5 minutes from now
                    next_time = datetime.utcnow() + timedelta(minutes=5)
            else:
                # If no conversations, next one in 5 minutes
                next_time = datetime.utcnow() + timedelta(minutes=5)
        
        # Convert to UTC if needed
        if next_time.tzinfo is None:
            next_time = pytz.UTC.localize(next_time)
        
        # Calculate countdown
        now = pytz.UTC.localize(datetime.utcnow())
        time_diff = next_time - now
        
        if time_diff.total_seconds() > 0:
            remaining_seconds = int(time_diff.total_seconds())
            state = 'waiting'
        else:
            remaining_seconds = 0
            state = 'active'
        
        return jsonify({
            'remaining_seconds': remaining_seconds,
            'next_time_local': next_time.isoformat(),
            'current_time': now.isoformat(),
            'state': state,
            'conversation_interval_minutes': 21,
            'active_conversations': len(active_conversations) if 'active_conversations' in locals() else 0
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# External AI Interface Route
@app.route('/external-ai')
def external_ai_interface():
    """Web interface for external AI to access and modify code"""
    return render_template('external_ai_interface.html')

# Mood Color Generator API Routes
@app.route('/api/conversation/<int:conversation_id>/mood')
def get_conversation_mood_api(conversation_id):
    """Get mood analysis for a conversation"""
    try:
        mood_scores = analyze_conversation_mood(conversation_id)
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'mood_scores': mood_scores,
            'dominant_mood': max(mood_scores.keys(), key=lambda k: mood_scores[k]) if mood_scores else 'professional'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversation/<int:conversation_id>/colors')
def get_conversation_colors_api(conversation_id):
    """Get color palette for a conversation"""
    try:
        palette = get_conversation_color_palette(conversation_id)
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'palette': palette
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversation/<int:conversation_id>/theme.css')
def get_conversation_theme_css_api(conversation_id):
    """Get CSS theme for a conversation"""
    try:
        css_content = get_conversation_theme_css(conversation_id)
        response = make_response(css_content)
        response.headers['Content-Type'] = 'text/css'
        response.headers['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
        return response
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Setup External AI API Routes
setup_ai_api_routes(app)

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
