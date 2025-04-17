"""
Research agent implementation.
"""
from typing import Dict, Any, List, Optional
import logging

from .llm_agent import LLMAgent

logger = logging.getLogger(__name__)

class ResearchAgent(LLMAgent):
    """
    Agent specialized in research and information gathering.
    """
    
    def __init__(self, agent_id: str, name: str, description: str, llm_client, search_tool=None):
        """
        Initialize a research agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            description: Detailed description of the agent's purpose and capabilities
            llm_client: Client for interacting with the LLM
            search_tool: Optional tool for web search or information retrieval
        """
        capabilities = ["research", "information_gathering", "summarization"]
        system_prompt = """
        You are a highly skilled research agent. Your primary capabilities include:
        
        1. Gathering information from various sources
        2. Analyzing and synthesizing information
        3. Identifying key insights and patterns
        4. Summarizing complex information clearly and concisely
        
        When given a research task, you should:
        1. Understand the specific information needs
        2. Gather relevant information using available tools
        3. Analyze the information for relevance and accuracy
        4. Synthesize the findings into a coherent response
        5. Provide proper citations and sources
        
        Always strive for accuracy, comprehensiveness, and objectivity in your research.
        """
        
        super().__init__(agent_id, name, description, capabilities, llm_client, system_prompt)
        self.search_tool = search_tool
        
    async def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a research task.
        
        Args:
            input_data: The input data for the agent to process
            context: Contextual information that might be relevant for processing
            
        Returns:
            Dict containing the research results
        """
        # Extract the research query
        research_query = None
        if "task" in input_data and "description" in input_data["task"]:
            research_query = input_data["task"]["description"]
        elif "query" in input_data:
            research_query = input_data["query"]
            
        if not research_query:
            return {
                "status": "error",
                "error": "No research query provided"
            }
            
        # Perform search if search tool is available
        search_results = []
        if self.search_tool:
            try:
                search_results = await self.search_tool.search(research_query)
            except Exception as e:
                logger.error(f"Error in search tool: {e}")
                search_results = []
                
        # Add search results to the input for the LLM
        input_with_results = input_data.copy()
        input_with_results["search_results"] = search_results
        
        # Process with the LLM
        llm_result = await super().process(input_with_results, context)
        
        # Add metadata about the research process
        if llm_result["status"] == "success":
            llm_result["metadata"] = {
                "query": research_query,
                "num_sources": len(search_results),
                "sources": [result.get("title", "Unknown source") for result in search_results[:3]]
            }
            
        return llm_result
