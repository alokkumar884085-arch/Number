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

user_active_numbers = {}

# ==========================================
# FLASK KEEP-ALIVE SYSTEM FOR RENDER
# ==========================================
@app.route('/')
def home():
    return "Bot Server Active with Full Multi-Server Directory!", 200

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

# ==========================================
# MULTI-SERVER PUBLIC SMS SCRAPERS
# ==========================================
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

def get_free_numbers():
    """Scrapes top high-availability public SMS sites."""
    numbers_list = []

    # Source 1: receive-smss.com
    try:
        url1 = "https://receive-smss.com"
        res1 = requests.get(url1, headers=HEADERS, timeout=5)
        if res1.status_code == 200:
            soup = BeautifulSoup(res1.text, 'html.parser')
            for card in soup.select('div.number-boxes-item'):
                num_tag = card.select_one('h4')
                country_tag = card.select_one('h5')
                link_tag = card.select_one('a')
                if num_tag and link_tag:
                    phone = num_tag.text.strip()
                    country = country_tag.text.strip() if country_tag else "Global"
                    detail_url = url1 + link_tag['href'] if not link_tag['href'].startswith("http") else link_tag['href']
                    numbers_list.append({"number": phone, "country": country, "url": detail_url, "source": "S1"})
    except Exception as e:
        logging.error(f"S1 Error: {e}")

    # Source 2: online-sms.org
    try:
        url2 = "https://online-sms.org"
        res2 = requests.get(url2, headers=HEADERS, timeout=5)
        if res2.status_code == 200:
            soup = BeautifulSoup(res2.text, 'html.parser')
            for card in soup.select('a.btn-number') or soup.select('div.col-lg-4'):
                num_text = card.text.strip()
                phone_matches = re.findall(r'\+\d{10,15}', num_text)
                href = card.get('href') or (card.find('a')['href'] if card.find('a') else '')
                if phone_matches and href:
                    detail_url = url2 + href if href.startswith('/') else href
                    numbers_list.append({"number": phone_matches[0], "country": "Public", "url": detail_url, "source": "S2"})
    except Exception as e:
        logging.error(f"S2 Error: {e}")

    # Source 3: receivesms.co
    try:
        url3 = "https://receivesms.co"
        res3 = requests.get(url3, headers=HEADERS, timeout=5)
        if res3.status_code == 200:
            soup = BeautifulSoup(res3.text, 'html.parser')
            for card in soup.select('div.mobile-card') or soup.select('a'):
                href = card.get('href', '')
                text = card.text.strip()
                phones = re.findall(r'\+\d{10,15}', text)
                if phones and ('/us/' in href or '/uk/' in href or 'receive' in href):
                    detail_url = url3 + href if href.startswith('/') else href
                    numbers_list.append({"number": phones[0], "country": "US/UK", "url": detail_url, "source": "S3"})
    except Exception as e:
        logging.error(f"S3 Error: {e}")

    # Source 4: receive-sms.cc
    try:
        url4 = "https://receive-sms.cc"
        res4 = requests.get(url4, headers=HEADERS, timeout=5)
        if res4.status_code == 200:
            soup = BeautifulSoup(res4.text, 'html.parser')
            for card in soup.select('div.number-boxes-item') or soup.select('a'):
                href = card.get('href', '')
                text = card.text.strip()
                phones = re.findall(r'\+\d{10,15}', text)
                if phones and href:
                    detail_url = url4 + href if href.startswith('/') else href
                    numbers_list.append({"number": phones[0], "country": "Global", "url": detail_url, "source": "S4"})
    except Exception as e:
        logging.error(f"S4 Error: {e}")

    return numbers_list

def get_latest_otp(number_url):
    """Scrapes latest SMS message from selected number page."""
    try:
        res = requests.get(number_url, headers=HEADERS, timeout=7)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.select('table tbody tr') or soup.select('div.table-row') or soup.select('div.msg-item')
            if rows:
                latest_row = rows[0]
                full_text = latest_row.text.strip()
                if len(full_text) > 3:
                    return full_text
    except Exception as e:
        logging.error(f"OTP Scraping Error: {e}")
    return None

def extract_code(text):
    """Extracts 4 to 8 digit OTP codes."""
    if not text:
        return None
    matches = re.findall(r'\b\d{4,8}\b', text)
    if matches:
        return matches[0]
    return None

# ==========================================
# TELEGRAM BOT HANDLERS
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("⚡ Auto-Fetch Virtual Numbers", callback_data="get_free_num"),
        types.InlineKeyboardButton("🌐 Free Public Web Directory (30+ Sites)", callback_data="dir_public"),
        types.InlineKeyboardButton("📱 Apps & Trial Credits (TextNow, Twilio)", callback_data="dir_apps"),
        types.InlineKeyboardButton("💎 Cheap / Paid Services (5SIM, SMSPVA)", callback_data="dir_paid")
    )
    
    welcome_text = (
        f"👋 <b>Welcome {message.from_user.first_name}!</b>\n\n"
        f"<b>SMS Verification Hub:</b>\n"
        f"• <b>Auto-Fetch:</b> Instant live numbers & OTPs\n"
        f"• <b>Web Directory:</b> All top 40+ SMS provider sites & apps"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id

    # --- AUTO SCRAPER ---
    if call.data == "get_free_num":
        bot.answer_callback_query(call.id, "Searching live servers...")
        numbers = get_free_numbers()
        
        if not numbers:
            bot.send_message(
                chat_id, 
                "❌ <i>Servers high load par hain. Web Directory button use karke direct site par try karein.</i>"
            )
            return
            
        markup = types.InlineKeyboardMarkup(row_width=1)
        for item in numbers[:10]:
            btn_text = f"[{item['source']}] 🌐 {item['country']} : {item['number']}"
            user_active_numbers[item['number']] = item['url']
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"sel_{item['number']}"))
        markup.add(types.InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu"))
            
        bot.edit_message_text(
            "👇 <b>Select any available Number:</b>",
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
            f"📱 <b>NUMBER:</b> <code>{selected_num}</code>\n\n"
            f"1️⃣ Number copy karke application me dalein.\n"
            f"2️⃣ Single click me OTP lene ke liye <b>Check OTP</b> par click karein."
        )
        bot.send_message(chat_id, text, reply_markup=markup)

    elif call.data.startswith("chk_"):
        selected_num = call.data.split("_")[1]
        number_url = user_active_numbers.get(selected_num)
        
        bot.answer_callback_query(call.id, "Reading inbox...")
        
        if not number_url:
            numbers = get_free_numbers()
            for item in numbers:
                if item['number'] == selected_num:
                    number_url = item['url']
                    break

        if number_url:
            sms_text = get_latest_otp(number_url)
            if sms_text:
                otp_code = extract_code(sms_text)
                
                if otp_code:
                    response = (
                        f"📱 <b>NUMBER:</b> <code>{selected_num}</code>\n\n"
                        f"🔑 <b>YOUR OTP CODE:</b>\n"
                        f"<code>{otp_code}</code>\n\n"
                        f"💬 <b>Full SMS:</b>\n<code>{sms_text[:250]}</code>"
                    )
                else:
                    response = (
                        f"📱 <b>NUMBER:</b> <code>{selected_num}</code>\n\n"
                        f"💬 <b>RECEIVED SMS:</b>\n<code>{sms_text[:300]}</code>"
                    )

                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🔄 Refresh OTP", callback_data=f"chk_{selected_num}"))
                markup.add(types.InlineKeyboardButton("📱 Select New Number", callback_data="get_free_num"))
                bot.send_message(chat_id, response, reply_markup=markup)
            else:
                bot.send_message(chat_id, "⏳ <i>Naya message abhi nahi aaya. 10 second baad 'Check OTP' dabayein.</i>")
        else:
            bot.send_message(chat_id, "❌ Session expired. Main menu se naya number chunein.")

    # --- MAIN MENU / DIRECTORY HANDLERS ---
    elif call.data == "main_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("⚡ Auto-Fetch Virtual Numbers", callback_data="get_free_num"),
            types.InlineKeyboardButton("🌐 Free Public Web Directory (30+ Sites)", callback_data="dir_public"),
            types.InlineKeyboardButton("📱 Apps & Trial Credits (TextNow, Twilio)", callback_data="dir_apps"),
            types.InlineKeyboardButton("💎 Cheap / Paid Services (5SIM, SMSPVA)", callback_data="dir_paid")
        )
        bot.edit_message_text("👋 <b>Main Menu:</b> Select an option below.", chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)

    elif call.data == "dir_public":
        text = (
            "🌐 <b>Free Public SMS Sites List:</b>\n\n"
            "• <a href='https://receive-a-sms.com'>Receive A SMS</a>\n"
            "• <a href='https://smsreceivefree.com'>SMS Receive Free</a>\n"
            "• <a href='https://sms-online.co'>Online SMS</a>\n"
            "• <a href='https://smsreceiveonline.com'>SMS Receive Online</a>\n"
            "• <a href='https://getfreesmsnumber.com'>Get Free SMS Number</a>\n"
            "• <a href='http://sms-receive.net'>SMS Receive Net</a>\n"
            "• <a href='https://www.receivesmsonline.net'>Receive SMS Online NET</a>\n"
            "• <a href='http://7sim.net'>7SIM Net</a>\n"
            "• <a href='http://receivefreesms.com'>Receive Free SMS</a>\n"
            "• <a href='https://receive-sms-online.com'>Receive SMS Online</a>\n"
            "• <a href='https://5sim.net'>5SIM Free Section</a>\n"
            "• <a href='https://anon-sms.com'>Anon SMS</a>\n"
            "• <a href='https://catchsms.com'>Catch SMS</a>\n"
            "• <a href='http://getsms.org'>Get SMS Org</a>\n"
            "• <a href='https://virtty.com'>Virtty SMS</a>\n"
            "• <a href='https://freevirtualsmsnumber.com'>Free Virtual SMS Number</a>\n"
            "• <a href='https://freesmscode.com'>Free SMS Code</a>\n"
            "• <a href='https://es.mytrashmobile.com/nu'>Trash Mobile</a>"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu"))
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup, disable_web_page_preview=True)

    elif call.data == "dir_apps":
        text = (
            "📱 <b>Apps & Free Trial Credits:</b>\n\n"
            "1. <b>TextNow:</b> Real US/Canada numbers via app/web\n"
            "🔗 <a href='https://www.textnow.com/'>TextNow Web</a>\n\n"
            "2. <b>Twilio:</b> Free trial credits for dedicated numbers\n"
            "🔗 <a href='https://www.twilio.com/'>Twilio Signup</a>\n\n"
            "3. <b>SMSCodes.io:</b> Free trial credits available\n"
            "🔗 <a href='https://www.smscodes.io/'>SMSCodes Web</a>\n\n"
            "4. <b>Pinger:</b> Virtual phone numbers app\n"
            "🔗 <a href='https://www.pinger.com'>Pinger Web</a>"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu"))
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup, disable_web_page_preview=True)

    elif call.data == "dir_paid":
        text = (
            "💎 <b>Cheapest Paid / API SMS Services (Starts at few cents):</b>\n\n"
            "• <a href='https://5sim.net'>5SIM.net</a> (Most Popular)\n"
            "• <a href='https://onlinesim.ru'>OnlineSIM.ru</a>\n"
            "• <a href='http://www.smspva.com/'>SMSPVA</a>\n"
            "• <a href='https://pingme.tel/'>PingMe Tel</a>\n"
            "• <a href='https://www.proovl.com/numbers'>Proovl Numbers</a>"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu"))
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup, disable_web_page_preview=True)

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("Bot is running with Scrapers & Directory List...")
    bot.infinity_polling(skip_pending=True)
