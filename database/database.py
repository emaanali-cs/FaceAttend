import sqlite3
from pathlib import Path
from datetime import datetime


# ============================================================
# DATABASE PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = (
    BASE_DIR / "database" / "attendance.db"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ============================================================
# CREATE TABLES
# ============================================================

def create_tables():

    connection = get_connection()

    cursor = connection.cursor()

    # --------------------------------------------------------
    # EMPLOYEES / STUDENTS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            employee_code TEXT UNIQUE NOT NULL,

            name TEXT NOT NULL,

            department TEXT,

            person_type TEXT DEFAULT 'Employee',

            parent_email TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------------------------
    # DATABASE MIGRATION
    #
    # Adds the new columns if an older database already exists.
    # This prevents your existing database from breaking.
    # --------------------------------------------------------

    cursor.execute("""
        PRAGMA table_info(employees)
    """)

    columns = [
        column[1]
        for column in cursor.fetchall()
    ]

    if "person_type" not in columns:

        cursor.execute("""
            ALTER TABLE employees
            ADD COLUMN person_type TEXT
            DEFAULT 'Employee'
        """)

    if "parent_email" not in columns:

        cursor.execute("""
            ALTER TABLE employees
            ADD COLUMN parent_email TEXT
        """)

    # --------------------------------------------------------
    # FACE EMBEDDINGS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS face_embeddings (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            employee_id INTEGER NOT NULL,

            pose TEXT NOT NULL,

            embedding BLOB NOT NULL,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (employee_id)
                REFERENCES employees(id)
                ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------------
    # ATTENDANCE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            employee_id INTEGER NOT NULL,

            attendance_date TEXT NOT NULL,

            check_in TEXT,

            check_out TEXT,

            status TEXT DEFAULT 'Present',

            FOREIGN KEY (employee_id)
                REFERENCES employees(id)
                ON DELETE CASCADE,

            UNIQUE (
                employee_id,
                attendance_date
            )
        )
    """)

    connection.commit()

    connection.close()


# ============================================================
# EMPLOYEE
# ============================================================

def employee_exists(employee_code):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM employees
        WHERE employee_code = ?
    """, (
        employee_code,
    ))

    result = cursor.fetchone()

    connection.close()

    if result:
        return result[0]

    return None


# ============================================================
# ADD EMPLOYEE
# ============================================================

def add_employee(
    employee_code,
    name,
    department,
    person_type="Employee",
    parent_email=None
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO employees
            (
                employee_code,
                name,
                department,
                person_type,
                parent_email
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            employee_code,
            name,
            department,
            person_type,
            parent_email
        ))

        connection.commit()

        employee_id = cursor.lastrowid

        return employee_id

    except sqlite3.IntegrityError:

        raise ValueError(
            "Employee/Student ID already exists."
        )

    finally:

        connection.close()


# ============================================================
# GET EMPLOYEES
# ============================================================

def get_employees():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            employee_code,
            name,
            department,
            created_at
        FROM employees
        ORDER BY id DESC
    """)

    records = cursor.fetchall()

    connection.close()

    return records


# ============================================================
# GET PERSON DETAILS
# ============================================================

def get_person_details(employee_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            employee_code,
            name,
            department,
            person_type,
            parent_email
        FROM employees
        WHERE id = ?
    """, (
        employee_id,
    ))

    record = cursor.fetchone()

    connection.close()

    return record


# ============================================================
# DELETE EMPLOYEE
# ============================================================

def delete_employee(employee_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM employees
        WHERE id = ?
    """, (
        employee_id,
    ))

    connection.commit()

    connection.close()


# ============================================================
# FACE EMBEDDINGS
# ============================================================

def save_embedding(
    employee_id,
    pose,
    embedding
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO face_embeddings
        (
            employee_id,
            pose,
            embedding
        )
        VALUES (?, ?, ?)
    """, (
        employee_id,
        pose,
        embedding
    ))

    connection.commit()

    connection.close()


def get_face_embeddings():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            employees.id,
            employees.employee_code,
            employees.name,
            employees.department,
            face_embeddings.pose,
            face_embeddings.embedding

        FROM employees

        INNER JOIN face_embeddings
            ON employees.id =
               face_embeddings.employee_id

        ORDER BY employees.id
    """)

    records = cursor.fetchall()

    connection.close()

    return records


# ============================================================
# CHECK WHETHER EMPLOYEE HAS FACE DATA
# ============================================================

def employee_has_face_embeddings(employee_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM face_embeddings
        WHERE employee_id = ?
    """, (
        employee_id,
    ))

    count = cursor.fetchone()[0]

    connection.close()

    return count > 0


# ============================================================
# TODAY'S ATTENDANCE
# ============================================================

def get_today_attendance(employee_id):

    connection = get_connection()

    cursor = connection.cursor()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    cursor.execute("""
        SELECT
            id,
            employee_id,
            attendance_date,
            check_in,
            check_out,
            status

        FROM attendance

        WHERE employee_id = ?

        AND attendance_date = ?
    """, (
        employee_id,
        today
    ))

    record = cursor.fetchone()

    connection.close()

    return record


# ============================================================
# CHECK-IN
# ============================================================

def mark_check_in(employee_id):

    connection = get_connection()

    cursor = connection.cursor()

    now = datetime.now()

    today = now.strftime(
        "%Y-%m-%d"
    )

    current_time = now.strftime(
        "%H:%M:%S"
    )

    # --------------------------------------------------------
    # Verify employee exists
    # --------------------------------------------------------

    cursor.execute("""
        SELECT id
        FROM employees
        WHERE id = ?
    """, (
        employee_id,
    ))

    employee = cursor.fetchone()

    if not employee:

        connection.close()

        return False, (
            "Employee does not exist."
        )

    # --------------------------------------------------------
    # Check today's attendance
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            check_in,
            check_out

        FROM attendance

        WHERE employee_id = ?

        AND attendance_date = ?
    """, (
        employee_id,
        today
    ))

    existing = cursor.fetchone()

    # --------------------------------------------------------
    # Already checked in
    # --------------------------------------------------------

    if existing:

        connection.close()

        return False, (
            "Employee already checked in today."
        )

    # --------------------------------------------------------
    # Create attendance
    # --------------------------------------------------------

    cursor.execute("""
        INSERT INTO attendance
        (
            employee_id,
            attendance_date,
            check_in,
            status
        )

        VALUES (?, ?, ?, ?)
    """, (
        employee_id,
        today,
        current_time,
        "Present"
    ))

    connection.commit()

    connection.close()

    return True, current_time


# ============================================================
# CHECK-OUT
# ============================================================

def mark_check_out(employee_id):

    connection = get_connection()

    cursor = connection.cursor()

    now = datetime.now()

    today = now.strftime(
        "%Y-%m-%d"
    )

    current_time = now.strftime(
        "%H:%M:%S"
    )

    # --------------------------------------------------------
    # Find today's attendance
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            check_in,
            check_out

        FROM attendance

        WHERE employee_id = ?

        AND attendance_date = ?
    """, (
        employee_id,
        today
    ))

    record = cursor.fetchone()

    # --------------------------------------------------------
    # Employee did not check in
    # --------------------------------------------------------

    if not record:

        connection.close()

        return False, (
            "Check-out unavailable.\n\n"
            "This employee has not checked in today."
        )

    # --------------------------------------------------------
    # Already checked out
    # --------------------------------------------------------

    if record[2]:

        connection.close()

        return False, (
            "Employee already checked out today."
        )

    # --------------------------------------------------------
    # Check-out
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE attendance

        SET check_out = ?

        WHERE id = ?
    """, (
        current_time,
        record[0]
    ))

    connection.commit()

    connection.close()

    return True, current_time


# ============================================================
# ALL ATTENDANCE
# ============================================================

def get_attendance_records():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            attendance.id,

            employees.employee_code,

            employees.name,

            employees.department,

            attendance.attendance_date,

            attendance.check_in,

            attendance.check_out,

            attendance.status

        FROM attendance

        INNER JOIN employees

            ON attendance.employee_id =
               employees.id

        ORDER BY
            attendance.attendance_date DESC,

            attendance.check_in DESC
    """)

    records = cursor.fetchall()

    connection.close()

    return records


# ============================================================
# TODAY'S DASHBOARD RECORDS
# ============================================================

def get_today_attendance_records():

    connection = get_connection()

    cursor = connection.cursor()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    cursor.execute("""
        SELECT

            employees.employee_code,

            employees.name,

            employees.department,

            attendance.check_in,

            attendance.check_out,

            attendance.status

        FROM attendance

        INNER JOIN employees

            ON attendance.employee_id =
               employees.id

        WHERE attendance.attendance_date = ?

        ORDER BY attendance.id DESC
    """, (
        today,
    ))

    records = cursor.fetchall()

    connection.close()

    return records


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    create_tables()

    print(
        "Database initialized successfully."
    )