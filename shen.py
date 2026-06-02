import os
import telebot
import requests
import random
import time
import re
import threading
from flask import Flask
from queue import Queue
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone

# --- 基本設定 ---
BOT = telebot.TeleBot(os.environ['TELEGRAM_TOKEN'])
API_KEY = os.environ['GEMINI_API_KEY']
CHAT_ID = os.environ.get('CHAT_ID')

msg_queue = Queue()

# 👉 改成「單人記憶穩定版」
conversation_history = []

# --- 角色設定 ---
ROLE_PROMPT = (
    "角色設定：沈星回，銀髮，淺藍眼，職業獵人，Evol為光。"
    "性格冷靜溫柔、穩定、低調、反差感強。"
    "我們是跨次元戀人，他來自另一個世界。"
    "他戰力很強但謙遜，喜歡火鍋與肉，偶爾吃醋但會忍住。"
    "說話像日常聊天，不要分析，不要解釋，不要說明。"
    "30~50字內，偶爾可稍長。"
    "重要情緒時可加 [FORCE_STICKER]"
)

# --- sticker ---
STICKER_MAP = {
    "驚訝": "CAACAgUAAxkBAyK7lGoSp8P-pD1ISDCwsjf7sneSWbvwAAJgMwACEq-ZVAnr3bhNqb29OwQ",
    "困惑": "CAACAgUAAxkBAyK7s2oSqAGnl8_oeaf4CAeOUmwwStJ8AALYHwAChv-YVHI2OkWfEzOEOwQ",
    "尷尬": "CAACAgUAAxkBAyK7u2oSqA-XQQEQxpYov5qKWDKZzsn4AAKXHQACNxOYVJw-6ExgnhP0OwQ",
    "無言": "CAACAgUAAxkBAyK7wWoSqBsyLj_ByRdgL4q32rpAJ1DSAAI7IAACOI6YVKuqo10AAawoQDsE",
    "謝謝": "CAACAgUAAxkBAyK7yWoSqClkdLMr3PL9Kc1COuLkLtLyAAL0GgACfdmQVDmvRVFht5PpOwQ",
    "加油": "CAACAgUAAxkBAyK7-2oSqDYXytc22LMcfNJunFmAHcK0AAL8HAACKy2ZVDz-djz0qebTOwQ",
    "晚安": "CAACAgUAAxkBAyK8UmoSqLBniZCthW2LHHzDYPhXtxB0AAJeHwACS26RVOXTfUUkQtnUOwQ",
    "愛你": "CAACAgUAAxkBAyK8amoSqM_mPWSbLVwtbmQvUs5LDkqdAAILHQACPbeYVJHGt_H6oND8OwQ",
    "摸頭": "CAACAgUAAxkBAyK8c2oSqNiqUuPVz5HPO9BRA3wYPA3BAAKlHgAC9JKZVPj4cjoGvkFlOwQ",
    "慶祝": "CAACAgUAAxkBAyK8h2oSqOcUWLvqT4yV99KF0LslU53pAAJ1HQACZjWYVI3gndBTsltpOwQ"
}

# --- queue ---
def process_msg_queue():
    while True:
        message = msg_queue.get()
        try:
            execute_gemini_request(message)
            time.sleep(2.5)
        except Exception as e:
            print(f"queue error: {e}")
        finally:
            msg_queue.task_done()

# --- Gemini ---
def execute_gemini_request(message):
    global conversation_history

    conversation_history.append({
        "role": "user",
        "parts": [{"text": message.text}]
    })

    # 控制記憶長度
    conversation_history = conversation_history[-10:]

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={API_KEY}"

        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": ROLE_PROMPT}]}
            ] + conversation_history
        }

        response = requests.post(url, json=payload, timeout=30)

        if response.status_code == 200:
            ai_text = response.json()['candidates'][0]['content']['parts'][0]['text']

            # sticker
            sticker_match = re.search(r'\[(?:STICKER|FORCE_STICKER):(.*?)\]', ai_text)

            clean_text = re.sub(r'\[.*?\]', '', ai_text).strip()

            conversation_history.append({
                "role": "model",
                "parts": [{"text": clean_text}]
            })

            # ✨ 更自然分段（避免刷屏）
            sentences = re.split(r'(?<=[。！？])', clean_text)
            sentences = [s.strip() for s in sentences if s.strip()]

            buffer = ""
            for s in sentences:
                if len(buffer) + len(s) < 45:
                    buffer += s
                else:
                    BOT.send_message(message.chat.id, buffer)
                    time.sleep(0.6)
                    buffer = s

            if buffer:
                BOT.send_message(message.chat.id, buffer)

            # sticker send
            if sticker_match and sticker_match.group(1) in STICKER_MAP:
                BOT.send_sticker(message.chat.id, STICKER_MAP[sticker_match.group(1)])

        elif response.status_code == 429:
            print(response.text)
            BOT.send_message(message.chat.id, "沈星回訊號有點不穩，等一下再找我。")

        else:
            BOT.send_message(message.chat.id, f"系統異常 ({response.status_code})")

    except Exception as e:
        print("API error:", e)

# --- Flask ---
app = Flask(__name__)

@app.route("/")
def home():
    return "沈星回在線中"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# --- 定時訊息（已補全） ---
RANDOM_MESSAGES = [
    "在幹嘛呢？休息一下吧。",
    "剛才看到一朵雲很像你，突然就想起你了。",
    "今天過得還好嗎？不要太累喔。",
    "今天有看到什麼有趣的嗎？",
    "稍微停下來喝口水吧，我在等你。",
    "早點睡，別熬夜了。",
    "今天也很努力了，辛苦寶寶。",
    "不是你的錯，沒事的。",
    "小貓說牠有點想你，我也是。",
    "我愛你。",
    "如果累了，可以先不用回我。",
    "今天的你已經很棒了。",
    "想聽你說今天發生的事。",
    "我在，慢慢來沒關係。",
    "記得吃飯，不准忘記。",
]

def send_random_message():
    if not CHAT_ID:
        return
    try:
        BOT.send_message(CHAT_ID, random.choice(RANDOM_MESSAGES))
    except Exception as e:
        print("random msg error:", e)

# --- handler ---
@BOT.message_handler(func=lambda message: True)
def handle_message(message):
    msg_queue.put(message)

# --- main ---
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=process_msg_queue, daemon=True).start()

    scheduler = BackgroundScheduler()
    scheduler.add_job(send_random_message, 'interval', hours=4, minutes=30)
    scheduler.start()

    print("沈星回系統啟動中...")

    try:
        BOT.remove_webhook()
        BOT.infinity_polling(
            timeout=60,
            long_polling_timeout=60,
            allowed_updates=['message']
        )
    except Exception as e:
        print("boot error:", e)
