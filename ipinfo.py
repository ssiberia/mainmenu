import os
import json
import folium
import socket
import webbrowser
from termcolor import colored
import re
from folium.plugins import AntPath

def get_location(ip):
    try:
        response = os.popen(f"curl -s http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,query")
        data = json.load(response)
        if data["status"] == "success":
            return data
        else:
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def extract_ips(mtr_output):
    ip_pattern = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
    ips = ip_pattern.findall(mtr_output)
    return ips

print(colored("\nPlease paste your MTR results and press Ctrl+C when you're done: ", 'blue'))
try:
    mtr_output = ""
    while True:
        mtr_output += input() + "\n"
except KeyboardInterrupt:
    pass

ips = extract_ips(mtr_output)

m = folium.Map(location=[0, 0], zoom_start=2)
locations = []

total_hops = len(ips)
for i, ip in enumerate(ips, start=1):
    location = get_location(ip)
    if location:
        lat = location["lat"]
        lon = location["lon"]
        locations.append([lat, lon])
        folium.Marker(
            [lat, lon],
            popup=f"{ip}",
            tooltip=f"{location['city']}, {location['regionName']}, {location['country']}"
        ).add_to(m)

for i in range(len(locations) - 1):
    AntPath([locations[i], locations[i+1]], color="blue", weight=2.5, opacity=1).add_to(m)

m.save("mtr_map.html")
print(colored("\nThe MTR map has been saved as mtr_map.html", "green"))

# Open the HTML file with the default viewer
webbrowser.open("mtr_map.html")

# Exit prompt
input(colored('\nPress ENTER to exit', attrs=['dark']))

# Return to the main menu
os.system("python mainmenu.py")
