from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError
import asyncio

from .base import StorageAdapter
from ..models.error import ErrorLog

logger = logging.getLogger("laneswap")


class MongoDBAdapter(StorageAdapter):
    """MongoDB adapter for storing heartbeat and error data."""
    
    def __init__(
        self,
        connection_string: str,
        database_name: str = "laneswap",
        heartbeats_collection: str = "heartbeats",
        errors_collection: str = "errors"
    ):
        """
        Initialize the MongoDB adapter.
        
        Args:
            connection_string: MongoDB connection string (including credentials)
            database_name: Name of the database to use
            heartbeats_collection: Name of the collection for heartbeat data
            errors_collection: Name of the collection for error logs
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.heartbeats_collection = heartbeats_collection
        self.errors_collection = errors_collection
        self.client = None
        self.db = None
        self.heartbeats_collection_name = heartbeats_collection
        self.errors_collection_name = errors_collection
        self._initialized = False
        
    async def initialize(self) -> None:
        """
        Initialize the MongoDB connection.
        
        This method must be called before using any other methods.
        """
        if self._initialized:
            return
            
        try:
            # Import motor here to avoid dependency issues
            import motor.motor_asyncio
            
            # Create client
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                self.connection_string,
                maxPoolSize=10,
                minPoolSize=1,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000
            )
            
            # Get database and collections
            self.db = self.client[self.database_name]
            self.heartbeats_collection = self.db[self.heartbeats_collection_name]
            self.errors_collection = self.db[self.errors_collection_name]
            
            # Create indexes
            await self.heartbeats_collection.create_index("id", unique=True)
            await self.errors_collection.create_index("service_id")
            await self.errors_collection.create_index("timestamp")
            
            self._initialized = True
            logger.info(f"MongoDB adapter initialized: {self.database_name}")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB adapter: {str(e)}")
            raise
    
    async def close(self) -> None:
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.heartbeats_collection = None
            self.errors_collection = None
            self._initialized = False
            logger.info("MongoDB connection closed")
    
    async def _ensure_initialized(self) -> None:
        """Ensure the adapter is initialized."""
        if not self._initialized:
            await self.initialize()

    async def connect(self):
        """Establish connection to MongoDB with retry logic."""
        if self.client:
            logger.debug("MongoDB client already exists, reusing")
            return True
        
        # Mask sensitive connection string details
        masked_connection = self._mask_connection_string(self.connection_string)
        logger.info(f"Connecting to MongoDB: {masked_connection}")
        
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(1, max_retries + 1):
            try:
                # Add connection pooling settings
                self.client = AsyncIOMotorClient(
                    self.connection_string,
                    maxPoolSize=10,
                    minPoolSize=1,
                    maxIdleTimeMS=30000,
                    serverSelectionTimeoutMS=5000
                )
                
                # Test the connection
                self.db = self.client[self.database_name]
                await self.db.command("ping")
                logger.info(f"MongoDB connection established (attempt {attempt})")
                return True
            except PyMongoError as e:
                if attempt == max_retries:
                    logger.error(f"Failed to connect to MongoDB after {max_retries} attempts: {str(e)}")
                    raise
                else:
                    logger.warning(f"MongoDB connection attempt {attempt} failed: {str(e)}. Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                
    async def store_heartbeat(self, service_id: str, heartbeat_data: Dict[str, Any]) -> bool:
        """
        Store heartbeat data in MongoDB.
        
        Args:
            service_id: Service identifier
            heartbeat_data: Heartbeat information to store
            
        Returns:
            bool: True if data was stored successfully
        """
        await self._ensure_initialized()
        
        try:
            # Convert datetime objects to strings for MongoDB
            heartbeat_data_copy = self._prepare_for_mongodb(heartbeat_data)
            
            # Ensure ID is set
            heartbeat_data_copy["id"] = service_id
            
            # Upsert the document
            result = await self.heartbeats_collection.replace_one(
                {"id": service_id},
                heartbeat_data_copy,
                upsert=True
            )
            
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error storing heartbeat: {str(e)}")
            return False
            
    async def get_heartbeat(self, service_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve heartbeat data from MongoDB.
        
        Args:
            service_id: Service identifier
            
        Returns:
            Optional[Dict[str, Any]]: Heartbeat data or None if not found
        """
        await self._ensure_initialized()
        
        try:
            result = await self.heartbeats_collection.find_one({"id": service_id})
            if result:
                # Convert MongoDB _id to string and remove it
                result = self._prepare_from_mongodb(result)
                return result
            return None
        except Exception as e:
            logger.error(f"Error retrieving heartbeat: {str(e)}")
            return None
            
    async def get_all_heartbeats(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve all heartbeat data from MongoDB.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping service IDs to heartbeat data
        """
        await self._ensure_initialized()
        
        try:
            result = {}
            async for doc in self.heartbeats_collection.find():
                # Convert MongoDB _id to string and remove it
                doc = self._prepare_from_mongodb(doc)
                service_id = doc.get("id")
                if service_id:
                    result[service_id] = doc
            return result
        except Exception as e:
            logger.error(f"Error retrieving all heartbeats: {str(e)}")
            return {}
            
    async def store_error(self, error_data: Dict[str, Any]) -> bool:
        """
        Store error information in MongoDB.
        
        Args:
            error_data: Error information to store
            
        Returns:
            bool: True if data was stored successfully
        """
        await self._ensure_initialized()
        
        try:
            # Convert datetime objects to strings for MongoDB
            error_data_copy = self._prepare_for_mongodb(error_data)
            
            # Ensure timestamp is set
            if "timestamp" not in error_data_copy:
                error_data_copy["timestamp"] = datetime.now()
            
            # Insert the document
            result = await self.errors_collection.insert_one(error_data_copy)
            
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error storing error: {str(e)}")
            return False
            
    async def get_errors(
        self,
        service_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve error logs from MongoDB.
        
        Args:
            service_id: Optional service identifier to filter by
            limit: Maximum number of errors to retrieve
            skip: Number of errors to skip (for pagination)
            
        Returns:
            List[Dict[str, Any]]: List of error logs
        """
        await self._ensure_initialized()
        
        try:
            # Build query
            query = {}
            if service_id:
                query["service_id"] = service_id
            
            # Execute query
            cursor = self.errors_collection.find(query)
            
            # Sort by timestamp descending
            cursor = cursor.sort("timestamp", -1)
            
            # Apply pagination
            cursor = cursor.skip(skip).limit(limit)
            
            # Convert results
            result = []
            async for doc in cursor:
                # Convert MongoDB _id to string and remove it
                doc = self._prepare_from_mongodb(doc)
                result.append(doc)
            
            return result
        except Exception as e:
            logger.error(f"Error retrieving errors: {str(e)}")
            return []
            
    def _prepare_for_mongodb(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare data for MongoDB storage by handling special types.
        
        Args:
            data: Data to prepare
            
        Returns:
            Dict[str, Any]: Prepared data
        """
        result = {}
        
        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = self._prepare_for_mongodb(value)
            elif isinstance(value, list):
                result[key] = [
                    self._prepare_for_mongodb(item) if isinstance(item, dict) else item
                    for item in value
                ]
            elif isinstance(value, datetime):
                # MongoDB can store datetime objects directly
                result[key] = value.isoformat()
            elif isinstance(value, (int, float, str, bool, type(None))):
                # These types are directly supported by MongoDB
                result[key] = value
            else:
                # Convert other types to string
                result[key] = str(value)
                
        return result

    def _prepare_from_mongodb(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare data from MongoDB for use.
        
        Args:
            data: Data to prepare
            
        Returns:
            Dict[str, Any]: Prepared data
        """
        # Create a deep copy to avoid modifying the original
        import copy
        result = copy.deepcopy(data)
        
        # Convert MongoDB _id to string and remove it
        if "_id" in result:
            result["_id"] = str(result["_id"])
            del result["_id"]
        
        # Convert string timestamps to datetime objects
        for key, value in result.items():
            if isinstance(value, str) and key in ["timestamp", "created_at", "updated_at", "last_heartbeat"]:
                try:
                    result[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    pass
            elif isinstance(value, dict):
                result[key] = self._prepare_from_mongodb(value)
            elif isinstance(value, list):
                result[key] = [
                    self._prepare_from_mongodb(item) if isinstance(item, dict) else item
                    for item in value
                ]
        
        return result

    async def disconnect(self):
        """Close MongoDB connection cleanly."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            logger.info("Disconnected from MongoDB")

    async def store_errors_bulk(self, error_logs: List[Dict[str, Any]]) -> bool:
        """
        Store multiple error logs in a single operation.
        
        Args:
            error_logs: List of error information to store
            
        Returns:
            bool: True if data was stored successfully
        """
        if not error_logs:
            return True
            
        if self.db is None:
            await self.connect()
            
        try:
            # Prepare all documents for MongoDB
            documents = []
            current_time = datetime.utcnow()
            
            for error in error_logs:
                data = self._prepare_for_mongodb(error)
                if "stored_at" not in data:
                    data["stored_at"] = current_time
                documents.append(data)
                
            result = await self.db[self.errors_collection].insert_many(documents)
            return result.acknowledged
        except PyMongoError as e:
            logger.error(f"Error storing bulk error logs in MongoDB: {str(e)}")
            return False

    async def health_check(self) -> bool:
        """
        Check if the MongoDB connection is healthy.
        
        Returns:
            bool: True if connection is healthy
        """
        if self.client is None:
            try:
                await self.connect()
            except Exception:
                return False
                
        try:
            # Run a simple command to check connection
            await self.db.command("ping")
            return True
        except PyMongoError as e:
            logger.error(f"MongoDB health check failed: {str(e)}")
            return False

    async def get_filtered_heartbeats(
        self, 
        filter_criteria: Dict[str, Any],
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve heartbeats matching specific criteria.
        
        Args:
            filter_criteria: MongoDB query filter
            limit: Maximum number of results
            skip: Number of results to skip
            
        Returns:
            List[Dict[str, Any]]: Filtered heartbeat data
        """
        if self.db is None:
            await self.connect()
            
        result = []
        try:
            cursor = self.db[self.heartbeats_collection].find(
                filter_criteria
            ).sort("last_seen", -1).skip(skip).limit(limit)
            
            async for document in cursor:
                document.pop("_id", None)
                result.append(document)
                
            return result
        except PyMongoError as e:
            logger.error(f"Error retrieving filtered heartbeats: {str(e)}")
            return []

    def _mask_connection_string(self, connection_string: str) -> str:
        """
        Mask sensitive information in MongoDB connection string.
        
        Args:
            connection_string: Original connection string
            
        Returns:
            str: Connection string with credentials masked
        """
        try:
            # Handle mongodb:// and mongodb+srv:// URLs
            if '@' in connection_string:
                # Split the connection string at '@' to separate credentials from host
                prefix, rest = connection_string.split('@', 1)
                protocol = prefix.split('://')[0] + '://'
                return f"{protocol}****@{rest}"
            return connection_string
        except Exception:
            return "mongodb://*****"