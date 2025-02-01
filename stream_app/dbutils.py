import sqlite3
from datetime import datetime
import cv2 as cv
import base64
import os

def load_database(db_name="/app/db/byakugan.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    conn.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("CREATE TABLE IF NOT EXISTS Recordings ( id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp INTEGER NOT NULL, path TEXT NOT NULL)")
    cursor.execute("SELECT name FROM sqlite_master WHERE name='Recordings' AND type='table'")
    if cursor.fetchone() is None:
        raise RuntimeError("Error creating Recordings table in database")
    
    cursor.execute("CREATE TABLE IF NOT EXISTS Alerts ( id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp INTEGER NOT NULL, recording_id INTEGER NOT NULL, description TEXT NOT NULL, thumbnail TEXT, FOREIGN KEY (recording_id) REFERENCES Recordings(id) ON DELETE CASCADE)")
    cursor.execute("SELECT name FROM sqlite_master WHERE name='Alerts' AND type='table'")
    if cursor.fetchone() is None:
        raise RuntimeError("Error creating Alerts table in database")
    
    cursor.execute("CREATE TABLE IF NOT EXISTS Settings ( name TEXT PRIMARY KEY, value TEXT NOT NULL )")
    cursor.execute("SELECT name FROM sqlite_master WHERE name='Settings' and type='table'")
    if cursor.fetchone() is None:
        raise RuntimeError("Error creating Settings table in database")

    return conn, cursor

def update_setting_value(conn, cursor, name, value):
    cursor.execute("INSERT OR REPLACE INTO Settings (name, value) VALUES (?, ?)", (name, value))
    conn.commit()

def get_setting_value(conn, cursor, name, defaultValue=None):
    cursor.execute("SELECT value FROM Settings WHERE name = ?", (name, ))
    row = cursor.fetchone()

    if row is None:
        return defaultValue
    else:
        return row[0]


def create_recording(conn, cursor, desc=None):
    cursor.execute("SELECT seq + 1 AS next_id FROM sqlite_sequence WHERE name = 'Recordings'")
    row = cursor.fetchone()

    if row is None:
        new_id = 1
    else:
        new_id = row[0]    

    record_filename = f'rec_{new_id}'
    current_timestamp = int(datetime.now().timestamp())
    cursor.execute("INSERT INTO Recordings (timestamp, path) VALUES (?, ?)", (current_timestamp, record_filename + ".mp4"))
    conn.commit()


    cursor.execute("INSERT INTO Alerts (timestamp, recording_id, description) VALUES (?, ?, ?)", (current_timestamp, cursor.lastrowid, desc))
    conn.commit()
    return record_filename, cursor.lastrowid

def add_thumbnail_to_alert(conn, cursor, alert_id, frame):
    fname = f't-{alert_id}.jpg'
    cv.imwrite("/app/thumbnails/" + fname, frame)

    cursor.execute("UPDATE Alerts SET thumbnail = ? WHERE id = ?", (fname, alert_id))
    conn.commit()

def get_alerts_data(conn, cursor, records_per_page, page_no):
    offset_number = page_no - 1
    cursor.execute("SELECT * FROM Alerts ORDER BY timestamp DESC LIMIT ? OFFSET ?", (records_per_page, offset_number * records_per_page))
    result_dict = []

    for row in cursor.fetchall():
        ts_readable = datetime.fromtimestamp(row[1]).strftime("%B %d, %Y %I:%M:%S %p")
        result_dict.append({"id" : row[0], "timestamp" : ts_readable, "description" : row[3], "thumbnail": row[4]})

    return result_dict

def get_alert_details(conn, cursor, alert_id):
    cursor.execute("""
                   SELECT Alerts.id, Alerts.timestamp, Alerts.description, Recordings.path, Alerts.thumbnail FROM Recordings 
                   INNER JOIN Alerts 
                   ON Recordings.id = Alerts.recording_id
                   WHERE Alerts.id = ?""", (alert_id, ))
    row = cursor.fetchone()

    if row is None:
        return None
    
    ts_readable = datetime.fromtimestamp(row[1]).strftime("%B %d, %Y %I:%M:%S %p")
    
    return {"id" : row[0], "timestamp" : ts_readable, "description" : row[2], "video" : row[3], "thumbnail" : row[4] }

def delete_alert(conn, cursor, alert_id):
    cursor.execute("""
                   SELECT Alerts.thumbnail, Recordings.path, Recordings.id FROM Recordings 
                   INNER JOIN Alerts 
                   ON Recordings.id = Alerts.recording_id
                   WHERE Alerts.id = ?""", (alert_id, ))
    row = cursor.fetchone()

    thumbnail_path = "/app/thumbnails/" + row[0]
    recording_path = "/app/recordings/" + row[1]
    rid = row[2]

    cursor.execute("DELETE FROM Alerts WHERE recording_id = ?", (rid, ))
    cursor.execute("DELETE FROM Recordings WHERE id = ?", (rid, ))
    conn.commit()

    os.remove(thumbnail_path)
    os.remove(recording_path)
