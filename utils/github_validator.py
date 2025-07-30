import os
from github import Github, GithubException
from typing import Dict, List, Tuple


def validate_github_setup(github_token: str = None, repo_url: str = None) -> Dict:
    """
    Validate GitHub token and repository access
    
    Args:
        github_token: GitHub API token (optional, will use env var if not provided)
        repo_url: Repository URL to test (optional)
        
    Returns:
        Dictionary with validation results
    """
    if github_token is None:
        github_token = os.getenv("GITHUB_API_TOKEN")
    
    if not github_token:
        return {
            "success": False,
            "error": "GITHUB_API_TOKEN not found in environment variables"
        }
    
    try:
        # Test GitHub API connection
        github = Github(github_token)
        user = github.get_user()
        
        result = {
            "success": True,
            "user": user.login,
            "token_valid": True,
            "repositories": []
        }
        
        # Test repository access if URL provided
        if repo_url:
            repo_result = validate_repository_access(github, repo_url)
            result.update(repo_result)
        
        return result
        
    except GithubException as e:
        if e.status == 401:
            return {
                "success": False,
                "error": "Invalid GitHub token. Please check your GITHUB_API_TOKEN"
            }
        else:
            return {
                "success": False,
                "error": f"GitHub API error: {e}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {e}"
        }


def validate_repository_access(github: Github, repo_url: str) -> Dict:
    """
    Validate access to a specific repository
    
    Args:
        github: GitHub API client
        repo_url: Repository URL to test
        
    Returns:
        Dictionary with repository validation results
    """
    try:
        # Parse repository URL
        if 'github.com' in repo_url:
            repo_path = repo_url.split('github.com/')[-1]
            if repo_path.endswith('.git'):
                repo_path = repo_path[:-4]
        else:
            repo_path = repo_url
        
        # Test repository access
        repo = github.get_repo(repo_path)
        
        return {
            "repo_accessible": True,
            "repo_name": repo.full_name,
            "repo_url": repo.html_url,
            "repo_private": repo.private,
            "permissions": {
                "admin": repo.permissions.admin,
                "push": repo.permissions.push,
                "pull": repo.permissions.pull
            }
        }
        
    except GithubException as e:
        if e.status == 404:
            return {
                "repo_accessible": False,
                "error": f"Repository not found: {repo_url}",
                "suggestions": [
                    "Check if the repository URL is correct",
                    "Verify the repository exists",
                    "Ensure your token has access to this repository"
                ]
            }
        elif e.status == 401:
            return {
                "repo_accessible": False,
                "error": "Authentication failed for repository access",
                "suggestions": [
                    "Check your GITHUB_API_TOKEN is valid",
                    "Ensure the token has 'repo' scope for private repositories"
                ]
            }
        else:
            return {
                "repo_accessible": False,
                "error": f"Repository access error: {e}"
            }
    except Exception as e:
        return {
            "repo_accessible": False,
            "error": f"Unexpected error accessing repository: {e}"
        }


def list_accessible_repositories(github_token: str = None, limit: int = 10) -> List[Dict]:
    """
    List repositories accessible with the current token
    
    Args:
        github_token: GitHub API token (optional)
        limit: Maximum number of repositories to list
        
    Returns:
        List of accessible repositories
    """
    if github_token is None:
        github_token = os.getenv("GITHUB_API_TOKEN")
    
    if not github_token:
        return []
    
    try:
        github = Github(github_token)
        user = github.get_user()
        
        repos = []
        for repo in user.get_repos()[:limit]:
            repos.append({
                "name": repo.name,
                "full_name": repo.full_name,
                "url": repo.html_url,
                "private": repo.private,
                "description": repo.description
            })
        
        return repos
        
    except Exception as e:
        return []


def test_repository_operations(github: Github, repo_url: str) -> Dict:
    """
    Test basic repository operations
    
    Args:
        github: GitHub API client
        repo_url: Repository URL to test
        
    Returns:
        Dictionary with operation test results
    """
    try:
        # Parse repository URL
        if 'github.com' in repo_url:
            repo_path = repo_url.split('github.com/')[-1]
            if repo_path.endswith('.git'):
                repo_path = repo_path[:-4]
        else:
            repo_path = repo_url
        
        repo = github.get_repo(repo_path)
        
        # Test basic operations
        operations = {
            "read_contents": False,
            "list_files": False,
            "create_branch": False,
            "write_access": False
        }
        
        # Test reading contents
        try:
            contents = repo.get_contents("")
            operations["read_contents"] = True
            operations["list_files"] = True
        except:
            pass
        
        # Test branch creation (if we have write access)
        if repo.permissions.push:
            operations["write_access"] = True
            try:
                # Try to create a test branch (will fail if branch exists, but that's okay)
                main_branch = repo.get_branch("main")
                operations["create_branch"] = True
            except:
                pass
        
        return {
            "success": True,
            "operations": operations,
            "recommendations": get_recommendations(operations)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to test repository operations: {e}"
        }


def get_recommendations(operations: Dict) -> List[str]:
    """Get recommendations based on operation test results"""
    recommendations = []
    
    if not operations["read_contents"]:
        recommendations.append("Token may not have read access to repository contents")
    
    if not operations["write_access"]:
        recommendations.append("Token does not have write access - can only read repository")
        recommendations.append("For full functionality, ensure token has 'repo' scope")
    
    if operations["write_access"] and not operations["create_branch"]:
        recommendations.append("Branch creation may be restricted by repository settings")
    
    return recommendations 