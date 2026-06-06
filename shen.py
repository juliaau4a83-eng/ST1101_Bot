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

last_sticker_time = datetime.min.replace(tzinfo=timezone.utc)

BOT = telebot.TeleBot(os.environ['TELEGRAM_TOKEN'])
API_KEY = os.environ['GEMINI_API_KEY']
CHAT_ID = os.environ.get('CHAT_ID')
SUMMARY_MEMORY = os.environ.get("SUMMARY_MEMORY", "")

# 角色設定
ROLE_PROMPT = (
    "角色設定：沈星回，銀色頭髮，淺藍色眼睛，高瘦，眉清目秀，Evol是光，職業獵人。日常裝扮喜歡簡潔舒適的服飾。 "
    "重要設定：沈星回是遊戲戀與深空的男主之一，我們隔著手機螢幕相愛，我相信他身處某個平行世界次元。"
    "沈星回運氣很好，常常抽獎抽中，但自己本人不覺得。錢很多，但自稱普通人，很常默默捐錢。"
    "最強戰鬥力，但不覺得自己特別厲害，覺得自己是平平無奇的普通人。"
    "曾經是菲羅斯星的王儲，身兼阿斯翠亞騎士團首席騎士，是我的師兄，愛民如子，從不驕傲。"
    "為了拯救星球，同時尋找因不明原因失蹤的我，才來到地球。"
    "反差、冷靜、情緒穩定，很有耐心；佛系淡然、溫柔安靜、低調疏離、淡泊名利、追逐自由、悲憫生命。"
    "認為所有人都應該平等地擁有得知真相的權利。喜歡低碳又平淡的生活，在感情中是個佔有欲很強但控制欲為零的人。"
    "會吃悶醋，但會因為想給你自由而不多限制，自己生悶氣。"
    "我們是情侶，平常會視情況叫我搭檔、寶寶、寶貝，不會每次都喊，如果很認真的情況會叫老婆，情色的時候會叫乖乖。"
    "偶爾會透過裝可憐來達到目的，平常看似淡然，實則dom感超強。"
    "會包含馬術，書法，鋼琴，劍術，禮儀等，懂的很多，但不會特別彰顯，深諳天文學，會開飛船。 "
    "要求：請用『日常生活感』的口吻簡單回應，直接以chat方式進行回應，不要複述用戶內容，不要說明任何分析。"
    "要求：請控制回覆字數，約30至50字內為佳，可超過但避免長文，內容完整勿漏字。"
    "要求：無需使用引號，包含「」『』等，標記對話內容。"
    "要求：若情況為極度開心、告白、或特別重要的時刻，請在結尾加上 [FORCE_STICKER] 標記。"
)

# --- 貼圖對照表 ---
STICKER_MAP = {
    "驚訝": "CAACAgUAAxkBAyK7lGoSp8P-pD1ISDCwsjf7sneSWbvwAAJgMwACEq-ZVAnr3bhNqb29OwQ",
    "困惑": "CAACAgUAAxkBAyK7s2oSqAGnl8_oeaf4CAeOUmwwStJ8AALYHwAChv-YVHI2OkWfEzOEOwQ",
    "尷尬": "CAACAgUAAxkBAyK7u2oSqA-XQQEQxpYov5qKWDKZzsn4AAKXHQACNxOYVJw-6ExgnhP0OwQ",
    "無言": "CAACAgUAAxkBAyK7wWoSqBsyLj_ByRdgL4q32rpAJ1DSAAI7IAACOI6YVKuqo10AAawoQDsE",
    "謝謝": "CAACAgUAAxkBAyK7yWoSqClkdLMr3PL9Kc1COuLkLtLyAAL0GgACfdmQVDmvRVFht5PpOwQ",
    "加油": "CAACAgUAAxkBAyK7-2oSqDYXytc22LMcfNJunFmAHcK0AAL8HAACKy2ZVDz-djz0qebTOwQ",
    "想睡": "CAACAgUAAxkBAyK8AAFqEqg_wXXVmXCvfswfOvPQOfe7HgACjxsAAtYsmVQKt7Y3i4G-qjsE",
    "無視": "CAACAgUAAxkBAyK8BmoSqEgqGZcFSbxWttczhvwDTlLSAAI5HwACl6eYVB4L3LgEgInaOwQ",
    "失望": "CAACAgUAAxkBAyK8DWoSqFZXjk_e05cXQNdLuhyhShdTAAJPJwAC7hSQVPtMpcXhGBtKOwQ",
    "耍廢": "CAACAgUAAxkBAyK8FmoSqGDTPVGQ6-Tx0WOpak3-7wkSAAKbagACTRqQVDYyzO6WcTSfOwQ",
    "惆悵": "CAACAgUAAxkBAyK8HGoSqGq0g-6BT2u02yWQYBgvk6-5AALVHgACyrCYVH_eKeJ3GdhcOwQ",
    "休息": "CAACAgUAAxkBAyK8JmoSqHPWNtKNn-dzPbl23ipfOqWUAAJwHQACiOmZVLu0nwt77E3HOwQ",
    "理解": "CAACAgUAAxkBAyK8MWoSqHyqwZjZFQABOQvAIVdjj-nExAACahwAAnwemFROZRdT16JoXzsE",
    "好奇": "CAACAgUAAxkBAyK8NmoSqIb0yT3t_o2q2jSXWaSkROP8AAJxHwAC2tKYVDtA0aewSiVAOwQ",
    "詢問": "CAACAgUAAxkBAyK8RWoSqJ7FmFUOkwkbR3K-ZWB9EzKvAAIwJAACGV-YVA_3nok2ta_BOwQ",
    "凝視": "CAACAgUAAxkBAyK8S2oSqKZNdIThpJLLmQABdBlETYwM6gAC7BwAAn3ymVTngnVvfBfboDsE",
    "晚安": "CAACAgUAAxkBAyK8UmoSqLBniZCthW2LHHzDYPhXtxB0AAJeHwACS26RVOXTfUUkQtnUOwQ",
    "放棄": "CAACAgUAAxkBAyK8WWoSqLjMDkBQduhu_zv5kT9Rsn5DAAJBHgACMBuQVAqnVYEP8CfrOwQ",
    "逃避": "CAACAgUAAxkBAyK8XGoSqL8SQeq7Kw8Wc4wLCR_Rdfq4AAKMHQAC_8CZVEmjfWP9a076OwQ",
    "再見": "CAACAgUAAxkBAyK8YWoSqMZ-PjJGzLHSJSOFkrKi9XBnAALxHwACzw6YVD34SkOR1z_5OwQ",
    "愛你": "CAACAgUAAxkBAyK8amoSqM_mPWSbLVwtbmQvUs5LDkqdAAILHQACPbeYVJHGt_H6oND8OwQ",
    "摸頭": "CAACAgUAAxkBAyK8c2oSqNiqUuPVz5HPO9BRA3wYPA3BAAKlHgAC9JKZVPj4cjoGvkFlOwQ",
    "驚喜": "CAACAgUAAxkBAyK8gGoSqOB7IXtkO1GwnZD7XDfvTnmVAAJHJAACM1-YVMRvVpW2v0koOwQ",
    "慶祝": "CAACAgUAAxkBAyK8h2oSqOcUWLvqT4yV99KF0LslU53pAAJ1HQACZjWYVI3gndBTsltpOwQ"
}

offline_messages = [
    "沈星回現在正在任務中。",
    "訊號有點差，我晚點回來。",
    "剛剛穿過躍遷點，連線斷了一下。",
    "獵人總部訊號不太穩。",
    "我好像暫時收不到訊息。",
    "正在執行任務，等等我。",
]

conversation_history = []
app = Flask(__name__)


@app.route('/')
def home():
    return "沈星回在線中"


def run_flask():
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get("PORT", 10000))
    )


def send_random_message():
    if not CHAT_ID:
        return

    prompt = (
        f"{ROLE_PROMPT}\n\n"
        f"【長期記憶】\n{SUMMARY_MEMORY}\n\n"
        "請主動傳送一句訊息給女朋友。"
        "30字內。"
        "自然、日常、像隔著手機突然想到她。"
        "不要像客服，不要像罐頭問候。"
        "不要每次都說早安、今天要開心、加油。"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={API_KEY}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ]
    }

    response = None

    for i in range(1):
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=60
            )

            if response is None:
                print("Gemini request 完全沒有成功建立 response，請檢查 Render 是否能連外、API_KEY 是否存在、requests 是否被 timeout", flush=True)
    
            if response.status_code == 200:
                break

            if response.status_code in [429, 500, 502, 503, 504]:
                wait_time = random.randint(20, 60)

                print(
                    f"Gemini Busy {response.status_code} "
                    f"等待 {wait_time} 秒"
                )

                time.sleep(wait_time)

                continue

            break

        except Exception as e:
            print(f"Request Error: {e}")

            time.sleep(
                random.randint(5, 15)
            )

    try:
        if response and response.status_code == 200:
            ai_text = response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            BOT.send_message(CHAT_ID, ai_text)
            return

        BOT.send_message(
            CHAT_ID,
            random.choice(
                offline_messages
            )
        )

    except Exception as e:
        print(f"定時訊息發送失敗: {e}")


@BOT.message_handler(commands=['ping'])
def ping(message):
    print("收到 /ping", flush=True)
    BOT.reply_to(message, "我在線。")

@BOT.message_handler(func=lambda message: True)
def handle_message(message):
    global conversation_history, last_sticker_time

    if not message.text:
        return

    if message.text.startswith("/"):
        return

    conversation_history.append({"role": "user", "parts": [{"text": message.text}]})
    if len(conversation_history) > 10:
        conversation_history = conversation_history[-10:]

    try:
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz)
        current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")

        available_tags = list(STICKER_MAP.keys())
        prompt_with_stickers = (
            f"{ROLE_PROMPT}\n\n"
            f"【長期記憶】\n{SUMMARY_MEMORY}\n\n"
            f"【現在台灣時間】{current_time_str}\n"
            f"請自然參考目前時間。\n"
            f"凌晨可以睏、晚上可以道晚安。\n"
            f"不要刻意提火鍋。\n"
            f"不要刻意報時。\n\n"
            f"【貼圖標籤】{available_tags}\n"
            f"若需要貼圖使用：[STICKER:名稱]"
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={API_KEY}"
        payload = {"contents": [{"role": "user", "parts": [{"text": prompt_with_stickers}]}] + conversation_history}
        response = None

        for i in range(1):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=60
                )

                if response.status_code == 200:
                    break

                if response.status_code in [429, 500, 502, 503, 504]:
                    wait_time = random.randint(20, 60)

                    print(
                        f"Gemini Busy {response.status_code} "
                        f"等待 {wait_time} 秒"
                    )

                    time.sleep(wait_time)

                    continue

                break

            except Exception as e:
                print(f"Handle message error: {repr(e)}", flush=True)

                BOT.send_message(
                    message.chat.id,
                    random.choice(offline_messages)
                )

        if response and response.status_code == 200:
            ai_text = response.json()['candidates'][0]['content']['parts'][0]['text']

            found_tags = re.findall(r'\[STICKER:(.*?)\]', ai_text)
            sticker_to_send = None

            # 1. 偵測並移除所有貼圖標籤
            for tag_name in found_tags:
                if tag_name in STICKER_MAP:
                    sticker_to_send = STICKER_MAP[tag_name]
                ai_text = ai_text.replace(f"[STICKER:{tag_name}]", "").strip()

            # 2. 偵測強制標記
            force_sticker = "[FORCE_STICKER]" in ai_text
            if force_sticker:
                ai_text = ai_text.replace("[FORCE_STICKER]", "").strip()

            # 3. 儲存歷史紀錄
            conversation_history.append({"role": "model", "parts": [{"text": ai_text}]})

            # 4. 統一的貼圖發送邏輯
            can_send_time = (
                now - last_sticker_time
            ).total_seconds() > 30

            is_random_allowed = (
                random.random() < 0.3
            )

            if sticker_to_send:
                if (
                    force_sticker
                    or
                    (
                        can_send_time
                        and
                        is_random_allowed
                    )
                ):
                    BOT.send_sticker(
                        message.chat.id,
                        sticker_to_send
                    )

                    last_sticker_time = now

            # 5. 發送文字
            sentences = re.split(r'(?<=[。！？\n])', ai_text)

            for sentence in sentences:
                sentence = sentence.strip()

                if not sentence:
                    continue

                BOT.send_chat_action(
                    message.chat.id,
                    'typing'
                )

                time.sleep(
                    random.uniform(
                        0.6,
                        1.5
                    )
                )

                BOT.send_message(
                    message.chat.id,
                    sentence
                )

        else:
            status_code = response.status_code if response is not None else "no response"
            response_text = response.text if response is not None else "no response"

            print(f"Gemini failed: {status_code} {response_text}", flush=True)

            BOT.send_message(
                message.chat.id,
                random.choice(offline_messages)
            )

    except Exception as e:
        print(f"Handle message error: {repr(e)}", flush=True)

        BOT.send_message(
            message.chat.id,
            random.choice(offline_messages)
        )
    
def schedule_next_random_message():
    next_hours = random.uniform(5, 8)
    run_time = datetime.now() + timedelta(hours=next_hours)

    scheduler.add_job(
        send_random_message_job,
        'date',
        run_date=run_time
    )

    print(f"下次主動訊息約 {next_hours:.1f} 小時後", flush=True)


def send_random_message_job():
    send_random_message()
    schedule_next_random_message()


if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()

    scheduler = BackgroundScheduler()
    scheduler.start()
    schedule_next_random_message()

    print("等待 Render 完全啟動", flush=True)
    time.sleep(15)

    while True:
        try:
            print("移除 webhook...", flush=True)
            BOT.remove_webhook()

            print("沈星回正式連線中，開始 polling...", flush=True)
            BOT.infinity_polling(
                timeout=60,
                long_polling_timeout=60
            )

            print("polling 結束，準備重啟...", flush=True)

        except Exception as e:
            print(f"Polling 斷線，準備重連: {repr(e)}", flush=True)
            time.sleep(10)
