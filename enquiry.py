import sqlite3
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Enquiry & Consultation API")
DB_PATH = "enquiries.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS enquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route TEXT NOT NULL,
                programme_interest TEXT NOT NULL,
                question TEXT NOT NULL,
                contact_email TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                programme_interest TEXT NOT NULL,
                preferred_slot TEXT NOT NULL,
                contact_email TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)


init_db()


class Enquiry(BaseModel):
    route: str
    programme_interest: str
    question: str
    contact_email: str
    status: str = "open"


class Consultation(BaseModel):
    programme_interest: str
    preferred_slot: str
    contact_email: str
    notes: Optional[str] = ""
    status: str = "requested"


# --- Endpoints ---
@app.post("/enquiries", status_code=201)
def post_enquiry(payload: Enquiry):
    created_at = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO enquiries (route, programme_interest, question, contact_email, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload.route,
                payload.programme_interest,
                payload.question,
                payload.contact_email,
                created_at,
                payload.status,
            ),
        )
        enquiry_id = cursor.lastrowid

    return {
        "id": enquiry_id,
        "route": payload.route,
        "programme_interest": payload.programme_interest,
        "question": payload.question,
        "contact_email": payload.contact_email,
        "created_at": created_at,
        "status": payload.status,
    }


@app.post("/consultations", status_code=201)
def post_consultation(payload: Consultation):
    created_at = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO consultations (programme_interest, preferred_slot, contact_email, notes, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload.programme_interest,
                payload.preferred_slot,
                payload.contact_email,
                payload.notes,
                created_at,
                payload.status,
            ),
        )
        consultation_id = cursor.lastrowid

    return {
        "id": consultation_id,
        "programme_interest": payload.programme_interest,
        "preferred_slot": payload.preferred_slot,
        "contact_email": payload.contact_email,
        "notes": payload.notes,
        "created_at": created_at,
        "status": payload.status,
    }


@app.get("/enquiries")
def get_enquiries():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM enquiries ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]