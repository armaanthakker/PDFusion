import os
from dotenv import load_dotenv, find_dotenv
import weaviate
from weaviate.classes.config import Configure, Property, DataType

# Load environment variables
_ = load_dotenv(find_dotenv())

# Connect to Weaviate
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=os.getenv("WCD_URL"),
    auth_credentials=weaviate.auth.AuthApiKey(os.getenv("WCD_API_KEY")),
    headers={
        "X-OpenAI-Api-Key": os.environ["OPENAI_APIKEY"]
    }
)

# Function to create collection
def create_collection():
    if not client.collections.exists("Document"):
            client.collections.create(
                name="Document",
                properties=[
                    wc.Property(name="content", data_type=wc.DataType.TEXT),
                    wc.Property(name="source", data_type=wc.DataType.TEXT, skip_vectorization=True)
                ],
                vectorizer_config=wc.Configure.Vectorizer.text2vec_openai(),
                generative_config=wc.Configure.Generative.openai()
            )
            return collection_of_docs
    else:
        return client.collections.get("Document")



def get_client():
    return client

# Create the collection when this script is run
if __name__ == "__main__":
    create_collection()

print("Running init_collection.py")