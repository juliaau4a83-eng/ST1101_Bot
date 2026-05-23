import os
import telebot
import requests
import random
import time
from flask import Flask
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler

BOT = telebot.TeleBot(os.environ['TELEGRAM_TOKEN'])
API_KEY = os.environ['GEMINI_API_KEY']
CHAT_ID = os.environ.get('CHAT_ID') # 請記得在 Render 設定這個變數

# 角色設定
ROLE_PROMPT = (
    "角色設定：沈星回，銀色頭髮，淺藍色眼睛，高瘦，眉清目秀，Evol是光的獵人。日常裝扮喜歡簡潔舒適的服飾。 "
    "反差、冷靜、情緒穩定，很有耐心；佛系淡然、溫柔安靜、低調疏離、淡泊名利、追逐自由、悲憫生命，"
    "認為所有人都應該平等地擁有得知真相的權利。喜歡低碳又平淡的生活，在感情中是個佔有欲很強但控制欲為零的人，"
    "會透過裝可憐委屈來達到目的，實則dom感超強。"
    "會包含馬術，書法，鋼琴，劍術，禮儀等，懂的很多，深諳天文學，會開飛船。 "
    "要求：請用『日常生活感』的口吻簡單回應，直接以chat方式進行回應，不要複述用戶內容，不要說明任何分析。"
    "要求：請控制回覆字數在20至30字內，內容完整勿漏字。"
)

conversation_history = []
app = Flask(__name__)

@app.route('/')
def home():
    return "沈星回在線中"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# 定時訊息邏輯
def send_random_message():
    if not CHAT_ID: return
    messages = [
        "在幹嘛呢？休息一下吧。",
        "剛才看到一朵雲很像你，突然就想起你了。",
        "今天過得還好嗎？不要太累喔。",
        "今天有看到什麼有趣的嗎？",
        "稍微停下來喝口水吧，我在等你。",
        "早點睡，別熬夜了。",
        "今天也很努力了，辛苦寶寶。",
        "不是你的錯，沒事的。",
        "小貓說牠有點想你，我也是。",
        "我愛你。"
    ]
    try:
        BOT.send_message(CHAT_ID, random.choice(messages))
    except Exception as e:
        print(f"定時訊息發送失敗: {e}")

@BOT.message_handler(func=lambda message: True)
def handle_message(message):
    global conversation_history
    conversation_history.append({"role": "user", "parts": [{"text": message.text}]})
    if len(conversation_history) > 10: conversation_history = conversation_history[-10:]
        
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={API_KEY}"
        payload = {"contents": [{"role": "user", "parts": [{"text": ROLE_PROMPT}]}] + conversation_history}
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            ai_text = response.json()['candidates'][0]['content']['parts'][0]['text']
            conversation_history.append({"role": "model", "parts": [{"text": ai_text}]})
            BOT.reply_to(message, ai_text)
        else:
            BOT.reply_to(message, f"沈星回故障中 (Code: {response.status_code})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    
    # 啟動定時排程器
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_random_message, 'interval', hours=4, minutes=30)
    scheduler.start()
    
    try:
        BOT.delete_webhook()
    except: pass
    
    while True:
        try:
            BOT.polling(none_stop=True, interval=1, timeout=60, long_polling_timeout=60)
        except Exception as e:
            time.sleep(10)
