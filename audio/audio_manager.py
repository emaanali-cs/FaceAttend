import pygame
from pathlib import Path


# ============================================================
# AUDIO DIRECTORY
# ============================================================

AUDIO_DIR = Path(__file__).resolve().parent


# ============================================================
# AUDIO FILE NAMES
# ============================================================

LOOK_CENTER_AUDIO = "look_center.mp3"
LOOK_LEFT_AUDIO = "look_left.mp3"
LOOK_RIGHT_AUDIO = "look_right.mp3"
REGISTRATION_COMPLETE_AUDIO = "registration_complete.mp3"


# ============================================================
# AUDIO MANAGER
# ============================================================

class AudioManager:

    def __init__(self):

        self.enabled = False

        try:

            pygame.mixer.pre_init(
                frequency=44100,
                size=-16,
                channels=2,
                buffer=512
            )

            pygame.mixer.init()

            self.enabled = True

            print("Audio system initialized successfully.")

        except Exception as error:

            print("Audio initialization failed:")
            print(error)

    # ========================================================
    # PLAY CENTER
    # ========================================================

    def play_center(self):

        self.play(
            LOOK_CENTER_AUDIO
        )

    # ========================================================
    # PLAY LEFT
    # ========================================================

    def play_left(self):

        self.play(
            LOOK_LEFT_AUDIO
        )

    # ========================================================
    # PLAY RIGHT
    # ========================================================

    def play_right(self):

        self.play(
            LOOK_RIGHT_AUDIO
        )

    # ========================================================
    # PLAY REGISTRATION COMPLETE
    # ========================================================

    def play_registration_complete(self):

        self.play(
            REGISTRATION_COMPLETE_AUDIO
        )

    # ========================================================
    # PLAY AUDIO
    # ========================================================

    def play(self, filename):

        if not self.enabled:

            print(
                "Audio is disabled because "
                "pygame mixer was not initialized."
            )

            return

        audio_file = AUDIO_DIR / filename

        print(
            f"Looking for audio file:\n"
            f"{audio_file}"
        )

        if not audio_file.exists():

            print(
                f"ERROR: Audio file does not exist:\n"
                f"{audio_file}"
            )

            return

        try:

            pygame.mixer.music.stop()

            pygame.mixer.music.load(
                str(audio_file)
            )

            pygame.mixer.music.play()

            print(
                f"Playing: {audio_file.name}"
            )

        except Exception as error:

            print(
                f"ERROR playing "
                f"{audio_file.name}:"
            )

            print(error)

    # ========================================================
    # STOP AUDIO
    # ========================================================

    def stop(self):

        if not self.enabled:
            return

        try:

            pygame.mixer.music.stop()

        except Exception:
            pass

    # ========================================================
    # CLEANUP
    # ========================================================

    def cleanup(self):

        self.stop()

        if self.enabled:

            try:

                pygame.mixer.quit()

            except Exception:
                pass

            self.enabled = False