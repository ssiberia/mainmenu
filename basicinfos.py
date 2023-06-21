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

print(str(response))

for level, item in data.items():
    filtered_item = {
        "first_name": item["first_name"],
        "last_name": item["last_name"],
        "email": item["email"],
        "phone": item["phone"]
    }
    filtered_data.append(filtered_item)


# print
print(colored("\nPhone numbers:", 'blue'))

for item in filtered_data:
    print("First Name:", item["first_name"])
    print("Last Name:", item["last_name"])
    print("Email:", item["email"])
    print("Phone:", item["phone"])
    print("-------------------")	


# Exit prompt
input(colored('\nPress ENTER to exit', attrs=['dark']))

# Return to the main menu
os.system("python3 mainmenu.py")
