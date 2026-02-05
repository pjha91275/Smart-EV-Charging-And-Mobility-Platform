from flask import Blueprint, render_template, request, redirect, session
from models.db import get_db
from ai.recommender import recommend_station
from blockchain.payment import process_payment

station_bp = Blueprint("station", __name__)

# ===============================
# OWNER: ADD CHARGING STATION
# ===============================
@station_bp.route("/owner/add-station", methods=["GET", "POST"])
def add_station():
    if session.get("role") != "owner":
        return redirect("/login")

    if request.method == "POST":
        name = request.form["name"]
        location = request.form["location"]
        chargers = int(request.form["chargers"])
        price = float(request.form["price"])
        green_score = int(request.form["green_score"])
        owner_id = session.get("user_id")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO stations (name, location, chargers, price, green_score, owner_id, approved)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (name, location, chargers, price, green_score, owner_id))
        conn.commit()
        conn.close()

        return redirect("/owner/stations")

    return render_template("owner_add_station.html")


# ===============================
# OWNER: VIEW OWN STATIONS
# ===============================
@station_bp.route("/owner/stations")
def owner_stations():
    if session.get("role") != "owner":
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT name, location, chargers, price, green_score
        FROM stations
        WHERE owner_id=?
    """, (session.get("user_id"),))
    stations = cur.fetchall()
    conn.close()

    return render_template("owner_stations.html", stations=stations)


# ===============================
# USER: VIEW ALL STATIONS
# ===============================
@station_bp.route("/user/stations")
def user_stations():
    if session.get("role") != "user":
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, location, chargers, price, green_score
        FROM stations
        WHERE approved = 1
        ORDER BY name ASC
    """)

    stations = cur.fetchall()
    conn.close()

    return render_template("user_stations.html", stations=stations)


# ===============================
# USER: AI RECOMMENDATION
# ===============================
@station_bp.route("/user/recommend", methods=["GET", "POST"])
def recommend():
    if session.get("role") != "user":
        return redirect("/login")

    if request.method == "POST":
        battery = int(request.form["battery"])
        distance = int(request.form["distance"])

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT name, location, chargers, price, green_score
            FROM stations
        """)
        stations = cur.fetchall()
        conn.close()

        best_station, explanation = recommend_station(battery, distance, stations)

        return render_template("recommend_result.html", station=best_station, explanation=explanation)

    return render_template("recommend_form.html")


# ===============================
# USER: CHARGE STATION (WITH QUEUE)
# ===============================
@station_bp.route("/user/charge/<station_name>", methods=["GET", "POST"])
def charge_station(station_name):
    if session.get("role") != "user":
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    # Prevent blacklisted users from starting charging
    cur.execute("SELECT blacklisted FROM users WHERE id=?", (session.get('user_id'),))
    b = cur.fetchone()
    if b and b[0]:
        conn.close()
        return "Account is blacklisted"

    # Get total chargers
    cur.execute(
        "SELECT chargers FROM stations WHERE name=?",
        (station_name,)
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return "Station not found"

    total_chargers = row[0]

    # Count active sessions
    cur.execute(
        "SELECT COUNT(*) FROM charging_sessions WHERE station_name=? AND status='Active'",
        (station_name,)
    )
    active_sessions = cur.fetchone()[0]

    # ===============================
    # IF STATION FULL → ADD TO QUEUE
    # ===============================
    if active_sessions >= total_chargers:
        # Prevent duplicate queue entry
        cur.execute("""
            SELECT COUNT(*) FROM waiting_queue
            WHERE station_name=? AND user_id=?
        """, (station_name, session.get("user_id")))
        already_queued = cur.fetchone()[0]

        if already_queued == 0:
            cur.execute("""
                INSERT INTO waiting_queue (station_name, user_id)
                VALUES (?, ?)
            """, (station_name, session.get("user_id")))
            conn.commit()

        # Get queue position
        cur.execute("""
            SELECT COUNT(*)
            FROM waiting_queue
            WHERE station_name=?
              AND joined_at <= (
                SELECT joined_at FROM waiting_queue
                WHERE station_name=? AND user_id=?
                ORDER BY joined_at ASC
                LIMIT 1
              )
        """, (station_name, station_name, session.get("user_id")))

        position = cur.fetchone()[0]
        conn.close()

        return render_template(
            "queue_status.html",
            station_name=station_name,
            position=position
        )

    # ===============================
    # START CHARGING
    # ===============================
    if request.method == "POST":
        units = float(request.form["units"])
        price = float(request.form["price"])
        amount = units * price

        payment = process_payment(amount)

        cur.execute("""
            INSERT INTO charging_sessions
            (user_id, station_name, units, amount, tx_hash, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session.get("user_id"),
            station_name,
            units,
            amount,
            payment["tx_hash"],
            "Active"
        ))

        conn.commit()
        conn.close()

        return redirect("/user/history")

    conn.close()
    return render_template("charge_form.html", station_name=station_name)


# ===============================
# USER: COMPLETE CHARGING
# ===============================
@station_bp.route("/user/complete/<int:session_id>")
def complete_charging(session_id):
    if session.get("role") != "user":
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    # Get station name
    cur.execute(
        "SELECT station_name FROM charging_sessions WHERE id=?",
        (session_id,)
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return redirect("/user/history")

    station_name = row[0]

    # Mark session completed
    cur.execute(
        "UPDATE charging_sessions SET status='Completed' WHERE id=?",
        (session_id,)
    )

    # Remove first user from queue (FIFO)
    cur.execute("""
        DELETE FROM waiting_queue
        WHERE id = (
            SELECT id FROM waiting_queue
            WHERE station_name=?
            ORDER BY joined_at ASC
            LIMIT 1
        )
    """, (station_name,))

    conn.commit()
    conn.close()

    return redirect("/user/history")


# ===============================
# USER: CHECK QUEUE STATUS (API)
# ===============================
@station_bp.route("/api/queue-status/<station_name>")
def check_queue_status(station_name):
    """
    API endpoint to check if user can now charge
    Returns JSON with queue position and availability
    """
    if session.get("role") != "user":
        return {"error": "Unauthorized"}, 403

    conn = get_db()
    cur = conn.cursor()

    # Get total chargers
    cur.execute(
        "SELECT chargers FROM stations WHERE name=?",
        (station_name,)
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"error": "Station not found"}, 404

    total_chargers = row[0]

    # Count active sessions
    cur.execute(
        "SELECT COUNT(*) FROM charging_sessions WHERE station_name=? AND status='Active'",
        (station_name,)
    )
    active_sessions = cur.fetchone()[0]

    # Check if user is still in queue
    cur.execute("""
        SELECT COUNT(*) FROM waiting_queue
        WHERE station_name=? AND user_id=?
    """, (station_name, session.get("user_id")))
    in_queue = cur.fetchone()[0]

    if not in_queue:
        conn.close()
        return {"error": "Not in queue"}, 400

    # Get queue position
    cur.execute("""
        SELECT COUNT(*)
        FROM waiting_queue
        WHERE station_name=?
          AND joined_at <= (
            SELECT joined_at FROM waiting_queue
            WHERE station_name=? AND user_id=?
            ORDER BY joined_at ASC
            LIMIT 1
          )
    """, (station_name, station_name, session.get("user_id")))

    position = cur.fetchone()[0]

    # Check if slot is available (position is 1 or less and not all chargers are in use)
    can_charge = position <= 1 and active_sessions < total_chargers

    conn.close()

    return {
        "position": position,
        "active_sessions": active_sessions,
        "total_chargers": total_chargers,
        "can_charge": can_charge
    }


# ===============================# USER: CHARGING HISTORY
# ===============================
@station_bp.route("/user/history")
def charging_history():
    if session.get("role") != "user":
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, station_name, units, amount, tx_hash, status, started_at, completed_at
        FROM charging_sessions
        WHERE user_id=?
        ORDER BY id DESC
    """, (session.get("user_id"),))
    history = cur.fetchall()
    conn.close()

    return render_template("charging_history.html", history=history)


# ===============================
# USER: STOP/COMPLETE CHARGING
# ===============================
@station_bp.route("/user/stop-charging/<int:session_id>", methods=["POST"])
def stop_charging(session_id):
    if session.get("role") != "user":
        return {"error": "Unauthorized"}, 403

    conn = get_db()
    cur = conn.cursor()

    # Verify this is the user's session
    cur.execute("""
        SELECT id, station_name, status FROM charging_sessions
        WHERE id=? AND user_id=?
    """, (session_id, session.get("user_id")))
    
    session_data = cur.fetchone()
    if not session_data:
        conn.close()
        return {"error": "Session not found"}, 404

    session_id_check, station_name, current_status = session_data

    if current_status != "Active":
        conn.close()
        return {"error": "Only active sessions can be stopped"}, 400

    # Compute duration and ensure amount is recorded, then mark as completed
    from datetime import datetime
    # Fetch start time, units and existing amount
    cur.execute("SELECT started_at, units, amount, station_name FROM charging_sessions WHERE id=?", (session_id,))
    info = cur.fetchone()
    started_at, units, existing_amount, station = info

    # Parse started_at (SQLite default format: YYYY-MM-DD HH:MM:SS)
    def parse_ts(ts):
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            from datetime import datetime as _dt
            try:
                return _dt.strptime(ts.split('.')[0], "%Y-%m-%d %H:%M:%S")
            except Exception:
                return None

    start_dt = parse_ts(started_at)
    now = datetime.now()
    duration_minutes = None
    if start_dt:
        duration_minutes = int((now - start_dt).total_seconds() // 60)

    # If amount missing or zero, compute from station price
    amount_to_set = existing_amount
    if not existing_amount:
        cur.execute("SELECT price FROM stations WHERE name=?", (station,))
        r = cur.fetchone()
        price = r[0] if r else 0
        amount_to_set = units * price if units else 0

    cur.execute("""
        UPDATE charging_sessions 
        SET status='Completed', completed_at=?, duration_minutes=?, amount=?
        WHERE id=?
    """, (now, duration_minutes, amount_to_set, session_id))

    # Remove first user from queue (for next user)
    cur.execute("""
        DELETE FROM waiting_queue
        WHERE id = (
            SELECT id FROM waiting_queue
            WHERE station_name=?
            ORDER BY joined_at ASC
            LIMIT 1
        )
    """, (station_name,))

    conn.commit()
    conn.close()

    return {"status": "success", "message": "Charging stopped"}, 200


# ===============================
# OWNER: GET ACTIVE CHARGING SESSIONS
# ===============================
@station_bp.route("/owner/active-sessions")
def owner_active_sessions():
    if session.get("role") != "owner":
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    # Get all stations owned by this owner
    cur.execute("""
        SELECT id, name FROM stations WHERE owner_id=?
    """, (session.get("user_id"),))
    
    owner_stations = cur.fetchall()
    station_ids = [s[0] for s in owner_stations]

    if not station_ids:
        conn.close()
        return render_template("owner_active_sessions.html", sessions=[])

    # Get active charging sessions for these stations
    placeholders = ','.join('?' * len(owner_stations))
    station_names = [s[1] for s in owner_stations]
    
    cur.execute(f"""
        SELECT cs.id, cs.user_id, cs.station_name, cs.units, cs.amount, 
               cs.status, cs.started_at, u.name, u.email
        FROM charging_sessions cs
        JOIN users u ON cs.user_id = u.id
        WHERE cs.station_name IN ({placeholders})
        AND cs.status = 'Active'
        ORDER BY cs.started_at DESC
    """, station_names)
    
    sessions = cur.fetchall()
    conn.close()

    return render_template("owner_active_sessions.html", sessions=sessions)


# ===============================
# OWNER: COMPLETE USER'S CHARGING
# ===============================
@station_bp.route("/owner/complete-charging/<int:session_id>", methods=["POST"])
def owner_complete_charging(session_id):
    if session.get("role") != "owner":
        return {"error": "Unauthorized"}, 403

    conn = get_db()
    cur = conn.cursor()

    # Get session and verify ownership
    cur.execute("""
        SELECT cs.id, cs.station_name, cs.status, s.owner_id
        FROM charging_sessions cs
        JOIN stations s ON cs.station_name = s.name
        WHERE cs.id=?
    """, (session_id,))
    
    session_data = cur.fetchone()
    if not session_data:
        conn.close()
        return {"error": "Session not found"}, 404

    session_id_check, station_name, status, owner_id = session_data

    if owner_id != session.get("user_id"):
        conn.close()
        return {"error": "Unauthorized"}, 403

    if status != "Active":
        conn.close()
        return {"error": "Only active sessions can be completed"}, 400

    # Compute duration and ensure amount is recorded, then mark as completed
    from datetime import datetime
    cur.execute("SELECT started_at, units, amount FROM charging_sessions WHERE id=?", (session_id,))
    info = cur.fetchone()
    started_at, units, existing_amount = info

    def parse_ts(ts):
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            from datetime import datetime as _dt
            try:
                return _dt.strptime(ts.split('.')[0], "%Y-%m-%d %H:%M:%S")
            except Exception:
                return None

    start_dt = parse_ts(started_at)
    now = datetime.now()
    duration_minutes = None
    if start_dt:
        duration_minutes = int((now - start_dt).total_seconds() // 60)

    amount_to_set = existing_amount
    if not existing_amount:
        cur.execute("SELECT price FROM stations WHERE name=?", (station_name,))
        r = cur.fetchone()
        price = r[0] if r else 0
        amount_to_set = units * price if units else 0

    cur.execute("""
        UPDATE charging_sessions 
        SET status='Completed', completed_at=?, duration_minutes=?, amount=?
        WHERE id=?
    """, (now, duration_minutes, amount_to_set, session_id))

    # Remove first user from queue
    cur.execute("""
        DELETE FROM waiting_queue
        WHERE id = (
            SELECT id FROM waiting_queue
            WHERE station_name=?
            ORDER BY joined_at ASC
            LIMIT 1
        )
    """, (station_name,))

    conn.commit()
    conn.close()

    return {"status": "success", "message": "Charging completed"}, 200


# ===============================
# OWNER: CANCEL USER'S CHARGING
# ===============================
@station_bp.route("/owner/cancel-charging/<int:session_id>", methods=["POST"])
def owner_cancel_charging(session_id):
    if session.get("role") != "owner":
        return {"error": "Unauthorized"}, 403

    conn = get_db()
    cur = conn.cursor()

    # Get session and verify ownership
    cur.execute("""
        SELECT cs.id, cs.station_name, cs.status, s.owner_id
        FROM charging_sessions cs
        JOIN stations s ON cs.station_name = s.name
        WHERE cs.id=?
    """, (session_id,))
    
    session_data = cur.fetchone()
    if not session_data:
        conn.close()
        return {"error": "Session not found"}, 404

    session_id_check, station_name, status, owner_id = session_data

    if owner_id != session.get("user_id"):
        conn.close()
        return {"error": "Unauthorized"}, 403

    # Mark as cancelled (set completed_at)
    from datetime import datetime
    cur.execute("SELECT started_at FROM charging_sessions WHERE id=?", (session_id,))
    started_at = cur.fetchone()[0]

    def parse_ts(ts):
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            from datetime import datetime as _dt
            try:
                return _dt.strptime(ts.split('.')[0], "%Y-%m-%d %H:%M:%S")
            except Exception:
                return None

    start_dt = parse_ts(started_at)
    now = datetime.now()
    duration_minutes = None
    if start_dt:
        duration_minutes = int((now - start_dt).total_seconds() // 60)

    cur.execute("""
        UPDATE charging_sessions 
        SET status='Cancelled', completed_at=?, duration_minutes=?
        WHERE id=?
    """, (now, duration_minutes, session_id))

    conn.commit()
    conn.close()

    return {"status": "success", "message": "Charging cancelled"}, 200


# ===============================
# AI CHATBOT
# ===============================
@station_bp.route("/user/chat", methods=["GET", "POST"])
def chat():
    if session.get("role") != "user":
        return redirect("/login")
    
    from ai.chatbot import chat_with_bot
    
    if request.method == "POST":
        user_message = request.form.get("message", "").strip()
        
        if not user_message:
            return render_template("chat_interface.html", error="Please enter a message")
        
        response, is_error = chat_with_bot(user_message)
        
        return render_template("chat_interface.html", 
                             user_message=user_message,
                             bot_response=response,
                             is_error=is_error)
    
    return render_template("chat_interface.html")


# ===============================
# USER INSIGHTS & ANALYTICS
# ===============================
@station_bp.route("/user/insights", methods=["GET"])
def user_insights():
    if session.get("role") != "user":
        return redirect("/login")
    
    from ai.insights import get_user_insights_dashboard
    
    user_id = session.get('user_id')
    insights = get_user_insights_dashboard(user_id)
    
    return render_template("user_insights.html", insights=insights)


# ===============================
# NATURAL LANGUAGE SEARCH
# ===============================
@station_bp.route("/user/nl-search", methods=["GET", "POST"])
def nl_search():
    if session.get("role") != "user":
        return redirect("/login")
    
    from ai.nl_query import search_with_natural_language
    
    results = None
    explanation = None
    query = None
    
    if request.method == "POST":
        query = request.form.get("query", "").strip()
        
        if not query:
            return render_template("nl_search.html", error="Please enter a search query")
        
        # Get all stations
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT name, location, chargers, price, green_score
            FROM stations WHERE approved = 1
        """)
        all_stations = cur.fetchall()
        conn.close()
        
        # Perform search
        search_result = search_with_natural_language(query, all_stations)
        results = search_result["results"]
        explanation = search_result["explanation"]
    
    return render_template("nl_search.html", 
                         results=results,
                         explanation=explanation,
                         query=query)


# ===============================
# STATION ANALYTICS
# ===============================
@station_bp.route("/user/station-analytics/<station_name>", methods=["GET"])
def station_analytics(station_name):
    if session.get("role") != "user":
        return redirect("/login")
    
    from ai.analytics import get_all_analytics_summary
    
    analytics = get_all_analytics_summary(station_name)
    
    return render_template("station_analytics.html", 
                         station_name=station_name,
                         analytics=analytics)


# ===============================
# GOOGLE MAPS INTEGRATION
# ===============================
@station_bp.route("/user/map-search", methods=["GET", "POST"])
def map_search():
    if session.get("role") != "user":
        return redirect("/login")
    
    from ai.map_utils import get_all_stations_with_location, search_stations_by_location, get_map_config
    
    stations = []
    search_performed = False
    search_type = None
    
    if request.method == "POST":
        search_type = request.form.get("search_type", "all")
        search_performed = True
        
        if search_type == "all":
            # Get all stations
            stations = get_all_stations_with_location()
        
        elif search_type == "nearby":
            # Search by user location
            lat = float(request.form.get("latitude", 28.6139))
            lng = float(request.form.get("longitude", 77.2090))
            radius = float(request.form.get("radius", 10))
            
            stations = search_stations_by_location(lat, lng, radius)
        
        elif search_type == "filter":
            # Filter by criteria
            all_stations = get_all_stations_with_location()
            green_min = int(request.form.get("green_min", 0))
            price_max = float(request.form.get("price_max", 1000))
            chargers_min = int(request.form.get("chargers_min", 0))
            
            stations = [
                s for s in all_stations
                if s["green_score"] >= green_min
                and s["price"] <= price_max
                and s["chargers"] >= chargers_min
            ]
    else:
        # Default: show all stations
        stations = get_all_stations_with_location()
    
    map_config = get_map_config()
    
    return render_template("map_search.html",
                         stations=stations,
                         map_config=map_config,
                         search_performed=search_performed,
                         search_type=search_type)


@station_bp.route("/user/map-booking/<int:station_id>", methods=["GET", "POST"])
def map_booking(station_id):
    if session.get("role") != "user":
        return redirect("/login")
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get station details
    cur.execute("""
        SELECT name, location, chargers, price, green_score
        FROM stations
        WHERE id = ? AND approved = 1
    """, (station_id,))
    
    station = cur.fetchone()
    conn.close()
    
    if not station:
        return "Station not found", 404
    
    if request.method == "POST":
        units = float(request.form.get("units", 10))
        
        # Redirect to charging page
        return redirect(f"/user/charge/{station[0]}?price={station[3]}&units={units}")
    
    return render_template("map_booking.html",
                         station_id=station_id,
                         station={
                             "name": station[0],
                             "location": station[1],
                             "chargers": station[2],
                             "price": station[3],
                             "green_score": station[4]
                         })