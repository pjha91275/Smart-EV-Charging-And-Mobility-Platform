from flask import Blueprint, render_template, request, redirect, session
from models.db import get_db

admin_bp = Blueprint("admin", __name__)

# Admin Login
@admin_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM admin WHERE username=? AND password=?",
            (username, password)
        )
        admin = cur.fetchone()
        conn.close()

        if admin:
            session["admin_logged_in"] = True
            return redirect("/admin/dashboard")
        else:
            return "Invalid Admin Credentials"

    return render_template("admin_login.html")


# Admin Dashboard
@admin_bp.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    # Initialize all variables
    total_users = 0
    total_stations = 0
    total_sessions = 0
    total_revenue = 0
    sessions = []

    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM users")
        result = cur.fetchone()
        total_users = result[0] if result else 0

        cur.execute("SELECT COUNT(*) FROM stations")
        result = cur.fetchone()
        total_stations = result[0] if result else 0

        cur.execute("SELECT COUNT(*) FROM charging_sessions")
        result = cur.fetchone()
        total_sessions = result[0] if result else 0

        cur.execute("SELECT IFNULL(SUM(amount), 0) FROM charging_sessions")
        result = cur.fetchone()
        total_revenue = result[0] if result else 0

        print("TOTAL USERS:", total_users)
        print("TOTAL STATIONS:", total_stations)
        print("TOTAL SESSIONS:", total_sessions)
        print("TOTAL REVENUE:", total_revenue)

        cur.execute("""
            SELECT station_name, units, amount, tx_hash, status
            FROM charging_sessions
        """)
        sessions = cur.fetchall() or []
        conn.close()

    except Exception as e:
        print(f"Error loading admin dashboard: {e}")
        import traceback
        traceback.print_exc()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_stations=total_stations,
        total_sessions=total_sessions,
        total_revenue=total_revenue,
        sessions=sessions
    )



# Admin Logout
@admin_bp.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect("/admin/login")

@admin_bp.route("/admin/stations")
def admin_stations():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, name, location, chargers, price, green_score, approved
            FROM stations
        """)
        stations = cur.fetchall() or []
        conn.close()
    except Exception as e:
        print(f"Error loading stations: {e}")
        stations = []

    return render_template("admin_stations.html", stations=stations)


@admin_bp.route('/admin/users')
def admin_users():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, role, blacklisted FROM users ORDER BY id DESC")
        users = cur.fetchall() or []
        conn.close()
    except Exception as e:
        print(f"Error loading users: {e}")
        users = []

    return render_template('admin_users.html', users=users)


@admin_bp.route('/admin/user-edit/<int:user_id>', methods=['GET', 'POST'])
def admin_user_edit(user_id):
    if not session.get("admin_logged_in"):
        return redirect('/admin/login')

    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        name = request.form.get('name').strip()
        email = request.form.get('email').strip().lower()
        role = request.form.get('role').strip()
        blacklisted = 1 if request.form.get('blacklisted') == 'on' else 0

        cur.execute("UPDATE users SET name=?, email=?, role=?, blacklisted=? WHERE id=?",
                    (name, email, role, blacklisted, user_id))
        conn.commit()
        conn.close()
        return redirect('/admin/users')

    cur.execute("SELECT id, name, email, role, blacklisted FROM users WHERE id=?", (user_id,))
    user = cur.fetchone()
    conn.close()
    if not user:
        return redirect('/admin/users')

    return render_template('admin_user_edit.html', user=user)


@admin_bp.route('/admin/user-blacklist/<int:user_id>', methods=['POST'])
def admin_user_blacklist(user_id):
    if not session.get("admin_logged_in"):
        return {"error": "Unauthorized"}, 403

    action = request.form.get('action')
    conn = get_db()
    cur = conn.cursor()
    if action == 'blacklist':
        cur.execute('UPDATE users SET blacklisted=1 WHERE id=?', (user_id,))
    else:
        cur.execute('UPDATE users SET blacklisted=0 WHERE id=?', (user_id,))
    conn.commit()
    conn.close()
    return redirect('/admin/users')

@admin_bp.route("/admin/approve-station/<int:station_id>")
def approve_station(station_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE stations SET approved=1 WHERE id=?
    """, (station_id,))
    conn.commit()
    conn.close()

    return redirect("/admin/stations")

@admin_bp.route("/admin/queue")
def admin_queue():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT w.station_name, u.name, w.joined_at
        FROM waiting_queue w
        JOIN users u ON w.user_id = u.id
        ORDER BY w.joined_at ASC
    """)
    queue = cur.fetchall()
    conn.close()

    return render_template("admin_queue.html", queue=queue)



