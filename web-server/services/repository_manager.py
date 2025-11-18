"""
Repository Manager Service
Handles git operations for project repositories.
"""
import os
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime
from git import Repo, GitCommandError
from git.exc import InvalidGitRepositoryError, NoSuchPathError

logger = logging.getLogger(__name__)


class RepositoryManager:
    """
    Manage git repositories for ESP32 projects.
    
    Responsibilities:
    - Clone repositories from GitHub
    - Update (pull) repositories
    - Checkout specific commits/branches
    - Get commit information
    - Calculate diffs between commits
    """
    
    def __init__(self, base_dir: str = "/app/projects"):
        """
        Initialize repository manager.
        
        Args:
            base_dir: Base directory for cloning repositories
        """
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        logger.info(f"Repository manager initialized with base_dir: {base_dir}")
    
    async def clone_repository(
        self,
        repo_url: str,
        clone_path: str,
        branch: str = "main",
        timeout: int = 300
    ) -> Dict[str, any]:
        """
        Clone a repository from GitHub.
        
        Args:
            repo_url: GitHub repository URL
            clone_path: Local path to clone to
            branch: Branch to checkout
            timeout: Timeout in seconds
        
        Returns:
            Dict with clone result:
            {
                "success": bool,
                "clone_path": str,
                "commit_sha": str,
                "commit_message": str,
                "error": str (if failed)
            }
        """
        try:
            logger.info(f"Cloning repository {repo_url} to {clone_path}")
            
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(clone_path), exist_ok=True)
            
            # Check if directory already exists
            if os.path.exists(clone_path):
                logger.warning(f"Path {clone_path} already exists, removing...")
                await self._remove_directory(clone_path)
            
            # Clone repository (blocking operation, run in executor)
            repo = await asyncio.to_thread(
                Repo.clone_from,
                repo_url,
                clone_path,
                branch=branch,
                depth=1  # Shallow clone for faster cloning
            )
            
            # Get latest commit info
            commit = repo.head.commit
            
            result = {
                "success": True,
                "clone_path": clone_path,
                "commit_sha": commit.hexsha,
                "commit_message": commit.message.strip(),
                "commit_author": commit.author.name,
                "committed_date": datetime.fromtimestamp(commit.committed_date)
            }
            
            logger.info(f"✅ Successfully cloned {repo_url} to {clone_path}")
            logger.info(f"   Latest commit: {commit.hexsha[:8]} - {commit.message.strip()}")
            
            return result
            
        except GitCommandError as e:
            error_msg = f"Git command failed: {str(e)}"
            logger.error(f"❌ Failed to clone {repo_url}: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ Failed to clone {repo_url}: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    async def update_repository(
        self,
        clone_path: str,
        branch: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Update repository by pulling latest changes.
        
        Args:
            clone_path: Path to local repository
            branch: Branch to update (None = current branch)
        
        Returns:
            Dict with update result:
            {
                "success": bool,
                "previous_commit": str,
                "current_commit": str,
                "commits_pulled": int,
                "files_changed": int,
                "insertions": int,
                "deletions": int,
                "error": str (if failed)
            }
        """
        try:
            logger.info(f"Updating repository at {clone_path}")
            
            # Open existing repository
            repo = Repo(clone_path)
            
            # Get current commit before pull
            previous_commit = repo.head.commit.hexsha
            
            # Checkout branch if specified
            if branch and repo.active_branch.name != branch:
                logger.info(f"Checking out branch: {branch}")
                await asyncio.to_thread(repo.git.checkout, branch)
            
            # Pull latest changes
            origin = repo.remotes.origin
            pull_info = await asyncio.to_thread(origin.pull)
            
            # Get current commit after pull
            current_commit = repo.head.commit.hexsha
            
            # Calculate changes
            if previous_commit != current_commit:
                diff = repo.commit(previous_commit).diff(repo.commit(current_commit))
                
                result = {
                    "success": True,
                    "previous_commit": previous_commit,
                    "current_commit": current_commit,
                    "commits_pulled": len(list(repo.iter_commits(f'{previous_commit}..{current_commit}'))),
                    "files_changed": len(diff),
                    "insertions": sum(d.diff.decode('utf-8', errors='ignore').count('\n+') for d in diff if d.diff),
                    "deletions": sum(d.diff.decode('utf-8', errors='ignore').count('\n-') for d in diff if d.diff)
                }
                
                logger.info(f"✅ Updated repository: {result['commits_pulled']} new commits")
            else:
                result = {
                    "success": True,
                    "previous_commit": previous_commit,
                    "current_commit": current_commit,
                    "commits_pulled": 0,
                    "files_changed": 0,
                    "insertions": 0,
                    "deletions": 0
                }
                logger.info("ℹ️ Repository already up to date")
            
            return result
            
        except InvalidGitRepositoryError:
            error_msg = f"Not a git repository: {clone_path}"
            logger.error(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
        except NoSuchPathError:
            error_msg = f"Path does not exist: {clone_path}"
            logger.error(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
        except GitCommandError as e:
            error_msg = f"Git command failed: {str(e)}"
            logger.error(f"❌ Failed to update {clone_path}: {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ Failed to update {clone_path}: {error_msg}")
            return {"success": False, "error": error_msg}
    
    async def checkout_commit(
        self,
        clone_path: str,
        commit_sha: str
    ) -> Dict[str, any]:
        """
        Checkout a specific commit.
        
        Args:
            clone_path: Path to local repository
            commit_sha: Commit SHA to checkout
        
        Returns:
            Dict with checkout result
        """
        try:
            logger.info(f"Checking out commit {commit_sha} in {clone_path}")
            
            repo = Repo(clone_path)
            await asyncio.to_thread(repo.git.checkout, commit_sha)
            
            commit = repo.head.commit
            
            result = {
                "success": True,
                "commit_sha": commit.hexsha,
                "commit_message": commit.message.strip(),
                "commit_author": commit.author.name
            }
            
            logger.info(f"✅ Checked out commit {commit_sha[:8]}")
            return result
            
        except GitCommandError as e:
            error_msg = f"Git command failed: {str(e)}"
            logger.error(f"❌ Failed to checkout {commit_sha}: {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ Failed to checkout {commit_sha}: {error_msg}")
            return {"success": False, "error": error_msg}
    
    async def get_latest_commit(
        self,
        clone_path: str
    ) -> Dict[str, any]:
        """
        Get information about the latest commit.
        
        Args:
            clone_path: Path to local repository
        
        Returns:
            Dict with commit information
        """
        try:
            repo = Repo(clone_path)
            commit = repo.head.commit
            
            return {
                "success": True,
                "commit_sha": commit.hexsha,
                "commit_message": commit.message.strip(),
                "commit_author": commit.author.name,
                "commit_email": commit.author.email,
                "committed_date": datetime.fromtimestamp(commit.committed_date),
                "branch": repo.active_branch.name
            }
            
        except Exception as e:
            error_msg = f"Failed to get commit info: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
    
    async def get_diff(
        self,
        clone_path: str,
        from_commit: str,
        to_commit: str
    ) -> Dict[str, any]:
        """
        Get diff between two commits.
        
        Args:
            clone_path: Path to local repository
            from_commit: Starting commit SHA
            to_commit: Ending commit SHA
        
        Returns:
            Dict with diff statistics
        """
        try:
            repo = Repo(clone_path)
            
            diff = repo.commit(from_commit).diff(repo.commit(to_commit))
            
            files_changed = []
            total_insertions = 0
            total_deletions = 0
            
            for d in diff:
                if d.diff:
                    diff_text = d.diff.decode('utf-8', errors='ignore')
                    insertions = diff_text.count('\n+')
                    deletions = diff_text.count('\n-')
                    
                    files_changed.append({
                        "file": d.a_path or d.b_path,
                        "change_type": d.change_type,
                        "insertions": insertions,
                        "deletions": deletions
                    })
                    
                    total_insertions += insertions
                    total_deletions += deletions
            
            return {
                "success": True,
                "from_commit": from_commit,
                "to_commit": to_commit,
                "files_changed": files_changed,
                "total_files": len(files_changed),
                "total_insertions": total_insertions,
                "total_deletions": total_deletions
            }
            
        except Exception as e:
            error_msg = f"Failed to get diff: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
    
    async def repository_exists(self, clone_path: str) -> bool:
        """Check if repository exists and is valid."""
        try:
            Repo(clone_path)
            return True
        except (InvalidGitRepositoryError, NoSuchPathError):
            return False
    
    async def _remove_directory(self, path: str):
        """Remove directory recursively."""
        import shutil
        if os.path.exists(path):
            await asyncio.to_thread(shutil.rmtree, path)
            logger.info(f"Removed directory: {path}")
