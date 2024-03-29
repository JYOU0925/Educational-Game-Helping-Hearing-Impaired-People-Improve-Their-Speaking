from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin
import numpy as np
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
import matplotlib.pyplot as plt
import base64
import matplotlib
import io

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

def convert_to_syllable_array(matrix_list):
    syllable_array = []
    for matrix in matrix_list:
        syllables = ["".join(row) for row in matrix]
        syllable_array.extend(syllables)
    return syllable_array

def remove_punctuation(text):
    translator = str.maketrans("", "", string.punctuation)
    return text.translate(translator)

def extract_pitch_contour(audio_file, num_syllables):
    print("before loading in librosa", file=sys.stdout)
    
    waveform, sample_rate = librosa.load(audio_file)
    
    print("librosa got basic info 1", file=sys.stdout)
    pitches, magnitudes = librosa.piptrack(y=waveform, sr=sample_rate)
    
    print("librosa got basic info 2", file=sys.stdout)
    duration = librosa.get_duration(y=waveform, sr=sample_rate)

    print("librosa got basic info", file=sys.stdout)
    
    syllable_duration = duration/num_syllables 

    timestamps = np.arange(0, num_syllables * syllable_duration, syllable_duration)

    average_pitches = []
    for i in range(len(timestamps)):
        pitch_values = pitches[:, i]
        average_pitch = pitch_values.mean()
        average_pitches.append(average_pitch)

    timestamps = timestamps.tolist()
    syllable_pitches = dict(zip(timestamps, average_pitches))

    print("before return from librosa job", file=sys.stdout)
    
    return syllable_pitches, syllable_duration, average_pitches

@app.route('/process_text', methods=['POST'])
def process_text():

    print("process_text triggered", file=sys.stdout)

    print(request.method, file=sys.stdout)

    if request.method == "OPTIONS":

        response = make_response(
            jsonify(
                {},
                200,
            )
        )
        response.headers["Content-Type"] = "application/json"
        response.headers["Acces-Control-Allow-Origin"] = "*"
        return response

    data = request.get_json()
    
    print(data)

    text = data['text']
    rate = data['rate']
    selected_language = data['language'] 
    
    print("Get input {}".format(text), file=sys.stdout)
    print("type of rate: {}".format(type(rate)))

    if text:
        ssp = SyllableTokenizer()
        text_without_punctuation = remove_punctuation(text)
        syllables = [ssp.tokenize(token) for token in word_tokenize(text_without_punctuation)]
        syllable_array = convert_to_syllable_array(syllables)

        num_syllables = len(syllable_array)

        print("Number of syllables {0}".format(num_syllables), file=sys.stdout)

        tts = gTTS(text=text, lang=selected_language, slow=rate) 
        tts.save("temp.wav")

        # pygame.mixer.init()
        # pygame.mixer.music.load("temp.mp3")

        if os.path.exists("output.wav"):
            os.remove("output.wav")

        print("Saving to mp3", file=sys.stdout)

        os.rename("temp.wav", "output.wav")

        print("Saved to mp3", file=sys.stdout)
        
        syllable_pitches, syllable_duration, average_pitches = extract_pitch_contour('output.wav', num_syllables)

        syllable_pitches = {float(key): float(value) for key, value in syllable_pitches.items()}

        print("Constructing response", file=sys.stdout)
        
        response_dict = {
            'syllables': syllable_array,
            'syllable_pitches': syllable_pitches,

            'average_pitches': str(average_pitches),
            'syllable_duration': syllable_duration
        }
        
        print("Before writing to file", file=sys.stdout)
        print(response_dict)

        with open('dissertation/file/output.txt', 'w') as output_file:
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

def process_img(path1,path2):
    x_1, fs = librosa.load(path1)
    librosa.display.waveshow(x_1, sr=fs)

    x_2, fs = librosa.load(path2)
    librosa.display.waveshow(x_2, sr=fs)

    n_fft = 4410
    hop_size = 2205

    x_1_chroma = librosa.feature.chroma_stft(y=x_1, sr=fs, tuning=0, norm=2,
                                            hop_length=hop_size, n_fft=n_fft)

    x_2_chroma = librosa.feature.chroma_stft(y=x_2, sr=fs, tuning=0, norm=2,
                                            hop_length=hop_size, n_fft=n_fft)

    D, wp = librosa.sequence.dtw(X=x_1_chroma, Y=x_2_chroma, metric='cosine')
    wp_s = np.asarray(wp) * hop_size / fs

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111)
    librosa.display.specshow(D, x_axis='time', y_axis='time',
                            cmap='gray_r', hop_length=hop_size)
    imax = ax.imshow(D, cmap=plt.get_cmap('gray_r'),
                    origin='lower', interpolation='nearest', aspect='auto')
    ax.plot(wp_s[:, 1], wp_s[:, 0], marker='o', color='r')

    fig = plt.figure(figsize=(16, 8))
    plt.subplot(2, 1, 1)
    librosa.display.waveshow(x_1, sr=fs)
    plt.title('Slower Version $X_1$')
    ax1 = plt.gca()

    plt.subplot(2, 1, 2)
    librosa.display.waveshow(x_2, sr=fs)
    plt.title('Slower Version $X_2$')
    ax2 = plt.gca()

    trans_figure = fig.transFigure.inverted()
    lines = []
    arrows = 30
    points_idx = np.int16(np.round(np.linspace(0, wp.shape[0] - 1, arrows)))

    for tp1, tp2 in wp[points_idx] * hop_size / fs:

        coord1 = trans_figure.transform(ax1.transData.transform([tp1, 0]))
        coord2 = trans_figure.transform(ax2.transData.transform([tp2, 0]))

        line = matplotlib.lines.Line2D((coord1[0], coord2[0]),
                                    (coord1[1], coord2[1]),
                                    transform=fig.transFigure,
                                    color='r')
        lines.append(line)

    fig.lines = lines
    plt.tight_layout()

    image_stream = io.BytesIO()
    plt.savefig(image_stream, format='png', dpi=300)
    image_stream.seek(0)
    image_data = image_stream.read()

    return image_data
    
@app.route('/get_score', methods=['POST'])
def get_score():
    default_value = 0
    front_end_audio = request.form.get('audio-file', default_value)
    path1 = 'dissertation/sample.mp3'  
    audio_data2 = front_end_audio  

    image_data = process_img(path1, audio_data2)

    response = {
        'image': image_data,
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run()
