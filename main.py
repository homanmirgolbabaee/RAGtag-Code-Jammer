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

# Set up Streamlit layout
st.title('Integrated Application')

# Sidebar for Vectara Semantic Search
st.sidebar.header('Vectara Semantic Search')

# Input for the Vectara query in the sidebar
vectara_query = st.sidebar.text_input("Enter your search query for Vectara:")


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

    response = requests.post(VECTARA_ENDPOINT, headers=headers, json=data)
    return response.json()


# Display Vectara search results
if vectara_query:
    with st.spinner('Searching Vectara...'):
        vectara_results = perform_vectara_search(vectara_query)
        if 'responseSet' in vectara_results:
            for result in vectara_results['responseSet'][0]['response']:
                text = result['text']
                score = result['score']
                st.sidebar.write(f"Score: {score} - Result: {text}")
        else:
            st.sidebar.write("No results found in Vectara.")


# Clarifai model invocation
st.header('Clarifai Model Response')

# Add a text input for the Clarifai model
clarifai_input = st.text_input('Enter some text for Clarifai Model:')



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
