import os
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import re
import tempfile
import io
import base64
import json
import requests
import html
import shutil

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_PATH="chroma"

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email'
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_connection')
def check_connection():
    return jsonify({'connected': 'credentials' in session})

@app.route('/connect_drive')
def connect_drive():
    flow = Flow.from_client_secrets_file(
        'client_secrets.json',
        scopes=SCOPES)
    flow.redirect_uri = url_for('oauth2callback', _external=True)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')
    session['state'] = state
    return jsonify({'success': True, 'url': authorization_url})

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = Flow.from_client_secrets_file(
        'client_secrets.json',
        scopes=SCOPES,
        state=state)
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    return redirect(url_for('index'))

@app.route('/list_files')
def list_files():
    if 'credentials' not in session:
        return redirect(url_for('connect_drive'))
    credentials = Credentials(**session['credentials'])

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

    folder_id = request.args.get('folder_id', 'root')
    
    drive_service = build('drive', 'v3', credentials=credentials)
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents and (mimeType='application/pdf' or mimeType='application/vnd.google-apps.folder')",
        fields="nextPageToken, files(id, name, mimeType, webViewLink, webContentLink)").execute()
    items = results.get('files', [])

    return render_template('list_files.html', items=items, current_folder=folder_id)

@app.route('/get_files')
def get_files():
    if 'credentials' not in session:
        return redirect(url_for('connect_drive'))
    credentials = Credentials(**session['credentials'])

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

    folder_id = request.args.get('folder_id', 'root')
    
    drive_service = build('drive', 'v3', credentials=credentials)
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents and (mimeType='application/pdf' or mimeType='application/vnd.google-apps.folder')",
        fields="nextPageToken, files(id, name, mimeType, webViewLink, webContentLink)").execute()
    items = results.get('files', [])

    return jsonify(items)

@app.route('/ask', methods=['POST'])
def ask():
    question = request.form.get('question')
    search_mode = request.form.get('searchMode') == 'true'
    
    if search_mode:
        # Web search mode
        return web_search(question)
    else:
        # Document analysis mode
        file_id = request.form.get('file_id')
        if not file_id:
            return jsonify({'error': 'No file selected'}), 400
        return document_analysis(question, file_id)

def web_search(question):
    try:
        url = "https://google.serper.dev/search"
        payload = json.dumps({
        "q": question
        })
        headers = {
        'X-API-KEY': 'fdc1a0026c0e4a0c35101f139bb04e06f08ae569',
        'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)

        ans = json.loads(response.text)
        count = 0
        webpage_data = scrape_text_content(ans["organic"][0]["link"])

        PROMPT_TEMPLATE = f"""
        Answer the question based only on the following context:
        {webpage_data}
        ---
        Answer the question based on the above context: {question}
        Don't use your own knowledge and intelligence. If the answer is not in the give context, just respond with "Sorry, the answer is not present". 
        Don't hallucinate and give proper response. Make sure the answer is in 3-4 lines only and not long.
        """
        llm = ChatOpenAI(model="gpt-4o-mini")
        response_text = llm.invoke(PROMPT_TEMPLATE)
        links = ""
        for i in ans["organic"]:
            if count == 5:
                break
            links += i["link"] + "\n"
            count += 1
        reference_links = "\nBelow are the following reference links:\n" + links
        answer = response_text.content + reference_links
        print(answer)
        formatted_response = html.escape(answer).replace('\n', '<br>')
        return jsonify({'answer': formatted_response})
    except Exception as e:
        print("Error: ", str(e))


def scrape_text_content(url):
    try:
        # Send a GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        # Remove script and style elements
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
        
        # Get text from the remaining tags
        text = soup.get_text()
        
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Remove blank lines and join the text
        text = '\n'.join(chunk for chunk in chunks if chunk)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    except requests.RequestException as e:
        return f"An error occurred while fetching the webpage: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

def document_analysis(question, file_id):
    PROMPT_TEMPLATE = """
    Answer the question based only on the following context:
    {context}
    ---
    Answer the question based on the above context: {question}
    Don't use your own knowledge and intelligence. If the answer is not in the give context, just respond with "Sorry, the answer is not present". Don't hallucinate and give proper response.
    Remember, don't use your own knowledge and only give answer from the provided context.
    """
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=OpenAIEmbeddings())
    results = db.similarity_search_with_score(question, k=5)
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=question)

    llm = ChatOpenAI(model="gpt-4o-mini")
    response_text = llm.invoke(prompt)
    print(response_text.content)

    return jsonify({'answer': response_text.content})

@app.route('/process_file', methods=['POST'])
def process_file():
    if 'credentials' not in session:
        return jsonify({"error": "Not connected to Google Drive"}), 401

    data = request.get_json()
    if not data or 'file_id' not in data:
        return jsonify({"error": "No file_id provided"}), 400

    file_id = data['file_id']
    
    credentials = Credentials(**session['credentials'])
    drive_service = build('drive', 'v3', credentials=credentials)

    try:
        file_request = drive_service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, file_request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        file.seek(0)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(file.getvalue())
            temp_file_path = temp_file.name
        
        CHROMA_PATH = "chroma"
        if os.path.exists(CHROMA_PATH):
            shutil.rmtree(CHROMA_PATH)

        loader = PyPDFLoader(temp_file_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=500)
        chunks = text_splitter.split_documents(documents)
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=OpenAIEmbeddings())
        db.add_documents(chunks)
        # db.persist()
        
        print(f"File processed: {temp_file.name}")
        return jsonify({"success": True, "file_path": temp_file_path})
    except Exception as e:
        return jsonify({"error": f"Error downloading file: {str(e)}"}), 500
    
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # For development only
    app.run(debug=True)
