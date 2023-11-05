import json
import os

import functions_framework
import requests
from bs4 import BeautifulSoup
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.vectorstores.chroma import Chroma


# Max number of pages of reviews to scrape. Each page contains 10 reviews.
YELP_REVIEWS_MAX_PAGES = int(os.environ["YELP_REVIEWS_MAX_PAGES"])
# Max number of documents to retrieve from vectorstore.
VECTORSTORE_MAX_DOCS = int(os.environ["VECTORSTORE_MAX_DOCS"])

YELP_PROMPT_TEMPLATE = """The following are customer reviews of a business:

BEGIN REVIEWS

{context}

END REVIEWS

Answer the following question based on the reviews: {question}

Follow the guidelines below when answering the question:
1. If something is mentioned in multiple reviews, it is important and more likely to be preferred in the answer.
2. If the reviews are of a restaurant, bar, or any food establishment, use specific names of dishes, drinks, and desserts.
"""


def clean_url(url: str) -> str:
    """Remove query string params from URL."""
    query_index = url.find("?")
    return url[:query_index] if query_index != -1 else url


def scrape_yelp_reviews(url: str) -> list[str]:
    """Scrape Yelp URL for reviews."""
    reviews = []

    for i in range(YELP_REVIEWS_MAX_PAGES):
        # start=0 is the first page, start=10 is the second page, etc.
        url_with_page = f"{url}&start={10*i}"
        print(f"Retrieving reviews from URL: {url_with_page}")
        response = requests.get(url_with_page)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            # Find the element containing reviews (use appropriate class or id)
            reviews_container = soup.find("div", id="reviews")
            
            # Find the individual reviews
            for review in reviews_container.find_all("li", class_="css-1q2nwpv"):
                # Extract review text
                review_text = review.find("span", class_="raw__09f24__T4Ezm").get_text(strip=True)
                reviews.append(review_text)
        else:
            print(
                f"Failed to retrieve the page '{url_with_page}'. "
                f"Status code: {response.status_code}"
            )

    print(f"Retrieved {len(reviews)} reviews")
    return reviews


def format_docs(docs) -> str:
    return "\n\n".join([d.page_content for d in docs])


@functions_framework.http
def main(request):
    # Set CORS headers for the preflight request
    if request.method == "OPTIONS":
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "3600",
        }

        return ("", 204, headers)
    
    headers = {"Access-Control-Allow-Origin": "*"}

    # parse request body
    req_body = request.get_json()
    yelp_url = req_body.get("yelp_url", "").strip()
    question = req_body.get("question", "").strip()
    print(f"Yelp URL: {yelp_url}, Question: {question}")

    # validate request body
    if not yelp_url or not question:
        return ('{"error": "Invalid request"}', 400, headers)
    
    # clean URL, append sort_by query param
    yelp_url = clean_url(yelp_url)
    yelp_url = f"{yelp_url}?sort_by=date_desc"

    # get Yelp reviews
    reviews = scrape_yelp_reviews(yelp_url)
    if len(reviews) == 0:
        return ('{"error": "No reviews"}', 500, headers)
    
    # embed reviews
    print("Loading reviews into vectorstore...")
    vectorstore = Chroma.from_texts(
        reviews,
        collection_name="yelp-reviews",
        embedding=OpenAIEmbeddings(),
    )
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": VECTORSTORE_MAX_DOCS}
    )

    # prompt GPT with Langchain
    prompt = ChatPromptTemplate.from_template(YELP_PROMPT_TEMPLATE)
    model = ChatOpenAI(model="gpt-4", temperature=0, top_p=1, max_tokens=1024)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | model
        | StrOutputParser()
    )

    print("Prompting GPT...")
    answer = chain.invoke(question)

    print(f"Recieved completion text: {answer}")
    resp = {"answer": answer}
    return (json.dumps(resp), 200, headers)
