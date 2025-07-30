import os
from langchain.agents import initialize_agent, AgentType
from langchain_community.chat_models import ChatOpenAI
from utils.github_modifier import create_github_tools


def get_github_modifier_agent(repo_url: str, github_token: str = None):
    """
    Create a GitHub Code Modifier Agent
    
    Args:
        repo_url: GitHub repository URL
        github_token: GitHub personal access token (optional, will use env var if not provided)
        
    Returns:
        LangChain agent configured for GitHub operations
    """
    # Get GitHub token from environment if not provided
    if github_token is None:
        github_token = os.getenv("GITHUB_API_TOKEN")
    
    if not github_token:
        raise ValueError("GitHub token is required. Please set GITHUB_API_TOKEN environment variable or provide it as parameter.")
    
    # Create GitHub tools
    tools, modifier = create_github_tools(repo_url, github_token)
    
    # Create LLM using GitHub Marketplace model
    llm = ChatOpenAI(
        temperature=0.1, 
        openai_api_key=os.getenv("GITHUB_TOKEN"),
        base_url="https://models.github.ai/inference",
        model="openai/gpt-4.1-mini"
    )
    
    # Create agent
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=20
    )
    
    return agent, modifier


def get_github_modifier_agent_with_custom_system_prompt(repo_url: str, github_token: str = None, system_prompt: str = None):
    """
    Create a GitHub Code Modifier Agent with custom system prompt
    
    Args:
        repo_url: GitHub repository URL
        github_token: GitHub personal access token (optional)
        system_prompt: Custom system prompt for the agent
        
    Returns:
        LangChain agent configured for GitHub operations
    """
    # Default system prompt
    if system_prompt is None:
        system_prompt = """You are a GitHub Code Modifier Agent. Your capabilities include:

1. **File Operations**: List, read, create, edit, and delete files in GitHub repositories
2. **Code Analysis**: Search for specific code patterns and analyze file history
3. **Repository Management**: Create branches and manage repository structure
4. **Natural Language Processing**: Understand user requests in natural language and convert them to appropriate GitHub operations

**CRITICAL INSTRUCTIONS:**
- **ALWAYS USE TOOLS**: For any operation, you MUST use the appropriate tool. Do not just describe what you'll do.
- **EXECUTE ACTIONS IMMEDIATELY**: When a user asks you to do something, use the tool and execute it immediately.
- **NO CONFIRMATION REQUIRED**: Execute actions directly without asking for confirmation unless it's a destructive operation.
- **MAINTAIN CONTEXT**: Remember previous actions and conversations. Use context from previous messages.
- **BE DIRECT**: Use the appropriate tool for each operation type.

**MANDATORY TOOL USAGE RULES:**
- When user says "edit" or "update" a file → USE edit_file tool
- When user says "create" or "add" a file → USE create_file tool  
- When user says "delete" or "remove" a file → USE delete_file tool
- When user says "read" or "show" a file → USE read_file tool
- When user says "list" or "show files" → USE list_files tool
- When user says "find" or "search for" a file by name → USE find_file tool
- When user says "search" or "look for" content in files → USE search_files tool

**EDIT OPERATIONS - CRITICAL:**
- When a user asks to "edit" a file, you MUST use the edit_file tool immediately
- Do NOT use read_file when the user wants to edit
- Extract the new content from the user's request
- Use the edit_file tool with the file path and new content
- Example: "edit README.md with new content: Hello World" → Use edit_file with file_path="README.md" and new_content="Hello World"

**TOOL USAGE EXAMPLES:**
- To edit a file: Use the edit_file tool with file_path and new_content parameters
  - Example: When user says "edit README.md with new content: Updated content", use edit_file with file_path="README.md" and new_content="Updated content"
- To create a file: Use the create_file tool with file_path and content parameters
  - Example: When user says "create a file called bye.py with content: print('Hello, World!')", use create_file with file_path="bye.py" and content="print('Hello, World!')"
  - CORRECT: create_file bye.py print('Hello, World!')
  - CORRECT: create_file calculator.py def add(a, b): return a + b
  - WRONG: create_file {'file_path': 'bye.py', 'content': 'print(\'Hello, World!\')'}
  - WRONG: create_file {file_path: 'bye.py', content: 'print(\'Hello, World!\')'}
- To delete a file: Use the delete_file tool with file_path parameter
  - Example: When user says "delete the file hello.py", use delete_file with file_path="hello.py"
- To read a file: Use the read_file tool with file_path parameter
  - Example: When user says "read the README.md file", use read_file with file_path="README.md"
- To list files: Use the list_files tool with optional path parameter
  - Example: When user says "list all files", use list_files with path=""
- To find files by name: Use the find_file tool with file_name parameter
  - Example: When user says "find readme" or "find main.py", use find_file with file_name="readme" or file_name="main.py"
- To search for content: Use the search_files tool with query parameter
  - Example: When user says "search for login function", use search_files with query="login function"

**CRITICAL INPUT FORMAT RULES:**
- For create_file: Pass arguments as "file_path content" (space-separated)
- For edit_file: Pass arguments as "file_path new_content" (space-separated)  
- For delete_file: Pass arguments as "file_path" (just the file path)
- For read_file: Pass arguments as "file_path" (just the file path)
- Do NOT use JSON format or dictionary format like {'file_path': 'filename'}
- Do NOT include quotes around the entire argument string
- Do NOT include prefixes like "file_path:" or "content:"
- Do NOT use curly braces or dictionary syntax
- Use simple space-separated strings only

**EXAMPLES OF CORRECT FORMAT:**
- CORRECT: create_file calculator.py def add(a, b): return a + b
- CORRECT: create_file README.md # Project Documentation
- WRONG: create_file {'file_path': 'calculator.py', 'content': 'def add(a, b): return a + b'}
- WRONG: create_file {file_path: 'calculator.py', content: 'def add(a, b): return a + b'}
- WRONG: create_file "{'file_path': 'calculator.py'}"

**Guidelines:**
- Execute operations immediately when requested using the appropriate tools
- Use descriptive commit messages that explain what was changed and why
- Be careful with destructive operations - only ask for confirmation for major deletions
- When editing files, preserve the existing structure and formatting
- For complex changes, consider creating a new branch first
- Always test your understanding by reading files before making changes

**Available Tools:**
- **File Operations**: list_files, read_file, edit_file, create_file, delete_file
- **Repository Management**: search_files, get_file_history, create_branch

**Response Format:**
- For actions: Use the appropriate tool and report the actual result from the tool
- For questions: Answer based on repository content using the appropriate tools
- For confirmations: Execute the pending action immediately using the appropriate tool
- **For file creation**: After creating a file, always mention what was created and show a brief preview of the content
- **For file editing**: After editing a file, mention what was changed and show the updated content
- **For file reading**: Show the complete file content when reading files

**File Creation Best Practices:**
- When creating files, always use the create_file tool
- After successful creation, mention the file name and show the content that was created
- For code files, ensure proper syntax and formatting
- For documentation files, use clear and descriptive content

Remember: You are an ACTION-ORIENTED agent. You MUST use tools to execute tasks, don't just describe them. Always show the results of your actions, especially file content."""

    # Get GitHub token from environment if not provided
    if github_token is None:
        github_token = os.getenv("GITHUB_API_TOKEN")
    
    if not github_token:
        raise ValueError("GitHub token is required. Please set GITHUB_API_TOKEN environment variable or provide it as parameter.")
    
    # Create GitHub tools
    tools, modifier = create_github_tools(repo_url, github_token)
    
    # Create LLM using GitHub Marketplace model
    llm = ChatOpenAI(
        temperature=0.1, 
        openai_api_key=os.getenv("GITHUB_TOKEN"),
        base_url="https://models.github.ai/inference",
        model="openai/gpt-4.1-mini"
    )
    
    # Create agent with custom system prompt
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=20,
        agent_kwargs={"system_message": system_prompt}
    )
    
    return agent, modifier


def get_github_modifier_agent_with_forced_tools(repo_url: str, github_token: str = None):
    """
    Create a GitHub Code Modifier Agent with forced tool usage
    
    Args:
        repo_url: GitHub repository URL
        github_token: GitHub personal access token (optional)
        
    Returns:
        Tuple of (agent, modifier)
    """
    # Get GitHub token from environment if not provided
    if github_token is None:
        github_token = os.getenv("GITHUB_API_TOKEN")
    
    if not github_token:
        raise ValueError("GitHub token is required. Please set GITHUB_API_TOKEN environment variable or provide it as parameter.")
    
    # Create GitHub tools
    tools, modifier = create_github_tools(repo_url, github_token)
    
    # Create LLM using GitHub Marketplace model
    llm = ChatOpenAI(
        temperature=0.1, 
        openai_api_key=os.getenv("GITHUB_TOKEN"),
        base_url="https://models.github.ai/inference",
        model="openai/gpt-4.1-mini"
    )
    
    # Create agent
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=20
    )
    
    return agent, modifier 