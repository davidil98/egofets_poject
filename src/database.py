"""SQLite database for EGOFET sample and measurement tracking."""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parent.parent / "samples.db"


def get_connection(path: Path | None = None) -> sqlite3.Connection:
    db = path or DB_PATH
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: Path | None = None) -> None:
    conn = get_connection(path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS wafers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            substrate TEXT DEFAULT 'Kapton',
            size_mm TEXT DEFAULT '75um',
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            notes TEXT,
            photo_path TEXT
        );

        CREATE TABLE IF NOT EXISTS samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wafer_id INTEGER NOT NULL,
            piece_number INTEGER NOT NULL CHECK(piece_number BETWEEN 1 AND 12),
            label TEXT NOT NULL UNIQUE,
            functionalization TEXT DEFAULT 'none',
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            notes TEXT,
            FOREIGN KEY (wafer_id) REFERENCES wafers(id) ON DELETE CASCADE,
            UNIQUE(wafer_id, piece_number)
        );

        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id INTEGER NOT NULL,
            device_number INTEGER NOT NULL CHECK(device_number BETWEEN 1 AND 6),
            channel_w_um REAL DEFAULT 10000,
            channel_l_um REAL DEFAULT 20,
            notes TEXT,
            FOREIGN KEY (sample_id) REFERENCES samples(id) ON DELETE CASCADE,
            UNIQUE(sample_id, device_number)
        );

        CREATE TABLE IF NOT EXISTS steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id INTEGER NOT NULL,
            step_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK(status IN ('pending','in_progress','completed','aborted')),
            started_at TEXT,
            completed_at TEXT,
            params_json TEXT DEFAULT '{}',
            notes TEXT,
            photo_paths TEXT DEFAULT '[]',
            FOREIGN KEY (sample_id) REFERENCES samples(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            sample_id INTEGER NOT NULL,
            measurement_type TEXT NOT NULL,
            measured_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            hdf5_path TEXT,
            notes TEXT,
            FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
            FOREIGN KEY (sample_id) REFERENCES samples(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ink_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            sc_material TEXT DEFAULT 'diFT-TES-ADT',
            ps_mw_gmol INTEGER DEFAULT 10000,
            sc_weight_mg REAL,
            ps_weight_mg REAL,
            cb_volume_ml REAL,
            ratio_osc_ps TEXT DEFAULT '4:1',
            prepared_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            usable_after TEXT,
            notes TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_samples_wafer ON samples(wafer_id);
        CREATE INDEX IF NOT EXISTS idx_devices_sample ON devices(sample_id);
        CREATE INDEX IF NOT EXISTS idx_steps_sample ON steps(sample_id);
        CREATE INDEX IF NOT EXISTS idx_measurements_device ON measurements(device_id);
    """)
    conn.commit()
    conn.close()


# --- Wafer CRUD ---

def add_wafer(
    name: str,
    substrate: str = "Kapton",
    size: str = "75um",
    n_pieces: int = 4,
    n_devices_per_piece: int = 3,
    notes: str = "",
    photo: str = "",
    path: Path | None = None,
) -> int:
    conn = get_connection(path)
    cur = conn.execute(
        "INSERT INTO wafers (name, substrate, size_mm, notes, photo_path) VALUES (?,?,?,?,?)",
        (name, substrate, size, notes, photo),
    )
    w_id = cur.lastrowid
    for p in range(1, n_pieces + 1):
        label = f"{name}_P{p}"
        cur2 = conn.execute(
            "INSERT INTO samples (wafer_id, piece_number, label) VALUES (?,?,?)",
            (w_id, p, label),
        )
        s_id = cur2.lastrowid
        for d in range(1, n_devices_per_piece + 1):
            conn.execute(
                "INSERT INTO devices (sample_id, device_number) VALUES (?,?)",
                (s_id, d),
            )
    conn.commit()
    conn.close()
    return w_id


def list_wafers(path: Path | None = None) -> list[dict]:
    conn = get_connection(path)
    rows = conn.execute("SELECT * FROM wafers ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_wafer(wafer_id: int, path: Path | None = None) -> dict | None:
    conn = get_connection(path)
    row = conn.execute("SELECT * FROM wafers WHERE id = ?", (wafer_id,)).fetchone()
    samples = conn.execute(
        "SELECT * FROM samples WHERE wafer_id = ? ORDER BY piece_number", (wafer_id,)
    ).fetchall()
    conn.close()
    if row:
        result = dict(row)
        result["samples"] = [dict(s) for s in samples]
        return result
    return None


# --- Sample CRUD ---

def get_sample(sample_id: int, path: Path | None = None) -> dict | None:
    conn = get_connection(path)
    row = conn.execute("SELECT * FROM samples WHERE id = ?", (sample_id,)).fetchone()
    if not row:
        conn.close()
        return None
    result = dict(row)
    result["devices"] = [
        dict(d)
        for d in conn.execute(
            "SELECT * FROM devices WHERE sample_id = ? ORDER BY device_number",
            (sample_id,),
        )
    ]
    result["steps"] = [
        dict(s)
        for s in conn.execute(
            "SELECT * FROM steps WHERE sample_id = ? ORDER BY started_at",
            (sample_id,),
        )
    ]
    result["wafer_name"] = conn.execute(
        "SELECT w.name FROM wafers w JOIN samples s ON s.wafer_id = w.id WHERE s.id = ?",
        (sample_id,),
    ).fetchone()["name"]
    conn.close()
    return result


def list_samples(
    wafer_id: int | None = None,
    status: str | None = None,
    path: Path | None = None,
) -> list[dict]:
    conn = get_connection(path)
    query = """
        SELECT s.*, w.name as wafer_name,
            (SELECT GROUP_CONCAT(st.step_type || ':' || st.status, ', ')
             FROM steps st WHERE st.sample_id = s.id) as step_status
        FROM samples s
        JOIN wafers w ON s.wafer_id = w.id
    """
    params: list = []
    if wafer_id is not None:
        query += " WHERE s.wafer_id = ?"
        params.append(wafer_id)
    query += " ORDER BY w.created_at DESC, s.piece_number"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Steps CRUD ---

SAMPLE_STEPS = {
    "photolithography": "Photolithography (resist + laser writing)",
    "developing": "Developing",
    "evaporation": "Cr/Au Evaporation (5nm/40nm)",
    "lift_off": "Lift-off (Acetone + IPA baths)",
    "cutting": "Cutting into pieces",
    "sam": "SAM (UVO + PFBT)",
    "bams": "BAMS semiconductor deposition",
    "measurement": "Electrical measurement",
    "functionalization": "Surface modification / bio-functionalization",
}


def add_step(
    sample_id: int,
    step_type: str,
    status: str = "pending",
    params: dict | None = None,
    notes: str = "",
    photo_paths: list[str] | None = None,
    path: Path | None = None,
) -> int:
    conn = get_connection(path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    started = now if status in ("in_progress", "completed") else None
    completed = now if status == "completed" else None
    cur = conn.execute(
        """INSERT INTO steps (sample_id, step_type, status, started_at, completed_at,
           params_json, notes, photo_paths)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            sample_id,
            step_type,
            status,
            started,
            completed,
            json.dumps(params or {}),
            notes,
            json.dumps(photo_paths or []),
        ),
    )
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return sid


def update_step(
    step_id: int,
    status: str | None = None,
    params: dict | None = None,
    notes: str | None = None,
    photo_paths: list[str] | None = None,
    path: Path | None = None,
) -> None:
    conn = get_connection(path)
    updates = []
    vals: list = []
    if status is not None:
        updates.append("status = ?")
        vals.append(status)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if status == "in_progress":
            updates.append("started_at = ?")
            vals.append(now)
        elif status == "completed":
            updates.append("completed_at = ?")
            vals.append(now)
    if params is not None:
        updates.append("params_json = ?")
        vals.append(json.dumps(params))
    if notes is not None:
        updates.append("notes = ?")
        vals.append(notes)
    if photo_paths is not None:
        updates.append("photo_paths = ?")
        vals.append(json.dumps(photo_paths))
    if updates:
        vals.append(step_id)
        conn.execute(f"UPDATE steps SET {', '.join(updates)} WHERE id = ?", vals)
        conn.commit()
    conn.close()


def get_latest_step(sample_id: int, path: Path | None = None) -> str:
    conn = get_connection(path)
    row = conn.execute(
        "SELECT step_type, status FROM steps WHERE sample_id = ? "
        "AND status != 'aborted' ORDER BY completed_at DESC LIMIT 1",
        (sample_id,),
    ).fetchone()
    conn.close()
    if row:
        return f"{row['step_type']}:{row['status']}"
    return "no_steps"


# --- Measurements CRUD ---

def add_measurement(
    device_id: int,
    sample_id: int,
    measurement_type: str,
    hdf5_path: str = "",
    notes: str = "",
    path: Path | None = None,
) -> int:
    conn = get_connection(path)
    cur = conn.execute(
        "INSERT INTO measurements (device_id, sample_id, measurement_type, hdf5_path, notes) "
        "VALUES (?,?,?,?,?)",
        (device_id, sample_id, measurement_type, hdf5_path, notes),
    )
    conn.commit()
    mid = cur.lastrowid
    conn.close()
    return mid


# --- Ink CRUD ---

def add_ink_batch(
    name: str,
    sc_weight_mg: float,
    ps_weight_mg: float,
    cb_volume_ml: float,
    sc_material: str = "diFT-TES-ADT",
    ps_mw: int = 10000,
    ratio: str = "4:1",
    notes: str = "",
    path: Path | None = None,
) -> int:
    conn = get_connection(path)
    prepared = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    usable = (datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    cur = conn.execute(
        """INSERT INTO ink_batches
           (name, sc_material, ps_mw_gmol, sc_weight_mg, ps_weight_mg,
            cb_volume_ml, ratio_osc_ps, prepared_at, usable_after, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (name, sc_material, ps_mw, sc_weight_mg, ps_weight_mg, cb_volume_ml, ratio, prepared, usable, notes),
    )
    conn.commit()
    iid = cur.lastrowid
    conn.close()
    return iid


def list_ink_batches(path: Path | None = None) -> list[dict]:
    conn = get_connection(path)
    rows = conn.execute("SELECT * FROM ink_batches ORDER BY prepared_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Init on import ---
if not DB_PATH.exists():
    init_db()
