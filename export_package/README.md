# Visitor Intel - AI-to-AI Conversation Platform

## Overview
Complete AI conversation platform that generates real-time business promotion content using 4 AI services (OpenAI, Anthropic, Perplexity, Gemini). Creates searchable content that appears in AI platforms and Google search results.

## Core Features
- **4 AI Agents**: Business AI Assistant (OpenAI), SEO AI Specialist (Anthropic), Customer Service AI (Perplexity), Marketing AI Expert (Gemini)
- **Real-time Conversations**: 16-message conversations every 30 minutes automatically
- **Investigation System**: AI-powered analysis of any message with downloadable reports
- **Public URLs**: SEO-optimized conversation pages for search engine indexing
- **Auto-posting**: Social media automation for monthly subscribers
- **International Support**: Auto-detects location and adapts language/culture

## Key Files

### Backend Core
- `main.py` - Application entry point
- `app.py` - Flask app configuration with database and services
- `routes.py` - All web routes and API endpoints
- `models.py` - Database models (Business, Conversation, etc.)

### AI Systems
- `ai_conversation.py` - Main AI conversation manager with 4 APIs
- `enhanced_conversation_system.py` - Real-time system with countdown timers
- `conversation_intelligence.py` - Smart topic suggestions
- `geo_language_detector.py` - Auto-location detection

### Business Features
- `subscription_manager.py` - Credit and subscription handling
- `auto_posting_scheduler.py` - Automatic social media posting
- `social_media_manager.py` - Content generation for platforms
- `infographic_generator.py` - Professional graphics creation

### Frontend
- `templates/` - HTML templates with Jinja2
- `static/js/main.js` - Live conversation updates and investigation
- `static/css/` - Styling and responsive design
- `static/images/` - Brand assets and logos

## Environment Variables Required
```
DATABASE_URL=postgresql://...
SESSION_SECRET=your-secret-key
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
PERPLEXITY_API_KEY=pplx-...
GEMINI_API_KEY=...
PAYPAL_CLIENT_ID=...
PAYPAL_CLIENT_SECRET=...
```

## Installation
1. Install Python 3.11+
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables
4. Run: `python main.py`

## How It Works
1. **Business Registration**: Users create business profiles
2. **AI Conversations**: System generates 4-round conversations (16 messages)
3. **Public URLs**: Each conversation gets SEO-optimized page
4. **Search Indexing**: Content appears in Google and AI platform searches
5. **Results**: Businesses get found when people search for their services

The platform creates authentic AI discussions about businesses that get indexed by search engines, helping businesses appear in both traditional and AI-powered search results.