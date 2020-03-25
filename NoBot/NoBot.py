#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tweepy
import time
import json
from datetime import datetime


def log(l):
    with open("NoBot/log", 'a') as lout:
        lout.write("{}: {}\n".format(str(datetime.now()), str(l)))


class MyStreamListener(tweepy.StreamListener):

    def __init__(self, self_id, self_screen_name, api):
        super().__init__(api)
        self.self_id = self_id
        self.screen_name = self_screen_name
        self.replay_text = 'לא'

    def on_connect(self):
        log("connected")

    def on_disconnect(self, notice):
        log("disconnected")

    def on_status(self, status):
        log(status)
        status_id = status.id_str
        status_author_screen_name = status.author.screen_name
        status_in_reply_to_status_id_str = status.in_reply_to_status_id_str
        status_in_reply_to_screen_name = status.in_reply_to_screen_name
        if status_author_screen_name == self.screen_name:
            return
        if status_in_reply_to_screen_name == self.screen_name:
            api.update_status('@{} {}'.format(status_author_screen_name, self.replay_text), status_id)
            return
        if status.text.strip() == "@{} @{}".format(status_in_reply_to_screen_name, self_screen_name):
            api.create_favorite(status_id)
            api.update_status('@{} {}'.format(status_in_reply_to_screen_name, self.replay_text), status_in_reply_to_status_id_str)
            return
        api.update_status('@{} {}'.format(status_author_screen_name, self.replay_text), status_id)
        return

    def on_direct_message(self, status):
        log(status)

    def on_exception(self, exception):
        log(exception)
        print(exception)

    def on_error(self, status_code):
        log(status_code)
        print(status_code)


with open("NoBot/NoBotAuth.json", 'r') as fin:
    auth_params = json.load(fin)


log("*****Starting NoBot*****")

self_user_id = '1225872616868777990'
self_screen_name = 'NoNooNoooNooNo'

auth = tweepy.OAuthHandler(consumer_key=auth_params["consumer_key"], consumer_secret=auth_params["consumer_secret"])
auth.set_access_token(auth_params["access_token"], auth_params["access_secret"])
api = tweepy.API(auth)

listener = MyStreamListener(self_user_id, self_screen_name, api)
stream = tweepy.Stream(auth=api.auth, listener=listener)

while True:
    with open("NoBot/heartbeat", 'w') as hbout:
        hbout.write('heartbeat at: %s' % datetime.now())
    if not stream.running:
        log("Attempting to connect")
        stream.filter(follow=[self_user_id], track=['@{}'.format(self_screen_name)], is_async=True)
    time.sleep(60)
