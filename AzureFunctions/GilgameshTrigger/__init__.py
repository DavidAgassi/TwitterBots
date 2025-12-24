import datetime
import logging
import os
import azure.functions as func
from ..Shared.bot_engine import TwitterBot

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    logging.info('Python timer trigger function ran at %s', utc_timestamp)

    config = {
        'consumer_key': os.environ['GILGAMESH_CONSUMER_KEY'],
        'consumer_secret': os.environ['GILGAMESH_CONSUMER_SECRET'],
        'access_token': os.environ['GILGAMESH_ACCESS_TOKEN'],
        'access_token_secret': os.environ['GILGAMESH_ACCESS_TOKEN_SECRET'],
        'blob_connection_string': os.environ['BLOB_CONNECTION_STRING'],
        'state_blob_name': 'gilgamesh_state.json',
        'content_file_path': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Data', 'parsed_gilgamesh.json'),
        'minor_list_key': 'lines',
        'text_key': 'line_text',
        'major_label_key': 'tablet_heb_ind',
        'heb_numbers_path': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Data', 'heb_numbers.json'),
        'template': "{}\n\n~ לוּחַ {} שׁוּרָה {}.",
        'description_template': "מצייץ את עֲלִילוֹת גִּלְגָּמֶשׁ. עכשיו בלוח הָ{}. בוט בהשראת @%s מאת @%s" % (os.environ['GILGAMESH_CREDIT_INSPIRED'], os.environ['GILGAMESH_CREDIT_CREATOR'])
    }
    
    bot = TwitterBot(config)
    bot.run()
