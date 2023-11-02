import os

import requests
from dotenv import load_dotenv


load_dotenv()
YELP_API_KEY = os.environ["YELP_API_KEY"]


host = "https://api.yelp.com"

# alias can be parsed from business page URL
# example: https://www.yelp.com/biz/wunderbar-san-mateo-2
business_id_or_alias = "wunderbar-san-mateo-2"

# this API only returns 3 reviews...
path = f"v3/businesses/{business_id_or_alias}/reviews?limit=100&sort_by=newest"

url = f"{host}/{path}"

headers = {
    "Authorization": f"Bearer {YELP_API_KEY}",
    "accept": "application/json"
}
response = requests.get(url, headers=headers)

print(response.text)
