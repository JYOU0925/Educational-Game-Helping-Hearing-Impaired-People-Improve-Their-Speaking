from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin
import queue
import threading
import numpy as np
import wave
import struct
from nltk.tokenize import SyllableTokenizer
from nltk import word_tokenize
import string
from gtts import gTTS
# import pygame
import os
import librosa
import librosa.display
import json
import sys


app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# 自定义函数将字符串矩阵转换为包含音节的数组
def convert_to_syllable_array(matrix_list):
    syllable_array = []
    for matrix in matrix_list:
        syllables = ["".join(row) for row in matrix]
        syllable_array.extend(syllables)
    return syllable_array

# 去除标点符号
def remove_punctuation(text):
    translator = str.maketrans("", "", string.punctuation)
    return text.translate(translator)

# 音调轮廓
def extract_pitch_contour(audio_file, num_syllables):
    print("before loading in librosa", file=sys.stdout)
    
    # 加载音频文件并提取音调信息
    waveform, sample_rate = librosa.load(audio_file)
    

    print("librosa got basic info 1", file=sys.stdout)
    pitches, magnitudes = librosa.piptrack(y=waveform, sr=sample_rate)
    

    print("librosa got basic info 2", file=sys.stdout)
    duration = librosa.get_duration(y=waveform, sr=sample_rate)# 获得音频总时长

    print("librosa got basic info", file=sys.stdout)
    
    # 音频总时长/音节个数 = 一个音节的时长
    syllable_duration = duration/num_syllables 

    # 生成时间戳数组
    timestamps = np.arange(0, num_syllables * syllable_duration, syllable_duration)

    average_pitches = []
    for i in range(len(timestamps)):
        pitch_values = pitches[:, i]
        average_pitch = pitch_values.mean()
        average_pitches.append(average_pitch)

    # 根据时间段和音高创建音节到音高的映射关系
    timestamps = timestamps.tolist()
    syllable_pitches = dict(zip(timestamps, average_pitches))

    print("before return from librosa job", file=sys.stdout)
    
    return syllable_pitches, syllable_duration

@app.route('/', methods=['POST'])
@cross_origin(origin='*')
def process_text():

    data = request.get_json()
    
    print(data)

    text = data['text']
    rate = data['rate']
    
    print("Get input {}".format(text), file=sys.stdout)
    print("type of rate: {}".format(type(rate)))

    if text:
        # 分割音节
        ssp = SyllableTokenizer()
        text_without_punctuation = remove_punctuation(text)
        syllables = [ssp.tokenize(token) for token in word_tokenize(text_without_punctuation)]
        syllable_array = convert_to_syllable_array(syllables)

        # 一共有几个音节
        num_syllables = len(syllable_array)

        print("Number of syllables {0}".format(num_syllables), file=sys.stdout)

        # 创建gTTS对象并将文本转换为语音
        tts = gTTS(text=text, lang='en', slow=rate)  # lang='en'表示将文本转换为英语语音
        tts.save("temp.mp3")  # 临时保存为MP3文件

        # # 使用pygame播放临时音频文件，确保音频文件被正确生成
        # pygame.mixer.init()
        # pygame.mixer.music.load("temp.mp3")

        # 重命名临时文件为目标输出文件
        if os.path.exists("output.mp3"):
            os.remove("output.mp3")

        print("Saving to mp3", file=sys.stdout)

        os.rename("temp.mp3", "output.mp3")

        print("Saved to mp3", file=sys.stdout)

        # 
        syllable_pitches, syllable_duration = extract_pitch_contour('output.mp3', num_syllables)

        syllable_pitches = {float(key): float(value) for key, value in syllable_pitches.items()}

        print("Constructing response", file=sys.stdout)
        
        response_dict = {
            'syllables': syllable_array,# 音节列表
            'syllable_pitches': syllable_pitches,# 音调
            # 音节和音调高低的匹配
        }
        
        print("Before writing to file", file=sys.stdout)

        # Write the JSON data to output.txt
        with open('output.txt', 'w') as output_file:
            print("Writing to file", file=sys.stdout)
            json.dump(response_dict, output_file)

        # print("Before returning " + jsonify(response))
        
        # return jsonify(response_dict)
    
        response = make_response(
            jsonify(
                response_dict,
                200,
            )
        )
        response.headers["Content-Type"] = "application/json"
        response.headers["Acces-Control-Allow-Origin"] = "*"
        return response

    return 'welcome'

# 创建一个队列来存储接收到的音频数据
audio_data_queue = queue.Queue()

# 处理从前端接收到的音频数据的函数
def process_audio_data():
    global audio_data_queue
    global syllable_duration

    while True:
        if not audio_data_queue.empty():
            # 在这里处理音频数据并计算平均音调
            audio_data = np.array(audio_data_queue.queue).flatten()
            if len(audio_data) > 0:
                avg_pitch = np.mean(audio_data)
                print("平均音调：", avg_pitch)
                # 将音频数据保存为一个wave文件
                save_wave_file(audio_data, "recorded_audio.wav")
                # 在处理后清空队列
                audio_data_queue.queue.clear()

# 启动音频数据处理线程
audio_processing_thread = threading.Thread(target=process_audio_data)
audio_processing_thread.daemon = True
audio_processing_thread.start()

# 路由用于接收前端传来的音频数据并将其保存到队列中
@app.route('/process_audio', methods=['POST'])
def process_audio():
    data = request.get_json()
    audio_data = data.get('audioData')
    if audio_data:
        # 计算平均音调并将音频数据保存到队列中
        audio_data_queue.put(audio_data)
        response = {
            'message': '音频数据接收并成功处理。',
            'syllables': 1 # 音节列表
            # 音节和音调高低的匹配
        }
        
        return jsonify(response)
    else:
        return jsonify({'message': '未接收到音频数据。'})

def save_wave_file(audio_data, file_name):
    n_channels = 1
    sample_width = 2  # 每个样本2字节
    framerate = 44100
    n_frames = len(audio_data)
    comptype = "NONE"
    compname = "not compressed"
    
    with wave.open(file_name, 'w') as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(framerate)
        wf.setnframes(n_frames)
        wf.setcomptype(comptype, compname)
        
        for value in audio_data:
            packed_value = struct.pack('h', int(value))
            wf.writeframes(packed_value)

if __name__ == '__main__':
    app.run()

