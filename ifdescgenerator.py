import os
from termcolor import colored

def get_input(prompt, color='cyan'):
    return input(colored(prompt, color))

def get_formatted_input(prompt, color='cyan'):
    return get_input(prompt, color).strip().upper()

try:
	# Print predefined types
	print(colored('\nCORE - to-router, to-csw, t-asw\nCUST - customer-facing\nLINK - LACP Members and single links to own devices\nLOOP - loopback\nMGMT - management to-mgt, oob uplink\nPEER - peering\nPORT - precabled/reserved\nSTOR - storage\nTRAN - transit uplink\nXAAS - XAAS-FW, XAAS-ESX\nLANL - Layer2 LAN Link Between network devices\nFIRE - Firewall Link Aggregation Interface\nMGMT - Out of Band Management Link\n', 'yellow'))

	# Get type description with default value
	final = get_formatted_input('Choose one: ', 'blue')
	if not final:
		final = "TYPE"
	elif len(final) != 4:
		print(colored("Length has to be 4 characters, try again!", 'red'))
		os.system("python ifdescgenerator.py")

	# Get interface name for full config (optional)
	ifname = get_input("If you need a full config, please give me the interface name: ", 'cyan').lower()

	# Prompt user for input values
	input_fields = [
		('r_dev', '1/8 Remote device: '),
		('r_if', '2/8 Remote interface: '),
		('cust', '3/8 Customer number: '),
		('ticket', '4/8 Ticket: '),
		('asn', '5/8 AS number: '),
		('carr', '6/8 Carrier abbr: '),
		('c_id', '7/8 Circuit id: '),
		('lag', '8/8 Parent LACP group: ')
	]

	result = {}
	for field, prompt in input_fields:
		value = get_formatted_input(prompt)
		if value:
			result[field] = value

	final += " - ["

	# Build the final string
	for key, value in result.items():
		final += f"{key}={value}, "

	final = final[:-2]
	final += "]"

	# Print the final result
	if ifname:
		print(colored(f"\nset interfaces {ifname} description \"{final}\"\n", 'green'))
	else:
		print(colored(f'\n{final}\n', 'green'))

	try:
		input(colored('Press ENTER to exit', attrs=['dark']))
	except:
		pass

except KeyboardInterrupt:
    pass

os.system("python mainmenu.py")
