import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('TMDB_API_KEY')

url = f"https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}"
response = requests.get(url)

print(response.status_code)
print(response.json())