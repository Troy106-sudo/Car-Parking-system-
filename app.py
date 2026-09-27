from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "parking-system-demo-key"

DB_NAME = "parking.db"
TOTAL_SLOTS = 20


def get_db():
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the required database tables and parking slots."""
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT NOT NULL,
            driver_name TEXT NOT NULL,
            slot_number INTEGER NOT NULL,
            entry_time TEXT NOT NULL,
            exit_time TEXT,
            duration_minutes INTEGER,
            amount REAL,
            status TEXT NOT NULL DEFAULT 'PARKED'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            slot_number INTEGER PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'AVAILABLE'
        )
    """)

    existing = conn.execute("SELECT COUNT(*) AS count FROM slots").fetchone()["count"]

    if existing == 0:
        for slot in range(1, TOTAL_SLOTS + 1):
            conn.execute(
                "INSERT INTO slots (slot_number, status) VALUES (?, ?)",
                (slot, "AVAILABLE")
            )

    conn.commit()
    conn.close()


def calculate_fee(minutes):
    """
    Calculate the parking fee according to the assignment:
    - Up to 30 minutes: Free
    - Up to 2 hours: KSh 50
    - Up to 4 hours: KSh 100
    - Up to 6 hours: KSh 300
    - More than 6 hours: KSh 500
    """
    if minutes <= 30:
        return 0
    elif minutes <= 120:
        return 50
    elif minutes <= 240:
        return 100
    elif minutes <= 360:
        return 300
    else:
        return 500


def calculate_duration(entry_time, exit_time):
    """Return the number of whole minutes between entry and exit."""
    entry = datetime.fromisoformat(entry_time)
    exit_ = datetime.fromisoformat(exit_time)
    seconds = max(0, (exit_ - entry).total_seconds())
    return int(seconds // 60)


@app.route("/")
def dashboard():
    """Display the main parking dashboard."""
    conn = get_db()

    slots = conn.execute(
        "SELECT * FROM slots ORDER BY slot_number"
    ).fetchall()

    parked = conn.execute("""
        SELECT * FROM vehicles
        WHERE status = 'PARKED'
        ORDER BY entry_time DESC
    """).fetchall()

    recent = conn.execute("""
        SELECT * FROM vehicles
        WHERE status = 'EXITED'
        ORDER BY exit_time DESC
        LIMIT 10
    """).fetchall()

    available_count = sum(1 for slot in slots if slot["status"] == "AVAILABLE")
    occupied_count = len(slots) - available_count

    conn.close()

    return render_template(
        "dashboard.html",
        slots=slots,
        parked=parked,
        recent=recent,
        available_count=available_count,
        occupied_count=occupied_count,
        total_slots=TOTAL_SLOTS
    )


@app.route("/entry", methods=["POST"])
def vehicle_entry():
    """Record a vehicle arrival and assign the first available slot."""
    plate = request.form.get("plate_number", "").strip().upper()
    driver = request.form.get("driver_name", "").strip()

    if not plate or not driver:
        flash("Please enter both the vehicle registration and driver name.", "error")
        return redirect(url_for("dashboard"))

    conn = get_db()

    duplicate = conn.execute("""
        SELECT id FROM vehicles
        WHERE plate_number = ? AND status = 'PARKED'
    """, (plate,)).fetchone()

    if duplicate:
        conn.close()
        flash("This vehicle is already inside the parking area.", "error")
        return redirect(url_for("dashboard"))

    slot = conn.execute("""
        SELECT slot_number FROM slots
        WHERE status = 'AVAILABLE'
        ORDER BY slot_number
        LIMIT 1
    """).fetchone()

    if not slot:
        conn.close()
        flash("Parking is full. No available slot.", "error")
        return redirect(url_for("dashboard"))

    slot_number = slot["slot_number"]
    entry_time = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    conn.execute("""
        INSERT INTO vehicles
        (plate_number, driver_name, slot_number, entry_time, status)
        VALUES (?, ?, ?, ?, 'PARKED')
    """, (plate, driver, slot_number, entry_time))

    conn.execute("""
        UPDATE slots SET status = 'OCCUPIED'
        WHERE slot_number = ?
    """, (slot_number,))

    conn.commit()
    conn.close()

    flash(
        f"Vehicle {plate} entered successfully. Assigned slot {slot_number}.",
        "success"
    )
    return redirect(url_for("dashboard"))


@app.route("/exit/<int:vehicle_id>", methods=["POST"])
def vehicle_exit(vehicle_id):
    """Calculate parking time and amount, then complete payment/barrier opening."""
    conn = get_db()

    vehicle = conn.execute(
        "SELECT * FROM vehicles WHERE id = ? AND status = 'PARKED'",
        (vehicle_id,)
    ).fetchone()

    if not vehicle:
        conn.close()
        flash("Vehicle not found or it has already exited.", "error")
        return redirect(url_for("dashboard"))

    exit_time = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    minutes = calculate_duration(vehicle["entry_time"], exit_time)
    amount = calculate_fee(minutes)

    # In this demo, submitting the exit form represents payment confirmation.
    # The barrier is considered open only after this transaction is completed.
    conn.execute("""
        UPDATE vehicles
        SET exit_time = ?, duration_minutes = ?, amount = ?, status = 'EXITED'
        WHERE id = ?
    """, (exit_time, minutes, amount, vehicle_id))

    conn.execute("""
        UPDATE slots SET status = 'AVAILABLE'
        WHERE slot_number = ?
    """, (vehicle["slot_number"],))

    conn.commit()
    conn.close()

    flash(
        f"Payment of KSh {amount:.0f} recorded for {vehicle['plate_number']}. "
        f"Barrier opened. Slot {vehicle['slot_number']} is now available.",
        "success"
    )
    return redirect(url_for("dashboard"))


@app.route("/api/status")
def api_status():
    """Return parking availability as JSON for future integrations."""
    conn = get_db()
    slots = conn.execute(
        "SELECT slot_number, status FROM slots ORDER BY slot_number"
    ).fetchall()
    conn.close()

    return jsonify({
        "total": TOTAL_SLOTS,
        "available": sum(1 for s in slots if s["status"] == "AVAILABLE"),
        "occupied": sum(1 for s in slots if s["status"] == "OCCUPIED"),
        "slots": [dict(s) for s in slots]
    })


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
