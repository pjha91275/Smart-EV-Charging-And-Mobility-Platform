from models.db import get_db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def get_peak_hours(station_name):
    """
    Predict peak charging hours for a station based on historical data
    Returns: List of hours (0-23) and their activity levels
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get charging sessions from last 30 days
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        
        cur.execute("""
            SELECT started_at FROM charging_sessions 
            WHERE station_name = ? AND started_at > ?
        """, (station_name, thirty_days_ago))
        
        sessions = cur.fetchall()
        
        # Count sessions by hour of day
        hour_counts = [0] * 24
        for session in sessions:
            if session[0]:
                try:
                    hour = datetime.fromisoformat(session[0]).hour
                    hour_counts[hour] += 1
                except:
                    pass
        
        # Calculate average
        total = sum(hour_counts)
        if total == 0:
            return None
        
        avg = total / 24
        
        # Return hours with intensity (0-10 scale)
        hours_data = []
        for hour, count in enumerate(hour_counts):
            intensity = min(10, int((count / max(hour_counts)) * 10)) if max(hour_counts) > 0 else 0
            hours_data.append({
                "hour": f"{hour:02d}:00",
                "count": count,
                "intensity": intensity,
                "is_peak": count > (total / 12)  # Peak if above average
            })
        
        return hours_data
        
    except Exception as e:
        logger.error(f"Error predicting peak hours: {e}")
        return None
    finally:
        conn.close()


def get_station_demand_forecast(station_name, days_ahead=7):
    """
    Forecast demand for a station over next N days
    Based on historical weekday patterns
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get data from last 60 days
        sixty_days_ago = (datetime.now() - timedelta(days=60)).isoformat()
        
        cur.execute("""
            SELECT started_at FROM charging_sessions 
            WHERE station_name = ? AND started_at > ?
        """, (station_name, sixty_days_ago))
        
        sessions = cur.fetchall()
        
        # Count by weekday (0=Monday, 6=Sunday)
        weekday_counts = [0] * 7
        for session in sessions:
            if session[0]:
                try:
                    dt = datetime.fromisoformat(session[0])
                    weekday_counts[dt.weekday()] += 1
                except:
                    pass
        
        # Generate forecast
        forecast = []
        today = datetime.now()
        
        for i in range(days_ahead):
            future_date = today + timedelta(days=i)
            weekday = future_date.weekday()
            demand = weekday_counts[weekday]
            
            forecast.append({
                "date": future_date.strftime("%Y-%m-%d"),
                "day": future_date.strftime("%A"),
                "expected_sessions": demand,
                "confidence": "high" if demand > 5 else "medium" if demand > 0 else "low"
            })
        
        return forecast
        
    except Exception as e:
        logger.error(f"Error forecasting demand: {e}")
        return None
    finally:
        conn.close()


def get_price_trend(station_name, days=30):
    """
    Analyze price trends for a station
    Returns: Average price over time, trend direction
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT price FROM stations WHERE name = ?
        """, (station_name,))
        
        result = cur.fetchone()
        if not result:
            return None
        
        current_price = result[0]
        
        # Get average historical price
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        
        cur.execute("""
            SELECT AVG(amount/units) as avg_price 
            FROM charging_sessions 
            WHERE station_name = ? AND started_at > ? AND units > 0
        """, (station_name, thirty_days_ago))
        
        hist_result = cur.fetchone()
        historical_avg = hist_result[0] if hist_result and hist_result[0] else current_price
        
        trend = "stable"
        if current_price > historical_avg * 1.1:
            trend = "increasing"
        elif current_price < historical_avg * 0.9:
            trend = "decreasing"
        
        return {
            "current_price": round(current_price, 2),
            "historical_avg": round(historical_avg, 2),
            "trend": trend,
            "recommendation": "Consider charging soon - prices are low!" if trend == "decreasing" else "Prices may increase soon" if trend == "increasing" else "Prices are stable"
        }
        
    except Exception as e:
        logger.error(f"Error analyzing price trend: {e}")
        return None
    finally:
        conn.close()


def get_station_efficiency_metrics(station_name):
    """
    Analyze station efficiency metrics
    Returns: Average charging time, throughput, ratings
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get sessions with duration
        cur.execute("""
            SELECT AVG(duration_minutes) as avg_duration, COUNT(*) as total_sessions
            FROM charging_sessions 
            WHERE station_name = ? AND duration_minutes IS NOT NULL
        """, (station_name,))
        
        result = cur.fetchone()
        avg_duration = result[0] if result and result[0] else 0
        total_sessions = result[1] if result and result[1] else 0
        
        # Get station info
        cur.execute("""
            SELECT chargers, green_score FROM stations WHERE name = ?
        """, (station_name,))
        
        station_info = cur.fetchone()
        if not station_info:
            return None
        
        chargers, green_score = station_info
        
        metrics = {
            "avg_charging_time_minutes": round(avg_duration, 1) if avg_duration > 0 else "N/A",
            "total_sessions_30d": total_sessions,
            "available_chargers": chargers,
            "green_score": green_score,
            "efficiency_rating": "Excellent" if avg_duration < 60 and green_score >= 8 else "Good" if avg_duration < 90 and green_score >= 6 else "Standard",
            "recommendation": "Fast and eco-friendly!" if avg_duration < 60 and green_score >= 8 else "Reliable option" if total_sessions > 50 else "Growing station"
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting efficiency metrics: {e}")
        return None
    finally:
        conn.close()


def get_all_analytics_summary(station_name):
    """Get comprehensive analytics for a station"""
    return {
        "peak_hours": get_peak_hours(station_name),
        "demand_forecast": get_station_demand_forecast(station_name),
        "price_trend": get_price_trend(station_name),
        "efficiency": get_station_efficiency_metrics(station_name)
    }
