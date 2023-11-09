import streamlit as st
import requests
#from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
#from clarifai_grpc.grpc.api import service_pb2, service_pb2_grpc
#from clarifai_grpc.grpc.api.status import status_code_pb2
#from clarifai_grpc.grpc.api import resources_pb2
from hugchat import hugchat
import requests
from urllib.parse import urlencode


## Chatbot 

def load_cookies_from_json(json_filepath):
    with open(json_filepath, 'r') as f:
        #cookies_dict = json.load(f)
        cookies_dict= None
    return cookies_dict

# It's assumed here that `cookies` is already a dictionary with your authentication cookies.
# NEVER hardcode your credentials. Use Streamlit secrets for this.
def secure_get_cookies():
    pass

def init_chatbot():
    # Assuming you have a method to securely obtain cookies
    cookies = load_cookies_from_json("cookies.json")
    return hugchat.ChatBot(cookies=cookies)

chatbot = init_chatbot()

def get_vectara_jwt(client_id, client_secret, auth_url):
    # The data to be sent with the POST request
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Sending a POST request to retrieve the JWT token
    response = requests.post(auth_url, data=urlencode(data), headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the token from the response
        jwt_token = response.json().get('access_token')
        return jwt_token
    else:
        raise Exception(f"Error retrieving JWT token: {response.text}")








# Retrieve the PAT from the environment variable and Vectara API Key
PAT = st.secrets['CLARIFAI_PAT']
VECTARA_API_KEY = st.secrets['VECTARA_API_KEY']

# Function to perform the Vectara search

def perform_vectara_search(query):
    VECTARA_ENDPOINT = "https://api.vectara.io/v1/query"
    CUSTOMER_ID = st.secrets['CUSTOMER_ID'] # Replace with your customer ID
    CORPUS_ID =  st.secrets['CORPUS_ID']# Replace with your corpus ID

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
    stored_results = {}
    if 'responseSet' in vectara_results:
        for result in vectara_results['responseSet'][0]['response']:
            text = result['text']
            score = result['score']
            if score not in stored_results:
                # If the score doesn't exist as a key, create a new list
                stored_results[score] = [text]
            else:
                # If the score does exist, append the text to the existing list
                stored_results[score].append(text)
                
                
            # Using columns to align score and text neatly
            col1, col2 = st.columns([1, 4])
            
            with col1:
                st.metric(label="Score", value=f"{score:.2f}")
            
            with col2:
                st.text_area("", value=text, height=100, key=f"result_{score}", disabled=True)
    else:
        st.error("No results found in Vectara.")
    print(stored_results)
    highest_score, highest_score_texts = find_highest_score_and_texts(stored_results)
    print(f"Highest Score: {highest_score}")
    print("Texts with the highest score:")
    for text in highest_score_texts:
        print(text)


def upload_file_to_vectara(file,doc_metadata):
    VECTARA_UPLOAD_ENDPOINT = "https://api.vectara.io/v1/upload"
    customer_id = st.secrets['CUSTOMER_ID']
    corpus_id = st.secrets['CORPUS_ID']
    client_id = st.secrets['client_id']
    client_secret = st.secrets['client_secret']
    auth_url = st.secrets['auth_url']

    jwt_token = get_vectara_jwt(client_id, client_secret, auth_url)
    jwt_token = str(jwt_token)
    #jwt_token = os.getenv('VECTARA_JWT')  # Add your JWT token to your .env file

    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'grpc-timeout': '30S'
    }
    
    files = {
        'file': (file.name, file, 'application/octet-stream'),
        'doc_metadata': (None, doc_metadata, 'application/json')
    }
    
    params = {
        'c': customer_id,
        'o': corpus_id,
    }
    
    try:
        response = requests.post(VECTARA_UPLOAD_ENDPOINT, headers=headers, files=files, params=params)
        if response.status_code == 200:
            return {"success": True, "message": "File uploaded successfully!"}
        else:
            return {"success": False, "message": response.text}
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": str(e)}

def find_highest_score_and_texts(stored_results):
    # If stored_results is empty, return None
    if not stored_results:
        return None, None
    
    # Get the highest score (Python dictionaries are unordered, so we need to sort by key)
    highest_score = max(stored_results.keys())
    # Get all texts associated with the highest score
    highest_score_texts = stored_results[highest_score]
    
    return highest_score, highest_score_texts


# Initialize Streamlit application
st.set_page_config(page_title='RAGtag Code Jammer', layout='wide')
# Title and description
st.title('🤖RAGtag Customer Assistant')
st.caption('Click Here for Tutorial')
option = st.sidebar.radio('Choose a service:', ('🤗Clarifai', '✔️Vectara', '💬Chatbot','🛠️Upload Comming Soon'))

'''
if option == '🤗Clarifai':
        st.header('Clarifai Model Response')
        clarifai_input = st.text_area('Enter text for Clarifai Model:', height=100)
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
'''
    
if option =="✔️Vectara":
    st.header('Vectara Semantic Search')
    vectara_query = st.text_input("Enter your search query:")     

    if vectara_query:
        with st.expander("Vectara Search Results"):
            vectara_results = perform_vectara_search(vectara_query)
            
            # Using an expander to show results
        with st.expander("Vectara Search Results", expanded=True):
            vectara_results = perform_vectara_search(vectara_query)
            display_vectara_results(vectara_results)
         # Text box for user input
         
    
if option == "💬Chatbot":
    # Assiging a role 
    
    
    prompt = st.chat_input("Say something")

    if prompt:
        message = st.chat_message("assistant")
        #st.write(f"User has sent the following prompt: {prompt}")
        message.write(prompt)
        # Get the chatbot's response
        query_result = chatbot.query(prompt)

        # Display the response
        #st.text_area("Chatbot says:", value=query_result["text"], height=200, max_chars=None, key=None)    
        message.write("🧠 Thinking ...")
        message.write(query_result["text"])
        
        
if option =="🛠️Upload Comming Soon":
    st.header('Vectara Document Upload')
    uploaded_file = st.file_uploader("Choose a file to upload")
    doc_metadata = '{"filesize": 1234}'  # This should be modified according to your metadata needs.
    
    if uploaded_file is not None:
        # Process the file upload
        if st.button('Upload to Vectara'):
            with st.spinner('Uploading...'):
                result = upload_file_to_vectara(uploaded_file, doc_metadata)
                if result['success']:
                    st.success(result['message'])
                else:
                    st.error(result['message'])      
        
