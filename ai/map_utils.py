import os
import logging
from models.db import get_db

logger = logging.getLogger(__name__)

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")


def get_all_stations_with_location():
    """
    Get all approved stations with their location coordinates
    For now, uses hardcoded coordinates for popular petrol pumps in India
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT name, location, chargers, price, green_score, id
            FROM stations
            WHERE approved = 1
        """)
        
        stations = cur.fetchall()
        
        # Add coordinates for stations
        # In production, you would geocode these addresses or have coordinates in DB
        station_coordinates = {
            "Central Hub": {"lat": 28.6139, "lng": 77.2090},  # Delhi
            "Downtown Station": {"lat": 19.0760, "lng": 72.8777},  # Mumbai
            "Tech Park Charger": {"lat": 12.9716, "lng": 77.5946},  # Bangalore
            "Airport Plaza": {"lat": 28.5921, "lng": 77.1385},  # Delhi Airport area
            "Highway Rest Point": {"lat": 28.4595, "lng": 77.0266},  # Noida
            "Shopping Mall Charging": {"lat": 18.9220, "lng": 72.8347},  # Mumbai area
            "Business District": {"lat": 13.0827, "lng": 80.2707},  # Chennai
            "Metro Station Hub": {"lat": 28.7041, "lng": 77.1025},  # Delhi Metro
        }
        
        stations_list = []
        for station in stations:
            name, location, chargers, price, green_score, station_id = station
            
            # Get coordinates from predefined list or use defaults
            coords = station_coordinates.get(name, {
                "lat": 28.6139 + (len(stations_list) * 0.01),  # Offset for visibility
                "lng": 77.2090 + (len(stations_list) * 0.01)
            })
            
            stations_list.append({
                "id": station_id,
                "name": name,
                "location": location,
                "chargers": chargers,
                "price": price,
                "green_score": green_score,
                "lat": coords.get("lat", 28.6139),
                "lng": coords.get("lng", 77.2090),
                "marker_color": get_marker_color(green_score)
            })
        
        return stations_list
        
    except Exception as e:
        logger.error(f"Error fetching stations: {e}")
        return []
    finally:
        conn.close()


def get_marker_color(green_score):
    """Determine marker color based on green score"""
    if green_score >= 8:
        return "green"  # Eco-friendly
    elif green_score >= 6:
        return "yellow"  # Moderate
    elif green_score >= 4:
        return "orange"  # Standard
    else:
        return "red"  # Low eco-score


def search_stations_by_location(lat, lng, radius_km=10):
    """
    Search stations within radius of given coordinates
    Uses Haversine formula for distance calculation
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT name, location, chargers, price, green_score, id
            FROM stations
            WHERE approved = 1
        """)
        
        stations = cur.fetchall()
        station_coordinates = _get_station_coordinates()
        
        nearby_stations = []
        
        for station in stations:
            name, location, chargers, price, green_score, station_id = station
            coords = station_coordinates.get(name)
            
            if coords:
                distance = calculate_distance(
                    lat, lng,
                    coords.get("lat", 28.6139),
                    coords.get("lng", 77.2090)
                )
                
                if distance <= radius_km:
                    nearby_stations.append({
                        "id": station_id,
                        "name": name,
                        "location": location,
                        "chargers": chargers,
                        "price": price,
                        "green_score": green_score,
                        "lat": coords.get("lat", 28.6139),
                        "lng": coords.get("lng", 77.2090),
                        "distance": round(distance, 2),
                        "marker_color": get_marker_color(green_score)
                    })
        
        # Sort by distance
        nearby_stations.sort(key=lambda x: x.get("distance", 0))
        return nearby_stations
        
    except Exception as e:
        logger.error(f"Error searching stations: {e}")
        return []
    finally:
        conn.close()


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates using Haversine formula
    Returns distance in kilometers
    """
    from math import radians, cos, sin, asin, sqrt
    
    # Convert to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of Earth in km
    
    return c * r


def _get_station_coordinates():
    """Helper to get station coordinates"""
    return {
        "Central Hub": {"lat": 28.6139, "lng": 77.2090},
        "Downtown Station": {"lat": 19.0760, "lng": 72.8777},
        "Tech Park Charger": {"lat": 12.9716, "lng": 77.5946},
        "Airport Plaza": {"lat": 28.5921, "lng": 77.1385},
        "Highway Rest Point": {"lat": 28.4595, "lng": 77.0266},
        "Shopping Mall Charging": {"lat": 18.9220, "lng": 72.8347},
        "Business District": {"lat": 13.0827, "lng": 80.2707},
        "Metro Station Hub": {"lat": 28.7041, "lng": 77.1025},
    }


def add_station_coordinates(station_name, lat, lng):
    """
    Add or update coordinates for a station
    Can be called when adding new stations
    """
    try:
        # In production, store in database
        coords_db = _get_station_coordinates()
        coords_db[station_name] = {"lat": lat, "lng": lng}
        return True
    except Exception as e:
        logger.error(f"Error adding coordinates: {e}")
        return False


def get_map_config():
    """Get Google Maps configuration"""
    return {
        "api_key": GOOGLE_MAPS_API_KEY,
        "center": {"lat": 28.6139, "lng": 77.2090},  # Delhi center
        "zoom": 12,
        "default_radius": 10  # km
    }
