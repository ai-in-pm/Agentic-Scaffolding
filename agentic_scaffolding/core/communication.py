"""
Communication and interfaces for the Agentic Scaffolding framework.
"""
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
import asyncio
import logging
import uuid
import json

logger = logging.getLogger(__name__)

class Message:
    """
    Represents a message exchanged between agents or components.
    """
    
    def __init__(self, sender_id: str, receiver_id: str, content: Dict[str, Any], 
                message_type: str, conversation_id: Optional[str] = None):
        """
        Initialize a message.
        
        Args:
            sender_id: ID of the sender
            receiver_id: ID of the receiver
            content: Message content
            message_type: Type of message (e.g., "request", "response", "notification")
            conversation_id: ID of the conversation this message belongs to
        """
        self.message_id = str(uuid.uuid4())
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.content = content
        self.message_type = message_type
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.timestamp = asyncio.get_event_loop().time()
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "message_type": self.message_type,
            "conversation_id": self.conversation_id,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create a message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            Message object
        """
        message = cls(
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            content=data["content"],
            message_type=data["message_type"],
            conversation_id=data.get("conversation_id")
        )
        message.message_id = data["message_id"]
        message.timestamp = data["timestamp"]
        return message


class MessageBroker(ABC):
    """
    Abstract base class for message brokers.
    """
    
    @abstractmethod
    async def publish(self, message: Message) -> None:
        """
        Publish a message.
        
        Args:
            message: The message to publish
        """
        pass
    
    @abstractmethod
    async def subscribe(self, subscriber_id: str, callback: Callable[[Message], None]) -> None:
        """
        Subscribe to messages.
        
        Args:
            subscriber_id: ID of the subscriber
            callback: Callback function to be called when a message is received
        """
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscriber_id: str) -> None:
        """
        Unsubscribe from messages.
        
        Args:
            subscriber_id: ID of the subscriber
        """
        pass


class InMemoryMessageBroker(MessageBroker):
    """
    Simple in-memory implementation of a message broker.
    """
    
    def __init__(self):
        """
        Initialize the in-memory message broker.
        """
        self.subscribers = {}
        self.message_history = []
        
    async def publish(self, message: Message) -> None:
        """
        Publish a message.
        
        Args:
            message: The message to publish
        """
        # Store the message in history
        self.message_history.append(message)
        
        # Deliver to the specific receiver if they are subscribed
        if message.receiver_id in self.subscribers:
            for callback in self.subscribers[message.receiver_id]:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"Error in subscriber callback: {e}")
        
        # Also deliver to any subscribers listening for all messages
        if "*" in self.subscribers:
            for callback in self.subscribers["*"]:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"Error in wildcard subscriber callback: {e}")
                    
        logger.debug(f"Published message: {message.message_id} from {message.sender_id} to {message.receiver_id}")
        
    async def subscribe(self, subscriber_id: str, callback: Callable[[Message], None]) -> None:
        """
        Subscribe to messages.
        
        Args:
            subscriber_id: ID of the subscriber
            callback: Callback function to be called when a message is received
        """
        if subscriber_id not in self.subscribers:
            self.subscribers[subscriber_id] = []
            
        self.subscribers[subscriber_id].append(callback)
        logger.debug(f"Subscribed: {subscriber_id}")
        
    async def unsubscribe(self, subscriber_id: str) -> None:
        """
        Unsubscribe from messages.
        
        Args:
            subscriber_id: ID of the subscriber
        """
        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]
            logger.debug(f"Unsubscribed: {subscriber_id}")
            
    def get_message_history(self, conversation_id: Optional[str] = None) -> List[Message]:
        """
        Get the message history.
        
        Args:
            conversation_id: Optional ID of the conversation to filter by
            
        Returns:
            List of messages
        """
        if conversation_id:
            return [msg for msg in self.message_history if msg.conversation_id == conversation_id]
        else:
            return self.message_history.copy()


class SharedContext:
    """
    Shared context for agents to store and retrieve information.
    """
    
    def __init__(self):
        """
        Initialize the shared context.
        """
        self.data = {}
        self.locks = {}
        
    async def set(self, key: str, value: Any) -> None:
        """
        Set a value in the shared context.
        
        Args:
            key: The key to store the value under
            value: The value to store
        """
        # Create a lock for this key if it doesn't exist
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()
            
        # Acquire the lock before updating
        async with self.locks[key]:
            self.data[key] = value
            
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the shared context.
        
        Args:
            key: The key to retrieve
            default: Default value to return if the key is not found
            
        Returns:
            The stored value, or the default if not found
        """
        return self.data.get(key, default)
    
    async def delete(self, key: str) -> None:
        """
        Delete a value from the shared context.
        
        Args:
            key: The key to delete
        """
        if key in self.data:
            # Create a lock for this key if it doesn't exist
            if key not in self.locks:
                self.locks[key] = asyncio.Lock()
                
            # Acquire the lock before deleting
            async with self.locks[key]:
                del self.data[key]
                
    async def get_all(self) -> Dict[str, Any]:
        """
        Get all values from the shared context.
        
        Returns:
            Dictionary of all stored values
        """
        return self.data.copy()
