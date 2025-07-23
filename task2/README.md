# OpenAI Assistant Vector Store Uploader

A Python tool that intelligently chunks markdown documentation and uploads it to OpenAI's Vector Store for use with AI assistants. Enables powerful Q&A capabilities over your knowledge base.

## 🎯 Purpose

This tool transforms static markdown documentation into an AI-searchable knowledge base by:
- **Chunking** large markdown files into manageable sections based on headers
- **Uploading** processed chunks to OpenAI's file storage system
- **Organizing** content in vector stores for semantic search
- **Connecting** your assistant to the knowledge base for intelligent responses
- **Managing** vector store lifecycle with automatic creation and updates

## 🚀 Key Features

- **📝 Smart Chunking**: Splits markdown files by header structure (H1, H2, H3)
- **🔄 Automatic Management**: Creates or finds existing vector stores by name
- **📊 Progress Tracking**: Real-time upload progress and processing status
- **🔗 Assistant Integration**: Automatically connects vector store to your assistant
- **⚙️ Flexible Configuration**: Command-line args and environment variable support
- **📈 Status Monitoring**: Polls vector store until all files are processed

## 🏗️ Architecture

```
main.py              # Main script with chunking and upload logic
├── Configuration    # Setup from CLI args and environment variables
├── File Processing  # Read, chunk, and upload markdown files
├── Vector Store     # Create/manage OpenAI vector stores
├── File Association # Link uploaded files to vector store
├── Status Polling   # Monitor processing completion
└── Assistant Update # Connect vector store to assistant
```

## 📁 Input/Output Structure

```
data/                       # Input directory (configurable)
├── article-1.md           # Source markdown files
├── article-2.md
└── documentation.md

# Processing creates chunked files uploaded to OpenAI:
# article-1_chunk_1.md, article-1_chunk_2.md, etc.
```

## 🛠️ Setup & Usage

### Prerequisites
- Python 3.8+
- OpenAI API Key
- OpenAI Assistant ID

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file:**
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ASSISTANT_ID=asst_your_assistant_id_here
   VECTOR_STORE_ID=vs_your_store_id_here  # Optional, will be created if not provided
   ```

3. **Prepare your data:**
   ```bash
   mkdir data
   # Place your markdown files in the data/ directory
   ```

### Running the Tool

#### Basic Usage
```bash
python main.py
```

#### With Custom Options
```bash
python main.py --folder my_docs --api-key sk-... --assistant-id asst-...
```

#### Command Line Arguments
- `--folder`: Directory containing markdown files (default: `data`)
- `--api-key`: OpenAI API key (overrides environment variable)
- `--assistant-id`: OpenAI Assistant ID (overrides environment variable)

## ⚙️ Configuration Options

| Environment Variable | CLI Argument | Required | Description |
|---------------------|--------------|----------|-------------|
| `OPENAI_API_KEY` | `--api-key` | ✅ | Your OpenAI API key |
| `ASSISTANT_ID` | `--assistant-id` | ✅ | ID of your OpenAI assistant |
| `VECTOR_STORE_ID` | - | ❌ | Existing vector store ID (auto-created if missing) |

## 🎯 How It Works

### 1. File Discovery & Reading
- Scans the specified directory for `.md` files
- Reads each markdown file with UTF-8 encoding
- Prepares files for processing

### 2. Intelligent Chunking
- Uses LangChain's `MarkdownHeaderTextSplitter`
- Splits content at header boundaries (H1, H2, H3)
- Preserves header context in each chunk
- Maintains document structure for better search

### 3. Upload Process
- Creates unique chunk filenames (`filename_chunk_1.md`)
- Uploads each chunk as an in-memory file to OpenAI
- Tracks upload success/failure rates
- Stores file IDs for vector store association

### 4. Vector Store Management
- Attempts to use existing vector store from environment
- Searches for existing store by name to avoid duplicates
- Creates new vector store if none found
- Saves vector store ID to `.env` for future runs

### 5. File Association
- Links all uploaded file chunks to the vector store
- Initiates processing for semantic indexing
- Monitors association status

### 6. Processing Monitoring
- Polls vector store status every 5 seconds
- Tracks pending, in-progress, completed, and failed files
- Waits up to 5 minutes for processing completion
- Reports final processing statistics

### 7. Assistant Integration
- Updates your assistant's tool resources
- Connects the vector store for file search capabilities
- Enables Q&A functionality over your documentation

## 📊 Sample Output

```
--- Starting file chunking and uploading from 'data' ---
Processing 'documentation.md': Split into 8 chunks.
  Uploading chunk 'documentation_chunk_1.md'...
  Successfully uploaded chunk 'documentation_chunk_1.md' with File ID: file-abc123

--- Chunking and Upload Summary ---
Total markdown files processed: 5
Total chunks created: 32
Successfully uploaded file chunks: 32
Failed uploads: 0

--- Managing Vector Store ---
Created new Vector Store: 'OptiSigns Customer Support Docs' with ID: vs-xyz789

--- Adding 32 file chunks to Vector Store 'vs-xyz789' ---
Successfully initiated add for file_id 'file-abc123'. Status: in_progress

--- Polling Vector Store for file processing status ---
Poll 1/60: Total=32, Completed=28, Failed=0, Pending=4, In Progress=0
All file chunks seem to have finished processing in the vector store.

--- Updating Assistant 'asst-def456' to use Vector Store 'vs-xyz789' ---
Assistant 'Customer Support Bot' updated successfully.
Vector store population and Assistant update complete!
```

## 🔧 Troubleshooting

### Common Issues

1. **API Key Error**
   ```
   Error: OpenAI API Key not found
   ```
   - Set `OPENAI_API_KEY` in `.env` or use `--api-key`

2. **Assistant Not Found**
   ```
   Error: Assistant ID not found
   ```
   - Verify your assistant ID in OpenAI playground
   - Set `ASSISTANT_ID` in `.env` or use `--assistant-id`

3. **No Files Found**
   ```
   Error: Directory 'data' does not exist
   ```
   - Create the data directory: `mkdir data`
   - Add markdown files to the directory

4. **Upload Failures**
   - Check file encoding (should be UTF-8)
   - Verify file sizes (OpenAI has limits)
   - Check your API quota and rate limits

5. **Processing Timeout**
   ```
   Warning: Polling timed out. Some file chunks might still be processing.
   ```
   - This is usually fine; processing may continue in background
   - Check OpenAI console for final status

### Debug Tips

1. **Check file content**: Ensure markdown files have proper header structure
2. **Verify chunking**: Look for meaningful chunk divisions at headers
3. **Monitor OpenAI console**: Check file processing status in OpenAI dashboard
4. **Test assistant**: Try asking questions to verify the knowledge base works

## 📈 Performance Notes

- **Chunking Speed**: ~1-2 seconds per file depending on size
- **Upload Speed**: ~1-2 seconds per chunk depending on size and network
- **Processing Time**: 1-10 minutes depending on total content volume
- **Rate Limits**: Respects OpenAI API rate limits automatically

## 🔗 Integration

After successful completion, your assistant will be able to:
- Search through all uploaded documentation
- Answer questions based on the content
- Provide citations and references to source material
- Handle complex queries across multiple documents

Test your assistant by asking questions about the uploaded documentation!

## 💡 Best Practices

1. **Organize content**: Use clear header hierarchy (H1 > H2 > H3)
2. **Meaningful headers**: Write descriptive section titles
3. **Reasonable file sizes**: Split very large files before upload
4. **Regular updates**: Re-run when documentation changes
5. **Monitor usage**: Track assistant performance and user feedback
