import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.pydantic_v1 import BaseModel
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableParallel, RunnablePassthrough
from langchain.vectorstores.chroma import Chroma


load_dotenv()

# Example for document loading (from url), splitting, and creating vectostore
""" 
# Load
from langchain.document_loaders import WebBaseLoader
loader = WebBaseLoader("https://lilianweng.github.io/posts/2023-06-23-agent/")
data = loader.load()

# Split
from langchain.text_splitter import RecursiveCharacterTextSplitter
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
all_splits = text_splitter.split_documents(data)

# Add to vectorDB
vectorstore = Chroma.from_documents(documents=all_splits, 
                                    collection_name="rag-chroma",
                                    embedding=OpenAIEmbeddings(),
                                    )
retriever = vectorstore.as_retriever()
"""
def scrape_yelp_reviews(url) -> list[str]:
    max_pages = 3
    reviews = []

    for i in range(max_pages):
        # Send a GET request to the Yelp business page
        url_with_page = f"{url}&start={10*i}"
        response = requests.get(url_with_page)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the page
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the element containing reviews (use appropriate class or id)
            reviews_container = soup.find('div', id='reviews')

            # Extract individual reviews
            
            for review in reviews_container.find_all('li', class_='css-1q2nwpv'):
                # Extract review text
                review_text = review.find('span', class_='raw__09f24__T4Ezm').get_text(strip=True)

                # Extract other information if needed (e.g., rating, date, etc.)
                # rating = review.find('div', class_='lemon--div__373c0__1mboc i-stars__373c0__1T6rz i-stars--regular-4__373c0__2Yrj1 border-color--default__373c0__3-ifU').get('aria-label')

                # Append the review to the list
                reviews.append(review_text)

            
        else:
            # Print an error message if the request was not successful
            print(f"Failed to retrieve the page. Status code: {response.status_code}")

    return reviews

reviews = scrape_yelp_reviews("https://www.yelp.com/biz/abv-san-francisco-2?sort_by=date_desc")

# Embed reviews
vectorstore = Chroma.from_texts(
    reviews,
    collection_name="yelp-reviews",
    embedding=OpenAIEmbeddings(),
)
retriever = vectorstore.as_retriever()
query = "What are the favorite foods or drinks to try? Be specific. Return a list of 5 items."
reviews = vectorstore.similarity_search(query)

template = """The following are customer reviews of a restaurant or bar:

{context}

Answer the following question based on the reviews: {question}

The answers that are mentioned in multiple reviews are more likely to be preferred.
"""
prompt = ChatPromptTemplate.from_template(template)
model = ChatOpenAI()

def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])

chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

print(chain.invoke(query))
