import logging
import json
import os
import azure.functions as func
from zoneinfo import ZoneInfo
import sys
from pathlib import Path

# Add parent directory to path for shared imports
sys.path.append(str(Path(__file__).parent.parent))
from Shared.constant_phrase_bot import ConstantPhraseBot

# Initialize the function app
app = func.FunctionApp()

# Israel timezone
ISRAEL_TZ = ZoneInfo("Asia/Jerusalem")

def _get_bot_config():
    """Get bot configuration from environment variables"""
    return {
        'consumer_key': os.environ['BIBI_QUIT_CONSUMER_KEY'],
        'consumer_secret': os.environ['BIBI_QUIT_CONSUMER_SECRET'],
        'access_token': os.environ['BIBI_QUIT_ACCESS_TOKEN'],
        'access_token_secret': os.environ['BIBI_QUIT_ACCESS_TOKEN_SECRET'],
        'blob_connection_string': os.environ['BLOB_CONNECTION_STRING'],
        'bot_name': 'bibi_quit',
        'constant_phrase': os.environ['BIBI_QUIT_PHRASE'],
        'timezone': ISRAEL_TZ,
        'target_hour': int(os.environ['BIBI_QUIT_HOUR'])
    }


# Timer Trigger - Runs at 20:00 and 21:00 UTC daily
@app.timer_trigger(schedule="0 0 20,21 * * *", arg_name="mytimer", run_on_startup=False)
def time_trigger(mytimer: func.TimerRequest) -> None:
    """Timer trigger that posts tweets at scheduled times"""
    logging.info('DidBiBiQuitToday timer trigger executed.')

    config = _get_bot_config()
    bot = ConstantPhraseBot(config)
    bot.run()


# HTTP Trigger - Management API
@app.route(route="api/bibi", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def api_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP API for managing overrides and kill switch"""
    logging.info('DidBiBiQuitToday API request received.')

    config = _get_bot_config()
    bot = ConstantPhraseBot(config)
    result = bot.handle_http_request(req)

    return func.HttpResponse(
        json.dumps(result['body'], indent=2, ensure_ascii=False),
        status_code=result['status'],
        mimetype="application/json"
    )
