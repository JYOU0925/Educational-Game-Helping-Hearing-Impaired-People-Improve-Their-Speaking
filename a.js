let constraints = { 
    audio: true, 
    video: false 
};
navigator.mediaDevices.getUserMedia(constraints)
.then((stream)=>{
    let audioCtx = new AudioContext() 
    let source = audioCtx.createMediaStreamSource(stream) // 引入音频流
    let analyser = audioCtx.createAnalyser() // 创建分析器
    source.connect(analyser) // 将stream连接到分析器上
    analyser.fftSize = 1024 // 可以理解为设置频率的单位取样宽度
    
    
    let array = new Uint8Array(analyser.frequencyBinCount); // 保证长度满足
    analyser.getByteFrequencyData(array) // 将当前频域数据拷贝进数组 
    let onePick = () => {
        var array = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(array); // 将当前的频率数据传入array
        console.log(array);
        requestAnimationFrame(onePick)
       } // 采样函数
       
       
      requestAnimationFrame(onePick) // 开始执行采样
})