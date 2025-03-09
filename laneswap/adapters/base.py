from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class NotifierAdapter(ABC):
    """Base class for notification adapters."""
    
    @abstractmethod
    async def send_notification(
        self,
        title: str,
        message: str,
        service_info: Optional[Dict[str, Any]] = None,
        level: str = "info"
    ) -> bool:
        """
        Send a notification.
        
        Args:
            title: Notification title
            message: Message body
            service_info: Additional service information
            level: Notification level (info, warning, error)
            
        Returns:
            bool: True if notification was sent successfully
        """
        pass


class StorageAdapter(ABC):
    """Base class for storage adapters."""
    
    @abstractmethod
    async def store_heartbeat(
        self,
        service_id: str,
        heartbeat_data: Dict[str, Any]
    ) -> bool:
        """
        Store heartbeat data.
        
        Args:
            service_id: Service identifier
            heartbeat_data: Heartbeat information to store
            
        Returns:
            bool: True if data was stored successfully
        """
        pass
    
    @abstractmethod
    async def get_heartbeat(self, service_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve heartbeat data.
        
        Args:
            service_id: Service identifier
            
        Returns:
            Optional[Dict[str, Any]]: Heartbeat data or None if not found
        """
        pass
    
    @abstractmethod
    async def get_all_heartbeats(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve all heartbeat data.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping service IDs to heartbeat data
        """
        pass
    
    @abstractmethod
    async def store_error(self, error_data: Dict[str, Any]) -> bool:
        """
        Store error information.
        
        Args:
            error_data: Error information to store
            
        Returns:
            bool: True if data was stored successfully
        """
        pass
    
    @abstractmethod
    async def get_errors(
        self,
        service_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve error logs.
        
        Args:
            service_id: Optional service identifier to filter by
            limit: Maximum number of errors to retrieve
            skip: Number of errors to skip (for pagination)
            
        Returns:
            List[Dict[str, Any]]: List of error logs
        """
        pass