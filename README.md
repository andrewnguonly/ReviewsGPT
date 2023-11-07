# ReviewsGPT
Ask any question, get answers from Yelp reviews.

> _What's the best dish to try?_

ReviewsGPT is a simple RAG LLM app that scrapes Yelp reviews and queries them using OpenAI's GPT-4. The app's implementation is based off Langchain's [rag-chroma](https://github.com/langchain-ai/langchain/tree/master/templates/rag-chroma) template and productionized as a stand-alone function that can be deployed to any serverless compute platform.

# Deployment
## Environment Variables
1. OPENAI_API_KEY: OpenAI API key.
1. YELP_REVIEWS_MAX_PAGES: Maximum number of pages of reviews to scrape per business. Each page has 10 reviews.
1. VECTORSTORE_MAX_DOCS: Maximum number of reviews to retrieve from vectorstore.

## Google Cloud Functions
The function should be deployed to Google's Cloud Functions platform. However, the function can be easily modified to run in any serverless compute platform (e.g. AWS Lambda).

Call the function (via API):
```
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"yelp_url": "https://www.yelp.com/biz/garaje-san-francisco", "question": "What's the best dish to try?"}' \
  https://region-project-id.cloudfunctions.net/function_name
```

# Web Client
[ReviewGPT-Web](https://github.com/andrewnguonly/ReviewsGPT-Web) is a simple React app that calls the function via API.
