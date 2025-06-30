"""
Async file I/O service
"""

import aiofiles
import aiofiles.os
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

class AsyncFileService:
    """Async file operations service"""
    
    @staticmethod
    async def read_text(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """Read text file asynchronously"""
        try:
            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                content = await f.read()
            return content
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise
    
    @staticmethod
    async def write_text(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> None:
        """Write text file asynchronously"""
        try:
            # Ensure directory exists
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding=encoding) as f:
                await f.write(content)
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            raise
    
    @staticmethod
    async def read_json(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Read JSON file asynchronously"""
        try:
            content = await AsyncFileService.read_text(file_path)
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading JSON file {file_path}: {e}")
            raise
    
    @staticmethod
    async def write_json(file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> None:
        """Write JSON file asynchronously"""
        try:
            content = json.dumps(data, indent=indent, ensure_ascii=False)
            await AsyncFileService.write_text(file_path, content)
        except Exception as e:
            logger.error(f"Error writing JSON file {file_path}: {e}")
            raise
    
    @staticmethod
    async def read_lines(file_path: Union[str, Path], encoding: str = 'utf-8') -> List[str]:
        """Read file lines asynchronously"""
        try:
            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                lines = await f.readlines()
            return [line.rstrip('\n\r') for line in lines]
        except Exception as e:
            logger.error(f"Error reading lines from {file_path}: {e}")
            raise
    
    @staticmethod
    async def write_lines(file_path: Union[str, Path], lines: List[str], encoding: str = 'utf-8') -> None:
        """Write lines to file asynchronously"""
        try:
            content = '\n'.join(lines) + '\n'
            await AsyncFileService.write_text(file_path, content, encoding)
        except Exception as e:
            logger.error(f"Error writing lines to {file_path}: {e}")
            raise
    
    @staticmethod
    async def append_text(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> None:
        """Append text to file asynchronously"""
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'a', encoding=encoding) as f:
                await f.write(content)
        except Exception as e:
            logger.error(f"Error appending to file {file_path}: {e}")
            raise
    
    @staticmethod
    async def file_exists(file_path: Union[str, Path]) -> bool:
        """Check if file exists asynchronously"""
        try:
            return await aiofiles.os.path.exists(file_path)
        except Exception as e:
            logger.error(f"Error checking file existence {file_path}: {e}")
            return False
    
    @staticmethod
    async def get_file_size(file_path: Union[str, Path]) -> int:
        """Get file size asynchronously"""
        try:
            stat = await aiofiles.os.stat(file_path)
            return stat.st_size
        except Exception as e:
            logger.error(f"Error getting file size {file_path}: {e}")
            raise
    
    @staticmethod
    async def delete_file(file_path: Union[str, Path]) -> None:
        """Delete file asynchronously"""
        try:
            await aiofiles.os.remove(file_path)
        except FileNotFoundError:
            logger.warning(f"File not found for deletion: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            raise
    
    @staticmethod
    async def copy_file(source: Union[str, Path], destination: Union[str, Path]) -> None:
        """Copy file asynchronously"""
        try:
            content = await AsyncFileService.read_text(source)
            await AsyncFileService.write_text(destination, content)
        except Exception as e:
            logger.error(f"Error copying file from {source} to {destination}: {e}")
            raise
    
    @staticmethod
    async def read_csv_dict(file_path: Union[str, Path], encoding: str = 'utf-8') -> List[Dict[str, str]]:
        """Read CSV file as list of dictionaries asynchronously"""
        try:
            content = await AsyncFileService.read_text(file_path, encoding)
            lines = content.split('\n')
            if not lines:
                return []
            
            # Use StringIO equivalent for async
            import io
            reader = csv.DictReader(io.StringIO(content))
            return list(reader)
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {e}")
            raise
    
    @staticmethod
    async def write_csv_dict(file_path: Union[str, Path], data: List[Dict[str, Any]], 
                           fieldnames: Optional[List[str]] = None, encoding: str = 'utf-8') -> None:
        """Write list of dictionaries to CSV file asynchronously"""
        try:
            if not data:
                await AsyncFileService.write_text(file_path, '', encoding)
                return
            
            if fieldnames is None:
                fieldnames = list(data[0].keys())
            
            import io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
            
            content = output.getvalue()
            await AsyncFileService.write_text(file_path, content, encoding)
        except Exception as e:
            logger.error(f"Error writing CSV file {file_path}: {e}")
            raise

# Example usage functions
async def load_synthetic_cases(file_path: str = "backend/data/synthetic/synthetic_clinical_cases.json") -> List[Dict[str, Any]]:
    """Load synthetic cases asynchronously"""
    try:
        data = await AsyncFileService.read_json(file_path)
        return data.get("cases", [])
    except FileNotFoundError:
        logger.warning(f"Synthetic cases file not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error loading synthetic cases: {e}")
        return []

async def save_analysis_result(case_id: str, analysis: Dict[str, Any], 
                             output_dir: str = "backend/data/analysis_results") -> None:
    """Save analysis result to file asynchronously"""
    try:
        file_path = Path(output_dir) / f"{case_id}_analysis.json"
        await AsyncFileService.write_json(file_path, analysis)
    except Exception as e:
        logger.error(f"Error saving analysis result for {case_id}: {e}")
        raise

async def log_user_activity(user_id: int, activity: str, 
                          log_file: str = "backend/logs/user_activity.log") -> None:
    """Log user activity asynchronously"""
    try:
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"{timestamp} - User {user_id}: {activity}\n"
        await AsyncFileService.append_text(log_file, log_entry)
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")
        # Don't raise, as logging errors shouldn't break the main flow