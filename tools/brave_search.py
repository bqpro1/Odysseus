from typing import List, Dict, Any, Optional
import requests
import logging
from pydantic import BaseModel, Field, HttpUrl, validator
from agents import function_tool, RunContextWrapper

# Configure logging
logger = logging.getLogger(__name__)

class SearchQuery(BaseModel):
    """Model for Brave Search query parameters"""
    query: str = Field(..., description="The search query to look up on Brave Search")
    count: int = Field(default=10, ge=1, le=20, description="Number of results to return (1-20)")

class SearchResultItem(BaseModel):
    """Model for a single search result item"""
    title: str = Field(default="", description="Title of the search result")
    link: HttpUrl = Field(description="URL of the search result")
    snippet: str = Field(default="", description="Description snippet of the search result")
    
    @validator('link', pre=True)
    def ensure_valid_url(cls, v):
        if not v:
            raise ValueError("URL cannot be empty")
        return v

class SearchResults(BaseModel):
    """Model for the search results response"""
    results: List[SearchResultItem] = Field(default_factory=list, description="List of search results")
    error: Optional[str] = Field(default=None, description="Error message if search failed")

class BraveSearchTool:
    """Tool for searching the web using Brave Search API"""
    
    def __init__(self, api_key: str):
        """Initialize the Brave Search tool with the API key"""
        self.api_key = api_key
        self.url = "https://api.search.brave.com/res/v1/web/search"
        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
    
    @function_tool
    async def brave_search(self, ctx: RunContextWrapper[Any], query: str, count: int = 10) -> Dict[str, Any]:
        """Search the web using the Brave Search API.
        
        Args:
            ctx: The run context.
            query: The search query to look up on Brave Search.
            count: Number of results to return (1-20).
            
        Returns:
            A dictionary containing search results and optional error information.
        """
        # Validate input parameters
        search_params = SearchQuery(query=query, count=count)
        
        params = {
            "q": search_params.query,
            "count": search_params.count,
        }
        
        try:
            response = requests.get(self.url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process and validate results
            results = []
            for item in data.get("web", {}).get("results", []):
                try:
                    result_item = SearchResultItem(
                        title=item.get("title", ""),
                        link=item.get("url", ""),
                        snippet=item.get("description", "")
                    )
                    results.append(result_item)
                except ValueError as e:
                    # Log validation errors but continue processing other results
                    logger.warning(f"Skipping invalid result: {str(e)}")
            
            # Create and validate the final response
            search_results = SearchResults(results=results)
            return search_results.model_dump()
            
        except Exception as e:
            logger.error(f"Error in Brave Search: {str(e)}")
            error_results = SearchResults(results=[], error=str(e))
            return error_results.model_dump() 