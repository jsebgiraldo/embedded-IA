"""
GitHub Webhook Service
Handles incoming webhooks from GitHub.
"""
import hmac
import hashlib
import json
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class WebhookService:
    """
    Handle GitHub webhook events.
    
    Responsibilities:
    - Validate webhook signatures
    - Parse event payloads
    - Extract relevant information
    """
    
    def __init__(self):
        """Initialize webhook service."""
        logger.info("Webhook service initialized")
    
    def validate_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Validate GitHub webhook signature using HMAC-SHA256.
        
        GitHub sends: X-Hub-Signature-256: sha256=<hash>
        We compute: HMAC-SHA256(secret, payload)
        
        Args:
            payload: Raw request body
            signature: Signature from X-Hub-Signature-256 header
            secret: Webhook secret configured in GitHub
        
        Returns:
            True if signature is valid, False otherwise
        """
        if not secret:
            logger.warning("No webhook secret configured, skipping validation")
            return True
        
        try:
            # Remove 'sha256=' prefix if present
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            # Compute expected signature
            expected = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare using constant-time comparison
            is_valid = hmac.compare_digest(expected, signature)
            
            if is_valid:
                logger.info("✅ Webhook signature valid")
            else:
                logger.error("❌ Webhook signature invalid")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ Failed to validate signature: {e}")
            return False
    
    def parse_push_event(self, payload: dict) -> Dict[str, any]:
        """
        Parse push event payload.
        
        Args:
            payload: GitHub push event payload
        
        Returns:
            Dict with extracted information:
            {
                "repo_full_name": "owner/repo",
                "repo_url": "https://github.com/owner/repo",
                "branch": "main",
                "commit_sha": "abc123...",
                "commit_message": "Fix bug",
                "commit_author": "John Doe",
                "commit_email": "john@example.com",
                "commits_count": 1,
                "pusher": "github_username"
            }
        """
        try:
            repository = payload.get("repository", {})
            ref = payload.get("ref", "")  # refs/heads/main
            head_commit = payload.get("head_commit", {})
            pusher = payload.get("pusher", {})
            
            # Extract branch from ref
            branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
            
            result = {
                "repo_full_name": repository.get("full_name"),
                "repo_url": repository.get("clone_url"),
                "branch": branch,
                "commit_sha": head_commit.get("id"),
                "commit_message": head_commit.get("message", "").strip(),
                "commit_author": head_commit.get("author", {}).get("name"),
                "commit_email": head_commit.get("author", {}).get("email"),
                "committed_at": head_commit.get("timestamp"),
                "commits_count": len(payload.get("commits", [])),
                "pusher": pusher.get("name")
            }
            
            logger.info(f"📝 Parsed push event: {result['repo_full_name']} @ {result['branch']}")
            logger.info(f"   Commit: {result['commit_sha'][:8]} - {result['commit_message'][:50]}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to parse push event: {e}")
            return {}
    
    def parse_pull_request_event(self, payload: dict) -> Dict[str, any]:
        """
        Parse pull request event payload.
        
        Args:
            payload: GitHub pull_request event payload
        
        Returns:
            Dict with extracted information:
            {
                "repo_full_name": "owner/repo",
                "repo_url": "https://github.com/owner/repo",
                "pr_number": 123,
                "pr_title": "Fix bug",
                "pr_action": "opened",
                "source_branch": "feature-branch",
                "target_branch": "main",
                "commit_sha": "abc123...",
                "author": "github_username"
            }
        """
        try:
            pull_request = payload.get("pull_request", {})
            repository = payload.get("repository", {})
            action = payload.get("action")  # opened, synchronize, reopened, closed
            
            result = {
                "repo_full_name": repository.get("full_name"),
                "repo_url": repository.get("clone_url"),
                "pr_number": pull_request.get("number"),
                "pr_title": pull_request.get("title"),
                "pr_action": action,
                "source_branch": pull_request.get("head", {}).get("ref"),
                "target_branch": pull_request.get("base", {}).get("ref"),
                "commit_sha": pull_request.get("head", {}).get("sha"),
                "author": pull_request.get("user", {}).get("login"),
                "mergeable": pull_request.get("mergeable"),
                "merged": pull_request.get("merged", False)
            }
            
            logger.info(f"🔀 Parsed PR event: {result['repo_full_name']} PR #{result['pr_number']}")
            logger.info(f"   Action: {action} | {result['source_branch']} → {result['target_branch']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to parse PR event: {e}")
            return {}
    
    def should_trigger_build(
        self,
        event_type: str,
        event_data: dict
    ) -> bool:
        """
        Determine if event should trigger a build.
        
        Args:
            event_type: Type of GitHub event
            event_data: Parsed event data
        
        Returns:
            True if build should be triggered
        """
        # Push events always trigger builds
        if event_type == "push":
            return True
        
        # PR events only trigger on certain actions
        if event_type == "pull_request":
            action = event_data.get("pr_action")
            # Trigger on: opened, synchronize (new commits), reopened
            return action in ["opened", "synchronize", "reopened"]
        
        # Ping events don't trigger builds
        if event_type == "ping":
            return False
        
        # Unknown event types don't trigger builds
        logger.warning(f"⚠️ Unknown event type: {event_type}")
        return False
    
    def extract_project_identifier(
        self,
        payload: dict
    ) -> Optional[str]:
        """
        Extract project identifier from payload.
        
        Uses repository full name (owner/repo) as identifier.
        
        Args:
            payload: GitHub webhook payload
        
        Returns:
            Repository full name or None
        """
        try:
            repository = payload.get("repository", {})
            return repository.get("full_name")
        except Exception:
            return None
