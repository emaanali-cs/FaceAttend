# FaceAttend

**Desktop face-recognition attendance system with liveness challenges, three-pose enrollment, and automated parent email notifications.**

[![Python](https://img.shields.io/badge/Python-3.13.7-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-5.0.0-5C3EE8?logo=opencv&logoColor=white)](https://opencv.org/)
[![NumPy](https://img.shields.io/badge/NumPy-2.3.4-013243?logo=numpy&logoColor=white)](https://numpy.org/)
[![Pillow](https://img.shields.io/badge/Pillow-12.0.0-3776AB?logo=python&logoColor=white)](https://python-pillow.org/)
[![pygame](https://img.shields.io/badge/pygame-2.6.1-2E6E4E?logo=pygame&logoColor=white)](https://www.pygame.org/)
[![python-dotenv](https://img.shields.io/badge/python--dotenv-1.2.3-ECB52B?logo=python&logoColor=white)](https://pypi.org/project/python-dotenv/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)](#known-issues-and-caveats)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Version note:** `requirements.txt` contains **no version pins at all** (5 bare package names). The versions in
> the badges above were **read from a live environment** (`Python 3.13.7`, `opencv-python 5.0.0.93`,
> `numpy 2.3.4`, `pillow 12.0.0`, `pygame 2.6.1`, `python-dotenv 1.2.3` on Windows), **not** from the repository.
> A fresh clone may resolve to different, untested versions.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup Guide](#setup-guide)
- [Execution Guide](#execution-guide)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Security Notes](#security-notes)
- [Known Issues and Caveats](#known-issues-and-caveats)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

FaceAttend is a single-machine, offline-capable desktop attendance application. An operator registers employees
and students by capturing three head poses (center, left, right) from a webcam; each pose is stored as a 128-D
SFace embedding blob in SQLite. At check-in or check-out time the app runs a **liveness challenge** — the user must
successively hold center, left, and right head positions — before a single attendance row is written. If the
registered person has `person_type = 'Student'` and a parent email on file, a check-in/check-out notification is
sent over SMTP with STARTTLS.

There is no server, no web framework, and no network dependency other than the optional parent-notification email.

---

## Features

Every item below was verified by reading the cited source lines. Dead code and broken paths are documented in
[Known Issues and Caveats](#known-issues-and-caveats) instead of being presented as features.

| # | Feature | Evidence |
|---|---------|----------|
| 1 | **Tkinter admin dashboard** with sidebar navigation, maximized on launch (falls back to full-screen geometry if `state("zoomed")` fails) | `admin/dashboard.py:247`, `admin/dashboard.py:265-276` |
| 2 | **Four live stat cards** — Total People, Present Today, Checked In, Checked Out — all recomputed from SQL on every refresh | `admin/dashboard.py:794-836`, `admin/dashboard.py:93-142` |
| 3 | **Today's attendance table** (`ttk.Treeview`) with per-column minwidth/stretches and a vertical scrollbar | `admin/dashboard.py:1013-1119` |
| 4 | **Live clock + date** in the header, refreshed every 1000 ms via `Tk.after` | `admin/dashboard.py:1715-1734` |
| 5 | **Person registration form** (ID, name, department, `Employee`/`Student` type, parent email) with per-field validation and a regex email check | `enrollment/face_enrollment.py:305-509`, `enrollment/face_enrollment.py:99-106` |
| 6 | **Parent-email field is conditionally enabled** only when Person Type is switched to `Student`, and cleared when switched back | `enrollment/face_enrollment.py:515-540` |
| 7 | **Three-pose face enrollment** (`CENTER` → `LEFT` → `RIGHT`) with live landmark overlay and a hold-still countdown | `enrollment/face_enrollment.py:212-216`, `enrollment/face_enrollment.py:1210-1260` |
| 8 | **Embedded 128-D SFace embeddings** persisted as `pickle` blobs, one row per pose | `enrollment/face_enrollment.py:1320-1328`, `database/database.py:322-348` |
| 9 | **Orphaned-record cleanup** — a partially enrolled person is deleted if enrollment fails or the window is closed mid-flow | `enrollment/face_enrollment.py:1670-1704`, `enrollment/face_enrollment.py:1754-1776` |
| 10 | **Spoken/audible pose guidance** via `pygame.mixer` using 4 committed MP3 clips (`look_center`, `look_left`, `look_right`, `registration_complete`) | `audio/audio_manager.py:26-51`, `enrollment/face_enrollment.py:1031,1433,1441,1463` |
| 11 | **Liveness challenge** on check-in/check-out: three poses must each be held for 0.8 s before verification passes | `attendance/live_verification.py:535-539`, `attendance/live_verification.py:45`, `attendance/live_verification.py:848-885` |
| 12 | **Head-direction estimation** derived from YuNet's 5-point landmarks (`yaw = (nose_x − eye_center_x) / eye_distance`, threshold 0.18) | `attendance/live_verification.py:135-190`, `attendance/live_verification.py:47` |
| 13 | **Recognition must be stable for 5 consecutive frames** and head direction stable for 5 frames, which suppresses single-frame misidentifications | `attendance/live_verification.py:51-53`, `attendance/live_verification.py:755-767`, `attendance/live_verification.py:446-469` |
| 14 | **15-second timeout** armed only *after* a face is first recognized; on expiry verification fails | `attendance/live_verification.py:49`, `attendance/live_verification.py:745-749`, `attendance/live_verification.py:947-969` |
| 15 | **Single-face enforcement** — 0 faces prompts positioning, 2+ faces is rejected and resets progress | `attendance/live_verification.py:634-674` |
| 16 | **`Q` cancels** the verification window at any time and returns a graceful failure dict | `attendance/live_verification.py:989-1004` |
| 17 | **Check-in / check-out flows** with one attendance row per person per day, enforced by a `UNIQUE(employee_id, attendance_date)` constraint | `attendance/checkin.py:23`, `attendance/checkout.py:23`, `database/database.py:144-147` |
| 18 | **Duplicate / out-of-order guards** — cannot check in twice, cannot check out twice, cannot check out without checking in | `database/database.py:515-521`, `database/database.py:597-616` |
| 19 | **Parent notification email, students only** — gated on `person_type.lower() == "student"` **and** a non-empty parent email | `attendance/checkin.py:81-93`, `attendance/checkout.py:81-93` |
| 20 | **SMTP with STARTTLS and login**, using `.env`-provided credentials via `python-dotenv` | `email_service/email_manager.py:12`, `email_service/email_manager.py:151-165` |
| 21 | **Manage People page** — lists all registered people and deletes a selected row behind a confirmation dialog | `admin/dashboard.py:1215`, `admin/dashboard.py:1568-1628` |
| 22 | **Cascading deletes** — removing a person also removes their embeddings and attendance rows | `database/database.py:115-118`, `database/database.py:140-143` |
| 23 | **Additive schema migration** — older databases are inspected with `PRAGMA table_info` and `person_type` / `parent_email` are `ALTER TABLE`-ed in if absent | `database/database.py:74-96` |
| 24 | **Check-in / check-out run in separate processes** via `subprocess.Popen([sys.executable, "-m", module])`, so a crash in a camera workflow cannot take down the dashboard | `admin/dashboard.py:218-229`, `admin/dashboard.py:511-527` |
| 25 | **Foreign keys are enforced** on every connection via `PRAGMA foreign_keys = ON` | `database/database.py:27-29`, `admin/dashboard.py:52-54` |
| 26 | **Audio degrades gracefully** — if `pygame.mixer.init()` fails the app still runs, printing the error and no-op'ing playback | `audio/audio_manager.py:47-50`, `audio/audio_manager.py:98-105` |

---

## Architecture

### How it runs end to end

`main.py` is the single entry point. It calls `create_tables()` (idempotent, `CREATE TABLE IF NOT EXISTS` plus the
migration) and then instantiates `Dashboard`, a `tk.Tk` subclass, and enters `mainloop()`.

The dashboard itself is a **launcher**, not a monolith:

- **Register Person** opens `FaceEnrollment`, a `tk.Toplevel` **in-process** (`admin/dashboard.py:1672-1696`).
  The Toplevel runs a `Tk.after(20, ...)` camera loop, converts each OpenCV BGR frame to a `PIL` image, and
  stores embeddings as they are captured.
- **Person Check-In / Check-Out** do *not* run in-process. `launch_module` shells out to
  `python -m attendance.checkin` / `python -m attendance.checkout` with `cwd` set to the repo root
  (`admin/dashboard.py:218-229`). Those child processes open a **native OpenCV window** (not Tk) for the liveness
  challenge, then write to the database and pop a `tkinter.messagebox`.

`attendance/live_verification.py` is the security-critical component and is deliberately **Tk-free except for one
measurement helper** (`get_screen_size`, used only to centre the OpenCV window). It re-loads the ONNX models and
all registered embeddings on every invocation (`attendance/live_verification.py:480-484`).

Recognition itself is a two-stage pipeline: `FaceSystem.detect` runs YuNet and filters on a 0.80 confidence floor
and an 80×80 minimum box size; `FaceSystem.get_feature` runs SFace's `alignCrop` + `feature`; matching is
**cosine similarity** (`cv2.FaceRecognizerSF_FR_COSINE`) against every stored embedding, best-score-wins, gated at
`MATCH_THRESHOLD = 0.55` (`recognition/face_recognition.py:29-34`, `recognition/face_recognition.py:155-165`,
`recognition/face_recognition.py:225-254`).

Note that a person with three enrolled poses has **three separate rows in `face_embeddings`**, and
`recognize_face` compares the live feature against all of them, so the best-matching pose wins.

### Data and control flow

![Architecture and data flow](docs/architecture.svg)

<sub>Source: [`docs/architecture.d2`](docs/architecture.d2). Rendered with `d2 --theme 0`. GitHub cannot render D2, so the SVG is committed and must be regenerated by hand after any change to the `.d2` file.</sub>

Want the full module-level wiring — every container, the manual test scripts, and the two known-broken
paths? See the [detailed diagram](docs/architecture-detailed.svg)
([source](docs/architecture-detailed.d2)). It is accurate but far too dense to embed inline, so it is
linked rather than inlined — open it full-size to read it.

> **Regenerating the diagrams:** each `.svg` is a build artifact and **will go stale** the moment its
> `.d2` changes. Re-render with:
>
> ```powershell
> d2 --theme 0 docs/architecture.d2          docs/architecture.svg
> d2 --theme 0 docs/architecture-detailed.d2 docs/architecture-detailed.svg
> ```
>
> The `--theme` flag is required — without it D2 substitutes its own default palette and the committed image
> will not match the source. Theme `0` is "Neutral Default" (light); theme `300` is "Terminal" (dark) if you
> would rather the image blend into GitHub dark mode. There is **no live rendering on GitHub for D2** the way
> there is for Mermaid, so there is no CI job that will catch a forgotten re-render for you.
>
> **Verified by execution.** Both diagrams were rendered with D2 v0.9.0 and visually inspected, including a
> simulation of GitHub's ~850 px embed width.
>
> *Simplified* (`architecture.svg`) — 2078×704 (**2.95:1**), 7 boxes, 7 edges, `direction: right`.
> At 850 px wide every box label is still legible, which is the whole reason it exists. No crossing edges
> and no overlapping boxes.
>
> *Detailed* (`architecture-detailed.svg`) — 4310×2165 (**1.99:1**), 7 containers, 26 shapes, 36 edges.
> Structurally verified: braces balance 19/19, every edge endpoint resolves to a declared node inside a
> declared container, and all labels are present in the rendered SVG. The semantic shapes really do render —
> the database is a cylinder, ONNX/MP3 files are `package`, SMTP is a `cloud`, `.env` is a dashed `document`
> (40 of 42 paths carry the curved geometry those need), and both broken paths are red dashed.
> **It is not legible when downscaled to README width** — the labels turn into roughly 3 px smudges — which
> is why it is linked above instead of embedded.

### Module dependency summary

| Module | Imports | Consumed by |
|--------|---------|-------------|
| `recognition/face_recognition.py` | `cv2`, `pickle`, `pathlib`; lazily imports `database.database` | `enrollment`, `attendance.live_verification`, `ui.terminal`, test scripts |
| `database/database.py` | `sqlite3`, `pathlib`, `datetime` | everything |
| `admin/dashboard.py` | `tkinter`, `sqlite3`, `subprocess`, `sys`; lazily imports `database.database`, `enrollment.face_enrollment` | `main.py` |
| `enrollment/face_enrollment.py` | `tkinter`, `cv2`, `pickle`, `numpy`, `re`, `PIL` | `admin.dashboard` |
| `attendance/live_verification.py` | `cv2`, `numpy`, `tkinter` (measurement only) | `attendance.checkin`, `attendance.checkout` |
| `audio/audio_manager.py` | `pygame`, `pathlib` | `enrollment.face_enrollment` |
| `email_service/email_manager.py` | `smtplib`, `email.message`, `dotenv` | `attendance.checkin`, `attendance.checkout` |
| `ui/terminal.py` | `tkinter`, `cv2`, `PIL` | **nothing** (orphan) |

---

## Tech Stack

| Technology | Version | Role |
|------------|---------|------|
| Python | 3.13.7 *(from environment; unpinned)* | Runtime. `tkinter` and `sqlite3` come from the stdlib and are **not** listed in `requirements.txt` |
| [OpenCV](https://opencv.org/) (`opencv-python`) | 5.0.0.93 *(from environment; unpinned)* | `FaceDetectorYN` (YuNet detection + 5 landmarks), `FaceRecognizerSF` (SFace alignment/embedding/cosine match), camera I/O, all on-screen drawing |
| [NumPy](https://numpy.org/) | 2.3.4 *(from environment; unpinned)* | Landmark arithmetic in `get_head_direction` (`attendance/live_verification.py:139-176`) |
| [Pillow](https://python-pillow.org/) | 12.0.0 *(from environment; unpinned)* | BGR→RGB conversion and `ImageTk.PhotoImage` for the Tk camera preview |
| [pygame](https://www.pygame.org/) | 2.6.1 *(from environment; unpinned)* | `pygame.mixer` MP3 playback of pose guidance |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | 1.2.3 *(from environment; unpinned)* | `load_dotenv()` for SMTP credentials (`email_service/email_manager.py:12`) |
| SQLite | 3.x (stdlib `sqlite3`) | Single local file `database/attendance.db`; 3 application tables |
| YuNet ONNX | `face_detection_yunet_2026may.onnx`, 229,738 bytes | Face detection, committed to the repo |
| SFace ONNX | `face_recognition_sface_2021dec.onnx`, 38,696,353 bytes | 128-D face embeddings, committed to the repo |

**Model files are committed**, so a fresh clone needs no extra model download. They account for 37.1 MB of the
37.4 MB tracked repository.

### Requirements coverage

`requirements.txt` lists exactly five packages: `opencv-python`, `numpy`, `Pillow`, `pygame`, `python-dotenv`.
Every third-party import in the codebase maps to one of these. **No undeclared third-party imports were found.**
`tkinter`, `sqlite3`, `pickle`, `smtplib`, `re`, `sys`, `subprocess`, `pathlib` and `datetime` are all stdlib.

---

## Project Structure

```
FaceAttend/
├── main.py                      # ENTRY POINT: create_tables() then Dashboard().mainloop()
├── requirements.txt             # 5 unpinned deps
├── test_audio.py                # manual audio smoke script (plays 1 clip, sleeps 5s)
├── LICENSE                      # MIT, Copyright (c) 2026 Emaan Ali
├── README.md                    # this file
├── .gitignore                   # 29 lines; excludes .env, *.db, __pycache__, images
│
├── admin/                       # [tracked] Admin console
│   ├── __init__.py
│   └── dashboard.py             # Dashboard(tk.Tk): stat cards, tables, subprocess launcher
│
├── attendance/                  # [tracked] Check-in / check-out orchestration
│   ├── __init__.py
│   ├── checkin.py               # run_checkin() -> liveness -> DB -> email
│   ├── checkout.py              # run_checkout() (mirror of checkin.py)
│   └── live_verification.py     # Liveness challenge loop (OpenCV window, no Tk UI)
│
├── audio/                       # [tracked] No __init__.py (PEP 420 namespace package)
│   ├── audio_manager.py         # AudioManager wrapping pygame.mixer
│   ├── look_center.mp3
│   ├── look_left.mp3
│   ├── look_right.mp3
│   └── registration_complete.mp3
│
├── config/                      # [tracked] ⚠ settings.py is 0 bytes and imported by nothing
│   └── settings.py              # (empty)
│
├── database/                    # [tracked]
│   ├── database.py              # ALL SQL + schema + migration (single source of truth)
│   ├── cleanup_employee.py      # ⚠ DESTRUCTIVE interactive script, runs on import
│   └── attendance.db            # ⚠ GITIGNORED (*.db) — absent on a fresh clone
│
├── docs/                        # [tracked] No __init__.py, not a Python package
│   ├── architecture.d2          # Simplified 7-box diagram embedded above (edit this one first)
│   ├── architecture.svg         #   └─ rendered image — regenerate with d2, never hand-edit
│   ├── architecture-detailed.d2 # Exhaustive module-level diagram incl. broken wiring
│   └── architecture-detailed.svg#   └─ rendered image — linked, not embedded (unreadable when scaled)
│
├── email_service/               # [tracked]
│   ├── __init__.py
│   └── email_manager.py         # SMTP + STARTTLS parent notification
│
├── enrollment/                  # [tracked]
│   ├── __init__.py
│   └── face_enrollment.py       # FaceEnrollment(tk.Toplevel): form + 3-pose capture
│
├── models/                      # [tracked] 37.1 MB of committed ONNX weights
│   ├── face_detection_yunet_2026may.onnx
│   └── face_recognition_sface_2021dec.onnx
│
├── recognition/                 # [tracked]
│   ├── __init__.py
│   ├── face_recognition.py      # FaceSystem + matching (the core)
│   ├── test_recognition.py      # manual camera script — works
│   ├── test_database_recognition.py  # manual camera script — works
│   └── test_detection.py        # ⚠ BROKEN: ImportError (see caveats)
│
├── ui/                          # [tracked]
│   ├── __init__.py
│   └── terminal.py              # ⚠ ORPHAN: no importer; its own open_admin() is broken
│
├── data/                        # ⚠ NOT TRACKED and NOT gitignored — contains only empty data/faces/
├── reports/                     # ⚠ NOT TRACKED and NOT gitignored — completely empty
├── .env.example                 # [tracked] Credential-free template — copy to .env (see Setup Guide)
├── .env                         # ⚠ GITIGNORED (.gitignore:11) — absent on a fresh clone. See Security Notes
└── __pycache__/                 # ⚠ GITIGNORED — regenerated automatically
```

### What a fresh `git clone` will be missing

Verified with `git ls-files`, `git check-ignore -v`, and `git status --untracked-files=all`:

| Path | Tracked? | Why it will be missing |
|------|----------|------------------------|
| `.env` | **No** | Explicitly ignored at `.gitignore:11`. **You must create this yourself** — copy the tracked `.env.example`. |
| `database/attendance.db` | **No** | Ignored by `*.db` at `.gitignore:14`. Auto-created by `create_tables()` on first run. |
| `__pycache__/` (all dirs) | **No** | Ignored at `.gitignore:2`. Regenerated on import. |
| `data/`, `data/faces/` | **No** | Not in `.gitignore`, but Git does not track empty directories. Will not appear. |
| `reports/` | **No** | Same reason — the directory is empty. |

`audio/*.mp3` and `models/*.onnx` **are** tracked, which is essential since the app cannot run without them.
`docs/architecture.svg` is tracked too, so the architecture diagram renders on a fresh clone.

---

## Setup Guide

### Prerequisites

- **Windows.** The code is not platform-agnostic: `admin/dashboard.py:267` calls `self.state("zoomed")` inside a
  `try` (it degrades gracefully), but the UI hardcodes the `"Segoe UI"` font in ~40 places and relies on the
  Windows shell for the `▣ ＋ ☷ ↳ ↲ ◈ ⟳ 🗑` glyphs. It is untested on macOS/Linux.
- **Python 3.10+.** Verified on **3.13.7**. `Image.Resampling.LANCZOS` (`enrollment/face_enrollment.py:1654`)
  requires Pillow ≥ 9.1. `FaceDetectorYN` / `FaceRecognizerSF` require OpenCV ≥ 4.5.4.
- **A webcam** at OS index 0. `CAMERA_ID = 0` is hardcoded in all three camera modules
  (`attendance/live_verification.py:17`, `enrollment/face_enrollment.py:28`, `ui/terminal.py:24`).
- **libstdc++ DLLs on Windows.** `opencv-python` (not `opencv-python-headless`) needs the MSVC runtime; the
  standard wheel normally pulls this in transitively.
- **A Gmail account with an App Password** — only if you want parent notifications.

### Install

```powershell
git clone https://github.com/emaanali-cs/FaceAttend.git
cd FaceAttend

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### Environment variables

A `.env.example` template is committed at the repo root. **Copy it to `.env` and fill in your own values** —
do not edit `.env.example` itself, since it is the shared, credential-free reference.

```powershell
# Windows (PowerShell or cmd)
copy .env.example .env
```

```bash
# macOS / Linux
cp .env.example .env
```

Then open `.env` and replace the four placeholder values:

```dotenv
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-16-character-app-password
```

The app **runs fine without a `.env`** — email is simply skipped with a
`False, "Sender email is not configured."` return (`email_service/email_manager.py:62-70`). Only parent
notifications require these values.

`SMTP_SERVER` and `SMTP_PORT` have code-level defaults (`email_service/email_manager.py:19-29`).
`SENDER_EMAIL` and `SENDER_PASSWORD` have **no defaults** and are read with `os.getenv(name)` only.

To generate a Gmail App Password: Google Account → Security → 2-Step Verification → App passwords. Use the
16-character app password, **not** your account password.

### Manually supplied assets

**None.** Both ONNX models and all four MP3 clips are committed to the repository. There is no
download step, no model registry, and no seeding script. This is unusual and worth calling out as a positive.

---

## Execution Guide

### Run the app

```powershell
python main.py
```

This is the only supported way to start the application. `main.py:11-17` calls `create_tables()` then enters
`mainloop()`. There are **no CLI flags, no argparse, and no environment toggles** anywhere in the project.

### Initial data setup

On a fresh clone the database is empty and check-in will fail with
`"No registered employees found."` (`attendance/live_verification.py:490-497`). You must enroll at least one
person first:

1. `python main.py`
2. Click **＋ Register Person** in the sidebar
3. Fill in ID / Name / Department, pick `Employee` or `Student`
4. Click **START FACE ENROLLMENT**
5. Follow the three on-screen + audible prompts: look straight → turn left → turn right
6. Click **DONE**

### Optional: create the database without the GUI

```powershell
python database/database.py
```

Verified output:

```
Database initialized successfully.
```

Safe to run repeatedly — every statement is `CREATE TABLE IF NOT EXISTS` or a guarded `ALTER TABLE`.

### The `test_*.py` scripts are **manual camera scripts, not automated tests**

There is **no pytest, no unittest, and no test runner of any kind** in this repository. Nothing asserts
anything; these scripts open your webcam, draw to a window, and block until you press a key.

| Script | Status | How to run | Exit condition |
|--------|--------|-----------|----------------|
| `test_audio.py` | **Verified working** — executed, exit code `0` | `python test_audio.py` | Automatic. Plays `look_center.mp3`, `time.sleep(5)`, then `audio.cleanup()`. Actual output: `Audio system initialized successfully.` / `Looking for audio file: ...\look_center.mp3` / `Playing: look_center.mp3` / `Test finished.` |
| `recognition/test_recognition.py` | Verified importable and working | `python -m recognition.test_recognition` | Press **`Q` or `q`** (`ord("q")`, `test_recognition.py:78`). Prints `Face feature generated: (1, 128)` per detected face. |
| `recognition/test_database_recognition.py` | Verified importable and working | `python -m recognition.test_database_recognition` | Press **`Q` or `q`** (`test_database_recognition.py:193`). Note it uses its **own** `MATCH_THRESHOLD = 0.40`, not the shared `0.55`. |
| `recognition/test_detection.py` | **BROKEN — verified `ImportError`** | n/a | Cannot run at all; see caveats. |

All camera scripts print `ERROR: Could not open camera.` and `return` cleanly if the webcam is unavailable
(`test_recognition.py:12-14`).

### Destructive maintenance script

```powershell
python database/cleanup_employee.py
```

**Read this before running it.** This file has **no `if __name__ == "__main__":` guard and no
`main()` function** — all of its code is at module scope (`cleanup_employee.py:8-66`). It prints every employee
and embedding, then `input()`s an employee ID and **immediately calls `delete_employee()` on it with no
confirmation and no dry-run** (`cleanup_employee.py:44-61`). Because of the missing guard, merely *importing*
this module triggers the prompt and the delete.

### Standalone attendance terminal

```powershell
python -m ui.terminal
```

Launches `AttendanceTerminal`, a second, fully-implemented check-in/check-out UI with an in-Tk camera preview.
It is **completely unreachable from `main.py`** — nothing imports it. Its **ADMIN DASHBOARD** button is broken
(see caveats).

---

## API Reference

This is a desktop application with **no HTTP/REST API, no server, and no network listener**. The consumable
interface is the Python module API, which is what an importer would use.

### `database.database` — the entire persistence layer

| Function | Signature | Returns | Notes |
|----------|-----------|---------|-------|
| `get_connection` | `()` | `sqlite3.Connection` | `PRAGMA foreign_keys = ON`; caller must `close()` |
| `create_tables` | `()` | `None` | Idempotent. Creates 3 tables + runs the additive migration |
| `employee_exists` | `(employee_code)` | `int \| None` | Returns the `id` if present |
| `add_employee` | `(employee_code, name, department, person_type="Employee", parent_email=None)` | `int` (new `id`) | Raises `ValueError("Employee/Student ID already exists.")` on `IntegrityError` |
| `get_employees` | `()` | `list[tuple]` | `(id, employee_code, name, department, created_at)`, newest first |
| `get_person_details` | `(employee_id)` | `tuple \| None` | `(id, employee_code, name, department, person_type, parent_email)` — **positional indices 1, 2, 4, 5 are load-bearing in the check-in flow** |
| `delete_employee` | `(employee_id)` | `None` | Cascades to embeddings + attendance |
| `save_embedding` | `(employee_id, pose, embedding)` | `None` | `embedding` is a `pickle` **BLOB** |
| `get_face_embeddings` | `()` | `list[tuple]` | `(employee_id, employee_code, name, department, pose, embedding_blob)` — inner join, so people with no embeddings are excluded |
| `employee_has_face_embeddings` | `(employee_id)` | `bool` | **Currently unused anywhere** |
| `get_today_attendance` | `(employee_id)` | `tuple \| None` | **Currently unused anywhere** |
| `mark_check_in` | `(employee_id)` | `(bool, str)` | `(True, "HH:MM:SS")` or `(False, reason)`. Rejects if no record exists today |
| `mark_check_out` | `(employee_id)` | `(bool, str)` | `(True, "HH:MM:SS")` or `(False, reason)`. Rejects if not checked in, or already checked out |
| `get_attendance_records` | `()` | `list[tuple]` | **Currently unused anywhere** |
| `get_today_attendance_records` | `()` | `list[tuple]` | **Currently unused anywhere** |

All SQL is parameterized with `?` placeholders — no string interpolation into queries.

### `recognition.face_recognition`

| Symbol | Signature | Notes |
|--------|-----------|-------|
| `FaceSystem` | `FaceSystem()` | Raises `FileNotFoundError` if either ONNX model is missing. Builds `cv2.FaceDetectorYN` (320×320 input, 0.80 conf, 0.3 NMS, 5000 top-K) and `cv2.FaceRecognizerSF` |
| `.detect` | `(frame) -> list` | Filters on `MIN_FACE_WIDTH/HEIGHT = 80` and `DETECTION_CONFIDENCE = 0.80` |
| `.get_feature` | `(frame, face) -> np.ndarray` | `alignCrop` then `feature`; returns a `(1, 128)` float array |
| `.compare` | `(feature1, feature2) -> float` | Cosine similarity, higher is better |
| `load_registered_faces` | `() -> list[dict]` | `pickle.loads` each blob; **silently `continue`s** past any blob that fails to deserialize |
| `recognize_face` | `(face_system, live_feature, registered_faces) -> (dict \| None, float)` | Best-score-wins; returns `(None, score)` below `MATCH_THRESHOLD = 0.55` |
| `draw_face` | `(frame, face, color=(0,255,0)) -> frame` | **Currently unused anywhere** |

### `attendance.live_verification`

| Symbol | Signature | Notes |
|--------|-----------|-------|
| `run_live_verification` | `(mode="CHECK-IN") -> dict` | Returns `{"success": bool, "reason": str, "person": dict \| None}`. Blocks until pass / fail / timeout / `Q` |
| `get_head_direction` | `(face) -> "CENTER" \| "LEFT" \| "RIGHT" \| "UNKNOWN"` | Uses landmarks `face[4..9]` |
| `get_stable_value` | `(history, value, max_length) -> value \| None` | Returns the value only if the last `max_length` entries are all identical |

### `email_service.email_manager`

`send_attendance_email(student_name, student_code, parent_email, attendance_type, attendance_time) -> (bool, str)`

`attendance_type` must be `"CHECK-IN"` or `"CHECK-OUT"` (case-insensitive); anything else returns
`(False, "Invalid attendance type.")`. This function is only ever called for students.

---

## Configuration

There is **no configuration file and no `config/settings.py` content** — `config/settings.py` is a 0-byte file
that no module imports. All configuration is hardcoded module-level constants. There is no CLI flag parsing and
no config loader.

### Environment variables (the only external configuration)

| Variable | Read at | Default | Purpose |
|----------|---------|---------|---------|
| `SMTP_SERVER` | `email_service/email_manager.py:19-22` | `smtp.gmail.com` | SMTP host |
| `SMTP_PORT` | `email_service/email_manager.py:24-29` | `587` | Cast with `int()`, so a non-numeric value raises `ValueError` at import time |
| `SENDER_EMAIL` | `email_service/email_manager.py:31-33` | **none** | `From` address and SMTP login user |
| `SENDER_PASSWORD` | `email_service/email_manager.py:35-37` | **none** | SMTP login password / app password |

All four are read **exactly once, at module import time**, via `load_dotenv()` (`email_service/email_manager.py:12`).

### Hardcoded tunables

**Recognition thresholds** — `recognition/face_recognition.py:29-34`

| Constant | Value | Effect |
|----------|-------|--------|
| `DETECTION_CONFIDENCE` | `0.80` | YuNet score floor; also a second filter in `detect()` |
| `MIN_FACE_WIDTH` / `MIN_FACE_HEIGHT` | `80` / `80` | Rejects small/ distant faces |
| `MATCH_THRESHOLD` | `0.55` | Minimum cosine score to accept an identity |

**Liveness challenge** — `attendance/live_verification.py:17-53`

| Constant | Value | Effect |
|----------|-------|--------|
| `CAMERA_ID` | `0` | Hardcoded webcam index |
| `CAMERA_WIDTH` / `CAMERA_HEIGHT` | `1280` / `720` | Requested capture size |
| `DISPLAY_WIDTH` / `DISPLAY_HEIGHT` | `1200` / `675` | Fixed 16:9 display size |
| `MATCH_THRESHOLD` | `0.55` | **Duplicate** of the value in `recognition/face_recognition.py` — two independent copies |
| `POSE_STABLE_TIME` | `0.8` s | How long each pose must be held |
| `YAW_THRESHOLD` | `0.18` | Head-turn sensitivity |
| `CHALLENGE_TIME_LIMIT` | `15` s | Timeout, armed only after first recognition |
| `RECOGNITION_STABILITY_FRAMES` | `5` | Frames the same identity must persist |
| `DIRECTION_STABILITY_FRAMES` | `5` | Frames the same head direction must persist |

**Enrollment** — `enrollment/face_enrollment.py:28-32`: `CAMERA_ID = 0`, `CAMERA_WIDTH = 640`,
`CAMERA_HEIGHT = 480`, `POSE_STABLE_TIME = 0.8`, `YAW_THRESHOLD = 0.18`. Note the enrollment capture resolution
(640×480) is **half** the live-verification resolution (1280×720).

**Standalone terminal** — `ui/terminal.py:24-29`: `CAMERA_ID = 0`, `MATCH_THRESHOLD = 0.55` (a *third* copy),
`SUCCESS_DISPLAY_TIME = 3000` ms.

### Declared but never read or used

| Symbol | Location | Status |
|--------|----------|--------|
| `config/settings.py` | `config/settings.py` | **0 bytes.** Importable only as a PEP 420 namespace package; imported by nothing |
| `AudioManager.play_center` | `audio/audio_manager.py:56` | Never called — `face_enrollment.py` calls `audio.play("look_center.mp3")` instead |
| `AudioManager.play_left` | `audio/audio_manager.py:66` | Never called |
| `AudioManager.play_right` | `audio/audio_manager.py:76` | Never called |
| `AudioManager.play_registration_complete` | `audio/audio_manager.py:86` | Never called |
| `get_employees` | `database/database.py:241` | Only used by `cleanup_employee.py`, not by the app |
| `employee_has_face_embeddings` | `database/database.py:386` | **Never called anywhere** |
| `get_today_attendance` | `database/database.py:411` | **Never called anywhere** |
| `get_attendance_records` | `database/database.py:644` | **Never called anywhere** |
| `get_today_attendance_records` | `database/database.py:692` | **Never called anywhere** — `admin/dashboard.py` runs its own inline SQL instead |
| `draw_face` (module-level) | `recognition/face_recognition.py:261` | **Never imported**; the two same-named methods on the UI classes are unrelated |
| `attendance.status` column | `database/database.py:138` | Always written as the literal `"Present"`; no code path ever produces `Absent`, `Late`, etc. |
| `audio/` as a package | — | Has **no `__init__.py`**; works only via PEP 420 namespace packages (verified) |

---

## Security Notes

**Read this section before deploying or sharing this repository.**

### 1. CRITICAL — a live Gmail app password is sitting in plaintext on disk

The repo's local `.env` contains a real Gmail account and a real 16-character Google App Password. The values
are **deliberately redacted here** — reproducing a live credential in a README is exactly the mistake this
finding is about, and this file is the one most likely to be copied, forked, or pasted into an issue. Open
`.env` locally to see them, and treat whatever is there as compromised:

```dotenv
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=<redacted — real @gmail.com address>
SENDER_PASSWORD=<redacted — 16-char Google App Password>
```

`SENDER_PASSWORD` is in the 16-character Google App Password format that Gmail issues for app credentials, so
it is almost certainly **live**.

**Good news, verified:** this file is **not** in git. It is ignored at `.gitignore:11`, it is absent from
`git ls-files`, and `git log --all -- .env` returns nothing. I also grepped **every blob in every commit**
(`git rev-list --all` + `git grep` for the literal password, the sender address, and `SENDER_PASSWORD=`) and
found **zero matches**. The secret has never entered the repository's history, and the remote
(`https://github.com/emaanali-cs/FaceAttend.git`) is clean. The working tree is also clean per
`git status --untracked-files=all`.

**But the exposure is still real and needs action:**

- **Recommendation: rotate it now.** Go to Google Account → Security → App passwords, revoke the existing
  app password, and generate a new one. Revocation is the only reliable fix — the value is already on disk in
  plaintext and should be considered compromised regardless of git hygiene.
- Copy `.env.example` to `.env` and put the **newly generated** value in it. Do not restore the old one.
- The repository is **public** on GitHub. `.gitignore` protecting a file is a safety net, not a control. If this
  project is ever forked, `git add -f .env`, or the `.gitignore` line is removed, the credential publishes
  silently.
- **Hardening already in place:** a credential-free `.env.example` template is committed at the repo root, and
  the Setup Guide now documents both the `cp`/`copy` step and an explicit "never commit or force-add `.env`"
  warning. Remaining gap: there is still no `CONTRIBUTING.md` codifying the rule, and no pre-commit hook to
  enforce it.

### 2. HIGH — `pickle.loads` on data from the database

`recognition/face_recognition.py:195` calls `pickle.loads(embedding_data)` on every row returned by
`get_face_embeddings()`. `unpickling` untrusted data is a documented arbitrary-code-execution vector.

The application currently only ever writes pickles it produced itself from `numpy` arrays
(`enrollment/face_enrollment.py:1320`), so this is safe **as long as `attendance.db` is trusted**. The risk is
that the database file is unencrypted, unauthenticated, and freely copyable — anyone who can write to it (a
malicious colleague, a shared network drive, a restored backup, a swapped USB stick) achieves code execution the
next time anyone runs a check-in.

Mitigations worth considering: store embeddings as raw `float32` bytes in a `BLOB` and `np.frombuffer` them
instead of pickling (this removes `pickle` entirely and shrinks the rows), or at minimum wrap the `loads` in
`pickle.Unpickler` subclass checks. Note the existing `except Exception: continue` at
`recognition/face_recognition.py:199-201` means a tampered row is **silently skipped**, so a malicious payload
would fail loudly only if the pickle itself is malformed.

### 3. HIGH — no authentication or authorization anywhere

There is no login, no password, no role system, and no session concept in the entire codebase. The sidebar
"Delete Person" button (`admin/dashboard.py:1314-1317`) will delete any person, along with their embeddings and
their entire attendance history, for **anyone who can open the application**. The only safeguard is a
`askyesno` confirmation dialog (`admin/dashboard.py:1613-1624`).

`dashboard.py:557` renders the footer text *"Local Database • Secure Access"*. That is a UI label, not a security
control, and it is misleading. Do not run this on a shared or multi-user machine.

### 4. MEDIUM — biometric data is stored unencrypted

Face embeddings are 128-D vectors that are effectively a biometric template. They are stored as raw BLOBs in an
unencrypted SQLite file, and the DB is deliberately gitignored — but `.gitignore` does not protect a file that
has already been copied, backed up to a cloud drive, or restored from a backup. There is no at-rest encryption
and no access control on the file.

### 5. LOW — positive findings worth keeping

- **All SQL is parameterized.** Every query in `database/database.py` and `admin/dashboard.py` uses `?`
  placeholders. No string interpolation into SQL anywhere. No injection surface found.
- **No command injection.** `launch_module` (`admin/dashboard.py:218-229`) passes module names to
  `subprocess.Popen` as a **list** (not `shell=True`), and the only arguments are hardcoded literals
  (`"attendance.checkin"`, `"attendance.checkout"`). There is no user-controlled path into it.
- **No embedded credentials in tracked source.** The only occurrence of `SENDER_PASSWORD` in any `.py` file is
  `email_service/email_manager.py:35-37`, and it is an `os.getenv` lookup.
- **No URLs with embedded credentials.** Grepped for `scheme://user:pass@host` across the tree: no matches.
- **Email is student-gated**, so an employee record can never trigger an outbound message
  (`attendance/checkin.py:81-85`).
- Email send failures are caught and returned, never raised into the UI (`email_service/email_manager.py:176-185`).

---

## Known Issues and Caveats

### Verified by reading source and confirmed by execution

These I reproduced or proved by running code.

Issues 2, 3, 4 and 5 are the ones the [detailed architecture diagram](docs/architecture-detailed.svg)
plots explicitly as red dashed edges and red-outlined nodes — it is the quickest way to see how the dead
and broken paths connect to the rest of the system.

| # | Severity | Issue |
|---|----------|-------|
| 1 | **Critical** | Live Gmail app password in plaintext `.env` on disk. Not in git, never in history — but **rotate it anyway**. See [Security Notes](#1-critical--a-live-gmail-app-password-is-sitting-in-plaintext-on-disk) |
| 2 | **Broken** | `recognition/test_detection.py:3` imports `FaceDetector, draw_faces` from `recognition.face_recognition`, but that module only defines `FaceSystem` and `draw_face`. Reproduced: `ImportError: cannot import name 'FaceDetector' from 'recognition.face_recognition'`. **This script cannot run at all.** It is dead code from a refactor that renamed the class |
| 3 | **Broken** | `ui/terminal.py:1495-1499` `open_admin()` does `from admin.dashboard import AdminDashboard`, but `admin/dashboard.py:247` defines the class as `Dashboard`. Reproduced: `ImportError: cannot import name 'AdminDashboard' from 'admin.dashboard'`. The error is caught at `ui/terminal.py:1505` and shown as a messagebox, so the **ADMIN DASHBOARD button in the standalone terminal never works**. Compounding bug: even if the name were fixed, `Dashboard` subclasses `tk.Tk`, not `tk.Toplevel`, so `AdminDashboard(self)` would be an invalid master |
| 4 | **Dead code** | `ui/terminal.py` (1,533 lines) is **imported by nothing**. It is a complete, functional second attendance UI that is unreachable from `main.py` and undocumented in the UI. Either wire it up or delete it |
| 5 | **Destructive** | `database/cleanup_employee.py` runs at **module scope with no `__main__` guard** and **deletes the entered employee ID with no confirmation** (`cleanup_employee.py:44-61`). Merely importing it triggers a delete |
| 6 | **Design** | The liveness challenge is a **head-pose challenge, not a true anti-spoofing check**. A printed photo held at the right angles, or a short video played on a second screen, would likely pass. The code contains no depth, texture, or blink/replay detection. `CHALLENGE_TIME_LIMIT` only starts *after* a face is recognized (`attendance/live_verification.py:745-749`), so there is no cap on how long an unrecognized person can hold the camera |
| 7 | **Consistency** | `MATCH_THRESHOLD` is **duplicated in three places** with no single source of truth: `recognition/face_recognition.py:34` (`0.55`), `attendance/live_verification.py:39` (`0.55`), `ui/terminal.py:26` (`0.55`). A fourth override exists at `recognition/test_database_recognition.py:16` (`0.40`) |
| 8 | **Consistency** | `get_head_direction` is **duplicated verbatim** in `attendance/live_verification.py:135-190` and `enrollment/face_enrollment.py:54-92`. The enrollment copy has no `try/except`, so a malformed landmark array raises an uncaught `IndexError` |
| 9 | **Fragile** | `admin/dashboard.py:44-56` opens a **second, independent** `sqlite3` connection with a duplicate `get_connection()` rather than reusing `database.database.get_connection()`. The two can drift |
| 10 | **Silent failure** | `recognition/face_recognition.py:199-201` swallows any exception from `pickle.loads` and `continue`s. A corrupted or tampered embedding row makes a person silently unrecognizable, with no log line and no UI warning |
| 11 | **Inert column** | `attendance.status` always receives the literal `"Present"` (`database/database.py:541`). No code path ever writes `Absent`, `Late`, or `Half Day`. The dashboard's STATUS column is therefore always "Present" |
| 12 | **Hardcoded index** | `CAMERA_ID = 0` in all three camera modules. Systems with an integrated + external camera may bind the wrong one. There is no device picker and no override |
| 13 | **Likely no-op** | `attendance/live_verification.py:517-520` sets `cv2.CAP_PROP_BUFFERSIZE`, which the MSMF/DShow backends on Windows generally ignore (it is a GStreamer/FFmpeg property). The intent — reduce frame latency — probably is not achieved |
| 14 | **No-op config** | `config/settings.py` is a 0-byte file imported by nothing; `audio/`, `config/`, `database/`, and `models/` all lack `__init__.py` and rely on PEP 420 namespace packages. This works on Python 3.3+ but is fragile under some packaging tools and test runners |
| 15 | **No tests** | Zero automated tests. No `pytest`, no `unittest`, no CI, no linter config. Nothing prevents regressions in the thresholds, and the two `ImportError`s above sat undetected |
| 16 | **No error surfacing** | `admin/dashboard.py:1204-1209` catches dashboard DB errors and only `print`s them. A user staring at stale cards gets no indication anything is wrong |
| 17 | **Portability** | Windows-only in practice: `state("zoomed")` (`admin/dashboard.py:267`), the hardcoded `"Segoe UI"` font throughout, and the reliance on Windows console glyphs for sidebar icons |
| 18 | **WAL absent** | `get_connection()` sets `foreign_keys` but never `journal_mode=WAL`. Concurrent dashboard reads during a check-in write can hit `database is locked` |
| 19 | **Unpinned deps** | `requirements.txt` has **no version constraints at all**. YuNet/SFace APIs moved around across OpenCV 4.x/5.x, so an unpinned install can break recognition in a way that is hard to diagnose |
| 20 | **Repo weight** | 37.1 MB of ONNX weights committed to git history. Cloning is slow, and the weights can never be updated without permanently growing the repository |

### Unverified / flagged assumptions

I could not test these without physical hardware or a live account. Treat them as open questions.

- **Webcam behaviour is untested.** No camera was available here. Capture resolution negotiation, whether
  `cv2.CAP_PROP_FRAME_WIDTH/HEIGHT = 1280x720` is honoured, and mirror/latency feel are all unconfirmed.
  The enrollment path deliberately requests only 640×480.
- **Recognition accuracy is unmeasured.** `0.55` cosine on SFace is a plausible default but I have no false-accept
  and false-reject rates for it. The stability-window logic (`RECOGNITION_STABILITY_FRAMES = 5`) means effective
  throughput depends on frame rate, which depends on the camera and lighting.
- **The head-pose challenge is unvalidated against spoofing.** Issue 6 above is inferred from reading the code —
  there is no liveness-presence signal of any kind. I did not attempt an actual spoof attack.
- **SMTP delivery is untested.** I did not send a message. Gmail App Password auth, STARTTLS negotiation
  (`email_service/email_manager.py:156`), and Gmail's 500/day sending cap are all assumed to work. The Gmail
  `From` header will also show as the raw address rather than a display name.
- **Multi-user / concurrent operation is untested.** One operator process at a time is assumed. Nothing prevents
  two check-in windows from racing on the same person; the `UNIQUE(employee_id, attendance_date)` constraint
  will reject the second, which is correct, but the error surfaces as a generic warning.
- **The committed `models/*.onnx` provenance is unverified.** Filenames follow the OpenCV model-zoo convention,
  and both load successfully with the installed OpenCV 5.0.0. I could not confirm they are unmodified upstream
  artifacts or check their licenses.
- **`data/faces/` and `reports/` are empty.** Neither is referenced by any code. They look like scaffolding for
  a planned face-image export and a reporting feature that were never built. I could not determine intent, so
  I have not claimed them as features.

---

## Contributing

There is **no `CONTRIBUTING.md`**. If you want to start one, these are the gaps I would put at the top of it:

1. **Pin your dependencies.** `requirements.txt` with no version constraints is the single highest-value fix.
2. **Add real tests.** The `test_*.py` scripts are interactive camera demos with side effects; rename them
   (e.g. `tools/`) and add pytest unit tests for the pure functions in `database/database.py` and the head-pose
   math, which need no camera.
3. **Fix the two `ImportError`s** (issues 2 and 3 above) and either wire `ui/terminal.py` into `main.py` or
   delete it.
4. **De-duplicate the constants** — `MATCH_THRESHOLD` ×3, `get_head_direction` ×2, `get_connection` ×2.
5. **Codify the `.env` rule.** A credential-free `.env.example` is now committed and the Setup Guide warns
   against force-adding `.env`. Next: a `CONTRIBUTING.md` line and a pre-commit hook so the rule is enforced
   rather than just documented.
6. **Add a linter** (`ruff` or `flake8`) — the codebase follows a consistent style that a config would lock in.
7. **Add a `.gitattributes`.** Git warns that `LF` will become `CRLF` on checkout for both new files; pinning
   line endings would remove that noise for contributors on all platforms.
8. **Confirm the ONNX model terms** separately from the MIT grant — see [License](#license).

---

## License

**MIT License — Copyright (c) 2026 Emaan Ali.** The full text is in [`LICENSE`](LICENSE), added in commit
`f9652f8`.

```
MIT License

Copyright (c) 2026 Emaan Ali

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

In short: you may use, modify, and redistribute this code, including commercially, provided the copyright
notice and permission notice are retained.

### One caveat worth knowing

The MIT license covers **this project's source code only**. The two bundled ONNX model files —
`models/face_detection_yunet_2026may.onnx` and `models/face_recognition_sface_2021dec.onnx` — are third-party
artifacts from the OpenCV model zoo, redistributed here under separate terms that the project's own license
does not change. **I could not verify their upstream licensing.** If you plan to redistribute this repo
commercially or in a product you ship, check the OpenCV model-zoo terms for those two files separately.
