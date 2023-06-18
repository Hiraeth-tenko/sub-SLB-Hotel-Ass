import threading
import wave

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
stream_flag = 0
app = Flask(__name__)

#print("play_obj", play_obj)
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
    patterns = []
    # 识别句子中，是否同时出现了’查询‘和’天气‘
    patterns.append(r'(?=.*查询)(?=.*天气)')

    # 识别句子中，是否出现了‘介绍’
    patterns.append(r'介绍(.+)')

    # 识别句子中的时间，例如：；请在八点四十七叫醒我’，提取出句中的’八点四十七‘
    patterns.append(r"请在(\S+)叫醒我")

    # 识别句子中，是否出现了‘指令’
    patterns.append("指令")

    # 识别句子中，是否出现了‘娱乐设施’或‘酒水’或‘呼唤人工’
    patterns.append(r"(娱乐设施|酒水|人工)")
    
    # 识别句子中，是否出现了‘播放音乐’
    patterns.append("播放音乐")
    
    # 暂停
    patterns.append(r"暂停")
    # 查询天气
    if re.search(patterns[0], order):
        func_weather_reporter(order)
        play_wav_file(proj_utils.WEATHER_TTS_WAV_FILEPATH)
        return True

    # 介绍娱乐设施或酒水
    elif re.search(patterns[1], order):
        # 介绍酒水
        if func_wine_introduce(order):
            play_wav_file(proj_utils.WINE_TTS_WAV_FILEPATH)
            return True

        # 介绍娱乐设施
        elif func_ertertianment_introduce(order):
            play_wav_file(proj_utils.ENTERTAINMENT_TTS_WAV_FILEPATH)
            return True

    elif re.search(patterns[2], order):
        # 在句子中查找匹配
        match = re.search(patterns[2], order)
        time = match.group(1)  # 获取匹配到的时间
        # 创建子线程
        thread = threading.Thread(target=thread_function(time))
        # 启动子线程
        thread.start()

    elif re.search(patterns[3], order):
        func_hint()
        play_wav_file(proj_utils.RECE_TTS_WAV_FILEPATH)
        return True

    elif re.search(patterns[4], order):
        func_receptionist(order)
        play_wav_file(proj_utils.RECE_TTS_WAV_FILEPATH)
        return True

    elif re.search(patterns[5], order):
        print("play audio")
        file_path =  play_music(order)
        play_audio(file_path)
        return True

    elif re.search(patterns[6], order):
        print("pause audio")
        pause_audio()
        return True

    else:
        sentence = "抱歉，我没有听清楚您说的话,能否再说一遍？"
        t = Tts('start text to speech', file=proj_utils.TTS_WAV_FILEPATH)
        t.start(sentence)
        t.wait()
        play_wav_file(proj_utils.TTS_WAV_FILEPATH)
        return False

def pause_audio():
    global play_flag
    play_flag = 0

def play_audio(audio_path):
    import wave
    import pyaudio
    global play_flag
    global stream_flag
    if play_flag == 0 and stream_flag == 1:# 暂停状态
        # 11 是播放状态
        # 01 是暂停状态
        # 10 是非预想状态
        # 00 是没有音频在播放
        play_flag = 1
        return
    if play_flag == 1 and stream_flag == 1:
        return 
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
        stream_flag = 1
        data = wf.readframes(CHUNK)
        while data:
            if play_flag == 1:
                stream.write(data)
                data = wf.readframes(CHUNK)

    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        play_flag = 0
        stream_flag = 0
        print("end music")

def play_wav_file(file_path):
    # 使用aplay命令播放wav文件
    subprocess.run(["aplay", "-D", "plughw:3,0", file_path])
    # subprocess.run(["ls", "-la"])

def thread_function(time):
    test(time)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
