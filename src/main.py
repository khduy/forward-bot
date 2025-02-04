import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
from core.message_forwarder import MessageForwarder
from handlers.command_handlers import CommandHandlers

# Load environment variables
load_dotenv()

# Enhanced logging configuration with file handler
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()  # Log to console
    ]
)
logger = logging.getLogger(__name__)

# Constants section
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Telegram Bot API token from .env file

def main():
    if not BOT_TOKEN:
        logger.error("Bot token not found in environment variables!")
        return

    # Initialize core components
    forwarder = MessageForwarder()
    command_handlers = CommandHandlers(forwarder)
    
    # Initialize application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", command_handlers.start))
    application.add_handler(CommandHandler("help", command_handlers.help_command))
    application.add_handler(CommandHandler("setsource", command_handlers.set_source))
    application.add_handler(CommandHandler("setdestination", command_handlers.set_destination))
    application.add_handler(CommandHandler("config", command_handlers.show_config))
    
    # Add message handler for forwarding
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forwarder.forward_message))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
