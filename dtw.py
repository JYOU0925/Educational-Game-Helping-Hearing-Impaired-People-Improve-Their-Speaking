from flask import Flask, jsonify
import matplotlib
import io
import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
import base64

app = Flask(__name__)

def plot_dtw(D, wp_s, hop_size, fs):
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111)
    librosa.display.specshow(D, x_axis='time', y_axis='time', cmap='gray_r', hop_length=hop_size)
    imax = ax.imshow(D, cmap=plt.get_cmap('gray_r'), origin='lower', interpolation='nearest', aspect='auto')
    ax.plot(wp_s[:, 1], wp_s[:, 0], marker='o', color='r')
    plt.tight_layout()

    img_bytes = io.BytesIO()
    fig.savefig(img_bytes, format='png')
    img_bytes.seek(0)
    plt.close()

    img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
    return img_base64

def plot_waveforms(x1, x2, fs, wp, hop_size):
    fig = plt.figure(figsize=(16, 8))
    plt.subplot(2, 1, 1)
    librosa.display.waveshow(x1, sr=fs)
    plt.title('Slower Version $X_1$')
    ax1 = plt.gca()

    plt.subplot(2, 1, 2)
    librosa.display.waveshow(x2, sr=fs)
    plt.title('Slower Version $X_2$')
    ax2 = plt.gca()

    trans_figure = fig.transFigure.inverted()
    lines = []
    arrows = 30
    points_idx = np.int16(np.round(np.linspace(0, wp.shape[0] - 1, arrows)))

    for tp1, tp2 in wp[points_idx] * hop_size / fs:
        # 获取在轴上的位置，用于绘制箭头
        coord1 = trans_figure.transform(ax1.transData.transform([tp1, 0]))
        coord2 = trans_figure.transform(ax2.transData.transform([tp2, 0]))

        # 绘制箭头
        line = matplotlib.lines.Line2D((coord1[0], coord2[0]),
                                    (coord1[1], coord2[1]),
                                    transform=fig.transFigure,
                                    color='r')
        lines.append(line)

    fig.lines = lines
    plt.tight_layout()

    img_bytes = io.BytesIO()
    fig.savefig(img_bytes, format='png')
    img_bytes.seek(0)
    plt.close()

    img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
    return img_base64

@app.route('/compute_dtw', methods=['POST'])
def compute_dtw():
    n_fft = 4410
    hop_size = 2205

    x1, fs = librosa.load('output.mp3')
    x2, fs = librosa.load('output.mp3')

    x1_chroma = librosa.feature.chroma_stft(y=x1, sr=fs, tuning=0, norm=2, hop_length=hop_size, n_fft=n_fft)
    x2_chroma = librosa.feature.chroma_stft(y=x2, sr=fs, tuning=0, norm=2, hop_length=hop_size, n_fft=n_fft)

    D, wp = librosa.sequence.dtw(X=x1_chroma, Y=x2_chroma, metric='cosine')
    wp_s = np.asarray(wp) * hop_size / fs

    dtw_img = plot_dtw(D, wp_s, hop_size, fs)
    waveforms_img = plot_waveforms(x1, x2, fs, wp, hop_size)

    response = {
        'dtw_img': dtw_img,
        'waveforms_img': waveforms_img
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
