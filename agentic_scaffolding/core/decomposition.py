"""
Task decomposition strategies for the Agentic Scaffolding framework.
"""
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

class TaskDecomposer(ABC):
    """
    Abstract base class for task decomposition strategies.
    """
    
    @abstractmethod
    async def decompose(self, goal: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Decompose a high-level goal into subtasks.
        
        Args:
            goal: The high-level goal to decompose
            context: Additional context that might be relevant for decomposition
            
        Returns:
            List of subtasks, each represented as a dictionary
        """
        pass


class LLMTaskDecomposer(TaskDecomposer):
    """
    Task decomposer that uses a Large Language Model to break down goals.
    """
    
    def __init__(self, llm_client):
        """
        Initialize the LLM-based task decomposer.
        
        Args:
            llm_client: Client for interacting with the LLM
        """
        self.llm_client = llm_client
        
    async def decompose(self, goal: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Use an LLM to decompose a high-level goal into subtasks.
        
        Args:
            goal: The high-level goal to decompose
            context: Additional context that might be relevant for decomposition
            
        Returns:
            List of subtasks, each represented as a dictionary
        """
        # Construct the prompt for the LLM
        prompt = self._construct_decomposition_prompt(goal, context)
        
        # Get the LLM response
        response = await self.llm_client.generate(prompt)
        
        # Parse the response into a list of subtasks
        subtasks = self._parse_decomposition_response(response)
        
        return subtasks
    
    def _construct_decomposition_prompt(self, goal: str, context: Dict[str, Any]) -> str:
        """
        Construct a prompt for the LLM to decompose the goal.
        
        Args:
            goal: The high-level goal to decompose
            context: Additional context that might be relevant for decomposition
            
        Returns:
            Prompt string for the LLM
        """
        prompt = f"""
        You are an expert in task decomposition. Your job is to break down complex goals into smaller, 
        manageable subtasks that can be executed by specialized agents.
        
        Goal: {goal}
        
        Additional Context:
        """
        
        for key, value in context.items():
            prompt += f"\n{key}: {value}"
            
        prompt += """
        
        Break down this goal into a list of subtasks. For each subtask, provide:
        1. A descriptive title
        2. A detailed description of what needs to be done
        3. Any dependencies on other subtasks (by title)
        4. Required capabilities or skills needed to complete this subtask
        
        Format your response as a JSON array of subtask objects.
        """
        
        return prompt
    
    def _parse_decomposition_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse the LLM response into a structured list of subtasks.
        
        Args:
            response: The raw response from the LLM
            
        Returns:
            List of subtasks, each represented as a dictionary
        """
        # In a real implementation, this would parse the JSON response
        # For this demo, we'll return a simplified structure
        import json
        try:
            # Try to parse as JSON
            subtasks = json.loads(response)
            return subtasks
        except json.JSONDecodeError:
            # Fallback to a simple parsing approach
            # This is a simplified implementation
            lines = response.strip().split('\n')
            subtasks = []
            current_task = {}
            
            for line in lines:
                if line.startswith("Subtask"):
                    if current_task:
                        subtasks.append(current_task)
                    current_task = {"title": line.strip()}
                elif ":" in line and current_task:
                    key, value = line.split(":", 1)
                    current_task[key.strip().lower()] = value.strip()
            
            if current_task:
                subtasks.append(current_task)
                
            return subtasks
