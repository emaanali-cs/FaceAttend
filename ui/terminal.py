import tkinter as tk
from tkinter import messagebox
from datetime import datetime

import cv2
from PIL import Image, ImageTk

from recognition.face_recognition import (
    FaceSystem,
    load_registered_faces,
    recognize_face
)

from database.database import (
    mark_check_in,
    mark_check_out
)


# ============================================================
# SETTINGS
# ============================================================

CAMERA_ID = 0

MATCH_THRESHOLD = 0.55

# How long the success/notice result remains visible
SUCCESS_DISPLAY_TIME = 3000


# ============================================================
# ATTENDANCE TERMINAL
# ============================================================

class AttendanceTerminal(tk.Tk):

    def __init__(self):

        super().__init__()

        # ----------------------------------------------------
        # WINDOW
        # ----------------------------------------------------

        self.title(
            "FaceAttend - Attendance Terminal"
        )

        self.geometry(
            "1400x850"
        )

        self.minsize(
            1100,
            700
        )

        self.configure(
            bg="#08111F"
        )

        # ----------------------------------------------------
        # CAMERA STATE
        # ----------------------------------------------------

        self.camera = None

        self.camera_running = False

        self.current_mode = None

        # ----------------------------------------------------
        # RECOGNITION STATE
        # ----------------------------------------------------

        self.face_system = None

        self.registered_faces = []

        # ----------------------------------------------------
        # DISPLAY STATE
        # ----------------------------------------------------

        self.photo = None

        self.result_displaying = False

        # ----------------------------------------------------
        # UI
        # ----------------------------------------------------

        self.create_header()

        self.create_main_area()

        self.update_clock()

        # ----------------------------------------------------
        # WINDOW CLOSE
        # ----------------------------------------------------

        self.protocol(
            "WM_DELETE_WINDOW",
            self.close_application
        )


    # ========================================================
    # HEADER
    # ========================================================

    def create_header(self):

        header = tk.Frame(
            self,
            bg="#111B2D",
            height=70
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(
            False
        )

        # ----------------------------------------------------
        # BRAND
        # ----------------------------------------------------

        brand = tk.Label(
            header,
            text="FACEATTEND",
            font=("Segoe UI", 25, "bold"),
            fg="#F5F7FA",
            bg="#111B2D"
        )

        brand.pack(
            side="left",
            padx=(35, 25)
        )

        # ----------------------------------------------------
        # SUBTITLE
        # ----------------------------------------------------

        subtitle = tk.Label(
            header,
            text="SMART ATTENDANCE TERMINAL",
            font=("Segoe UI", 11),
            fg="#8FA6C2",
            bg="#111B2D"
        )

        subtitle.pack(
            side="left"
        )

        # ----------------------------------------------------
        # CLOCK
        # ----------------------------------------------------

        self.clock_label = tk.Label(
            header,
            font=("Segoe UI", 12, "bold"),
            fg="#F5F7FA",
            bg="#111B2D",
            justify="right"
        )

        self.clock_label.pack(
            side="right",
            padx=35
        )


    # ========================================================
    # MAIN AREA
    # ========================================================

    def create_main_area(self):

        container = tk.Frame(
            self,
            bg="#08111F"
        )

        container.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=30
        )

        # ====================================================
        # CAMERA PANEL
        # ====================================================

        camera_panel = tk.Frame(
            container,
            bg="#111B2D"
        )

        camera_panel.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 20)
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title = tk.Label(
            camera_panel,
            text="Attendance Terminal",
            font=("Segoe UI", 25, "bold"),
            fg="#F5F7FA",
            bg="#111B2D"
        )

        title.pack(
            pady=(35, 5)
        )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        self.status_label = tk.Label(
            camera_panel,
            text="Ready to scan",
            font=("Segoe UI", 13),
            fg="#8FA6C2",
            bg="#111B2D"
        )

        self.status_label.pack(
            pady=(0, 25)
        )

        # ----------------------------------------------------
        # CAMERA VIEW
        # ----------------------------------------------------

        self.camera_view = tk.Label(
            camera_panel,
            text=(
                "CAMERA\n\n"
                "Click CHECK IN or CHECK OUT\n"
                "to begin"
            ),
            font=("Segoe UI", 20, "bold"),
            fg="#657994",
            bg="#020817",
            justify="center"
        )

        self.camera_view.pack(
            fill="both",
            expand=True,
            padx=40,
            pady=(0, 25)
        )

        # ----------------------------------------------------
        # INSTRUCTION
        # ----------------------------------------------------

        self.instruction_label = tk.Label(
            camera_panel,
            text="Position your face inside the camera view",
            font=("Segoe UI", 12),
            fg="#8FA6C2",
            bg="#111B2D"
        )

        self.instruction_label.pack(
            pady=(0, 25)
        )

        # ====================================================
        # RIGHT PANEL
        # ====================================================

        side_panel = tk.Frame(
            container,
            bg="#111B2D",
            width=285
        )

        side_panel.pack(
            side="right",
            fill="y"
        )

        side_panel.pack_propagate(
            False
        )

        # ----------------------------------------------------
        # HEADING
        # ----------------------------------------------------

        tk.Label(
            side_panel,
            text="MARK ATTENDANCE",
            font=("Segoe UI", 16, "bold"),
            fg="#F5F7FA",
            bg="#111B2D"
        ).pack(
            pady=(60, 35)
        )

        # ----------------------------------------------------
        # CHECK-IN BUTTON
        # ----------------------------------------------------

        self.checkin_button = tk.Button(
            side_panel,
            text="CHECK IN",
            font=("Segoe UI", 16, "bold"),
            fg="white",
            bg="#2478B8",
            activebackground="#2F8DCE",
            activeforeground="white",
            disabledforeground="#8293A6",
            relief="flat",
            cursor="hand2",
            height=2,
            command=self.start_checkin
        )

        self.checkin_button.pack(
            fill="x",
            padx=45,
            pady=10
        )

        # ----------------------------------------------------
        # CHECK-OUT BUTTON
        # ----------------------------------------------------

        self.checkout_button = tk.Button(
            side_panel,
            text="CHECK OUT",
            font=("Segoe UI", 16, "bold"),
            fg="white",
            bg="#2478B8",
            activebackground="#2F8DCE",
            activeforeground="white",
            disabledforeground="#8293A6",
            relief="flat",
            cursor="hand2",
            height=2,
            command=self.start_checkout
        )

        self.checkout_button.pack(
            fill="x",
            padx=45,
            pady=10
        )

        # ----------------------------------------------------
        # SYSTEM STATUS BOX
        # ----------------------------------------------------

        status_box = tk.Frame(
            side_panel,
            bg="#0D1728"
        )

        status_box.pack(
            fill="x",
            padx=45,
            pady=(55, 20)
        )

        tk.Label(
            status_box,
            text="SYSTEM STATUS",
            font=("Segoe UI", 10, "bold"),
            fg="#7189A6",
            bg="#0D1728"
        ).pack(
            pady=(18, 5)
        )

        self.system_status = tk.Label(
            status_box,
            text="● Ready",
            font=("Segoe UI", 14, "bold"),
            fg="#20D66B",
            bg="#0D1728"
        )

        self.system_status.pack(
            pady=(0, 18)
        )

        # ----------------------------------------------------
        # ADMIN BUTTON
        # ----------------------------------------------------

        admin_button = tk.Button(
            side_panel,
            text="ADMIN DASHBOARD",
            font=("Segoe UI", 11),
            fg="#D8E2EF",
            bg="#1C2A3E",
            activebackground="#263A54",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.open_admin
        )

        admin_button.pack(
            side="bottom",
            fill="x",
            padx=45,
            pady=35
        )


    # ========================================================
    # CLOCK
    # ========================================================

    def update_clock(self):

        now = datetime.now()

        self.clock_label.config(
            text=now.strftime(
                "%A, %d %B %Y\n%I:%M:%S %p"
            )
        )

        self.after(
            1000,
            self.update_clock
        )


    # ========================================================
    # LOAD RECOGNITION SYSTEM
    # ========================================================

    def load_recognition(self):

        try:

            # Load recognition models only once
            if self.face_system is None:

                self.face_system = FaceSystem()

            # Load registered employees
            self.registered_faces = (
                load_registered_faces()
            )

            if not self.registered_faces:

                messagebox.showwarning(
                    "No Employees",
                    "No registered employees were found.\n\n"
                    "Please enroll an employee first."
                )

                return False

            return True

        except Exception as e:

            messagebox.showerror(
                "Recognition Error",
                "Could not load face recognition system:\n\n"
                f"{e}"
            )

            return False


    # ========================================================
    # START CHECK-IN
    # ========================================================

    def start_checkin(self):

        if self.camera_running:

            return

        if not self.load_recognition():

            return

        self.current_mode = "checkin"

        self.status_label.config(
            text="Check-in mode active"
        )

        self.instruction_label.config(
            text="Look directly at the camera"
        )

        self.system_status.config(
            text="● Scanning",
            fg="#F5C542"
        )

        self.disable_buttons()

        self.open_camera()


    # ========================================================
    # START CHECK-OUT
    # ========================================================

    def start_checkout(self):

        if self.camera_running:

            return

        if not self.load_recognition():

            return

        self.current_mode = "checkout"

        self.status_label.config(
            text="Check-out mode active"
        )

        self.instruction_label.config(
            text="Look directly at the camera"
        )

        self.system_status.config(
            text="● Scanning",
            fg="#F5C542"
        )

        self.disable_buttons()

        self.open_camera()


    # ========================================================
    # OPEN CAMERA
    # ========================================================

    def open_camera(self):

        self.camera = cv2.VideoCapture(
            CAMERA_ID
        )

        if not self.camera.isOpened():

            self.camera = None

            messagebox.showerror(
                "Camera Error",
                "Could not open the camera."
            )

            self.reset_terminal()

            return

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Do NOT force camera resolution here.
        #
        # Some webcams change their field of view when a
        # different resolution is requested.
        # ----------------------------------------------------

        self.camera_running = True

        self.result_displaying = False

        self.update_camera()


    # ========================================================
    # UPDATE CAMERA
    # ========================================================

    def update_camera(self):

        if not self.camera_running:

            return

        # ----------------------------------------------------
        # Read frame
        # ----------------------------------------------------

        success, frame = self.camera.read()

        if not success:

            self.stop_camera()

            messagebox.showerror(
                "Camera Error",
                "Could not read from the camera."
            )

            self.reset_terminal()

            return

        # ----------------------------------------------------
        # Mirror camera
        # ----------------------------------------------------

        frame = cv2.flip(
            frame,
            1
        )

        # ----------------------------------------------------
        # Detect faces
        # ----------------------------------------------------

        faces = self.face_system.detect(
            frame
        )

        # ====================================================
        # NO FACE
        # ====================================================

        if len(faces) == 0:

            self.status_label.config(
                text="Searching for face..."
            )

            self.instruction_label.config(
                text="Position your face inside the camera view"
            )

            self.system_status.config(
                text="● Scanning",
                fg="#F5C542"
            )

            self.draw_top_status(
                frame,
                "LOOK AT CAMERA",
                "normal"
            )


        # ====================================================
        # MULTIPLE FACES
        # ====================================================

        elif len(faces) > 1:

            self.status_label.config(
                text="Multiple faces detected"
            )

            self.instruction_label.config(
                text="Please make sure only one person is visible"
            )

            self.system_status.config(
                text="● Attention",
                fg="#F5C542"
            )

            self.draw_top_status(
                frame,
                "ONE PERSON AT A TIME",
                "warning"
            )

            for face in faces:

                self.draw_face(
                    frame,
                    face,
                    "warning"
                )


        # ====================================================
        # ONE FACE
        # ====================================================

        else:

            face = faces[0]

            x, y, w, h = face[:4]

            x = int(x)
            y = int(y)
            w = int(w)
            h = int(h)

            # ------------------------------------------------
            # Generate face feature
            # ------------------------------------------------

            try:

                feature = (
                    self.face_system.get_feature(
                        frame,
                        face
                    )
                )

                match, score = recognize_face(
                    self.face_system,
                    feature,
                    self.registered_faces
                )

            except Exception:

                match = None

                score = 0.0

            # =================================================
            # RECOGNIZED PERSON
            # =================================================

            if match and score >= MATCH_THRESHOLD:

                name = match["name"]

                employee_code = (
                    match["employee_code"]
                )

                employee_id = (
                    match["employee_id"]
                )

                self.status_label.config(
                    text=f"Identity verified • {name}"
                )

                self.instruction_label.config(
                    text="Identity recognized"
                )

                self.system_status.config(
                    text="● Verified",
                    fg="#20D66B"
                )

                # ------------------------------------------------
                # Clean face box
                # ------------------------------------------------

                self.draw_face(
                    frame,
                    face,
                    "success",
                    name=name
                )

                self.draw_top_status(
                    frame,
                    "IDENTITY VERIFIED",
                    "success"
                )

                # ------------------------------------------------
                # Record attendance only once
                # ------------------------------------------------

                if not self.result_displaying:

                    self.result_displaying = True

                    # ============================================
                    # CHECK-IN
                    # ============================================

                    if self.current_mode == "checkin":

                        marked, result = (
                            mark_check_in(
                                employee_id
                            )
                        )

                        if marked:

                            self.show_success(
                                frame,
                                "CHECK-IN SUCCESSFUL",
                                name,
                                employee_code,
                                result
                            )

                        else:

                            self.show_result(
                                frame,
                                "ALREADY CHECKED IN",
                                name,
                                employee_code,
                                result,
                                "warning"
                            )

                    # ============================================
                    # CHECK-OUT
                    # ============================================

                    else:

                        marked, result = (
                            mark_check_out(
                                employee_id
                            )
                        )

                        if marked:

                            self.show_success(
                                frame,
                                "CHECK-OUT SUCCESSFUL",
                                name,
                                employee_code,
                                result
                            )

                        else:

                            self.show_result(
                                frame,
                                "CHECK-OUT NOT RECORDED",
                                name,
                                employee_code,
                                result,
                                "warning"
                            )

                    # ------------------------------------------------
                    # Keep result visible for a few seconds
                    # ------------------------------------------------

                    self.after(
                        SUCCESS_DISPLAY_TIME,
                        self.reset_terminal
                    )


            # =================================================
            # UNKNOWN PERSON
            # =================================================

            else:

                self.status_label.config(
                    text="Face detected • Identity not recognized"
                )

                self.instruction_label.config(
                    text="Please try again"
                )

                self.system_status.config(
                    text="● Not Recognized",
                    fg="#F05A5A"
                )

                self.draw_face(
                    frame,
                    face,
                    "unknown"
                )

                self.draw_top_status(
                    frame,
                    "IDENTITY NOT RECOGNIZED",
                    "error"
                )

        # ----------------------------------------------------
        # Display camera frame
        # ----------------------------------------------------

        self.display_frame(
            frame
        )

        # ----------------------------------------------------
        # Continue camera loop
        # ----------------------------------------------------

        if self.camera_running:

            self.after(
                15,
                self.update_camera
            )


    # ========================================================
    # DRAW FACE
    # ========================================================

    def draw_face(
        self,
        frame,
        face,
        state,
        name=None
    ):

        x, y, w, h = face[:4]

        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)

        # ----------------------------------------------------
        # Colors
        # ----------------------------------------------------

        if state == "success":

            color = (40, 220, 100)

        elif state == "unknown":

            color = (60, 90, 255)

        elif state == "warning":

            color = (0, 180, 255)

        else:

            color = (255, 200, 60)

        # ----------------------------------------------------
        # Face bounding box
        # ----------------------------------------------------

        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            color,
            3
        )

        # ----------------------------------------------------
        # Label
        # ----------------------------------------------------

        if name:

            label = name

        elif state == "unknown":

            label = "IDENTITY NOT RECOGNIZED"

        elif state == "warning":

            label = "PLEASE WAIT"

        else:

            label = "FACE DETECTED"

        # ----------------------------------------------------
        # Label dimensions
        # ----------------------------------------------------

        font = cv2.FONT_HERSHEY_SIMPLEX

        scale = 0.65

        thickness = 2

        (text_w, text_h), _ = (
            cv2.getTextSize(
                label,
                font,
                scale,
                thickness
            )
        )

        label_top = max(
            y - text_h - 15,
            5
        )

        # ----------------------------------------------------
        # Label background
        # ----------------------------------------------------

        cv2.rectangle(
            frame,
            (
                x,
                label_top
            ),
            (
                x + text_w + 20,
                label_top + text_h + 15
            ),
            color,
            -1
        )

        # ----------------------------------------------------
        # Label text
        # ----------------------------------------------------

        cv2.putText(
            frame,
            label,
            (
                x + 10,
                label_top + text_h + 4
            ),
            font,
            scale,
            (255, 255, 255),
            thickness
        )


    # ========================================================
    # TOP STATUS
    # ========================================================

    def draw_top_status(
        self,
        frame,
        text,
        state
    ):

        if state == "success":

            color = (40, 220, 100)

        elif state == "error":

            color = (60, 90, 255)

        elif state == "warning":

            color = (0, 180, 255)

        else:

            color = (255, 200, 60)

        # ----------------------------------------------------
        # Banner
        # ----------------------------------------------------

        cv2.rectangle(
            frame,
            (20, 20),
            (455, 70),
            (2, 8, 23),
            -1
        )

        cv2.putText(
            frame,
            text,
            (35, 53),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            color,
            2
        )


    # ========================================================
    # RESULT OVERLAY
    # ========================================================

    def draw_result_overlay(
        self,
        frame,
        action,
        name,
        employee_code,
        time_value,
        state
    ):

        height, width = frame.shape[:2]

        # ----------------------------------------------------
        # Colors
        # ----------------------------------------------------

        if state == "success":

            color = (40, 220, 100)

        else:

            color = (0, 180, 255)

        # ----------------------------------------------------
        # Main result panel
        # ----------------------------------------------------

        panel_width = min(
            width - 50,
            620
        )

        panel_height = 145

        x1 = int(
            (width - panel_width) / 2
        )

        y1 = height - panel_height - 25

        x2 = x1 + panel_width

        y2 = y1 + panel_height

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (2, 8, 23),
            -1
        )

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y1 + 5),
            color,
            -1
        )

        # ----------------------------------------------------
        # Action
        # ----------------------------------------------------

        cv2.putText(
            frame,
            action,
            (
                x1 + 25,
                y1 + 45
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            color,
            2
        )

        # ----------------------------------------------------
        # Employee
        # ----------------------------------------------------

        cv2.putText(
            frame,
            name,
            (
                x1 + 25,
                y1 + 82
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        # ----------------------------------------------------
        # Employee code + time
        # ----------------------------------------------------

        detail = (
            f"{employee_code}  •  {time_value}"
        )

        cv2.putText(
            frame,
            detail,
            (
                x1 + 25,
                y1 + 115
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (170, 190, 210),
            1
        )


    # ========================================================
    # DISPLAY FRAME IN TKINTER
    # ========================================================

    def display_frame(
        self,
        frame
    ):

        # ----------------------------------------------------
        # BGR -> RGB
        # ----------------------------------------------------

        frame_rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        image = Image.fromarray(
            frame_rgb
        )

        # ----------------------------------------------------
        # Camera display dimensions
        # ----------------------------------------------------

        width = self.camera_view.winfo_width()

        height = self.camera_view.winfo_height()

        if width <= 10:

            width = 800

        if height <= 10:

            height = 450

        # ----------------------------------------------------
        # Preserve aspect ratio
        # ----------------------------------------------------

        image.thumbnail(
            (width, height),
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
    # SUCCESS RESULT
    # ========================================================

    def show_success(
        self,
        frame,
        action,
        name,
        employee_code,
        time_value
    ):

        # ----------------------------------------------------
        # Update main UI
        # ----------------------------------------------------

        self.status_label.config(
            text=f"✓ {action.title()}"
        )

        if self.current_mode == "checkin":

            self.instruction_label.config(
                text=f"Welcome, {name}"
            )

        else:

            self.instruction_label.config(
                text=f"Goodbye, {name}"
            )

        self.system_status.config(
            text="● Success",
            fg="#20D66B"
        )

        # ----------------------------------------------------
        # Draw result on camera
        # ----------------------------------------------------

        self.draw_result_overlay(
            frame,
            action,
            name,
            employee_code,
            time_value,
            "success"
        )


    # ========================================================
    # NOTICE RESULT
    # ========================================================

    def show_result(
        self,
        frame,
        action,
        name,
        employee_code,
        result,
        state
    ):

        # ----------------------------------------------------
        # Update UI
        # ----------------------------------------------------

        self.status_label.config(
            text=action
        )

        self.instruction_label.config(
            text=f"{name} • {employee_code}"
        )

        self.system_status.config(
            text="● Notice",
            fg="#F5C542"
        )

        # ----------------------------------------------------
        # Draw result on camera
        # ----------------------------------------------------

        self.draw_result_overlay(
            frame,
            action,
            name,
            employee_code,
            result,
            state
        )


    # ========================================================
    # DISABLE BUTTONS
    # ========================================================

    def disable_buttons(self):

        self.checkin_button.config(
            state="disabled"
        )

        self.checkout_button.config(
            state="disabled"
        )


    # ========================================================
    # ENABLE BUTTONS
    # ========================================================

    def enable_buttons(self):

        self.checkin_button.config(
            state="normal"
        )

        self.checkout_button.config(
            state="normal"
        )


    # ========================================================
    # STOP CAMERA
    # ========================================================

    def stop_camera(self):

        self.camera_running = False

        if self.camera is not None:

            self.camera.release()

            self.camera = None


    # ========================================================
    # RESET TERMINAL
    # ========================================================

    def reset_terminal(self):

        self.stop_camera()

        self.current_mode = None

        self.result_displaying = False

        self.photo = None

        # ----------------------------------------------------
        # Reset camera display
        # ----------------------------------------------------

        self.camera_view.config(
            image="",
            text=(
                "CAMERA\n\n"
                "Click CHECK IN or CHECK OUT\n"
                "to begin"
            )
        )

        # ----------------------------------------------------
        # Reset labels
        # ----------------------------------------------------

        self.status_label.config(
            text="Ready to scan"
        )

        self.instruction_label.config(
            text="Position your face inside the camera view"
        )

        self.system_status.config(
            text="● Ready",
            fg="#20D66B"
        )

        # ----------------------------------------------------
        # Enable buttons
        # ----------------------------------------------------

        self.enable_buttons()


    # ========================================================
    # ADMIN DASHBOARD
    # ========================================================

    def open_admin(self):

        if self.camera_running:

            messagebox.showwarning(
                "Scanning Active",
                "Please finish the current attendance scan first."
            )

            return

        try:

            from admin.dashboard import (
                AdminDashboard
            )

            dashboard = AdminDashboard(
                self
            )

            dashboard.grab_set()

        except Exception as e:

            messagebox.showerror(
                "Admin Dashboard",
                "Could not open dashboard:\n\n"
                f"{e}"
            )


    # ========================================================
    # CLOSE APPLICATION
    # ========================================================

    def close_application(self):

        self.stop_camera()

        self.destroy()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    app = AttendanceTerminal()

    app.mainloop()