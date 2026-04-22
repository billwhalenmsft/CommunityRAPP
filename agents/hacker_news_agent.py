"""
Hacker News Agent - Real-time access to the Hacker News API
Fetches top stories, new posts, best discussions, jobs, and more.
"""

import requests
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# HN Firebase API
HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
# Algolia HN Search API
HN_SEARCH_API = "https://hn.algolia.com/api/v1"


class HackerNewsAgent:
    """Agent for fetching and analyzing Hacker News content."""
    
    def __init__(self, name: str = "HackerNews", metadata: dict = None):
        self.name = name
        self.metadata = metadata or {}
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "RAPP-HackerNews-Agent/1.0"
        })
    
    def perform(self, action: str, **kwargs) -> str:
        """Main entry point for agent actions."""
        actions = {
            "get_top_stories": self.get_top_stories,
            "get_new_stories": self.get_new_stories,
            "get_best_stories": self.get_best_stories,
            "get_ask_hn": self.get_ask_hn,
            "get_show_hn": self.get_show_hn,
            "get_jobs": self.get_jobs,
            "get_story_details": self.get_story_details,
            "search_stories": self.search_stories,
        }
        
        if action not in actions:
            return f"❌ Unknown action: {action}. Available: {', '.join(actions.keys())}"
        
        try:
            return actions[action](**kwargs)
        except Exception as e:
            logger.error(f"Error in HackerNewsAgent.{action}: {e}")
            return f"❌ Error fetching from Hacker News: {str(e)}"
    
    def _fetch_story_ids(self, endpoint: str) -> List[int]:
        """Fetch story IDs from HN API."""
        url = f"{HN_API_BASE}/{endpoint}"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def _fetch_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single item (story/comment) from HN API."""
        url = f"{HN_API_BASE}/item/{item_id}.json"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def _relative_time(self, timestamp: int) -> str:
        """Convert Unix timestamp to relative time string."""
        now = datetime.now(timezone.utc)
        posted = datetime.fromtimestamp(timestamp, timezone.utc)
        diff = now - posted
        
        seconds = diff.total_seconds()
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            mins = int(seconds / 60)
            return f"{mins} min{'s' if mins != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
    
    def _format_story(self, story: Dict[str, Any], index: int = None) -> str:
        """Format a story for display."""
        if not story:
            return ""
        
        title = story.get("title", "Untitled")
        score = story.get("score", 0)
        url = story.get("url", "")
        comments = story.get("descendants", 0)
        author = story.get("by", "unknown")
        time_str = self._relative_time(story.get("time", 0))
        story_type = story.get("type", "story")
        
        # Extract domain from URL
        domain = ""
        if url:
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc.replace("www.", "")
            except:
                domain = url[:30]
        
        # Build formatted string
        prefix = f"{index}. " if index else ""
        lines = [f"{prefix}**{title}** ({score} pts)"]
        
        if domain:
            lines.append(f"   🔗 {domain} | 💬 {comments} comments")
        else:
            lines.append(f"   💬 {comments} comments | by {author}")
        
        lines.append(f"   ⏰ {time_str}")
        
        return "\n".join(lines)
    
    def _fetch_and_format_stories(self, endpoint: str, emoji: str, title: str, limit: int = 10) -> str:
        """Generic method to fetch and format a list of stories."""
        limit = min(limit or 10, 30)  # Cap at 30
        
        story_ids = self._fetch_story_ids(endpoint)[:limit]
        
        stories = []
        for story_id in story_ids:
            story = self._fetch_item(story_id)
            if story:
                stories.append(story)
        
        if not stories:
            return f"❌ No stories found."
        
        output = [f"**{emoji} {title}:**\n"]
        for i, story in enumerate(stories, 1):
            output.append(self._format_story(story, i))
            output.append("")  # Blank line between stories
        
        output.append("---")
        output.append("*Reply with a story number to get more details!*")
        
        return "\n".join(output)
    
    def get_top_stories(self, limit: int = 10) -> str:
        """Fetch the current top stories from Hacker News front page."""
        return self._fetch_and_format_stories(
            "topstories.json", "🔥", f"Top {limit} Hacker News Stories", limit
        )
    
    def get_new_stories(self, limit: int = 10) -> str:
        """Fetch the newest stories just submitted to HN."""
        return self._fetch_and_format_stories(
            "newstories.json", "🆕", f"Latest {limit} Stories", limit
        )
    
    def get_best_stories(self, limit: int = 10) -> str:
        """Fetch the highest-voted stories of recent time."""
        return self._fetch_and_format_stories(
            "beststories.json", "⭐", f"Best {limit} Stories", limit
        )
    
    def get_ask_hn(self, limit: int = 10) -> str:
        """Fetch 'Ask HN' discussion threads."""
        return self._fetch_and_format_stories(
            "askstories.json", "❓", f"Top {limit} Ask HN Discussions", limit
        )
    
    def get_show_hn(self, limit: int = 10) -> str:
        """Fetch 'Show HN' project showcases."""
        return self._fetch_and_format_stories(
            "showstories.json", "🚀", f"Top {limit} Show HN Projects", limit
        )
    
    def get_jobs(self, limit: int = 10) -> str:
        """Fetch current job postings from HN."""
        limit = min(limit or 10, 30)
        
        story_ids = self._fetch_story_ids("jobstories.json")[:limit]
        
        jobs = []
        for job_id in story_ids:
            job = self._fetch_item(job_id)
            if job:
                jobs.append(job)
        
        if not jobs:
            return "❌ No job postings found."
        
        output = [f"**💼 Latest {len(jobs)} HN Job Postings:**\n"]
        
        for i, job in enumerate(jobs, 1):
            title = job.get("title", "Untitled")
            url = job.get("url", "")
            time_str = self._relative_time(job.get("time", 0))
            
            output.append(f"{i}. **{title}**")
            if url:
                output.append(f"   🔗 {url[:50]}...")
            output.append(f"   ⏰ Posted {time_str}")
            output.append("")
        
        return "\n".join(output)
    
    def get_story_details(self, story_id: int) -> str:
        """Get full details for a specific story including top comments."""
        story = self._fetch_item(story_id)
        
        if not story:
            return f"❌ Story {story_id} not found."
        
        title = story.get("title", "Untitled")
        score = story.get("score", 0)
        url = story.get("url", "")
        author = story.get("by", "unknown")
        time_str = self._relative_time(story.get("time", 0))
        text = story.get("text", "")
        comment_ids = story.get("kids", [])[:5]  # Top 5 comments
        
        output = [
            "**📖 Story Details:**\n",
            f"**Title:** {title}",
            f"**Author:** {author}",
            f"**Score:** {score} points",
            f"**Posted:** {time_str}",
            f"**Comments:** {len(story.get('kids', []))}",
        ]
        
        if url:
            output.append(f"**URL:** {url}")
        
        if text:
            # Clean HTML from self-posts
            import re
            clean_text = re.sub(r'<[^>]+>', '', text)[:500]
            output.append(f"\n**Content:**\n> {clean_text}...")
        
        # Fetch top comments
        if comment_ids:
            output.append("\n**Top Comments:**")
            for cid in comment_ids:
                comment = self._fetch_item(cid)
                if comment and comment.get("text"):
                    import re
                    comment_text = re.sub(r'<[^>]+>', '', comment.get("text", ""))[:200]
                    comment_author = comment.get("by", "anon")
                    output.append(f"\n> \"{comment_text}...\" - *{comment_author}*")
        
        return "\n".join(output)
    
    def search_stories(self, query: str, limit: int = 10) -> str:
        """Search for stories matching a query using Algolia HN Search API."""
        limit = min(limit or 10, 30)
        
        url = f"{HN_SEARCH_API}/search"
        params = {
            "query": query,
            "tags": "story",
            "hitsPerPage": limit
        }
        
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        hits = data.get("hits", [])
        
        if not hits:
            return f"❌ No stories found for '{query}'."
        
        output = [f"**🔍 Search Results for '{query}':**\n"]
        
        for i, hit in enumerate(hits, 1):
            title = hit.get("title", "Untitled")
            points = hit.get("points", 0)
            url = hit.get("url", "")
            comments = hit.get("num_comments", 0)
            author = hit.get("author", "unknown")
            
            output.append(f"{i}. **{title}** ({points} pts)")
            output.append(f"   💬 {comments} comments | by {author}")
            if url:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc.replace("www.", "")
                output.append(f"   🔗 {domain}")
            output.append("")
        
        total = data.get("nbHits", len(hits))
        output.append(f"---\n*Found {total} total results. Showing top {len(hits)}.*")
        
        return "\n".join(output)


# Convenience function for direct use
def fetch_hacker_news(action: str, **kwargs) -> str:
    """Quick function to fetch HN data without instantiating the agent."""
    agent = HackerNewsAgent()
    return agent.perform(action, **kwargs)


# Example usage when run directly
if __name__ == "__main__":
    agent = HackerNewsAgent()
    
    print("=" * 60)
    print("HACKER NEWS AGENT - Live Demo")
    print("=" * 60)
    
    print("\n📥 Fetching top 5 stories...\n")
    print(agent.get_top_stories(limit=5))
    
    print("\n" + "=" * 60)
    print("\n🔍 Searching for 'Python'...\n")
    print(agent.search_stories("Python", limit=3))
