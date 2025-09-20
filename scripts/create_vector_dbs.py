# scripts/create_vector_dbs.py

from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import json
import os
import numpy as np # Still good to have for general numeric operations if needed, though not directly used for embedding in this LangChain flow.

# --- Configuration ---
VALUE_JSON_PATH = os.path.join("data", "value_resources.json")
CULTURAL_JSON_PATH = os.path.join("data", "cultural_resources.json") # Path for your cultural data
FAISS_BASE_DIR = "vector2_db" # Base directory for FAISS databases
VALUE_FAISS_DIR = os.path.join(FAISS_BASE_DIR, "value_advice_db")
CULTURAL_FAISS_DIR = os.path.join(FAISS_BASE_DIR, "cultural_info_db")
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# --- Load Embedding Model ---
# The HuggingFaceEmbeddings class handles loading the tokenizer and model internally
print(f"Initializing embedding model: {EMBEDDING_MODEL_NAME}")
embedder = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
print("Embedding model initialized.")

# --- Helper function to load JSON and create LangChain Documents ---
def load_and_prepare_documents(json_path, doc_type="value"):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            articles = json.load(f)
        print(f"✅ Successfully loaded {len(articles)} {doc_type} documents from '{json_path}'.")
    except FileNotFoundError:
        print(f"❌ Error: JSON file not found at '{json_path}'. Please check the path.")
        return []
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode JSON from '{json_path}'. Check file format.")
        return []

    documents_for_faiss = []
    for item in articles:
        text_for_embedding = ""
        metadata = {}

        if doc_type == "value":
            # --- Logic for Value Resources (as per your previous project) ---
            if "synthesized_output" not in item:
                print(f"⚠️ Warning: Skipping value item as 'synthesized_output' key is missing: {item.get('pdf_filename', 'N/A')}")
                continue

            synthesized_data = item["synthesized_output"]
            pdf_filename = item.get("pdf_filename", "unknown_filename.pdf")

            text_for_embedding = synthesized_data.get("paper_name", "")
            if synthesized_data.get("keywords"):
                text_for_embedding += " " + ", ".join(synthesized_data["keywords"])

            if "extracted_sociocultural_elements_from_paper" in synthesized_data:
                for meta_type, elements in synthesized_data["extracted_sociocultural_elements_from_paper"].items():
                    if isinstance(elements, dict):
                        for key, val in elements.items():
                            if val.get("concept"):
                                text_for_embedding += " " + val["concept"]
                            if val.get("description"):
                                text_for_embedding += " " + val["description"]
                    elif isinstance(elements, list):
                        for elem in elements:
                            if elem.get("name"):
                                text_for_embedding += " " + elem["name"]
                            if elem.get("description"):
                                text_for_embedding += " " + elem["description"]

            if synthesized_data.get("conclusion_of_how_collected_information_from_resource_would_inform_generating_a_response_for_user_if_any"):
                for guidance_entry in synthesized_data["conclusion_of_how_collected_information_from_resource_would_inform_generating_a_response_for_user_if_any"]:
                    if guidance_entry.get("llm_response_guidance"):
                        text_for_embedding += " " + guidance_entry["llm_response_guidance"]

            metadata = {
                "pdf_filename": pdf_filename,
                "full_data": item # Store the ENTIRE original item
            }

        elif doc_type == "cultural":
            # --- Logic for Cultural Resources (based on your bare-bones structure) ---
            text_for_embedding = (
                f"Cultural Element: {item.get('cultural_element_name', '')}. "
                f"Region: {item.get('region', '')}. "
                f"Description: {item.get('description', '')}. "
                f"Examples: {', '.join(item.get('examples', []))}"
            )
            metadata = {
                "cultural_id": item.get('cultural_id'),
                "cultural_element_name": item.get('cultural_element_name'),
                "full_data": item # Store the ENTIRE original item
            }
        
        # Only add if we have content for embedding
        if text_for_embedding.strip():
            documents_for_faiss.append(Document(
                page_content=text_for_embedding.strip(),
                metadata=metadata
            ))

    print(f"Prepared {len(documents_for_faiss)} {doc_type} documents for FAISS indexing.")
    return documents_for_faiss

# --- Main Execution ---
if __name__ == "__main__":
    os.makedirs(FAISS_BASE_DIR, exist_ok=True)

    # --- Process Value Resources ---
    value_docs = load_and_prepare_documents(VALUE_JSON_PATH, "value")
    if value_docs:
        print(f"Creating FAISS DB for value resources in '{VALUE_FAISS_DIR}'...")
        try:
            value_db = FAISS.from_documents(value_docs, embedder)
            value_db.save_local(VALUE_FAISS_DIR)
            print(f"✅ Value advice DB created and saved to `{os.path.abspath(VALUE_FAISS_DIR)}`.")
        except Exception as e:
            print(f"❌ Error creating/saving value FAISS DB: {e}")
    else:
        print("Skipping value DB creation due to no documents.")

    print("-" * 50) # Separator for clarity

    # --- Process Cultural Resources ---
    cultural_docs = load_and_prepare_documents(CULTURAL_JSON_PATH, "cultural")
    if cultural_docs:
        print(f"Creating FAISS DB for cultural resources in '{CULTURAL_FAISS_DIR}'...")
        try:
            cultural_db = FAISS.from_documents(cultural_docs, embedder)
            cultural_db.save_local(CULTURAL_FAISS_DIR)
            print(f"✅ Cultural information DB created and saved to `{os.path.abspath(CULTURAL_FAISS_DIR)}`.")
        except Exception as e:
            print(f"❌ Error creating/saving cultural FAISS DB: {e}")
    else:
        print("Skipping cultural DB creation due to no documents.")

    print("\nFAISS DB creation process complete.")