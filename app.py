#Change out of test API for stripe, get out of WCD sandbox instance, and deploy code on streamlit
import streamlit as st
from init_collection import create_collection, get_client
import os
# from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from unstructured.partition.pdf import partition_pdf
from stripe_helper import create_checkout_session

# Load environment variables
# _ = load_dotenv(find_dotenv())

openai_key = st.secrets["OPENAI_API_KEY"]
wcd_api_key = st.secrets["WCD_API_KEY"]
wcd_url = st.secrets["WCD_URL"]
stripe_secret_key = st.secrets["STRIPE_SECRET_KEY"]
success_url = st.secrets["SUCCESS_URL"]
cancel_url = st.secrets["CANCEL_URL"]

# Connect to Weaviate
client = get_client()

# Custom CSS for better styling
st.markdown("""
    <style>
    body {
        background-color: #d3d3d3;
        color: green;
    }
    .main {
        padding: 20px;
    }
    .title {
        font-size: 36px;
        font-weight: bold;
        color: #4CAF50;
        text-align: center;
    }
    .subtitle {
        font-size: 24px;
        font-weight: bold;
        color: #666;
        text-align: center;
        margin-bottom: 20px;
    }
    .header-green {
        color: white;
    }
    .button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
    }
    .warning {
        color: red;
        font-weight: bold;
    }
    .stTextInput label {
        color: white;
    }
    .stFileUploader label {
        color: white;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
    }
    .footer {
        position: fixed;
        bottom: 10px;
        right: 10px;
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
    }
    .footer img {
        height: 30px;
        margin-right: 10px;
    }
    .footer p {
        margin: 0;
        color: green;
        font-size: 14px;
    }
<style>
.footer {
    position: fixed;
    bottom: 10px;
    right: 10px;
    background-color: rgba(0, 0, 0, 0);
    border-radius: 10px;
    padding: 10px;
    box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    transition: transform 0.3s ease;
    text-decoration: none;
}
.footer:hover {
    transform: scale(1.1);
}
.footer p {
    margin: 0;
    color: green;
    font-size: 14px;
}
a.footer {
    text-decoration: none;
}
</style>
<a href="https://weaviate.io" target="_blank" class="footer">
    <div>
        <p>Powered by Weaviate</p>
    </div>
</a>


""", unsafe_allow_html=True)

# Streamlit interface
st.markdown('<div class="main">', unsafe_allow_html=True)
st.markdown('<div class="title" style="font-size: 48px;">PDFusion</div>', unsafe_allow_html=True)

# Value Proposition
st.markdown('<div class="subtitle" style="text-align: center; font-size: 24px;">Unlock the Full Potential of Your PDFs</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align: center; font-size: 18px; margin-bottom: 30px; ">Upload and search your PDF documents effortlessly. Pay to get started and enjoy seamless document management.</div>', unsafe_allow_html=True)


# Check if the client is ready
client_ready = client.is_ready()

# Function to check chunks
def check_chunks():
    collection_of_docs = client.collections.get("Document")
    result = collection_of_docs.aggregate.over_all()
    return result

# Function to insert chunks from a file
def insert_chunks_from_file(pdf_path):
    chunks = read_file(pdf_path)
    if not chunks:
        st.error("No chunks generated from the PDF file. Please check the file content.")
        return
    
    chunks_list = [{"content": chunk, "source": pdf_path} for chunk in chunks]
    
    if not chunks_list:
        st.error("No chunks to insert into Weaviate.")
        return

    docs = client.collections.get("Document")
    try:
        docs.data.insert_many(chunks_list)
        st.success(f"Inserted {len(chunks_list)} chunks into Weaviate.")
    except Exception as e:
        st.error(f"Failed to insert chunks: {e}")

def chunk_sizer(pdf_path):
    return int(0.05 * len(pdf_path))

# Function to read and partition the file
def read_file(pdf_path):
    partitions = partition_pdf(pdf_path)
    pdf_text = "\n".join([str(part) for part in partitions])
    chunks = list(get_chunks(pdf_text, 500))
    return chunks

# Function to split text into chunks
def get_chunks(text, chunk_size):
    for i in range(0, len(text), chunk_size):
        yield text[i:i + chunk_size]

# Function to perform search
def perform_search(query, prompt):
    collection_of_docs = client.collections.get("Document")
    response = collection_of_docs.generate.near_text(
        query=query,
        grouped_task=prompt,
        limit=2
    )
    return response

# Check if payment is done
query_params = st.query_params
if 'session_id' in query_params and query_params['session_id'][0] == 'success':
    st.session_state.payment_done = True

# Payment and file upload section
st.header("Upload and Process PDF")

# File upload button
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    if 'payment_done' not in st.session_state or not st.session_state.payment_done:
        st.markdown('<p class="warning">You must pay $0.99 before you can upload your PDF.</p>', unsafe_allow_html=True)
        if st.button("Pay $0.99", key="pay_button_upload"):
            # Create a checkout session
            session = create_checkout_session()
            if isinstance(session, dict) and session.get('url'):
                checkout_url = session.get('url')
                # Use JavaScript to redirect to the checkout URL
                st.write(f"""
                    <meta http-equiv="refresh" content="0; url={checkout_url}" />
                    """, unsafe_allow_html=True)
            else:
                st.error("Failed to create checkout session.")
    else:
        save_path = f"/tmp/{uploaded_file.name}"
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        insert_chunks_from_file(save_path)
        st.write(f"Inserted chunks from {uploaded_file.name}")

# Search section
st.markdown('<h2 class="header-green">Search Your Documents</h2>', unsafe_allow_html=True)
st.write("Easily search through your uploaded PDF documents.")
query = st.text_input("Enter your search query")
prompt = st.text_input("Enter your search prompt")

if st.button("Perform Search"):
    if 'payment_done' not in st.session_state or not st.session_state.payment_done:
        st.markdown('<p class="warning">You must pay $0.99 before you can use the search functionality.</p>', unsafe_allow_html=True)
    else:
        if query and prompt:
            search_results = perform_search(query, prompt)
            st.write("Search Results:")
            st.write(search_results.generated)
        else:
            st.write("Please enter both query and prompt.")

st.markdown('</div>', unsafe_allow_html=True)