"""
Monthly Subscription Management System
Handles monthly plans, conversation limits, and billing cycles
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models import Business, Conversation
from app import db


class SubscriptionManager:
    """Manages monthly subscriptions and conversation allowances"""
    
    # Monthly subscription plans
    MONTHLY_PLANS = {
        'monthly_basic': {
            'name': 'Basic Monthly',
            'price': 29.99,
            'conversations_per_month': 10,
            'description': 'Perfect for small businesses getting started with AI conversations',
            'features': ['10 AI conversations/month', 'Basic analytics', 'Email support']
        },
        'monthly_pro': {
            'name': 'Professional Monthly', 
            'price': 79.99,
            'conversations_per_month': 50,
            'description': 'Ideal for growing businesses with regular marketing needs',
            'features': ['50 AI conversations/month', 'Advanced analytics', 'Priority support', 'Custom topics']
        },
        'monthly_enterprise': {
            'name': 'Enterprise Monthly',
            'price': 299.99,
            'conversations_per_month': -1,  # Unlimited
            'description': 'Best for large organizations with unlimited conversation needs',
            'features': ['Unlimited AI conversations', 'Advanced analytics', 'Priority support', 'Custom domain', 'API access']
        }
    }
    
    def __init__(self):
        pass
    
    def upgrade_to_monthly_plan(self, business_id: int, plan_type: str) -> Dict[str, any]:
        """Upgrade a business to a monthly subscription plan"""
        business = Business.query.get(business_id)
        if not business:
            return {'success': False, 'error': 'Business not found'}
        
        if plan_type not in self.MONTHLY_PLANS:
            return {'success': False, 'error': 'Invalid plan type'}
        
        plan = self.MONTHLY_PLANS[plan_type]
        now = datetime.utcnow()
        
        # Update business subscription
        business.subscription_type = plan_type
        business.monthly_conversation_limit = plan['conversations_per_month']
        business.conversations_used_this_month = 0
        business.subscription_start_date = now
        business.subscription_end_date = now + timedelta(days=30)
        business.auto_renew = True
        
        # For enterprise plans, also set unlimited flag
        if plan_type == 'monthly_enterprise':
            business.is_unlimited = True
            business.plan_type = 'enterprise'
        else:
            business.is_unlimited = False
        
        db.session.commit()
        
        return {
            'success': True,
            'plan': plan,
            'next_billing_date': business.subscription_end_date
        }
    
    def check_conversation_allowance(self, business_id: int) -> Dict[str, any]:
        """Check if business can create a new conversation"""
        business = Business.query.get(business_id)
        if not business:
            return {'can_create': False, 'reason': 'Business not found'}
        
        # Reset monthly counter if new billing cycle
        self._reset_monthly_counter_if_needed(business)
        
        # Check allowance based on subscription type
        if business.subscription_type == 'credit':
            # Credit-based system
            if business.is_unlimited or business.credits_remaining > 0:
                return {'can_create': True, 'remaining': business.credits_remaining if not business.is_unlimited else 'unlimited'}
            else:
                return {'can_create': False, 'reason': 'Insufficient credits'}
        
        elif business.subscription_type in self.MONTHLY_PLANS:
            plan = self.MONTHLY_PLANS[business.subscription_type]
            
            # Unlimited plans
            if plan['conversations_per_month'] == -1:
                return {'can_create': True, 'remaining': 'unlimited'}
            
            # Limited monthly plans
            used = business.conversations_used_this_month or 0
            remaining = plan['conversations_per_month'] - used
            
            if remaining > 0:
                return {'can_create': True, 'remaining': remaining}
            else:
                return {'can_create': False, 'reason': f'Monthly limit reached ({plan["conversations_per_month"]} conversations)'}
        
        return {'can_create': False, 'reason': 'Invalid subscription'}
    
    def consume_conversation_allowance(self, business_id: int) -> bool:
        """Consume one conversation from the allowance"""
        business = Business.query.get(business_id)
        if not business:
            return False
        
        allowance_check = self.check_conversation_allowance(business_id)
        if not allowance_check['can_create']:
            return False
        
        # Deduct from appropriate system
        if business.subscription_type == 'credit':
            if not business.is_unlimited and business.credits_remaining > 0:
                business.credits_remaining -= 1
        elif business.subscription_type in self.MONTHLY_PLANS:
            if self.MONTHLY_PLANS[business.subscription_type]['conversations_per_month'] != -1:
                business.conversations_used_this_month = (business.conversations_used_this_month or 0) + 1
        
        db.session.commit()
        return True
    
    def _reset_monthly_counter_if_needed(self, business: Business):
        """Reset monthly conversation counter if billing cycle has renewed"""
        if not business.subscription_end_date:
            return
        
        now = datetime.utcnow()
        
        # If subscription has expired and auto-renew is enabled
        if now > business.subscription_end_date and business.auto_renew:
            business.conversations_used_this_month = 0
            business.subscription_start_date = now
            business.subscription_end_date = now + timedelta(days=30)
            db.session.commit()
    
    def get_subscription_status(self, business_id: int) -> Dict[str, any]:
        """Get detailed subscription status for a business"""
        business = Business.query.get(business_id)
        if not business:
            return {'error': 'Business not found'}
        
        self._reset_monthly_counter_if_needed(business)
        
        status = {
            'business_id': business_id,
            'subscription_type': business.subscription_type,
            'is_active': True
        }
        
        if business.subscription_type == 'credit':
            status.update({
                'system': 'credit-based',
                'credits_remaining': business.credits_remaining,
                'is_unlimited': business.is_unlimited
            })
        elif business.subscription_type in self.MONTHLY_PLANS:
            plan = self.MONTHLY_PLANS[business.subscription_type]
            used = business.conversations_used_this_month or 0
            
            status.update({
                'system': 'monthly-subscription',
                'plan_name': plan['name'],
                'plan_price': plan['price'],
                'conversations_limit': plan['conversations_per_month'],
                'conversations_used': used,
                'conversations_remaining': 'unlimited' if plan['conversations_per_month'] == -1 else plan['conversations_per_month'] - used,
                'billing_cycle_start': business.subscription_start_date,
                'billing_cycle_end': business.subscription_end_date,
                'auto_renew': business.auto_renew,
                'days_until_renewal': (business.subscription_end_date - datetime.utcnow()).days if business.subscription_end_date else None
            })
        
        return status
    
    def get_monthly_plans_for_display(self) -> List[Dict[str, any]]:
        """Get monthly plans formatted for display"""
        plans = []
        
        for plan_id, plan_data in self.MONTHLY_PLANS.items():
            display_plan = {
                'id': plan_id,
                'name': plan_data['name'],
                'price': plan_data['price'],
                'conversations': 'Unlimited' if plan_data['conversations_per_month'] == -1 else f"{plan_data['conversations_per_month']} per month",
                'description': plan_data['description'],
                'features': plan_data['features'],
                'is_popular': plan_id == 'monthly_pro'  # Mark Pro as popular
            }
            plans.append(display_plan)
        
        return plans
    
    def calculate_upgrade_savings(self, business_id: int, target_plan: str) -> Dict[str, any]:
        """Calculate potential savings when upgrading to monthly plan"""
        if target_plan not in self.MONTHLY_PLANS:
            return {'error': 'Invalid plan'}
        
        plan = self.MONTHLY_PLANS[target_plan]
        monthly_price = plan['price']
        conversations_included = plan['conversations_per_month']
        
        # Calculate equivalent credit cost
        credit_price_per_conversation = 10.00  # Assuming $10 per conversation in credit system
        
        if conversations_included == -1:  # Unlimited
            equivalent_credit_cost = 500.00  # High estimate for unlimited
        else:
            equivalent_credit_cost = conversations_included * credit_price_per_conversation
        
        monthly_savings = equivalent_credit_cost - monthly_price
        annual_savings = monthly_savings * 12
        
        return {
            'monthly_price': monthly_price,
            'equivalent_credit_cost': equivalent_credit_cost,
            'monthly_savings': monthly_savings,
            'annual_savings': annual_savings,
            'savings_percentage': int((monthly_savings / equivalent_credit_cost) * 100) if equivalent_credit_cost > 0 else 0
        }