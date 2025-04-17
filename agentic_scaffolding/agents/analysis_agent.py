"""
Analysis agent implementation.
"""
from typing import Dict, Any, List, Optional
import logging

from .llm_agent import LLMAgent

logger = logging.getLogger(__name__)

class AnalysisAgent(LLMAgent):
    """
    Agent specialized in data analysis and interpretation.
    """
    
    def __init__(self, agent_id: str, name: str, description: str, llm_client):
        """
        Initialize an analysis agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            description: Detailed description of the agent's purpose and capabilities
            llm_client: Client for interacting with the LLM
        """
        capabilities = ["data_analysis", "pattern_recognition", "insight_generation", "critical_thinking"]
        system_prompt = """
        You are a highly skilled analysis agent. Your primary capabilities include:
        
        1. Analyzing data and information to identify patterns, trends, and insights
        2. Evaluating evidence and arguments critically
        3. Drawing logical conclusions based on available information
        4. Identifying gaps in information and potential biases
        5. Generating actionable insights and recommendations
        
        When given an analysis task, you should:
        1. Understand the specific analysis needs
        2. Examine the provided information carefully
        3. Apply appropriate analytical frameworks and methods
        4. Identify key patterns, relationships, and insights
        5. Present your findings clearly, with supporting evidence
        
        Always strive for objectivity, logical rigor, and clarity in your analysis.
        """
        
        super().__init__(agent_id, name, description, capabilities, llm_client, system_prompt)
        
    async def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an analysis task.
        
        Args:
            input_data: The input data for the agent to process
            context: Contextual information that might be relevant for processing
            
        Returns:
            Dict containing the analysis results
        """
        # Extract the data to analyze
        data_to_analyze = None
        if "task" in input_data and "data" in input_data["task"]:
            data_to_analyze = input_data["task"]["data"]
        elif "data" in input_data:
            data_to_analyze = input_data["data"]
        elif "research_results" in input_data:
            data_to_analyze = input_data["research_results"]
            
        if not data_to_analyze:
            return {
                "status": "error",
                "error": "No data provided for analysis"
            }
            
        # Process with the LLM
        llm_result = await super().process(input_data, context)
        
        # Add metadata about the analysis process
        if llm_result["status"] == "success":
            llm_result["metadata"] = {
                "analysis_type": input_data.get("analysis_type", "general"),
                "data_points": len(data_to_analyze) if isinstance(data_to_analyze, list) else "unknown"
            }
            
        return llm_result
