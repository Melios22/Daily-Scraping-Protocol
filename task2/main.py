import argparse
import io
import os
import time

from dotenv import load_dotenv
from langchain_text_splitters import MarkdownHeaderTextSplitter
from openai import OpenAI


def setup_configuration():
    """Sets up configuration by parsing arguments and loading environment variables."""
    # Parse command line arguments for API key, assistant ID, and data folder
    parser = argparse.ArgumentParser(
        description="Chunk and upload markdown files to an OpenAI Vector Store."
    )
    parser.add_argument(
        "--api-key", help="OpenAI API Key. Overrides OPENAI_API_KEY from .env."
    )
    parser.add_argument(
        "--assistant-id", help="OpenAI Assistant ID. Overrides ASSISTANT_ID from .env."
    )
    parser.add_argument(
        "--folder",
        default="data",
        help="Directory where markdown files are located. Defaults to 'data'.",
    )
    args = parser.parse_args()

    # Load environment variables from .env file
    load_dotenv()

    # Combine command line args and environment variables with precedence
    config = {
        "api_key": args.api_key or os.getenv("OPENAI_API_KEY"),
        "assistant_id": args.assistant_id or os.getenv("ASSISTANT_ID"),
        "vector_store_id": os.getenv("VECTOR_STORE_ID"),
        "markdown_files_directory": args.folder,
        "vector_store_name": "OptiSigns Customer Support Docs",
    }
    return config


# Load configuration and extract key variables
config = setup_configuration()
OPENAI_API_KEY = config["api_key"]
ASSISTANT_ID = config["assistant_id"]
VECTOR_STORE_ID = config["vector_store_id"]
MARKDOWN_FILES_DIRECTORY = config["markdown_files_directory"]
VECTOR_STORE_NAME = config["vector_store_name"]

# Validate required configuration and initialize OpenAI client
try:
    if not OPENAI_API_KEY:
        raise ValueError(
            "OpenAI API Key not found. Provide it via --api-key or OPENAI_API_KEY in .env."
        )
    if not ASSISTANT_ID:
        raise ValueError(
            "Assistant ID not found. Provide it via --assistant-id or ASSISTANT_ID in .env."
        )

    client = OpenAI(api_key=OPENAI_API_KEY)
    print("OpenAI client initialized successfully.")
except Exception as e:
    print(f"Error initializing: {e}")
    exit()


# --- 1. Read, Chunk, and Upload Files ---
# Initialize tracking variables for the chunking and upload process
uploaded_file_ids = []
# Initialize counters for tracking file processing
file_upload_success_count = 0
file_upload_failed_count = 0
total_chunks_created = 0

print(
    f"\n--- Starting file chunking and uploading from '{MARKDOWN_FILES_DIRECTORY}' ---"
)

# Validate that the source directory exists
if not os.path.isdir(MARKDOWN_FILES_DIRECTORY):
    print(
        f"Error: Directory '{MARKDOWN_FILES_DIRECTORY}' does not exist. Please create it and place your Markdown files inside."
    )
    exit()

# Configure the Markdown splitter to chunk documents by headers
headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]
markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

# Process each markdown file in the directory
for filename in os.listdir(MARKDOWN_FILES_DIRECTORY):
    if filename.endswith(".md"):
        filepath = os.path.join(MARKDOWN_FILES_DIRECTORY, filename)
        try:
            # Read the markdown file content
            with open(filepath, "r", encoding="utf-8") as f:
                markdown_text = f.read()

            # Split the document into chunks based on headers
            chunks = markdown_splitter.split_text(markdown_text)
            total_chunks_created += len(chunks)
            print(f"\nProcessing '{filename}': Split into {len(chunks)} chunks.")

            # Upload each chunk as a separate file to OpenAI
            for i, chunk in enumerate(chunks):
                # The chunk object has `page_content` and `metadata`.
                # We'll format the metadata back into the content for better context.
                chunk_content = ""
                # Add headers from metadata back to the content
                for header, value in chunk.metadata.items():
                    chunk_content += f"{value}\n"

                chunk_content += chunk.page_content

                # Create a unique filename for the chunk
                chunk_filename = f"{os.path.splitext(filename)[0]}_chunk_{i+1}.md"

                # Upload the chunk as an in-memory file
                with io.BytesIO(chunk_content.encode("utf-8")) as chunk_file:
                    print(f"  Uploading chunk '{chunk_filename}'...")
                    uploaded_file = client.files.create(
                        file=(chunk_filename, chunk_file), purpose="assistants"
                    )
                    uploaded_file_ids.append(uploaded_file.id)
                    file_upload_success_count += 1
                    print(
                        f"  Successfully uploaded chunk '{chunk_filename}' with File ID: {uploaded_file.id}"
                    )

        except Exception as e:
            file_upload_failed_count += 1
            print(f"Error processing and uploading chunks for '{filename}': {e}")


# Display summary of chunking and upload process
print(f"\n--- Chunking and Upload Summary ---")
print(
    f"Total markdown files processed: {len([f for f in os.listdir(MARKDOWN_FILES_DIRECTORY) if f.endswith('.md')])}"
)
print(f"Total chunks created: {total_chunks_created}")
print(f"Successfully uploaded file chunks: {file_upload_success_count}")
print(f"Failed uploads: {file_upload_failed_count}")


# --- 2. Create/Retrieve a Vector Store ---
# Handle vector store creation or retrieval for storing document chunks
print(f"\n--- Managing Vector Store ---")

# Try to use existing vector store ID from environment if available
if VECTOR_STORE_ID:
    print(f"Attempting to use existing Vector Store ID from .env: {VECTOR_STORE_ID}")
    try:
        # Verify the existing vector store actually exists
        existing_vector_store = client.vector_stores.retrieve(VECTOR_STORE_ID)
        print(
            f"Verified existing Vector Store: '{existing_vector_store.name}' with ID: {VECTOR_STORE_ID}"
        )
    except Exception as e:
        print(f"Error retrieving existing Vector Store ID '{VECTOR_STORE_ID}': {e}")
        print("Falling back to creating or finding a new one by name.")
        VECTOR_STORE_ID = None  # Reset to create/find new
else:
    print("No VECTOR_STORE_ID found in .env. Attempting to create or find one by name.")

# Create new vector store or find existing one by name if no ID provided
if not VECTOR_STORE_ID:
    try:
        # First, try to find an existing one by name to avoid duplicates
        list_vector_stores = client.vector_stores.list(
            limit=100
        )  # Adjust limit as needed
        found_existing = False
        for vs in list_vector_stores.data:
            if vs.name == VECTOR_STORE_NAME:
                VECTOR_STORE_ID = vs.id
                print(
                    f"Found existing Vector Store by name: '{VECTOR_STORE_NAME}' with ID: {VECTOR_STORE_ID}"
                )
                found_existing = True
                break
        if not found_existing:
            # If not found, create a new one
            new_vector_store = client.vector_stores.create(name=VECTOR_STORE_NAME)
            VECTOR_STORE_ID = new_vector_store.id
            print(
                f"Created new Vector Store: '{VECTOR_STORE_NAME}' with ID: {VECTOR_STORE_ID}"
            )

            # Store the new VECTOR_STORE_ID in the .env file for future use
            with open(".env", "a") as f:  # Use 'a' for append mode
                f.write(f'\nVECTOR_STORE_ID="{VECTOR_STORE_ID}"\n')
            print(f"VECTOR_STORE_ID '{VECTOR_STORE_ID}' saved to .env file.")

    except Exception as e:
        print(f"Error creating or finding vector store: {e}")
        print("Cannot proceed without a Vector Store. Exiting.")
        exit()

# --- 3. Add Uploaded Files (Chunks) to the Vector Store ---
# Associate all uploaded file chunks with the vector store
vector_store_file_objects = []
if uploaded_file_ids and VECTOR_STORE_ID:
    print(
        f"\n--- Adding {len(uploaded_file_ids)} file chunks to Vector Store '{VECTOR_STORE_ID}' ---"
    )
    for file_id in uploaded_file_ids:
        try:
            print(f"Adding file_id '{file_id}' to vector store...")
            vector_store_file = client.vector_stores.files.create(
                vector_store_id=VECTOR_STORE_ID, file_id=file_id
            )
            vector_store_file_objects.append(vector_store_file)
            print(
                f"Successfully initiated add for file_id '{file_id}'. Status: {vector_store_file.status}"
            )
        except Exception as e:
            print(f"Error adding file_id '{file_id}' to vector store: {e}")
else:
    print(
        "No new file chunks to add to the vector store or VECTOR_STORE_ID is missing. Skipping file addition."
    )


# --- 4. Poll Vector Store Status for File Processing ---
# Monitor the vector store until all files are processed
if uploaded_file_ids and VECTOR_STORE_ID:
    print(f"\n--- Polling Vector Store for file processing status ---")
    retries = 0
    max_retries = 60  # Poll for up to 5 minutes (60 * 5 seconds)
    poll_interval_seconds = 5

    # Keep checking until all files are processed or timeout
    while retries < max_retries:
        try:
            current_vector_store = client.vector_stores.retrieve(VECTOR_STORE_ID)
            file_counts = current_vector_store.file_counts

            print(
                f"  Poll {retries+1}/{max_retries}: Total={file_counts.total}, Completed={file_counts.completed}, Failed={file_counts.failed}, Pending={file_counts.pending}, In Progress={file_counts.in_progress}"
            )

            # Break when no files are pending or in progress
            if file_counts.pending == 0 and file_counts.in_progress == 0:
                print(
                    "\nAll file chunks seem to have finished processing in the vector store."
                )
                break

        except Exception as e:
            print(f"Error while polling vector store status: {e}")
            break  # Exit loop on error

        time.sleep(poll_interval_seconds)
        retries += 1

    # Display timeout warning if needed
    if retries == max_retries:
        print(
            "\nWarning: Polling timed out. Some file chunks might still be processing."
        )

    # Show final processing statistics
    print(f"\n--- Final Vector Store File Processing Summary ---")
    final_vector_store = client.vector_stores.retrieve(VECTOR_STORE_ID)
    final_file_counts = final_vector_store.file_counts
    print(f"  Total files in store: {final_file_counts.total}")
    print(f"  Files completed processing: {final_file_counts.completed}")
    print(f"  Files failed processing: {final_file_counts.failed}")
    print(f"  Files in progress: {final_file_counts.in_progress}")

    if final_file_counts.failed > 0:
        print(
            "\nNote: Some files failed processing. Please check the OpenAI UI for details."
        )


# --- 5. Update Your Assistant to Use the Vector Store ---
# Connect the vector store to the OpenAI assistant for Q&A functionality
print(
    f"\n--- Updating Assistant '{ASSISTANT_ID}' to use Vector Store '{VECTOR_STORE_ID}' ---"
)
try:
    assistant = client.beta.assistants.update(
        ASSISTANT_ID,
        tool_resources={"file_search": {"vector_store_ids": [VECTOR_STORE_ID]}},
    )
    print(f"Assistant '{assistant.name}' updated successfully.")
    print(
        f"Assistant now uses Vector Store ID(s): {assistant.tool_resources.file_search.vector_store_ids}"
    )
    print("\nVector store population and Assistant update complete!")
except Exception as e:
    print(f"Error updating Assistant: {e}")
    print("Please ensure the ASSISTANT_ID is correct and you have permissions.")
