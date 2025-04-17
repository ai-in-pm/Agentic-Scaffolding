"""
Base Agent class for the Agentic Scaffolding framework.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class Agent(ABC):
    """
    Abstract base class for all agents in the Agentic Scaffolding framework.
    """
    def __init__(self, agent_id: str, name: str, description: str, capabilities: List[str]):
        """
        Initialize an agent with basic metadata.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            description: Detailed description of the agent's purpose and capabilities
            capabilities: List of capabilities this agent possesses
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.state = {}
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and return results.
        
        Args:
            input_data: The input data for the agent to process
            context: Contextual information that might be relevant for processing
            
        Returns:
            Dict containing the processing results
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get agent metadata for registration and discovery.
        
        Returns:
            Dict containing agent metadata
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities
        }
    
    def update_state(self, state_updates: Dict[str, Any]) -> None:
        """
        Update the agent's internal state.
        
        Args:
            state_updates: Dictionary of state variables to update
        """
        self.state.update(state_updates)
        
    def get_state(self) -> Dict[str, Any]:
        """
        Get the agent's current state.
        
        Returns:
            Dict containing the agent's current state
        """
        return self.state.copy()
