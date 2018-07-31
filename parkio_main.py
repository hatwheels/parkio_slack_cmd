#!/usr/env python3
import os, sys, time, subprocess
from slackclient import SlackClient
from pprint import pprint
from parkiolib import get_slack_client, TX_CHANNEL, RX_CHANNEL, RX_USER


'''
	CLI Commands
'''
HELP = 'help'
ALIVE = 'alive?'
RUNNING = 'running?'
CLOSE = 'close'
AUCTION = 'auction'
DOMAIN = 'domain'
SEARCH = 'search'
'''
	CLI Arguments
'''
ALL = 'all'
SNAME = '-n='
STLD = '-t='

'''
	Handle received command and run appropriate routine
'''
def handle_command(processes, command, reply_to):
	msg = ''
	if reply_to:
		msg = 'Ignored last message\n'
	elif command == HELP:
		msg = 'Commands:' + '\n'
		msg = msg + AUCTION + ' all' + ' -> track all auctions' + '\n'
		msg = msg + AUCTION + ' domain.tld' + ' -> track auctioned domain: \'domain.tld\'' + '\n'
		msg = msg + DOMAIN + ' all' + ' -> track all dropping domains' + '\n'
		msg = msg + DOMAIN + ' tld' + ' -> track all dropping domains with tld: \'tld\'' + '\n'
		msg = msg + SEARCH + ' -n=\'domain\' -t=\'tld\'' + ' -> search for dropping and auctioned domains ' + \
			'by domain keyword and tld. Don\'t pass a tld to search for all tlds' + '\n'
		msg = msg + CLOSE + ' command' + ' -> close \'command\', i.e \'close auction all\'' + '\n'
		msg = msg + ALIVE + ' -> check if command handler is running' + '\n'
		msg = msg + RUNNING + ' -> check which scripts are running' + '\n'
	elif command == ALIVE:
		msg = 'alive and kicking!\n'
	elif command == RUNNING:
		if processes:
			msg = 'Currently running:' + '\n'
			for key in list(processes.keys()):
				msg = msg + key + '\n'
		else:
			msg = 'No scripts are currently running\n'
	elif command.startswith(CLOSE):
		msg = 'Wrong argument passed, please run \'help\'\n'
		length = len(CLOSE + ' ')
		if len(command) > length:
			argument = command[length:]
			msg = 'Closed: \n'
			if argument == ALL:
				for cmd, p in list(processes.items()):
					msg = msg + cmd + '\n'
					p.terminate()
					del processes[cmd]
			elif argument in list(processes.keys()):
				msg = 'Closed ' + argument + '\n'
				processes[argument].terminate()
				del processes[argument]
			else:
				msg = argument + ' is not running\n'
	elif command in list(processes.keys()):
		msg = command + ' is already running'
	elif command.startswith(SEARCH):
		msg = 'Wrong argument passed, please run \'help\'\n'
		length = len(SEARCH + ' ')
		if len(command) > length:
			cmd = None
			arglist = command[length:].split(" ")
			msg = 'Wrong number of arguments, please run \'help\'\n'
			if len(arglist) == 1 and arglist[0].startswith(SNAME):
				cmd = arglist[0][len(SNAME):] + ' ' + ALL
			elif len(arglist) == 2:
				msg = 'Invalid arguments, please run \'help\'\n'
				if arglist[0].startswith(SNAME) and arglist[1].startswith(STLD):
					cmd = arglist[0][len(SNAME):] + ' ' + arglist[1][len(STLD):]
				elif arglist[0].startswith(STLD) and arglist[1].startswith(SNAME):
					cmd = arglist[1][len(SNAME):] + ' ' + arglist[0][len(STLD):]
			if cmd is not None:
				msg = 'Running ' + command + '\n'
				p = subprocess.Popen([sys.executable, 'parkio_search.py', cmd])
				processes[command] = p
				print('[handler] ' + command + ' pid: ' + str(processes[command].pid))
				sys.stdout.flush() #flush output due to threading
	elif command.startswith(AUCTION):
		msg = 'Wrong argument passed, please run \'help\'\n'
		length = len(AUCTION + ' ')
		if len(command) > length:
			msg = 'Running ' + command + '\n'
			p = subprocess.Popen([sys.executable, 'parkio_auctions.py', command[length:]])
			processes[command] = p
			print('[handler] ' + command + ' pid: ' + str(processes[command].pid))
			sys.stdout.flush() #flush output due to threading
	elif command.startswith(DOMAIN):
		msg = 'Wrong argument passed, please run \'help\'\n'
		length = len(DOMAIN + ' ')
		if len(command) > length:
			msg = 'Running ' + command + '\n'
			p = subprocess.Popen([sys.executable, 'parkio_domains.py', command[length:]])
			processes[command] = p
			print('[handler] ' + command + ' pid: ' + str(processes[command].pid))
			sys.stdout.flush() #flush output due to threading
	else:
		msg = 'Invalid command' + '\n' + 'send \'help\' for information' + '\n'

	get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)
	print('[handler] ' + msg, end='')
	sys.stdout.flush() #flush output due to threading

'''
	Read message sent to cmdbot and parse it.
'''
def parse_slack_output(slack_rtm_output):
	output_list = slack_rtm_output
	if output_list and len(output_list) > 0:
		for output in output_list:
			if not output:
				continue
			if 'type' not in output or output['type'] != 'message':
				continue
			if 'channel' not in output or output['channel'] != RX_CHANNEL:
				continue
			if 'user' not in output or output['user'] != RX_USER:
				continue
			if 'text' not in output:
				continue
			pprint(output)
			sys.stdout.flush() #flush output due to threading
			if 'reply_to' in output:
				return output['text'], True
			return output['text'], False
	return None, None


if __name__ == "__main__":
	processes = dict()
	while True:
		if get_slack_client().rtm_connect():
			msg = 'Running'
			get_slack_client().api_call("chat.postMessage", channel=TX_CHANNEL, text=msg, as_user=True)
			print('[handler] ' + msg)
			sys.stdout.flush() #flush output due to threading
			while True:
				print('[handler] alive')
				pprint(processes)
				sys.stdout.flush() #flush output due to threading
				#check if any subprocess has finished
				for cmd, p in list(processes.items()):
					if p.poll() != None:
						del processes[cmd]
				command, reply_to = parse_slack_output(get_slack_client().rtm_read())
				if command:
					handle_command(processes, command.lower(), reply_to)
				time.sleep(1)
		else:
			print('[handler] Connection failed. Invalid Slack token or bot ID?')
