from models.db import get_db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def get_user_charging_statistics(user_id):
    """Get comprehensive charging statistics for a user"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Total sessions and kWh
        cur.execute("""
            SELECT COUNT(*) as total_sessions, SUM(units) as total_units, 
                   SUM(amount) as total_spent
            FROM charging_sessions 
            WHERE user_id = ? AND status = 'Completed'
        """, (user_id,))
        
        stats = cur.fetchone()
        total_sessions = stats[0] if stats and stats[0] else 0
        total_units = stats[1] if stats and stats[1] else 0
        total_spent = stats[2] if stats and stats[2] else 0
        
        # Average per session
        avg_per_session = (total_spent / total_sessions) if total_sessions > 0 else 0
        avg_units_per_session = (total_units / total_sessions) if total_sessions > 0 else 0
        
        # Most used station
        cur.execute("""
            SELECT station_name, COUNT(*) as count
            FROM charging_sessions 
            WHERE user_id = ? AND status = 'Completed'
            GROUP BY station_name
            ORDER BY count DESC
            LIMIT 1
        """, (user_id,))
        
        fav_station = cur.fetchone()
        
        # Last charging session
        cur.execute("""
            SELECT started_at, units, amount, station_name, status
            FROM charging_sessions 
            WHERE user_id = ?
            ORDER BY started_at DESC
            LIMIT 1
        """, (user_id,))
        
        last_session = cur.fetchone()
        
        return {
            "total_sessions": total_sessions,
            "total_units_charged": round(total_units, 2),
            "total_spent": round(total_spent, 2),
            "avg_per_session": round(avg_per_session, 2),
            "avg_units_per_session": round(avg_units_per_session, 2),
            "favorite_station": fav_station[0] if fav_station else "N/A",
            "favorite_count": fav_station[1] if fav_station else 0,
            "last_session": {
                "date": last_session[0] if last_session and last_session[0] else "N/A",
                "units": last_session[1] if last_session and last_session[1] else 0,
                "amount": last_session[2] if last_session and last_session[2] else 0,
                "station": last_session[3] if last_session and last_session[3] else "N/A",
                "status": last_session[4] if last_session and last_session[4] else "N/A"
            } if last_session else None
        }
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return None
    finally:
        conn.close()


def get_user_eco_impact(user_id):
    """Calculate environmental impact of user's charging habits"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get total units and average green score
        cur.execute("""
            SELECT SUM(cs.units), AVG(s.green_score)
            FROM charging_sessions cs
            JOIN stations s ON cs.station_name = s.name
            WHERE cs.user_id = ? AND cs.status = 'Completed'
        """, (user_id,))
        
        result = cur.fetchone()
        total_units = result[0] if result and result[0] else 0
        avg_green_score = result[1] if result and result[1] else 0
        
        # Carbon footprint calculation
        # Average EV charging: 0.4-0.6 kg CO2 per kWh (depends on grid source)
        # High green score: 0.2 kg CO2 per kWh
        # Low green score: 0.6 kg CO2 per kWh
        
        co2_factor = 0.2 + (10 - avg_green_score) * 0.04 if avg_green_score else 0.4
        carbon_saved = total_units * co2_factor
        
        # Trees equivalent (1 tree absorbs ~20kg CO2/year)
        trees_equivalent = carbon_saved / 20
        
        # Green charging percentage
        green_percentage = avg_green_score * 10 if avg_green_score else 0
        
        return {
            "total_green_charges": total_units,
            "avg_green_score": round(avg_green_score, 1),
            "estimated_co2_emissions_kg": round(carbon_saved, 2),
            "trees_equivalent": round(trees_equivalent, 1),
            "eco_percentage": round(green_percentage, 1),
            "eco_rating": "Excellent Eco-Warrior!" if avg_green_score >= 8 else "Good Green Citizen" if avg_green_score >= 6 else "Moderate" if avg_green_score >= 4 else "Standard",
            "recommendation": "Amazing! Keep using green stations!" if avg_green_score >= 8 else "Try to choose higher-rated green stations when possible"
        }
        
    except Exception as e:
        logger.error(f"Error calculating eco impact: {e}")
        return None
    finally:
        conn.close()


def get_user_spending_insights(user_id):
    """Analyze user spending patterns and savings opportunities"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Spending by station
        cur.execute("""
            SELECT station_name, SUM(amount) as total, COUNT(*) as count, 
                   AVG(amount) as avg_session
            FROM charging_sessions 
            WHERE user_id = ? AND status = 'Completed'
            GROUP BY station_name
            ORDER BY total DESC
            LIMIT 5
        """, (user_id,))
        
        spending_by_station = cur.fetchall()
        
        # Spending trends (last 7, 14, 30 days)
        def get_spending_period(days):
            date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
            cur.execute("""
                SELECT SUM(amount), COUNT(*)
                FROM charging_sessions 
                WHERE user_id = ? AND status = 'Completed' AND started_at > ?
            """, (user_id, date_threshold))
            result = cur.fetchone()
            return (result[0] if result and result[0] else 0, result[1] if result and result[1] else 0)
        
        spending_7d = get_spending_period(7)
        spending_14d = get_spending_period(14)
        spending_30d = get_spending_period(30)
        
        # Find cheapest station used
        cur.execute("""
            SELECT station_name, AVG(amount/units) as avg_price_per_unit
            FROM charging_sessions 
            WHERE user_id = ? AND status = 'Completed' AND units > 0
            GROUP BY station_name
            ORDER BY avg_price_per_unit ASC
            LIMIT 1
        """, (user_id,))
        
        cheapest = cur.fetchone()
        
        return {
            "spending_last_7_days": {
                "total": round(spending_7d[0], 2),
                "sessions": spending_7d[1]
            },
            "spending_last_14_days": {
                "total": round(spending_14d[0], 2),
                "sessions": spending_14d[1]
            },
            "spending_last_30_days": {
                "total": round(spending_30d[0], 2),
                "sessions": spending_30d[1]
            },
            "top_stations": [
                {
                    "name": s[0],
                    "total": round(s[1], 2),
                    "sessions": s[2],
                    "avg_per_session": round(s[3], 2)
                }
                for s in spending_by_station
            ],
            "cheapest_station": cheapest[0] if cheapest else "N/A",
            "recommendation": f"Save money by charging at {cheapest[0]} more often!" if cheapest else "No spending data available yet"
        }
        
    except Exception as e:
        logger.error(f"Error analyzing spending: {e}")
        return None
    finally:
        conn.close()


def get_personalized_recommendations(user_id):
    """Generate personalized recommendations for user"""
    try:
        stats = get_user_charging_statistics(user_id)
        eco = get_user_eco_impact(user_id)
        spending = get_user_spending_insights(user_id)
        
        recommendations = []
        
        # Recommendation 1: Charging frequency
        if stats and stats["total_sessions"] < 5:
            recommendations.append({
                "type": "frequency",
                "title": "Getting Started",
                "message": "You've just started! Build a habit by charging regularly at your favorite station.",
                "icon": "🚀"
            })
        elif stats and stats["total_sessions"] > 100:
            recommendations.append({
                "type": "loyalty",
                "title": "Loyal User",
                "message": f"You're a power user! You've completed {stats['total_sessions']} charges. Consider a loyalty program!",
                "icon": "⭐"
            })
        
        # Recommendation 2: Eco impact
        if eco and eco["avg_green_score"] < 5:
            recommendations.append({
                "type": "eco",
                "title": "Go Green",
                "message": f"Switch to higher green-score stations to reduce your carbon footprint! Current: {eco['avg_green_score']}/10",
                "icon": "🌱"
            })
        elif eco and eco["avg_green_score"] >= 8:
            recommendations.append({
                "type": "eco_hero",
                "title": "Eco-Warrior",
                "message": f"Amazing! Your charging is {eco['eco_percentage']:.1f}% eco-friendly. Keep it up!",
                "icon": "🌍"
            })
        
        # Recommendation 3: Spending optimization
        if spending and spending["spending_last_30_days"]["sessions"] > 0:
            avg_cost = spending["spending_last_30_days"]["total"] / spending["spending_last_30_days"]["sessions"]
            if avg_cost > 100:
                recommendations.append({
                    "type": "budget",
                    "title": "Save Money",
                    "message": f"Try {spending['cheapest_station']} - it's cheaper and equally reliable!",
                    "icon": "💰"
                })
            elif avg_cost < 30:
                recommendations.append({
                    "type": "budget_wise",
                    "title": "Budget Conscious",
                    "message": f"Great spending habits! You average ₹{avg_cost:.0f} per session.",
                    "icon": "✅"
                })
        
        # Recommendation 4: Favorite station usage
        if stats and stats["favorite_count"] > stats["total_sessions"] * 0.5:
            recommendations.append({
                "type": "diversity",
                "title": "Explore More",
                "message": f"Try other stations! {(stats['favorite_count']/stats['total_sessions']*100):.0f}% of your charges are at one station.",
                "icon": "🗺️"
            })
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return []


def get_user_insights_dashboard(user_id):
    """Get complete insights dashboard for user"""
    return {
        "statistics": get_user_charging_statistics(user_id),
        "eco_impact": get_user_eco_impact(user_id),
        "spending": get_user_spending_insights(user_id),
        "recommendations": get_personalized_recommendations(user_id)
    }
