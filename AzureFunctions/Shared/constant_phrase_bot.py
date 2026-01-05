import tweepy
import json
import logging
from datetime import datetime
from azure.storage.blob import BlobServiceClient

class ConstantPhraseBot:
    def __init__(self, config):
        """
        config: {
            'consumer_key': str,
            'consumer_secret': str,
            'access_token': str,
            'access_token_secret': str,
            'blob_connection_string': str,
            'bot_name': str,  # Used to generate blob names: {bot_name}_overrides.json, {bot_name}_enabled.json
            'constant_phrase': str,
            'timezone': ZoneInfo object,  # Timezone for date matching
            'target_hour': int  # Target hour to post (in configured timezone)
        }
        """
        self.config = config
        self.client = tweepy.Client(
            consumer_key=config['consumer_key'],
            consumer_secret=config['consumer_secret'],
            access_token=config['access_token'],
            access_token_secret=config['access_token_secret']
        )

        self.blob_service_client = BlobServiceClient.from_connection_string(config['blob_connection_string'])
        self.container_name = "bot-state"
        self.bot_name = config['bot_name']
        self.overrides_blob_name = f"{self.bot_name}_overrides.json"
        self.enabled_blob_name = f"{self.bot_name}_enabled.json"
        self._ensure_container_exists()

    # ============================================================================
    # Infrastructure & State Management
    # ============================================================================

    def _ensure_container_exists(self):
        """Create container if it doesn't exist"""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            container_client.create_container()
            logging.info(f"Created container: {self.container_name}")
        except Exception as e:
            # Container likely already exists
            logging.info(f"Container {self.container_name} already exists or error: {e}")

    def is_enabled(self):
        """Check if bot is enabled"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=self.enabled_blob_name
            )
            blob_data = blob_client.download_blob().readall()
            state = json.loads(blob_data)
            return state.get('enabled', True)  # Default to enabled
        except Exception as e:
            logging.info(f"No enabled state found, defaulting to enabled: {e}")
            return True  # Default to enabled if no state file

    def set_enabled(self, enabled):
        """Enable or disable the bot"""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=self.enabled_blob_name
        )
        state = {'enabled': enabled}
        blob_client.upload_blob(
            json.dumps(state, indent=2),
            overwrite=True
        )
        status = "enabled" if enabled else "disabled"
        logging.info(f"Bot {status}")

    def get_overrides(self):
        """Load overrides from blob storage"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=self.overrides_blob_name
            )
            blob_data = blob_client.download_blob().readall()
            return json.loads(blob_data)
        except Exception as e:
            logging.info(f"No overrides found or error loading: {e}")
            return {}

    def save_overrides(self, overrides):
        """Save overrides to blob storage"""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=self.overrides_blob_name
        )
        blob_client.upload_blob(
            json.dumps(overrides, indent=2, ensure_ascii=False),
            overwrite=True
        )
        logging.info("Overrides saved successfully")

    def cleanup_past_overrides(self, overrides, today_str):
        """Remove overrides for dates in the past (including today)"""
        today_date = datetime.strptime(today_str, '%Y-%m-%d').date()
        original_count = len(overrides)

        # Remove all dates <= today
        cleaned_overrides = {
            date: phrase for date, phrase in overrides.items()
            if datetime.strptime(date, '%Y-%m-%d').date() > today_date
        }

        if len(cleaned_overrides) < original_count:
            self.save_overrides(cleaned_overrides)
            removed = original_count - len(cleaned_overrides)
            logging.info(f"Cleaned up {removed} past override(s)")
        else:
            logging.info("No past overrides to clean up")

    # ============================================================================
    # Timer Trigger - Tweet Posting Logic
    # ============================================================================

    def get_phrase_for_today(self):
        """Get phrase for today - check override first, then use constant"""
        # Use configured timezone for date matching
        today = datetime.now(self.config['timezone']).strftime('%Y-%m-%d')
        overrides = self.get_overrides()

        phrase = None
        if today in overrides:
            logging.info(f"Using override phrase for {today}")
            phrase = overrides[today]
        else:
            logging.info(f"Using constant phrase for {today}")
            phrase = self.config['constant_phrase']

        # Clean up past overrides (including today's after using it)
        self.cleanup_past_overrides(overrides, today)

        return phrase

    def is_target_time(self):
        """Check if current time (rounded to nearest hour) matches target hour"""
        from datetime import timedelta

        now = datetime.now(self.config['timezone'])
        target_hour = self.config['target_hour']

        # Round to nearest hour: add 30 minutes and take the hour
        rounded_hour = (now + timedelta(minutes=30)).hour

        if rounded_hour != target_hour:
            logging.info(f'Not the target hour. Current time: {now.strftime("%H:%M")} (rounds to {rounded_hour}:00), Target: {target_hour}:00')
            return False

        logging.info(f'Target time reached: {now.strftime("%H:%M")} (rounds to {rounded_hour}:00)')
        return True

    def post_tweet(self):
        """Post the appropriate phrase for today"""
        phrase = self.get_phrase_for_today()

        try:
            response = self.client.create_tweet(text=phrase)
            logging.info(f"Tweet posted successfully: {phrase}")
            logging.info(f"Tweet ID: {response.data['id']}")
            return True
        except Exception as e:
            logging.error(f"Error posting tweet: {e}")
            return False

    def run(self):
        """Main run method - checks time and posts if appropriate"""
        if not self.is_enabled():
            logging.info('Bot is disabled via kill switch')
            return False

        if not self.is_target_time():
            return False

        return self.post_tweet()

    # ============================================================================
    # HTTP API - Management Endpoints
    # ============================================================================

    def add_override(self, date, phrase):
        """Add or update an override for a specific date"""
        overrides = self.get_overrides()
        overrides[date] = phrase
        self.save_overrides(overrides)
        logging.info(f"Override added for {date}")

    def remove_override(self, date):
        """Remove an override for a specific date"""
        overrides = self.get_overrides()
        if date in overrides:
            del overrides[date]
            self.save_overrides(overrides)
            logging.info(f"Override removed for {date}")
            return True
        return False

    def list_overrides(self):
        """List all scheduled overrides"""
        return self.get_overrides()

    def handle_schedule_override_request(self, action, request_body=None):
        """Handle schedule override API requests"""
        if action == 'list':
            overrides = self.list_overrides()
            return {"status": 200, "body": overrides}

        # For add/remove, need request body
        if not request_body:
            return {"status": 400, "body": {"error": "Request body required"}}

        date = request_body.get('date')
        if not date:
            return {"status": 400, "body": {"error": "Please provide 'date' in format YYYY-MM-DD"}}

        if action == 'add':
            phrase = request_body.get('phrase')
            if not phrase:
                return {"status": 400, "body": {"error": "Please provide 'phrase' for the override"}}

            self.add_override(date, phrase)
            return {
                "status": 200,
                "body": {
                    "success": True,
                    "message": f"Override scheduled for {date}",
                    "date": date,
                    "phrase": phrase
                }
            }

        elif action == 'remove':
            success = self.remove_override(date)
            if success:
                return {
                    "status": 200,
                    "body": {"success": True, "message": f"Override removed for {date}"}
                }
            else:
                return {
                    "status": 404,
                    "body": {"success": False, "message": f"No override found for {date}"}
                }

        else:
            return {
                "status": 400,
                "body": {"error": f"Unknown action: {action}. Use 'add', 'remove', or 'list'"}
            }

    def handle_kill_switch_request(self, action):
        """Handle kill switch API requests"""
        if action == 'status':
            enabled = self.is_enabled()
            return {
                "status": 200,
                "body": {"enabled": enabled, "status": "enabled" if enabled else "disabled"}
            }

        elif action == 'enable':
            self.set_enabled(True)
            return {
                "status": 200,
                "body": {"success": True, "message": "Bot enabled", "enabled": True}
            }

        elif action == 'disable':
            self.set_enabled(False)
            return {
                "status": 200,
                "body": {"success": True, "message": "Bot disabled", "enabled": False}
            }

        else:
            return {
                "status": 400,
                "body": {"error": f"Unknown action: {action}. Use 'status', 'enable', or 'disable'"}
            }

    def handle_http_request(self, req):
        """
        Handle HTTP API requests - parse parameters and route to appropriate handler
        Returns: dict with 'status' and 'body' keys
        """
        try:
            # Route based on endpoint parameter (required)
            endpoint = req.params.get('endpoint')
            if not endpoint:
                return {
                    "status": 400,
                    "body": {"error": "Missing required parameter 'endpoint'. Use 'override' or 'killswitch'"}
                }

            if endpoint == 'override':
                # Schedule override operations
                action = req.params.get('action')
                if not action:
                    return {
                        "status": 400,
                        "body": {"error": "Missing required parameter 'action'. Use 'add', 'remove', or 'list'"}
                    }

                request_body = None
                if action != 'list':
                    try:
                        request_body = req.get_json()
                    except ValueError:
                        return {
                            "status": 400,
                            "body": {"error": "Invalid JSON in request body"}
                        }

                return self.handle_schedule_override_request(action, request_body)

            elif endpoint == 'killswitch':
                # Kill switch operations
                action = req.params.get('action')
                if not action:
                    return {
                        "status": 400,
                        "body": {"error": "Missing required parameter 'action'. Use 'status', 'enable', or 'disable'"}
                    }
                return self.handle_kill_switch_request(action)

            else:
                return {
                    "status": 400,
                    "body": {"error": f"Unknown endpoint: {endpoint}. Use 'override' or 'killswitch'"}
                }

        except Exception as e:
            logging.error(f"Error processing request: {e}")
            return {
                "status": 500,
                "body": {"error": str(e)}
            }
