#!/usr/env python3
import sys, time, requests, threading
from slackclient import SlackClient
from pprint import pprint
from parkiolib import get_slack_client, xstr, TX_CHANNEL


def parkio_auction(s, name, auctions):
	try:
		response = s.get("https://app.park.io/auctions.json")
		if response.status_code != 200:
			print('[auction ' + name + ']' + ' http error: ' + str(response.status_code) + '\n')
			pprint(response.json())
			sys.stdout.flush() #flush output due to threading

			# repeat main request in 20 seconds
			main_thread(s, name, auctions)
		elif name == 'all':
			newAuctions = dict()
			msg = ''

			#transform response list to a dictionary
			for k in response.json()['auctions']:
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
						msg = msg + 'New bid for #' + xstr(k) + ':\n' + xstr(v['name']) + ', ' + 'bids: ' + \
							xstr(v['num_bids']) + ', ' + 'price: ' + xstr(v['price']) + ' USD\n'
				else: #new auction
					auctions[k] = {'name': v['name'], 'num_bids': v['num_bids'], 'price': v['price']}
					msg = msg + 'New auction #' + xstr(k) + ':\n' + xstr(v['name']) + ', ' + 'bids: ' + \
						xstr(v['num_bids']) + ', ' + 'price: ' + xstr(v['price']) + ' USD\n'

			#print changes to console and send slack message
			if not msg:
				print('[auction ' + name + ']' + ' nothing changed\n')
			else:
				print('[auction ' + name + ']' + ' ' + msg + '\n')
				get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)
			sys.stdout.flush() #flush output due to threading

			# repeat main request in 20 seconds
			main_thread(s, name, auctions)
		else:
			found = False
			msg = ''

			for k in response.json()['auctions']:
				if k['id'] in auctions:
					found = True
					if k['num_bids'] != auctions[k['id']].get('num_bids'):
						auctions[k['id']] = {'name' : k['name'], 'num_bids': k['num_bids'], 'price': k['price']}
						msg = 'New bid for #' + xstr(k['id']) + ':\n' + xstr(k['name']) + ', bids: ' + \
							xstr(k['num_bids']) + ', price: ' + xstr(k['price']) + ' USD\n'
						print('[auction ' + name + ']' + ' ' + msg + '\n')
						sys.stdout.flush() #flush output due to threading
						get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)
					break

			if found:
				if not msg:
					print('[auction ' + name + ']' + ' nothing changed\n')

				# repeat main request in 20 seconds
				main_thread(s, name, auctions)
			else:
				for k, v_dict in auctions:
					msg = 'Auction #' + xstr(k) + ' finished:\n' + xstr(v_dict['name']) + ', bids: ' + \
						xstr(v_dict['num_bids']) + ', prices: ' + xstr(v_dict['price']) + ' USD\n'
					print('[auction ' + name + ']' + ' ' + msg + ' \n')
					get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)
	except:
		print('[auction ' + name + ']' + ' connection error\n')
		sys.stdout.flush() #flush output due to threading
		
		# repeat main request in 20 seconds
		main_thread(s, name, auctions)


def parkio_start(name='all'):
	with requests.Session() as s:
		try:
			response = s.get("https://app.park.io/auctions.json")
			if response.status_code != 200:
				print('[auction ' + name + ']' + ' http error: ' + str(response.status_code) + '\n')
				pprint(response.json())
				sys.stdout.flush() #flush output due to threading

				#restart init request in 20 seconds
				init_thread(name)
			elif name == 'all':
				auctions = dict()
				msg = 'Current Auctions:\n'

				#transform response list to a dictionary
				for k in response.json()['auctions']:
					auctions[k['id']] = {'name': k['name'], 'num_bids': k['num_bids'], 'price': k['price']}
					msg = msg + '#' + xstr(k['id']) + ': ' + xstr(k['name']) + ', ' + 'bids: ' + xstr(k['num_bids']) + \
						', ' + 'price: ' + xstr(k['price']) + ' USD\n'

				#print auctions to console and send slack message
				print('[auction ' + name + ']' + ' ' + msg +  '\n')
				sys.stdout.flush() #flush output due to threading
				get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)

				#start main request in 20 seconds
				main_thread(s, name, auctions)
			else:
				auctions = dict()
				found = False
				msg = 'Auction \'' + name + '\' not found!'

				for k in response.json()['auctions']:
					if k['name'] == name:
						found = True
						auctions[k['id']] = {'name' : k['name'], 'num_bids': k['num_bids'], 'price': k['price']}
						msg = 'Auction #' + xstr(k['id']) +':\n' + xstr(k['name']) + ', bids: ' + \
							xstr(k['num_bids']) + ', price: ' + xstr(k['price']) + ' USD\n'
						break

				print('[auction ' + name + ']' + ' ' + msg + '\n')
				sys.stdout.flush() #flush output due to threading
				get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)

				if found:
					#start main thread in 20 seconds
					main_thread(s, name, auctions)
		except:
			print('[auction ' + name + ']' + ' connection error\n')
			sys.stdout.flush() #flush output due to threading

			#restart init request in 20 seconds
			init_thread(name)


'''
	run init request in 20 seconds
'''
def init_thread(name):
	print("[auction " + name + "]" + " Thread {} starting.".format(threading.current_thread()))
	sys.stdout.flush() #flush output due to threading
	threading.Timer(20, parkio_start, [name]).start()
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
	msg = 'Wrong number of arguments'
	if len(sys.argv) != 2:
		print('[auction] ' + msg)
		sys.stdout.flush() #flush output due to threading
		get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)
	elif sys.argv[1] == 'all':
		parkio_start()
	else:
		msg = 'Name passed not a domain'
		split = sys.argv[1].split("|")
		if len(split) == 2:
			name = split[1].split(">")
			if len(name) == 2:
				parkio_start(name[0])
			else:
				print('[auction] ' + msg)
				sys.stdout.flush() #flush output due to threading
				get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)
		else:
			print('[auction] ' + msg)
			sys.stdout.flush() #flush output due to threading
			get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)
