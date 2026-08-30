from audio.audio_manager import AudioManager
import time


audio = AudioManager()

audio.play("look_center.mp3")

print("Waiting for audio...")
time.sleep(5)

audio.cleanup()

print("Test finished.")