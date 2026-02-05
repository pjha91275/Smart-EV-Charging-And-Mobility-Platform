import google.genai as genai
import os
import json
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    logger.info("✅ Gemini API key configured for NL Query")
else:
    logger.warning("⚠️ GEMINI_API_KEY not set for NL Query")


def parse_natural_language_query(query):
    """
    Convert natural language query to structured search filters
    
    Example inputs:
    - "Find me a green station with fast charging within 10km"
    - "Cheapest station near me"
    - "Eco-friendly chargers under 200"
    
    Returns: {
        "green_score_min": 8,
        "max_distance": 10,
        "price_max": None,
        "chargers_required": True,
        "sort_by": "green_score",
        "natural_explanation": "Looking for eco-friendly stations..."
    }
    """
    
    if not GEMINI_API_KEY:
        return _parse_fallback_query(query)
    
    try:
        prompt = f"""Parse this EV charging station search query into structured filters.

Query: "{query}"

Return ONLY a JSON object (no markdown, no extra text) with these fields:
{{
    "green_score_min": <0-10 or null>,
    "green_score_max": <0-10 or null>,
    "price_min": <price in rupees or null>,
    "price_max": <price in rupees or null>,
    "max_distance": <km or null>,
    "min_chargers": <number or null>,
    "fast_charging": <true/false>,
    "sort_by": "green_score|price|distance|availability",
    "intent": "cheapest|greenest|fastest|nearest|balanced"
}}

Rules:
- If "green" or "eco" mentioned: green_score_min should be >= 7
- If "cheap" or "budget" mentioned: sort_by = price
- If "fast" or "quick" mentioned: fast_charging = true
- If distance mentioned (km, near): extract max_distance
- If price mentioned: extract price_max
- Only return valid JSON, no extra text"""
        
        client = genai.Client()
        response = client.models.generate_content(
            model="models/gemini-2.0-flash",
            contents=prompt,
            config={"temperature": 0.3}
        )
        
        if response and response.text:
            try:
                # Clean up response
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                
                filters = json.loads(text.strip())
                filters["query_method"] = "ai"
                filters["natural_explanation"] = _generate_explanation(query, filters)
                return filters
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse Gemini response: {response.text}")
                return _parse_fallback_query(query)
        
        return _parse_fallback_query(query)
        
    except Exception as e:
        logger.error(f"Error parsing natural query: {e}")
        return _parse_fallback_query(query)


def _parse_fallback_query(query):
    """Fallback parser when Gemini API is unavailable"""
    
    query_lower = query.lower()
    filters = {
        "green_score_min": None,
        "green_score_max": None,
        "price_min": None,
        "price_max": None,
        "max_distance": None,
        "min_chargers": None,
        "fast_charging": False,
        "sort_by": "distance",
        "intent": "balanced",
        "query_method": "fallback"
    }
    
    # Green/Eco check
    if any(word in query_lower for word in ["green", "eco", "environment", "renewable", "clean"]):
        filters["green_score_min"] = 7
        filters["sort_by"] = "green_score"
        filters["intent"] = "greenest"
    
    # Cheap/Budget check
    if any(word in query_lower for word in ["cheap", "budget", "affordable", "inexpensive", "cost", "price"]):
        filters["sort_by"] = "price"
        filters["intent"] = "cheapest"
        # Try to extract price
        import re
        price_match = re.search(r'(\d+)\s*(rupees?|rs|₹)', query_lower)
        if price_match:
            filters["price_max"] = int(price_match.group(1))
    
    # Fast/Quick check
    if any(word in query_lower for word in ["fast", "quick", "quick", "rapid", "speed"]):
        filters["fast_charging"] = True
        filters["sort_by"] = "availability"
    
    # Distance check
    import re
    distance_match = re.search(r'(\d+)\s*(km|kilometer|mile)', query_lower)
    if distance_match:
        distance = int(distance_match.group(1))
        filters["max_distance"] = distance if "km" in query_lower else distance * 1.6
    else:
        filters["max_distance"] = 10  # Default to 10km if not specified
    
    filters["natural_explanation"] = _generate_explanation(query, filters)
    return filters


def _generate_explanation(query, filters):
    """Generate human-readable explanation of parsed query"""
    
    parts = []
    
    if filters.get("intent") == "greenest":
        parts.append("Looking for eco-friendly stations")
    elif filters.get("intent") == "cheapest":
        parts.append("Searching for affordable charging")
    elif filters.get("intent") == "fastest":
        parts.append("Finding fast charging options")
    else:
        parts.append("Searching for charging stations")
    
    if filters.get("max_distance"):
        parts.append(f"within {filters['max_distance']}km")
    
    if filters.get("green_score_min"):
        parts.append(f"with green score ≥{filters['green_score_min']}")
    
    if filters.get("price_max"):
        parts.append(f"under ₹{filters['price_max']}/kWh")
    
    if filters.get("fast_charging"):
        parts.append("with fast charging")
    
    return " ".join(parts) if parts else "Searching for charging stations"


def apply_filters_to_stations(stations, filters):
    """
    Apply parsed filters to station list
    stations: list of (name, location, chargers, price, green_score) tuples
    filters: output from parse_natural_language_query()
    
    Returns: filtered and sorted station list
    """
    
    filtered = stations
    
    # Apply filters
    if filters.get("green_score_min"):
        filtered = [s for s in filtered if s[4] >= filters["green_score_min"]]
    
    if filters.get("green_score_max"):
        filtered = [s for s in filtered if s[4] <= filters["green_score_max"]]
    
    if filters.get("price_max"):
        filtered = [s for s in filtered if s[3] <= filters["price_max"]]
    
    if filters.get("price_min"):
        filtered = [s for s in filtered if s[3] >= filters["price_min"]]
    
    if filters.get("min_chargers"):
        filtered = [s for s in filtered if s[2] >= filters["min_chargers"]]
    
    # Sort
    sort_by = filters.get("sort_by", "distance")
    
    if sort_by == "green_score":
        filtered.sort(key=lambda x: x[4], reverse=True)  # Higher is better
    elif sort_by == "price":
        filtered.sort(key=lambda x: x[3])  # Lower is better
    elif sort_by == "chargers":
        filtered.sort(key=lambda x: x[2], reverse=True)
    
    return filtered


def search_with_natural_language(query, all_stations):
    """
    End-to-end natural language search
    query: user input like "Find me a green station near me"
    all_stations: list of station tuples
    
    Returns: {
        "explanation": "Searching for eco-friendly stations within 10km",
        "filters": {...},
        "results": [stations],
        "result_count": N
    }
    """
    
    filters = parse_natural_language_query(query)
    results = apply_filters_to_stations(all_stations, filters)
    
    return {
        "explanation": filters.get("natural_explanation"),
        "filters": filters,
        "results": results,
        "result_count": len(results),
        "query_method": filters.get("query_method")
    }
