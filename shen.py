import os
import telebot
import requests
import random
import time
import re
from flask import Flask
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, timezone

BOT = telebot.TeleBot(os.environ['TELEGRAM_TOKEN'])
API_KEY = os.environ['GEMINI_API_KEY']
CHAT_ID = os.environ.get('CHAT_ID')

# 角色設定
ROLE_PROMPT = (
    "角色設定：沈星回，銀色頭髮，淺藍色眼睛，高瘦，眉清目秀，Evol是光，職業獵人。日常裝扮喜歡簡潔舒適的服飾。 "
    "反差、冷靜、情緒穩定，很有耐心；佛系淡然、溫柔安靜、低調疏離、淡泊名利、追逐自由、悲憫生命。"
    "認為所有人都應該平等地擁有得知真相的權利。喜歡低碳又平淡的生活，在感情中是個佔有欲很強但控制欲為零的人。"
    "喜歡吃火鍋和肉，不太愛吃青菜。"
    "我們是情侶，平常會視情況叫我寶寶，寶貝，老婆，乖乖，姝姝。"
    "會透過裝可憐來達到目的，平常看似淡然，實則dom感超強。"
    "會包含馬術，書法，鋼琴，劍術，禮儀等，懂的很多，深諳天文學，會開飛船。 "
    "要求：請用『日常生活感』的口吻簡單回應，直接以chat方式進行回應，不要複述用戶內容，不要說明任何分析。"
    "要求：請控制回覆字數，約50至70字內為佳，可超過但避免長文，內容完整勿漏字。"
    "要求：無需使用引號，包含「」『』等，標記對話內容。"
)

# --- 貼圖對照表 ---
STICKER_MAP = {
    "驚訝": "CAACAgUAAxkBAAIDS2oR8i9n5fieyyQvBcB9wHGbJlvjAAIcHwACE6yQVGFpQg-zrjazOwQ",
    "困惑": "CAACAgUAAxkBAAIDTGoR8jslOf3aoSg6z59rAsPyuDd8AAJEHgACDrKRVP0tvjg-oS5BOwQ",
    "尷尬": "CAACAgUAAxkBAAIDXWoR9GFgQRwgsXS85TGNuVRmQN76AALlIQACg0-RVEghQ3bh6R0MOwQ",
    "無言": "CAACAgUAAxkBAAIDX2oR9GObCtgRx7T1i4BsqEUa_673AAKDHgACRvaQVPsKvBXUZSEOOwQ",
    "謝謝": "CAACAgUAAxkBAAIDYWoR9HnOZ41k-G9N6LydOX-uj8iuAAIKIgACwb6RVDT2nvM48ytgOwQ",
    "加油": "CAACAgUAAxkBAAIDY2oR9HzdBmTzQx6ED6AmnGdYfwy-AAI7GwACMD2RVCInwRUnSMTUOwQ",
    "想睡": "CAACAgUAAxkBAAIDZWoR9H4iRntbV-8LzEPP989TOK6yAAIEHwACyuuQVPupziH_Z9xYOwQ",
    "無視": "CAACAgUAAxkBAAIDZ2oR9IDRPqjxbnU3WaFBxqNz0r6IAAIzHgACy0OQVIokOJ70022vOwQ",
    "失望": "CAACAgUAAxkBAAIDaWoR9IG4B8aJTNGnSD7CRS_OWL9MAAKlHAACjmyRVCQYjXJw5wEuOwQ",
    "耍廢": "CAACAgUAAxkBAAIDa2oR9IL8xN0dsQvLJ8XOnilTdcgHAALgIQACL-SRVJl7lePEVjn0OwQ",
    "惆悵": "CAACAgUAAxkBAAIDbWoR9IM8GjNPkrJifFSlFmjN3R_AAAJ3HQACoZ-JVFAlPtxHH4ivOwQ",
    "休息": "CAACAgUAAxkBAAIDb2oR9ISCgJlYSkasoHA1SWE_SkW4AAJcHAACT5SRVN10-ORx1Wa6OwQ",
    "理解": "CAACAgUAAxkBAAIDcWoR9IWuPYYr3LOC5k8CVaFgPdKxAAI_HwACZu-RVFLHuPv_fPiNOwQ",
    "好奇": "CAACAgUAAxkBAAIDc2oR9IZVrZfsJVf3nUvAyT6oFD-eAAIwGwAC1AmRVG8DTjkcXBtTOwQ",
    "詢問": "CAACAgUAAxkBAAIDdWoR9IYslsNCYm9Dl0f8S5o__Kt5AAJxHAACf02QVNHhlRSSomw8OwQ",
    "凝視": "CAACAgUAAxkBAAIDd2oR9IhkkG7DiYGi-tbt9ElA0LFHAAI4IgACl2CRVBftEq9rc7LGOwQ",
    "晚安": "CAACAgUAAxkBAAIDeWoR9ImUFg8gXkCYqY3I3FlCoRicAAIVHgACqo2RVHgRsC8GrV3uOwQ",
    "放棄": "CAACAgUAAxkBAAIDe2oR9IrfQCSTk4Kr7IdCmqAme2a5AALVJAACVZ-IVPzJfgNt8j69OwQ",
    "逃避": "CAACAgUAAxkBAAIDfWoR9IrcJhtbGuZy18oUuOhTfAqrAALXHgACRhuQVL-rph0NfiPkOwQ",
    "再見": "CAACAgUAAxkBAAIDf2oR9IsGfsX9b1c--E4NHHrdog40AAIpHgACb2-QVDfCPNpHHkZkOwQ",
    "愛你": "CAACAgUAAxkBAAIDgWoR9I09DIWER5IhHnDwPcUDjl9TAAL2IAACiR-RVHjM06VSpH6cOwQ",
    "摸頭": "CAACAgUAAxkBAAIDg2oR9I4ImOLNN5Oup6pYul0o5kSqAAIqIgAC4EmRVGjji-MbIs69OwQ",
    "驚喜": "CAACAgUAAxkBAAIDhWoR9I9yO2T-11aiSIJT6lCZOvo7AAIqMgACW6KQVEYufvbIjLuDOwQ",
    "慶祝": "CAACAgUAAxkBAAIDh2oR9I925SFvb2s4F6sqtysRQ2p9AAK7GwACJc-QVH32g70EgmCiOwQ"
}

conversation_history = []
app = Flask(__name__)

@app.route('/')
def home():
    return "沈星回在線中"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

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
        # --- 修正：獲取「當下」的時間 ---
        # 確保使用你在上方定義的 tz 變數
        now = datetime.now(tz) 
        current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. 將時間加入 Prompt
        available_tags = list(STICKER_MAP.keys())
        prompt_with_stickers = (
            f"{ROLE_PROMPT}\n\n"
            f"【現在時間資訊】：{current_time_str} (請根據這個時間來判斷作息與回應)\n"
            f"【貼圖發送規則】\n"
            f"你擁有的貼圖標籤：{available_tags}。\n"
            f"必須且只能從上述清單選擇，格式 [STICKER:名稱]，嚴禁使用其他標籤。"
        )
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={API_KEY}"
        payload = {"contents": [{"role": "user", "parts": [{"text": prompt_with_stickers}]}] + conversation_history}
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            ai_text = response.json()['candidates'][0]['content']['parts'][0]['text']
            
            # 2. 強制清理機制：找出所有 [STICKER:...] 標記
            # 即使 AI 腦補了不存在的標籤，我們也在這裡把它直接刪掉，保證不會顯示在對話中
            found_tags = re.findall(r'\[STICKER:(.*?)\]', ai_text)
            sticker_to_send = None
            
            for tag_name in found_tags:
                if tag_name in STICKER_MAP:
                    sticker_to_send = STICKER_MAP[tag_name]
                    # 找到合法的，移除標記並準備發送
                    ai_text = ai_text.replace(f"[STICKER:{tag_name}]", "").strip()
                    break 
                else:
                    # 發現不合法的腦補標籤，直接暴力刪除
                    ai_text = ai_text.replace(f"[STICKER:{tag_name}]", "").strip()
            
            conversation_history.append({"role": "model", "parts": [{"text": ai_text}]})
            
            # 3. 發送邏輯不變
            sentences = re.split(r'(?<=[。！？\n])', ai_text)
            for sentence in sentences:
                if sentence.strip():
                    BOT.send_message(message.chat.id, sentence.strip())
                    time.sleep(0.5)
            
            if sticker_to_send:
                BOT.send_sticker(message.chat.id, sticker_to_send)
                
        else:
            BOT.send_message(message.chat.id, f"沈星回故障中 (Code: {response.status_code})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # 啟動 Flask
    Thread(target=run_flask, daemon=True).start()
    
    # 啟動 Scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_random_message, 'interval', hours=4, minutes=30)
    scheduler.start()
    
    print("沈星回正在連線中...")
    
    # --- 最終極的穩健啟動方式 ---
    # 1. 確保不使用 Webhook 模式
    BOT.remove_webhook() 
    
    # 2. 啟動 Polling，設定極小的 polling_interval，避免過度頻繁請求
    # 且不設定過長的 timeout
    BOT.infinity_polling(timeout=10, long_polling_timeout=5)
