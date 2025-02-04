# Forward Bot

A Python-based message forwarding bot

## Features
- Message forwarding between configured channels
- Environment-based configuration management
- Command handling system
- JSON configuration support

## Installation
1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Copy `.env.example` to `.env` and configure your settings
4. Set up your `config.json` (see Configuration section)

## Configuration
Create a `config.json` file with your platform credentials and routing rules. See `config.json.example` for reference.

## Running the Bot
```bash
python src/main.py
```
