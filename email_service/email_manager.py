import os
import smtplib

from email.message import EmailMessage
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# EMAIL SETTINGS
# ============================================================

SMTP_SERVER = os.getenv(
    "SMTP_SERVER",
    "smtp.gmail.com"
)

SMTP_PORT = int(
    os.getenv(
        "SMTP_PORT",
        "587"
    )
)

SENDER_EMAIL = os.getenv(
    "SENDER_EMAIL"
)

SENDER_PASSWORD = os.getenv(
    "SENDER_PASSWORD"
)


# ============================================================
# SEND ATTENDANCE EMAIL
# ============================================================

def send_attendance_email(
    student_name,
    student_code,
    parent_email,
    attendance_type,
    attendance_time
):
    """
    Sends an attendance notification to a student's parent.

    This function is ONLY called for students.
    Employees will not receive attendance emails.
    """

    # --------------------------------------------------------
    # Validate email configuration
    # --------------------------------------------------------

    if not SENDER_EMAIL:
        return False, (
            "Sender email is not configured."
        )

    if not SENDER_PASSWORD:
        return False, (
            "Sender email password is not configured."
        )

    if not parent_email:
        return False, (
            "Parent email address is not available."
        )

    # --------------------------------------------------------
    # Determine attendance message
    # --------------------------------------------------------

    if attendance_type.upper() == "CHECK-IN":

        subject = (
            f"Student Check-In Notification - "
            f"{student_name}"
        )

        message = (
            f"Dear Parent/Guardian,\n\n"

            f"This is to inform you that "
            f"{student_name} "
            f"(Student ID: {student_code}) "
            f"has checked in successfully.\n\n"

            f"Check-in Time: {attendance_time}\n\n"

            f"Regards,\n"
            f"FaceAttend Attendance System"
        )

    elif attendance_type.upper() == "CHECK-OUT":

        subject = (
            f"Student Check-Out Notification - "
            f"{student_name}"
        )

        message = (
            f"Dear Parent/Guardian,\n\n"

            f"This is to inform you that "
            f"{student_name} "
            f"(Student ID: {student_code}) "
            f"has checked out successfully.\n\n"

            f"Check-out Time: {attendance_time}\n\n"

            f"Regards,\n"
            f"FaceAttend Attendance System"
        )

    else:

        return False, (
            "Invalid attendance type."
        )

    # --------------------------------------------------------
    # Create email
    # --------------------------------------------------------

    email = EmailMessage()

    email["Subject"] = subject

    email["From"] = SENDER_EMAIL

    email["To"] = parent_email

    email.set_content(
        message
    )

    # --------------------------------------------------------
    # Send email
    # --------------------------------------------------------

    try:

        with smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT
        ) as server:

            server.starttls()

            server.login(
                SENDER_EMAIL,
                SENDER_PASSWORD
            )

            server.send_message(
                email
            )

        print(
            f"Attendance email sent to "
            f"{parent_email}"
        )

        return True, (
            "Attendance email sent successfully."
        )

    except Exception as error:

        print(
            "Email sending failed:",
            error
        )

        return False, (
            f"Email sending failed: {error}"
        )