"""
Resource management within the Agentic Scaffolding framework.
"""
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class ResourceRegistry(ABC):
    """
    Abstract base class for resource registries.
    """
    
    @abstractmethod
    def register(self, resource_id: str, metadata: Dict[str, Any]) -> None:
        """
        Register a resource in the registry.
        
        Args:
            resource_id: Unique identifier for the resource
            metadata: Resource metadata
        """
        pass
    
    @abstractmethod
    def unregister(self, resource_id: str) -> None:
        """
        Unregister a resource from the registry.
        
        Args:
            resource_id: Unique identifier for the resource
        """
        pass
    
    @abstractmethod
    def get(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a resource by its ID.
        
        Args:
            resource_id: Unique identifier for the resource
            
        Returns:
            Resource metadata, or None if not found
        """
        pass
    
    @abstractmethod
    def query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query for resources matching certain criteria.
        
        Args:
            query: Query parameters
            
        Returns:
            List of matching resources
        """
        pass


class InMemoryResourceRegistry(ResourceRegistry):
    """
    Simple in-memory implementation of a resource registry.
    """
    
    def __init__(self):
        """
        Initialize the in-memory resource registry.
        """
        self.resources = {}
        
    def register(self, resource_id: str, metadata: Dict[str, Any]) -> None:
        """
        Register a resource in the registry.
        
        Args:
            resource_id: Unique identifier for the resource
            metadata: Resource metadata
        """
        self.resources[resource_id] = metadata
        logger.info(f"Registered resource: {resource_id}")
        
    def unregister(self, resource_id: str) -> None:
        """
        Unregister a resource from the registry.
        
        Args:
            resource_id: Unique identifier for the resource
        """
        if resource_id in self.resources:
            del self.resources[resource_id]
            logger.info(f"Unregistered resource: {resource_id}")
        else:
            logger.warning(f"Attempted to unregister unknown resource: {resource_id}")
            
    def get(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a resource by its ID.
        
        Args:
            resource_id: Unique identifier for the resource
            
        Returns:
            Resource metadata, or None if not found
        """
        return self.resources.get(resource_id)
    
    def query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query for resources matching certain criteria.
        
        Args:
            query: Query parameters
            
        Returns:
            List of matching resources
        """
        results = []
        
        for resource_id, metadata in self.resources.items():
            match = True
            
            for key, value in query.items():
                if key not in metadata or metadata[key] != value:
                    match = False
                    break
                    
            if match:
                results.append({
                    "resource_id": resource_id,
                    **metadata
                })
                
        return results


class AgentRegistry(InMemoryResourceRegistry):
    """
    Registry for agent resources.
    """
    
    def register_agent(self, agent_id: str, name: str, description: str, capabilities: List[str], 
                      additional_metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Register an agent in the registry.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            description: Detailed description of the agent's purpose and capabilities
            capabilities: List of capabilities this agent possesses
            additional_metadata: Any additional metadata to store
        """
        metadata = {
            "type": "agent",
            "name": name,
            "description": description,
            "capabilities": capabilities,
            "status": "available"
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
            
        self.register(agent_id, metadata)
        
    def query_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """
        Query for agents that have a specific capability.
        
        Args:
            capability: The capability to search for
            
        Returns:
            List of matching agents
        """
        results = []
        
        for agent_id, metadata in self.resources.items():
            if metadata.get("type") == "agent" and capability in metadata.get("capabilities", []):
                results.append({
                    "agent_id": agent_id,
                    **metadata
                })
                
        return results


class ToolRegistry(InMemoryResourceRegistry):
    """
    Registry for tool resources.
    """
    
    def register_tool(self, tool_id: str, name: str, description: str, input_schema: Dict[str, Any],
                     output_schema: Dict[str, Any], additional_metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Register a tool in the registry.
        
        Args:
            tool_id: Unique identifier for the tool
            name: Human-readable name for the tool
            description: Detailed description of the tool's purpose and functionality
            input_schema: Schema describing the expected input format
            output_schema: Schema describing the output format
            additional_metadata: Any additional metadata to store
        """
        metadata = {
            "type": "tool",
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "output_schema": output_schema
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
            
        self.register(tool_id, metadata)


class KnowledgeSourceRegistry(InMemoryResourceRegistry):
    """
    Registry for knowledge source resources.
    """
    
    def register_knowledge_source(self, source_id: str, name: str, description: str, source_type: str,
                                 access_info: Dict[str, Any], additional_metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Register a knowledge source in the registry.
        
        Args:
            source_id: Unique identifier for the knowledge source
            name: Human-readable name for the knowledge source
            description: Detailed description of the knowledge source
            source_type: Type of knowledge source (e.g., "database", "vector_store", "api")
            access_info: Information needed to access the knowledge source
            additional_metadata: Any additional metadata to store
        """
        metadata = {
            "type": "knowledge_source",
            "name": name,
            "description": description,
            "source_type": source_type,
            "access_info": access_info
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
            
        self.register(source_id, metadata)
