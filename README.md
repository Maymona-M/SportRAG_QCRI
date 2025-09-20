# RAG System

---

This project implements a **Retrieval-Augmented Generation (RAG) system** with a Flask backend and a HTML/JavaScript frontend.

---

## How to Run

Follow these steps to get the RAG system up and running:

### 1. Setup Python Environment and Install Dependencies

From the **project's root directory**, SocioCulturalRAG, in your terminal:

1.  **Create a virtual environment:**

    python -m venv venv

2.  **Activate the virtual environment:**

    * **On macOS/Linux:**

        source venv/bin/activate

    * **On Windows (Command Prompt):**

        venv\Scripts\activate.bat


3.  **Install the required packages:**

    pip install -r requirements.txt


---

### 2. Start the Backend

Make sure your virtual environment is activated. Then, from the **project's root directory**, (SocioCulturalRAG), run the following command:

    python api/app.py

You'll see output indicating the RAG components are loading, followed by a message that Flask is running on `http://0.0.0.0:9610`.

### 3. Open the Frontend**

**Use Python's HTTP Server**
From the **project's root directory**, (SocioCulturalRAG), run the following command:

    cd frontend

    python -m http.server 8000

Then, open your web browser and go to `http://localhost:8000`.

---


## Usage


Once both the backend and frontend are running, you can type your queries into the web interface. You'll observe a sequence of messages (e.g., "Received user query...", "Fetching value resources...", etc.) appearing dynamically as the system processes your request, before the final AI-generated response is displayed.