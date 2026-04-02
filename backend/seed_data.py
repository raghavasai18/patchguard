import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

systems = [
    ("web-prod-01", "192.168.1.10", "Ubuntu", "20.04", "Security Team", "Production", 1, 5, "2026-04-01"),
    ("app-prod-02", "192.168.1.11", "Windows Server", "2019", "Infra Team", "Production", 0, 4, "2026-04-01"),
    ("test-db-01", "192.168.1.12", "CentOS", "8", "QA Team", "Test", 0, 3, "2026-04-01"),
    ("dev-api-01", "192.168.1.13", "Ubuntu", "22.04", "Dev Team", "Development", 1, 2, "2026-04-01")
]

cursor.executemany("""
INSERT INTO systems (
    hostname, ip_address, operating_system, os_version,
    owner_team, environment, internet_facing, criticality, last_seen
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", systems)

software_inventory = [
    (1, "nginx", "1.18.0", "2026-01-10"),
    (1, "openssl", "1.1.1", "2025-12-20"),
    (2, "apache", "2.4.52", "2026-02-10"),
    (3, "mysql", "8.0.28", "2025-12-01"),
    (4, "python", "3.10.4", "2026-01-15")
]

cursor.executemany("""
INSERT INTO software_inventory (
    system_id, software_name, installed_version, last_patch_date
) VALUES (?, ?, ?, ?)
""", software_inventory)

latest_versions = [
    ("nginx", "1.24.0", "2026-01-01", 8),
    ("openssl", "3.0.12", "2026-01-15", 10),
    ("apache", "2.4.58", "2026-02-01", 7),
    ("mysql", "8.0.36", "2026-01-20", 9),
    ("python", "3.12.2", "2026-02-05", 6)
]

cursor.executemany("""
INSERT INTO latest_versions (
    software_name, latest_version, release_date, severity_base
) VALUES (?, ?, ?, ?)
""", latest_versions)

conn.commit()
conn.close()

print("Sample data inserted successfully")