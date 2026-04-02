from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_NAME = "database.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_version(version):
    try:
        return [int(x) for x in version.split('.')]
    except:
        return [0]


def is_outdated(installed_version, latest_version):
    return normalize_version(installed_version) < normalize_version(latest_version)


def get_days_outdated(release_date_str):
    today = datetime.today().date()
    release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()
    return (today - release_date).days


def calculate_risk_score(days_outdated, criticality, internet_facing, environment, severity_base):
    if days_outdated <= 7:
        days_score = 10
    elif days_outdated <= 15:
        days_score = 30
    elif days_outdated <= 30:
        days_score = 60
    elif days_outdated <= 60:
        days_score = 80
    else:
        days_score = 100

    criticality_score = criticality * 20
    exposure_score = 100 if internet_facing else 30

    env_map = {
        "Development": 20,
        "Test": 40,
        "Production": 100
    }
    environment_score = env_map.get(environment, 20)

    software_severity_score = severity_base * 10

    risk_score = (
        0.35 * days_score +
        0.25 * criticality_score +
        0.15 * exposure_score +
        0.15 * environment_score +
        0.10 * software_severity_score
    )

    return round(min(risk_score, 100), 2)


def classify_severity(score):
    if score >= 75:
        return "Critical"
    elif score >= 55:
        return "High"
    elif score >= 30:
        return "Medium"
    return "Low"


def predict_high_risk(environment, internet_facing, days_outdated, criticality, risk_score, outdated_count):
    if environment == "Production" and internet_facing and days_outdated > 30:
        return 1
    if criticality >= 4 and risk_score >= 70:
        return 1
    if outdated_count >= 3:
        return 1
    if days_outdated > 45:
        return 1
    return 0


@app.route("/")
def home():
    return jsonify({"message": "PatchGuard backend running"})


@app.route("/systems", methods=["GET"])
def get_systems():
    conn = get_db_connection()
    systems = conn.execute("SELECT * FROM systems").fetchall()
    conn.close()
    return jsonify([dict(row) for row in systems])


@app.route("/systems", methods=["POST"])
def add_system():
    data = request.json

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO systems (
            hostname, ip_address, operating_system, os_version,
            owner_team, environment, internet_facing, criticality, last_seen
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["hostname"],
        data.get("ip_address", ""),
        data.get("operating_system", ""),
        data.get("os_version", ""),
        data.get("owner_team", ""),
        data.get("environment", "Development"),
        data.get("internet_facing", 0),
        data.get("criticality", 1),
        data.get("last_seen", datetime.today().strftime("%Y-%m-%d"))
    ))
    conn.commit()
    conn.close()

    return jsonify({"message": "System added successfully"})


@app.route("/inventory", methods=["POST"])
def add_inventory():
    data = request.json

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO software_inventory (
            system_id, software_name, installed_version, last_patch_date
        ) VALUES (?, ?, ?, ?)
    """, (
        data["system_id"],
        data["software_name"],
        data["installed_version"],
        data.get("last_patch_date", datetime.today().strftime("%Y-%m-%d"))
    ))
    conn.commit()
    conn.close()

    return jsonify({"message": "Software inventory added successfully"})


@app.route("/latest-version", methods=["POST"])
def add_latest_version():
    data = request.json

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO latest_versions (
            software_name, latest_version, release_date, severity_base
        ) VALUES (?, ?, ?, ?)
    """, (
        data["software_name"],
        data["latest_version"],
        data["release_date"],
        data.get("severity_base", 5)
    ))
    conn.commit()
    conn.close()

    return jsonify({"message": "Latest version added successfully"})


@app.route("/analyze", methods=["POST"])
def analyze():
    conn = get_db_connection()

    conn.execute("DELETE FROM risk_analysis")
    conn.execute("DELETE FROM alerts")
    conn.commit()

    systems = conn.execute("SELECT * FROM systems").fetchall()
    results = []

    for system in systems:
        inventory_items = conn.execute("""
            SELECT * FROM software_inventory WHERE system_id = ?
        """, (system["id"],)).fetchall()

        outdated_count = 0

        for item in inventory_items:
            latest = conn.execute("""
                SELECT * FROM latest_versions WHERE software_name = ?
            """, (item["software_name"],)).fetchone()

            if latest and is_outdated(item["installed_version"], latest["latest_version"]):
                outdated_count += 1
                days_outdated = get_days_outdated(latest["release_date"])

                risk_score = calculate_risk_score(
                    days_outdated,
                    system["criticality"],
                    system["internet_facing"],
                    system["environment"],
                    latest["severity_base"]
                )

                severity = classify_severity(risk_score)
                predicted = predict_high_risk(
                    system["environment"],
                    system["internet_facing"],
                    days_outdated,
                    system["criticality"],
                    risk_score,
                    outdated_count
                )

                analyzed_at = datetime.today().strftime("%Y-%m-%d")

                conn.execute("""
                    INSERT INTO risk_analysis (
                        system_id, software_id, latest_version_id,
                        days_outdated, missing_update, risk_score,
                        severity, predicted_high_risk, analyzed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    system["id"],
                    item["id"],
                    latest["id"],
                    days_outdated,
                    1,
                    risk_score,
                    severity,
                    predicted,
                    analyzed_at
                ))

                alert_message = f"{system['hostname']} has outdated {item['software_name']} ({item['installed_version']} -> {latest['latest_version']})"
                conn.execute("""
                    INSERT INTO alerts (
                        system_id, message, severity, status, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    system["id"],
                    alert_message,
                    severity,
                    "Open",
                    analyzed_at
                ))

                results.append({
                    "hostname": system["hostname"],
                    "software_name": item["software_name"],
                    "installed_version": item["installed_version"],
                    "latest_version": latest["latest_version"],
                    "days_outdated": days_outdated,
                    "risk_score": risk_score,
                    "severity": severity,
                    "predicted_high_risk": bool(predicted)
                })

    conn.commit()
    conn.close()

    return jsonify(results)


@app.route("/risks", methods=["GET"])
def get_risks():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT ra.*, s.hostname, si.software_name, si.installed_version, lv.latest_version
        FROM risk_analysis ra
        JOIN systems s ON ra.system_id = s.id
        JOIN software_inventory si ON ra.software_id = si.id
        JOIN latest_versions lv ON ra.latest_version_id = lv.id
        ORDER BY ra.risk_score DESC
    """).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/alerts", methods=["GET"])
def get_alerts():
    conn = get_db_connection()
    alerts = conn.execute("""
        SELECT a.*, s.hostname
        FROM alerts a
        JOIN systems s ON a.system_id = s.id
        ORDER BY a.created_at DESC
    """).fetchall()
    conn.close()
    return jsonify([dict(row) for row in alerts])


@app.route("/dashboard-summary", methods=["GET"])
def dashboard_summary():
    conn = get_db_connection()

    total_systems = conn.execute("SELECT COUNT(*) as count FROM systems").fetchone()["count"]
    total_inventory = conn.execute("SELECT COUNT(*) as count FROM software_inventory").fetchone()["count"]
    outdated_count = conn.execute("SELECT COUNT(*) as count FROM risk_analysis").fetchone()["count"]
    critical_alerts = conn.execute("SELECT COUNT(*) as count FROM alerts WHERE severity = 'Critical'").fetchone()["count"]
    predicted_high_risk = conn.execute("SELECT COUNT(*) as count FROM risk_analysis WHERE predicted_high_risk = 1").fetchone()["count"]

    compliance = 0
    if total_inventory > 0:
        compliance = round(((total_inventory - outdated_count) / total_inventory) * 100, 2)

    conn.close()

    return jsonify({
        "total_systems": total_systems,
        "total_software": total_inventory,
        "outdated_software": outdated_count,
        "critical_alerts": critical_alerts,
        "predicted_high_risk_systems": predicted_high_risk,
        "patch_compliance_percent": compliance
    })


import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))