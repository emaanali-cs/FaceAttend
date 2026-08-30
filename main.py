import tkinter as tk

from database.database import create_tables
from admin.dashboard import Dashboard


# ============================================================
# MAIN
# ============================================================

def main():

    create_tables()

    app = Dashboard()

    app.mainloop()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()