#!/usr/bin/env python

import os
import sys
from slackclient import SlackClient

BOT_NAME = 'syn-bs-bot'

slack_client = SlackClient(os.environ.get('SLACK_BOT_BS_TOKEN'))

if __name__ == "__main__":
    api_call = slack_client.api_call("users.list")
    if api_call.get("ok"):
        users = api_call.get("members")
        for user in users:
            if user['name'] == BOT_NAME:
                print("Bot ID for '{}' is {}".format(user['name'], user['id']))
                sys.exit(0)
    print("No user named '{}'".format(BOT_NAME))
