#!/usr/bin/env python3
"""
Seed data script for local SQLite database (opsagent_dev.db).
Populates realistic operational data for PT Nusantara Coal Operations.
"""
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "opsagent_dev.db"

def seed_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Drop existing tables to recreate with complete schema
    tables = ["stockpiles", "coal_inventory", "barges", "barge_shipments", "customers", "suppliers", "daily_production"]
    for t in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {t};")

    # 1. Customers
    cursor.execute("""
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        customer_code TEXT UNIQUE,
        company_name TEXT,
        industry_type TEXT,
        delivery_port TEXT,
        payment_term_days INT,
        credit_limit_usd REAL,
        status TEXT
    );
    """)
    cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
        (1, "CUST-PLN-01", "PT PLN Energi Primer Indonesia", "PLTU Pembangkit", "Pelabuhan PLTU Suralaya", 45, 15000000.0, "ACTIVE"),
        (2, "CUST-SMN-01", "PT Semen Indonesia (Persero) Tbk", "Pabrik Semen", "Pelabuhan Khusus Tuban", 30, 8000000.0, "ACTIVE"),
        (3, "CUST-NCK-01", "PT Gunbuster Nickel Industry", "Smelter Nikel", "Jetty Morowali", 30, 12000000.0, "ACTIVE"),
        (4, "CUST-NCK-02", "PT Huadi Nickel-Alloy Indonesia", "Smelter Nikel", "Jetty Bantaeng", 14, 5000000.0, "ACTIVE"),
        (5, "CUST-JWP-01", "PT Jawa Power", "PLTU Swasta (IPP)", "Pelabuhan Paiton", 30, 9500000.0, "ACTIVE"),
    ])

    # 2. Suppliers
    cursor.execute("""
    CREATE TABLE suppliers (
        id INTEGER PRIMARY KEY,
        supplier_code TEXT UNIQUE,
        company_name TEXT,
        concession_area TEXT,
        monthly_quota_mt REAL,
        status TEXT
    );
    """)
    cursor.executemany("INSERT INTO suppliers VALUES (?, ?, ?, ?, ?, ?)", [
        (1, "SUP-KPC-01", "PT Kaltim Prima Mining Concession", "Sangatta, Kutai Timur", 150000.0, "ACTIVE"),
        (2, "SUP-ADR-02", "PT Adaro Minerals Indo", "Tabalong, Kalsel", 120000.0, "ACTIVE"),
        (3, "SUP-BPN-03", "PT Borneo Pasir Energi", "Muara Berau, Kaltim", 80000.0, "ACTIVE"),
        (4, "SUP-BKT-04", "PT Bukit Asam Tambang Prima", "Tanjung Enim", 100000.0, "ACTIVE"),
    ])

    # 3. Stockpiles
    cursor.execute("""
    CREATE TABLE stockpiles (
        id INTEGER PRIMARY KEY,
        stockpile_code TEXT UNIQUE,
        stockpile_name TEXT,
        location TEXT,
        province TEXT,
        max_capacity_mt REAL,
        current_stock_mt REAL,
        manager_name TEXT,
        status TEXT
    );
    """)
    cursor.executemany("INSERT INTO stockpiles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        (1, "STK-PLR-01", "Stockpile Palaran Jetty", "Palaran, Samarinda", "Kalimantan Timur", 120000.0, 84500.0, "Bambang Sudiro", "OPERATIONAL"),
        (2, "STK-KRG-02", "Stockpile Kariangau Interport", "Kariangau, Balikpapan", "Kalimantan Timur", 250000.0, 192000.0, "Hendra Kusuma", "OPERATIONAL"),
        (3, "STK-BRU-03", "Stockpile Muara Berau Floating Terminal", "Muara Berau", "Kalimantan Timur", 180000.0, 115000.0, "Ferry Irawan", "OPERATIONAL"),
    ])

    # 4. Coal Inventory
    cursor.execute("""
    CREATE TABLE coal_inventory (
        id INTEGER PRIMARY KEY,
        stockpile_id INT,
        grade TEXT,
        calorific_value_gar INT,
        total_moisture_pct REAL,
        ash_content_pct REAL,
        total_sulfur_pct REAL,
        tonnage_mt REAL,
        batch_number TEXT,
        temperature_celsius REAL,
        status TEXT
    );
    """)
    cursor.executemany("INSERT INTO coal_inventory VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        (1, 1, "GAR 4200", 4210, 34.2, 5.8, 0.38, 42500.0, "BAT-2026-0301", 39.2, "AVAILABLE"),
        (2, 1, "GAR 5000", 5025, 26.5, 7.2, 0.65, 42000.0, "BAT-2026-0302", 41.0, "AVAILABLE"),
        (3, 2, "GAR 3800", 3820, 38.0, 4.9, 0.25, 95000.0, "BAT-2026-0303", 37.5, "AVAILABLE"),
        (4, 2, "GAR 4200", 4215, 34.0, 5.7, 0.40, 97000.0, "BAT-2026-0304", 42.1, "AVAILABLE"),
        (5, 3, "GAR 4200", 4220, 33.8, 5.9, 0.42, 65000.0, "BAT-2026-0305", 38.0, "AVAILABLE"),
        (6, 3, "GAR 5800", 5810, 16.2, 9.1, 0.82, 50000.0, "BAT-2026-0306", 44.5, "AVAILABLE"),
    ])

    # 5. Barges
    cursor.execute("""
    CREATE TABLE barges (
        id INTEGER PRIMARY KEY,
        barge_code TEXT UNIQUE,
        barge_name TEXT,
        tugboat_name TEXT,
        capacity_feet INT,
        max_capacity_mt REAL,
        owner_company TEXT,
        status TEXT
    );
    """)
    cursor.executemany("INSERT INTO barges VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
        (1, "BG-301", "BG Trans Coal 301", "TB Rajawali 08", 300, 8000.0, "PT Pelayaran Sejahtera", "IN_TRANSIT"),
        (2, "BG-302", "BG Samudra Jaya 02", "TB Megah 01", 300, 7800.0, "PT Maritim Samudra", "IN_TRANSIT"),
        (3, "BG-330", "BG Nusantara 330", "TB Perkasa 12", 330, 10500.0, "PT Borneo Bahari Lines", "LOADING"),
        (4, "BG-303", "BG Kaltim Trans 05", "TB Bahari 03", 300, 8200.0, "PT Pelayaran Nusantara", "AVAILABLE"),
    ])

    # 6. Barge Shipments
    cursor.execute("""
    CREATE TABLE barge_shipments (
        id INTEGER PRIMARY KEY,
        shipment_number TEXT UNIQUE,
        barge_id INT,
        customer_id INT,
        stockpile_origin_id INT,
        coal_grade TEXT,
        tonnage_loaded_mt REAL,
        origin_jetty TEXT,
        destination_port TEXT,
        status TEXT,
        etd TEXT,
        eta TEXT
    );
    """)
    now = datetime.now()
    cursor.executemany("INSERT INTO barge_shipments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        (1, "SHP-2026-0390", 2, 1, 1, "GAR 4200", 7800.0, "Palaran Jetty, Samarinda", "Pelabuhan PLTU Suralaya", "SAILING", (now - timedelta(days=2)).strftime("%Y-%m-%d"), (now + timedelta(days=3)).strftime("%Y-%m-%d")),
        (2, "SHP-2026-0395", 1, 3, 2, "GAR 4200", 7950.0, "Kariangau Interport, Balikpapan", "Jetty Morowali", "SAILING", (now - timedelta(days=1)).strftime("%Y-%m-%d"), (now + timedelta(days=4)).strftime("%Y-%m-%d")),
        (3, "SHP-2026-0382", 4, 2, 1, "GAR 5000", 6500.0, "Palaran Jetty, Samarinda", "Pelabuhan Khusus Tuban", "DISCHARGING", (now - timedelta(days=5)).strftime("%Y-%m-%d"), (now - timedelta(days=1)).strftime("%Y-%m-%d")),
        (4, "SHP-2026-0401", 3, 5, 3, "GAR 5800", 10200.0, "Muara Berau Floating Terminal", "Pelabuhan Paiton", "LOADING", (now + timedelta(days=1)).strftime("%Y-%m-%d"), (now + timedelta(days=6)).strftime("%Y-%m-%d")),
    ])

    # 7. Daily Production
    cursor.execute("""
    CREATE TABLE daily_production (
        id INTEGER PRIMARY KEY,
        production_date TEXT,
        pit_name TEXT,
        grade TEXT,
        mined_tonnage_mt REAL,
        crushed_tonnage_mt REAL,
        rainfall_mm REAL
    );
    """)
    cursor.executemany("INSERT INTO daily_production VALUES (?, ?, ?, ?, ?, ?, ?)", [
        (1, (now - timedelta(days=1)).strftime("%Y-%m-%d"), "Pit A North", "GAR 4200", 12500.0, 11800.0, 0.0),
        (2, (now - timedelta(days=1)).strftime("%Y-%m-%d"), "Pit B South", "GAR 5000", 9400.0, 9200.0, 5.5),
        (3, now.strftime("%Y-%m-%d"), "Pit A North", "GAR 4200", 13200.0, 12900.0, 0.0),
    ])

    conn.commit()
    conn.close()
    print("Local database opsagent_dev.db seeded successfully with full operational schema!")

if __name__ == "__main__":
    seed_database()
