import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import subprocess
import sys
from pathlib import Path
from datetime import datetime


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = BASE_DIR / "database" / "attendance.db"


# ============================================================
# COLORS
# ============================================================

BG = "#0F172A"
SIDEBAR = "#111827"
CARD = "#1E293B"
CARD_LIGHT = "#243247"

TEXT = "#F8FAFC"
MUTED = "#94A3B8"

ACCENT = "#38BDF8"
SUCCESS = "#22C55E"
WARNING = "#F59E0B"
PURPLE = "#A78BFA"

BORDER = "#334155"
ERROR = "#EF4444"


# ============================================================
# DATABASE
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def initialize_database():

    try:

        from database.database import create_tables

        create_tables()

    except Exception as error:

        print(
            f"Database initialization warning: {error}"
        )


# ============================================================
# DASHBOARD DATA
# ============================================================

def get_dashboard_data():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        today = datetime.now().strftime(
            "%Y-%m-%d"
        )

        # ----------------------------------------------------
        # Total people
        # ----------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM employees
        """)

        total_people = cursor.fetchone()["total"]

        # ----------------------------------------------------
        # Present today
        # ----------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM attendance
            WHERE attendance_date = ?
        """, (
            today,
        ))

        present_today = cursor.fetchone()["total"]

        # ----------------------------------------------------
        # Checked in
        # ----------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM attendance
            WHERE attendance_date = ?
            AND check_in IS NOT NULL
        """, (
            today,
        ))

        checked_in = cursor.fetchone()["total"]

        # ----------------------------------------------------
        # Checked out
        # ----------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM attendance
            WHERE attendance_date = ?
            AND check_out IS NOT NULL
        """, (
            today,
        ))

        checked_out = cursor.fetchone()["total"]

        # ----------------------------------------------------
        # Today's attendance
        # ----------------------------------------------------

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
                ON employees.id = attendance.employee_id

            WHERE attendance.attendance_date = ?

            ORDER BY attendance.id DESC
        """, (
            today,
        ))

        records = cursor.fetchall()

        return (
            total_people,
            present_today,
            checked_in,
            checked_out,
            records
        )

    finally:

        connection.close()


# ============================================================
# PEOPLE DATA
# ============================================================

def get_all_employees():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                id,
                employee_code,
                name,
                department

            FROM employees

            ORDER BY id DESC
        """)

        return cursor.fetchall()

    finally:

        connection.close()


# ============================================================
# LAUNCH MODULE
# ============================================================

def launch_module(module_name):

    try:

        subprocess.Popen(
            [
                sys.executable,
                "-m",
                module_name
            ],
            cwd=str(BASE_DIR)
        )

    except Exception as error:

        messagebox.showerror(
            "Unable to Launch",
            (
                f"Could not start:\n\n"
                f"{module_name}\n\n"
                f"Error:\n{error}"
            )
        )


# ============================================================
# DASHBOARD
# ============================================================

class Dashboard(tk.Tk):

    def __init__(self):

        super().__init__()

        # ----------------------------------------------------
        # WINDOW
        # ----------------------------------------------------

        self.title(
            "FaceAttend - Admin Dashboard"
        )

        # ----------------------------------------------------
        # Open maximized
        # ----------------------------------------------------

        try:

            self.state("zoomed")

        except Exception:

            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()

            self.geometry(
                f"{screen_width}x{screen_height}+0+0"
            )

        self.minsize(
            1000,
            650
        )

        self.configure(
            bg=BG
        )

        # ----------------------------------------------------
        # CLOSE EVENT
        # ----------------------------------------------------

        self.protocol(
            "WM_DELETE_WINDOW",
            self.close_application
        )

        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        initialize_database()

        # ----------------------------------------------------
        # STYLE
        # ----------------------------------------------------

        self.setup_style()

        # ----------------------------------------------------
        # INTERFACE
        # ----------------------------------------------------

        self.build_interface()

        # ----------------------------------------------------
        # INITIAL PAGE
        # ----------------------------------------------------

        self.show_dashboard()

        # ----------------------------------------------------
        # CLOCK
        # ----------------------------------------------------

        self.update_clock()

    # ========================================================
    # STYLE
    # ========================================================

    def setup_style(self):

        style = ttk.Style()

        style.theme_use(
            "clam"
        )

        # ----------------------------------------------------
        # Treeview
        # ----------------------------------------------------

        style.configure(
            "Treeview",
            background=CARD,
            foreground=TEXT,
            fieldbackground=CARD,
            borderwidth=0,
            rowheight=42,
            font=("Segoe UI", 10)
        )

        # ----------------------------------------------------
        # Treeview headings
        # ----------------------------------------------------

        style.configure(
            "Treeview.Heading",
            background=SIDEBAR,
            foreground=MUTED,
            borderwidth=0,
            font=("Segoe UI Semibold", 10)
        )

        # ----------------------------------------------------
        # Selected row
        # ----------------------------------------------------

        style.map(
            "Treeview",
            background=[
                (
                    "selected",
                    "#334155"
                )
            ],
            foreground=[
                (
                    "selected",
                    TEXT
                )
            ]
        )

    # ========================================================
    # BUILD INTERFACE
    # ========================================================

    def build_interface(self):

        # ====================================================
        # SIDEBAR
        # ====================================================

        self.sidebar = tk.Frame(
            self,
            bg=SIDEBAR,
            width=245
        )

        self.sidebar.pack(
            side="left",
            fill="y"
        )

        self.sidebar.pack_propagate(
            False
        )

        # ----------------------------------------------------
        # BRAND
        # ----------------------------------------------------

        brand = tk.Frame(
            self.sidebar,
            bg=SIDEBAR
        )

        brand.pack(
            fill="x",
            padx=25,
            pady=(28, 35)
        )

        tk.Label(
            brand,
            text="◈",
            bg=SIDEBAR,
            fg=ACCENT,
            font=("Segoe UI", 27, "bold")
        ).pack(
            side="left"
        )

        brand_text = tk.Frame(
            brand,
            bg=SIDEBAR
        )

        brand_text.pack(
            side="left",
            padx=10
        )

        tk.Label(
            brand_text,
            text="FACEATTEND",
            bg=SIDEBAR,
            fg=TEXT,
            font=("Segoe UI Semibold", 12)
        ).pack(
            anchor="w"
        )

        tk.Label(
            brand_text,
            text="ADMIN CONSOLE",
            bg=SIDEBAR,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(
            anchor="w"
        )

        # ----------------------------------------------------
        # NAVIGATION TITLE
        # ----------------------------------------------------

        tk.Label(
            self.sidebar,
            text="OPERATIONS",
            bg=SIDEBAR,
            fg="#64748B",
            font=("Segoe UI Semibold", 9)
        ).pack(
            anchor="w",
            padx=25,
            pady=(0, 12)
        )

        # ----------------------------------------------------
        # DASHBOARD BUTTON
        # ----------------------------------------------------

        self.dashboard_button = self.create_nav_button(
            "▣   Dashboard",
            self.show_dashboard
        )

        # ----------------------------------------------------
        # REGISTER PERSON
        # ----------------------------------------------------

        self.register_button = self.create_nav_button(
            "＋   Register Person",
            self.open_enrollment
        )

        # ----------------------------------------------------
        # MANAGE PEOPLE
        # ----------------------------------------------------

        self.manage_button = self.create_nav_button(
            "☷   Manage People",
            self.show_manage_employees
        )

        # ----------------------------------------------------
        # CHECK-IN
        # ----------------------------------------------------

        self.checkin_button = self.create_nav_button(
            "↳   Person Check-In",
            lambda: launch_module(
                "attendance.checkin"
            )
        )

        # ----------------------------------------------------
        # CHECK-OUT
        # ----------------------------------------------------

        self.checkout_button = self.create_nav_button(
            "↲   Person Check-Out",
            lambda: launch_module(
                "attendance.checkout"
            )
        )

        # ----------------------------------------------------
        # SIDEBAR FOOTER
        # ----------------------------------------------------

        bottom = tk.Frame(
            self.sidebar,
            bg=SIDEBAR
        )

        bottom.pack(
            side="bottom",
            fill="x",
            padx=25,
            pady=25
        )

        tk.Label(
            bottom,
            text="BIOMETRIC ATTENDANCE",
            bg=SIDEBAR,
            fg="#64748B",
            font=("Segoe UI Semibold", 8)
        ).pack(
            anchor="w"
        )

        tk.Label(
            bottom,
            text="Local Database • Secure Access",
            bg=SIDEBAR,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(
            anchor="w",
            pady=(4, 0)
        )

        # ====================================================
        # MAIN AREA
        # ====================================================

        self.main = tk.Frame(
            self,
            bg=BG
        )

        self.main.pack(
            side="left",
            fill="both",
            expand=True
        )

        # ====================================================
        # HEADER
        # ====================================================

        self.header = tk.Frame(
            self.main,
            bg=BG,
            height=90
        )

        self.header.pack(
            fill="x",
            padx=35,
            pady=(25, 0)
        )

        self.title_area = tk.Frame(
            self.header,
            bg=BG
        )

        self.title_area.pack(
            side="left"
        )

        self.page_title = tk.Label(
            self.title_area,
            text="Dashboard",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI Semibold", 25)
        )

        self.page_title.pack(
            anchor="w"
        )

        self.date_label = tk.Label(
            self.title_area,
            text="",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 10)
        )

        self.date_label.pack(
            anchor="w",
            pady=(3, 0)
        )

        # ----------------------------------------------------
        # CLOCK
        # ----------------------------------------------------

        self.clock_label = tk.Label(
            self.header,
            text="",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI Semibold", 13)
        )

        self.clock_label.pack(
            side="right",
            pady=12
        )

        # ====================================================
        # CONTENT
        # ====================================================

        self.content = tk.Frame(
            self.main,
            bg=BG
        )

        self.content.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=15
        )

    # ========================================================
    # NAVIGATION BUTTON
    # ========================================================

    def create_nav_button(
        self,
        text,
        command,
        active=False
    ):

        button_bg = (
            "#1E293B"
            if active
            else SIDEBAR
        )

        button = tk.Button(
            self.sidebar,
            text=text,
            command=command,
            bg=button_bg,
            fg=TEXT if active else MUTED,
            activebackground="#263449",
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            anchor="w",
            padx=20,
            font=("Segoe UI", 10),
            cursor="hand2"
        )

        button.pack(
            fill="x",
            padx=15,
            pady=3,
            ipady=10
        )

        return button

    # ========================================================
    # SET ACTIVE NAVIGATION
    # ========================================================

    def set_active_button(self, active_button):

        buttons = [
            self.dashboard_button,
            self.register_button,
            self.manage_button,
            self.checkin_button,
            self.checkout_button
        ]

        for button in buttons:

            if button == active_button:

                button.config(
                    bg="#1E293B",
                    fg=TEXT
                )

            else:

                button.config(
                    bg=SIDEBAR,
                    fg=MUTED
                )

    # ========================================================
    # CLEAR CONTENT
    # ========================================================

    def clear_content(self):

        for widget in self.content.winfo_children():

            widget.destroy()

    # ========================================================
    # DASHBOARD PAGE
    # ========================================================

    def show_dashboard(self):

        self.set_active_button(
            self.dashboard_button
        )

        self.page_title.config(
            text="Dashboard"
        )

        self.clear_content()

        self.build_cards()

        self.build_attendance_section()

        self.refresh_dashboard()

    # ========================================================
    # CARDS
    # ========================================================

    def build_cards(self):

        self.cards_frame = tk.Frame(
            self.content,
            bg=BG
        )

        self.cards_frame.pack(
            fill="x"
        )

        for column in range(4):

            self.cards_frame.columnconfigure(
                column,
                weight=1
            )

        # ----------------------------------------------------
        # Total People
        # ----------------------------------------------------

        self.total_card = self.create_card(
            0,
            "TOTAL PEOPLE",
            "0",
            "Registered people",
            ACCENT
        )

        # ----------------------------------------------------
        # Present
        # ----------------------------------------------------

        self.present_card = self.create_card(
            1,
            "PRESENT TODAY",
            "0",
            "Attendance records",
            SUCCESS
        )

        # ----------------------------------------------------
        # Checked in
        # ----------------------------------------------------

        self.checkin_card = self.create_card(
            2,
            "CHECKED IN",
            "0",
            "Today's check-ins",
            WARNING
        )

        # ----------------------------------------------------
        # Checked out
        # ----------------------------------------------------

        self.checkout_card = self.create_card(
            3,
            "CHECKED OUT",
            "0",
            "Today's check-outs",
            PURPLE
        )

    # ========================================================
    # CREATE CARD
    # ========================================================

    def create_card(
        self,
        column,
        title,
        value,
        subtitle,
        accent
    ):

        card = tk.Frame(
            self.cards_frame,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        card.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=6
        )

        # ----------------------------------------------------
        # Accent
        # ----------------------------------------------------

        tk.Frame(
            card,
            bg=accent,
            height=3
        ).pack(
            fill="x"
        )

        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        tk.Label(
            card,
            text=title,
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI Semibold", 9)
        ).pack(
            anchor="w",
            padx=18,
            pady=(17, 3)
        )

        # ----------------------------------------------------
        # Value
        # ----------------------------------------------------

        value_label = tk.Label(
            card,
            text=value,
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI Semibold", 25)
        )

        value_label.pack(
            anchor="w",
            padx=18
        )

        # ----------------------------------------------------
        # Subtitle
        # ----------------------------------------------------

        tk.Label(
            card,
            text=subtitle,
            bg=CARD,
            fg="#64748B",
            font=("Segoe UI", 9)
        ).pack(
            anchor="w",
            padx=18,
            pady=(2, 15)
        )

        return value_label

    # ========================================================
    # ATTENDANCE SECTION
    # ========================================================

    def build_attendance_section(self):

        section = tk.Frame(
            self.content,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        section.pack(
            fill="both",
            expand=True,
            pady=(25, 0)
        )

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        header = tk.Frame(
            section,
            bg=CARD,
            height=70
        )

        header.pack(
            fill="x",
            padx=22,
            pady=(15, 0)
        )

        tk.Label(
            header,
            text="Today's Attendance",
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI Semibold", 15)
        ).pack(
            side="left"
        )

        # ----------------------------------------------------
        # Refresh
        # ----------------------------------------------------

        refresh_button = tk.Button(
            header,
            text="⟳  Refresh",
            command=self.refresh_dashboard,
            bg=CARD_LIGHT,
            fg=TEXT,
            activebackground="#334155",
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            padx=15,
            pady=7,
            font=("Segoe UI", 9),
            cursor="hand2"
        )

        refresh_button.pack(
            side="right"
        )

        # ====================================================
        # TABLE
        # ====================================================

        table_frame = tk.Frame(
            section,
            bg=CARD
        )

        table_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

        columns = (
            "person",
            "name",
            "department",
            "checkin",
            "checkout",
            "status"
        )

        self.table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "person": "PERSON ID",
            "name": "NAME",
            "department": "DEPARTMENT",
            "checkin": "CHECK-IN",
            "checkout": "CHECK-OUT",
            "status": "STATUS"
        }

        for column, heading in headings.items():

            self.table.heading(
                column,
                text=heading
            )

        # ----------------------------------------------------
        # Responsive columns
        # ----------------------------------------------------

        self.table.column(
            "person",
            width=120,
            minwidth=100,
            anchor="center",
            stretch=True
        )

        self.table.column(
            "name",
            width=180,
            minwidth=130,
            anchor="w",
            stretch=True
        )

        self.table.column(
            "department",
            width=150,
            minwidth=120,
            anchor="w",
            stretch=True
        )

        self.table.column(
            "checkin",
            width=130,
            minwidth=100,
            anchor="center",
            stretch=True
        )

        self.table.column(
            "checkout",
            width=130,
            minwidth=100,
            anchor="center",
            stretch=True
        )

        self.table.column(
            "status",
            width=120,
            minwidth=100,
            anchor="center",
            stretch=True
        )

        # ----------------------------------------------------
        # Scrollbar
        # ----------------------------------------------------

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.table.yview
        )

        self.table.configure(
            yscrollcommand=scrollbar.set
        )

        self.table.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

    # ========================================================
    # REFRESH DASHBOARD
    # ========================================================

    def refresh_dashboard(self):

        try:

            (
                total,
                present,
                checked_in,
                checked_out,
                records
            ) = get_dashboard_data()

            # ------------------------------------------------
            # Update cards
            # ------------------------------------------------

            self.total_card.config(
                text=str(total)
            )

            self.present_card.config(
                text=str(present)
            )

            self.checkin_card.config(
                text=str(checked_in)
            )

            self.checkout_card.config(
                text=str(checked_out)
            )

            # ------------------------------------------------
            # Clear table
            # ------------------------------------------------

            for item in self.table.get_children():

                self.table.delete(
                    item
                )

            # ------------------------------------------------
            # Add records
            # ------------------------------------------------

            for record in records:

                checkin = (
                    record["check_in"]
                    if record["check_in"]
                    else "—"
                )

                checkout = (
                    record["check_out"]
                    if record["check_out"]
                    else "—"
                )

                status = (
                    record["status"]
                    if record["status"]
                    else "Present"
                )

                self.table.insert(
                    "",
                    "end",
                    values=(
                        record["employee_code"],
                        record["name"],
                        record["department"] or "—",
                        checkin,
                        checkout,
                        status
                    )
                )

        except Exception as error:

            print(
                "Dashboard database error:",
                error
            )

    # ========================================================
    # MANAGE PEOPLE PAGE
    # ========================================================

    def show_manage_employees(self):

        self.set_active_button(
            self.manage_button
        )

        self.page_title.config(
            text="Manage People"
        )

        self.clear_content()

        # ====================================================
        # MAIN MANAGEMENT CARD
        # ====================================================

        section = tk.Frame(
            self.content,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        section.pack(
            fill="both",
            expand=True
        )

        # ====================================================
        # SECTION HEADER
        # ====================================================

        header = tk.Frame(
            section,
            bg=CARD,
            height=85
        )

        header.pack(
            fill="x",
            padx=25,
            pady=(20, 0)
        )

        header.pack_propagate(
            False
        )

        # ----------------------------------------------------
        # TITLE AREA
        # ----------------------------------------------------

        title_area = tk.Frame(
            header,
            bg=CARD
        )

        title_area.pack(
            side="left"
        )

        tk.Label(
            title_area,
            text="Registered People",
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI Semibold", 18)
        ).pack(
            anchor="w"
        )

        tk.Label(
            title_area,
            text="View and manage registered person records",
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(
            anchor="w",
            pady=(4, 0)
        )

        # ====================================================
        # HEADER ACTIONS
        # ====================================================

        actions = tk.Frame(
            header,
            bg=CARD
        )

        actions.pack(
            side="right"
        )

        # ----------------------------------------------------
        # DELETE BUTTON
        # ----------------------------------------------------

        self.delete_employee_button = tk.Button(
            actions,
            text="🗑  Delete Person",
            command=self.delete_selected_employee,
            bg=ERROR,
            fg="white",
            activebackground="#DC2626",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=18,
            pady=9,
            font=("Segoe UI Semibold", 10),
            cursor="hand2"
        )

        self.delete_employee_button.pack(
            side="left",
            padx=(0, 10)
        )

        # ----------------------------------------------------
        # REFRESH BUTTON
        # ----------------------------------------------------

        refresh_button = tk.Button(
            actions,
            text="⟳  Refresh",
            command=self.refresh_employee_table,
            bg=CARD_LIGHT,
            fg=TEXT,
            activebackground="#334155",
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            padx=18,
            pady=9,
            font=("Segoe UI", 9),
            cursor="hand2"
        )

        refresh_button.pack(
            side="left"
        )

        # ====================================================
        # TABLE AREA
        # ====================================================

        table_container = tk.Frame(
            section,
            bg=CARD
        )

        table_container.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(5, 10)
        )

        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        columns = (
            "id",
            "person_code",
            "name",
            "department"
        )

        self.employee_table = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # ----------------------------------------------------
        # HEADINGS
        # ----------------------------------------------------

        self.employee_table.heading(
            "id",
            text="DATABASE ID"
        )

        self.employee_table.heading(
            "person_code",
            text="PERSON ID"
        )

        self.employee_table.heading(
            "name",
            text="NAME"
        )

        self.employee_table.heading(
            "department",
            text="DEPARTMENT"
        )

        # ----------------------------------------------------
        # COLUMNS
        # ----------------------------------------------------

        self.employee_table.column(
            "id",
            width=130,
            minwidth=100,
            anchor="center",
            stretch=True
        )

        self.employee_table.column(
            "person_code",
            width=180,
            minwidth=130,
            anchor="center",
            stretch=True
        )

        self.employee_table.column(
            "name",
            width=250,
            minwidth=150,
            anchor="w",
            stretch=True
        )

        self.employee_table.column(
            "department",
            width=220,
            minwidth=150,
            anchor="w",
            stretch=True
        )

        # ----------------------------------------------------
        # SCROLLBAR
        # ----------------------------------------------------

        scrollbar = ttk.Scrollbar(
            table_container,
            orient="vertical",
            command=self.employee_table.yview
        )

        self.employee_table.configure(
            yscrollcommand=scrollbar.set
        )

        self.employee_table.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        # ====================================================
        # INFORMATION AREA
        # ====================================================

        info_frame = tk.Frame(
            section,
            bg=CARD
        )

        info_frame.pack(
            fill="x",
            padx=25,
            pady=(0, 20)
        )

        tk.Label(
            info_frame,
            text=(
                "Select a person from the table, "
                "then click Delete Person."
            ),
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(
            anchor="w"
        )

        # ====================================================
        # LOAD PEOPLE
        # ====================================================

        self.refresh_employee_table()

    # ========================================================
    # REFRESH PEOPLE TABLE
    # ========================================================

    def refresh_employee_table(self):

        try:

            # ------------------------------------------------
            # Clear existing rows
            # ------------------------------------------------

            for item in self.employee_table.get_children():

                self.employee_table.delete(
                    item
                )

            # ------------------------------------------------
            # Get people
            # ------------------------------------------------

            people = get_all_employees()

            # ------------------------------------------------
            # Insert people
            # ------------------------------------------------

            for person in people:

                self.employee_table.insert(
                    "",
                    "end",
                    values=(
                        person["id"],
                        person["employee_code"],
                        person["name"],
                        person["department"] or "—"
                    )
                )

        except Exception as error:

            messagebox.showerror(
                "Database Error",
                (
                    "Could not load person records.\n\n"
                    f"{error}"
                ),
                parent=self
            )

    # ========================================================
    # DELETE SELECTED PERSON
    # ========================================================

    def delete_selected_employee(self):

        # ----------------------------------------------------
        # Check selection
        # ----------------------------------------------------

        selected = self.employee_table.selection()

        if not selected:

            messagebox.showwarning(
                "No Person Selected",
                "Please select a person from the table first.",
                parent=self
            )

            return

        # ----------------------------------------------------
        # Get selected person
        # ----------------------------------------------------

        item = selected[0]

        values = self.employee_table.item(
            item,
            "values"
        )

        if not values:

            return

        person_db_id = int(
            values[0]
        )

        person_code = values[1]

        person_name = values[2]

        # ====================================================
        # CONFIRMATION
        # ====================================================

        confirm = messagebox.askyesno(
            "Delete Person",
            (
                "Are you sure you want to delete this person?\n\n"
                f"Person ID: {person_code}\n"
                f"Name: {person_name}\n\n"
                "This will remove the person record "
                "from the system."
            ),
            icon="warning",
            parent=self
        )

        if not confirm:

            return

        # ====================================================
        # DELETE
        # ====================================================

        try:

            from database.database import delete_employee

            delete_employee(
                person_db_id
            )

            messagebox.showinfo(
                "Person Deleted",
                (
                    f"{person_name} "
                    "has been removed successfully."
                ),
                parent=self
            )

            # ------------------------------------------------
            # Refresh people table
            # ------------------------------------------------

            self.refresh_employee_table()

        except Exception as error:

            messagebox.showerror(
                "Delete Failed",
                (
                    "The person could not be deleted.\n\n"
                    f"{error}"
                ),
                parent=self
            )

    # ========================================================
    # OPEN ENROLLMENT
    # ========================================================

    def open_enrollment(self):

        self.set_active_button(
            self.register_button
        )

        try:

            from enrollment.face_enrollment import FaceEnrollment

            enrollment_window = FaceEnrollment(
                self
            )

            enrollment_window.grab_set()

            self.wait_window(
                enrollment_window
            )

            # ------------------------------------------------
            # Return to dashboard after enrollment
            # ------------------------------------------------

            self.show_dashboard()

        except Exception as error:

            messagebox.showerror(
                "Enrollment Error",
                (
                    "Could not open person registration.\n\n"
                    f"{error}"
                ),
                parent=self
            )

            self.show_dashboard()

    # ========================================================
    # CLOCK
    # ========================================================

    def update_clock(self):

        now = datetime.now()

        self.clock_label.config(
            text=now.strftime(
                "%I:%M:%S %p"
            )
        )

        self.date_label.config(
            text=now.strftime(
                "%A, %d %B %Y"
            )
        )

        self.after(
            1000,
            self.update_clock
        )

    # ========================================================
    # CLOSE APPLICATION
    # ========================================================

    def close_application(self):

        self.destroy()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app = Dashboard()

    app.mainloop()