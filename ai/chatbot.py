import google.genai as genai
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    logger.info("✅ Gemini API key configured")
else:
    logger.warning("⚠️ GEMINI_API_KEY not set. Chatbot will use fallback responses.")


def chat_with_bot(user_message, conversation_history=None):
    """
    AI-powered chatbot for Smart EV Charging platform
    Handles: station info, pricing, troubleshooting, payment issues, recommendations
    
    Args:
        user_message: User's question or message
        conversation_history: List of previous messages for context [(role, message), ...]
    
    Returns:
        (response_text, is_error)
    """
    
    if not GEMINI_API_KEY:
        logger.info("ℹ️ No Gemini API key - using fallback response")
        return _get_fallback_response(user_message), False
    
    try:
        system_prompt = """You are a friendly and helpful AI assistant for a Smart EV Charging platform. You help users with:
- Station information (location, pricing, availability, chargers)
- Charging recommendations based on their needs
- Troubleshooting charging issues
- Payment and billing questions
- Booking and queue information
- Environmental benefits and eco-friendly choices
- Pricing comparison and cost-saving tips

Be concise, helpful, and professional. Provide actionable advice. If you don't know something specific, suggest the user contact support or check the app.

Today's date: January 23, 2026."""

        # Build message history
        messages = []
        
        # Add conversation context
        if conversation_history:
            for role, content in conversation_history[-10:]:  # Last 10 messages for context
                messages.append({
                    "role": "user" if role == "user" else "model",
                    "parts": [{"text": content}]
                })
        
        # Add current user message with system context
        messages.append({
            "role": "user",
            "parts": [{"text": f"{system_prompt}\n\nUser Message: {user_message}"}]
        })
        
        logger.debug(f"🔄 Sending message to Gemini API: {user_message[:50]}...")
        
        model = genai.Client().models.get("models/gemini-2.0-flash")
        response = model.generate_content(
            messages,
            generation_config={"temperature": 0.7, "max_output_tokens": 500}
        )
        
        if response and response.text:
            logger.info("✅ Gemini API response received successfully")
            return response.text, False
        else:
            logger.warning("⚠️ Gemini API returned empty response")
            return _get_fallback_response(user_message), False
        
    except Exception as e:
        logger.error(f"❌ Chatbot API error: {str(e)}")
        logger.info("📌 Falling back to keyword-based response")
        return _get_fallback_response(user_message), False


def _get_fallback_response(user_message):
    """Fallback responses when API is unavailable"""
    
    message_lower = user_message.lower()
    
    if any(word in message_lower for word in ["price", "cost", "expensive", "cheap"]):
        return "Station prices vary by location and charger type. Use the 'AI Recommendations' feature to find the best-priced station for your needs. Check your charging history to see average costs!"
    
    elif any(word in message_lower for word in ["green", "eco", "environment", "renewable"]):
        return "Great question! Our stations with high green scores use renewable energy. Look for stations with 8+ green score to minimize your environmental impact. You'll see the eco-impact in your charging history!"
    
    elif any(word in message_lower for word in ["queue", "wait", "time", "available"]):
        return "Station availability varies throughout the day. Visit 'My Stations' to check current queue lengths and availability. Peak hours are typically 7-9 AM and 5-7 PM."
    
    elif any(word in message_lower for word in ["problem", "issue", "error", "not working", "trouble"]):
        return "I'm sorry you're experiencing issues! Please try: 1) Refresh the page, 2) Check your internet connection, 3) Try a different charger. If problems persist, please contact support@evcharging.com"
    
    elif any(word in message_lower for word in ["help", "support", "assistance"]):
        return "I'm here to help! I can assist with: charging recommendations, station information, pricing questions, troubleshooting, and booking help. What would you like to know?"
    
    else:
        return "That's a great question! For specific information about our Smart EV Charging platform, please visit the 'My Stations' section or use 'AI Recommendations' to find the perfect charging station for your needs."
