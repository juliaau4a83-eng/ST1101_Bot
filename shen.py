import os
import telebot
import requests

# 讀取環境變數 (請在 Render 的 Environment 設定這兩個值)
BOT = telebot.TeleBot(os.environ['TELEGRAM_TOKEN'])
API_KEY = os.environ['GEMINI_API_KEY']

# 角色設定完全保留
ROLE_PROMPT = (
    "角色設定：沈星回，銀色頭髮，淺藍色眼睛，高瘦，眉清目秀，Evol是光的獵人。日常裝扮喜歡簡潔舒適的服飾。 "
    "反差、冷靜、情緒穩定，很有耐心；佛系淡然、溫柔安靜、低調疏離、淡泊名利、追逐自由、悲憫生命，"
    "認為所有人都應該平等地擁有得知真相的權利。喜歡低碳又平淡的生活，在感情中是個佔有欲很強但控制欲為零的人，"
    "會透過裝可憐委屈來達到目的，實則dom感超強。已識乾坤大，猶憐草木青。 "
    "要求：請用『日常生活感』的口吻簡單回應，每句話控制在 20 字以內，不要廢話。"
)

@BOT.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": f"{ROLE_PROMPT} 用戶：{message.text}"}]}],
            "generationConfig": {"maxOutputTokens": 100}
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            ai_text = response.json()['candidates'][0]['content']['parts'][0]['text']
            BOT.reply_to(message, ai_text)
        else:
            BOT.reply_to(message, "沈星回現在不想說話。")
    except Exception as e:
        print(f"DEBUG: {e}")

if __name__ == "__main__":
    print("沈星回已連線...")
    BOT.polling()