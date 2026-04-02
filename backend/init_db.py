import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS systems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname TEXT NOT NULL,
    ip_address TEXT,
    operating_system TEXT,
    os_version TEXT,
    owner_team TEXT,
    environment TEXT,
    internet_facing INTEGER,
    criticality INTEGER,
    last_seen TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS software_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_id INTEGER,
    software_name TEXT NOT NULL,
    installed_version TEXT NOT NULL,
    last_patch_date TEXT,
    FOREIGN KEY(system_id) REFERENCES systems(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS latest_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    software_name TEXT NOT NULL,
    latest_version TEXT NOT NULL,
    release_date TEXT NOT NULL,
    severity_base INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS risk_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_id INTEGER,
    software_id INTEGER,
    latest_version_id INTEGER,
    days_outdated INTEGER,
    missing_update INTEGER,
    risk_score REAL,
    severity TEXT,
    predicted_high_risk INTEGER,
    analyzed_at TEXT,
    FOREIGN KEY(system_id) REFERENCES systems(id),
    FOREIGN KEY(software_id) REFERENCES software_inventory(id),
    FOREIGN KEY(latest_version_id) REFERENCES latest_versions(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    system_id INTEGER,
    message TEXT,
    severity TEXT,
    status TEXT,
    created_at TEXT,
    FOREIGN KEY(system_id) REFERENCES systems(id)
)
""")

conn.commit()
conn.close()

print("Database created successfully")