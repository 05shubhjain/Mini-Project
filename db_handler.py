import sqlite3
import numpy as np
import os
from datetime import datetime

DB_NAME = os.path.join(os.path.dirname(__file__), "faces.db")

def connect_db():
    return sqlite3.connect(DB_NAME)

def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    
    # Faces table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        embedding BLOB
    )
    """)
    
    # Payroll table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payroll (
        name TEXT PRIMARY KEY,
        base_salary REAL DEFAULT 60000,
        deductions REAL DEFAULT 0,
        net_salary REAL DEFAULT 60000
    )
    """)
    
    # ✅ Attendance table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        date TEXT,
        time TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def insert_face(name, embedding):
    conn = connect_db()
    cursor = conn.cursor()
    emb_bytes = embedding.astype(np.float32).tobytes()
    
    cursor.execute("INSERT INTO faces (name, embedding) VALUES (?, ?)", (name, emb_bytes))
    # also create payroll entry if not exists
    cursor.execute("INSERT OR IGNORE INTO payroll (name) VALUES (?)", (name,))
    
    conn.commit()
    conn.close()

def get_all_faces():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, embedding FROM faces")
    results = []
    for name, emb_bytes in cursor.fetchall():
        embedding = np.frombuffer(emb_bytes, dtype=np.float32)
        results.append((name, embedding))
    conn.close()
    return results

# ✅ Attendance functions
def mark_attendance(name):
    conn = connect_db()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("SELECT * FROM attendance WHERE name=? AND date=?", (name, today))
    result = cursor.fetchone()
    
    if result is None:
        current_time = datetime.now().strftime("%H:%M:%S")
        cursor.execute("INSERT INTO attendance (name, date, time) VALUES (?, ?, ?)", (name, today, current_time))
        conn.commit()
        conn.close()
        return current_time
    else:
        conn.close()
        return None

# Payroll functions
def update_deduction(name, deduction):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE payroll 
        SET deductions = deductions + ?, 
            net_salary = base_salary - deductions 
        WHERE name = ?
    """, (deduction, name))
    conn.commit()
    conn.close()

def mark_absent(name):
    conn = connect_db()
    cursor = conn.cursor()
    daily_salary = 60000 / 30  
    cursor.execute("""
        UPDATE payroll 
        SET deductions = deductions + ?, 
            net_salary = base_salary - deductions 
        WHERE name = ?
    """, (daily_salary, name))
    conn.commit()
    conn.close()

def get_payroll(name):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payroll WHERE name=?", (name,))
    result = cursor.fetchone()
    conn.close()
    return result
