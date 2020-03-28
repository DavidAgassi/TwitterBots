#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tweepy
import json
import os.path
import time
from datetime import datetime


def log(l):
    with open("TehilimBot/TehilimBot.log", 'a') as lout:
        lout.write("{}: {}\n".format(str(datetime.now()), str(l)))


def get_time():
    return int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())


with open("TehilimBot/TehilimBotSecrets.json", 'r') as fin:
    secrets = json.load(fin)

DELAY_IN_SEC = 1800
ERROR_DELAY = 60
DESCRIPTION_TEMPLATE = "מצייץ תהילים להצלת עם ישראל. עכשיו בפרק {}'. בוט מאת @%s" % (secrets["credit"])

log("*****Starting TehilimBot*****")
now = get_time()


with open("TehilimBot/parsed_tehilim.json", 'r') as fin:
    tehilim = json.load(fin)
if os.path.isfile(secrets["state_path"]):
    with open(secrets["state_path"], 'r') as fin:
        state = json.load(fin)
        chapter = state["chapter"]
        verse = state["verse"]
        last_post_time = state["time"]
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

auth = tweepy.OAuthHandler(consumer_key=secrets["consumer_key"], consumer_secret=secrets["consumer_secret"])
auth.set_access_token(secrets["access_token"], secrets["access_secret"])
api = tweepy.API(auth)

while True:
    try:
        if verse == 0:
            api.update_profile(description=DESCRIPTION_TEMPLATE.format(tehilim[chapter]["chapter_heb_ind"]))
        api.update_status(tehilim[chapter]["verses"][verse]["verse_text"])
    except Exception as e:
        print("{}: ERROR - {} ".format(str(datetime.now()), str(e)))
        time.sleep(ERROR_DELAY)
    else:
        with open("TehilimBot/heartbeat.log", 'w') as hbout:
            hbout.write('heartbeat at: {}, posted chapter: {}, verse: {}.'.format(datetime.now(), str(chapter), str(verse)))
        verse = verse + 1
        if len(tehilim[chapter]["verses"]) == verse:
            verse = 0
            chapter = (chapter + 1) % 150
        with open(secrets["state_path"], 'w') as fout:
            json.dump({
                "chapter": chapter,
                "verse": verse,
                "time": get_time()
            }, fout)
        time.sleep(DELAY_IN_SEC)
