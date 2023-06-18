import simpleaudio as sa
import sys

path = sys.argv[1]
wav = sa.WaveObject.from_wave_file(path)
play_obj = wav.play()
play_obj.wait_done()

