import requests
from apikey import weather_api  # Import the weather API key from apikey.py

lat = 44.34
lon = 10.99
url = f"http://api.openweathermap.org/v1/current.json"

response = requests.get(url)
print(response.json())
