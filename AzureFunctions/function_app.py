import logging
import json
import os
import datetime
import azure.functions as func
from Shared.bot_engine import TwitterBot
from Shared.constant_phrase_bot import ConstantPhraseBot
from zoneinfo import ZoneInfo

# Initialize the function app
app = func.FunctionApp()

# Israel timezone for BiBi bot
ISRAEL_TZ = ZoneInfo("Asia/Jerusalem")

# =============================================================================
# Tehilim Bot - Posts verses from Tehilim (Psalms) every 2 hours
# =============================================================================

@app.timer_trigger(schedule="0 0 */2 * * *", arg_name="mytimer", run_on_startup=False)
def tehilim_timer(mytimer: func.TimerRequest) -> None:
    """Timer trigger for Tehilim bot - posts every 2 hours"""
    utc_timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    logging.info('Tehilim timer trigger function ran at %s', utc_timestamp)

    config = {
        'consumer_key': os.environ['TEHILIM_CONSUMER_KEY'],
        'consumer_secret': os.environ['TEHILIM_CONSUMER_SECRET'],
        'access_token': os.environ['TEHILIM_ACCESS_TOKEN'],
        'access_token_secret': os.environ['TEHILIM_ACCESS_TOKEN_SECRET'],
        'blob_connection_string': os.environ['BLOB_CONNECTION_STRING'],
        'state_blob_name': 'tehilim_state.json',
        'content_file_path': os.path.join(os.path.dirname(__file__), 'Data', 'parsed_tehilim.json'),
        'minor_list_key': 'verses',
        'text_key': 'verse_text',
        'major_label_key': 'chapter_heb_ind',
        'minor_label_key': 'verse_heb_ind',
        'template': "{}\n~ {}', {}'",
        'description_template': "מצייץ תהילים להצלת עם ישראל. עכשיו במזמור {}'. בוט מאת @%s" % (os.environ['TEHILIM_CREDIT_CREATOR'])
    }

    bot = TwitterBot(config)
    bot.run()


# =============================================================================
# Gilgamesh Bot - Posts lines from Epic of Gilgamesh every 2 hours
# =============================================================================

@app.timer_trigger(schedule="0 0 */2 * * *", arg_name="mytimer", run_on_startup=False)
def gilgamesh_timer(mytimer: func.TimerRequest) -> None:
    """Timer trigger for Gilgamesh bot - posts every 2 hours"""
    utc_timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    logging.info('Gilgamesh timer trigger function ran at %s', utc_timestamp)

    config = {
        'consumer_key': os.environ['GILGAMESH_CONSUMER_KEY'],
        'consumer_secret': os.environ['GILGAMESH_CONSUMER_SECRET'],
        'access_token': os.environ['GILGAMESH_ACCESS_TOKEN'],
        'access_token_secret': os.environ['GILGAMESH_ACCESS_TOKEN_SECRET'],
        'blob_connection_string': os.environ['BLOB_CONNECTION_STRING'],
        'state_blob_name': 'gilgamesh_state.json',
        'content_file_path': os.path.join(os.path.dirname(__file__), 'Data', 'parsed_gilgamesh.json'),
        'minor_list_key': 'lines',
        'text_key': 'line_text',
        'major_label_key': 'tablet_heb_ind',
        'heb_numbers_path': os.path.join(os.path.dirname(__file__), 'Data', 'heb_numbers.json'),
        'template': "{}\n\n~ לוּחַ {} שׁוּרָה {}.",
        'description_template': "מצייץ את עֲלִילוֹת גִּלְגָּמֶשׁ. עכשיו בלוח הָ{}. בוט בהשראת @%s מאת @%s" % (os.environ['GILGAMESH_CREDIT_INSPIRED'], os.environ['GILGAMESH_CREDIT_CREATOR'])
    }

    bot = TwitterBot(config)
    bot.run()


# =============================================================================
# DidBiBiQuitToday Bot - Posts constant phrase at specific time daily
# =============================================================================

def _get_bibi_quit_config():
    """Get BiBi Quit bot configuration from environment variables"""
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


@app.timer_trigger(schedule="0 0 20,21 * * *", arg_name="mytimer", run_on_startup=False)
def bibi_quit_timer(mytimer: func.TimerRequest) -> None:
    """Timer trigger for BiBi Quit bot - posts at 23:00 Israel time"""
    logging.info('DidBiBiQuitToday timer trigger executed.')

    config = _get_bibi_quit_config()
    bot = ConstantPhraseBot(config)
    bot.run()


@app.route(route="api/bibi", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def bibi_quit_api(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP API for managing BiBi Quit bot overrides and kill switch"""
    logging.info('DidBiBiQuitToday API request received.')

    config = _get_bibi_quit_config()
    bot = ConstantPhraseBot(config)
    result = bot.handle_http_request(req)

    return func.HttpResponse(
        json.dumps(result['body'], indent=2, ensure_ascii=False),
        status_code=result['status'],
        mimetype="application/json"
    )
