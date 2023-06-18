import threading
import wave
import simpleaudio as sa
import sys
import os
import signal
import pydub

from components.music import play_music
from components.wav_to_pcm import wav2pcm
from components.SR import Sr
from components.TTS import Tts
from flask import Flask, request
import re
import proj_utils
from program import func_wine_introduce, func_hint, func_receptionist
from program import func_weather_reporter
from program import func_ertertianment_introduce
import subprocess
import requests
from test_timer import test

play_flag = 0
app = Flask(__name__)
@app.route('/stt', methods=['POST'])
def stt():
    if request.headers['Content-Type'] == 'audio/wav':
        audio_data = request.data

        with wave.open(proj_utils.RHASSPY_RECV_WAV_FILEPATH, 'wb') as wav_file:
            wav_file.setnchannels(1)  # 单声道
            wav_file.setsampwidth(2)  # 16-bit 样本宽度
            wav_file.setframerate(16000)  # 采样率为 16000Hz
            wav_file.writeframes(audio_data)
            print("wav file saved")

        wav2pcm(src_path=proj_utils.RHASSPY_RECV_WAV_FILEPATH,
                des_path=proj_utils.RHASSPY_RECV_PCM_FILEPATH)

        t = Sr(tid="main.py sr", file=proj_utils.RHASSPY_RECV_PCM_FILEPATH)
        t.start()
        t.wait()

        # 获取用户语音识别的结果
        order = t.msg['payload']['result']


        # url = "http://10.22.120.71:12101/api/events/intent"  # 替换为实际的目标 URL
        url = "http://192.168.43.50:12101/api/events/intent"  # 替换为实际的目标 URL

        headers = {
            'Content-Type': 'text/plain'
        }   
        if dispatch(order):
            data = "recognition successful"
            requests.post(url, headers=headers, data=data)
        else:
            deta = "recognition failed"
            requests.post(url, headers=headers, data=data)


    else:
        return "Content-Type is not audio/wav"
    return "return something"


def tts(text):
    Tts('start text to speech', file=proj_utils.TTS_WAV_FILEPATH).start(text)

def dispatch(order):
    import time
    global play_flag
    file = "/home/hi/hi/test/"
    # pid = os.fork()
    # if pid == 0:
    #     play_audio(file)
    # else:
    if play_flag == 0:
        th = threading.Thread(target=play_audio, args=(file+"this.wav", ))
        th.start()
    else:
        th = threading.Thread(target=play_audio, args=(file+"that.wav", ))
        th.start()
    time.sleep(10)
    print("pause pid: ")
    play_flag = 0
    time.sleep(5)
    print("start pid: ")
    play_flag = 1
    return True

def play_audio(audio_path):
    import wave
    import pyaudio
    global play_flag
    CHUNK = 1024
    wf = wave.open(audio_path, 'rb')
    p = pyaudio.PyAudio()
    try:
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                    output_device_index=2)
        print("start music")
        play_flag = 1
        data = wf.readframes(CHUNK)
        while data:
            if play_flag == 1:
                stream.write(data)
                data = wf.readframes(CHUNK)

        print("end music")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

def play_wav_file(file_path):
    # 使用aplay命令播放wav文件
    subprocess.run(["aplay", "-D", "plughw:3,0", file_path])
    # subprocess.run(["ls", "-la"])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
