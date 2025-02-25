import os
import webbrowser
from termcolor import colored

try:
	# Prompt the user for the AS set (not case sensitive)
	print(colored("\nPlease give me the AS set (not case sensitive): ", 'blue') + "AS", end='')
	asset = input()

	# Check if the AS set is provided
	if str(asset) == "":
		print(colored("As set is missing!", 'red'))
	else:
		# Query the number of prefixes in the AS set using bgpq3
		os.system('bgpq4 -h whois.radb.net AS' + str(asset).upper() + " | wc -l")
		
		# Ask the user if they want the whole prefix list
		pfl = input(colored('Do you need the whole prefix list? (y/n): ', 'blue'))
		
		if pfl == 'y':
			# Query the prefixes in the AS set using bgpq3
			os.system('bgpq4 -h whois.radb.net AS' + str(asset).upper())

		# Ask the user if they want to open the PeeringDB website
		pdb = input(colored('Do you need PeeringDb website? (y/n): ', 'blue'))
		
		# Open the PeeringDB website if the user answers 'y'
		if pdb == 'y':
			# Remove the hyphen from the beginning of the string, if it exists
			asset_without_hyphen = str(asset).lstrip("-")

			# Create the URL and open the PeeringDB website
			purl = "https://www.peeringdb.com/search?q=" + asset_without_hyphen.upper()
			webbrowser.open(purl)

	# Exit prompt
	input(colored('\nPress ENTER to exit', attrs=['dark']))
except KeyboardInterrupt:
	pass

# Return to the main menu
os.system("python3 mainmenu.py")
