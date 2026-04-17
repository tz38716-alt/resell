# main.py

import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.constants import ParseMode

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# IMPORTANT: Replace these with your actual Bot Token and Admin User ID
TOKEN = '8500530484:AAF1DGohab5lxPiDnFmoBMjJ4LG21es-dFQ' 
ADMIN_ID = 6931544887  # Replace with your numeric Admin User ID

# --- DATA STORAGE (In-memory) ---
# For a real-world bot, you should use a database (e.g., SQLite, PostgreSQL) to persist data.
user_states = {}          # Stores the current state of each user's order
approved_resellers = {ADMIN_ID} # Set of user IDs who are approved resellers. Admin is always approved.
pending_approvals = {}    # Stores user info for pending reseller requests

# --- KEYBOARD LAYOUTS ---

def get_main_menu_keyboard():
    """Returns the main menu keyboard layout."""
    keyboard = [
        [InlineKeyboardButton("Discover Products", callback_data='discover_products')],
        [InlineKeyboardButton("Admin", url='t.me/minkhant8792'), InlineKeyboardButton("Main Menu", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_discover_products_keyboard():
    """Returns the product selection keyboard."""
    keyboard = [
        [InlineKeyboardButton("Express VPN", callback_data='p_expressvpn')],
        [InlineKeyboardButton("ChatGPT", callback_data='p_chatgpt')],
        [InlineKeyboardButton("Spotify", callback_data='p_spotify')],
        [InlineKeyboardButton("Capcut", callback_data='p_capcut')],
        [InlineKeyboardButton("Alightmotion", callback_data='p_alightmotion')],
        [InlineKeyboardButton("<< Back", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- START & HELP COMMANDS ---

async def start_command(update: Update, context) -> None:
    """Handles the /start command. Checks if the user is an approved reseller."""
    user = update.effective_user
    if user.id in approved_resellers:
        await update.message.reply_text(
            "သင်သည် Reseller ဖြစ်ပြီးဖြစ်သောကြောင့် Product များနှင့် ဈေးနှုန်းများကို ကြည့်ရှုနိုင်ပါပြီ။",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        pending_approvals[user.id] = user.full_name
        await update.message.reply_text(
            "သင်သည် Reseller မဟုတ်သည့်အတွက် ဤ Bot ကိုအသုံးပြုခွင့်မရှိပါ။\n"
            "Reseller ယူမည်ဆိုပါက Admin ၏ လက်ခံမှုလိုအပ်ပါသည်။\n"
            "ခွင့်ပြုချက်ရရန် Admin ကို ဆက်သွယ်ပါ။ @minkhant8792"
        )
        # Notify Admin
        keyboard = [[InlineKeyboardButton("Approve", callback_data=f'approve_{user.id}'), InlineKeyboardButton("Reject", callback_data=f'reject_{user.id}')]]
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"<b>New Reseller Request</b>\nUser: {user.mention_html()}\nID: <code>{user.id}</code>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )

# --- CALLBACK QUERY HANDLER (Button Clicks) ---

async def button_handler(update: Update, context) -> None:
    """Handles all button clicks from inline keyboards."""
    query = update.callback_query
    await query.answer() # Acknowledge the button press
    user_id = query.from_user.id
    data = query.data

    # --- Admin Actions ---
    if data.startswith(('approve_', 'reject_')):
        if user_id != ADMIN_ID: return
        action, target_user_id_str = data.split('_')
        target_user_id = int(target_user_id_str)
        
        if action == 'approve':
            approved_resellers.add(target_user_id)
            if target_user_id in pending_approvals: del pending_approvals[target_user_id]
            await context.bot.send_message(target_user_id, "သင်သည် Reseller ဖြစ်သွားပါပြီ။ Product များကို ကြည့်ရှုနိုင်ပါပြီ။", reply_markup=get_main_menu_keyboard())
            await query.edit_message_text(f"User {target_user_id} has been approved.")
        else: # Reject
            if target_user_id in pending_approvals: del pending_approvals[target_user_id]
            await context.bot.send_message(target_user_id, "Access Denied. သင်၏ Reseller တောင်းဆိုမှုကို ပယ်ချလိုက်ပါသည်။ ❌")
            await query.edit_message_text(f"User {target_user_id} has been rejected.")
        return

    # --- Reseller-Only Area ---
    if user_id not in approved_resellers:
        await query.edit_message_text("သင်သည် Reseller မဟုတ်သည့်အတွက် အသုံးပြုခွင့်မရှိပါ။")
        return

    # --- Menu Navigation ---
    if data == 'main_menu':
        await query.edit_message_text("Main Menu", reply_markup=get_main_menu_keyboard())
    elif data == 'discover_products':
        await query.edit_message_text("Please select a product category:", reply_markup=get_discover_products_keyboard())
    
    # --- Product Selection ---
    products = {
        'p_expressvpn': ("Express VPN", [[InlineKeyboardButton("1 Month - 1500ks", callback_data='buy_expressvpn_1m')], [InlineKeyboardButton("1 Year - 15000ks", callback_data='buy_expressvpn_1y')]]),
        'p_chatgpt': ("ChatGPT", [[InlineKeyboardButton("1 Month - 10000ks", callback_data='buy_chatgpt_1m')]]),
        'p_spotify': ("Spotify", [[InlineKeyboardButton("Individual 2 Months - 13000ks", callback_data='buy_spotify_2m')]]),
        'p_capcut': ("Capcut", [[InlineKeyboardButton("30-35 Days - 8000ks", callback_data='buy_capcut_30d')]]),
        'p_alightmotion': ("Alightmotion", [[InlineKeyboardButton("1 Year (Private) - 6500ks", callback_data='buy_alightmotion_1y')]])
    }
    if data in products:
        name, keyboard_layout = products[data]
        keyboard_layout.append([InlineKeyboardButton("<< Back", callback_data='discover_products')])
        await query.edit_message_text(f"Select a plan for {name}:", reply_markup=InlineKeyboardMarkup(keyboard_layout))

    # --- Purchase Flow ---
    purchase_options = {
        'buy_expressvpn_1m': {"name": "Express VPN 1 Month", "price": "1500ks", "duration": "N/A"},
        'buy_expressvpn_1y': {"name": "Express VPN 1 Year", "price": "15000ks", "duration": "N/A"},
        'buy_chatgpt_1m': {"name": "ChatGPT 1 Month", "price": "10000ks", "duration": "၃၀ မိနစ်"},
        'buy_spotify_2m': {"name": "Spotify Individual 2 Months", "price": "13000ks", "duration": "N/A"},
        'buy_capcut_30d': {"name": "Capcut 30-35 Days", "price": "8000ks", "duration": "၅ မိနစ်"},
        'buy_alightmotion_1y': {"name": "Alightmotion 1 Year (Private)", "price": "6500ks", "duration": "30 မိနစ်"}
    }
    if data in purchase_options:
        option = purchase_options[data]
        order_id = f"ORDER-{int(time.time())}-{user_id % 1000}"
        user_states[user_id] = {'order_id': order_id, 'product_name': option['name'], 'status': 'pending_payment'}
        
        notice = ""
        if 'alightmotion' in data: notice = "<b>Notice:</b> Own Mail ဖြင့်ယူမည်ဆိုပါက Admin ဆီ Mail ပို့ပေးပါ။\n"

        payment_info = (
            f"<b>Order Details</b>\n"
            f"Order ID: <code>{order_id}</code>\n"
            f"Product: {option['name']}\n"
            f"Price: {option['price']}\n"
            f"{f'Est. Time: {option['duration']}\n' if option['duration'] != 'N/A' else ''}"
            f"{notice}"
            f"\n<b>Payment Methods</b>\n"
            f"Kpay/Wave: <code>09682764695</code> (Thant Zin Maung)\n"
            f"<pre>Note: 'Payment' ဟုသာရေးပါ။ အခြား Note ရေးပါက Ban ပါမည်။</pre>\n"
            f"ငွေလွှဲပြီးပါက ပြေစာကို ဤနေရာသို့ ပို့ပေးပါ။"
        )
        await query.edit_message_text(payment_info, parse_mode=ParseMode.HTML)

# --- RECEIPT HANDLING ---

async def receipt_handler(update: Update, context) -> None:
    """Handles incoming photos, assuming they are receipts for pending payments."""
    user = update.effective_user
    if user.id not in user_states or user_states[user.id]['status'] != 'pending_payment':
        return

    user_state = user_states[user.id]
    user_state['status'] = 'receipt_sent'
    await update.message.reply_text("Verifying Receipt... ⏳")

    keyboard = [[InlineKeyboardButton("✅ Verify", callback_data=f'verify_{user.id}'), InlineKeyboardButton("❌ Reject", callback_data=f'reject_receipt_{user.id}')]]
    caption = (
        f"<b>Receipt Verification</b>\n"
        f"User: {user.mention_html()} (<code>{user.id}</code>)\n"
        f"Order ID: <code>{user_state['order_id']}</code>\n"
        f"Product: {user_state['product_name']}"
    )
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def receipt_action_handler(update: Update, context) -> None:
    """Handles admin's verification or rejection of a receipt."""
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID: return

    action, target_user_id_str = query.data.split('_', 1)[0], query.data.split('_')[-1]
    target_user_id = int(target_user_id_str)

    if target_user_id not in user_states:
        await query.edit_message_text("User state not found. Maybe the order was already processed.")
        return

    if action == 'verify':
        user_states[target_user_id]['status'] = 'verified'
        await context.bot.send_message(target_user_id, "✅ Verification successful! Please wait while we prepare your product...")
        await query.edit_message_caption(caption=query.message.caption + "\n\n<b>Status: ✅ Verified</b>", parse_mode=ParseMode.HTML)
    else: # Reject
        user_states[target_user_id]['status'] = 'pending_payment' # Allow user to resubmit
        await context.bot.send_message(target_user_id, "❌ Your receipt was rejected. Please check and send the correct one.")
        await query.edit_message_caption(caption=query.message.caption + "\n\n<b>Status: ❌ Rejected</b>", parse_mode=ParseMode.HTML)

# --- ADMIN COMMANDS ---

async def admin_command_wrapper(update: Update, context, command_func):
    """Wrapper to check for admin privileges before executing a command."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("This is an admin-only command.")
        return
    await command_func(update, context)

async def product_command(update: Update, context) -> None:
    """Usage: /product <user_id> <info> - Sends product info to a verified user."""
    try:
        _, user_id_str, *info_parts = update.message.text.split()
        user_id = int(user_id_str)
        info = ' '.join(info_parts)
        if not info: raise ValueError
        
        if user_id in user_states and user_states[user_id]['status'] == 'verified':
            await context.bot.send_message(user_id, f"Here is your product info:\n\n{info}")
            await update.message.reply_text(f"Product info sent to user {user_id}.")
            del user_states[user_id] # Clean up state
        else:
            await update.message.reply_text("User has not been verified for any product.")
    except (ValueError, IndexError):
        await update.message.reply_text("Usage: /product <user_id> <product_info>")

async def ban_command(update: Update, context) -> None:
    """Usage: /ban <user_id> - Bans a user from the bot."""
    try:
        target_user_id = int(context.args[0])
        if target_user_id in approved_resellers:
            approved_resellers.remove(target_user_id)
            await update.message.reply_text(f"User {target_user_id} has been banned.")
            await context.bot.send_message(target_user_id, "You have been banned from this bot.")
        else:
            await update.message.reply_text("User is not an approved reseller.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /ban <user_id>")

async def unban_command(update: Update, context) -> None:
    """Usage: /unban <user_id> - Unbans a user."""
    try:
        target_user_id = int(context.args[0])
        if target_user_id not in approved_resellers:
            approved_resellers.add(target_user_id)
            await update.message.reply_text(f"User {target_user_id} has been unbanned.")
            await context.bot.send_message(target_user_id, "You have been unbanned and can now use the bot.")
        else:
            await update.message.reply_text("User is already an approved reseller.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /unban <user_id>")

async def broadcast_command(update: Update, context) -> None:
    """Usage: /broadcast <message> - Sends a message to all approved resellers."""
    message = ' '.join(context.args)
    if not message:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    
    count = 0
    for user_id in approved_resellers:
        try:
            await context.bot.send_message(user_id, message)
            count += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
    await update.message.reply_text(f"Broadcast sent to {count} reseller(s).")

# --- MAIN FUNCTION ---

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("product", lambda u, c: admin_command_wrapper(u, c, product_command)))
    application.add_handler(CommandHandler("ban", lambda u, c: admin_command_wrapper(u, c, ban_command)))
    application.add_handler(CommandHandler("unban", lambda u, c: admin_command_wrapper(u, c, unban_command)))
    application.add_handler(CommandHandler("broadcast", lambda u, c: admin_command_wrapper(u, c, broadcast_command)))

    # Callback Query Handlers
    application.add_handler(CallbackQueryHandler(receipt_action_handler, pattern='^(verify|reject_receipt)_'))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Message Handlers
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, receipt_handler))

    # Run the bot
    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
