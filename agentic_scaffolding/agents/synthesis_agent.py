"""
Synthesis agent implementation.
"""
from typing import Dict, Any, List, Optional
import logging

from .llm_agent import LLMAgent

logger = logging.getLogger(__name__)

class SynthesisAgent(LLMAgent):
    """
    Agent specialized in synthesizing information and generating outputs.
    """
    
    def __init__(self, agent_id: str, name: str, description: str, llm_client):
        """
        Initialize a synthesis agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            description: Detailed description of the agent's purpose and capabilities
            llm_client: Client for interacting with the LLM
        """
        capabilities = ["information_synthesis", "content_generation", "summarization", "report_writing"]
        system_prompt = """
        You are a highly skilled synthesis agent. Your primary capabilities include:
        
        1. Integrating information from multiple sources into a coherent whole
        2. Identifying key themes and insights across diverse inputs
        3. Generating clear, well-structured content based on synthesized information
        4. Adapting your output to different formats and audiences
        5. Ensuring logical flow and narrative coherence
        
        When given a synthesis task, you should:
        1. Understand the specific output requirements
        2. Review all provided inputs carefully
        3. Identify connections, patterns, and key points across inputs
        4. Organize the information into a logical structure
        5. Generate a cohesive, well-crafted output that meets the requirements
        
        Always strive for clarity, coherence, and comprehensiveness in your synthesis.
        """
        
        super().__init__(agent_id, name, description, capabilities, llm_client, system_prompt)
        
    async def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a synthesis task.
        
        Args:
            input_data: The input data for the agent to process
            context: Contextual information that might be relevant for processing
            
        Returns:
            Dict containing the synthesis results
        """
        # Extract the inputs to synthesize
        inputs_to_synthesize = []
        if "task" in input_data and "inputs" in input_data["task"]:
            inputs_to_synthesize = input_data["task"]["inputs"]
        elif "inputs" in input_data:
            inputs_to_synthesize = input_data["inputs"]
        elif "research_results" in input_data:
            inputs_to_synthesize.append({"type": "research", "content": input_data["research_results"]})
        elif "analysis_results" in input_data:
            inputs_to_synthesize.append({"type": "analysis", "content": input_data["analysis_results"]})
            
        if not inputs_to_synthesize:
            return {
                "status": "error",
                "error": "No inputs provided for synthesis"
            }
            
        # Extract the output format
        output_format = input_data.get("output_format", "report")
        
        # Add synthesis-specific instructions to the input
        input_with_instructions = input_data.copy()
        input_with_instructions["synthesis_instructions"] = f"""
        Please synthesize the provided inputs into a coherent {output_format}.
        Ensure that you integrate all key information and insights.
        The output should be well-structured, clear, and comprehensive.
        """
        
        # Process with the LLM
        llm_result = await super().process(input_with_instructions, context)
        
        # Add metadata about the synthesis process
        if llm_result["status"] == "success":
            llm_result["metadata"] = {
                "output_format": output_format,
                "num_inputs": len(inputs_to_synthesize),
                "input_types": [input_item.get("type", "unknown") for input_item in inputs_to_synthesize]
            }
            
        return llm_result
