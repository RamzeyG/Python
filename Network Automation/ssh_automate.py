import paramiko
import time
import argparse
# Remove bad chars
import re

# from printer import *

# used for running os commands
import pexpect

#              ssh_automate.py
# This is a simple program that ssh's into Networking devices and
# gets the interface configuration. This program requires all devices'
# ssh information reside in the file "config.txt", which should be in the
# same directory as this script.
#
# This program assumes devices are already set up for ssh (instructions
# can be found in the file "sshSetupCisco.txt" for Cisco devices)


parser = argparse.ArgumentParser()
parser.add_argument('-kfile', '--kevinfile')
parser.add_argument('-sf', '--singlefile')
parser.add_argument('-os', '--operatingsystem', default='cisco')

args = parser.parse_args()
kevin_file = args.kevinfile
single_file = args.singlefile
os = args.operatingsystem

kevin_flag = False
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())


def print_progress(line):
	title = 'About to execute command: ' + line.strip()
	top_bar = '           '

	for z in range(0, len(title), 1):
		top_bar += '_'
	print top_bar

	curr_cmd = '__________|About to execute command: ' + line.strip() + '|__________'
	print curr_cmd

	empty_line = '|'
	for y in range(0, len(curr_cmd) - 1, 1):
		empty_line += ' '
	empty_line += '|'
	print empty_line

	return curr_cmd


def print_cmd_completion_status(curr_cmd, output):
	success_string = '| command status: successful'
	invalid_string = '| command status: invalid/incomplete'
	if 'Invalid input' in output or 'Incomplete command' in output:
		for u in range(0, len(curr_cmd) - len(invalid_string), 1):
			invalid_string += ' '
		invalid_string += '|'
		print invalid_string
	else:
		for u in range(0, len(curr_cmd) - len(success_string), 1):
			success_string += ' '
		success_string += '|'
		print success_string

	end_line = '|'
	for x in range(0, len(curr_cmd) - 1, 1):
		end_line += '_'
	end_line += '|\n\n\n'
	print end_line



config_mode = {
		# Works for arista EOS!
        'cisco': 'en\nconf t\nterm len 0',
		'arista': 'en\nconf t\nterm len 0',
        'juniper': 'cli\nconfigure\nset cli screen-length 0'

    }

conf = config_mode.get(os)


def readFile(fileName):
	deviceList =[]
	numOfDevices = 0
	readfile = open("log in credentials.txt", "r")
	for line in readfile:
		# Skip commented out and blank lines (\n) which have a len of 2
		if not line.startswith('#') and not line.startswith('//') and len(line) > 2:
			line = line.strip("\r\n")
			line = line.split(" ")
			deviceList.append([line[0], line[1], line[2]])
			numOfDevices += 1
	return numOfDevices, deviceList




# DEFUALT COMMANDS I NEED TO IMPLEMENT:
# enable, conf t, terminal len 0
def execute_commands(ip_commands, ssh_remote, device_name, kevin_flag, k_file_name):
	if kevin_flag:
		print 'Kevin flag is on'
		global begin_found
		global start
		# start = 0

		# print begin_found
		command_list = open(ip_commands, 'w')
		kevin_file = open(k_file_name, 'r')

		for line in kevin_file:
			while begin_found <= start:
				if line.startswith('######') and 'BEGIN CONFIG' in line:
					begin_found += 1
				elif begin_found == start:
					command_list.write(line.strip() + '\n')
					print 'Writing the following cmd: ['+ line.strip()+']'

				line = kevin_file.next()
		command_list.close()
		start += 1
		begin_found = -1
	print 'AFTER: ', 	begin_found, start
	new_file = 'output-' + device_name # + '.txt'
	# result = open(new_file, 'w')
	command_list = open(ip_commands, 'r')
	config_cmds = conf.split('\n')

	# # Executing config commands
	# for f in range(0,len(config_cmds), 1):
	# 	curr_cmd = print_progress(config_cmds[f])
	# 	ssh_remote.send(config_cmds[f])
	# 	time.sleep(3)
	# 	output = ssh_remote.recv(655350)
	# 	print_cmd_completion_status(curr_cmd, output)
	hostname = ''
	first_run = 1
	# executing user commands
	for line in command_list:

		cmd = line.strip()
		if len(cmd) > 0 and '!' != cmd:
			curr_cmd = print_progress(line)

			# Now we can execute commands
			ssh_remote.send(line.lstrip())
			if 'show' in line:
				time.sleep(5)
			else:
				time.sleep(1)


			# Continue to read from buffer until output is done.
			rcv_timeout = 6
			interval_length = 1
			hostname_found = False
			new_output = ''
			while True:
				if ssh_remote.recv_ready():
					output = ssh_remote.recv(1024)

					# Remove unwanted chars
					for x in output:
						new_output += (re.compile(r'\x1b[^m]*m')).sub('', x)

				# If recv buffer is empty (we got all the output)
				else:
					rcv_timeout -= interval_length
				if rcv_timeout < 0:
					print 'FIRST RUN IS: ', first_run
					if first_run:
						print 'ABOUT TO GET PROMPT'
						hostname = ssh_remote.recv(1024)
						print hostname
						if '# ' in hostname:
							rm_prompt = hostname.split('#')
							hostname = rm_prompt[0]
							hostname_found = True
						elif '> ' in hostname:
							rm_prompt = hostname.split('>')
							hostname = rm_prompt[0]
							hostname_found = True
						# Look for" hostname(currentmode)"
						if '(' in hostname:
							rm_parenthesis = hostname.split('(')
							hostname = rm_parenthesis[0]
						# Look for username@hostname
						if '@' in hostname:
							rm_user = hostname.split('@')
							hostname = rm_user[1]

						if hostname_found:
							new_file += '-' + hostname + '.txt'
							result = open(new_file, 'w')
							first_run = False
						if not hostname_found:
							print 'DID NOT FIND HOSTNAME, exiting program'
							exit()
						first_run = False
					break

			print_cmd_completion_status(curr_cmd, output)
			# Write output to the output file
			result.write(new_output)
			result.write('\n')
	result.close()
	return new_file


# Main()

#Read in file for address, username and password
numOfDevices, deviceList = readFile("log in credentials.txt")
global begin_found
global start
start = 0 # 0
begin_found = -1 # -1
if kevin_file:
	kevin_flag = True
	print 'KEVIN FILE'
output_files_list = []


for i in range(numOfDevices):
	print "********** Now Going into device: ", deviceList[i][0], " ************"
	print begin_found, start
	ssh.connect(deviceList[i][0], port=22, username=deviceList[i][1], password=deviceList[i][2], look_for_keys=False)

	ssh_remote = ssh.invoke_shell()

	if single_file:
		output_file = execute_commands(single_file, ssh_remote, deviceList[i][0], kevin_flag, kevin_file)
	else:
		output_file = execute_commands(deviceList[i][0], ssh_remote, deviceList[i][0], kevin_flag, kevin_file)
	
	ssh.close()

	output_files_list.append(output_file)

print '\n\n            Checking for errors'

# Check for errors or invalid input
for z in range(0, len(output_files_list), 1):
	title = output_files_list[i].strip('output-')
	title = title.strip('.txt')

	print 'Device ' + title + ' Errors'
	# Palo alto key word is "Unknown command:"
	# Arista and Cisco key word is: "Invalid"
	cmd = 'cat ' + output_files_list[i] + ' | grep -B 2 Invalid'
	print cmd
	process = pexpect.spawn('/bin/bash')
	process.sendline(cmd)

	print process.before
	process.interact()
