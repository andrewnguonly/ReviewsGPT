import langchain
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

langchain.debug = True
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
    max_pages = 5
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

biz_url = "https://www.yelp.com/biz/hatchet-hall-los-angeles"
reviews = scrape_yelp_reviews(f"{biz_url}?sort_by=date_desc")

# Embed reviews
vectorstore = Chroma.from_texts(
    reviews,
    collection_name="yelp-reviews",
    embedding=OpenAIEmbeddings(),
)
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 20})
query = "What are the favorite foods or drinks to try? Be specific. Return a list of 10 items."
query_2 = "What are some foods or drinks to avoid? What was bad or regrettable?"
# reviews = vectorstore.similarity_search(query, k=20)

for i, review in enumerate(reviews):
    pass
    # print(f"review #{i}:", review.page_content, "\n")

template = """The following are customer reviews of a restaurant or bar:

BEGIN REVIEWS

{context}

END REVIEWS

If something is mentioned in multiple reviews, it is more likely to be preferred in the answer.
Use specific names of dishes, drinks, and cocktails.

Answer the following question based on the reviews: {question}
"""
prompt = ChatPromptTemplate.from_template(template)
model = ChatOpenAI(model="gpt-4", temperature=0, top_p=1, max_tokens=1024)

def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])

chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

print(chain.invoke(query))
