#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tweepy
import json
import os.path
import time
from datetime import datetime


def log(l):
    with open("TehilimBot/log", 'a') as lout:
        lout.write("{}: {}\n".format(str(datetime.now()), str(l)))


DELAY_IN_SEC = 1800
ERROR_DELAY = 60
DESCRIPTION_TEMPLATE = "מצייץ תהילים להצלת עם ישראל. עכשיו בפרק {}'. בוט מאת @owl_fruit"

log("*****Starting TehilimBot*****")
now = int(time.time())

with open("TehilimBot/TehilimBotAuth.json", 'r') as fin:
    auth_params = json.load(fin)
with open("TehilimBot/parsed_tehilim.json", 'r') as fin:
    tehilim = json.load(fin)
if os.path.isfile("TehilimBot/current_verse"):
    with open("TehilimBot/current_verse", 'r') as fin:
        current_s = fin.readline().split(",")
        chapter = int(current_s[0])
        verse = int(current_s[1])
        last_post_time = int(current_s[2])
        log("Found recovering point!!!")
        time_diff = now - last_post_time
        log("time diff from last run is: {}sec.".format(str(time_diff)))
        if time_diff > DELAY_IN_SEC:
            log("Lagging continue immediately")
            print("Lagging continue immediately")
        else:
            log("Restored in fine delay, sleeping till next")
            time.sleep(DELAY_IN_SEC - time_diff)
else:
    log("No start point found restarting!!!")
    chapter = 0
    verse = 0

auth = tweepy.OAuthHandler(consumer_key=auth_params["consumer_key"], consumer_secret=auth_params["consumer_secret"])
auth.set_access_token(auth_params["access_token"], auth_params["access_secret"])
api = tweepy.API(auth)

while True:
    try:
        if verse == 0:
            api.update_profile(description=DESCRIPTION_TEMPLATE.format(tehilim[chapter]["chapter_heb_ind"]))
        api.update_status(tehilim[chapter]["verses"][verse]["verse_text"])
    except Exception as e:
        print(e)
        time.sleep(ERROR_DELAY)
    else:
        verse = verse + 1
        if len(tehilim[chapter]["verses"]) == verse:
            verse = 0
            chapter = (chapter + 1) % 150
        with open("TehilimBot/current_verse", 'w') as fout:
            fout.writelines(",".join([
                str(chapter),
                str(verse),
                str(int(time.time()))
            ]))
        time.sleep(DELAY_IN_SEC)
