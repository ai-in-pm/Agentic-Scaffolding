"""
LLM-based agent implementation.
"""
from typing import Dict, Any, List, Optional
import logging

from ..core.agent import Agent

logger = logging.getLogger(__name__)

class LLMAgent(Agent):
    """
    Agent that uses a Large Language Model for processing.
    """
    
    def __init__(self, agent_id: str, name: str, description: str, capabilities: List[str], 
                llm_client, system_prompt: str):
        """
        Initialize an LLM-based agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            description: Detailed description of the agent's purpose and capabilities
            capabilities: List of capabilities this agent possesses
            llm_client: Client for interacting with the LLM
            system_prompt: System prompt to use for the LLM
        """
        super().__init__(agent_id, name, description, capabilities)
        self.llm_client = llm_client
        self.system_prompt = system_prompt
        
    async def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data using the LLM.
        
        Args:
            input_data: The input data for the agent to process
            context: Contextual information that might be relevant for processing
            
        Returns:
            Dict containing the processing results
        """
        # Construct the prompt for the LLM
        prompt = self._construct_prompt(input_data, context)
        
        # Get the LLM response
        try:
            response = await self.llm_client.generate(prompt)
            
            # Parse the response
            result = self._parse_response(response)
            
            return {
                "status": "success",
                "result": result
            }
        except Exception as e:
            logger.error(f"Error in LLM processing: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _construct_prompt(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Construct a prompt for the LLM based on input data and context.
        
        Args:
            input_data: The input data for the agent to process
            context: Contextual information that might be relevant for processing
            
        Returns:
            Prompt string for the LLM
        """
        # Start with the system prompt
        prompt = self.system_prompt + "\n\n"
        
        # Add task information if available
        if "task" in input_data:
            task = input_data["task"]
            prompt += f"Task: {task.get('title', 'Untitled task')}\n"
            if "description" in task:
                prompt += f"Description: {task['description']}\n"
                
        # Add any other relevant input data
        for key, value in input_data.items():
            if key != "task" and not isinstance(value, dict) and not isinstance(value, list):
                prompt += f"{key}: {value}\n"
                
        # Add a final instruction
        prompt += "\nPlease process this information and provide your response."
        
        return prompt
    
    def _parse_response(self, response: str) -> Any:
        """
        Parse the LLM response.
        
        Args:
            response: The raw response from the LLM
            
        Returns:
            Parsed response
        """
        # In a real implementation, this would parse the response based on the expected format
        # For this demo, we'll just return the raw response
        return response
