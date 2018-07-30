#!/usr/env python3
import sys, time, requests, threading
from slackclient import SlackClient
from pprint import pprint
from parkiolib import get_slack_client, xstr, TX_CHANNEL, DOMAIN_JSON_EP


'''
	data['conn'], data['tld'], data['domains'], data['new_domains'], data['limit']
'''
def parkio_process(data):
	msg = ''
	domains = data['domains']
	newDomains = data['new_domains']

	#check for available domains and delete available domains from dropping domains
	for k, v_dict in list(domains.items()):
		if k not in newDomains:
			msg = msg + 'Domain ' + xstr(k) + ' is now available:\n' + xstr(v_dict['name']) + ', ' + \
				'date available: ' + xstr(v_dict['date_available']) + ', ' + \
				'date registered: ' + xstr(v_dict['date_registered']) + '\n'
			del domains[k]

	#check for new domains
	for k, v_dict in newDomains.items():
		if k not in domains: #new domain
			domains[k] = {'name': v_dict['name'], 'date_available': v_dict['date_available'], 
				'date_registered': v_dict['date_registered'], 'tld': v_dict['tld']}
			msg = msg + 'New dropping domain ' + xstr(k) + ':\n' + xstr(v_dict['name']) + ', ' + \
				'date available: ' + xstr(v_dict['date_available']) + ', ' + \
				'date registered: ' + xstr(v_dict['date_registered']) + '\n'

	#print changes to console and send slack message
	if not msg:
		print('[domain ' + data['tld'] + '] ' + 'nothing changed\n')
	else:
		print('[domain ' + data['tld'] + '] ' + msg + '\n')
		get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)
	sys.stdout.flush() #flush output due to threading


'''
	data['conn'], data['tld'], data['domains'], data['new_domains'], data['limit']
'''
def parkio_domain(data):
	msg = ''
	state = 'e' #'e': error, 'c': continue, 'f': found, 'n': nothing found
	try:
		reply = data['conn'].get(DOMAIN_JSON_EP + data['tld'] + '.json?limit=' + xstr(data['limit']))
		reply.raise_for_status
	except requests.exceptions.HTTPError as err:
		msg = xstr(err) + '\n'
	except:
		msg = 'connection error\n'
	else:
		#Check if any dropping domains with tld
		if not eval_tld(data['tld'], reply.json()['domains']):
			state = 'n'
			msg = 'No more expiring domains found\n'
		else:
			count = int(xstr(reply.json()['count']))
			if count > data['limit']: #Check if more domains available than current limit
				state = 'c'
				data['limit'] = count
			else:
				state = 'f'
				newDomains = data['new_domains']
				#transform response list to a dictionary
				for k in reply.json()['domains']:
					newDomains[k['id']] = {'name': k['name'], 'date_available': k['date_available'], 
						'date_registered': k['date_registered'], 'tld': k['tld']}
	finally:
		if state is 'e': #Some error occured, restart
			print('[domain ' + data['tld'] + '] ' + msg + '\n')
			sys.stdout.flush() #flush output due to threading
			# repeat main request in 20 seconds
			main_thread(data)
		elif state is 'c': parkio_domain(data) #More domains available, re-request with higher limit
		elif state is 'f': #Found domains with tld
			parkio_process(data)
			data['new_domains'] = dict()
			data['limit'] = len(data['domains'])
			# repeat main request in 20 seconds
			main_thread(data)
		elif state is 'n':
			print('[domain ' + data['tld'] + '] ' + msg + '\n')
			sys.stdout.flush() #flush output due to threading
			get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)


'''
	data['conn'], data['tld'], data['domains'], data['new_domains'], data['limit']
'''
def parkio_start(data):
	msg = ''
	state = 'e' #'e': error, 'c': continue, 'f': found, 'n': nothing found
	try:
		reply = data['conn'].get(DOMAIN_JSON_EP + data['tld'] + '.json?limit=' + xstr(data['limit']))
		reply.raise_for_status
	except requests.exceptions.HTTPError as err:
		msg = xstr(err) + '\n'
	except:
		msg = 'connection error\n'
	else:
		#Check if any dropping domains with tld
		if not eval_tld(data['tld'], reply.json()['domains']):
			state = 'n'
			msg = 'No expiring domains found\n'
		else:
			count = int(xstr(reply.json()['count']))
			if count > data['limit']: #Check if more domains available than current limit
				state = 'c'
				data['limit'] = count
			else:
				state = 'f'
				msg = 'Dropping Domains:\n'
				domains = data['domains']
				#transform response list to a dictionary
				for k in reply.json()['domains']:
					domains[k['id']] = {'name': k['name'], 'date_available': k['date_available'], 
						'date_registered': k['date_registered'], 'tld': k['tld']}
					msg = msg + xstr(k['id']) + ': ' + xstr(k['name']) + ', ' + 'date available: ' + \
						xstr(k['date_available']) + ', ' + 'date registered: ' + xstr(k['date_registered']) + '\n'
	finally:
		if state is 'e': #Some error occured, restart
			print('[domain ' + data['tld'] + '] ' + msg + '\n')
			sys.stdout.flush() #flush output due to threading
			#restart init request in 20 seconds
			init_thread(data)
		elif state is 'c': parkio_start(data) #More domains available, re-request with higher limit
		elif state is 'f': #Found domains with tld
			data['limit'] = len(data['domains'])
			print('[domain ' + data['tld'] + '] ' + msg + '\n')
			sys.stdout.flush() #flush output due to threading
			get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)
			#start main request in 20 seconds
			main_thread(data)
		elif state is 'n': #No domains found with tld
			print('[domain ' + data['tld'] + '] ' + msg + '\n')
			sys.stdout.flush() #flush output due to threading
			get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)


'''
	check if park.io database has any dropping domains with the passed tld
'''
def eval_tld(tld, domains):
	if tld != 'all' and tld != domains[0].get('tld'):
		msg = 'No domain with tld ' + tld + ' is dropping soon'
		print('[domain ' + tld + '] ' + msg + '\n')
		sys.stdout.flush() #flush output due to threading
		get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)
		return False
	return True


'''
	run init request in 20 seconds
'''
def init_thread(data):
	print('[domain ' + data['tld'] + '] ' + " Thread {} starting.".format(threading.current_thread()))
	sys.stdout.flush() #flush output due to threading
	threading.Timer(20, parkio_start, [data]).start()
	print('[domain ' + data['tld'] + '] ' + " Thread {} done.".format(threading.current_thread()))
	sys.stdout.flush() #flush output due to threading


'''
	run main request in 20 seconds 
'''
def main_thread(data):
	print('[domain ' + data['tld'] + '] ' + " Thread {} starting.".format(threading.current_thread()))
	sys.stdout.flush() #flush output due to threading
	threading.Timer(20, parkio_domain, [data]).start()
	print('[domain ' + data['tld'] + '] ' + " Thread {} done.".format(threading.current_thread()))
	sys.stdout.flush() #flush output due to threading


if __name__ == "__main__":
	if len(sys.argv) == 2:
		data = {
			'conn': requests.Session(),
			'tld': sys.argv[1],
			'domains' : dict(),
			'new_domains': dict(),
			'limit': 1000,
		}
		parkio_start(data)
	else:
		msg = 'Wrong number of arguments'
		print('[domain] ' + msg)
		sys.stdout.flush() #flush output due to threading
		get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)
