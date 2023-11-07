import streamlit as st
import os
import requests
import json
from dotenv import load_dotenv
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2
from clarifai_grpc.grpc.api import resources_pb2


# Load the environment variables from the .env file
load_dotenv("secrets.env")

# Retrieve the PAT from the environment variable and Vectara API Key
PAT = os.getenv('CLARIFAI_PAT')
VECTARA_API_KEY = os.getenv('VECTARA_API_KEY')  # Assuming you have stored Vectara API Key in the .env file


# Function to perform the Vectara search

def perform_vectara_search(query):
    VECTARA_ENDPOINT = "https://api.vectara.io/v1/query"
    CUSTOMER_ID = str(os.getenv('CUSTOMER_ID')) # Replace with your customer ID
    CORPUS_ID =  str(os.getenv('CORPUS_ID'))# Replace with your corpus ID

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'customer-id': CUSTOMER_ID,
        'x-api-key': VECTARA_API_KEY,
    }

    data = {
        "query": [
            {
                "query": query,
                "start": 0,
                "numResults": 10,
                "corpusKey": [
                    {
                        "customerId": int(CUSTOMER_ID),
                        "corpusId": int(CORPUS_ID),
                        "semantics": "DEFAULT",
                        "metadataFilter": "part.lang = 'eng'",
                    }
                ],
            }
        ]
    }

    try:
        response = requests.post(VECTARA_ENDPOINT, headers=headers, json=data)
        # Check if the request was successful
        if response.status_code == 200:
            return response.json()
        else:
            # Log the status code and response content for debugging
            st.error(f"Error in Vectara API request: Status code {response.status_code}")
            st.json(response.json())
            return None
    except requests.exceptions.RequestException as e:
        # Handle any errors that occur during the request
        st.error(f"An error occurred while making a request to Vectara: {e}")
        return None
  

def display_vectara_results(vectara_results):
    if 'responseSet' in vectara_results:
        for result in vectara_results['responseSet'][0]['response']:
            text = result['text']
            score = result['score']
            
            # Using columns to align score and text neatly
            col1, col2 = st.columns([1, 4])
            
            with col1:
                st.metric(label="Score", value=f"{score:.2f}")
            
            with col2:
                st.text_area("", value=text, height=100, key=f"result_{score}", disabled=True)
    else:
        st.error("No results found in Vectara.")






# Initialize Streamlit application
st.set_page_config(page_title='Customer Service Chatbot', layout='wide')
st.title('Customer Service Chatbot')

# Sidebar settings and queries
with st.sidebar:
    st.header('Settings')
    st.caption('Configure your bot settings here.')

    # Sidebar for Vectara Semantic Search
    st.header('Vectara Semantic Search')
    vectara_query = st.text_input("Enter your search query:")

# Main content layout
with st.container():
    col1, col2 = st.columns((1, 2))  # Adjust the ratio as per your UI need
    with col1:
        st.header('Clarifai Model Response')
        clarifai_input = st.text_input('Enter text for Clarifai Model:')
        # Button to trigger Clarifai model inference
        if st.button('Generate Response'):
            with st.spinner("Processing with Clarifai..."):
                # Set up the connection and authentication
                channel = ClarifaiChannel.get_grpc_channel()
                stub = service_pb2_grpc.V2Stub(channel)
                metadata = (('authorization', 'Key ' + PAT),)

                # Create user data object
                userDataObject = resources_pb2.UserAppIDSet(user_id='openai', app_id='chat-completion')

                # Make the API call for Clarifai
                post_model_outputs_response = stub.PostModelOutputs(
                    service_pb2.PostModelOutputsRequest(
                        user_app_id=userDataObject,
                        model_id='GPT-4',
                        version_id='222980e6d13341a5a3d892e63dda1f9e',
                        inputs=[
                            resources_pb2.Input(
                                data=resources_pb2.Data(
                                    text=resources_pb2.Text(
                                        raw=clarifai_input
                                    )
                                )
                            )
                        ]
                    ),
                    metadata=metadata
                )

                # Check the response status
                if post_model_outputs_response.status.code != status_code_pb2.SUCCESS:
                    st.error(f"An error occurred with Clarifai: {post_model_outputs_response.status.description}")
                else:
                    # Display the output
                    output = post_model_outputs_response.outputs[0].data.text.raw
                    st.success("Analysis Complete with Clarifai")
                    st.write("Response:")
                    st.write(output)
    with col2:
        if vectara_query:
            with st.expander("Vectara Search Results"):
                vectara_results = perform_vectara_search(vectara_query)
                
                # Using an expander to show results
            with st.expander("Vectara Search Results", expanded=True):
                vectara_results = perform_vectara_search(vectara_query)
                display_vectara_results(vectara_results)



