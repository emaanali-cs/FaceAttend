import tkinter as tk
from tkinter import messagebox
import cv2
import pickle
import numpy as np
import time
import re

from PIL import Image, ImageTk

from recognition.face_recognition import FaceSystem

from database.database import (
    create_tables,
    add_employee,
    employee_exists,
    save_embedding,
    delete_employee
)

from audio.audio_manager import AudioManager


# ============================================================
# SETTINGS
# ============================================================

CAMERA_ID = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
POSE_STABLE_TIME = 0.8
YAW_THRESHOLD = 0.18


# ============================================================
# COLORS
# ============================================================

BG = "#08111F"
PANEL = "#111B2D"
CAMERA_BG = "#020817"
TEXT = "#F5F7FA"
MUTED = "#8FA6C2"
ACCENT = "#2478B8"
SUCCESS = "#20D66B"
WARNING = "#F5C542"
ERROR = "#FF5C5C"


# ============================================================
# HEAD DIRECTION
# ============================================================

def get_head_direction(face):

    right_eye = np.array([
        face[4],
        face[5]
    ])

    left_eye = np.array([
        face[6],
        face[7]
    ])

    nose = np.array([
        face[8],
        face[9]
    ])

    eye_center = (
        right_eye + left_eye
    ) / 2

    eye_distance = np.linalg.norm(
        right_eye - left_eye
    )

    if eye_distance < 1:
        return "UNKNOWN"

    yaw = (
        nose[0] - eye_center[0]
    ) / eye_distance

    if yaw > YAW_THRESHOLD:
        return "RIGHT"

    if yaw < -YAW_THRESHOLD:
        return "LEFT"

    return "CENTER"


# ============================================================
# EMAIL VALIDATION
# ============================================================

def is_valid_email(email):

    pattern = (
        r"^[A-Za-z0-9._%+-]+@"
        r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    return re.match(pattern, email) is not None


# ============================================================
# ENROLLMENT WINDOW
# ============================================================

class FaceEnrollment(tk.Toplevel):

    def __init__(self, parent):

        super().__init__(parent)

        self.parent = parent

        # ----------------------------------------------------
        # WINDOW
        # ----------------------------------------------------

        self.title(
            "FaceAttend - Employee / Student Registration"
        )

        self.configure(
            bg=BG
        )

        self.minsize(
            950,
            620
        )

        # ----------------------------------------------------
        # RESPONSIVE INITIAL SIZE
        # ----------------------------------------------------

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        window_width = min(
            1250,
            max(950, int(screen_width * 0.88))
        )

        window_height = min(
            800,
            max(620, int(screen_height * 0.82))
        )

        x = max(
            0,
            (screen_width - window_width) // 2
        )

        y = max(
            0,
            (screen_height - window_height) // 2
        )

        self.geometry(
            f"{window_width}x{window_height}+{x}+{y}"
        )

        self.resizable(
            True,
            True
        )

        # ----------------------------------------------------
        # SYSTEM STATE
        # ----------------------------------------------------

        self.camera = None
        self.camera_running = False
        self.face_system = None
        self.photo = None

        # ----------------------------------------------------
        # AUDIO
        # ----------------------------------------------------

        self.audio = AudioManager()

        # ----------------------------------------------------
        # PERSON STATE
        # ----------------------------------------------------

        self.employee_id = None
        self.enrollment_completed = False

        self.employee_code = ""
        self.employee_name = ""
        self.department = ""

        self.person_type = "Employee"
        self.parent_email = ""

        # ----------------------------------------------------
        # ENROLLMENT STATE
        # ----------------------------------------------------

        self.current_pose_index = 0
        self.stable_start = None
        self.capture_locked = False
        self.enrolled_poses = []

        self.poses = [
            ("CENTER", "LOOK STRAIGHT"),
            ("LEFT", "TURN LEFT"),
            ("RIGHT", "TURN RIGHT")
        ]

        # ----------------------------------------------------
        # CLOSE EVENT
        # ----------------------------------------------------

        self.protocol(
            "WM_DELETE_WINDOW",
            self.close_window
        )

        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        create_tables()

        # ----------------------------------------------------
        # BUILD UI
        # ----------------------------------------------------

        self.create_header()
        self.create_content()

        self.update_idletasks()

    # ========================================================
    # HEADER
    # ========================================================

    def create_header(self):

        header = tk.Frame(
            self,
            bg=PANEL,
            height=70
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(False)

        tk.Label(
            header,
            text="FACEATTEND",
            font=("Segoe UI", 23, "bold"),
            fg=TEXT,
            bg=PANEL
        ).pack(
            side="left",
            padx=30
        )

        tk.Label(
            header,
            text="EMPLOYEE / STUDENT FACE REGISTRATION",
            font=("Segoe UI", 10),
            fg=MUTED,
            bg=PANEL
        ).pack(
            side="left"
        )

    # ========================================================
    # CONTENT
    # ========================================================

    def create_content(self):

        self.container = tk.Frame(
            self,
            bg=BG
        )

        self.container.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=20
        )

        self.show_employee_form()

    # ========================================================
    # EMPLOYEE / STUDENT FORM
    # ========================================================

    def show_employee_form(self):

        for widget in self.container.winfo_children():
            widget.destroy()

        panel = tk.Frame(
            self.container,
            bg=PANEL
        )

        panel.pack(
            fill="both",
            expand=True
        )

        form_container = tk.Frame(
            panel,
            bg=PANEL
        )

        form_container.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        tk.Label(
            form_container,
            text="Register Employee / Student",
            font=("Segoe UI", 27, "bold"),
            fg=TEXT,
            bg=PANEL
        ).pack(
            pady=(0, 8)
        )

        tk.Label(
            form_container,
            text=(
                "Enter registration information "
                "before starting face enrollment."
            ),
            font=("Segoe UI", 12),
            fg=MUTED,
            bg=PANEL
        ).pack(
            pady=(0, 25)
        )

        form = tk.Frame(
            form_container,
            bg=PANEL
        )

        form.pack()

        # ----------------------------------------------------
        # PERSON TYPE
        # ----------------------------------------------------

        type_row = tk.Frame(
            form,
            bg=PANEL
        )

        type_row.pack(
            pady=8
        )

        tk.Label(
            type_row,
            text="Person Type",
            width=18,
            anchor="w",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT,
            bg=PANEL
        ).pack(
            side="left"
        )

        self.person_type_var = tk.StringVar(
            value="Employee"
        )

        self.person_type_menu = tk.OptionMenu(
            type_row,
            self.person_type_var,
            "Employee",
            "Student",
            command=self.on_person_type_changed
        )

        self.person_type_menu.config(
            font=("Segoe UI", 11),
            bg=CAMERA_BG,
            fg=TEXT,
            activebackground=ACCENT,
            activeforeground=TEXT,
            relief="flat",
            width=32,
            highlightthickness=0
        )

        self.person_type_menu["menu"].config(
            font=("Segoe UI", 11),
            bg=CAMERA_BG,
            fg=TEXT
        )

        self.person_type_menu.pack(
            side="left",
            padx=(15, 0),
            ipady=5
        )

        # ----------------------------------------------------
        # ID
        # ----------------------------------------------------

        self.code_entry = self.create_entry(
            form,
            "Person ID"
        )

        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        self.name_entry = self.create_entry(
            form,
            "Person Name"
        )

        # ----------------------------------------------------
        # DEPARTMENT
        # ----------------------------------------------------

        self.department_entry = self.create_entry(
            form,
            "Department"
        )

        # ----------------------------------------------------
        # PARENT EMAIL
        # ----------------------------------------------------

        parent_row = tk.Frame(
            form,
            bg=PANEL
        )

        parent_row.pack(
            pady=8
        )

        tk.Label(
            parent_row,
            text="Parent Email",
            width=18,
            anchor="w",
            font=("Segoe UI", 11, "bold"),
            fg=MUTED,
            bg=PANEL
        ).pack(
            side="left"
        )

        self.parent_email_entry = tk.Entry(
            parent_row,
            font=("Segoe UI", 12),
            bg=CAMERA_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            width=35,
            state="disabled"
        )

        self.parent_email_entry.pack(
            side="left",
            padx=(15, 0),
            ipady=9
        )

        # ----------------------------------------------------
        # START BUTTON
        # ----------------------------------------------------

        tk.Button(
            form_container,
            text="START FACE ENROLLMENT",
            font=("Segoe UI", 13, "bold"),
            fg="white",
            bg=ACCENT,
            activebackground="#2F8DCE",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=35,
            pady=14,
            command=self.start_enrollment
        ).pack(
            pady=(25, 0)
        )

    # ========================================================
    # PERSON TYPE CHANGED
    # ========================================================

    def on_person_type_changed(self, selected_type):

        self.person_type = selected_type

        if selected_type == "Student":

            self.parent_email_entry.config(
                state="normal"
            )

            self.parent_email_entry.focus_set()

        else:

            self.parent_email_entry.config(
                state="normal"
            )

            self.parent_email_entry.delete(
                0,
                tk.END
            )

            self.parent_email_entry.config(
                state="disabled"
            )

    # ========================================================
    # ENTRY
    # ========================================================

    def create_entry(
        self,
        parent,
        label
    ):

        row = tk.Frame(
            parent,
            bg=PANEL
        )

        row.pack(
            pady=8
        )

        tk.Label(
            row,
            text=label,
            width=18,
            anchor="w",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT,
            bg=PANEL
        ).pack(
            side="left"
        )

        entry = tk.Entry(
            row,
            font=("Segoe UI", 12),
            bg=CAMERA_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            width=35
        )

        entry.pack(
            side="left",
            padx=(15, 0),
            ipady=9
        )

        return entry

    # ========================================================
    # START ENROLLMENT
    # ========================================================

    def start_enrollment(self):

        self.employee_code = (
            self.code_entry.get().strip()
        )

        self.employee_name = (
            self.name_entry.get().strip()
        )

        self.department = (
            self.department_entry.get().strip()
        )

        self.person_type = (
            self.person_type_var.get().strip()
        )

        # ----------------------------------------------------
        # PARENT EMAIL
        # ----------------------------------------------------

        if self.person_type == "Student":

            self.parent_email = (
                self.parent_email_entry.get().strip()
            )

        else:

            self.parent_email = None

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not self.employee_code:

            messagebox.showwarning(
                "Missing Information",
                "Please enter the employee/student ID.",
                parent=self
            )

            return

        if not self.employee_name:

            messagebox.showwarning(
                "Missing Information",
                "Please enter the employee/student name.",
                parent=self
            )

            return

        # ----------------------------------------------------
        # STUDENT PARENT EMAIL VALIDATION
        # ----------------------------------------------------

        if self.person_type == "Student":

            if not self.parent_email:

                messagebox.showwarning(
                    "Missing Information",
                    "Please enter the parent's email address.",
                    parent=self
                )

                return

            if not is_valid_email(
                self.parent_email
            ):

                messagebox.showwarning(
                    "Invalid Email",
                    "Please enter a valid parent email address.",
                    parent=self
                )

                return

        # ----------------------------------------------------
        # DUPLICATE CHECK
        # ----------------------------------------------------

        existing_id = employee_exists(
            self.employee_code
        )

        if existing_id:

            messagebox.showerror(
                "Employee / Student Already Exists",
                (
                    f"ID "
                    f"'{self.employee_code}' "
                    "is already registered."
                ),
                parent=self
            )

            return

        # ----------------------------------------------------
        # CREATE TEMPORARY EMPLOYEE / STUDENT
        # ----------------------------------------------------

        try:

            self.employee_id = add_employee(
                employee_code=self.employee_code,
                name=self.employee_name,
                department=self.department,
                person_type=self.person_type,
                parent_email=self.parent_email
            )

            self.face_system = FaceSystem()

        except Exception as error:

            messagebox.showerror(
                "Registration Error",
                str(error),
                parent=self
            )

            return

        # ----------------------------------------------------
        # RESET ENROLLMENT STATE
        # ----------------------------------------------------

        self.current_pose_index = 0
        self.stable_start = None
        self.capture_locked = False
        self.enrolled_poses = []
        self.enrollment_completed = False

        # ----------------------------------------------------
        # SHOW CAMERA
        # ----------------------------------------------------

        self.show_camera_screen()

        self.open_camera()

    # ========================================================
    # CAMERA SCREEN
    # ========================================================

    def show_camera_screen(self):

        for widget in self.container.winfo_children():
            widget.destroy()

        self.container.columnconfigure(
            0,
            weight=1
        )

        self.container.columnconfigure(
            1,
            weight=0
        )

        self.container.rowconfigure(
            0,
            weight=1
        )

        # ----------------------------------------------------
        # LEFT CAMERA PANEL
        # ----------------------------------------------------

        left = tk.Frame(
            self.container,
            bg=PANEL
        )

        left.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 12)
        )

        # ----------------------------------------------------
        # RIGHT INFORMATION PANEL
        # ----------------------------------------------------

        right = tk.Frame(
            self.container,
            bg=PANEL,
            width=290
        )

        right.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        right.grid_propagate(
            False
        )

        # ====================================================
        # LEFT PANEL
        # ====================================================

        tk.Label(
            left,
            text="Face Enrollment",
            font=("Segoe UI", 25, "bold"),
            fg=TEXT,
            bg=PANEL
        ).pack(
            pady=(20, 4)
        )

        self.camera_status = tk.Label(
            left,
            text="Preparing camera...",
            font=("Segoe UI", 12),
            fg=MUTED,
            bg=PANEL
        )

        self.camera_status.pack(
            pady=(0, 10)
        )

        # ----------------------------------------------------
        # CAMERA DISPLAY
        # ----------------------------------------------------

        camera_container = tk.Frame(
            left,
            bg=CAMERA_BG
        )

        camera_container.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 10)
        )

        self.camera_view = tk.Label(
            camera_container,
            text="Starting camera...",
            font=("Segoe UI", 18, "bold"),
            fg=MUTED,
            bg=CAMERA_BG
        )

        self.camera_view.pack(
            fill="both",
            expand=True
        )

        # ----------------------------------------------------
        # INSTRUCTION
        # ----------------------------------------------------

        self.camera_instruction = tk.Label(
            left,
            text="",
            font=("Segoe UI", 13),
            fg=MUTED,
            bg=PANEL
        )

        self.camera_instruction.pack(
            pady=(0, 10)
        )

        # ====================================================
        # RIGHT PANEL
        # ====================================================

        tk.Label(
            right,
            text="ENROLLMENT",
            font=("Segoe UI", 15, "bold"),
            fg=TEXT,
            bg=PANEL
        ).pack(
            pady=(35, 18)
        )

        self.progress_label = tk.Label(
            right,
            text="STEP 1 / 3",
            font=("Segoe UI", 12, "bold"),
            fg=ACCENT,
            bg=PANEL
        )

        self.progress_label.pack()

        self.pose_label = tk.Label(
            right,
            text="LOOK STRAIGHT",
            font=("Segoe UI", 20, "bold"),
            fg=TEXT,
            bg=PANEL,
            wraplength=240
        )

        self.pose_label.pack(
            pady=(20, 8)
        )

        self.employee_label = tk.Label(
            right,
            text=(
                f"{self.employee_name}\n"
                f"{self.employee_code}"
            ),
            font=("Segoe UI", 11),
            fg=MUTED,
            bg=PANEL,
            justify="center"
        )

        self.employee_label.pack(
            pady=18
        )

        # ----------------------------------------------------
        # SEPARATOR
        # ----------------------------------------------------

        tk.Frame(
            right,
            bg="#263449",
            height=1
        ).pack(
            fill="x",
            padx=25,
            pady=8
        )

        # ----------------------------------------------------
        # PROGRESS TEXT
        # ----------------------------------------------------

        self.progress_text = tk.Label(
            right,
            text=(
                "The system will capture:\n\n"
                "1. Front face\n"
                "2. Left pose\n"
                "3. Right pose"
            ),
            font=("Segoe UI", 10),
            fg=MUTED,
            bg=PANEL,
            justify="left"
        )

        self.progress_text.pack(
            padx=25,
            pady=20
        )

        # ----------------------------------------------------
        # TIP
        # ----------------------------------------------------

        tk.Label(
            right,
            text=(
                "TIP\n\n"
                "Keep your face clearly visible "
                "and follow the instructions shown "
                "on the screen."
            ),
            font=("Segoe UI", 9),
            fg="#64748B",
            bg=PANEL,
            justify="center",
            wraplength=235
        ).pack(
            padx=20,
            pady=15
        )

    # ========================================================
    # OPEN CAMERA
    # ========================================================

    def open_camera(self):

        self.camera = cv2.VideoCapture(
            CAMERA_ID
        )

        if not self.camera.isOpened():

            messagebox.showerror(
                "Camera Error",
                "Could not open the camera.",
                parent=self
            )

            self.cleanup_failed_enrollment()

            return

        self.camera.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            CAMERA_WIDTH
        )

        self.camera.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            CAMERA_HEIGHT
        )

        self.camera_running = True

        # ----------------------------------------------------
        # CENTER AUDIO
        #
        # This plays ONCE when enrollment starts.
        #
        # File:
        # audio/look_center.mp3
        # ----------------------------------------------------

        self.audio.play(
            "look_center.mp3"
        )

        # ----------------------------------------------------
        # START CAMERA LOOP
        # ----------------------------------------------------

        self.update_camera()

    # ========================================================
    # CAMERA LOOP
    # ========================================================

    def update_camera(self):

        if not self.camera_running:
            return

        success, frame = self.camera.read()

        if not success:

            self.camera_status.config(
                text="Camera read error.",
                fg=ERROR
            )

            self.cleanup_failed_enrollment()

            messagebox.showerror(
                "Camera Error",
                "Live camera capture failed.",
                parent=self
            )

            return

        frame = cv2.flip(
            frame,
            1
        )

        faces = self.face_system.detect(
            frame
        )

        required_pose, instruction = (
            self.poses[
                self.current_pose_index
            ]
        )

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        cv2.rectangle(
            frame,
            (0, 0),
            (frame.shape[1], 80),
            (8, 17, 31),
            -1
        )

        cv2.putText(
            frame,
            f"STEP {self.current_pose_index + 1} / 3",
            (25, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            instruction,
            (25, 64),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (40, 220, 100),
            2
        )

        # ====================================================
        # NO FACE
        # ====================================================

        if len(faces) == 0:

            self.stable_start = None

            self.camera_status.config(
                text="Searching for your face...",
                fg=MUTED
            )

            self.camera_instruction.config(
                text="Position your face inside the camera"
            )

            cv2.putText(
                frame,
                "FACE NOT DETECTED",
                (25, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 180, 255),
                2
            )

        # ====================================================
        # MULTIPLE FACES
        # ====================================================

        elif len(faces) > 1:

            self.stable_start = None

            self.camera_status.config(
                text="Multiple faces detected",
                fg=ERROR
            )

            self.camera_instruction.config(
                text="Only one person should be visible"
            )

            cv2.putText(
                frame,
                "ONLY ONE PERSON ALLOWED",
                (25, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 0, 255),
                2
            )

            for face in faces:

                self.draw_face(
                    frame,
                    face,
                    (0, 0, 255)
                )

        # ====================================================
        # ONE FACE
        # ====================================================

        else:

            face = faces[0]

            self.draw_face(
                frame,
                face,
                (40, 220, 100)
            )

            direction = get_head_direction(
                face
            )

            cv2.putText(
                frame,
                f"DETECTED: {direction}",
                (25, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (220, 220, 220),
                2
            )

            # =================================================
            # CORRECT POSE
            # =================================================

            if direction == required_pose:

                if self.stable_start is None:

                    self.stable_start = time.time()

                elapsed = (
                    time.time()
                    - self.stable_start
                )

                remaining = max(
                    0,
                    POSE_STABLE_TIME - elapsed
                )

                self.camera_status.config(
                    text=f"Hold still... {remaining:.1f}s",
                    fg=SUCCESS
                )

                self.camera_instruction.config(
                    text=instruction
                )

                cv2.putText(
                    frame,
                    f"HOLD STILL: {remaining:.1f}s",
                    (25, 158),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (40, 220, 100),
                    2
                )

                # ------------------------------------------------
                # CAPTURE
                # ------------------------------------------------

                if (
                    elapsed >= POSE_STABLE_TIME
                    and not self.capture_locked
                ):

                    self.capture_locked = True

                    self.capture_pose(
                        frame,
                        face,
                        required_pose
                    )

            # =================================================
            # WRONG POSE
            # =================================================

            else:

                self.stable_start = None

                self.camera_status.config(
                    text=f"Detected {direction}",
                    fg=WARNING
                )

                self.camera_instruction.config(
                    text=instruction
                )

        # ====================================================
        # DISPLAY
        # ====================================================

        self.display_frame(
            frame
        )

        if self.camera_running:

            self.after(
                20,
                self.update_camera
            )

    # ========================================================
    # CAPTURE POSE
    # ========================================================

    def capture_pose(
        self,
        frame,
        face,
        pose
    ):

        try:

            feature = (
                self.face_system.get_feature(
                    frame,
                    face
                )
            )

            if feature is None:

                raise ValueError(
                    "Could not extract face features."
                )

            embedding_data = pickle.dumps(
                feature
            )

            save_embedding(
                self.employee_id,
                pose,
                embedding_data
            )

            self.enrolled_poses.append(
                pose
            )

        except Exception as error:

            self.capture_locked = False
            self.stable_start = None

            messagebox.showerror(
                "Capture Error",
                str(error),
                parent=self
            )

            return

        # ----------------------------------------------------
        # CAPTURE SUCCESS
        # ----------------------------------------------------

        self.camera_status.config(
            text=f"✓ {pose} FACE CAPTURED",
            fg=SUCCESS
        )

        self.camera_instruction.config(
            text="Capture successful"
        )

        # ----------------------------------------------------
        # MOVE TO NEXT POSE AFTER 900ms
        # ----------------------------------------------------

        self.after(
            900,
            self.next_pose
        )

    # ========================================================
    # NEXT POSE
    # ========================================================

    def next_pose(self):

        if not self.camera_running:
            return

        self.current_pose_index += 1
        self.stable_start = None
        self.capture_locked = False

        # ====================================================
        # ALL THREE COMPLETED
        # ====================================================

        if self.current_pose_index >= len(
            self.poses
        ):

            self.finish_enrollment()

            return

        required_pose, instruction = (
            self.poses[
                self.current_pose_index
            ]
        )

        # ----------------------------------------------------
        # UPDATE UI
        # ----------------------------------------------------

        self.progress_label.config(
            text=(
                f"STEP "
                f"{self.current_pose_index + 1}"
                f" / 3"
            )
        )

        self.pose_label.config(
            text=instruction
        )

        self.camera_status.config(
            text="Get ready...",
            fg=MUTED
        )

        self.camera_instruction.config(
            text=instruction
        )

        # ====================================================
        # PLAY NEXT POSE AUDIO
        # ====================================================

        if required_pose == "LEFT":

            # audio/look_left.mp3

            self.audio.play(
                "look_left.mp3"
            )

        elif required_pose == "RIGHT":

            # audio/look_right.mp3

            self.audio.play(
                "look_right.mp3"
            )

    # ========================================================
    # FINISH ENROLLMENT
    # ========================================================

    def finish_enrollment(self):

        # ----------------------------------------------------
        # Mark registration complete
        # ----------------------------------------------------

        self.enrollment_completed = True

        # ----------------------------------------------------
        # PLAY COMPLETION AUDIO
        #
        # audio/registration_complete.mp3
        # ----------------------------------------------------

        self.audio.play(
            "registration_complete.mp3"
        )

        # ----------------------------------------------------
        # STOP CAMERA
        # ----------------------------------------------------

        self.stop_camera()

        # ----------------------------------------------------
        # UPDATE UI
        # ----------------------------------------------------

        self.progress_label.config(
            text="✓ COMPLETE",
            fg=SUCCESS
        )

        self.pose_label.config(
            text="FACE ENROLLMENT COMPLETE",
            fg=SUCCESS
        )

        self.camera_status.config(
            text="3 face poses successfully registered",
            fg=SUCCESS
        )

        self.camera_instruction.config(
            text=(
                f"{self.employee_name} • "
                f"{self.employee_code}"
            )
        )

        self.camera_view.config(
            image="",
            text=(
                "✓\n\n"
                "ENROLLMENT COMPLETE\n\n"
                f"{self.employee_name}\n"
                f"{self.employee_code}"
            ),
            font=("Segoe UI", 22, "bold"),
            fg=SUCCESS,
            bg=CAMERA_BG
        )

        # ----------------------------------------------------
        # DONE BUTTON
        # ----------------------------------------------------

        self.done_button = tk.Button(
            self,
            text="DONE",
            font=("Segoe UI", 12, "bold"),
            fg="white",
            bg=ACCENT,
            activebackground="#2F8DCE",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=40,
            pady=12,
            command=self.close_window
        )

        self.done_button.pack(
            side="bottom",
            anchor="e",
            padx=50,
            pady=20
        )

    # ========================================================
    # DRAW FACE
    # ========================================================

    def draw_face(
        self,
        frame,
        face,
        color
    ):

        x, y, w, h = face[:4]

        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)

        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            color,
            3
        )

        if len(face) >= 14:

            for i in range(5):

                px = int(
                    face[
                        4 + i * 2
                    ]
                )

                py = int(
                    face[
                        5 + i * 2
                    ]
                )

                cv2.circle(
                    frame,
                    (px, py),
                    4,
                    color,
                    -1
                )

    # ========================================================
    # DISPLAY FRAME
    # ========================================================

    def display_frame(
        self,
        frame
    ):

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        image = Image.fromarray(
            rgb
        )

        width = self.camera_view.winfo_width()
        height = self.camera_view.winfo_height()

        if width <= 10:
            width = 640

        if height <= 10:
            height = 480

        image_ratio = (
            image.width / image.height
        )

        available_ratio = (
            width / height
        )

        if image_ratio > available_ratio:

            new_width = width

            new_height = int(
                width / image_ratio
            )

        else:

            new_height = height

            new_width = int(
                height * image_ratio
            )

        new_width = max(
            1,
            new_width
        )

        new_height = max(
            1,
            new_height
        )

        image = image.resize(
            (
                new_width,
                new_height
            ),
            Image.Resampling.LANCZOS
        )

        self.photo = ImageTk.PhotoImage(
            image
        )

        self.camera_view.config(
            image=self.photo,
            text=""
        )

    # ========================================================
    # FAILED ENROLLMENT CLEANUP
    # ========================================================

    def cleanup_failed_enrollment(self):

        self.stop_camera()

        # ----------------------------------------------------
        # STOP AUDIO
        # ----------------------------------------------------

        self.audio.stop()

        # ----------------------------------------------------
        # DELETE TEMPORARY EMPLOYEE / STUDENT
        # ----------------------------------------------------

        if self.employee_id is not None:

            try:

                delete_employee(
                    self.employee_id
                )

                print(
                    "Incomplete enrollment deleted."
                )

            except Exception as error:

                print(
                    "Could not delete incomplete "
                    "employee/student:",
                    error
                )

            self.employee_id = None

    # ========================================================
    # STOP CAMERA
    # ========================================================

    def stop_camera(self):

        self.camera_running = False

        if self.camera is not None:

            try:

                self.camera.release()

            except Exception:

                pass

            self.camera = None

    # ========================================================
    # CLOSE WINDOW
    # ========================================================

    def close_window(self):

        # ----------------------------------------------------
        # STOP CAMERA
        # ----------------------------------------------------

        self.stop_camera()

        # ----------------------------------------------------
        # STOP + CLEANUP AUDIO
        # ----------------------------------------------------

        try:

            self.audio.cleanup()

        except Exception:

            pass

        # ----------------------------------------------------
        # DELETE INCOMPLETE REGISTRATION
        # ----------------------------------------------------

        if (
            self.employee_id is not None
            and not self.enrollment_completed
        ):

            try:

                delete_employee(
                    self.employee_id
                )

                print(
                    "Incomplete employee/student "
                    "registration removed."
                )

            except Exception as error:

                print(
                    "Could not remove incomplete "
                    "employee/student:",
                    error
                )

        # ----------------------------------------------------
        # CLOSE WINDOW
        # ----------------------------------------------------

        self.destroy()


# ============================================================
# DIRECT RUN
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    root.withdraw()

    window = FaceEnrollment(
        root
    )

    window.grab_set()

    root.mainloop()