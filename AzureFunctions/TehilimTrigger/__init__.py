import datetime
import logging
import os
import azure.functions as func
from ..Shared.bot_engine import TwitterBot

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    logging.info('Python timer trigger function ran at %s', utc_timestamp)

    config = {
        'consumer_key': os.environ['TEHILIM_CONSUMER_KEY'],
        'consumer_secret': os.environ['TEHILIM_CONSUMER_SECRET'],
        'access_token': os.environ['TEHILIM_ACCESS_TOKEN'],
        'access_token_secret': os.environ['TEHILIM_ACCESS_TOKEN_SECRET'],
        'blob_connection_string': os.environ['BLOB_CONNECTION_STRING'],
        'state_blob_name': 'tehilim_state.json',
        'content_file_path': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Data', 'parsed_tehilim.json'),
        'minor_list_key': 'verses',
        'text_key': 'verse_text',
        'major_label_key': 'chapter_heb_ind',
        'minor_label_key': 'verse_heb_ind',
        'template': "{}\n~ {}', {}'",
        'description_template': "מצייץ תהילים להצלת עם ישראל. עכשיו בפרק {}'. בוט מאת @%s" % (os.environ['TEHILIM_CREDIT_CREATOR'])
    }
    
    bot = TwitterBot(config)
    bot.run()
