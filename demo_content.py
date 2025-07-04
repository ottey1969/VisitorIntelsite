#!/usr/bin/env python3
"""Demo the enhanced social media content generation"""

import random

# Professional content templates for roofing businesses
ROOFING_TEMPLATES = {
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
        'location': ['#NewJerseyRoofing', '#LodiRoofing', '#LocalContractors', '#NJHomeImprovement'],
        'quality': ['#LicensedRoofers', '#InsuredContractors', '#WarrantyBacked', '#CertifiedProfessionals']
    }
}

def generate_professional_post(topic="Professional Roofing Installation", business_name="Perfect Roofing Team"):
    """Generate a professional social media post"""
    
    # Get random content elements
    hook = random.choice(ROOFING_TEMPLATES['opening_hooks'])
    value_prop = random.choice(ROOFING_TEMPLATES['value_propositions'])
    cta = random.choice(ROOFING_TEMPLATES['call_to_actions'])
    
    # Build hashtags
    hashtags = []
    hashtags.append(f"#{business_name.replace(' ', '')}")
    hashtags.extend(ROOFING_TEMPLATES['hashtags']['general'])
    hashtags.extend(ROOFING_TEMPLATES['hashtags']['location'])
    hashtags.extend(ROOFING_TEMPLATES['hashtags']['quality'][:2])
    
    hashtag_string = ' '.join(hashtags[:8])
    
    # AI conversation highlight post
    highlight_content = f"""{hook}

💬 "Our AI experts are discussing {topic.lower()} - the latest insights show tremendous value for homeowners!"

✅ {value_prop}
🎯 AI experts discussing {topic.lower()}
⚡ Real-time insights about our services
📞 {cta}

{hashtag_string}"""

    return highlight_content

def generate_summary_post(topic="Professional Roofing Installation", business_name="Perfect Roofing Team"):
    """Generate a conversation summary post"""
    
    hook = random.choice(ROOFING_TEMPLATES['opening_hooks'])
    value_prop = random.choice(ROOFING_TEMPLATES['value_propositions'])
    cta = random.choice(ROOFING_TEMPLATES['call_to_actions'])
    
    hashtags = []
    hashtags.append(f"#{business_name.replace(' ', '')}")
    hashtags.extend(ROOFING_TEMPLATES['hashtags']['general'])
    hashtags.extend(ROOFING_TEMPLATES['hashtags']['quality'])
    
    hashtag_string = ' '.join(hashtags[:8])
    
    summary_content = f"""{hook}

🤖 Latest AI conversation: {topic}
📊 16 expert messages exchanged
👥 4 AI specialists discussing our services
⭐ {value_prop}

Key highlights:
🔧 Professional expertise and quality standards
🏠 Customer-focused service delivery
📈 Industry-leading solutions and results

{cta}

{hashtag_string}"""

    return summary_content

def adapt_for_twitter(content):
    """Adapt content for Twitter's 280 character limit"""
    if len(content) <= 280:
        return content
    
    lines = content.split('\n')
    short_content = []
    short_content.append(lines[0])  # Hook
    
    # Find key content line
    for line in lines[1:]:
        if any(emoji in line for emoji in ['✅', '🎯', '⚡', '📞']) and len(' '.join(short_content + [line])) < 230:
            short_content.append(line)
            break
    
    # Add hashtags
    hashtag_line = next((line for line in reversed(lines) if line.startswith('#')), '')
    if hashtag_line:
        hashtags = hashtag_line.split()[:5]  # Limit hashtags for Twitter
        short_content.append(' '.join(hashtags))
    
    return '\n'.join(short_content)

def demo_enhanced_content():
    """Demonstrate the enhanced content generation"""
    
    print("🚀 ENHANCED SOCIAL MEDIA CONTENT GENERATION DEMO")
    print("=" * 60)
    
    topics = [
        "Emergency Roof Repair Services",
        "Licensed Contractors and Industry Certifications", 
        "Energy Efficient Roofing and Modern Materials"
    ]
    
    for i, topic in enumerate(topics, 1):
        print(f"\n--- DEMO POST {i}: CONVERSATION HIGHLIGHT ---")
        print(f"Topic: {topic}")
        print("-" * 40)
        
        highlight_post = generate_professional_post(topic)
        print(highlight_post)
        print(f"\nLength: {len(highlight_post)} characters")
        
        print(f"\n--- TWITTER ADAPTATION ---")
        twitter_version = adapt_for_twitter(highlight_post)
        print(twitter_version)
        print(f"Length: {len(twitter_version)} characters")
        
        print("\n" + "=" * 60)
    
    print(f"\n--- DEMO POST: CONVERSATION SUMMARY ---")
    print("-" * 40)
    
    summary_post = generate_summary_post("Professional Roofing Installation")
    print(summary_post)
    print(f"\nLength: {len(summary_post)} characters")
    
    print(f"\n--- TWITTER ADAPTATION ---")
    twitter_summary = adapt_for_twitter(summary_post)
    print(twitter_summary)
    print(f"Length: {len(twitter_summary)} characters")
    
    print("\n" + "=" * 60)
    print("✅ Enhanced content features:")
    print("• Professional industry-specific templates")
    print("• Varied hooks, value props, and CTAs to prevent repetition")
    print("• Strategic emoji usage for engagement")
    print("• Location-specific and quality-focused hashtags")
    print("• Platform-specific optimization (Twitter, LinkedIn, etc.)")
    print("• Perfect spelling and grammar")
    print("• Engaging, authentic content that drives results")

if __name__ == "__main__":
    demo_enhanced_content()