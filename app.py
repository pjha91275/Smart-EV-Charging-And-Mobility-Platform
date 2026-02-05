from flask import Flask, redirect, render_template, session
from dotenv import load_dotenv
from models.db import init_db, get_db
from routes.admin_routes import admin_bp
from routes.auth_routes import auth_bp 
from routes.station_routes import station_bp

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = "secret123"  # required for session

# Initialize DB
init_db()

# Pre-create admin
def create_admin():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM admin")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO admin (username, password) VALUES (?, ?)",
            ("admin", "admin123")
        )
        conn.commit()
    conn.close()

create_admin()

# Register blueprint
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp) 
app.register_blueprint(station_bp)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/user/dashboard")
def user_dashboard():
    if session.get("role") != "user":
        return redirect("/login")

    # Compute user stats: total sessions, units charged, average green score
    conn = get_db()
    cur = conn.cursor()

    # Total sessions
    cur.execute("SELECT COUNT(*) FROM charging_sessions WHERE user_id=?", (session.get('user_id'),))
    total_sessions = cur.fetchone()[0]

    # Total units charged (sum of units from completed sessions)
    cur.execute("SELECT COALESCE(SUM(units), 0) FROM charging_sessions WHERE user_id=? AND status='Completed'", (session.get('user_id'),))
    total_units = cur.fetchone()[0]

    # Average green score of stations the user has charged at
    cur.execute("""
        SELECT COALESCE(AVG(s.green_score), 0)
        FROM charging_sessions cs
        JOIN stations s ON cs.station_name = s.name
        WHERE cs.user_id = ?
    """, (session.get('user_id'),))
    avg_green_score = cur.fetchone()[0]

    conn.close()

    return render_template("user_dashboard.html", total_sessions=total_sessions, total_units=total_units, avg_green_score=avg_green_score)


@app.route("/owner/dashboard")
def owner_dashboard():
    if session.get("role") != "owner":
        return redirect("/login")

    # Compute owner stats: total stations, users served, revenue
    conn = get_db()
    cur = conn.cursor()

    # Total stations owned
    cur.execute("SELECT COUNT(*) FROM stations WHERE owner_id=?", (session.get('user_id'),))
    total_stations = cur.fetchone()[0]

    # Users served (distinct users with sessions at this owner's stations)
    cur.execute("""
        SELECT COUNT(DISTINCT cs.user_id)
        FROM charging_sessions cs
        JOIN stations s ON cs.station_name = s.name
        WHERE s.owner_id = ?
    """, (session.get('user_id'),))
    users_served = cur.fetchone()[0]

    # Revenue generated (sum of amounts for sessions at owner's stations)
    cur.execute("""
        SELECT COALESCE(SUM(cs.amount), 0)
        FROM charging_sessions cs
        JOIN stations s ON cs.station_name = s.name
        WHERE s.owner_id = ?
    """, (session.get('user_id'),))
    total_revenue = cur.fetchone()[0]

    conn.close()

    return render_template("owner_dashboard.html", total_stations=total_stations, total_users=users_served, total_revenue=total_revenue)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)