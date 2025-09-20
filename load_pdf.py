import os
import json
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings

# --- Configuration ---
PDF_DIR = 'Articles_for_rag'  # Folder with your PDFs
INDEX_DIR = "vector2_db"  # Output FAISS index folder
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# --- Helper: Extract title, author, year from filename ---
def parse_metadata(fname):
    base = fname.replace(".pdf", "")
    parts = [p.strip() for p in base.split(",")]
    title = parts[0] if len(parts) > 0 else "Unknown"
    author_name = parts[1]
    year = str(parts[2]) if len(parts) > 2 and parts[2].isdigit() else "2024"
    author = [{"name": author_name}]
    print(author)
    print(type(author_name))
    return title, author, year

# --- Step 1: Load PDFs and assign metadata ---
all_docs = []
corpus_id_map = {}

for i, fname in enumerate(os.listdir(PDF_DIR)):
    if not fname.endswith(".pdf"):
        continue

    print(f"🔍 Loading: {fname}")
    path = os.path.join(PDF_DIR, fname)
    loader = PyPDFLoader(path)
    pages = loader.load()

    title, author, year = parse_metadata(fname)
    corpus_id = str(i)
    corpus_id_map[corpus_id] = f"{title}, {author[0]['name'] if author else 'Unknown'}, {year}"

    for page in pages:
        page.metadata = {
            "corpus_id": corpus_id,
            "title": title,
            "authors": author,
            "year": year,
            "abstract": ""
        }

    all_docs.extend(pages)

print(f"✅ Loaded {len(all_docs)} total pages from {len(corpus_id_map)} PDFs")

# --- Step 2: Split into chunks ---
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP
)

chunks = splitter.split_documents(all_docs)
print(f"🧩 Created {len(chunks)} chunks")

# --- Step 3: Embed using HuggingFace ---
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# --- Step 4: Create FAISS index ---
vectorstore = FAISS.from_documents(chunks, embedding_model)

# --- Step 5: Save index and corpus map ---
vectorstore.save_local(INDEX_DIR)

with open(os.path.join(INDEX_DIR, "corpus_id_map.json"), "w") as f:
    json.dump(corpus_id_map, f, indent=2)

print(f"✅ Saved FAISS index to '{INDEX_DIR}' with {len(chunks)} chunks")
