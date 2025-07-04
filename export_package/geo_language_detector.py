"""
Automatic Geographic and Language Detection System
Detects user location via IP and automatically adapts language, currency, and business context
"""

import requests
import logging
from typing import Dict, Optional, Tuple
from flask import request
import json

class GeoLanguageDetector:
    """Detects user location and automatically adapts the platform"""
    
    def __init__(self):
        self.country_configs = {
            'NL': {
                'language': 'Dutch',
                'language_code': 'nl',
                'currency': 'EUR',
                'timezone': 'Europe/Amsterdam',
                'business_culture': 'direct_efficient',
                'popular_platforms': ['LinkedIn', 'Facebook', 'Instagram'],
                'business_hours': '9:00-17:00',
                'vat_required': True,
                'payment_methods': ['PayPal', 'iDEAL', 'Stripe'],
                'date_format': 'DD-MM-YYYY',
                'business_registration': 'KvK number'
            },
            'DE': {
                'language': 'German',
                'language_code': 'de',
                'currency': 'EUR',
                'timezone': 'Europe/Berlin',
                'business_culture': 'formal_detailed',
                'popular_platforms': ['LinkedIn', 'XING', 'Facebook'],
                'business_hours': '8:00-17:00',
                'vat_required': True,
                'payment_methods': ['PayPal', 'SEPA', 'Stripe'],
                'date_format': 'DD.MM.YYYY',
                'business_registration': 'Handelsregisternummer'
            },
            'FR': {
                'language': 'French',
                'language_code': 'fr',
                'currency': 'EUR',
                'timezone': 'Europe/Paris',
                'business_culture': 'formal_relationship',
                'popular_platforms': ['LinkedIn', 'Facebook', 'Instagram'],
                'business_hours': '9:00-18:00',
                'vat_required': True,
                'payment_methods': ['PayPal', 'CB', 'Stripe'],
                'date_format': 'DD/MM/YYYY',
                'business_registration': 'SIRET number'
            },
            'GB': {
                'language': 'English',
                'language_code': 'en-GB',
                'currency': 'GBP',
                'timezone': 'Europe/London',
                'business_culture': 'polite_professional',
                'popular_platforms': ['LinkedIn', 'Facebook', 'Twitter'],
                'business_hours': '9:00-17:00',
                'vat_required': True,
                'payment_methods': ['PayPal', 'Stripe', 'Bank Transfer'],
                'date_format': 'DD/MM/YYYY',
                'business_registration': 'Companies House number'
            },
            'US': {
                'language': 'English',
                'language_code': 'en-US',
                'currency': 'USD',
                'timezone': 'America/New_York',  # Default to Eastern
                'business_culture': 'friendly_efficient',
                'popular_platforms': ['LinkedIn', 'Facebook', 'Instagram', 'Twitter'],
                'business_hours': '9:00-17:00',
                'vat_required': False,
                'payment_methods': ['PayPal', 'Stripe', 'Venmo'],
                'date_format': 'MM/DD/YYYY',
                'business_registration': 'EIN number'
            }
        }
    
    def detect_country_from_ip(self, ip_address: str = None) -> Optional[str]:
        """Detect country from IP address"""
        try:
            if not ip_address:
                ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
            
            # Skip localhost/private IPs in development
            if ip_address in ['127.0.0.1', 'localhost'] or ip_address.startswith('192.168.') or ip_address.startswith('10.'):
                return None
            
            # Use a free IP geolocation service
            response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return data.get('countryCode')
                    
        except Exception as e:
            logging.warning(f"IP detection failed: {e}")
            return None
    
    def get_localized_config(self, country_code: str = None) -> Dict:
        """Get localized configuration for a country"""
        if not country_code:
            country_code = self.detect_country_from_ip()
        
        # Default to US if detection fails
        if country_code not in self.country_configs:
            country_code = 'US'
            
        config = self.country_configs[country_code].copy()
        config['country_code'] = country_code
        
        return config
    
    def translate_ai_prompt(self, prompt: str, target_language: str, business_context: str = None) -> str:
        """Translate and localize AI prompts for different countries"""
        
        # Language-specific business contexts
        cultural_adaptations = {
            'Dutch': {
                'style': 'Be direct, practical, and focus on efficiency. Use "je/jij" for informal tone.',
                'business_focus': 'Emphasize sustainability, energy efficiency, and practical solutions.',
                'local_refs': 'Reference Dutch building codes, seasonal weather patterns, and local suppliers.'
            },
            'German': {
                'style': 'Be thorough, detailed, and technically precise. Use formal "Sie" address.',
                'business_focus': 'Emphasize quality, engineering excellence, and regulatory compliance.',
                'local_refs': 'Reference German standards (DIN), Handwerk traditions, and regional practices.'
            },
            'French': {
                'style': 'Be polite, relationship-focused, and culturally sensitive.',
                'business_focus': 'Emphasize craftsmanship, aesthetics, and customer relationships.',
                'local_refs': 'Reference French regulations, regional variations, and local artisan traditions.'
            },
            'English': {
                'style': 'Be friendly, professional, and solution-oriented.',
                'business_focus': 'Emphasize value, customer service, and practical benefits.',
                'local_refs': 'Use local examples and industry standards relevant to the region.'
            }
        }
        
        if target_language in cultural_adaptations:
            adaptation = cultural_adaptations[target_language]
            
            enhanced_prompt = f"""
{prompt}

IMPORTANT LOCALIZATION INSTRUCTIONS:
- Respond entirely in {target_language}
- Communication style: {adaptation['style']}
- Business focus: {adaptation['business_focus']}
- Local context: {adaptation['local_refs']}
{f"- Business context: {business_context}" if business_context else ""}

Generate authentic, culturally appropriate content that resonates with local business practices and customer expectations.
"""
            return enhanced_prompt
        
        return prompt
    
    def format_price_for_country(self, usd_price: float, country_config: Dict) -> str:
        """Format price according to local currency and conventions"""
        
        # Simple currency conversion (in production, use real exchange rates)
        currency_rates = {
            'EUR': 0.85,  # USD to EUR
            'GBP': 0.75,  # USD to GBP
            'USD': 1.0
        }
        
        currency = country_config['currency']
        rate = currency_rates.get(currency, 1.0)
        local_price = usd_price * rate
        
        # Format according to local conventions
        if currency == 'EUR':
            return f"€{local_price:.2f}"
        elif currency == 'GBP':
            return f"£{local_price:.2f}"
        else:
            return f"${local_price:.2f}"
    
    def get_localized_business_fields(self, country_config: Dict) -> Dict:
        """Get localized business registration fields"""
        
        fields = {
            'registration_label': country_config.get('business_registration', 'Business Registration'),
            'vat_required': country_config.get('vat_required', False),
            'date_format': country_config.get('date_format', 'MM/DD/YYYY'),
            'timezone': country_config.get('timezone', 'UTC'),
            'business_hours': country_config.get('business_hours', '9:00-17:00'),
            'popular_platforms': country_config.get('popular_platforms', ['LinkedIn', 'Facebook'])
        }
        
        return fields
    
    def auto_detect_and_configure(self) -> Dict:
        """Main function to auto-detect and configure everything"""
        
        # Detect country
        country_code = self.detect_country_from_ip()
        config = self.get_localized_config(country_code)
        
        # Add business fields
        config.update(self.get_localized_business_fields(config))
        
        return config

# Global instance
geo_detector = GeoLanguageDetector()