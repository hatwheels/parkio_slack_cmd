#!/usr/env python3
import sys, time, requests, threading
from slackclient import SlackClient
from pprint import pprint
from parkiolib import get_slack_client, xstr, TX_CHANNEL

DOMAIN_JSON_ENDPOINT = "https://app.park.io/domains/index/"


'''
	data['conn'], data['tld'], data['domains'], data['new_domains'], data['page'], data['msg']
'''
def parkio_process(data):
	domains = data['domains']
	newDomains = data['new_domains']

	#check for available domains and delete available domains from dropping domains
	for k, v_dict in list(domains.items()):
		if k not in newDomains:
			data['msg'] = data['msg'] + 'Domain #' + xstr(k) + ' is now available:\n' + xstr(v_dict['name']) + ', ' + \
				'date available: ' + xstr(v_dict['date_available']) + ', ' + \
				'date registered: ' + xstr(v_dict['date_registered']) + '\n'
			del domains[k]
			print('deleted')
			sys.stdout.flush() #flush output due to threading

	#check for new domains
	for k, v_dict in newDomains.items():
		if k not in domains: #new domain
			domains[k] = {'name': v_dict['name'], 'date_available': v_dict['date_available'], 
				'date_registered': v_dict['date_registered'], 'tld': v_dict['tld']}
			data['msg'] = data['msg'] + 'New dropping domain #' + xstr(k) + ':\n' + xstr(v_dict['name']) + ', ' + \
				'date available: ' + xstr(v_dict['date_available']) + ', ' + \
				'date registered: ' + xstr(v_dict['date_registered']) + '\n'

	#print changes to console and send slack message
	if not data['msg']:
		print('[domain ' + data['tld'] + '] ' + 'nothing changed\n')
	else:
		print('[domain ' + data['tld'] + '] ' + data['msg'] + '\n')
		get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=data['msg'], as_user=True)
	sys.stdout.flush() #flush output due to threading


'''
	data['conn'], data['tld'], data['domains'], data['new_domains'], data['page'], data['msg']
'''
def parkio_domain(data):
	try:
		response = data['conn'].get(DOMAIN_JSON_ENDPOINT + data['tld'] + '/page:' + xstr(data['page']) + '.json')
		if response.status_code != 200:
			print('[domain ' + data['tld'] + '] ' + 'http error: ' + str(response.status_code) + '\n')
			pprint(response.json())
			sys.stdout.flush() #flush output due to threading

			# repeat main request in 20 seconds
			main_thread(data)
		else:
			if not eval_tld(data['tld'], response.json()['domains']): return

			newDomains = data['new_domains']

			#transform response list to a dictionary
			for k in response.json()['domains']:
				newDomains[k['id']] = {'name': k['name'], 'date_available': k['date_available'], 
					'date_registered': k['date_registered'], 'tld': k['tld']}

			#check if this was the last request
			if not response.json()['nextPage']:
				parkio_process(data)
				data['new_domains'] = dict()
				data['page'] = 1
				data['msg'] = ''
				# repeat main request in 20 seconds
				main_thread(data)
			#otherwise request next page
			else:
				data['page'] = data['page'] + 1
				parkio_domain(data)
	except:
		print('[domain ' + data['tld'] + '] ' + 'connection error')
		sys.stdout.flush() #flush output due to threading

		# repeat main request in 20 seconds
		main_thread(data)


'''
	data['conn'], data['tld'], data['domains'], data['new_domains'], data['page'], data['msg']
'''
def parkio_start(data):
	try:
		response = data['conn'].get(DOMAIN_JSON_ENDPOINT + data['tld'] + '/page:' + xstr(data['page']) + '.json')
		if response.status_code != 200:
			print('[domain ' + data['tld'] + '] ' + 'http error: ' + str(response.status_code) + '\n')
			pprint(response.json())
			sys.stdout.flush() #flush output due to threading

			#restart init request in 20 seconds
			init_thread(data)
		else:
			if not eval_tld(data['tld'], response.json()['domains']): return

			domains = data['domains']

			#transform response list to a dictionary
			for k in response.json()['domains']:
				domains[k['id']] = {'name': k['name'], 'date_available': k['date_available'], 
					'date_registered': k['date_registered'], 'tld': k['tld']}
				data['msg'] = data['msg'] + '#' + xstr(k['id']) + ': ' + xstr(k['name']) + ', ' + 'date available: ' + \
					xstr(k['date_available']) + ', ' + 'date registered: ' + xstr(k['date_registered']) + '\n'

			#check if this was the last request
			if not response.json()['nextPage']:
				#print domains to console and send slack message
				print('[domain ' + data['tld'] + '] ' + data['msg'] + '\n')
				sys.stdout.flush() #flush output due to threading
				get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=data['msg'], as_user=True)

				data['page'] = 1
				data['msg'] = ''
				#start main request in 20 seconds
				main_thread(data)
			#otherwise request next page
			else:
				data['page'] = data['page'] + 1
				parkio_start(data)
	except:
		print('[domain ' + data['tld'] + '] ' + 'connection error' + '\n')
		sys.stdout.flush() #flush output due to threading

		#restart init request in 20 seconds
		init_thread(data)


'''
	check if park.io database has any dropping domains with the passed tld
'''
def eval_tld(tld, domains):
	if tld != 'all' and tld != domains[0].get('tld'):
		msg = 'No domain with tld ' + tld + ' is dropping soon'
		print('[domain ' + tld + '] ' + msg + '\n')
		sys.stdout.flush() #flush output due to threading
		get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=data['msg'], as_user=True)
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
			'page': 1,
			'msg': 'Dropping Domains:\n'
		}
		parkio_start(data)
	else:
		msg = 'Wrong number of arguments'
		print('[domain] ' + msg)
		sys.stdout.flush() #flush output due to threading
		get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=data['msg'], as_user=True)
