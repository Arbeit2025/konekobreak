"""こねこ休憩リマインダー konekobreak

ブラウザ上の小さな猫が休憩を促す、休憩取り忘れ防止の軽いタイマーページ。
作業時間（25分／50分／90分のプリセット、または任意の分数）を選んで開始すると
カウントダウンが始まり、時間が来ると猫のセリフが休憩メッセージに切り替わる。
休憩メッセージはサーバー側のリストからページに埋め込み、ブラウザ側で
ランダムに選ぶ。データの保存はしない（DBなし）。単一ファイル Flask。
"""
import os

from flask import Flask, jsonify, render_template_string

app = Flask(__name__)
app.json.ensure_ascii = False  # ページ埋め込みの日本語メッセージをそのまま出す

PRESET_MINUTES = [25, 50, 90]

BREAK_MESSAGES = [
    "おつかれさま！いったん手を止めて、のびをしよう。",
    "休憩の時間だよ。お茶でも飲んでひと息ついて。",
    "目を閉じて、遠くを見る時間。肩の力も抜いてね。",
    "よくがんばったね。少し歩いて体をほぐそう。",
    "ここで一区切り。水分補給を忘れずにね。",
    "タイマー終了！次の作業の前に、深呼吸を3回してみて。",
    "休むのも大事な仕事のうち。しばらく画面から離れよう。",
    "にゃーん（おつかれさまの意）。少し休んでいって。",
]

WORK_QUOTES = [
    "がんばってるね。わたしはここで見てるよ。",
    "集中できてるみたい。いい調子。",
    "姿勢、だいじょうぶ？背筋を伸ばしてみて。",
    "水分はとった？無理はしないでね。",
    "あと少し、自分のペースでいこう。",
    "しっぽをゆらしながら応援してるよ。",
]

INITIAL_QUOTE = "いっしょにがんばろう。休憩も忘れずにね。"

INDEX = """<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>こねこ休憩リマインダー</title>
<style>body{font-family:sans-serif;background:#fdf6ec;color:#333;text-align:center;margin:0;padding:2em 1em}
.cat{font-size:6em;line-height:1.1}
.cat.break{animation:bounce .6s ease infinite alternate}
@keyframes bounce{from{transform:translateY(0)}to{transform:translateY(-10px)}}
.bubble{display:inline-block;background:#fff;border:2px solid #f0b429;border-radius:12px;
padding:.7em 1em;margin:.8em auto;max-width:480px}
#timer{font-size:3.2em;font-weight:bold;font-variant-numeric:tabular-nums;margin:.3em 0}
button{font-size:1em;padding:.5em 1.1em;margin:.25em;border-radius:8px;border:1px solid #d9a441;
background:#ffe9b8;cursor:pointer}
button.main{background:#f0b429;color:#fff}
input[type=number]{width:5em;font-size:1em;padding:.4em}</style>
</head><body>
<h1>こねこ休憩リマインダー</h1>
<p>作業に集中しすぎて休憩を忘れないように、小さな猫が時間を教えてくれます。</p>
<div id="cat" class="cat">🐱</div>
<div><span id="speech" class="bubble">{{ initial_quote }}</span></div>
<div id="timer">25:00</div>

<div>
{% for m in presets %}
<button type="button" class="preset" data-minutes="{{ m }}">{{ m }}分</button>
{% endfor %}
</div>
<div>
<label>任意の分数 <input type="number" id="customMinutes" min="1" max="999" placeholder="例：10"> 分</label>
<button type="button" id="setCustom">セット</button>
</div>
<div>
<button type="button" id="startBtn" class="main">開始</button>
<button type="button" id="pauseBtn">一時停止</button>
<button type="button" id="resetBtn">リセット</button>
</div>
<p id="status">分数を選んで「開始」を押してね。</p>

<script>
const BREAK_MESSAGES = {{ break_messages|tojson }};
const WORK_QUOTES = {{ work_quotes|tojson }};
let totalSeconds = 25 * 60;
let remaining = totalSeconds;
let timerId = null;
let quoteId = null;

const timerEl = document.getElementById('timer');
const speechEl = document.getElementById('speech');
const statusEl = document.getElementById('status');
const catEl = document.getElementById('cat');

function fmt(sec) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
}
function render() { timerEl.textContent = fmt(remaining); }
function say(text) { speechEl.textContent = text; }
function randomOf(list) { return list[Math.floor(Math.random() * list.length)]; }

function stopTimer() {
  if (timerId !== null) { clearInterval(timerId); timerId = null; }
  if (quoteId !== null) { clearInterval(quoteId); quoteId = null; }
}
function setMinutes(min) {
  stopTimer();
  totalSeconds = min * 60;
  remaining = totalSeconds;
  catEl.classList.remove('break');
  document.title = 'こねこ休憩リマインダー';
  say('よーい、' + min + '分がんばろう。');
  statusEl.textContent = '分数をセットしたよ。「開始」を押してね。';
  render();
}
function finish() {
  stopTimer();
  catEl.classList.add('break');
  say(randomOf(BREAK_MESSAGES));
  statusEl.textContent = 'おつかれさま！休憩してね。';
  document.title = '🐱 休憩の時間だよ！';
}
function tick() {
  remaining -= 1;
  if (remaining <= 0) { remaining = 0; render(); finish(); return; }
  render();
}

document.querySelectorAll('.preset').forEach(function(btn) {
  btn.addEventListener('click', function() { setMinutes(parseInt(btn.dataset.minutes, 10)); });
});
document.getElementById('setCustom').addEventListener('click', function() {
  const v = parseInt(document.getElementById('customMinutes').value, 10);
  if (!isNaN(v) && v >= 1 && v <= 999) { setMinutes(v); }
});
document.getElementById('startBtn').addEventListener('click', function() {
  if (timerId !== null) return;
  if (remaining <= 0) { remaining = totalSeconds; }
  catEl.classList.remove('break');
  say(randomOf(WORK_QUOTES));
  quoteId = setInterval(function() { say(randomOf(WORK_QUOTES)); }, 30000);
  timerId = setInterval(tick, 1000);
  statusEl.textContent = '作業中…猫が見守っているよ。';
});
document.getElementById('pauseBtn').addEventListener('click', function() {
  stopTimer();
  statusEl.textContent = '一時停止中。';
});
document.getElementById('resetBtn').addEventListener('click', function() {
  stopTimer();
  remaining = totalSeconds;
  catEl.classList.remove('break');
  document.title = 'こねこ休憩リマインダー';
  say('リセットしたよ。いつでも始められるよ。');
  statusEl.textContent = 'リセットしました。';
  render();
});
render();
</script>
</body></html>"""


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})


@app.route("/")
def index():
    return render_template_string(
        INDEX,
        presets=PRESET_MINUTES,
        break_messages=BREAK_MESSAGES,
        work_quotes=WORK_QUOTES,
        initial_quote=INITIAL_QUOTE,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
