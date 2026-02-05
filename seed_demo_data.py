#!/usr/bin/env python3
"""
Seed Demo Data - Smart EV Charging Platform
============================================

Populates the database with realistic demo data including:
- Multiple users (admin, owner, regular users)
- Charging stations with different specs
- Charging session history
- Waiting queue entries
- Environmental tracking

Usage:
    python seed_demo_data.py

This will create a realistic demo environment for testing and exploration.
"""

import sqlite3
import datetime
import random
from hashlib import md5

# Database path
DB_PATH = 'database/ev.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hash password using MD5 (same as app.py)"""
    return md5(password.encode()).hexdigest()

def seed_users(conn):
    """Seed users table with demo data"""
    print("📝 Seeding users...")
    
    cursor = conn.cursor()
    
    users = [
        # Admin user
        ('Admin User', 'admin@evcharge.com', hash_password('admin123'), 'admin'),
        
        # Station owners
        ('Rajesh Kumar', 'owner1@evcharge.com', hash_password('owner123'), 'owner'),
        ('Priya Singh', 'owner2@evcharge.com', hash_password('owner123'), 'owner'),
        
        # Regular users
        ('Amit Patel', 'user1@gmail.com', hash_password('user123'), 'user'),
        ('Sneha Sharma', 'user2@gmail.com', hash_password('user123'), 'user'),
        ('Vikas Reddy', 'user3@gmail.com', hash_password('user123'), 'user'),
        ('Priyanka Verma', 'user4@gmail.com', hash_password('user123'), 'user'),
        ('Arjun Singh', 'user5@gmail.com', hash_password('user123'), 'user'),
    ]
    
    for name, email, password, role in users:
        try:
            cursor.execute('''
                INSERT INTO users (name, email, password, role)
                VALUES (?, ?, ?, ?)
            ''', (name, email, password, role))
            print(f"  ✅ Created {role}: {name} ({email})")
        except sqlite3.IntegrityError:
            print(f"  ⚠️  {name} already exists")
    
    conn.commit()

def seed_stations(conn):
    """Seed stations table with demo data"""
    print("\n🔌 Seeding charging stations...")
    
    cursor = conn.cursor()
    
    # Get owner IDs
    cursor.execute("SELECT id FROM users WHERE role='owner' LIMIT 2")
    owner_ids = [row[0] for row in cursor.fetchall()]
    
    stations = [
        # Delhi stations
        ('ChargeFast Delhi', 'Sector 5, Dwarka, Delhi', 5, 10.50, 8, owner_ids[0] if len(owner_ids) > 0 else 2, 1),
        ('EcoPower Station', 'Connaught Place, Delhi', 8, 11.00, 9, owner_ids[0] if len(owner_ids) > 0 else 2, 1),
        ('GreenCharge Hub', 'Aerocity, Delhi', 6, 10.00, 8, owner_ids[0] if len(owner_ids) > 0 else 2, 1),
        ('PowerPoint Delhi', 'Gurgaon Road, Delhi', 4, 9.50, 8, owner_ids[0] if len(owner_ids) > 0 else 2, 1),
        
        # Mumbai stations
        ('ChargeFast Mumbai', 'Bandra, Mumbai', 10, 12.00, 9, owner_ids[1] if len(owner_ids) > 1 else 3, 1),
        ('EcoPower Mumbai', 'Powai, Mumbai', 7, 12.50, 9, owner_ids[1] if len(owner_ids) > 1 else 3, 1),
        ('GreenHub BKC', 'Bandra Kurla Complex, Mumbai', 9, 13.00, 9, owner_ids[1] if len(owner_ids) > 1 else 3, 1),
        ('RapidCharge Mumbai', 'Vile Parle, Mumbai', 5, 11.50, 7, owner_ids[1] if len(owner_ids) > 1 else 3, 1),
        
        # Bangalore stations
        ('ChargeFast Bangalore', 'Whitefield, Bangalore', 8, 9.50, 8, owner_ids[0] if len(owner_ids) > 0 else 2, 1),
        ('EcoPower Bangalore', 'Koramangala, Bangalore', 6, 10.00, 9, owner_ids[0] if len(owner_ids) > 0 else 2, 1),
        ('GreenCharge Tech Park', 'ITPL, Bangalore', 12, 9.00, 9, owner_ids[0] if len(owner_ids) > 0 else 2, 1),
        
        # Chennai stations
        ('ChargeFast Chennai', 'T. Nagar, Chennai', 5, 8.50, 8, owner_ids[1] if len(owner_ids) > 1 else 3, 1),
        ('EcoPower Chennai', 'Guindy, Chennai', 7, 9.00, 8, owner_ids[1] if len(owner_ids) > 1 else 3, 1),
        ('GreenHub OMR', 'Old Mahabalipuram Road, Chennai', 9, 8.00, 9, owner_ids[1] if len(owner_ids) > 1 else 3, 1),
    ]
    
    for name, location, chargers, price, green_score, owner_id, approved in stations:
        try:
            cursor.execute('''
                INSERT INTO stations (name, location, chargers, price, green_score, owner_id, approved)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, location, chargers, price, green_score, owner_id, approved))
            print(f"  ✅ Created: {name} ({chargers} chargers, ₹{price}/kWh, score: {green_score})")
        except sqlite3.IntegrityError:
            print(f"  ⚠️  {name} already exists")
    
    conn.commit()

def seed_charging_sessions(conn):
    """Seed charging sessions with history"""
    print("\n⚡ Seeding charging sessions...")
    
    cursor = conn.cursor()
    
    # Get user and station IDs
    cursor.execute("SELECT id FROM users WHERE role='user' LIMIT 5")
    user_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT name FROM stations LIMIT 10")
    station_names = [row[0] for row in cursor.fetchall()]
    
    if not user_ids or not station_names:
        print("  ⚠️  Not enough users or stations")
        return
    
    sessions = [
        # Recent sessions
        (user_ids[0], station_names[0], 40, 420, 'completed'),
        (user_ids[1], station_names[1], 50, 550, 'completed'),
        (user_ids[2], station_names[2], 30, 300, 'completed'),
        (user_ids[3], station_names[3], 35, 333, 'completed'),
        (user_ids[4], station_names[4], 60, 720, 'completed'),
        (user_ids[0], station_names[5], 45, 562, 'completed'),
        (user_ids[1], station_names[6], 55, 715, 'completed'),
        (user_ids[2], station_names[7], 25, 288, 'completed'),
        
        # Older sessions
        (user_ids[3], station_names[8], 40, 380, 'completed'),
        (user_ids[4], station_names[9], 50, 500, 'completed'),
        (user_ids[0], station_names[0], 35, 368, 'completed'),
        (user_ids[1], station_names[1], 45, 495, 'completed'),
    ]
    
    for user_id, station_name, units, amount, status in sessions:
        try:
            cursor.execute('''
                INSERT INTO charging_sessions (user_id, station_name, units, amount, status, duration_minutes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, station_name, units, amount, status, random.randint(30, 120)))
            print(f"  ✅ Session: User {user_id} charged {units}kWh at {station_name}")
        except sqlite3.IntegrityError as e:
            print(f"  ⚠️  Error creating session: {e}")
    
    conn.commit()

def seed_waiting_queue(conn):
    """Seed waiting queue entries"""
    print("\n⏳ Seeding waiting queue...")
    
    cursor = conn.cursor()
    
    # Get user and station IDs
    cursor.execute("SELECT id FROM users WHERE role='user' LIMIT 3")
    user_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT name FROM stations LIMIT 3")
    station_names = [row[0] for row in cursor.fetchall()]
    
    if not user_ids or not station_names:
        print("  ⚠️  Not enough users or stations")
        return
    
    queue_entries = [
        (station_names[0], user_ids[0]),
        (station_names[1], user_ids[1]),
        (station_names[2], user_ids[2]),
    ]
    
    for station_name, user_id in queue_entries:
        try:
            cursor.execute('''
                INSERT INTO waiting_queue (station_name, user_id)
                VALUES (?, ?)
            ''', (station_name, user_id))
            print(f"  ✅ Queue: User {user_id} added to {station_name}")
        except sqlite3.IntegrityError:
            print(f"  ⚠️  Queue entry already exists")
    
    conn.commit()

def print_walkthrough():
    """Print interactive walkthrough guide"""
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                     🎯 WALKTHROUGH & TESTING GUIDE                        ║
╚═══════════════════════════════════════════════════════════════════════════╝

🚀 Now you have demo data! Here's how to explore:

STEP 1: START THE APPLICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  $ python app.py
  Visit: http://localhost:5000

STEP 2: LOGIN & EXPLORE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  👤 REGULAR USER (Full Features)
  ├─ Email: user1@gmail.com
  ├─ Password: user123
  └─ Can access:
     ├─ Dashboard (view stats)
     ├─ Google Maps Search (NEW!) - Try all 3 modes
     ├─ Find Stations (traditional list)
     ├─ Chat with AI
     ├─ Get Recommendations
     ├─ View Insights (spending, eco-impact)
     └─ Charging History (15+ sessions)

  🏢 STATION OWNER
  ├─ Email: owner1@evcharge.com
  ├─ Password: owner123
  └─ Can access:
     ├─ Owner Dashboard
     ├─ Manage Stations
     ├─ Active Sessions
     └─ Station Analytics

  👨‍💼 ADMIN (Full Control)
  ├─ Email: admin@evcharge.com
  ├─ Password: admin123
  └─ Can access:
     ├─ Admin Dashboard
     ├─ User Management
     ├─ Station Approval
     ├─ Queue Management
     └─ Platform Analytics

STEP 3: TEST GOOGLE MAPS FEATURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  After getting Google Maps API key and setting env var:

  🗺️  MODE 1: ALL STATIONS
  ├─ Click: Dashboard → "Google Maps Search"
  ├─ Select: "All Stations" radio button
  ├─ Click: "Search"
  ├─ See: 14 charging stations on interactive map
  ├─ Try: Click on markers, view info windows
  └─ Result: Complete list of stations with prices & eco-scores

  📍 MODE 2: NEARBY SEARCH
  ├─ Select: "Nearby" radio button
  ├─ Enter: Radius (10 km default)
  ├─ Click: "Use My Location" button
  ├─ Allow: Browser geolocation permission
  ├─ See: Only stations within your radius
  └─ Result: Sorted by distance

  🔍 MODE 3: ADVANCED FILTER
  ├─ Select: "Filter" radio button
  ├─ Set: Green Score = 8+ (excellent)
  ├─ Set: Max Price = ₹11/kWh
  ├─ Set: Min Chargers = 5
  ├─ Click: "Search"
  └─ Result: 7-9 high-quality, affordable stations

STEP 4: TEST BOOKING FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. From map search results:
     ├─ Click "Book" button on any station
     ├─ See: Station details, charger count, eco-rating
     └─ See: Price breakdown calculation

  2. Adjust charging amount:
     ├─ Use +/- buttons or quick-select (20/40/60/80 kWh)
     ├─ Watch: Price updates in real-time
     ├─ Note: Service fee (5%) included
     └─ See: CO₂ savings calculated

  3. Complete booking:
     ├─ Accept terms & conditions
     ├─ Click "Confirm Booking"
     └─ Redirected to charging interface

STEP 5: EXPLORE AI FEATURES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  💬 AI CHAT (24/7 Support)
  ├─ Click: "AI Chat Assistant"
  ├─ Ask: "Find me a green station under 11 rupees"
  ├─ Or: "What's the best time to charge?"
  └─ Get: Instant AI-powered answers

  🧠 AI RECOMMENDATIONS
  ├─ Click: "AI Recommendations"
  ├─ Get: Personalized station suggestions
  ├─ See: Why recommended
  └─ Compare: Price vs eco-rating

  📊 INSIGHTS & ANALYTICS
  ├─ Click: "Your Insights"
  ├─ See: Your charging statistics
  ├─ Track: Spending trends (7/14/30 days)
  ├─ Calculate: CO₂ saved vs petrol
  └─ View: Environmental impact

  🔍 SMART SEARCH
  ├─ Click: "Smart Search"
  ├─ Type: "green station near me under 10 rupees"
  ├─ Results: AI understands natural language
  └─ Find: Exactly what you want

STEP 6: DEMO DATA DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  📍 Stations Created: 14
  ├─ Delhi: 4 stations
  ├─ Mumbai: 4 stations
  ├─ Bangalore: 3 stations
  └─ Chennai: 3 stations

  💰 Price Range: ₹8.00 - ₹13.00 per kWh

  🌱 Green Scores: 7.0 - 9.0 (all certified eco-friendly)

  🔌 Chargers: 4 - 12 chargers per station

  👥 Users Created: 8
  ├─ 1 Admin
  ├─ 2 Station Owners
  └─ 5 Regular Users

  ⚡ Charging Sessions: 12 past sessions with history

  ⏳ Waiting Queue: 3 entries for testing

STEP 7: TESTING CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Map Features:
  ☐ Map loads with all 14 stations
  ☐ Markers are color-coded (green/yellow)
  ☐ Click marker shows info window
  ☐ Info window has "Book" button

  Search Modes:
  ☐ "All Stations" shows all 14 stations
  ☐ "Nearby" filters by radius
  ☐ "Filter" narrows by criteria
  ☐ Results update in real-time

  Booking:
  ☐ Booking page loads correctly
  ☐ Price calculates dynamically
  ☐ Service fee (5%) added correctly
  ☐ CO₂ savings displayed
  ☐ Redirect to charging works

  AI Features:
  ☐ Chat responds with relevant answers
  ☐ Recommendations are personalized
  ☐ Insights show your history
  ☐ Smart search understands queries

  Mobile:
  ☐ Map responsive on mobile
  ☐ Buttons are touchable
  ☐ List is scrollable
  ☐ Forms are usable

TIPS FOR EXPLORATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  💡 Try different user accounts to see different interfaces
  💡 Test on mobile by resizing your browser (F12)
  💡 Check browser console (F12) for any errors
  💡 Test in incognito mode for fresh session
  💡 Add more stations in admin panel to see clustering
  💡 Create new sessions to see analytics update
  💡 Rate stations to test feedback system

TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ❌ Map shows error "This page can't load Google Maps correctly"
  ✅ Solution: Set your Google Maps API key
     $ $env:GOOGLE_MAPS_API_KEY = "YOUR_KEY"
     $ python app.py

  ❌ Can't login with demo accounts
  ✅ Solution: Database might be corrupted
     $ python verify_db.py
     $ python seed_demo_data.py

  ❌ Stations not showing on map
  ✅ Solution: Make sure stations are approved=1
     $ python -c "from models.db import get_db; db = get_db(); print(db.execute('SELECT COUNT(*) FROM stations WHERE approved=1').fetchone())"

═══════════════════════════════════════════════════════════════════════════════

Ready to explore? Start with: python app.py

Then visit: http://localhost:5000

Enjoy the demo! 🚗⚡
""")

def main():
    """Main seeding function"""
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║              🌱 SEEDING DEMO DATA - Smart EV Charging                     ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        conn = get_db_connection()
        
        # Seed data
        seed_users(conn)
        seed_stations(conn)
        seed_charging_sessions(conn)
        seed_waiting_queue(conn)
        
        conn.close()
        
        print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                     ✅ SEEDING COMPLETE!                                 ║
╚═══════════════════════════════════════════════════════════════════════════╝

✨ Demo data successfully created!

Database now contains:
  👥 8 users (1 admin, 2 owners, 5 regular users)
  🔌 14 charging stations (Delhi, Mumbai, Bangalore, Chennai)
  ⚡ 12 charging session records with history
  ⏳ 3 waiting queue entries
        """)
        
        print_walkthrough()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
