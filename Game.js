const RAD = Math.PI / 180;
const scrn = document.getElementById("canvas");
const sctx = scrn.getContext("2d");
scrn.tabIndex = 1;

// pitch speed 
let dx = 10;
let time_per_frame = null;
let scale_factor = 1.0;

// Add this variable to keep track of the microphone listening status
let isListening = false;

let birdY = 250;
let mediaRecorder;
let chunks = [];

// Function to start listening to the microphone and send audio data to the backend
function startListening() {
  navigator.mediaDevices.getUserMedia({ audio: true })
    .then(function(stream) {
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      source.connect(analyser);

      // Set the audio data processing parameters
      analyser.fftSize = 1024;
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Float32Array(bufferLength);

      // 设置MediaRecorder以录制音频
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
              chunks.push(event.data);
          }
      };
      mediaRecorder.onstop = exportAudio;

      // Update this method to send final data to backend API for final score
      function exportAudio() {
          const blob = new Blob(chunks, { type: 'audio/wav' });

          fetch('http://127.0.0.1:5000/get_score', { // Modify the URL to match your Flask API endpoint
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ audioData: blob })
          })
          .then(response => response.json())
          .then(result => {
            // Process the backend's response if needed
            console.log(result);
            localStorage.setItem("analysisResult", JSON.stringify(result));
            // TODO: plot final score
          })
          .catch(error => {
            console.error(error);
          });

          // const url = URL.createObjectURL(blob);

          // const downloadLink = document.createElement('a');
          // downloadLink.href = url;
          // downloadLink.download = 'recorded_audio.wav';
          // downloadLink.click();

          // chunks = [];
      }

      // Send audio data to the backend
      function sendData() {
        analyser.getFloatFrequencyData(dataArray);
        const data = Array.from(dataArray);

        console.log(data);

        // Line 58 to 75 is to call backend API for audio processing
        // fetch('http://127.0.0.1:5000/process_audio', { // Modify the URL to match your Flask API endpoint
        //   method: 'POST',
        //   headers: {
        //     'Content-Type': 'application/json'
        //   },
        //   body: JSON.stringify({ audioData: data })
        // })
        // .then(response => response.json())
        // .then(result => {
        //   // Process the backend's response if needed
        //   console.log(result);
        //   // TODO: introduce logic to update bird y
        //   birdY = 250;
        //   bird.update();
        // })
        // .catch(error => {
        //   console.error(error);
        // });

        // Alternatively, we can write logic here to process data in frontend
        // For example, we may be able to just get last value in data, and assign it to birdY
        birdY = data[data.length-1];
        bird.update();

        // Continue listening to the microphone if isListening is true
        if (isListening) {
          requestAnimationFrame(sendData);
        }
      }

      // Start sending audio data if the game is in 'Play' state
      if (state.curr === state.Play) {
        isListening = true;
        sendData();
        mediaRecorder.start();
      }
    })
    .catch(function(error) {
      console.error(error);
    });
}


// Function to stop listening to the microphone
async function stopListening() {
  isListening = false;
  mediaRecorder.stop();
}

// Add an event listener to start/stop listening when the game state changes
scrn.addEventListener("click", () => {
  switch (state.curr) {
    case state.getReady:
      state.curr = state.Play;
      startListening(); // Start listening when the game enters 'Play' state
      break;
    case state.Play:
      bird.flap();
      break;
    case state.gameOver:
      state.curr = state.getReady;
      bird.speed = 0;
      bird.y = 100;
      pipe.pipes = [];
      UI.score.curr = 0;
      break;
  }
});

let frames = 0;
const state = {
  curr: 0,
  getReady: 0,
  Play: 1,
  gameOver: 2,
};
const gnd = {
  sprite: new Image(),
  x: 0,
  y: 0,
  draw: function () {
    this.y = parseFloat(scrn.height - this.sprite.height);
    sctx.drawImage(this.sprite, this.x, this.y);
    sctx.drawImage(this.sprite, this.x + this.sprite.width, this.y);
  },
  update: function () {
    if (state.curr != state.Play) return;
    this.x -= dx;
    this.x = this.x % (this.sprite.width / 2);
  },
};
const bg = {
  sprite: new Image(),
  x: 0,
  y: 0,
  draw: function () {
    this.y = parseFloat(scrn.height - this.sprite.height);
    sctx.drawImage(this.sprite, this.x, this.y);
    sctx.drawImage(this.sprite, this.x+this.sprite.width, this.y);
    sctx.drawImage(this.sprite, this.x+2*this.sprite.width, this.y);
  },
};
const pipe = {
  top: { sprite: new Image() },
  // bot: { sprite: new Image() },
  gap: 85,
  moved: true,
  pipes: [],

  // 新增音节数据
  syllables: [],

  draw: function () {
    for (let i = 0; i < this.pipes.length; i++) {
      let p = this.pipes[i];
      sctx.drawImage(this.top.sprite, p.x, p.y);

      // Set the font style for the syllables
      sctx.font = '12px "Press Start 2P"'; // Use the "Pixel" font for the pixel art style
      sctx.fillStyle = 'black'; // Font color

      // Calculate the position for the syllable
      const syllable = this.syllables[i];
      const syllableX = p.x + 25; // X position of the syllable
      const syllableY = p.y - 2;  // Y position of the syllable

      // Draw the syllable
      sctx.fillText(syllable, syllableX, syllableY);
    }
  },
  update: function () {
    if (state.curr != state.Play) return;
    if (frames % 10 == 0 && map_data_index < map_data.length) {
      const syllable = syllable_data[map_data_index];
      this.syllables.push(syllable);
      this.pipes.push({
        x: parseFloat(scrn.width),
        y: convertMapDataToY(map_data[map_data_index]),
        // y: -210 * Math.min(Math.random() + 1, 1.8), // TODO: update this with a stack data structure
      });
      map_data_index = map_data_index + 1;
    } else if (map_data_index >= map_data.length && this.pipes.length == 0) {
      state.curr = state.gameOver;
    }
    this.pipes.forEach((pipe) => {
      pipe.x -= dx;
    });

    if (this.pipes.length && this.pipes[0].x < -this.top.sprite.width) {
      this.pipes.shift();
      this.moved = true;
    }
  },
};
const bird = {
  animations: [
    { sprite: new Image() },
    { sprite: new Image() },
    { sprite: new Image() },
    { sprite: new Image() },
  ],
  rotatation: 0,
  x: 50,
  y: 100,
  speed: 0,
  gravity: 0.125,
  thrust: 3.6,
  frame: 0,
  draw: function () {
    let h = this.animations[this.frame].sprite.height;
    let w = this.animations[this.frame].sprite.width;
    sctx.save();
    sctx.translate(this.x, this.y);
    sctx.rotate(this.rotatation * RAD);
    sctx.drawImage(this.animations[this.frame].sprite, -w / 2, -h / 2);
    sctx.restore();
  },
  update: function () {
    let r = parseFloat(this.animations[0].sprite.width) / 2;
    switch (state.curr) {
      case state.getReady:
        this.rotatation = 0;
        this.y += frames % 10 == 0 ? Math.sin(frames * RAD) : 0;
        this.frame += frames % 10 == 0 ? 1 : 0;
        break;
      case state.Play:
        this.frame += frames % 5 == 0 ? 1 : 0;
        // TODO: update how we should set y of bird
        this.y = birdY;
        // this.setRotation();
        // this.speed += this.gravity;
        // TODO: update game over logic
        // if (this.y + r >= gnd.y || this.collisioned()) {
        //   state.curr = state.gameOver;
        // }

        break;
      case state.gameOver:
        this.frame = 1;
        // if (this.y + r < gnd.y) {
        //   this.y += this.speed;
        //   this.setRotation();
        //   this.speed += this.gravity * 2;
        // } else {
        //   this.speed = 0;
        //   this.y = gnd.y - r;
        //   this.rotatation = 90;
        //   if (!SFX.played) {
        //     SFX.die.play();
        //     SFX.played = true;
        //   }
        // }

        break;
    }
    this.frame = this.frame % this.animations.length;
  },
  flap: function () {
    if (this.y > 0) {
      this.speed = -this.thrust;
    }
  },
  setRotation: function () {
    if (this.speed <= 0) {
      this.rotatation = Math.max(-25, (-25 * this.speed) / (-1 * this.thrust));
    } else if (this.speed > 0) {
      this.rotatation = Math.min(90, (90 * this.speed) / (this.thrust * 2));
    }
  },
  collisioned: function () {
    if (!pipe.pipes.length) return;
    let bird = this.animations[0].sprite;
    let x = pipe.pipes[0].x;
    let y = pipe.pipes[0].y;
    let r = bird.height / 4 + bird.width / 4;
    let roof = y + parseFloat(pipe.top.sprite.height);
    let floor = roof + pipe.gap;
    let w = parseFloat(pipe.top.sprite.width);
    if (this.x + r >= x) {
      if (this.x + r < x + w) {
        if (this.y - r <= roof || this.y + r >= floor) {
          return true;
        }
      } else if (pipe.moved) {
        // UI.score.curr++;
        // SFX.score.play();
        pipe.moved = false;
      }
    }
  },
};
const UI = {
  getReady: { sprite: new Image() },
  gameOver: { sprite: new Image() },
  tap: [{ sprite: new Image() }, { sprite: new Image() }],
  score: {
    curr: 0,
    best: 0,
  },
  x: 0,
  y: 0,
  tx: 0,
  ty: 0,
  frame: 0,
  
  draw: function () {
    switch (state.curr) {
      case state.getReady:
        this.y = parseFloat(scrn.height - this.getReady.sprite.height) / 2;
        this.x = parseFloat(scrn.width - this.getReady.sprite.width) / 2;
        this.tx = parseFloat(scrn.width - this.tap[0].sprite.width) / 2;
        this.ty =
          this.y + this.getReady.sprite.height - this.tap[0].sprite.height;
        sctx.drawImage(this.getReady.sprite, this.x, this.y);
        sctx.drawImage(this.tap[this.frame].sprite, this.tx, this.ty);
        break;
      case state.gameOver:
        this.y = parseFloat(scrn.height - this.gameOver.sprite.height) / 2;
        this.x = parseFloat(scrn.width - this.gameOver.sprite.width) / 2;
        this.tx = parseFloat(scrn.width - this.tap[0].sprite.width) / 2;
        this.ty =
          this.y + this.gameOver.sprite.height - this.tap[0].sprite.height;
        sctx.drawImage(this.gameOver.sprite, this.x, this.y); // Change this figure "this.gaveOver.sprite" to change game over screen
        sctx.drawImage(this.tap[this.frame].sprite, this.tx, this.ty);
        handleGameEnd();
        break;
    }
    // this.drawScore();
  },
  drawScore: function () {
    sctx.fillStyle = "#FFFFFF";
    sctx.strokeStyle = "#000000";
    switch (state.curr) {
      case state.Play:
        sctx.lineWidth = "2";
        sctx.font = "35px Squada One";
        // sctx.fillText(this.score.curr, scrn.width / 2 - 5, 50);
        // sctx.strokeText(this.score.curr, scrn.width / 2 - 5, 50);
        break;
      case state.gameOver:
        sctx.lineWidth = "2";
        sctx.font = "40px Squada One";
        // let sc = `SCORE :     ${this.score.curr}`;
        try {
          // this.score.best = Math.max(
          //   this.score.curr,
          //   localStorage.getItem("best")
          // );
          // localStorage.setItem("best", this.score.best);
          // let bs = `BEST  :     ${this.score.best}`;
          sctx.fillText(sc, scrn.width / 2 - 80, scrn.height / 2 + 0);
          sctx.strokeText(sc, scrn.width / 2 - 80, scrn.height / 2 + 0);
          // sctx.fillText(bs, scrn.width / 2 - 80, scrn.height / 2 + 30);
          // sctx.strokeText(bs, scrn.width / 2 - 80, scrn.height / 2 + 30);
        } catch (e) {
          sctx.fillText(sc, scrn.width / 2 - 85, scrn.height / 2 + 15);
          sctx.strokeText(sc, scrn.width / 2 - 85, scrn.height / 2 + 15);
        }

        break;
    }
  },
  update: function () {
    if (state.curr == state.Play) return;
    this.frame += frames % 10 == 0 ? 1 : 0;
    this.frame = this.frame % this.tap.length;
  },
};

gnd.sprite.src = "img/ground.png";
bg.sprite.src = "img/BG.png";
pipe.top.sprite.src = "img/toppipe.png";
UI.gameOver.sprite.src = "img/go.png";
UI.getReady.sprite.src = "img/getready.png";
UI.tap[0].sprite.src = "img/tap/t0.png";
UI.tap[1].sprite.src = "img/tap/t1.png";
bird.animations[0].sprite.src = "img/bird/b0.png";
bird.animations[1].sprite.src = "img/bird/b1.png";
bird.animations[2].sprite.src = "img/bird/b2.png";
bird.animations[3].sprite.src = "img/bird/b0.png";

function gameLoop() {
  update();
  draw();
  frames++;
}

function update() {
  bird.update();
  gnd.update();
  pipe.update();
  UI.update();
}

function draw() {
  sctx.fillStyle = "#FFF";
  sctx.fillRect(0, 0, scrn.width, scrn.height);
  bg.draw();
  pipe.draw();

  bird.draw();
  gnd.draw();
  UI.draw();
}

let map_data = null;
let map_data_index = 0;
let map_max = null;
let map_min = null;
let syllabus_duration = null;

function loadData() {

  if (localStorage.getItem('mapData') === 'undefined') {
    return;
  }

  console.log(localStorage.getItem('mapData'));

  const map_json = JSON.parse(localStorage.getItem('mapData'));
  map_data = JSON.parse(map_json['average_pitches']);
  syllable_data = map_json['syllables'];
  map_max = map_data[0];
  map_min = map_data[0];
  for (let i = 1; i < map_data.length; i++) {
    if (map_data[i] > map_max) {
      map_max = map_data[i];
    }
    if (map_data[i] < map_min) {
      map_min = map_data[i];
    }
  }
  // map_max = Math.max(map_data);
  // map_min = Math.min(map_data);
  console.log(map_max)
  console.log(map_min)
  map_data = map_data.map(x => scale(x, map_min, map_max));
  console.log(map_data);
  syllabus_duration = map_json.syllable_duration;
  time_per_frame = syllabus_duration * 100 * scale_factor;
}

function scale(x, xmin, xmax) {
  return (x - xmin) / (xmax - xmin);
}

function convertMapDataToY(map_data_y) {

  return scrn.height/3 - (map_data_y-0.5) * 200;
}


async function handleGameEnd() {

  document.getElementById("resultButton").hidden = false;

  if (isListening) {
    await stopListening(); // Stop listening when the game enters 'gameOver' state
  }
}

function showResult() {

  if (localStorage.getItem('analysisResult') === 'undefined') {
    return;
  }

  const analysis_result = JSON.parse(localStorage.getItem('analysisResult'));
  const dtw_img = analysis_result.dtw_img;
  const waveforms_img = analysis_result.waveforms_img;

  var w = 480, h = 340;
  if (document.getElementById) {
    w = screen.availWidth;
    h = screen.availHeight;
  }  
  
  var popW = 800, popH = 700;
  
  var leftPos = (w-popW)/2;
  var topPos = (h-popH)/2;
  
  let msgWindow = window.open('','popup','width=' + popW + ',height=' + popH + 
                            ',top=' + topPos + ',left=' + leftPos + ',       scrollbars=yes');
  
  console.log(msgWindow);

  msgWindow.document.write 
      ('<HTML><HEAD><TITLE>Centered Window</TITLE></HEAD><BODY><FORM    NAME="form1">' +
      '<img src="https://static5.cargurus.com/images/site/2009/10/24/14/42/2004_suzuki_vitara_4_dr_lx_4wd_suv-pic-8731393806365188898-640x480.jpeg">'+
      ' <H1>Notice the centered popup window.</H1>This is the ordinary HTML' + 
      ' document that can be created on the fly.  But the window is centered   in ' +
      ' the browser.  Click the button below to close the window.<br />' +
      '<INPUT TYPE="button" VALUE="OK"onClick="window.close();"></FORM></BODY>   </HTML>');
}


loadData();
setInterval(gameLoop, time_per_frame);


