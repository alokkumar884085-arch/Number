import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ------------------- CONFIG -------------------
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # @BotFather se lo

# ------------------- LOGGING -------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------------- START COMMAND -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔥 Free Fire Like", callback_data='ff')],
        [InlineKeyboardButton("🚗 Vehicle Info", callback_data='vehicle')],
        [InlineKeyboardButton("📸 Instagram Profile", callback_data='insta')],
        [InlineKeyboardButton("ℹ️ About", callback_data='about')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 **Welcome to Multi-Bot!**\n\n"
        "Choose an option below 👇",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ------------------- BUTTON HANDLER -------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'ff':
        await query.edit_message_text(
            "🔥 **Free Fire Like Bot**\n\n"
            "Send /like UID\n"
            "Example: `/like 2599674268`",
            parse_mode="Markdown"
        )
    elif query.data == 'vehicle':
        await query.edit_message_text(
            "🚗 **Vehicle Info Bot**\n\n"
            "Send /vehicle REGISTRATION_NUMBER\n"
            "Example: `/vehicle MH12AB1234`",
            parse_mode="Markdown"
        )
    elif query.data == 'insta':
        await query.edit_message_text(
            "📸 **Instagram Profile Bot**\n\n"
            "Send /insta USERNAME\n"
            "Example: `/insta modxpatel`",
            parse_mode="Markdown"
        )
    elif query.data == 'about':
        await query.edit_message_text(
            "🤖 **Multi-Bot v1.0**\n\n"
            "Features:\n"
            "✅ Free Fire Likes\n"
            "✅ Vehicle Info (India)\n"
            "✅ Instagram Profile Viewer\n\n"
            "👨‍💻 Developer: @modxpatel\n"
            "🔗 Source: GitHub",
            parse_mode="Markdown"
        )

# ------------------- FREE FIRE LIKE -------------------
async def like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ **Error!**\n\n"
            "Usage: `/like UID`\n"
            "Example: `/like 2599674268`",
            parse_mode="Markdown"
        )
        return
    
    uid = context.args[0]
    if not uid.isdigit():
        await update.message.reply_text("❌ UID must be a number! Example: `2599674268`", parse_mode="Markdown")
        return
    
    # Send processing message
    msg = await update.message.reply_text("⏳ Sending likes... Please wait")
    
    url = f"http://187.127.175.208:5002/like?uid={uid}&server_name=IND"
    
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        
        # Try to extract success message
        success = data.get('success', False)
        message = data.get('message', 'No response message')
        
        if response.status_code == 200 or success:
            await msg.edit_text(
                f"✅ **Likes Sent Successfully!**\n\n"
                f"👤 UID: `{uid}`\n"
                f"📊 Status: {message}\n"
                f"🌐 Server: IND",
                parse_mode="Markdown"
            )
        else:
            await msg.edit_text(
                f"❌ **Failed to send likes**\n\n"
                f"📊 Response: {message}\n"
                f"🆘 Try again later.",
                parse_mode="Markdown"
            )
    except requests.exceptions.Timeout:
        await msg.edit_text("⏰ **Timeout!** The server is not responding. Try again later.", parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"⚠️ **Error:** `{str(e)}`", parse_mode="Markdown")
        logger.error(f"Free Fire Error: {e}")

# ------------------- VEHICLE INFO -------------------
async def vehicle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ **Error!**\n\n"
            "Usage: `/vehicle REG_NUMBER`\n"
            "Example: `/vehicle MH12AB1234`",
            parse_mode="Markdown"
        )
        return
    
    reg = context.args[0].upper().strip()
    msg = await update.message.reply_text("⏳ Fetching vehicle details...")
    
    url = f"https://patel-car-info-api.vercel.app/details={reg}"
    
    try:
        response = requests.get(url, timeout=20)
        data = response.json()
        
        if "error" in data or "message" in data and "not found" in data.get("message", "").lower():
            await msg.edit_text(f"❌ **Vehicle not found!**\n\nRegistration: `{reg}`", parse_mode="Markdown")
            return
        
        # Extract details
        owner = data.get("Owner Details", {})
        vehicle = data.get("Vehicle Details", {})
        registration = data.get("Registration Details", {})
        insurance = data.get("Insurance Details", {})
        compliance = data.get("Compliance Details", {})
        
        reply = f"""
🚗 **Vehicle Information: `{reg}`**

👤 **Owner Details:**
• Name: `{owner.get('Owner Name', 'N/A')}`
• City: `{owner.get('City Name', 'N/A')}`
• Address: `{owner.get('Address', 'N/A')}`
• Owner No: `{owner.get('Owner Serial No', 'N/A')}`

🚲 **Vehicle Details:**
• Model: `{vehicle.get('Modal Name', 'N/A')}`
• Maker: `{vehicle.get('Maker Model', 'N/A')}`
• Class: `{vehicle.get('Vehicle Class', 'N/A')}`
• Fuel: `{vehicle.get('Fuel Type', 'N/A')}`
• CC: `{vehicle.get('Cubic Capacity', 'N/A')}`
• Seating: `{vehicle.get('Seating Capacity', 'N/A')}`
• Age: `{vehicle.get('Vehicle Age', 'N/A')}`

🏛️ **Registration:**
• RTO: `{registration.get('Registered RTO', 'N/A')}`
• Date: `{registration.get('Registration Date', 'N/A')}`
• Phone: `{registration.get('RTO Phone Number', 'N/A')}`

🛡️ **Insurance:**
• Company: `{insurance.get('Insurance Company', 'N/A')}`
• Expiry: `{insurance.get('Insurance Expiry', 'N/A')}`
• Valid: `{insurance.get('Insurance Valid Upto', 'N/A')}`

✅ **Compliance:**
• Fitness: `{compliance.get('Fitness Upto', 'N/A')}`
• Tax: `{compliance.get('Tax Upto', 'N/A')}`
        """
        
        await msg.edit_text(reply, parse_mode="Markdown")
        
    except requests.exceptions.Timeout:
        await msg.edit_text("⏰ **Timeout!** API not responding. Try again.", parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"⚠️ **Error:** `{str(e)}`", parse_mode="Markdown")
        logger.error(f"Vehicle Error: {e}")

# ------------------- INSTAGRAM PROFILE VIEWER -------------------
async def insta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ **Error!**\n\n"
            "Usage: `/insta USERNAME`\n"
            "Example: `/insta modxpatel`",
            parse_mode="Markdown"
        )
        return
    
    username = context.args[0].strip()
    msg = await update.message.reply_text("⏳ Fetching Instagram profile...")
    
    url = f"https://www.instagram.com/{username}/?__a=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            await msg.edit_text(f"❌ **Profile not found or private!**\n\nUsername: `{username}`", parse_mode="Markdown")
            return
        
        data = response.json()
        user = data.get("graphql", {}).get("user", {})
        
        if not user:
            await msg.edit_text(f"❌ **User not found!**\n\nUsername: `{username}`", parse_mode="Markdown")
            return
        
        full_name = user.get('full_name', 'N/A')
        bio = user.get('biography', 'N/A')
        followers = user.get('edge_followed_by', {}).get('count', 0)
        following = user.get('edge_follow', {}).get('count', 0)
        posts = user.get('edge_owner_to_timeline_media', {}).get('count', 0)
        is_private = user.get('is_private', False)
        is_verified = user.get('is_verified', False)
        profile_pic = user.get('profile_pic_url_hd', user.get('profile_pic_url', ''))
        
        reply = f"""
📸 **Instagram Profile: `@{username}`**

👤 **Name:** `{full_name}`
📝 **Bio:** {bio[:100]}{'...' if len(bio) > 100 else ''}

📊 **Stats:**
• Followers: `{followers:,}`
• Following: `{following:,}`
• Posts: `{posts:,}`

🔒 **Private:** `{'Yes' if is_private else 'No'}`
✅ **Verified:** `{'Yes' if is_verified else 'No'}`

🔗 **Profile:** https://www.instagram.com/{username}/
        """
        
        await msg.edit_text(reply, parse_mode="Markdown")
        
    except requests.exceptions.Timeout:
        await msg.edit_text("⏰ **Timeout!** Instagram not responding. Try again.", parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"⚠️ **Error:** `{str(e)}`", parse_mode="Markdown")
        logger.error(f"Instagram Error: {e}")

# ------------------- HELP COMMAND -------------------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📚 **Available Commands:**

/start - Show main menu
/help - Show this help

🔥 **Free Fire:**
/like UID - Send likes to Free Fire profile
Example: `/like 2599674268`

🚗 **Vehicle Info:**
/vehicle REG_NUMBER - Get Indian vehicle details
Example: `/vehicle MH12AB1234`

📸 **Instagram:**
/insta USERNAME - Get Instagram profile info
Example: `/insta modxpatel`

👨‍💻 **Developer:** @modxpatel
    """
    await update.message.reply_text(help_text, parse_mode="Markdown")

# ------------------- ERROR HANDLER -------------------
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    try:
        await update.message.reply_text("⚠️ **An error occurred!** Please try again later.", parse_mode="Markdown")
    except:
        pass

# ------------------- MAIN FUNCTION -------------------
def main():
    print("🤖 Bot Starting...")
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("like", like))
    app.add_handler(CommandHandler("vehicle", vehicle))
    app.add_handler(CommandHandler("insta", insta))
    
    # Add callback handler for buttons
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Add error handler
    app.add_error_handler(error_handler)
    
    print("✅ Bot is running! Press Ctrl+C to stop.")
    
    # Start the bot
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
