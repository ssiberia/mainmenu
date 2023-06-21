import os
from termcolor import colored
import requests

url = "https://engine-internal.anexia-it.com/api/config-management/v1/oncallduty.json"
params = {
    "api_key": "prbSXKkXuCqIycJE2bgg!1da-Z16nAr1"
}
response = requests.get(url, params=params)
data = response.json()
filtered_data = []

for level, item in data.items():
    filtered_item = {
        "Type": level,
        "first_name": item["first_name"],
        "last_name": item["last_name"],
        "email": item["email"],
        "phone": "+" + item["phone"]
    }
    filtered_data.append(filtered_item)


# print
print(colored("\nRegular phone numbers:", 'green'))
print(colored("- NO first level: ",'cyan'),end="")
print(colored("+4312650708",'white'))
print(colored("- NO second level: ",'cyan'),end="")
print(colored("+4312655675",'white'))
print(colored("- Security: ",'cyan'),end="")
print(colored("+4312655671\n", 'white'))

for item in filtered_data:
    if item["Type"] == 'first_level':
        item["Type"] = 'NO first lvl'
    elif item["Type"] == 'second_level':
        item["Type"] = 'NO second lvl'
    elif item["Type"] == 'first_security_level':
        item["Type"] = 'Security'
    print(colored(item["Type"],'yellow'))
    print(" " + item["first_name"] + " " + item["last_name"])
    print(colored("Email:" , 'cyan'), end="")
    print(item["email"])
    print(colored("Phone:", 'cyan'), end="")
    print(item["phone"])
    print(colored("---------------------", attrs=['dark']))


# Exit prompt
input(colored('\nPress ENTER to exit', attrs=['dark']))

# Return to the main menu
os.system("python3 mainmenu.py")
