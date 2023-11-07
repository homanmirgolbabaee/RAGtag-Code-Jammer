import streamlit as st
import os
from dotenv import load_dotenv
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2
from clarifai_grpc.grpc.api import resources_pb2

# Load the environment variables from the .env file
load_dotenv("secrets.env")

# Retrieve the PAT from the environment variable
PAT = os.getenv('CLARIFAI_PAT')

# Set up Streamlit layout
st.title('GPT-4 Chatbot')


# Input text box for user to enter text
user_input = st.text_area("Enter text to analyze:", "I love your product very much")

# Button to trigger model inference
if st.button('Generate Response'):
    with st.spinner("Processing..."):
        # Set up the connection and authentication
        channel = ClarifaiChannel.get_grpc_channel()
        stub = service_pb2_grpc.V2Stub(channel)
        metadata = (('authorization', 'Key ' + PAT),)

        # Create user data object
        userDataObject = resources_pb2.UserAppIDSet(user_id='openai', app_id='chat-completion')

        # Make the API call
        post_model_outputs_response = stub.PostModelOutputs(
            service_pb2.PostModelOutputsRequest(
                user_app_id=userDataObject,
                model_id='GPT-4',
                version_id='222980e6d13341a5a3d892e63dda1f9e',
                inputs=[
                    resources_pb2.Input(
                        data=resources_pb2.Data(
                            text=resources_pb2.Text(
                                raw=user_input
                            )
                        )
                    )
                ]
            ),
            metadata=metadata
        )

        # Check the response status
        if post_model_outputs_response.status.code != status_code_pb2.SUCCESS:
            st.error(f"An error occurred: {post_model_outputs_response.status.description}")
        else:
            # Display the output
            output = post_model_outputs_response.outputs[0].data.text.raw
            st.success("Analysis Complete")
            st.write("Response:")
            st.write(output)