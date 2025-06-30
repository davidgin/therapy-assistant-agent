"""
Async HTTP service for external API calls
"""

import httpx
import asyncio
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AsyncHttpService:
    """Async HTTP client service for external API calls"""
    
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
                headers={"User-Agent": "TherapyAssistant/1.0"}
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def get(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> httpx.Response:
        """Make async GET request"""
        client = await self.get_client()
        try:
            response = await client.get(url, headers=headers, **kwargs)
            return response
        except httpx.RequestError as e:
            logger.error(f"HTTP GET error for {url}: {e}")
            raise
    
    async def post(self, url: str, data: Optional[Dict[str, Any]] = None, 
                   json_data: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None, **kwargs) -> httpx.Response:
        """Make async POST request"""
        client = await self.get_client()
        try:
            response = await client.post(
                url, 
                data=data, 
                json=json_data, 
                headers=headers, 
                **kwargs
            )
            return response
        except httpx.RequestError as e:
            logger.error(f"HTTP POST error for {url}: {e}")
            raise
    
    async def put(self, url: str, data: Optional[Dict[str, Any]] = None,
                  json_data: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, str]] = None, **kwargs) -> httpx.Response:
        """Make async PUT request"""
        client = await self.get_client()
        try:
            response = await client.put(
                url, 
                data=data, 
                json=json_data, 
                headers=headers, 
                **kwargs
            )
            return response
        except httpx.RequestError as e:
            logger.error(f"HTTP PUT error for {url}: {e}")
            raise
    
    async def delete(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> httpx.Response:
        """Make async DELETE request"""
        client = await self.get_client()
        try:
            response = await client.delete(url, headers=headers, **kwargs)
            return response
        except httpx.RequestError as e:
            logger.error(f"HTTP DELETE error for {url}: {e}")
            raise

# Global instance
http_service = AsyncHttpService()

async def get_http_service() -> AsyncHttpService:
    """Dependency to get HTTP service"""
    return http_service

# Context manager for automatic cleanup
class HttpServiceManager:
    """Context manager for HTTP service lifecycle"""
    
    def __init__(self):
        self.service = AsyncHttpService()
    
    async def __aenter__(self) -> AsyncHttpService:
        return self.service
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.service.close()

# Example usage functions
async def fetch_external_data(url: str) -> Dict[str, Any]:
    """Example function to fetch external data"""
    async with HttpServiceManager() as http:
        try:
            response = await http.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for {url}: {e}")
            raise

async def post_external_data(url: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Example function to post data to external API"""
    async with HttpServiceManager() as http:
        try:
            response = await http.post(url, json_data=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for {url}: {e}")
            raise