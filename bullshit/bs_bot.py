#!/usr/bin/env python

import os
import time
from slackclient import SlackClient
from bullshit import bullshit

KEYWORDS=['bs', 'BS', 'bullshit', 'no way', 'nonsense', 'bull', 'BULL', 'BULLSHIT']

BOT_QUIET_PERIOD = 300

BOT_NAME = 'syn-bs-bot'
BOT_ID = os.environ.get("SLACK_BOT_BS_ID")
AT_BOT = '<@{}>'.format(BOT_ID)
slack_client = SlackClient(os.environ.get("SLACK_BOT_BS_TOKEN"))

def parse_slack_output(outputs):
    """if an incoming event matches our bot's id, interpret it as a command for this bot, and return the channel as well"""
    if outputs and len(outputs) > 0:
        for output in outputs:
            if output and 'text' in output:
                if AT_BOT in output['text']:
                    return output['text'].split(AT_BOT)[1].strip().lower(), output['channel']
                if any(x in output['text'] for x in KEYWORDS):
                    print("someone said '{}'!".format(output['text']))
                    return output['text'], output['channel']
    return None, None

def handle_command(command, channel):
    response = bullshit()
    print(response)
    slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)

if __name__ == "__main__":
    if slack_client.rtm_connect():
        print("Bot connected and running")
        print(AT_BOT)
        last_message_time = time.time()
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel and time.time() - last_message_time > BOT_QUIET_PERIOD:
                handle_command(command, channel)
                last_message_time = time.time()
            time.sleep(1.0)
    else:
        print("Connection failed")
