import streamlit as st
from streamlit_chat import message
from dotenv import load_dotenv
import os
from openai import OpenAI

from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_experimental.tools import PythonREPLTool
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from utils.doc import (
    get_pdf_text,
    get_text_chunks,
    build_vector_store,
    load_vector_store,
    get_context_from_docs,
    get_documents_hash
)
from utils.git_repo import GitCodeEmbedder
from utils.github_agent import get_github_modifier_agent
from utils.github_validator import validate_github_setup, list_accessible_repositories
from utils.voice import listen, speak, stop_speaking 
import speech_recognition as sr
import requests
from bs4 import BeautifulSoup
import re

recognizer = sr.Recognizer()
def init():
    load_dotenv()
    # Check for GitHub token (if using GitHub API)
    if os.getenv("GITHUB_TOKEN") is None or os.getenv("GITHUB_TOKEN") == "":
        st.warning("GITHUB_TOKEN is not set in environment. Some features may be limited.")
    
    st.set_page_config(
        page_title="ASK LLAMA - AI-Powered Multi-Agent Chatbot",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/your-repo/ask-llama',
            'Report a bug': 'https://github.com/your-repo/ask-llama/issues',
            'About': 'ASK LLAMA is an AI-powered multi-agent chatbot for document analysis, GitHub repository management, and code generation.'
        }
    )
    if "voice_input_enabled" not in st.session_state:
        st.session_state.voice_input_enabled = False
    if "voice_output_enabled" not in st.session_state:
        st.session_state.voice_output_enabled = True
    if "is_speaking" not in st.session_state:
        st.session_state.is_speaking = False
    if "tts_working" not in st.session_state:
        st.session_state.tts_working = True
    
    # Custom CSS for enhanced styling
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .agent-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
    
    .feature-list {
        background: #e9ecef;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .stButton > button {
        border-radius: 20px;
        font-weight: bold;
    }
    
    .stSelectbox > div > div > div {
        border-radius: 10px;
    }
    
    .stTextInput > div > div > input {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

def create_custom_client():
    # Try GitHub AI first
    github_token = os.getenv("GITHUB_TOKEN", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    
    if github_token:
        endpoint = "https://models.github.ai/inference"
        model_name = "openai/gpt-4.1-mini"
        
        try:
            client = OpenAI(base_url=endpoint, api_key=github_token)
            return client, model_name
        except Exception as e:
            st.warning(f"GitHub AI client failed: {str(e)}. Trying OpenAI...")
    
    # Fallback to OpenAI
    if openai_key:
        model_name = "gpt-4.1-mini"
        try:
            client = OpenAI(api_key=openai_key)
            return client, model_name
        except Exception as e:
            st.error(f"Error creating OpenAI client: {str(e)}")
            return None, None
    
    # No API keys found
    st.error("No API key found. Please set either GITHUB_TOKEN or OPENAI_API_KEY in your environment variables.")
    return None, None

def create_web_scraping_tools():
    """Create tools for web scraping functionality using DuckDuckGo"""
    from langchain.tools import Tool
    from duckduckgo_search import DDGS
    
    def search_duckduckgo(query: str, max_results: int = 5) -> str:
        """Search the web using DuckDuckGo"""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                
                if not results:
                    return f"No results found for '{query}'"
                
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(f"{i}. {result['title']}\n   URL: {result['link']}\n   Snippet: {result['body']}\n")
                
                return f"Search results for '{query}':\n\n" + '\n'.join(formatted_results)
                
        except Exception as e:
            return f"Error searching for '{query}': {str(e)}"
    
    def scrape_website(url: str) -> str:
        """Scrape content from a website"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
            
            # Special handling for Hacker News
            if "news.ycombinator.com" in url:
                return scrape_hacker_news(soup, url)
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            return f"Content from {url}:\n\n{text[:3000]}..." if len(text) > 3000 else f"Content from {url}:\n\n{text}"
            
        except Exception as e:
            return f"Error scraping {url}: {str(e)}"
    
    def scrape_hacker_news(soup, url: str) -> str:
        """Specialized scraper for Hacker News"""
        try:
            # Find all story rows
            stories = []
            story_rows = soup.find_all('tr', class_='athing')
            
            for i, row in enumerate(story_rows[:20]):  # Limit to top 20 stories
                try:
                    # Get title and link
                    title_cell = row.find('td', class_='title')
                    if title_cell:
                        title_link = title_cell.find('a')
                        if title_link:
                            title = title_link.get_text().strip()
                            link = title_link.get('href', '')
                            if not link.startswith('http'):
                                link = f"https://news.ycombinator.com{link}"
                            
                            # Get points and author from next row
                            next_row = row.find_next_sibling('tr')
                            points = "0"
                            author = "Unknown"
                            comments = "0"
                            
                            if next_row:
                                subtext = next_row.find('td', class_='subtext')
                                if subtext:
                                    # Extract points
                                    points_elem = subtext.find('span', class_='score')
                                    if points_elem:
                                        points = points_elem.get_text().replace(' points', '').replace(' point', '')
                                    
                                    # Extract author
                                    author_elem = subtext.find('a', class_='hnuser')
                                    if author_elem:
                                        author = author_elem.get_text()
                                    
                                    # Extract comments
                                    comments_elem = subtext.find_all('a')[-1]
                                    if comments_elem and 'comment' in comments_elem.get_text().lower():
                                        comments_text = comments_elem.get_text()
                                        comments = re.search(r'\d+', comments_text)
                                        if comments:
                                            comments = comments.group()
                            
                            stories.append({
                                'rank': i + 1,
                                'title': title,
                                'link': link,
                                'points': points,
                                'author': author,
                                'comments': comments
                            })
                except Exception as e:
                    continue
            
            if stories:
                result = f"Top Stories from Hacker News ({url}):\n\n"
                for story in stories:
                    result += f"{story['rank']}. {story['title']}\n"
                    result += f"   Points: {story['points']} | Author: {story['author']} | Comments: {story['comments']}\n"
                    result += f"   Link: {story['link']}\n\n"
                return result
            else:
                return f"Could not extract stories from {url}. The page structure may have changed."
                
        except Exception as e:
            return f"Error parsing Hacker News content: {str(e)}"
    
    def search_and_scrape(query: str, max_results: int = 3) -> str:
        """Search for content and scrape the top results"""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                
                if not results:
                    return f"No results found for '{query}'"
                
                scraped_content = []
                for i, result in enumerate(results, 1):
                    try:
                        # Scrape the content from the result URL
                        content = scrape_website(result['link'])
                        scraped_content.append(f"Result {i}: {result['title']}\n{content}\n")
                    except Exception as e:
                        scraped_content.append(f"Result {i}: {result['title']}\nError scraping: {str(e)}\n")
                
                return f"Search and scrape results for '{query}':\n\n" + '\n'.join(scraped_content)
                
        except Exception as e:
            return f"Error searching and scraping for '{query}': {str(e)}"
    
    def search_news(query: str, max_results: int = 5) -> str:
        """Search for news articles using DuckDuckGo"""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(query, max_results=max_results))
                
                if not results:
                    return f"No news found for '{query}'"
                
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(f"{i}. {result['title']}\n   Source: {result.get('source', 'Unknown')}\n   Date: {result.get('date', 'Unknown')}\n   URL: {result['link']}\n   Summary: {result['body']}\n")
                
                return f"News results for '{query}':\n\n" + '\n'.join(formatted_results)
                
        except Exception as e:
            return f"Error searching news for '{query}': {str(e)}"
    
    tools = [
        Tool(
            name="search_duckduckgo",
            description="Search the web using DuckDuckGo. Input: search query (e.g., 'latest AI news', 'Python tutorials', 'weather in New York').",
            func=search_duckduckgo
        ),
        Tool(
            name="scrape_website",
            description="Scrape content from a specific website. Input: URL of the website to scrape (e.g., 'https://example.com', 'https://news.ycombinator.com'). Special handling for Hacker News.",
            func=scrape_website
        ),
        Tool(
            name="search_and_scrape",
            description="Search for content and scrape the top results. Input: search query (e.g., 'machine learning tutorials', 'latest tech news').",
            func=search_and_scrape
        ),
        Tool(
            name="search_news",
            description="Search for news articles using DuckDuckGo. Input: news topic (e.g., 'artificial intelligence', 'climate change', 'technology').",
            func=search_news
        )
    ]
    
    return tools

def create_calculator_tools():
    """Create tools for calculator functionality"""
    from langchain.tools import Tool
    
    # Python REPL tool for complex calculations
    python_repl = PythonREPLTool()
    
    def simple_calculator(expression: str) -> str:
        """Perform simple mathematical calculations"""
        try:
            # Remove any potentially dangerous characters
            expression = re.sub(r'[^0-9+\-*/().\s]', '', expression)
            result = eval(expression)
            return f"Result: {result}"
        except Exception as e:
            return f"Error calculating {expression}: {str(e)}"
    
    tools = [
        Tool(
            name="simple_calculator",
            description="Perform simple mathematical calculations. Input: mathematical expression (e.g., '2 + 2', '10 * 5', '100 / 4').",
            func=simple_calculator
        ),
        Tool(
            name="python_repl",
            description="Execute Python code for complex calculations, data analysis, or mathematical operations. Input: Python code.",
            func=python_repl.run
        )
    ]
    
    return tools


def get_chat_response(client, model_name, messages):
    # Validate messages
    if not messages:
        return "Sorry, I encountered an error: No messages provided."
    
    formatted = []
    for msg in messages:
        role = (
            "system" if isinstance(msg, SystemMessage)
            else "user" if isinstance(msg, HumanMessage)
            else "assistant"
        )
        # Ensure content is not empty
        content = msg.content if msg.content else ""
        if not content.strip() and role == "user":
            return "Sorry, I encountered an error: No content in user message."
        
        formatted.append({"role": role, "content": content})

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=formatted,
            temperature=0.3  # Lower temperature for more focused responses
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"


def clear_chat_history():
    st.session_state.messages = [
        SystemMessage(content="You are a helpful assistant. Please wait for the user to select an agent type.")
    ]
    st.session_state.vector_store = None
    st.session_state.git_embedder = None
    # Clean up GitHub Code Modifier Agent
    if "github_modifier" in st.session_state:
        st.session_state.github_modifier.cleanup()
    st.session_state.github_modifier_agent = None
    st.session_state.github_modifier = None
    st.session_state.current_repo_url = None
    # Clear GitHub agent context
    if 'github_agent_context' in st.session_state:
        del st.session_state.github_agent_context
    if 'pending_action' in st.session_state:
        del st.session_state.pending_action


def handle_voice_input():
    recognizer = sr.Recognizer()
    try:
        user_input = listen(recognizer)
        if user_input and not user_input.startswith("Sorry") and not user_input.startswith("Mic error"):
            return user_input
    except Exception as e:
        st.error(f"Voice input error: {e}")
    return None

def main():
    init()
    client, model_name = create_custom_client()
    
    if client is None:
        st.error("Failed to initialize AI client. Please check your GITHUB_TOKEN configuration.")
        return

    # Initialize session state
    if "messages" not in st.session_state:
        clear_chat_history()
    if "agent_type" not in st.session_state:
        st.session_state.agent_type = None
    if "agent" not in st.session_state:
        st.session_state.agent = None
   

    # --- Sidebar ---
    with st.sidebar:
        # Enhanced header with better styling
        st.markdown("""
        <div style="padding: 1rem 0;">
            <h1 style="color: #1f77b4; margin-bottom: -0.5rem; font-size: 2.5rem; font-weight: bold;">ASK LLAMA</h1>
            <p style="color: #666; font-size: 0.9rem; margin: 0;">AI-Powered Multi-Agent Chatbot</p>
        </div>
        """, unsafe_allow_html=True)

        # New Chat button with better styling
        if st.button("🔄 New Chat", help="Start a fresh conversation", use_container_width=True):
            clear_chat_history()
            st.rerun()
        
        # Enhanced tabs with About section
        sidebar_tab1, sidebar_tab2, sidebar_tab3 = st.sidebar.tabs(["⚙️ Agents", "🔊 Voice", "ℹ️ About"])
        with sidebar_tab1:
            st.markdown("### ⚙️ Select Agent")
            
            # Enhanced agent selection with descriptions
            agent_options = {
                "Select Agent": "Choose an agent to get started",
                "Document Agent": "📄 Ask questions about uploaded PDF documents",
                "GitHub Repo Agent": "📂 Analyze and answer questions about GitHub repositories",
                "GitHub Code Modifier Agent": "⚡ Create, edit, and manage files in GitHub repositories",
                "Web Scraping Agent": "🌐 Scrape and analyze web content",
                "Calculator Agent": "🧮 Perform calculations and mathematical operations"
            }
            
            new_agent_type = st.selectbox(
                "Choose Assistant Type",
                options=list(agent_options.keys()),
                format_func=lambda x: agent_options[x],
                index=0 if st.session_state.agent_type is None else 
                    1 if st.session_state.agent_type == "Document Agent" else 
                    2 if st.session_state.agent_type == "GitHub Repo Agent" else 3
            )

            # Handle agent type change
            if new_agent_type != st.session_state.agent_type:
                st.session_state.agent_type = new_agent_type
                if new_agent_type == "Select Agent":
                    st.session_state.messages = [
                        SystemMessage(content="You are ASK LLAMA, a helpful AI assistant. You can engage in general conversation, answer questions, and provide assistance. When users select a specialized agent, you'll switch to that specific role. Always maintain context from previous conversations and be helpful and informative.")
                    ]
                    st.session_state.agent = None
                elif new_agent_type == "Document Agent":
                    st.session_state.messages = [
                        SystemMessage(content="You are a document assistant. Only answer questions based on the provided documents. If a question is unrelated to the documents, politely decline to answer.")
                    ]
                    st.session_state.agent = None
                elif new_agent_type == "GitHub Code Modifier Agent":
                    st.session_state.messages = [
                        SystemMessage(content="You are a GitHub Code Modifier Agent. You can list files, read contents, make edits, and commit changes to GitHub repositories. Be careful and precise with all operations.")
                    ]
                    st.session_state.agent = None
                elif new_agent_type == "Web Scraping Agent":
                    st.session_state.messages = [
                        SystemMessage(content="You are a web scraping assistant powered by DuckDuckGo. You can search the web, find news articles, scrape website content, and provide insights from web data. Always maintain context from previous conversations and refer to previously scraped content when answering follow-up questions. Use the appropriate tools for web search and scraping tasks.")
                    ]
                    st.session_state.agent = None
                elif new_agent_type == "Calculator Agent":
                    st.session_state.messages = [
                        SystemMessage(content="You are a calculator assistant. You can perform mathematical calculations, solve equations, and provide numerical analysis. Always maintain context from previous calculations and use previous results when answering follow-up questions. Use Python REPL for complex calculations.")
                    ]
                    st.session_state.agent = None
                else:
                    st.session_state.messages = [
                        SystemMessage(content="You are a GitHub repository assistant. Only answer questions about the provided codebase. Always maintain context from previous conversations and refer to previously discussed code when answering follow-up questions. If a question is unrelated to the repository, politely decline to answer.")
                    ]
                    st.session_state.agent = None
                st.rerun()

            # Agent-specific controls with enhanced UI
            if st.session_state.agent_type == "Document Agent":
                st.markdown("---")
                st.subheader("📄 Document Agent Controls")
                st.info("Upload PDF documents to ask questions about their content")
                
                uploaded_files = st.file_uploader(
                    "📎 Upload PDF(s)", 
                    type=["pdf"], 
                    accept_multiple_files=True,
                    help="Upload documents to ask questions about"
                )
                
                # Check if we have new documents to process
                if uploaded_files and (
                    "processed_files_hash" not in st.session_state or
                    st.session_state.processed_files_hash != get_documents_hash(uploaded_files)
                ):
                    with st.spinner("Reading and indexing PDFs..."):
                        try:
                            # Store hash of processed files
                            st.session_state.processed_files_hash = get_documents_hash(uploaded_files)
                            
                            raw_text = get_pdf_text(uploaded_files)
                            chunks = get_text_chunks(raw_text)
                            st.session_state.vector_store = build_vector_store(chunks)
                            st.success("PDFs processed successfully!")
                        except Exception as e:
                            st.error(f"Error processing documents: {str(e)}")
                

            elif st.session_state.agent_type == "GitHub Repo Agent":
                st.markdown("---")
                st.subheader("📂 GitHub Repo Agent Controls")
                st.info("Provide a GitHub repository URL to analyze and ask questions about the codebase")
                
                repo_url = st.text_input(
                    "🔗 GitHub Repository URL", 
                    key="repo_url",
                    placeholder="https://github.com/username/repo.git",
                    help="Enter a GitHub repository URL to analyze"
                )
                if repo_url and st.button("🚀 Process Repository", use_container_width=True):
                    with st.spinner("Cloning and embedding repo..."):
                        try:
                            embedder = GitCodeEmbedder(repo_url)
                            embedder.load_or_create_db()
                            st.session_state.git_embedder = embedder
                            st.success("GitHub repo processed successfully!")
                        except Exception as e:
                            st.error(f"Error processing repository: {str(e)}")

            elif st.session_state.agent_type == "GitHub Code Modifier Agent":
                st.markdown("---")
                st.subheader("⚡ GitHub Code Modifier Agent Controls")
                st.warning("⚠️ **Warning**: This agent can make direct changes to your GitHub repository. Use with caution!")
                
                repo_url = st.text_input(
                    "🔗 GitHub Repository URL", 
                    placeholder="https://github.com/username/repo",
                    help="Enter the GitHub repository URL you want to modify"
                )
                
                if repo_url and st.button("⚡ Initialize Code Modifier Agent", use_container_width=True):
                    with st.spinner("Setting up GitHub Code Modifier Agent..."):
                        try:
                            # First validate repository access
                            validation = validate_github_setup(repo_url=repo_url)
                            if not validation.get("repo_accessible", False):
                                st.error(f"❌ Repository access failed: {validation.get('error', 'Unknown error')}")
                                if validation.get("suggestions"):
                                    st.info("💡 Suggestions:")
                                    for suggestion in validation["suggestions"]:
                                        st.write(f"• {suggestion}")
                                return
                            
                            # Show repository info
                            if validation.get("permissions"):
                                perms = validation["permissions"]
                                st.info(f"✅ Repository accessible: {validation['repo_name']} (Read: {perms['pull']}, Write: {perms['push']})")
                            
                            # Initialize the agent
                            try:
                                agent, modifier = get_github_modifier_agent(repo_url)
                                st.session_state.github_modifier_agent = agent
                                st.session_state.github_modifier = modifier
                                st.session_state.current_repo_url = repo_url
                                st.success(f"GitHub Code Modifier Agent initialized for {repo_url}")
                            except ValueError as e:
                                st.error(f"Configuration error: {str(e)}")
                            except Exception as e:
                                st.error(f"Agent initialization failed: {str(e)}")
                                st.info("💡 This might be due to AI model access issues. Check your GITHUB_TOKEN.")
                        except Exception as e:
                            st.error(f"Error initializing GitHub Code Modifier Agent: {str(e)}")
                
                if st.session_state.get("github_modifier_agent"):
                    if st.button("Reset Agent"):
                        if "github_modifier" in st.session_state:
                            st.session_state.github_modifier.cleanup()
                        st.session_state.github_modifier_agent = None
                        st.session_state.github_modifier = None
                        st.session_state.current_repo_url = None
                        st.rerun()

            
        # Load fallback vector store for Document Agent
        if st.session_state.agent_type == "Document Agent":
            if "vector_store" not in st.session_state and os.path.exists("chroma_doc_store"):
                try:
                    st.session_state.vector_store = load_vector_store()
                except Exception as e:
                    st.warning(f"Could not load vector store: {str(e)}")

        with sidebar_tab2:
            st.subheader("🔊 Voice Settings")
            
            # Voice Output Settings
            st.subheader("🔊 Voice Output")
            voice_toggle = st.toggle("Enable Voice Output", value=st.session_state.voice_output_enabled, 
                                   help="When enabled, the AI will speak its responses aloud")
            if voice_toggle != st.session_state.voice_output_enabled:
                st.session_state.voice_output_enabled = voice_toggle
                st.rerun()
            
            # Voice Output Status
            if st.session_state.voice_output_enabled:
                st.success("✅ Voice output is enabled")
                if st.session_state.tts_working:
                    st.info("🔊 AI responses will be spoken aloud")
                    st.success("🎯 Voice output works for all chat modes including general chat")
                else:
                    st.warning("⚠️ TTS system not working. Voice output disabled.")
            else:
                st.info("🔇 Voice output is disabled")
                st.warning("💡 Enable voice output to hear AI responses in all chat modes")
            
            # Voice Control Buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔇 Stop Speaking", use_container_width=True, 
                            help="Stop any currently playing voice output"):
                    stop_speaking()
            
            with col2:
                if st.button("🎤 Test Voice", use_container_width=True,
                            help="Test voice output with a sample message"):
                    test_message = "Voice output test successful. Hello, world!"
                    speak(test_message)
            
            # Voice Input Test
            st.markdown("---")
            st.subheader("🎙️ Voice Input Test")
            
            # Microphone status check
            try:
                import speech_recognition as sr
                mic = sr.Microphone()
                st.success("✅ Microphone detected and available")
            except Exception as e:
                st.error(f"❌ Microphone issue: {str(e)}")
                st.info("💡 Please check your microphone permissions and settings")
            if st.button("🎤 Test Voice Input", use_container_width=True,
                        help="Test voice input functionality"):
                if 'recognizer' not in st.session_state:
                    st.session_state.recognizer = sr.Recognizer()
                
                with st.spinner("🎙️ Testing voice input..."):
                    test_input = listen(st.session_state.recognizer)
                    if test_input and not any(error_phrase in test_input.lower() for error_phrase in [
                        "sorry", "mic error", "no speech detected", "speech recognition service error", "timeout"
                    ]):
                        st.success(f"✅ Voice input test successful! Captured: '{test_input}'")
                    else:
                        st.error(f"❌ Voice input test failed: {test_input}")
                        st.info("💡 Try speaking louder or checking your microphone settings")

            # Show speaking status
            if st.session_state.is_speaking:
                st.warning("🔊 Currently speaking...")
            
            st.markdown("---")
            
            # Voice Input Settings
            st.subheader("🎙️ Voice Input")
            st.info("Click the button below to speak your question instead of typing")
            
            if st.button("🎙️ Speak Your Question", use_container_width=True):
                # Initialize recognizer if not already done
                if 'recognizer' not in st.session_state:
                    st.session_state.recognizer = sr.Recognizer()
                
                with st.spinner("🎙️ Listening for your voice input..."):
                    user_input = listen(st.session_state.recognizer)
                    # Debug: Show what was captured
                    if user_input:
                        st.info(f"🎤 Captured: '{user_input}'")
                
                # Check if voice input was successful
                if user_input and user_input.strip() and not any(error_phrase in user_input.lower() for error_phrase in [
                    "sorry", "mic error", "no speech detected", "speech recognition service error"
                ]):
                    # Set flag to hide welcome message immediately
                    st.session_state.user_started_typing = True
                    
                    # adds user's prompt to session state
                    st.session_state.messages.append(HumanMessage(content=user_input))

                    with st.spinner('Generating response...'):
                        # Get response based on agent type
                        agent_type = st.session_state.agent_type
                        response = None
                        
                        if not agent_type or agent_type == "Select Agent":
                            # General chat
                            try:
                                chat_history = st.session_state.messages + [HumanMessage(content=user_input)]
                                response = get_chat_response(client, model_name, chat_history)
                            except Exception as e:
                                response = f"Sorry, I encountered an error: {str(e)}"
                        elif agent_type == "GitHub Code Modifier Agent":
                            if st.session_state.get("github_modifier_agent"):
                                try:
                                    response = st.session_state.github_modifier_agent.run(user_input)
                                except Exception as e:
                                    response = f"❌ Error using GitHub Code Modifier Agent: {str(e)}"
                            else:
                                response = "Please provide a GitHub repository URL first."
                        elif agent_type == "Web Scraping Agent":
                            if st.session_state.get("web_scraping_agent"):
                                try:
                                    response = st.session_state.web_scraping_agent.run(user_input)
                                except Exception as e:
                                    response = f"❌ Error using Web Scraping Agent: {str(e)}"
                            else:
                                response = "Web Scraping Agent not initialized. Please try again."
                        elif agent_type == "Calculator Agent":
                            if st.session_state.get("calculator_agent"):
                                try:
                                    response = st.session_state.calculator_agent.run(user_input)
                                except Exception as e:
                                    response = f"❌ Error using Calculator Agent: {str(e)}"
                            else:
                                response = "Calculator Agent not initialized. Please try again."
                        else:
                            # For Document Agent and GitHub Repo Agent, use general chat
                            try:
                                chat_history = st.session_state.messages + [HumanMessage(content=user_input)]
                                response = get_chat_response(client, model_name, chat_history)
                            except Exception as e:
                                response = f"Sorry, I encountered an error: {str(e)}"

                        # appends response to the message list
                        st.session_state.messages.append(AIMessage(content=response))
                    
                    st.session_state.needs_save = True  # Mark that we need to save
                    
                    # Speak the response if voice output is enabled
                    if st.session_state.voice_output_enabled and st.session_state.tts_working:
                        speak(response)
                    
                    st.rerun()
                else:
                    # Show the specific error message from voice input
                    st.error(f"Voice input failed: {user_input}")
                    st.info("💡 Tips for better voice input:")
                    st.markdown("""
                    - **Speak clearly and at a normal pace**
                    - **Ensure your microphone is working and not muted**
                    - **Try to minimize background noise**
                    - **Wait for the "Listening... Speak now!" message before speaking**
                    - **Speak a bit louder than normal conversation**
                    - **Position yourself closer to the microphone**
                    - **Try the "Test Voice Input" button first to verify microphone works**
                    """)
        
        # About Tab
        with sidebar_tab3:
            st.markdown("### ℹ️ About ASK LLAMA")
            st.markdown("""
            **ASK LLAMA** is an AI-powered multi-agent chatbot that provides specialized assistance for different tasks.
            """)
            
            st.markdown("---")
            
            # General Chat Info
            st.markdown("#### 💬 General Chat")
            st.markdown("""
            **Purpose**: Engage in general conversation and get help with various topics
            
            **Capabilities**:
            - 💬 General conversation and Q&A
            - 📚 Answer questions on various topics
            - 🎯 Provide helpful information and advice
            - 🔄 Maintain conversation context
            - 🚀 No setup required - start chatting immediately
            
            **Best for**: General questions, casual conversation, getting help with various topics
            """)
            
            st.markdown("---")
            
            # Document Agent Info
            st.markdown("#### 📄 Document Agent")
            st.markdown("""
            **Purpose**: Analyze and answer questions about PDF documents
            
            **Capabilities**:
            - 📖 Read and process PDF documents
            - 🔍 Search through document content
            - 💬 Answer questions based on document content
            - 🔗 Maintain context across multiple questions
            
            **Best for**: Research papers, reports, manuals, contracts, and any PDF-based content analysis
            """)
            
            st.markdown("---")
            
            # GitHub Repo Agent Info
            st.markdown("#### 📂 GitHub Repo Agent")
            st.markdown("""
            **Purpose**: Analyze and answer questions about GitHub repositories
            
            **Capabilities**:
            - 🔍 Explore repository structure
            - 📝 Read and analyze code files
            - 💡 Explain code functionality
            - 🔗 Understand code relationships
            - 📊 Provide insights about the codebase
            
            **Best for**: Code reviews, understanding unfamiliar codebases, documentation generation
            """)
            
            st.markdown("---")
            
            # GitHub Code Modifier Agent Info
            st.markdown("#### ⚡ GitHub Code Modifier Agent")
            st.markdown("""
            **Purpose**: Create, edit, and manage files in GitHub repositories
            
            **Capabilities**:
            - ➕ Create new files and directories
            - ✏️ Edit existing files
            - 🗑️ Delete files
            - 🔍 Search and find files
            - 📋 List repository contents
            - 🌿 Manage branches
            - 📝 Generate code based on requirements
            
            **Best for**: Code generation, file management, repository maintenance, automated coding tasks
            
            ⚠️ **Note**: This agent can make direct changes to your repository. Use with caution!
            """)
            
            st.markdown("---")
            
            # Web Scraping Agent Info
            st.markdown("#### 🌐 Web Scraping Agent")
            st.markdown("""
            **Purpose**: Search and scrape web content using DuckDuckGo
            
            **Capabilities**:
            - 🔍 **Web Search**: Search the internet using DuckDuckGo
            - 📰 **News Search**: Find latest news articles on any topic
            - 🌐 **Website Scraping**: Extract content from specific websites
            - 📊 **Search & Scrape**: Search for content and scrape top results
            - 📝 **Content Analysis**: Analyze and summarize web content
            
            **Best for**: Research, news monitoring, data collection, content analysis, web research
            """)
            
            st.markdown("---")
            
            # Calculator Agent Info
            st.markdown("#### 🧮 Calculator Agent")
            st.markdown("""
            **Purpose**: Perform mathematical calculations and data analysis
            
            **Capabilities**:
            - ➕ Simple arithmetic calculations
            - 🧮 Complex mathematical operations
            - 📊 Data analysis and statistics
            - 📈 Mathematical modeling
            - 🔢 Python code execution for advanced calculations
            
            **Best for**: Mathematical problems, data analysis, statistical calculations, scientific computations
            """)
            
            st.markdown("---")
            
            # Voice Features
            st.markdown("#### 🔊 Voice Features")
            st.markdown("""
            - 🎙️ **Voice Input**: Speak your questions instead of typing
            - 🔊 **Voice Output**: Listen to AI responses aloud
            - 🎯 **Smart Processing**: Automatic text cleaning for better speech
            - ⏹️ **Control**: Stop speaking at any time
            """)
            
            st.markdown("---")
            
            # API Configuration
            st.markdown("#### 🔑 API Configuration")
            st.markdown("""
            **Required**: Set one of the following environment variables:
            
            - **GITHUB_TOKEN**: For GitHub AI (recommended) - Set to your GitHub personal access token
            - **OPENAI_API_KEY**: For OpenAI - Set to your OpenAI API key
            
            The app will automatically use GitHub AI if GITHUB_TOKEN is available, otherwise fallback to OpenAI.
            """)
            
            st.markdown("---")
            
            # Tips
            st.markdown("#### 💡 Tips for Best Results")
            st.markdown("""
            1. **Start Chatting**: You can begin chatting immediately without selecting an agent
            2. **Be Specific**: Provide clear, detailed instructions
            3. **Use Context**: All agents maintain conversation context - ask follow-up questions naturally
            4. **Voice Quality**: Speak clearly for better voice recognition
            5. **Repository Access**: Ensure your GitHub token has appropriate permissions
            6. **File Formats**: Use PDF files for Document Agent
            7. **API Keys**: Set GITHUB_TOKEN or OPENAI_API_KEY in your environment
            8. **Conversation Flow**: Each agent remembers previous interactions and can build on them
            """)
            
            st.markdown("---")
        
    # Enhanced main area styling
    
    
    # Display agent status with enhanced styling
    if not st.session_state.agent_type:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;">
            <h3>🚀 Welcome to ASK LLAMA!</h3>
            <p>You can start chatting right away, or select a specialized agent from the sidebar for enhanced capabilities.</p>
            <p style="font-size: 0.9rem; opacity: 0.9;">Available agents: Document Agent, GitHub Repo Agent, GitHub Code Modifier Agent, Web Scraping Agent, or Calculator Agent</p>
            <p style="font-size: 0.9rem; opacity: 0.9; margin-top: 1rem;">🎤 <strong>Voice Input & Output:</strong> Use voice for both input and output in all chat modes!</p>
        </div>
        """, unsafe_allow_html=True)

    # --- Chat Input ---
    user_input = st.chat_input("💬 How can I assist you today?", disabled=client is None)

    if user_input:
        agent = st.session_state.agent_type
        context = None
        model_input = user_input
        response = None
        use_previous_context = False


        if len(st.session_state.messages) > 1 and isinstance(st.session_state.messages[-1], AIMessage):
            last_ai_response = st.session_state.messages[-1].content
            if "context" in st.session_state and st.session_state.context:
                use_previous_context = True
        
        # Handle simple chat when no agent is selected
        if not agent or agent == "Select Agent":
            # Simple chat loop with conversation history
            with st.spinner("Thinking..."):
                try:
                    chat_history = st.session_state.messages + [HumanMessage(content=user_input)]
                    response = get_chat_response(client, model_name, chat_history)
                except Exception as e:
                    response = f"Sorry, I encountered an error: {str(e)}"
        
        # Handle Document Agent queries
        elif agent == "Document Agent":
            if st.session_state.get("vector_store"):
                if use_previous_context:
                    # Use previous context for follow-up questions
                    context = st.session_state.context
                    model_input = f"""This is a follow-up question about the same document context. 
                    Use the previous context to answer. If unclear, say you need more specific information.
                    
                    Previous Context:
                    {context}
                    
                    Follow-up Question: {user_input}"""
                else:
                    # New question - get fresh context
                    context = get_context_from_docs(user_input, st.session_state.vector_store)
                    if context:
                        st.session_state.context = context  # Store for possible follow-ups
                        model_input = f"""You are a document assistant. Use this context to answer. 
                        For follow-up questions, maintain context about these documents.
                        
                        Context:
                        {context}
                        
                        Question: {user_input}"""
                    else:
                        response = "I can only answer questions about the uploaded documents. Please ask something related to the documents."
            else:
                response = "Please upload documents first before asking questions."
        # Handle GitHub Repo Agent queries
        elif agent == "GitHub Repo Agent":
            if st.session_state.get("git_embedder"):
                # Check if this is a follow-up question
                if len(st.session_state.messages) > 1 and isinstance(st.session_state.messages[-1], AIMessage):
                    last_ai_response = st.session_state.messages[-1].content
                    # Use previous context for follow-up questions
                    model_input = f"""This is a follow-up question about the same GitHub repository. 
                    Use the previous conversation context to answer. If unclear, say you need more specific information.
                    
                    Previous AI Response:
                    {last_ai_response}
                    
                    Follow-up Question: {user_input}
                    
                    Please maintain context from the previous conversation and respond appropriately."""
                else:
                    # New question - get fresh context
                    context = st.session_state.git_embedder.get_context(user_input)
                    if context:
                        model_input = f"""You are a GitHub repository assistant. Use this code context to answer the question. 
                        For follow-up questions, maintain context about this codebase.
                        
                        Code Context:
                        {context}
                        
                        Question: {user_input}"""
                    else:
                        response = "I can only answer questions about the provided GitHub repository. Please ask something related to the codebase."
            else:
                response = "Please provide a GitHub repository URL and process it first before asking questions."

        # Handle GitHub Code Modifier Agent queries
        elif agent == "GitHub Code Modifier Agent":
            if st.session_state.get("github_modifier_agent"):
                try:
                    # Initialize context if not exists
                    if 'github_agent_context' not in st.session_state:
                        st.session_state.github_agent_context = {
                            'conversation_history': [],
                            'last_action': None,
                            'pending_action': None
                        }
                    
                    # Add current input to context
                    st.session_state.github_agent_context['conversation_history'].append({
                        'user': user_input,
                        'timestamp': len(st.session_state.github_agent_context['conversation_history'])
                    })
                    
                    # Check if this is a follow-up to a previous action
                    if len(st.session_state.messages) > 1 and isinstance(st.session_state.messages[-1], AIMessage):
                        last_ai_response = st.session_state.messages[-1].content
                        
                        # If the last response mentioned an action that needs confirmation
                        if any(keyword in last_ai_response.lower() for keyword in ['will proceed', 'going to', 'about to', 'confirm', 'proceed']):
                            # This is likely a confirmation response
                            if user_input.lower() in ['yes', 'confirm', 'proceed', 'ok', 'sure', 'do it']:
                                # Execute the pending action
                                if 'pending_action' in st.session_state:
                                    action = st.session_state.pending_action
                                    with st.spinner(f"Executing {action['type']}..."):
                                        response = st.session_state.github_modifier_agent.run(action['command'])
                                    # Clear pending action
                                    del st.session_state.pending_action
                                    st.session_state.github_agent_context['last_action'] = action
                                else:
                                    response = "I don't have a pending action to execute. Please specify what you'd like me to do."
                            else:
                                response = "Action cancelled. Please specify what you'd like me to do."
                        else:
                            # Regular conversation - maintain context
                            context_prompt = f"""Previous conversation context:
                            Last AI response: {last_ai_response}
                            Conversation history: {st.session_state.github_agent_context['conversation_history'][-3:] if len(st.session_state.github_agent_context['conversation_history']) > 3 else st.session_state.github_agent_context['conversation_history']}
                            
                            Current user input: {user_input}
                            
                            Please maintain context from the previous conversation and respond appropriately. If the user is confirming an action, execute it. If they're asking a follow-up question, use the context from the previous response."""
                            
                            with st.spinner("Processing with GitHub Code Modifier Agent..."):
                                response = st.session_state.github_modifier_agent.run(context_prompt)
                    else:
                        # First message or new conversation
                        with st.spinner("Processing with GitHub Code Modifier Agent..."):
                            response = st.session_state.github_modifier_agent.run(user_input)
                            
                        # Check if the response indicates a pending action that needs confirmation
                        if any(keyword in response.lower() for keyword in ['will proceed', 'going to', 'about to', 'confirm', 'proceed']):
                            # Store the action for confirmation
                            st.session_state.pending_action = {
                                'type': 'file_operation',
                                'command': user_input,
                                'response': response
                            }
                            
                    # Update context with response
                    st.session_state.github_agent_context['conversation_history'].append({
                        'ai': response,
                        'timestamp': len(st.session_state.github_agent_context['conversation_history'])
                    })
                            
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"Agent execution error: {error_msg}")
                    
                    # Provide specific guidance based on error type
                    if "404" in error_msg and "Not Found" in error_msg:
                        st.info("💡 This appears to be a file not found error. Please check the file path and ensure the file exists in the repository.")
                    elif "'list' object has no attribute 'lower'" in error_msg:
                        st.info("💡 This is an internal parsing error. Please try rephrasing your request.")
                    elif "'dict' object has no attribute 'lower'" in error_msg:
                        st.info("💡 This is an internal parsing error. Please try rephrasing your request or restart the agent.")
                    elif "Authentication failed" in error_msg:
                        st.info("💡 Please check your GitHub token permissions and ensure it has access to the repository.")
                    else:
                        st.info("💡 This might be due to network issues, model access problems, or repository permissions.")
                    
                    response = f"❌ Error using GitHub Code Modifier Agent: {error_msg}"
            else:
                response = "Please initialize the GitHub Code Modifier Agent first by providing a repository URL and clicking 'Initialize Code Modifier Agent'."

        # Handle Web Scraping Agent queries
        elif agent == "Web Scraping Agent":
            if "web_scraping_agent" not in st.session_state:
                # Initialize web scraping agent
                tools = create_web_scraping_tools()
                # Use the same API key and base as the main client
                api_key = os.getenv("GITHUB_TOKEN") or os.getenv("OPENAI_API_KEY")
                api_base = "https://models.github.ai/inference" if os.getenv("GITHUB_TOKEN") else None
                
                llm = ChatOpenAI(
                    model=model_name, 
                    temperature=0,
                    openai_api_key=api_key,
                    openai_api_base=api_base
                )
                st.session_state.web_scraping_agent = initialize_agent(
                    tools, 
                    llm, 
                    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                    verbose=True,
                    handle_parsing_errors=True
                )
            
            # Check if this is a follow-up question
            if len(st.session_state.messages) > 1 and isinstance(st.session_state.messages[-1], AIMessage):
                last_ai_response = st.session_state.messages[-1].content
                # Add context to the user input for follow-up questions
                contextualized_input = f"""Previous response: {last_ai_response}

Follow-up question: {user_input}

Please maintain context from the previous web scraping results and respond appropriately. If the user is asking for more details about previously scraped content, refer to that context."""
            else:
                contextualized_input = user_input
            
            with st.spinner("Processing with Web Scraping Agent..."):
                try:
                    response = st.session_state.web_scraping_agent.run(contextualized_input)
                except Exception as e:
                    response = f"❌ Error using Web Scraping Agent: {str(e)}"

        # Handle Calculator Agent queries
        elif agent == "Calculator Agent":
            if "calculator_agent" not in st.session_state:
                # Initialize calculator agent
                tools = create_calculator_tools()
                # Use the same API key and base as the main client
                api_key = os.getenv("GITHUB_TOKEN") or os.getenv("OPENAI_API_KEY")
                api_base = "https://models.github.ai/inference" if os.getenv("GITHUB_TOKEN") else None
                
                llm = ChatOpenAI(
                    model=model_name, 
                    temperature=0,
                    openai_api_key=api_key,
                    openai_api_base=api_base
                )
                st.session_state.calculator_agent = initialize_agent(
                    tools, 
                    llm, 
                    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                    verbose=True,
                    handle_parsing_errors=True
                )
            
            # Check if this is a follow-up question
            if len(st.session_state.messages) > 1 and isinstance(st.session_state.messages[-1], AIMessage):
                last_ai_response = st.session_state.messages[-1].content
                # Add context to the user input for follow-up questions
                contextualized_input = f"""Previous calculation result: {last_ai_response}

Follow-up request: {user_input}

Please maintain context from the previous calculation and respond appropriately. If the user is asking for calculations based on previous results, use those values."""
            else:
                contextualized_input = user_input
            
            with st.spinner("Processing with Calculator Agent..."):
                try:
                    response = st.session_state.calculator_agent.run(contextualized_input)
                except Exception as e:
                    response = f"❌ Error using Calculator Agent: {str(e)}"

        # Get response from model if not already determined
        if response is None:
            with st.spinner("Thinking..."):
                try:
                    chat_history = st.session_state.messages + [HumanMessage(content=model_input)]
                    response = get_chat_response(client, model_name, chat_history)
                    
                    # Store the full context including the response for future reference
                    if context and agent == "Document Agent":
                        st.session_state.last_doc_context = {
                            "question": user_input,
                            "context": context,
                            "response": response
                        }
                except Exception as e:
                    response = f"Sorry, I encountered an error: {str(e)}"

        # Append messages to history
        st.session_state.messages.append(HumanMessage(content=user_input))
        
        # Convert response to string if it's a dictionary
        if isinstance(response, dict):
            # Format dictionary response as a readable string
            if 'commit' in response:
                response_str = f"✅ Success! Commit: {response['commit']}\n\n"
                if 'message' in response:
                    response_str += f"Commit message: {response['message']}\n\n"
                if 'content' in response and hasattr(response['content'], 'path'):
                    response_str += f"File: {response['content'].path}"
            else:
                response_str = str(response)
        else:
            response_str = str(response)
            
        st.session_state.messages.append(AIMessage(content=response_str))
        
        # Speak the response if voice output is enabled
        if st.session_state.voice_output_enabled and st.session_state.tts_working:
            speak(response_str)
        
        st.rerun()

    # --- Display chat history with enhanced styling ---
    if len(st.session_state.messages) > 1:  # Skip system prompt
        
        for i, msg in enumerate(st.session_state.messages[1:]):  # skip system prompt
            if isinstance(msg, HumanMessage):
                message(msg.content, is_user=True, key=f"user_{i}")
            elif isinstance(msg, AIMessage):
                message(msg.content, is_user=False, key=f"ai_{i}")


if __name__ == "__main__":
    main()


 