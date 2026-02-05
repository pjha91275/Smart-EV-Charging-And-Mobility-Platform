import google.generativeai as genai
import os
import json
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    logger.info("✅ Gemini API key configured for Recommender")
else:
    logger.warning("⚠️ GEMINI_API_KEY not set for Recommender")


def recommend_station(battery, distance, stations):
    """
    battery: current battery percentage (0–100)
    distance: distance to destination (km)
    stations: list of stations from DB
    Returns: (station_data, explanation) or (None, error_message)
    """

    reachable_stations = []

    # Assume: 1% battery ≈ 1 km (simple heuristic)
    max_distance = battery * 1

    for s in stations:
        name, location, chargers, price, green_score = s

        if max_distance >= distance:
            score = (green_score * 2) - price
            reachable_stations.append((score, s))

    if not reachable_stations:
        return None, "No reachable stations found with your current battery level."

    # Pick station with highest score
    reachable_stations.sort(reverse=True, key=lambda x: x[0])
    best_station = reachable_stations[0][1]
    
    # Generate AI explanation using Gemini if API is configured
    explanation = _generate_ai_explanation(battery, distance, best_station, reachable_stations)
    
    return best_station, explanation


def _generate_ai_explanation(battery, distance, best_station, all_reachable):
    """
    Generate an AI-powered explanation for the recommendation using Gemini API
    """
    if not GEMINI_API_KEY:
        return _generate_fallback_explanation(battery, distance, best_station)
    
    try:
        name, location, chargers, price, green_score = best_station
        
        # Prepare station data for Gemini
        stations_info = []
        for i, (score, station) in enumerate(all_reachable[:5], 1):  # Top 5 reachable
            s_name, s_loc, s_chargers, s_price, s_green = station
            stations_info.append({
                "rank": i,
                "name": s_name,
                "location": s_loc,
                "price": f"₹{s_price}/kWh",
                "green_score": s_green,
                "chargers_available": s_chargers
            })
        
        prompt = f"""You are an AI assistant for an EV charging platform. Based on the user's current situation and available charging stations, provide a brief, friendly recommendation.

User Situation:
- Current Battery: {battery}%
- Distance to Destination: {distance} km
- Estimated Max Range: {battery * 1} km

Recommended Station (Best Option):
- Name: {name}
- Location: {location}
- Price: ₹{price}/kWh
- Green Energy Score: {green_score}/10
- Available Chargers: {chargers}

Other Reachable Stations:
{json.dumps(stations_info[1:], indent=2) if len(stations_info) > 1 else "None"}

Please provide:
1. A short 1-2 sentence explanation of why this station is recommended
2. Key benefits (max 2-3 points)
3. A brief tip for optimal charging

Keep the response concise and practical. Format as JSON with keys: "why", "benefits", "tip"."""
        
        client = genai.Client()
        response = client.models.generate_content(
            model="models/gemini-2.0-flash",
            contents=prompt,
            config={"temperature": 0.7}
        )
        
        if response and response.text:
            # Try to parse JSON response
            try:
                response_text = response.text.strip()
                # Remove markdown code blocks if present
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                
                ai_data = json.loads(response_text.strip())
                explanation = f"""
{ai_data.get('why', 'Recommended based on availability and pricing.')}

Benefits:
{chr(10).join(f"• {benefit}" for benefit in ai_data.get('benefits', []))}

Tip: {ai_data.get('tip', 'Charge during off-peak hours for better rates!')}
"""
                return explanation.strip()
            except json.JSONDecodeError:
                # If JSON parsing fails, use the raw response
                return f"AI Recommendation:\n{response.text}"
        
        return _generate_fallback_explanation(battery, distance, best_station)
        
    except Exception as e:
        logger.error(f"Error generating AI explanation: {e}")
        return _generate_fallback_explanation(battery, distance, best_station)


def _generate_fallback_explanation(battery, distance, best_station):
    """
    Fallback explanation generator when Gemini API is not available
    """
    name, location, chargers, price, green_score = best_station
    
    explanation = f"""
Best Station Found: {name}

Location: {location}
Price: ₹{price}/kWh
Green Score: {green_score}/10
Available Chargers: {chargers}

This station offers an optimal balance of:
• Accessibility with {chargers} available chargers
• {'Eco-friendly' if green_score >= 7 else 'Reasonably efficient'} energy sources (Score: {green_score}/10)
• Competitive pricing at ₹{price}/kWh

Tip: Charge now to ensure you reach your destination comfortably!
"""
    return explanation.strip()
