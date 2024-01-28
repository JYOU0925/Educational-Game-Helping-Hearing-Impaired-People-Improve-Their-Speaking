# 导入必要的库
from __future__ import print_function
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import librosa
import librosa.display


def process_img(path1,path2):
    # 读取第一个音频文件并绘制波形图
    x_1, fs = librosa.load(path1)
    librosa.display.waveshow(x_1, sr=fs)

    # 读取第二个音频文件并绘制波形图
    x_2, fs = librosa.load(path2)
    librosa.display.waveshow(x_2, sr=fs)

    # 设定用于计算DTW的参数
    n_fft = 4410
    hop_size = 2205

    # 计算第一个音频文件的色谱图
    x_1_chroma = librosa.feature.chroma_stft(y=x_1, sr=fs, tuning=0, norm=2,
                                            hop_length=hop_size, n_fft=n_fft)

    # 计算第二个音频文件的色谱图
    x_2_chroma = librosa.feature.chroma_stft(y=x_2, sr=fs, tuning=0, norm=2,
                                            hop_length=hop_size, n_fft=n_fft)

    # 使用DTW计算两个音频文件的距离和最优路径
    D, wp = librosa.sequence.dtw(X=x_1_chroma, Y=x_2_chroma, metric='cosine')
    wp_s = np.asarray(wp) * hop_size / fs

    # 绘制DTW的累积代价矩阵及最优路径
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111)
    librosa.display.specshow(D, x_axis='time', y_axis='time',
                            cmap='gray_r', hop_length=hop_size)
    imax = ax.imshow(D, cmap=plt.get_cmap('gray_r'),
                    origin='lower', interpolation='nearest', aspect='auto')
    ax.plot(wp_s[:, 1], wp_s[:, 0], marker='o', color='r')

    # 绘制两个音频文件的波形图，并标记最优路径上的对应点
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
    output_filename = 'waveform_plot.png'
    plt.savefig(output_filename, dpi=300)  # 保存为高分辨率照片，dpi可调整

    return output_filename

path1 = '/Users/apple/Documents/dissertation/dissertation/sample.mp3'
path2 = '/Users/apple/Documents/dissertation/output.wav'
output_filename = process_img(path1,path2)
print(output_filename)
