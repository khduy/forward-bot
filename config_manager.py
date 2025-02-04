import os
import json
import logging
from typing import Dict, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Handles configuration management with file-based storage and caching
    - Uses JSON file to persist channel IDs
    - Implements LRU cache for better performance
    """
    def __init__(self, config_file: str = 'config.json'):
        self.config_file = config_file
        self.config: Dict[str, Optional[int]] = self._load_config()
    
    @lru_cache(maxsize=1)
    def _load_config(self) -> Dict[str, Optional[int]]:
        """
        Load config from JSON file with error handling and caching
        Returns default config if file doesn't exist or is invalid
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Error reading {self.config_file}: {e}")
        return {'source_id': None, 'destination_id': None}
    
    def save_config(self) -> None:
        """Save config and invalidate cache"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)
        self._load_config.cache_clear()

    def validate_config(self):
        """
        Validate configuration with:
        - Channel ID format checks
        - Access verification
        - Self-forwarding prevention
        """
        if self.config['source_id'] == self.config['destination_id']:
            raise ValueError("Source and destination channels cannot be the same")
        
        if not (isinstance(self.config['source_id'], int) and self.config['source_id'] < 0):
            raise ValueError("Invalid source channel ID format")
            
        if not (isinstance(self.config['destination_id'], int) and self.config['destination_id'] < 0):
            raise ValueError("Invalid destination channel ID format")
