import ipaddress
from termcolor import colored
from terminaltables import SingleTable
import os

try:
	# Function to determine the address type
	def get_address_type(address):
		if address.is_multicast:
			return "Multicast"
		elif address.is_private:
			return "Private"
		elif address.is_global:
			return "Global"
		elif address.is_reserved:
			return "Reserved"
		elif address.is_loopback:
			return "Loopback"
		elif address.is_link_local:
			return "Link-local"
		elif address.is_unspecified:
			return "Unspecified"
		else:
			return "Unknown"

	# Get user input for IP address and netmask
	try:
		address_input = input(colored("Address in any format: ", 'blue'))
		netmask = ''
		if '/' not in address_input:
			netmask = input(colored("Netmask: ", 'blue') + '/')
			address_input = address_input + '/' + netmask
	except KeyboardInterrupt:
		os.system("python mainmenu.py")

	# Validate user input and create an IP network object
	try:
		network = ipaddress.ip_network(address_input, strict=False)
	except ValueError:
		print(colored("Error: The provided address and netmask combination is not valid.", 'red'))
		os.system("python mainmenu.py")
		exit()


	network = ipaddress.ip_network(address_input, strict=False)
	ip = ipaddress.ip_address(network.network_address)

	# Calculate the range of valid IP addresses based on the provided netmask
	if network.prefixlen == 0:
		first_address = network.network_address
		last_address = network.broadcast_address
		total_hosts = network.num_addresses
	elif network.prefixlen == 32 or (network.prefixlen == 128 and network.version == 6):
		first_address = network.network_address
		last_address = network.network_address
		total_hosts = 1
	elif network.prefixlen == 31 or (network.prefixlen == 127 and network.version == 6):
		first_address = network.network_address
		last_address = network.broadcast_address
		total_hosts = 2
	else:
		first_address = network.network_address + 1
		last_address = network.broadcast_address - 1
		total_hosts = network.num_addresses - 2

	# Prepare the data for the output table
	data = [
		[colored("Address Type", attrs=['bold']), colored(get_address_type(ip), 'yellow')],
		[colored("Netmask Full", attrs=['bold']), colored(str(network.netmask), 'yellow')],
		[colored("Network Address", attrs=['bold']), colored(str(network.network_address), 'yellow')],
		[colored("Hosts Range", attrs=['bold']), colored(f"{str(first_address)} - {str(last_address)}", 'yellow')],
		[colored("Broadcast Address", attrs=['bold']), colored(str(network.broadcast_address), 'yellow')],
		[colored("Total Valid Hosts", attrs=['bold']), colored("{:,}".format(total_hosts), 'yellow')]
	]

	# Create the table with the prepared data
	table = SingleTable(data)
	table.inner_row_border = True

	# Print the table
	print(table.table)
	print(colored("\nDo you need the full table? (y/n)", 'blue'))
	choice = input()
	if choice == 'y':
		if total_hosts > 100:
			print(colored("There are more than 100 hosts. Are you sure you want to print all of them? (y/n): ", 'blue'), end='')
			choice = input()
			if choice == 'n':
				pass
			elif choice == 'y':
				for host in network.hosts():
					print(host)
			else:
				print(colored("Invalid input!", 'red'))
		else:
			for host in network.hosts():
				print(host)
	elif choice == 'n':
		pass
	else:
		print(colored("Invalid input!", 'red'))
	# Exit prompt
	try:
		input(colored('\nPress ENTER to exit', attrs=['dark']))
	except KeyboardInterrupt:
		pass
except KeyboardInterrupt:
	pass

# Return to the main menu
os.system("python mainmenu.py")
