"""
Global configuration settings for LP_Crate modules.

This module provides centralized configuration for all LP_Crate scripts,
allowing easy adjustment of settings like file limits without modifying
multiple files.
"""

from typing import Optional

class GlobalConfig:
    """Global configuration class for LP_Crate operations."""
    
    # Default limit for file operations (e.g., how many example files to include)
    # Set to None for no limit, or an integer for a specific limit
    DEFAULT_FILE_LIMIT: Optional[int] = 2
    
    @classmethod
    def get_file_limit(cls) -> Optional[int]:
        """Get the current file limit setting."""
        return cls.DEFAULT_FILE_LIMIT
    
    @classmethod
    def set_file_limit(cls, limit: Optional[int]) -> None:
        """Set the file limit setting.
        
        Args:
            limit: Maximum number of files to process, or None for no limit
        """
        cls.DEFAULT_FILE_LIMIT = limit

# Convenience function for quick access
def get_file_limit() -> Optional[int]:
    """Get the current global file limit setting."""
    return GlobalConfig.get_file_limit()

def set_file_limit(limit: Optional[int]) -> None:
    """Set the global file limit setting.
    
    Args:
        limit: Maximum number of files to process, or None for no limit
    """
    GlobalConfig.set_file_limit(limit)
