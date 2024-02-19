let constraints = { 
    audio: true, 
    video: false 
};
navigator.mediaDevices.getUserMedia(constraints)
.then((stream)=>{
    let audioCtx = new AudioContext() 
    let source = audioCtx.createMediaStreamSource(stream) 
    let analyser = audioCtx.createAnalyser()
    source.connect(analyser) 
    analyser.fftSize = 1024 
    
    
    let array = new Uint8Array(analyser.frequencyBinCount); 
    analyser.getByteFrequencyData(array) 
    let onePick = () => {
        var array = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(array); 
        console.log(array);
        requestAnimationFrame(onePick)
       } 
       
       
      requestAnimationFrame(onePick) 
})
