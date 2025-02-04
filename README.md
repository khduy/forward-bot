# Telegram Message Forwarding Bot

This is a Telegram bot that automatically forwards messages from a source channel/group to a designated destination channel/group.

## Features

-   **Forwards Messages:** Sends messages from a source to a destination.
-   **Handles Media Groups:** Keeps media groups together and forwards them as a single message.


## Setup and Installation

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/khduy/forward-bot.git
    cd forward-bot
    ```

2. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Environment Variables:**
    -   Create a `.env` file in the root directory.
    -   Add the following:

        ```
        BOT_TOKEN=<your_bot_token>
        OWNER_ID=<your_telegram_user_id>
        ```

        -   Replace `<your_bot_token>` with the token from BotFather.
        -   Replace `<your_telegram_user_id>` with your Telegram user ID (use a bot like `@userinfobot` to find it).

4. **Configuration:**
    -   `config.json` is created automatically when you set source and destination IDs.
    -   **Source ID:** ID of where to forward messages from (use negative IDs for channels/groups, e.g., `-1001234567890`).
    -   **Destination ID:** ID of where messages will be forwarded to.

5. **Running the Bot:**

    ```bash
    python src/main.py
    ```

## Usage

1. **Start the bot:** Send `/start` to the bot in Telegram.
2. **Set the source:**
    -   `/setsource <source_channel_id>` (bot must be in the source channel/group).
3. **Set the destination:**
    -   `/setdestination <destination_channel_id>` (bot must be an admin in the destination channel).
4. **View config:** `/config`
5. **Help:** `/help`

## Notes

-   The bot forwards messages that arrive *after* setup.
-   Ensure the bot has needed permissions.
-   Constants like `MEDIA_GROUP_TIMEOUT`, `MAX_RETRIES` can be adjusted in `message_forwarder.py`.

## Troubleshooting

-   **"Bot token not found..." error:** Check your `.env` file and `BOT_TOKEN`.
-   **"You're not authorized..." error:** Make sure `OWNER_ID` in `.env` is your Telegram ID.
-   **Messages not being forwarded:**
    -   Check source/destination IDs.
    -   Ensure the bot has correct permissions.
    -   Look for errors in the console log.
-   **"Failed to forward media group..." error:** Usually a network or Telegram API issue. Try again later.
-   **Other errors:** The console log will have more details.

## Disclaimer

This bot is provided as-is. Use it responsibly and follow Telegram's terms of service. The developers are not responsible for any misuse.