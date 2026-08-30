import tkinter as tk
from tkinter import messagebox

from database.database import (
    create_tables,
    mark_check_in,
    get_person_details
)

from attendance.live_verification import (
    run_live_verification
)

from email_service.email_manager import (
    send_attendance_email
)


# ============================================================
# CHECK-IN
# ============================================================

def run_checkin():

    create_tables()

    result = run_live_verification(
        mode="CHECK-IN"
    )

    # --------------------------------------------------------
    # Verification failed/cancelled
    # --------------------------------------------------------

    if not result["success"]:

        root = tk.Tk()
        root.withdraw()

        messagebox.showwarning(
            "Check-In",
            result["reason"]
        )

        root.destroy()
        return

    # --------------------------------------------------------
    # Recognized person
    # --------------------------------------------------------

    person = result["person"]

    success, checkin_time = mark_check_in(
        person["employee_id"]
    )

    root = tk.Tk()
    root.withdraw()

    if success:

        # ----------------------------------------------------
        # GET PERSON DETAILS
        # ----------------------------------------------------

        person_details = get_person_details(
            person["employee_id"]
        )

        # ----------------------------------------------------
        # EMAIL ONLY FOR STUDENTS
        # ----------------------------------------------------

        if person_details:

            person_type = person_details[4]

            parent_email = person_details[5]

            if (
                person_type
                and person_type.lower() == "student"
                and parent_email
            ):

                email_success, email_message = send_attendance_email(
                    parent_email=parent_email,
                    student_name=person_details[2],
                    student_code=person_details[1],
                    attendance_type="CHECK-IN",
                    attendance_time=checkin_time
                )

                print(
                    "EMAIL RESULT:",
                    email_success,
                    email_message
                )

        # ----------------------------------------------------
        # EXISTING UI
        # ----------------------------------------------------

        messagebox.showinfo(
            "Check-In Successful",
            (
                f"Welcome, {person['name']}!\n\n"
                f"Employee ID: "
                f"{person['employee_code']}\n\n"
                f"Check-in time: "
                f"{checkin_time}"
            )
        )

    else:

        messagebox.showwarning(
            "Check-In",
            checkin_time
        )

    root.destroy()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    run_checkin()