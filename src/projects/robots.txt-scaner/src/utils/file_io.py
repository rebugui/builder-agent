"""
File I/O Utilities Module

Handles file reading and writing operations.
"""

import asyncio
from pathlib import Path
from typing import List, Union
import aiofiles


async def read_file_async(filepath: Union[str, Path]) -> str:
    """
    Asynchronously read file content.
    
    Args:
        filepath: Path to the file.
        
    Returns:
        File content as string.
        
    Raises:
        FileNotFoundError: If file doesn't exist.
        PermissionError: If file is not readable.
    """
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    if not path.is_file():
        raise ValueError(f"Path is not a file: {filepath}")
    
    async with aiofiles.open(path, mode='r', encoding='utf-8') as f:
        return await f.read()


async def write_file_async(
    filepath: Union[str, Path],
    content: str
) -> None:
    """
    Asynchronously write content to file.
    
    Args:
        filepath: Path to the file.
        content: Content to write.
        
    Raises:
        PermissionError: If file is not writable.
    """
    path = Path(filepath)
    
    # Create parent directories if needed
    path.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiofiles.open(path, mode='w', encoding='utf-8') as f:
        await f.write(content)


def read_lines_from_file(filepath: Union[str, Path]) -> List[str]:
    """
    Read non-empty lines from a file.
    
    Args:
        filepath: Path to the file.
        
    Returns:
        List of non-empty lines.
    """
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]
