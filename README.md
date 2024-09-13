# QnA RAG Bot

## Overview

The QnA RAG (Retrieve and Generate) Bot is a Python-based solution that enables users to upload files from Google Drive or search the web to ask questions and get answers from a Large Language Model (LLM). The bot provides two functionalities:

1. **File-based QnA:** Users can upload a file from Google Drive, which is processed and stored in vector embeddings using a Chroma database. Users can then ask questions based on the uploaded file's content.
   
2. **Web-based QnA:** Users can search the web using the Serper API, extract content from the retrieved links using BeautifulSoup, and ask questions based on the extracted information.

## Features

- **Google Drive Integration:** Upload files directly from Google Drive.
- **Chroma Database for Vector Storage:** Store file embeddings to enable fast and accurate retrieval-based questioning.
- **Web Search Integration:** Search the web with Serper API and extract text from web pages using BeautifulSoup for QnA.
- **UI Toggle:** A checkbox allows users to switch between file-based QnA and web-based QnA.
- **LLM Model:** OpenAI's `gpt-4o-mini` is used for generating answers based on the provided context.
- **Embeddings:** OpenAI’s embedding model is used for creating vector embeddings for the file content.

## Tech Stack

- **Language:** Python
- **LLM Model:** OpenAI `gpt-4o-mini`
- **Embedding Model:** OpenAI Embeddings API
- **Database:** Chroma Database for storing vector embeddings
- **Web Scraping:** BeautifulSoup for extracting text from URLs
- **API Integration:** Serper API for web search
- **File Processing:** Google Drive API for uploading and accessing files

## How It Works

### File-based QnA

1. **Connect Google Drive:** Users connect their Google Drive account to the application.
2. **Upload File:** The user selects a file from their Drive, which is then processed.
3. **Vector Embeddings:** The file's content is converted into vector embeddings using OpenAI’s embedding model and stored in the Chroma database.
4. **Ask Questions:** Users can ask questions related to the uploaded file, and the LLM (`gpt-4o-mini`) will generate an answer based on the file content.

### Web-based QnA

1. **Web Search:** Users can search the web using a query. The query is passed to Serper API, which retrieves relevant URLs.
2. **Extract Text:** The content from the URLs is extracted using BeautifulSoup.
3. **Ask Questions:** The extracted text is passed along with the query to the LLM for generating answers.

**Checkbox Toggle:** The user interface includes a checkbox to switch between file-based and web-based QnA. When checked, the web search functionality is enabled, otherwise, the bot will default to file-based QnA.

## Prerequisites

- Python 3.8+
- OpenAI API Key
- Google Cloud credentials for Google Drive API
- Serper API Key

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-repo/qna-rag-bot.git
   cd qna-rag-bot
2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
4. Set up your environment variables for OpenAI API, Google Cloud credentials, and Serper API key.

5. Run the application:
   
   ```bash
   python app.py

## Usage
 - **Run the Application:** Once the application is running, users can access the UI to upload files or search the web.
 - **Select Mode:** Use the checkbox to toggle between file-based QnA or web-based QnA.
 - **Ask Questions:** Enter a question in the input field and click submit to get an answer from the LLM.