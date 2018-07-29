#!/usr/env python3
import sys, time, requests
from slackclient import SlackClient
from parkiolib import get_slack_client, xstr, TX_CHANNEL, AUCTION_JSON_EP, DOMAIN_JSON_EP

#TODO: GET requests at most 2 by matching "count" key with "current" key!

def parkio_auction(s, name, tld):
    msg = ''
    try:
        reply = s.get(AUCTION_JSON_EP)
        reply.raise_for_status()
    except requests.exceptions.HTTPError as err:
        msg = xstr(err) + '\n'
    except:
        msg = 'connection error\n'
    else:
        for k in reply.json()['auctions']:
            domain = xstr(k['name'])
            ls = domain.split('.') if domain != None else list()
            if len(ls) == 2 and (tld == 'all' or tld == ls[1]) and ls[0].find(name) is not -1:
                msg = msg + xstr(k['id']) + ': ' + xstr(k['name']) + ', ' + 'bids: ' + xstr(k['num_bids']) + \
                    ', ' + 'price: ' + xstr(k['price']) + ' USD\n'
        if msg == '':
            msg = 'No auctions containing name: \'' + name + '\' and with tld: \'' + tld + '\'\n'
        else:
            msg = 'Auctions found:\n' + msg
    finally:
        print('[search -n=' + name + ' -t=' + tld + '] ' + msg + '\n')
        sys.stdout.flush() #flush output due to threading
        get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)


def parkio_domain(s, name, tld, pg=1, msg=''):
    err = True
    try:
        reply = s.get(DOMAIN_JSON_EP + tld + '/page:' + xstr(pg) + '.json?limit=1000')
        reply.raise_for_status()
    except requests.exceptions.HTTPError as err:
        msg = msg + xstr(err) + '\n'
    except:
        msg = msg + 'connection error\n'
    else:
        err = False
        for k in reply.json()['domains']:
            domain = xstr(k['name'])
            ls = domain.split('.') if domain != None else list()
            if len(ls) == 2 and (tld == 'all' or tld == ls[1]) and ls[0].find(name) is not -1:
                msg = msg + xstr(k['id']) + ': ' + xstr(k['name']) + ', ' + 'date available: ' + \
                    xstr(k['date_available']) + ', ' + 'date registered: ' + xstr(k['date_registered']) + '\n'
    finally:
        #Check if there are more pages
        if not err and reply.json()['nextPage']:
            parkio_domain(s, name, tld, pg + 1, msg)
        else:
            if msg == '':
                msg = 'No domains containing name: \'' + name + '\' and with tld: \'' + tld + '\'\n'
            else:
                msg = 'Domains found:\n' + msg
            print('[search -n=' + name + ' -t=' + tld + '] ' + msg + '\n')
            sys.stdout.flush() #flush output due to threading
            get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)


def parkio_search(name, tld):
    with requests.Session() as s:
        parkio_auction(s, name, tld)
        parkio_domain(s, name, tld)


if __name__ == "__main__":
    err = True
    if len(sys.argv) == 2:
        domain = sys.argv[1].split(' ')
        if len(domain) == 2:
            err = False
            parkio_search(domain[0], domain[1]) 
    if err == True:
        msg = 'Invalid arguments, please run \'help\''
        print('[search] ' + msg)
        sys.stdout.flush() #flush output due to threading
        get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)
