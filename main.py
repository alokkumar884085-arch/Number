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
BOT_TOKEN = "8856008829:AAHgne9V0zbxiSb67FUKNKIQM1x89_Lk1QY"
PORT = int(os.environ.get("PORT", 8080))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_URL = "https://receive-smss.com"

# Temporary database to store user numbers
user_active_numbers = {}

# ==========================================
# FLASK KEEP-ALIVE
# ==========================================
@app.route('/')
def home():
    return "Bot is active!", 200

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

# ==========================================
# FREE NUMBERS & OTP SCRAPER FUNCTIONS
# ==========================================
def get_free_numbers():
    """Website se live free numbers ki list nikalta hai."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(BASE_URL, headers=headers, timeout=10)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            numbers_list = []
            
            # Extract number boxes
            for card in soup.select('div.number-boxes-item'):
                num_tag = card.select_one('h4')
                country_tag = card.select_one('h5')
                link_tag = card.select_one('a')
                
                if num_tag and link_tag:
                    phone_number = num_tag.text.strip()
                    country = country_tag.text.strip() if country_tag else "Unknown"
                    detail_page = BASE_URL + link_tag['href'] if not link_tag['href'].startswith("http") else link_tag['href']
                    
                    numbers_list.append({
                        "number": phone_number,
                        "country": country,
                        "url": detail_page
                    })
            return numbers_list
    except Exception as e:
        logging.error(f"Scraping Error: {e}")
    return []

def get_latest_otp(number_url):
    """Number ke inbox page se latest OTP SMS fetch karta hai."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(number_url, headers=headers, timeout=10)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # Look for table rows containing SMS
            rows = soup.select('table tbody tr')
            if rows:
                latest_row = rows[0]
                cols = latest_row.find_all('td')
                if len(cols) >= 2:
                    sms_text = cols[1].text.strip()
                    return sms_text
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
        bot.answer_callback_query(call.id, "Fetching live numbers...")
        numbers = get_free_numbers()
        
        if not numbers:
            bot.send_message(chat_id, "❌ <i>Abhi koi free number available nahi hai. Thodi der baad try karein.</i>")
            return
            
        markup = types.InlineKeyboardMarkup(row_width=1)
        for item in numbers[:10]: # Top 10 numbers show karega
            btn_text = f"🌐 {item['country']} : {item['number']}"
            # Short callback storing index/url
            callback_id = f"sel_{item['number']}"
            user_active_numbers[item['number']] = item['url']
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=callback_id))
            
        bot.edit_message_text(
            "👇 <b>Select a Virtual Number from below:</b>",
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=markup
        )

    elif call.data.startswith("sel_"):
        selected_num = call.data.split("_")[1]
        number_url = user_active_numbers.get(selected_num)
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📩 Check OTP", callback_data=f"chk_{selected_num}"))
        markup.add(types.InlineKeyboardButton("🔄 Back to List", callback_data="get_free_num"))
        
        text = (
            f"✅ <b>Number Selected!</b>\n\n"
            f"📱 <b>Number:</b> <code>{selected_num}</code>\n\n"
            f"Is number ko aap app me dalein, fir niche <b>Check OTP</b> par click karein."
        )
        bot.send_message(chat_id, text, reply_markup=markup)

    elif call.data.startswith("chk_"):
        selected_num = call.data.split("_")[1]
        number_url = user_active_numbers.get(selected_num)
        
        bot.answer_callback_query(call.id, "Checking latest SMS...")
        
        if not number_url:
            # Fallback re-fetch URL if missing
            numbers = get_free_numbers()
            for item in numbers:
                if item['number'] == selected_num:
                    number_url = item['url']
                    break

        if number_url:
            sms_text = get_latest_otp(number_url)
            if sms_text:
                # Digits extract karne ke liye
                digits = re.findall(r'\b\d{4,8}\b', sms_text)
                code_text = f"<code>{digits[0]}</code>" if digits else "N/A"

                response = (
                    f"📩 <b>Latest SMS Received!</b>\n\n"
                    f"📱 <b>Number:</b> <code>{selected_num}</code>\n"
                    f"🔑 <b>Extracted Code:</b> {code_text}\n\n"
                    f"💬 <b>Message Content:</b>\n<code>{sms_text}</code>"
                )
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🔄 Refresh OTP", callback_data=f"chk_{selected_num}"))
                bot.send_message(chat_id, response, reply_markup=markup)
            else:
                bot.send_message(chat_id, "⏳ <i>Abhi tak koi naya message nahi aaya hai. 10 second baad dobara Check karein.</i>")
        else:
            bot.send_message(chat_id, "❌ Number link expired. Kripya naya number chunen.")

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("Bot is running...")
    bot.infinity_polling(skip_pending=True)
