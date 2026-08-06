import os
import time
import logging
import re
import threading
import requests
from bs4 import BeautifulSoup
import telebot
from telebot import types
from flask import Flask

# ==========================================
# CONFIGURATION
# ==========================================
# New Bot Token Updated
BOT_TOKEN = "8856008829:AAHgne9V0zbxiSb67FUKNKIQM1x89_Lk1QY"
PORT = int(os.environ.get("PORT", 8080))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

user_active_numbers = {}

# ==========================================
# FLASK KEEP-ALIVE SYSTEM FOR RENDER
# ==========================================
@app.route('/')
def home():
    return "Bot is alive and running 24/7!", 200

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

# ==========================================
# MULTI-SOURCE FREE NUMBERS SCRAPER
# ==========================================
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_free_numbers():
    """Fetches free public numbers from multiple sources."""
    numbers_list = []
    
    # Source 1: online-sms.org
    try:
        url1 = "https://online-sms.org"
        res = requests.get(url1, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for card in soup.select('a.btn-number') or soup.select('div.col-lg-4'):
                num_text = card.text.strip()
                phone_matches = re.findall(r'\+\d{10,15}', num_text)
                href = card.get('href') or (card.find('a')['href'] if card.find('a') else '')
                
                if phone_matches and href:
                    detail_page = url1 + href if href.startswith('/') else href
                    numbers_list.append({
                        "number": phone_matches[0],
                        "country": "Public",
                        "url": detail_page
                    })
    except Exception as e:
        logging.error(f"Source 1 Error: {e}")

    # Source 2: receive-smss.com Fallback
    if not numbers_list:
        try:
            url2 = "https://receive-smss.com"
            res = requests.get(url2, headers=HEADERS, timeout=8)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                for card in soup.select('div.number-boxes-item'):
                    num_tag = card.select_one('h4')
                    country_tag = card.select_one('h5')
                    link_tag = card.select_one('a')
                    
                    if num_tag and link_tag:
                        phone_number = num_tag.text.strip()
                        country = country_tag.text.strip() if country_tag else "Public"
                        detail_page = url2 + link_tag['href'] if not link_tag['href'].startswith("http") else link_tag['href']
                        numbers_list.append({
                            "number": phone_number,
                            "country": country,
                            "url": detail_page
                        })
        except Exception as e:
            logging.error(f"Source 2 Error: {e}")

    return numbers_list

def get_latest_otp(number_url):
    """Scrapes the latest SMS from selected number detail page."""
    try:
        res = requests.get(number_url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Search in table rows
            rows = soup.select('table tbody tr') or soup.select('div.table-row')
            if rows:
                latest_row = rows[0]
                text_content = latest_row.text.strip()
                if len(text_content) > 5:
                    return text_content
    except Exception as e:
        logging.error(f"OTP Scraping Error: {e}")
    return None

# ==========================================
# BOT HANDLERS
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📱 Get Free Number", callback_data="get_free_num"))
    
    welcome_text = (
        f"👋 <b>Welcome {message.from_user.first_name}!</b>\n\n"
        f"Aap yahan se Free Virtual Numbers le sakte hain aur unke OTP dekh sakte hain."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id

    if call.data == "get_free_num":
        bot.answer_callback_query(call.id, "Searching available free numbers...")
        numbers = get_free_numbers()
        
        if not numbers:
            bot.send_message(
                chat_id, 
                "❌ <i>Free servers par abhi load hai. 1 min baad dobara try karein.</i>"
            )
            return
            
        markup = types.InlineKeyboardMarkup(row_width=1)
        for item in numbers[:8]: # Top 8 numbers show karega
            btn_text = f"🌐 {item['country']} : {item['number']}"
            user_active_numbers[item['number']] = item['url']
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"sel_{item['number']}"))
            
        bot.edit_message_text(
            "👇 <b>Select a Virtual Number:</b>",
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=markup
        )

    elif call.data.startswith("sel_"):
        selected_num = call.data.split("_")[1]
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📩 Check OTP", callback_data=f"chk_{selected_num}"))
        markup.add(types.InlineKeyboardButton("🔄 Back to List", callback_data="get_free_num"))
        
        text = (
            f"✅ <b>Number Selected!</b>\n\n"
            f"📱 <b>Number:</b> <code>{selected_num}</code>\n\n"
            f"Is number ko app me dalein, fir <b>Check OTP</b> dabayein."
        )
        bot.send_message(chat_id, text, reply_markup=markup)

    elif call.data.startswith("chk_"):
        selected_num = call.data.split("_")[1]
        number_url = user_active_numbers.get(selected_num)
        
        bot.answer_callback_query(call.id, "Checking inbox...")
        
        if not number_url:
            numbers = get_free_numbers()
            for item in numbers:
                if item['number'] == selected_num:
                    number_url = item['url']
                    break

        if number_url:
            sms_text = get_latest_otp(number_url)
            if sms_text:
                digits = re.findall(r'\b\d{4,8}\b', sms_text)
                code_text = f"<code>{digits[0]}</code>" if digits else "Below"

                response = (
                    f"📩 <b>Latest SMS Received!</b>\n\n"
                    f"📱 <b>Number:</b> <code>{selected_num}</code>\n"
                    f"🔑 <b>OTP Code:</b> {code_text}\n\n"
                    f"💬 <b>Full Message:</b>\n<code>{sms_text[:300]}</code>"
                )
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🔄 Refresh OTP", callback_data=f"chk_{selected_num}"))
                bot.send_message(chat_id, response, reply_markup=markup)
            else:
                bot.send_message(chat_id, "⏳ <i>Abhi tak koi naya message nahi aaya hai. 10 second baad Check karein.</i>")
        else:
            bot.send_message(chat_id, "❌ Number record expired. Kripya naya number select karein.")

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("Bot is running with new token...")
    bot.infinity_polling(skip_pending=True)
