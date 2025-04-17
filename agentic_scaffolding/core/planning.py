"""
Planning and sequencing algorithms for the Agentic Scaffolding framework.
"""
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod

class Planner(ABC):
    """
    Abstract base class for planning algorithms.
    """
    
    @abstractmethod
    async def create_plan(self, subtasks: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a plan from a list of subtasks.
        
        Args:
            subtasks: List of subtasks to plan
            context: Additional context that might be relevant for planning
            
        Returns:
            A plan dictionary containing the execution sequence and other metadata
        """
        pass


class LLMPlanner(Planner):
    """
    Planner that uses a Large Language Model to create execution plans.
    """
    
    def __init__(self, llm_client):
        """
        Initialize the LLM-based planner.
        
        Args:
            llm_client: Client for interacting with the LLM
        """
        self.llm_client = llm_client
        
    async def create_plan(self, subtasks: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use an LLM to create a plan from a list of subtasks.
        
        Args:
            subtasks: List of subtasks to plan
            context: Additional context that might be relevant for planning
            
        Returns:
            A plan dictionary containing the execution sequence and other metadata
        """
        # Construct the prompt for the LLM
        prompt = self._construct_planning_prompt(subtasks, context)
        
        # Get the LLM response
        response = await self.llm_client.generate(prompt)
        
        # Parse the response into a plan
        plan = self._parse_planning_response(response, subtasks)
        
        return plan
    
    def _construct_planning_prompt(self, subtasks: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        """
        Construct a prompt for the LLM to create a plan.
        
        Args:
            subtasks: List of subtasks to plan
            context: Additional context that might be relevant for planning
            
        Returns:
            Prompt string for the LLM
        """
        prompt = f"""
        You are an expert in planning and sequencing tasks. Your job is to create an optimal execution plan
        for a set of subtasks, considering their dependencies and requirements.
        
        Subtasks:
        """
        
        for i, task in enumerate(subtasks):
            prompt += f"\n{i+1}. {task['title']}"
            if 'description' in task:
                prompt += f"\n   Description: {task['description']}"
            if 'dependencies' in task:
                prompt += f"\n   Dependencies: {task['dependencies']}"
            if 'required_capabilities' in task:
                prompt += f"\n   Required Capabilities: {task['required_capabilities']}"
            
        prompt += """
        
        Additional Context:
        """
        
        for key, value in context.items():
            prompt += f"\n{key}: {value}"
            
        prompt += """
        
        Create an execution plan for these subtasks. For each step in the plan, specify:
        1. Which subtask(s) should be executed
        2. Whether they can be executed in parallel or must be sequential
        3. Any conditions that must be met before execution
        4. Expected outcomes or success criteria
        
        Format your response as a JSON object with an ordered list of execution steps.
        """
        
        return prompt
    
    def _parse_planning_response(self, response: str, subtasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse the LLM response into a structured plan.
        
        Args:
            response: The raw response from the LLM
            subtasks: The original list of subtasks
            
        Returns:
            A plan dictionary containing the execution sequence and other metadata
        """
        # In a real implementation, this would parse the JSON response
        # For this demo, we'll return a simplified structure
        import json
        try:
            # Try to parse as JSON
            plan_data = json.loads(response)
            return {
                "steps": plan_data.get("steps", []),
                "metadata": {
                    "estimated_duration": plan_data.get("estimated_duration", "unknown"),
                    "parallel_execution": plan_data.get("parallel_execution", False)
                }
            }
        except json.JSONDecodeError:
            # Fallback to a simple parsing approach
            # This is a simplified implementation
            lines = response.strip().split('\n')
            steps = []
            current_step = {}
            
            for line in lines:
                if line.startswith("Step"):
                    if current_step:
                        steps.append(current_step)
                    current_step = {"name": line.strip()}
                elif ":" in line and current_step:
                    key, value = line.split(":", 1)
                    current_step[key.strip().lower()] = value.strip()
            
            if current_step:
                steps.append(current_step)
                
            return {
                "steps": steps,
                "metadata": {
                    "estimated_duration": "unknown",
                    "parallel_execution": False
                }
            }
