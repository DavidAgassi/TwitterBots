from logging import config
import tweepy
import json
import logging
from azure.storage.blob import BlobServiceClient

class TwitterBot:
    def __init__(self, config):
        """
        config: {
            'consumer_key': str,
            'consumer_secret': str,
            'access_token': str,
            'access_token_secret': str,
            'blob_connection_string': str,
            'state_blob_name': str,
            'content_file_path': str,
            'minor_list_key': str, # 'verses' or 'lines'
            'text_key': str, # 'verse_text' or 'line_text'
            'major_label_key': str, # 'chapter_heb_ind' or 'tablet_heb_ind'
            'minor_label_key': str, # 'verse_heb_ind' or None (if using index lookup)
            'template': str,
            'description_template': str,
            'heb_numbers_path': str # Optional, for Gilgamesh
        }
        """
        self.config = config
        self.client = tweepy.Client(
            consumer_key=config['consumer_key'],
            consumer_secret=config['consumer_secret'],
            access_token=config['access_token'],
            access_token_secret=config['access_token_secret']
        )
        auth = tweepy.OAuth1UserHandler(
            config['consumer_key'],
            config['consumer_secret'],
            config['access_token'],
            config['access_token_secret']
        )
        self.api_v1 = tweepy.API(auth)

        self.blob_service_client = BlobServiceClient.from_connection_string(config['blob_connection_string'])
        self.container_name = "bot-state"
        self.blob_name = config['state_blob_name']

    def load_json(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_state(self):
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            if not container_client.exists():
                container_client.create_container()

            blob_client = container_client.get_blob_client(self.blob_name)
            if blob_client.exists():
                data = blob_client.download_blob().readall()
                return json.loads(data)
        except Exception as e:
            logging.warning(f"Error loading state: {e}")
        return {"major": 0, "minor": 0}

    def save_state(self, state):
        try:
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=self.blob_name)
            blob_client.upload_blob(json.dumps(state), overwrite=True)
        except Exception as e:
            logging.error(f"Error saving state: {e}")

    def run(self):
        content = self.load_json(self.config['content_file_path'])
        state = self.get_state()
        major_idx = state['major']
        minor_idx = state['minor']

        # Validate state - reset to beginning if corrupted
        if (major_idx < 0 or major_idx >= len(content) or
            minor_idx < 0 or minor_idx >= len(content[major_idx][self.config['minor_list_key']])):
            logging.warning(f"Invalid state: major={major_idx}, minor={minor_idx}. Resetting to 0,0")
            major_idx = 0
            minor_idx = 0

        current_major = content[major_idx]
        minor_list = current_major[self.config['minor_list_key']]

        current_item = minor_list[minor_idx]
        text = current_item[self.config['text_key']]
        major_label = current_major[self.config['major_label_key']]

        # Determine minor label
        if self.config.get('minor_label_key'):
            minor_label = current_item[self.config['minor_label_key']]
        elif self.config.get('heb_numbers_path'):
            heb_numbers = self.load_json(self.config['heb_numbers_path'])
            minor_label = heb_numbers[minor_idx]
        else:
            minor_label = str(minor_idx + 1)

        # Update Description if at start of major unit
        if minor_idx == 0 and self.config.get('description_template'):
            try:
                new_desc = self.config['description_template'].format(major_label)
                self.api_v1.update_profile(description=new_desc)
                logging.info(f"Updated profile description: {new_desc}")
            except Exception as e:
                logging.error(f"Failed to update description: {e}")

        # Post Tweet
        tweet_text = self.config['template'].format(text, major_label, minor_label)
        try:
            self.client.create_tweet(text=tweet_text)
            logging.info(f"Posted tweet: {tweet_text}")
        except Exception as e:
            logging.error(f"Failed to post tweet: {e}")
            # Don't advance state if failed and it will try again next trigger.
            return

        # Advance State
        minor_idx += 1
        if minor_idx >= len(minor_list):
            minor_idx = 0
            major_idx = (major_idx + 1) % len(content)

        self.save_state({"major": major_idx, "minor": minor_idx})
