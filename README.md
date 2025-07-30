# AI Chatbot with Multiple Agents

A Streamlit-based AI chatbot application that supports multiple types of agents for different use cases.

## Features

- **Document Agent**: Upload and query PDF documents
- **GitHub Repo Agent**: Analyze and query GitHub repositories
- **GitHub Code Modifier Agent**: Make direct edits to GitHub repositories (create, edit, delete files, commit changes)
- **Web Search Agent**: Search the web and perform calculations

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Create a `.env` file in the project root with:
   ```
   GITHUB_TOKEN=your_github_marketplace_model_token_here
   GITHUB_API_TOKEN=your_github_repository_token_here
   ```
   
   **Note**: 
   - `GITHUB_TOKEN`: Used for AI model access (GitHub Marketplace models)
   - `GITHUB_API_TOKEN`: Used for repository operations (GitHub API access)

3. **Run the Application**:
   ```bash
   streamlit run app.py
   ```

## Usage

1. **Select Agent Type**: Choose from the sidebar
   - **Document Agent**: Upload PDFs and ask questions about them
   - **GitHub Repo Agent**: Provide a GitHub repository URL and ask questions about the code
   - **Web Search Agent**: Ask questions that require web search or calculations

2. **Interact**: Use the chat interface to ask questions

### GitHub Code Modifier Agent Usage

The GitHub Code Modifier Agent can perform the following operations:

- **List files**: Explore repository structure
- **Read files**: View file contents
- **Edit files**: Modify existing files with natural language instructions
- **Create files**: Add new files to the repository
- **Delete files**: Remove files from the repository
- **Search files**: Find files by content or filename
- **View history**: Check commit history for specific files
- **Create branches**: Create new branches for development


## Project Structure

```
AI chatbot/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── utils/
│   ├── doc.py            # Document processing utilities
│   ├── git_repo.py       # GitHub repository analysis
│   ├── github_modifier.py # GitHub Code Modifier Agent
│   ├── github_agent.py   # GitHub Code Modifier Agent setup
│   └── voice.py          # Voice input/output utilities
├── chroma_doc_store/     # Document vector store
└── chroma_git_store/     # GitHub repository vector store
```

## Dependencies

- **Streamlit**: Web application framework
- **LangChain**: AI/LLM framework
- **ChromaDB**: Vector database for embeddings
- **HuggingFace**: Embeddings and models
- **PyPDF2**: PDF processing
- **GitPython**: Git repository handling
- **PyGithub**: GitHub API integration
- **OpenAI**: AI model API

## Notes

- The application uses GitHub Marketplace models exclusively for AI functionality
- `GITHUB_TOKEN` is required for AI model access (GitHub Marketplace)
- `GITHUB_API_TOKEN` is required for repository operations (GitHub API)
- Voice features are available on macOS using the built-in `say` command
- Vector stores are persisted locally for document and repository analysis 
