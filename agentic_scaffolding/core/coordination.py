"""
Dynamic coordination and control mechanisms for the Agentic Scaffolding framework.
"""
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
import asyncio
import logging

logger = logging.getLogger(__name__)

class TaskAllocator(ABC):
    """
    Abstract base class for task allocation mechanisms.
    """
    
    @abstractmethod
    async def allocate(self, tasks: List[Dict[str, Any]], available_agents: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Allocate tasks to agents.
        
        Args:
            tasks: List of tasks to allocate
            available_agents: List of available agents with their capabilities
            
        Returns:
            Dictionary mapping agent IDs to lists of allocated task IDs
        """
        pass


class CapabilityBasedAllocator(TaskAllocator):
    """
    Task allocator that matches tasks to agents based on required capabilities.
    """
    
    async def allocate(self, tasks: List[Dict[str, Any]], available_agents: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Allocate tasks to agents based on capability matching.
        
        Args:
            tasks: List of tasks to allocate
            available_agents: List of available agents with their capabilities
            
        Returns:
            Dictionary mapping agent IDs to lists of allocated task IDs
        """
        allocations = {}
        
        # Create a capability index for faster lookup
        capability_index = {}
        for agent in available_agents:
            agent_id = agent["agent_id"]
            for capability in agent.get("capabilities", []):
                if capability not in capability_index:
                    capability_index[capability] = []
                capability_index[capability].append(agent_id)
        
        # Allocate tasks based on required capabilities
        for task in tasks:
            task_id = task["task_id"]
            required_capabilities = task.get("required_capabilities", [])
            
            # Find agents that have all required capabilities
            candidate_agents = set()
            if required_capabilities:
                # Start with agents that have the first capability
                if required_capabilities[0] in capability_index:
                    candidate_agents = set(capability_index[required_capabilities[0]])
                
                # Filter by remaining capabilities
                for capability in required_capabilities[1:]:
                    if capability in capability_index:
                        candidate_agents &= set(capability_index[capability])
                    else:
                        # No agents have this capability
                        candidate_agents = set()
                        break
            else:
                # If no specific capabilities required, consider all agents
                candidate_agents = {agent["agent_id"] for agent in available_agents}
            
            # Allocate to the first available agent with matching capabilities
            # In a real system, this would use a more sophisticated algorithm
            if candidate_agents:
                selected_agent_id = next(iter(candidate_agents))
                if selected_agent_id not in allocations:
                    allocations[selected_agent_id] = []
                allocations[selected_agent_id].append(task_id)
            else:
                logger.warning(f"No suitable agent found for task {task_id} requiring capabilities {required_capabilities}")
        
        return allocations


class ProgressMonitor:
    """
    Monitor for tracking task progress and agent status.
    """
    
    def __init__(self):
        """
        Initialize the progress monitor.
        """
        self.task_status = {}
        self.agent_status = {}
        self.callbacks = {}
        
    def register_task(self, task_id: str, metadata: Dict[str, Any]) -> None:
        """
        Register a task for monitoring.
        
        Args:
            task_id: Unique identifier for the task
            metadata: Task metadata
        """
        self.task_status[task_id] = {
            "status": "pending",
            "progress": 0.0,
            "metadata": metadata,
            "start_time": None,
            "end_time": None,
            "assigned_agent": None,
            "result": None,
            "errors": []
        }
        
    def register_agent(self, agent_id: str, metadata: Dict[str, Any]) -> None:
        """
        Register an agent for monitoring.
        
        Args:
            agent_id: Unique identifier for the agent
            metadata: Agent metadata
        """
        self.agent_status[agent_id] = {
            "status": "idle",
            "current_tasks": [],
            "completed_tasks": [],
            "metadata": metadata,
            "last_update": None,
            "performance_metrics": {}
        }
        
    def update_task_status(self, task_id: str, updates: Dict[str, Any]) -> None:
        """
        Update the status of a task.
        
        Args:
            task_id: Unique identifier for the task
            updates: Dictionary of status updates
        """
        if task_id in self.task_status:
            self.task_status[task_id].update(updates)
            
            # Trigger any registered callbacks for this task
            if task_id in self.callbacks:
                for callback in self.callbacks[task_id]:
                    asyncio.create_task(callback(self.task_status[task_id]))
        else:
            logger.warning(f"Attempted to update unknown task: {task_id}")
            
    def update_agent_status(self, agent_id: str, updates: Dict[str, Any]) -> None:
        """
        Update the status of an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            updates: Dictionary of status updates
        """
        if agent_id in self.agent_status:
            self.agent_status[agent_id].update(updates)
        else:
            logger.warning(f"Attempted to update unknown agent: {agent_id}")
            
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a task.
        
        Args:
            task_id: Unique identifier for the task
            
        Returns:
            Dictionary containing the task status, or None if the task is not found
        """
        return self.task_status.get(task_id)
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Dictionary containing the agent status, or None if the agent is not found
        """
        return self.agent_status.get(agent_id)
    
    def get_all_task_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the current status of all tasks.
        
        Returns:
            Dictionary mapping task IDs to their status dictionaries
        """
        return self.task_status.copy()
    
    def get_all_agent_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the current status of all agents.
        
        Returns:
            Dictionary mapping agent IDs to their status dictionaries
        """
        return self.agent_status.copy()
    
    def register_task_callback(self, task_id: str, callback: Callable) -> None:
        """
        Register a callback function to be called when a task's status is updated.
        
        Args:
            task_id: Unique identifier for the task
            callback: Async callback function that takes the task status dictionary as an argument
        """
        if task_id not in self.callbacks:
            self.callbacks[task_id] = []
        self.callbacks[task_id].append(callback)
        
    def unregister_task_callback(self, task_id: str, callback: Callable) -> None:
        """
        Unregister a previously registered callback function.
        
        Args:
            task_id: Unique identifier for the task
            callback: The callback function to unregister
        """
        if task_id in self.callbacks and callback in self.callbacks[task_id]:
            self.callbacks[task_id].remove(callback)
