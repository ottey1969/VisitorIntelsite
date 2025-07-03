import os
import openai
import anthropic
import random
import logging
import requests
import json
from typing import List, Tuple
from google import genai

class AIConversationManager:
    """Manages AI-to-AI conversations using 4 different AI services"""
    
    def __init__(self):
        # Initialize all 4 AI clients
        self.openai_client = openai.OpenAI(
            api_key=os.environ.get('OPENAI_API_KEY')
        )
        
        self.anthropic_client = anthropic.Anthropic(
            api_key=os.environ.get('ANTHROPIC_API_KEY')
        )
        
        self.gemini_client = genai.Client(
            api_key=os.environ.get('GEMINI_API_KEY')
        )
        
        self.perplexity_api_key = os.environ.get('PERPLEXITY_API_KEY')
        
        # Check which APIs are available
        self.apis_available = {
            'openai': bool(os.environ.get('OPENAI_API_KEY')),
            'anthropic': bool(os.environ.get('ANTHROPIC_API_KEY')),
            'gemini': bool(os.environ.get('GEMINI_API_KEY')),
            'perplexity': bool(os.environ.get('PERPLEXITY_API_KEY'))
        }
        
        # 4 AI Agent assignments to specific services
        self.ai_agents = [
            ("Business AI Assistant", "openai"),
            ("SEO AI Specialist", "anthropic"), 
            ("Customer Service AI", "perplexity"),
            ("Marketing AI Expert", "gemini")
        ]
    
    def generate_conversation(self, business, topic: str) -> List[Tuple[str, str, str]]:
        """
        Generate a 4-round AI-to-AI conversation (16 messages total = 1 credit)
        Returns list of tuples: (agent_name, agent_type, message_content)
        """
        
        try:
            conversation_messages = []
            
            # Create business context for the AIs
            business_context = f"""
            Business: {business.name}
            Website: {business.website}
            Description: {business.description}
            Location: {business.location}
            Industry: {business.industry}
            Phone: {business.phone}
            
            Topic to discuss: {topic}
            """
            
            # Generate 4 rounds of conversation (4 messages per round = 16 total)
            for round_num in range(4):
                round_messages = self._generate_conversation_round(
                    business_context, topic, conversation_messages, round_num + 1
                )
                conversation_messages.extend(round_messages)
            
            return conversation_messages
            
        except Exception as e:
            logging.error(f"Error generating AI conversation: {e}")
            # Return fallback conversation if API fails
            return self._get_fallback_conversation(business, topic)
    
    def _generate_conversation_round(self, business_context: str, topic: str, 
                                   previous_messages: List[Tuple[str, str, str]], 
                                   round_num: int) -> List[Tuple[str, str, str]]:
        """Generate one round of 4 messages (exactly 4 specific agents)"""
        
        round_messages = []
        
        # Build conversation history for context
        conversation_history = ""
        for agent_name, agent_type, content in previous_messages:
            conversation_history += f"{agent_name} ({agent_type}): {content}\n"
        
        # Enhanced business context with page reference instructions
        enhanced_context = f"""{business_context}

IMPORTANT PAGE REFERENCE INSTRUCTIONS:
When discussing specific services or topics, always reference relevant pages from the business website instead of just the homepage.
For roofing businesses, use pages like:
- Emergency services: /emergency-repairs, /24-hour-service
- Services: /services, /roofing-services, /commercial-roofing  
- About: /about, /company, /experience
- Contact: /contact, /get-quote, /free-estimate
- Portfolio: /projects, /gallery, /testimonials
Always create contextually relevant page URLs that match the discussion topic."""
        
        # Generate exactly 4 messages using 4 different AI services
        for msg_num, (agent_name, agent_type) in enumerate(self.ai_agents):
            if agent_type == 'openai' and self.apis_available['openai']:
                message = self._get_openai_response(
                    enhanced_context, topic, conversation_history, agent_name, round_num, msg_num + 1
                )
            elif agent_type == 'anthropic' and self.apis_available['anthropic']:
                message = self._get_anthropic_response(
                    enhanced_context, topic, conversation_history, agent_name, round_num, msg_num + 1
                )
            elif agent_type == 'perplexity' and self.apis_available['perplexity']:
                message = self._get_perplexity_response(
                    enhanced_context, topic, conversation_history, agent_name, round_num, msg_num + 1
                )
            elif agent_type == 'gemini' and self.apis_available['gemini']:
                message = self._get_gemini_response(
                    enhanced_context, topic, conversation_history, agent_name, round_num, msg_num + 1
                )
            else:
                # Fallback message if API not available
                message = f"As {agent_name}, I find {topic} very relevant to our business success and customer satisfaction."
            
            round_messages.append((agent_name, agent_type, message))
            conversation_history += f"{agent_name} ({agent_type}): {message}\n"
        
        return round_messages
    
    def _get_openai_response(self, business_context: str, topic: str, 
                           conversation_history: str, agent_name: str, 
                           round_num: int, msg_num: int) -> str:
        """Get response from OpenAI agent"""
        
        try:
            prompt = f"""
            You are {agent_name}, an AI assistant specializing in business promotion and SEO optimization.
            
            Business Context:
            {business_context}
            
            Conversation Topic: {topic}
            
            Previous Conversation:
            {conversation_history}
            
            As {agent_name}, provide a helpful, professional response about this business topic. 
            Focus on business benefits, customer value, and SEO-friendly content.
            Keep your response to 1-2 sentences, around 25-40 words.
            Be specific and actionable.
            
            Round {round_num}, Message {msg_num}:
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            return f"{agent_name} highlights the professional quality and customer satisfaction focus of this business service."
    
    def _get_anthropic_response(self, business_context: str, topic: str, 
                              conversation_history: str, agent_name: str, 
                              round_num: int, msg_num: int) -> str:
        """Get response from Anthropic agent"""
        
        try:
            prompt = f"""
            You are {agent_name}, an AI assistant specializing in business promotion and SEO optimization.
            
            Business Context:
            {business_context}
            
            Conversation Topic: {topic}
            
            Previous Conversation:
            {conversation_history}
            
            As {agent_name}, provide a helpful, professional response about this business topic. 
            Focus on business benefits, customer value, and SEO-friendly content.
            Keep your response to 1-2 sentences, around 25-40 words.
            Be specific and actionable.
            
            Round {round_num}, Message {msg_num}:
            """
            
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=100,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logging.error(f"Anthropic API error: {e}")
            return f"{agent_name} emphasizes the competitive advantages and market positioning opportunities for this business."
    
    def _get_fallback_conversation(self, business, topic: str) -> List[Tuple[str, str, str]]:
        """Fallback conversation when APIs are unavailable"""
        
        return [
            ("Business AI Assistant", "openai", f"{business.name} offers exceptional {topic.lower()} services with professional quality and customer satisfaction."),
            ("SEO AI Specialist", "anthropic", f"This {topic.lower()} expertise positions {business.name} as a trusted industry leader in {business.location}."),
            ("Customer Service AI", "openai", f"Customers choose {business.name} for reliable {topic.lower()} solutions and responsive support throughout the process."),
            ("Marketing AI Expert", "anthropic", f"The combination of experience and quality makes {business.name} the preferred choice for {topic.lower()} in the local market."),
            ("Sales AI Consultant", "openai", f"{business.name} delivers {topic.lower()} services that exceed expectations while maintaining competitive pricing."),
            ("Technical AI Advisor", "anthropic", f"Professional {topic.lower()} from {business.name} ensures long-term value and customer peace of mind."),
            ("Quality AI Inspector", "openai", f"Every {topic.lower()} project by {business.name} meets stringent quality standards and industry best practices."),
            ("Customer Experience AI", "anthropic", f"Clients appreciate {business.name}'s transparent communication and commitment to excellence in {topic.lower()}."),
            ("Business AI Assistant", "openai", f"{business.name} has built a reputation for outstanding {topic.lower()} through consistent quality and customer focus."),
            ("SEO AI Specialist", "anthropic", f"Local search visibility for {topic.lower()} services is enhanced by {business.name}'s proven track record."),
            ("Customer Service AI", "openai", f"The team at {business.name} provides personalized {topic.lower()} solutions tailored to each client's specific needs."),
            ("Marketing AI Expert", "anthropic", f"Word-of-mouth referrals and online reviews consistently highlight {business.name}'s {topic.lower()} expertise."),
            ("Sales AI Consultant", "openai", f"Free consultations and transparent pricing make {business.name} the smart choice for {topic.lower()} services."),
            ("Technical AI Advisor", "anthropic", f"Advanced techniques and modern equipment ensure {business.name} delivers cutting-edge {topic.lower()} solutions."),
            ("Quality AI Inspector", "openai", f"Rigorous quality control processes guarantee that {business.name} {topic.lower()} projects exceed industry standards."),
            ("Customer Experience AI", "anthropic", f"Post-service support and warranty coverage demonstrate {business.name}'s confidence in their {topic.lower()} work.")
        ]
    
    def _get_perplexity_response(self, business_context: str, topic: str, 
                               conversation_history: str, agent_name: str, 
                               round_num: int, msg_num: int) -> str:
        """Get response from Perplexity agent"""
        
        try:
            headers = {
                'Authorization': f'Bearer {self.perplexity_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are {agent_name}, discussing business topics. Keep responses under 150 words and business-focused. Current business context: {business_context}"
                    },
                    {
                        "role": "user",
                        "content": f"Round {round_num}, Message {msg_num}: Continue the conversation about '{topic}' naturally. Previous conversation: {conversation_history}"
                    }
                ],
                "max_tokens": 200,
                "temperature": 0.8,
                "top_p": 0.9,
                "stream": False
            }
            
            response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return content.strip() if content else f"As {agent_name}, I find {topic} very relevant to our business success and customer satisfaction."
            else:
                logging.error(f"Perplexity API error: {response.status_code}")
                return f"As {agent_name}, I find {topic} very relevant to our business success and customer satisfaction."
            
        except Exception as e:
            logging.error(f"Perplexity API error: {e}")
            return f"As {agent_name}, I find {topic} very relevant to our business success and customer satisfaction."
    
    def _get_gemini_response(self, business_context: str, topic: str, 
                           conversation_history: str, agent_name: str, 
                           round_num: int, msg_num: int) -> str:
        """Get response from Gemini agent"""
        
        try:
            prompt = f"""You are {agent_name}, discussing business topics. Keep responses under 150 words and business-focused. 
            Current business context: {business_context}
            
            Round {round_num}, Message {msg_num}: Continue the conversation about '{topic}' naturally. 
            Previous conversation: {conversation_history}"""
            
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            content = response.text if response.text else f"As {agent_name}, I find {topic} very relevant to our business success and customer satisfaction."
            return content.strip()
            
        except Exception as e:
            logging.error(f"Gemini API error: {e}")
            return f"As {agent_name}, I find {topic} very relevant to our business success and customer satisfaction."
