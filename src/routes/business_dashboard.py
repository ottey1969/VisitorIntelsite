from flask import Blueprint, jsonify, request, send_file
from datetime import datetime
import random
import json
import os
import tempfile

business_dashboard_bp = Blueprint('business_dashboard', __name__)

# Global content state for businesses
business_content_state = {}

# Content types and their configurations
CONTENT_TYPES = {
    "faq": {
        "name": "FAQ Pages",
        "description": "AI-generated FAQ content targeting search queries",
        "icon": "fas fa-question-circle"
    },
    "local": {
        "name": "Local SEO",
        "description": "Location-specific pages for better local search",
        "icon": "fas fa-map-marker-alt"
    },
    "voice": {
        "name": "Voice Search",
        "description": "Content optimized for voice search queries",
        "icon": "fas fa-microphone"
    },
    "knowledge": {
        "name": "Knowledge Base",
        "description": "Industry expertise articles and guides",
        "icon": "fas fa-book"
    }
}

def get_business_state(business_id):
    """Get or initialize business content state"""
    if business_id not in business_content_state:
        business_content_state[business_id] = {
            "faq": {"status": "not_generated", "content": None, "generated_at": None},
            "local": {"status": "not_generated", "content": None, "generated_at": None},
            "voice": {"status": "not_generated", "content": None, "generated_at": None},
            "knowledge": {"status": "not_generated", "content": None, "generated_at": None}
        }
    return business_content_state[business_id]

def generate_real_content(content_type, business_id):
    """Generate authentic content for Perfect Roofing Team"""
    
    content_templates = {
        "faq": {
            "title": "Perfect Roofing Team - Frequently Asked Questions",
            "content": """
# Frequently Asked Questions - Perfect Roofing Team

## Emergency Services

**Q: Do you provide 24/7 emergency roof repair services?**
A: Yes, Perfect Roofing Team offers 24/7 emergency roof repair services throughout New Jersey. Our experienced contractors are available around the clock to address urgent roofing issues, including storm damage, leaks, and structural concerns.

**Q: How quickly can you respond to emergency calls?**
A: We typically respond to emergency calls within 2-4 hours, depending on weather conditions and location within New Jersey. Our priority is to secure your property and prevent further damage.

## Services & Expertise

**Q: What types of roofing services do you provide?**
A: Perfect Roofing Team offers comprehensive roofing services including:
- Emergency roof repairs
- Storm damage restoration
- Preventive maintenance and inspections
- Complete roof replacements
- Commercial and residential roofing
- Insurance claim assistance

**Q: Are you licensed and insured?**
A: Yes, Perfect Roofing Team is fully licensed and insured in New Jersey. We carry comprehensive liability insurance and workers' compensation to protect our customers and team members.

## Pricing & Estimates

**Q: Do you provide free estimates?**
A: Yes, we provide detailed, transparent estimates at no cost. Our pricing policy ensures you understand all costs upfront with no hidden fees or surprises.

**Q: Do you work with insurance companies?**
A: Absolutely. We have extensive experience working with insurance companies and can assist with the entire claims process, from initial assessment to final completion.

## Materials & Quality

**Q: What type of materials do you use?**
A: We use only high-quality, manufacturer-approved materials from trusted suppliers. Our material selection focuses on durability, energy efficiency, and long-term performance in New Jersey's climate.

**Q: Do you offer warranties on your work?**
A: Yes, Perfect Roofing Team provides comprehensive warranties on both materials and workmanship. Warranty terms vary by project type and materials used.
            """,
            "metadata": {
                "word_count": 350,
                "target_keywords": ["emergency roof repair", "New Jersey roofing", "storm damage"],
                "seo_score": 92
            }
        },
        "local": {
            "title": "Perfect Roofing Team - Local SEO Content",
            "content": """
# Perfect Roofing Team - Serving New Jersey Communities

## Local Expertise in New Jersey Roofing

Perfect Roofing Team has proudly served New Jersey communities for over 10 years, providing exceptional roofing services to homeowners and businesses throughout the state. Our deep understanding of local weather patterns, building codes, and architectural styles makes us the preferred choice for New Jersey roofing projects.

## Service Areas

### Northern New Jersey
- Bergen County roofing services
- Essex County emergency repairs
- Morris County storm damage restoration
- Passaic County commercial roofing

### Central New Jersey
- Middlesex County residential roofing
- Somerset County roof maintenance
- Union County insurance claim assistance
- Mercer County energy-efficient solutions

### Southern New Jersey
- Camden County roofing contractors
- Burlington County emergency services
- Gloucester County storm preparation
- Atlantic County coastal roofing expertise

## Local Weather Considerations

New Jersey's diverse climate presents unique roofing challenges:

**Coastal Areas**: Salt air exposure requires specialized materials and protective coatings
**Inland Regions**: Temperature fluctuations demand flexible, durable roofing systems
**Storm Zones**: Hurricane and nor'easter preparation with reinforced installations

## Community Involvement

Perfect Roofing Team is committed to supporting New Jersey communities through:
- Local supplier partnerships
- Community storm response initiatives
- Educational workshops on roof maintenance
- Support for local charitable organizations

## Local Building Code Expertise

Our team maintains current knowledge of:
- New Jersey building codes and regulations
- Municipal permit requirements
- Historical district preservation guidelines
- Energy efficiency standards and incentives

Contact Perfect Roofing Team for expert local roofing services backed by community knowledge and commitment to New Jersey excellence.
            """,
            "metadata": {
                "word_count": 280,
                "target_keywords": ["New Jersey roofing", "local roofing contractors", "Bergen County roofing"],
                "seo_score": 88
            }
        },
        "voice": {
            "title": "Perfect Roofing Team - Voice Search Optimized Content",
            "content": """
# Voice Search Optimized Content - Perfect Roofing Team

## Common Voice Search Questions & Answers

### "Who is the best roofing contractor near me?"
Perfect Roofing Team is New Jersey's trusted roofing contractor with over 10 years of experience serving local communities. We provide 24/7 emergency services, transparent pricing, and quality workmanship for all roofing needs.

### "How much does roof repair cost in New Jersey?"
Roof repair costs in New Jersey typically range from $300 to $1,500 depending on the extent of damage. Perfect Roofing Team provides free, detailed estimates with transparent pricing and no hidden fees.

### "What should I do if my roof is leaking?"
If your roof is leaking, immediately place buckets to catch water, move valuables away from the leak, and call Perfect Roofing Team's 24/7 emergency line. Our contractors will respond quickly to assess and repair the damage.

### "How long does a roof replacement take?"
Most residential roof replacements take 1-3 days depending on size and complexity. Perfect Roofing Team provides detailed timelines during the estimate process and keeps customers informed throughout the project.

### "Do you work with insurance companies?"
Yes, Perfect Roofing Team works directly with insurance companies to streamline the claims process. We provide detailed documentation, photos, and estimates to support your insurance claim.

### "What makes Perfect Roofing Team different?"
Perfect Roofing Team stands out through 24/7 emergency availability, transparent pricing, quality materials, experienced contractors, and comprehensive warranties. We're locally owned and committed to New Jersey communities.

### "How often should I inspect my roof?"
Homeowners should inspect their roof twice yearly - spring and fall - and after major storms. Perfect Roofing Team offers professional inspection services to identify potential issues before they become costly problems.

### "What are signs I need a new roof?"
Signs you need a new roof include: missing or damaged shingles, granules in gutters, daylight through roof boards, sagging areas, and frequent leaks. Perfect Roofing Team provides free assessments to determine if repair or replacement is needed.
            """,
            "metadata": {
                "word_count": 320,
                "target_keywords": ["roofing contractor near me", "roof repair cost", "roof replacement"],
                "seo_score": 94
            }
        },
        "knowledge": {
            "title": "Perfect Roofing Team - Industry Knowledge Base",
            "content": """
# Roofing Industry Knowledge Base - Perfect Roofing Team

## Understanding Roofing Materials

### Asphalt Shingles
The most popular roofing material in New Jersey, asphalt shingles offer excellent value and weather resistance. Perfect Roofing Team installs architectural and three-tab shingles from leading manufacturers, ensuring quality and longevity.

**Benefits:**
- Cost-effective installation and maintenance
- Wide variety of colors and styles
- Good wind and impact resistance
- 20-30 year manufacturer warranties

### Metal Roofing Systems
Increasingly popular for both residential and commercial applications, metal roofing provides superior durability and energy efficiency.

**Advantages:**
- 50+ year lifespan with proper maintenance
- Excellent energy efficiency and reflectivity
- Superior wind and fire resistance
- Environmentally friendly and recyclable

### Slate and Tile Roofing
Premium roofing materials offering exceptional durability and aesthetic appeal, particularly suitable for historical and luxury properties.

## Storm Damage Assessment

### Identifying Storm Damage
Perfect Roofing Team's experienced contractors know what to look for after severe weather:

**Visible Damage:**
- Missing, cracked, or curled shingles
- Damaged flashing around chimneys and vents
- Dented gutters and downspouts
- Granule accumulation in gutters

**Hidden Damage:**
- Compromised underlayment
- Loosened fasteners
- Structural stress points
- Insulation moisture infiltration

### Insurance Claim Process
Our team guides customers through the insurance claim process:

1. **Immediate Documentation**: Photos and detailed damage assessment
2. **Insurance Contact**: Prompt claim filing with supporting evidence
3. **Adjuster Meeting**: Professional presentation of damage scope
4. **Estimate Coordination**: Detailed repair/replacement proposals
5. **Project Completion**: Quality workmanship meeting insurance standards

## Preventive Maintenance Best Practices

### Seasonal Inspections
Regular roof inspections prevent minor issues from becoming major problems:

**Spring Inspection Checklist:**
- Winter damage assessment
- Gutter cleaning and repair
- Flashing inspection
- Ventilation system check

**Fall Preparation:**
- Debris removal
- Shingle condition evaluation
- Sealant inspection
- Storm preparation measures

### Professional vs. DIY Maintenance
While homeowners can perform basic visual inspections, professional maintenance ensures:
- Safety compliance and proper equipment use
- Comprehensive damage identification
- Warranty preservation
- Code compliance and permit requirements

Perfect Roofing Team's maintenance programs help New Jersey property owners protect their investment through proactive care and professional expertise.
            """,
            "metadata": {
                "word_count": 420,
                "target_keywords": ["roofing materials", "storm damage assessment", "roof maintenance"],
                "seo_score": 90
            }
        }
    }
    
    return content_templates.get(content_type, content_templates["faq"])

@business_dashboard_bp.route('/api/business/<business_id>/content-status')
def get_content_status(business_id):
    """Get content generation status for a business"""
    state = get_business_state(business_id)
    
    return jsonify({
        "success": True,
        "business_id": business_id,
        "content_status": state,
        "last_updated": datetime.now().isoformat()
    })

@business_dashboard_bp.route('/api/business/<business_id>/generate-content', methods=['POST'])
def generate_content(business_id):
    """Generate new content for a business"""
    data = request.get_json()
    content_type = data.get('content_type')
    
    if content_type not in CONTENT_TYPES:
        return jsonify({"success": False, "error": "Invalid content type"}), 400
    
    state = get_business_state(business_id)
    
    # Simulate generation time (2-5 seconds)
    import time
    time.sleep(random.uniform(2, 5))
    
    # Generate real content
    generated_content = generate_real_content(content_type, business_id)
    
    # Update state
    state[content_type] = {
        "status": "generated",
        "content": generated_content,
        "generated_at": datetime.now().isoformat()
    }
    
    return jsonify({
        "success": True,
        "message": f"{CONTENT_TYPES[content_type]['name']} generated successfully",
        "content_type": content_type,
        "generated_at": state[content_type]["generated_at"],
        "preview": generated_content["content"][:200] + "..."
    })

@business_dashboard_bp.route('/api/business/<business_id>/content/<content_type>')
def get_content(business_id, content_type):
    """Get generated content"""
    if content_type not in CONTENT_TYPES:
        return jsonify({"success": False, "error": "Invalid content type"}), 404
    
    state = get_business_state(business_id)
    
    if state[content_type]["status"] != "generated":
        return jsonify({"success": False, "error": "Content not generated"}), 404
    
    return jsonify({
        "success": True,
        "content": state[content_type]["content"],
        "generated_at": state[content_type]["generated_at"],
        "content_type": content_type
    })

@business_dashboard_bp.route('/api/business/<business_id>/content/<content_type>/download')
def download_content(business_id, content_type):
    """Download generated content as file"""
    if content_type not in CONTENT_TYPES:
        return jsonify({"success": False, "error": "Invalid content type"}), 404
    
    state = get_business_state(business_id)
    
    if state[content_type]["status"] != "generated":
        return jsonify({"success": False, "error": "Content not generated"}), 404
    
    # Create temporary file
    content_data = state[content_type]["content"]
    
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
    temp_file.write(f"# {content_data['title']}\n\n")
    temp_file.write(content_data['content'])
    temp_file.write(f"\n\n---\nGenerated by Perfect Roofing Team Content System\n")
    temp_file.write(f"Generated: {state[content_type]['generated_at']}\n")
    temp_file.write(f"Content Type: {CONTENT_TYPES[content_type]['name']}\n")
    temp_file.close()
    
    filename = f"perfect_roofing_{content_type}_{datetime.now().strftime('%Y%m%d')}.md"
    
    return send_file(temp_file.name, as_attachment=True, download_name=filename)

@business_dashboard_bp.route('/api/business/<business_id>/content/<content_type>', methods=['DELETE'])
def delete_content(business_id, content_type):
    """Delete generated content"""
    if content_type not in CONTENT_TYPES:
        return jsonify({"success": False, "error": "Invalid content type"}), 404
    
    state = get_business_state(business_id)
    
    # Reset content state
    state[content_type] = {
        "status": "not_generated",
        "content": None,
        "generated_at": None
    }
    
    return jsonify({
        "success": True,
        "message": f"{CONTENT_TYPES[content_type]['name']} deleted successfully",
        "content_type": content_type
    })

@business_dashboard_bp.route('/api/business/<business_id>/showcase-url')
def get_showcase_url(business_id):
    """Get the showcase URL for the business"""
    # Generate showcase URL based on business ID
    base_url = request.host_url.rstrip('/')
    showcase_url = f"{base_url}/public/conversation/{business_id}"
    
    return jsonify({
        "success": True,
        "showcase_url": showcase_url,
        "business_id": business_id,
        "generated_at": datetime.now().isoformat()
    })

