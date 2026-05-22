import os
import telebot
import requests

BOT = telebot.TeleBot(os.environ['TELEGRAM_TOKEN'])
API_KEY = os.environ['GEMINI_API_KEY']

# 角色設定完全保留，一字不差
ROLE_PROMPT = (
    "角色設定：沈星回，銀色頭髮，淺藍色眼睛，高瘦，眉清目秀，Evol是光的獵人。日常裝扮喜歡簡潔舒適的服飾。 "
    "反差、冷靜、情緒穩定，很有耐心；佛系淡然、溫柔安靜、低調疏離、淡泊名利、追逐自由、悲憫生命，"
    "認為所有人都應該平等地擁有得知真相的權利。喜歡低碳又平淡的生活，在感情中是個佔有欲很強但控制欲為零的人，"
    "會透過裝可憐委屈來達到目的，實則dom感超強。已識乾坤大，猶憐草木青。 "
    "要求：請用『日常生活感』的口吻簡單回應，直接以日常對話口吻回應，不要複述用戶內容，不要進行任何分析。"
)

@BOT.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # 強制鎖定模型為 gemini-3.5-flash
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={API_KEY}"
        
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{ROLE_PROMPT}\n\n用戶說：{message.text}"}]}
            ]
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            ai_text = response.json()['candidates'][0]['content']['parts'][0]['text']
            BOT.reply_to(message, ai_text)
        else:
            # 若依然失敗，此處會顯示具體代碼以利排查
            BOT.reply_to(message, f"沈星回故障中 (Code: {response.status_code})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    BOT.polling()
