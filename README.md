# 🚀 ASK LLAMA - AI-Powered Multi-Agent Chatbot

A comprehensive Streamlit-based AI chatbot application that supports multiple specialized agents for different use cases, featuring voice input/output capabilities and advanced AI interactions.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.22+-red.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.0.173+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🌟 Features

### 🤖 **Multi-Agent System**
- **💬 General Chat**: Engage in general conversation and Q&A
- **📄 Document Agent**: Upload and query PDF documents with intelligent analysis
- **📂 GitHub Repo Agent**: Analyze and understand GitHub repositories
- **⚡ GitHub Code Modifier Agent**: Create, edit, and manage files in GitHub repositories
- **🌐 Web Scraping Agent**: Search the web and extract information
- **🧮 Calculator Agent**: Perform mathematical calculations and analysis

### 🎤 **Voice Interface**
- **🎙️ Voice Input**: Speak your questions instead of typing
- **🔊 Voice Output**: Listen to AI responses aloud
- **🎯 Smart Processing**: Automatic text cleaning for better speech quality
- **⏹️ Voice Control**: Stop speaking at any time

### 🔧 **Advanced Capabilities**
- **🔄 Context Awareness**: All agents maintain conversation history
- **📊 Intelligent Analysis**: Deep understanding of documents and code
- **🔍 Smart Search**: Find files and content across repositories
- **📝 Code Generation**: Generate code based on natural language descriptions
- **🌿 Branch Management**: Create and manage Git branches
- **📋 File Operations**: Create, edit, delete, and search files

## 🚀 Quick Start

### 1. **Clone the Repository**
```bash
git clone <repository-url>
cd "AI chatbot"
```

### 2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Set Up Environment Variables**
Create a `.env` file in the project root:
```bash
# Required: Set one of the following
GITHUB_TOKEN=your_github_personal_access_token_here
GITHUB_API_KEY=your_github_api_key_here
```

**Note**: 
- **GITHUB_TOKEN** (Recommended): Provides access to GitHub AI models
- **GITHUB_API_KEY**: Provides Github repo access
- The app automatically uses GitHub AI if `GITHUB_TOKEN` is available

### 4. **Run the Application**
```bash
streamlit run app.py
```

### 5. **Access the Application**
Open your browser and navigate to: `http://localhost:8501`

## 📖 Detailed Usage Guide

### 🎯 **Getting Started**
1. **Launch the app** and you'll see the welcome screen
2. **Start chatting immediately** or select a specialized agent
3. **Use voice input/output** for hands-free interaction

### 🤖 **Agent-Specific Usage**

#### 💬 **General Chat (No Agent Selected)**
- **Purpose**: General conversation and Q&A
- **Capabilities**: 
  - Answer questions on various topics
  - Provide helpful information and advice
  - Maintain conversation context
- **Best for**: General questions, casual conversation, getting help

#### 📄 **Document Agent**
- **Purpose**: Analyze and answer questions about PDF documents
- **Setup**: Upload PDF files using the file uploader
- **Capabilities**:
  - Read and process PDF documents
  - Search through document content
  - Answer questions based on document content
  - Maintain context across multiple questions
- **Best for**: Research papers, reports, manuals, contracts

#### 📂 **GitHub Repo Agent**
- **Purpose**: Analyze and answer questions about GitHub repositories
- **Setup**: Provide a GitHub repository URL
- **Capabilities**:
  - Explore repository structure
  - Read and analyze code files
  - Explain code functionality
  - Understand code relationships
  - Provide insights about the codebase
- **Best for**: Code reviews, understanding unfamiliar codebases

#### ⚡ **GitHub Code Modifier Agent**
- **Purpose**: Create, edit, and manage files in GitHub repositories
- **Setup**: Provide a GitHub repository URL and initialize the agent
- **Capabilities**:
  - Create new files and directories
  - Edit existing files
  - Delete files
  - Search and find files
  - List repository contents
  - Manage branches
  - Generate code based on requirements
- **Best for**: Code generation, file management, repository maintenance
- **⚠️ Note**: This agent can make direct changes to your repository

#### 🌐 **Web Scraping Agent**
- **Purpose**: Search the web and extract information
- **Capabilities**:
  - Search the web using DuckDuckGo
  - Extract content from websites
  - Find news articles
  - Scrape specific websites
  - Provide insights from web data
- **Best for**: Research, news gathering, web content analysis

#### 🧮 **Calculator Agent**
- **Purpose**: Perform mathematical calculations and analysis
- **Capabilities**:
  - Perform mathematical calculations
  - Solve equations
  - Provide numerical analysis
  - Use Python REPL for complex calculations
- **Best for**: Mathematical problems, data analysis, calculations

### 🎤 **Voice Features**

#### **Voice Input**
1. Go to the **Voice** tab in the sidebar
2. Click **"🎙️ Speak Your Question"**
3. Wait for "Listening... Speak now!" message
4. Speak your question clearly
5. The text will appear in the chat and be processed

#### **Voice Output**
1. Enable voice output in the **Voice** settings
2. All AI responses will be spoken aloud
3. Use the **"🔇 Stop Speaking"** button to interrupt
4. Test voice functionality with **"🎤 Test Voice"** button

#### **Voice Tips**
- Speak clearly and at normal pace
- Ensure microphone is working and not muted
- Minimize background noise
- Wait for the listening prompt before speaking
- Speak a bit louder than normal conversation

## 🏗️ Project Structure

```
AI chatbot/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── README.md                # Project documentation
├── utils/
│   ├── doc.py               # Document processing utilities
│   ├── git_repo.py          # GitHub repository analysis
│   ├── github_modifier.py   # GitHub Code Modifier Agent
│   ├── github_agent.py      # GitHub Code Modifier Agent setup
│   ├── github_validator.py  # GitHub validation utilities
│   ├── voice.py             # Voice input/output utilities
│  
├── chroma_doc_store/        # Document vector store
└── chroma_git_store/        # GitHub repository vector store
```

## 📦 Dependencies

### **Core Framework**
- **Streamlit**: Web application framework
- **LangChain**: AI/LLM framework
- **OpenAI**: AI model API integration

### **Document Processing**
- **PyPDF2**: PDF processing
- **ChromaDB**: Vector database for embeddings
- **Sentence Transformers**: Text embeddings

### **GitHub Integration**
- **PyGithub**: GitHub API integration
- **GitPython**: Git repository handling

### **Web Scraping**
- **Requests**: HTTP library
- **BeautifulSoup**: HTML parsing
- **DuckDuckGo Search**: Web search functionality

### **Voice Processing**
- **SpeechRecognition**: Speech-to-text conversion
- **Subprocess**: System command execution (for TTS)

### **Data Processing**
- **NumPy**: Numerical computing
- **Pandas**: Data manipulation
- **Tiktoken**: Token counting

## 🔧 Configuration

### **Environment Variables**
```bash
# Required: Set one of the following
GITHUB_TOKEN=your_github_personal_access_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

### **GitHub Token Setup**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with the following permissions:
   - `repo` (Full control of private repositories)
   - `read:org` (Read organization data)
   - `read:user` (Read user data)
3. Copy the token to your `.env` file

### **Voice System Requirements**
- **macOS**: Built-in `say` command (default)
- **Linux**: Install TTS engines (espeak, festival, etc.)
- **Windows**: PowerShell TTS or install additional engines

## 🚨 Troubleshooting

### **Common Issues**

#### **"Failed to initialize AI client"**
- Check your API keys in the `.env` file
- Ensure the keys are valid and have proper permissions
- Try using a different API key

#### **"Voice input failed"**
- Check microphone permissions in system settings
- Ensure microphone is not muted
- Try speaking louder or closer to the microphone
- Use the "Test Voice Input" button to verify functionality

#### **"Repository not found"**
- Check the repository URL is correct
- Ensure your GitHub token has access to the repository
- Verify the repository is public or you have access permissions

#### **"Document processing failed"**
- Ensure the PDF file is not corrupted
- Check file size (large files may take longer)
- Try with a smaller PDF file first

### **Performance Tips**
- Use smaller PDF files for faster processing
- Limit the number of files uploaded at once
- Close unnecessary browser tabs
- Ensure stable internet connection

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Streamlit** for the amazing web framework
- **LangChain** for the AI/LLM integration
- **GitHub** for providing AI models and API access
- **OpenAI** for alternative AI model access
- **ChromaDB** for vector storage capabilities

## 📞 Support

If you encounter any issues or have questions:
1. Check the troubleshooting section above
2. Review the project documentation
3. Open an issue on GitHub
4. Check the project wiki for additional resources
