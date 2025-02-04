from telegram import Update
from telegram.ext import ContextTypes
import os

OWNER_ID = int(os.getenv('OWNER_ID', '0'))  # Telegram user ID of bot owner

class CommandHandlers:
    def __init__(self, message_forwarder):
        self.message_forwarder = message_forwarder

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Hello! I am a message forwarding bot. Use /help to see available commands.')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
Available commands:
/setsource <channel_id> - Set the source channel/group/forum ID
/setdestination <channel_id> - Set the destination channel ID
/config - Show current configuration
/help - Show this help message
"""
        await update.message.reply_text(help_text)

    async def set_source(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("You're not authorized to use this command.")
            return

        if not context.args:
            await update.message.reply_text("Please provide the source channel/group/forum ID.")
            return

        try:
            self.message_forwarder.config_manager.config['source_id'] = int(context.args[0])
            self.message_forwarder.config_manager.save_config()
            await update.message.reply_text(f"Source ID set to: {self.message_forwarder.config_manager.config['source_id']}")
        except ValueError:
            await update.message.reply_text("Please provide a valid numeric ID.")

    async def set_destination(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("You're not authorized to use this command.")
            return

        if not context.args:
            await update.message.reply_text("Please provide the destination channel ID.")
            return

        try:
            self.message_forwarder.config_manager.config['destination_id'] = int(context.args[0])
            self.message_forwarder.config_manager.save_config()
            await update.message.reply_text(f"Destination ID set to: {self.message_forwarder.config_manager.config['destination_id']}")
        except ValueError:
            await update.message.reply_text("Please provide a valid numeric ID.")

    async def show_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("You're not authorized to use this command.")
            return

        config_text = f"Source ID: {self.message_forwarder.config_manager.config['source_id']}\nDestination ID: {self.message_forwarder.config_manager.config['destination_id']}"
        await update.message.reply_text(config_text)
