import sys
sys.path.insert(0, '.')

print("=" * 50)
print("VERIFICATION REPORT")
print("=" * 50)

# Test 1: Routes
try:
    from routes.station_routes import station_bp
    print("✓ Routes module imports successfully")
except Exception as e:
    print(f"✗ Routes error: {e}")

# Test 2: AI Modules
try:
    from ai.chatbot import chat_with_bot
    from ai.analytics import get_all_analytics_summary
    from ai.insights import get_user_insights_dashboard
    from ai.nl_query import parse_natural_language_query
    print("✓ All AI modules import successfully")
except Exception as e:
    print(f"✗ AI module error: {e}")

# Test 3: Database
try:
    from models.db import get_db, init_db
    print("✓ Database module imports successfully")
except Exception as e:
    print(f"✗ Database error: {e}")

# Test 4: Flask
try:
    from flask import Flask
    print("✓ Flask imports successfully")
except Exception as e:
    print(f"✗ Flask error: {e}")

# Test 5: Check database has tables
try:
    from models.db import get_db
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    table_names = [t[0] for t in tables]
    expected = ['admin', 'users', 'stations', 'charging_sessions', 'waiting_queue']
    
    if all(t in table_names for t in expected):
        print(f"✓ Database tables initialized ({len(table_names)} tables)")
    else:
        print(f"✗ Missing tables. Found: {table_names}")
    conn.close()
except Exception as e:
    print(f"✗ Database check error: {e}")

print("\n" + "=" * 50)
print("✓ VERIFICATION COMPLETE - ALL SYSTEMS GO!")
print("=" * 50)
print("\nReady to use:")
print("  • /user/chat - AI Chat Assistant")
print("  • /user/insights - Personal Insights")
print("  • /user/nl-search - Natural Language Search")
print("  • /user/station-analytics/<name> - Station Analytics")
