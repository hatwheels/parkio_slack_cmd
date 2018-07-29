#!/usr/env python3
from slackclient import SlackClient

TX_CHANNEL = '' # your channel id to send messages
RX_CHANNEL = '' #your channel id to receive messages
RX_USER = '' # your user id to receive messages from
SLACK_CMD_BOT = ''#<-- your bot token, keep it safe

DOMAIN_JSON_EP = "https://park.io/domains/index/"
AUCTION_JSON_EP = "https://park.io/auctions.json"

slack_client = SlackClient(SLACK_CMD_BOT)


'''
	Get token
'''
def get_slack_client():
	return slack_client


'''
	Transform None type to string 'None'
'''
def xstr(s): 
	return 'None' if s is None else str(s)