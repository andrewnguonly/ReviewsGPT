import requests
from bs4 import BeautifulSoup


def scrape_yelp_reviews(url):
    # Send a GET request to the Yelp business page
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the element containing reviews (use appropriate class or id)
        reviews_container = soup.find('div', id='reviews')

        # Extract individual reviews
        reviews = []
        for review in reviews_container.find_all('li', class_='css-1q2nwpv'):
            # Extract review text
            review_text = review.find('span', class_='raw__09f24__T4Ezm').get_text(strip=True)

            # Extract other information if needed (e.g., rating, date, etc.)
            # rating = review.find('div', class_='lemon--div__373c0__1mboc i-stars__373c0__1T6rz i-stars--regular-4__373c0__2Yrj1 border-color--default__373c0__3-ifU').get('aria-label')

            # Append the review to the list
            reviews.append(review_text)

        return reviews
    else:
        # Print an error message if the request was not successful
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
        return None

# Example usage
url = "https://www.yelp.com/biz/wunderbar-san-mateo-2?start=0&sort_by=date_desc"
reviews = scrape_yelp_reviews(url)

if reviews:
    for i, review in enumerate(reviews, start=1):
        print(f"Review {i}: {review}")
