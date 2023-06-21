import os
import time
from termcolor import colored

def print_colored(text, color):
    print(colored(text, color))

try:
	location = "ANX00"
	customers = "noone"

	outage_fields = {
		'**What happened:** ': 'We have received messages that ' + location + ' is not available.',
		'**Who\'s affected:** ': customers,
		'**Impact:** ': '',
		'**Customers informed:** ': 'Customers were informed via Notifier',
		'**Next step:** ': 'Investigate the issue and resolve it.',
		'**Next update:** ': 'Next update comes in 2 hours.'
	}

	print_colored("\nANX-STATUS Chat text generator\n\nLocation: ", 'yellow')
	location = input(f"")

	print_colored("What has happened?\n1. total outage\n2. partial outage\n3. fibercut\n4. Other", 'yellow')
	number = input()
	if number == '4':
		custom_event = input("Please describe the event: ")
	else:
		custom_event = None

	event_choices = {
		'1': 'We have received messages that ' + location + ' is not available.',
		'2': 'We have received messages that some services at ' + location + ' are not available. (partial outage)',
		'3': 'We have received messages that there is a fibre cut at ' + location + '.',
		'4': custom_event
	}
	outage_fields['**What happened:** '] = event_choices.get(number, "Invalid choice")

	print_colored("Who is affected? List of the customer(s): ", 'yellow')
	customers = input()
	outage_fields['**Who\'s affected:** '] = customers

	print_colored("What is the impact?\n1. outage\n2. packet loss\n3. other", 'yellow')
	number = input()
	if number == '3':
		custom_impact = input("Please describe the impact: ")
	else:
		custom_impact = None

	impact_choices = {
		'1': '',
		'2': 'packet loss',
		'3': custom_impact
	}
	outage_fields['**Impact:** '] = impact_choices.get(number, "Invalid choice")

	print_colored("Have the affected customers been informed? (y/n): ", 'yellow')
	informed_choices = {
		'n': 'Not yet, but will do asap',
		'y': 'Customers were informed via Notifier'
	}

	number = input()
	outage_fields['**Customers informed:** '] = informed_choices.get(number, "Invalid choice")

	print_colored("What are we doing now/next?\n1. tshoot\n2. contact provider\n3. other", 'yellow')
	number = input()
	if number == '3':
		custom_next_step = input("Please describe the next step: ")
	else:
		custom_next_step = None

	next_step_choices = {
		'1': 'Investigate the issue and resolve it.',
		'2': 'Contacting our provider to resolve the issue.',
		'3': custom_next_step
	}
	outage_fields['**Next step:** '] = next_step_choices.get(number, "Invalid choice")

	print_colored("When is the next update incoming?\n1. in 2 hours\n2. next morning\n3. when we get response\n", 'yellow')
	next_update_choices = {
		'1': 'Next update comes in 2 hours.',
		'2': 'Next update comes at 8:00 in the morning.',
		'3': 'Next updates comes as soon as we get more information, but latest in 2 hours.'
	}

	number = input()
	outage_fields['**Next update:** '] = next_update_choices.get(number, "Invalid choice")

	time.sleep(2)

	output = "\n".join([f"{key} {value}" for key, value in outage_fields.items()])
	print_colored("\n" + output, 'green')

	try:
		input(colored('\nPress ENTER to exit', attrs=['dark']))
	except KeyboardInterrupt:
		pass
except KeyboardInterrupt:
	pass

#Return to the main menu
os.system("python3 mainmenu.py")