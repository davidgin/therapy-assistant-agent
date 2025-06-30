"""
Async data acquisition service for free clinical data sources
"""

import asyncio
import aiofiles
import httpx
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
import json
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

from ..config.data_sources import (
    FREE_CLINICAL_DATA_SOURCES, 
    DataSource, 
    DataSourceType, 
    DataFormat,
    get_sources_by_category,
    get_high_reliability_sources
)

logger = logging.getLogger(__name__)

class DataAcquisitionService:
    """Service for acquiring data from free clinical sources"""
    
    def __init__(self, 
                 data_dir: str = "backend/data/acquired",
                 max_concurrent: int = 5,
                 timeout: int = 30):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.max_concurrent = max_concurrent
        self.timeout = httpx.Timeout(timeout)
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Create subdirectories for different types of data
        (self.data_dir / "guidelines").mkdir(exist_ok=True)
        (self.data_dir / "research").mkdir(exist_ok=True)
        (self.data_dir / "classifications").mkdir(exist_ok=True)
        (self.data_dir / "metadata").mkdir(exist_ok=True)
    
    async def acquire_all_sources(self, 
                                categories: Optional[List[str]] = None,
                                min_reliability: float = 0.8) -> Dict[str, Any]:
        """Acquire data from all configured sources"""
        results = {
            "acquired": [],
            "failed": [],
            "skipped": [],
            "total_sources": 0,
            "start_time": datetime.utcnow().isoformat()
        }
        
        # Filter sources based on criteria
        sources_to_process = []
        for name, source in FREE_CLINICAL_DATA_SOURCES.items():
            if source.reliability_score < min_reliability:
                results["skipped"].append({
                    "name": name,
                    "reason": f"Reliability score {source.reliability_score} < {min_reliability}"
                })
                continue
                
            if categories and not any(cat in source.categories for cat in categories):
                results["skipped"].append({
                    "name": name,
                    "reason": f"No matching categories in {categories}"
                })
                continue
                
            sources_to_process.append((name, source))
        
        results["total_sources"] = len(sources_to_process)
        
        # Process sources concurrently
        tasks = [
            self._acquire_source(name, source)
            for name, source in sources_to_process
        ]
        
        source_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Categorize results
        for i, result in enumerate(source_results):
            name = sources_to_process[i][0]
            if isinstance(result, Exception):
                results["failed"].append({
                    "name": name,
                    "error": str(result)
                })
            elif result.get("success"):
                results["acquired"].append({
                    "name": name,
                    "files": result.get("files", []),
                    "records": result.get("records", 0),
                    "size_bytes": result.get("size_bytes", 0)
                })
            else:
                results["failed"].append({
                    "name": name,
                    "error": result.get("error", "Unknown error")
                })
        
        results["end_time"] = datetime.utcnow().isoformat()
        
        # Save acquisition report
        await self._save_acquisition_report(results)
        
        return results
    
    async def _acquire_source(self, name: str, source: DataSource) -> Dict[str, Any]:
        """Acquire data from a single source"""
        async with self.semaphore:
            try:
                logger.info(f"Starting acquisition from {name}")
                
                if source.source_type == DataSourceType.API:
                    return await self._acquire_from_api(name, source)
                elif source.source_type == DataSourceType.DOWNLOAD:
                    return await self._acquire_from_download(name, source)
                elif source.source_type == DataSourceType.WEB_SCRAPE:
                    return await self._acquire_from_web_scrape(name, source)
                else:
                    return {"success": False, "error": f"Unsupported source type: {source.source_type}"}
                    
            except Exception as e:
                logger.error(f"Error acquiring from {name}: {e}")
                return {"success": False, "error": str(e)}
    
    async def _acquire_from_api(self, name: str, source: DataSource) -> Dict[str, Any]:
        """Acquire data from API source"""
        headers = {"User-Agent": "TherapyAssistant/1.0 (Educational Research)"}
        
        # Add API key if available
        api_key = self._get_api_key(name)
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # Handle rate limiting
                if source.rate_limit:
                    await asyncio.sleep(60 / source.rate_limit)
                
                response = await client.get(source.url, headers=headers)
                response.raise_for_status()
                
                # Save raw response
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"{name}_{timestamp}.{source.data_format.value}"
                filepath = self.data_dir / "api_responses" / filename
                filepath.parent.mkdir(exist_ok=True)
                
                content = response.content
                async with aiofiles.open(filepath, 'wb') as f:
                    await f.write(content)
                
                # Parse and extract relevant data
                parsed_data = await self._parse_response(content, source.data_format)
                
                # Save parsed data
                if parsed_data:
                    parsed_filepath = filepath.with_suffix('.json')
                    async with aiofiles.open(parsed_filepath, 'w') as f:
                        await f.write(json.dumps(parsed_data, indent=2))
                
                return {
                    "success": True,
                    "files": [str(filepath), str(parsed_filepath)],
                    "records": len(parsed_data) if isinstance(parsed_data, list) else 1,
                    "size_bytes": len(content)
                }
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limited
                    logger.warning(f"Rate limited for {name}, waiting...")
                    await asyncio.sleep(60)
                    return await self._acquire_from_api(name, source)  # Retry once
                raise
    
    async def _acquire_from_download(self, name: str, source: DataSource) -> Dict[str, Any]:
        """Acquire data from direct download source"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(source.url)
            response.raise_for_status()
            
            # Determine filename from URL or use default
            parsed_url = urlparse(source.url)
            filename = Path(parsed_url.path).name
            if not filename or not Path(filename).suffix:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"{name}_{timestamp}.{source.data_format.value}"
            
            # Save to appropriate category directory
            category_dir = self._get_category_dir(source.categories)
            filepath = category_dir / filename
            
            async with aiofiles.open(filepath, 'wb') as f:
                await f.write(response.content)
            
            return {
                "success": True,
                "files": [str(filepath)],
                "records": 1,
                "size_bytes": len(response.content)
            }
    
    async def _acquire_from_web_scrape(self, name: str, source: DataSource) -> Dict[str, Any]:
        """Acquire data from web scraping (basic implementation)"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(source.url)
            response.raise_for_status()
            
            # Save HTML content
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.html"
            category_dir = self._get_category_dir(source.categories)
            filepath = category_dir / filename
            
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(response.text)
            
            # Extract relevant links for PDFs and other resources
            extracted_links = await self._extract_resource_links(response.text, source.url)
            
            # Download linked resources
            downloaded_files = [str(filepath)]
            total_size = len(response.content)
            
            for link_url in extracted_links[:10]:  # Limit to first 10 links
                try:
                    link_response = await client.get(link_url)
                    link_response.raise_for_status()
                    
                    link_filename = Path(urlparse(link_url).path).name
                    if link_filename:
                        link_filepath = category_dir / f"{name}_{link_filename}"
                        async with aiofiles.open(link_filepath, 'wb') as f:
                            await f.write(link_response.content)
                        downloaded_files.append(str(link_filepath))
                        total_size += len(link_response.content)
                        
                        # Rate limiting
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    logger.warning(f"Failed to download linked resource {link_url}: {e}")
            
            return {
                "success": True,
                "files": downloaded_files,
                "records": len(extracted_links),
                "size_bytes": total_size
            }
    
    async def _parse_response(self, content: bytes, data_format: DataFormat) -> Any:
        """Parse response content based on format"""
        try:
            if data_format == DataFormat.JSON:
                return json.loads(content.decode('utf-8'))
            elif data_format == DataFormat.XML:
                root = ET.fromstring(content)
                return self._xml_to_dict(root)
            elif data_format == DataFormat.CSV:
                # Basic CSV parsing - could be enhanced
                text = content.decode('utf-8')
                lines = text.split('\n')
                if lines:
                    header = lines[0].split(',')
                    data = []
                    for line in lines[1:]:
                        if line.strip():
                            values = line.split(',')
                            if len(values) == len(header):
                                data.append(dict(zip(header, values)))
                    return data
            else:
                # Return as text for other formats
                return content.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Error parsing {data_format} content: {e}")
            return None
    
    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary"""
        result = {}
        
        # Add attributes
        if element.attrib:
            result.update(element.attrib)
        
        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            result['text'] = element.text.strip()
        
        # Add child elements
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                # Convert to list if multiple children with same tag
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    async def _extract_resource_links(self, html_content: str, base_url: str) -> List[str]:
        """Extract relevant resource links from HTML"""
        import re
        
        # Simple regex to find PDF and document links
        pdf_pattern = r'href=["\']([^"\']*\.pdf[^"\']*)["\']'
        doc_pattern = r'href=["\']([^"\']*\.(doc|docx|txt|rtf)[^"\']*)["\']'
        
        links = []
        
        for pattern in [pdf_pattern, doc_pattern]:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    link = match[0]
                else:
                    link = match
                
                # Convert relative URLs to absolute
                if link.startswith('/'):
                    link = urljoin(base_url, link)
                elif not link.startswith('http'):
                    link = urljoin(base_url, link)
                
                if link not in links:
                    links.append(link)
        
        return links
    
    def _get_category_dir(self, categories: List[str]) -> Path:
        """Get appropriate directory for data based on categories"""
        if "guidelines" in categories:
            return self.data_dir / "guidelines"
        elif "research" in categories:
            return self.data_dir / "research"
        elif "classification" in categories:
            return self.data_dir / "classifications"
        else:
            return self.data_dir / "general"
    
    def _get_api_key(self, source_name: str) -> Optional[str]:
        """Get API key for source from environment"""
        import os
        key_name = f"{source_name.upper()}_API_KEY"
        return os.getenv(key_name)
    
    async def _save_acquisition_report(self, results: Dict[str, Any]) -> None:
        """Save acquisition report to file"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_path = self.data_dir / "metadata" / f"acquisition_report_{timestamp}.json"
        
        async with aiofiles.open(report_path, 'w') as f:
            await f.write(json.dumps(results, indent=2))
        
        logger.info(f"Acquisition report saved to {report_path}")

# Convenience functions
async def download_clinical_guidelines() -> Dict[str, Any]:
    """Download clinical guidelines specifically"""
    service = DataAcquisitionService()
    return await service.acquire_all_sources(
        categories=["guidelines"],
        min_reliability=0.85
    )

async def download_research_data() -> Dict[str, Any]:
    """Download research data specifically"""
    service = DataAcquisitionService()
    return await service.acquire_all_sources(
        categories=["research", "evidence-based"],
        min_reliability=0.80
    )

async def download_classification_data() -> Dict[str, Any]:
    """Download classification systems (DSM, ICD)"""
    service = DataAcquisitionService()
    return await service.acquire_all_sources(
        categories=["classification"],
        min_reliability=0.90
    )

# Example usage
if __name__ == "__main__":
    async def main():
        service = DataAcquisitionService()
        
        # Download high-reliability sources only
        results = await service.acquire_all_sources(min_reliability=0.90)
        
        print(f"Acquisition completed:")
        print(f"- Acquired: {len(results['acquired'])} sources")
        print(f"- Failed: {len(results['failed'])} sources")
        print(f"- Skipped: {len(results['skipped'])} sources")
        
        for acquired in results['acquired']:
            print(f"  ✓ {acquired['name']}: {acquired['records']} records")
        
        for failed in results['failed']:
            print(f"  ✗ {failed['name']}: {failed['error']}")
    
    asyncio.run(main())