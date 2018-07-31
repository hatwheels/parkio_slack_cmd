#!/usr/env python3
import sys, time, requests, threading
from slackclient import SlackClient
from parkiolib import get_slack_client, xstr, TX_CHANNEL, AUCTION_JSON_EP


'''
	s: Requests Session, name: 'domain.tld', auctions: dictionary with current auctions
'''
def parkio_auction(s, name, auctions):
	msg = ''
	state = 'e' #'e': error, 'c': change, 'n': no change, 's': stop
	try:
		reply = s.get(AUCTION_JSON_EP)
		reply.raise_for_status()
	except requests.exceptions.HTTPError as err:
		msg = xstr(err) + '\n'
	except:
		msg = 'connection error\n'
	else:
		if name == 'all':
			state = 'c'
			newAuctions = dict()
			#transform response list to a dictionary
			for k in reply.json()['auctions']:
				newAuctions[k['id']] = {'name': k['name'], 'num_bids': k['num_bids'], 'price': k['price']}
			#check for finished auctions and delete finished auctions from auctions
			for k, v in list(auctions.items()):
				if k not in newAuctions:
					msg = msg + 'Auction #' + xstr(k) + ' finished:\n' + xstr(v['name']) + ', ' + \
						xstr(v['num_bids']) + ', ' + 'price: ' + xstr(v['price']) + 'USD\n'
					del auctions[k]
			#check for new auctions and altered auctions
			for k, v in newAuctions.items():
				if k in auctions: #auction exists
					if v['num_bids'] != auctions[k].get('num_bids'): #new bid in current auction
						auctions[k] = {'name': v['name'], 'num_bids': v['num_bids'], 'price': v['price']}
						msg = msg + 'New bid for ' + xstr(k) + ':\n' + xstr(v['name']) + ', ' + 'bids: ' + \
							xstr(v['num_bids']) + ', ' + 'price: ' + xstr(v['price']) + ' USD\n'
				else: #new auction
					auctions[k] = {'name': v['name'], 'num_bids': v['num_bids'], 'price': v['price']}
					msg = msg + 'New auction ' + xstr(k) + ':\n' + xstr(v['name']) + ', ' + 'bids: ' + \
						xstr(v['num_bids']) + ', ' + 'price: ' + xstr(v['price']) + ' USD\n'
			if not msg:
				state = 'n'
				msg = 'Nothing changed\n'
		else:
			state = 's'
			#Search for auction in response list
			for k in reply.json()['auctions']:
				#Check if auction found, else auction has finished
				if k['id'] in auctions:
					if k['num_bids'] != auctions[k['id']].get('num_bids'): #new bid in auction
						state = 'c'
						auctions[k['id']] = {'name' : k['name'], 'num_bids': k['num_bids'], 'price': k['price']}
						msg = 'New bid for ' + xstr(k['id']) + ':\n' + xstr(k['name']) + ', bids: ' + \
							xstr(k['num_bids']) + ', price: ' + xstr(k['price']) + ' USD\n'
					else: #Auctions intact
						state = 'n'
						msg = 'Nothing changed\n'
					break
			if state is 's':
				#Auction has finished
				for k, v_dict in auctions:
					msg = msg + 'Auction ' + xstr(k) + ' finished:\n' + xstr(v_dict['name']) + ', bids: ' + \
						xstr(v_dict['num_bids']) + ', prices: ' + xstr(v_dict['price']) + ' USD\n'
	finally:
		print('[auction ' + name + '] ' + msg, end='')
		sys.stdout.flush() #flush output due to threading
		if state is 'e' or 'n':
			# repeat main request in 20 seconds
			main_thread(s, name, auctions)
		elif state is 'c':
			get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)
			# repeat main request in 20 seconds
			main_thread(s, name, auctions)
		elif state is 's':
			get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)


'''
	name: 'domain.tld'
'''
def parkio_start(s, name='all'):
	state = 'e' #'e': error, 'c': continue, 's': stop
	try:
		reply = s.get(AUCTION_JSON_EP)
		reply.raise_for_status()
	except requests.exceptions.HTTPError as err:
		msg = xstr(err) + '\n'
	except:
		msg = 'connection error\n'
	else:
		auctions = dict()
		if name == 'all':
			state = 'c'
			msg = 'Current Auctions:\n'
			#transform response list to a dictionary
			for k in reply.json()['auctions']:
				auctions[k['id']] = {'name': k['name'], 'num_bids': k['num_bids'], 'price': k['price']}
				msg = msg + xstr(k['id']) + ': ' + xstr(k['name']) + ', ' + 'bids: ' + xstr(k['num_bids']) + \
					', ' + 'price: ' + xstr(k['price']) + ' USD\n'
		else:
			state = 's'
			msg = 'Auction \'' + name + '\' not found!\n'
			#Find auction in response list
			for k in reply.json()['auctions']:
				if k['name'] == name:
					state = 'c'
					auctions[k['id']] = {'name' : k['name'], 'num_bids': k['num_bids'], 'price': k['price']}
					msg = 'Auction ' + xstr(k['id']) +':\n' + xstr(k['name']) + ', bids: ' + \
						xstr(k['num_bids']) + ', price: ' + xstr(k['price']) + ' USD\n'
					break
	finally:
		print('[auction ' + name + '] ' + msg, end='')
		sys.stdout.flush() #flush output due to threading
		if state is 'e':
			#restart init request in 20 seconds
			init_thread(s, name)
		elif state is 'c':
			get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)
			#start main request in 20 seconds
			main_thread(s, name, auctions)
		elif state is 's':
			get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)


'''
	run init request in 20 seconds
'''
def init_thread(s, name):
	print("[auction " + name + "]" + " Thread {} starting.".format(threading.current_thread()))
	sys.stdout.flush() #flush output due to threading
	threading.Timer(20, parkio_start, [s, name]).start()
	print("[auction " + name + "]" + " Thread {} done.".format(threading.current_thread()))
	sys.stdout.flush() #flush output due to threading


'''
	run main request in 20 seconds 
'''
def main_thread(s, name, auctions):
	print("[auction " + name + "]" + " Thread {} starting.".format(threading.current_thread()))
	sys.stdout.flush() #flush output due to threading
	threading.Timer(20, parkio_auction, [s, name, auctions]).start()
	print("[auction " + name + "]" + " Thread {} done.".format(threading.current_thread()))
	sys.stdout.flush() #flush output due to threading


if __name__ == "__main__":
	state = 'e'
	name = 'all'
	msg = 'Wrong number of arguments'
	if len(sys.argv) == 2:
		if sys.argv[1] != 'all':
			msg = 'Name passed not a domain'
			first = sys.argv[1].split("|")
			if len(first) == 2:
				second = first[1].split(">")
				if len(second) == 2:
					name = second[0]
					state = 'c'
		else: state = 'c'
	#Handle states
	if state is 'e':
		print('[auction] ' + msg)
		sys.stdout.flush() #flush output due to threading
		get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)
	elif state is 'c':
		parkio_start(requests.Session(), name)
