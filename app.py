"""
Web application for demonstrating the Agentic Scaffolding framework.
"""
import os
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from agentic_scaffolding.core.scaffolding import AgenticScaffolding
from agentic_scaffolding.utils.llm_client import MockLLMClient, OpenAIClient
from agentic_scaffolding.agents.research_agent import ResearchAgent
from agentic_scaffolding.agents.analysis_agent import AnalysisAgent
from agentic_scaffolding.agents.synthesis_agent import SynthesisAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize the scaffolding and agents
scaffolding = None
executions = {}

def initialize_scaffolding():
    """Initialize the Agentic Scaffolding with agents."""
    global scaffolding
    
    # Use mock LLM client for demonstration
    # In a real application, you would use OpenAIClient or another LLM client
    llm_client = MockLLMClient()
    # Uncomment to use OpenAI (requires API key in .env file)
    # llm_client = OpenAIClient()
    
    # Initialize the scaffolding
    scaffolding = AgenticScaffolding(llm_client=llm_client)
    
    # Create and register agents
    research_agent = ResearchAgent(
        agent_id="research-agent-1",
        name="Research Specialist",
        description="Specialized agent for gathering and organizing information from various sources.",
        llm_client=llm_client
    )
    
    analysis_agent = AnalysisAgent(
        agent_id="analysis-agent-1",
        name="Analysis Expert",
        description="Specialized agent for analyzing data and identifying patterns and insights.",
        llm_client=llm_client
    )
    
    synthesis_agent = SynthesisAgent(
        agent_id="synthesis-agent-1",
        name="Synthesis Master",
        description="Specialized agent for synthesizing information and generating coherent outputs.",
        llm_client=llm_client
    )
    
    # Register agents with the scaffolding
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    loop.run_until_complete(scaffolding.register_agent(research_agent))
    loop.run_until_complete(scaffolding.register_agent(analysis_agent))
    loop.run_until_complete(scaffolding.register_agent(synthesis_agent))
    
    logger.info("Scaffolding initialized with agents")

# Initialize scaffolding on startup
initialize_scaffolding()

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/process-goal', methods=['POST'])
def process_goal():
    """Process a goal through the scaffolding."""
    data = request.json
    goal = data.get('goal')
    context = data.get('context', {})
    
    if not goal:
        return jsonify({"error": "No goal provided"}), 400
    
    # Process the goal asynchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    execution_id = loop.run_until_complete(scaffolding.process_goal(goal, context))
    
    # Store execution for tracking
    executions[execution_id] = {
        "goal": goal,
        "context": context,
        "start_time": datetime.now().isoformat(),
        "status": "processing"
    }
    
    return jsonify({
        "execution_id": execution_id,
        "status": "processing",
        "message": "Goal is being processed"
    })

@app.route('/api/execution-status/<execution_id>', methods=['GET'])
def execution_status(execution_id):
    """Get the status of a goal execution."""
    if not scaffolding:
        return jsonify({"error": "Scaffolding not initialized"}), 500
    
    status = scaffolding.get_execution_status(execution_id)
    
    if not status:
        return jsonify({"error": "Execution not found"}), 404
    
    return jsonify(status)

@app.route('/api/all-executions', methods=['GET'])
def all_executions():
    """Get all executions."""
    if not scaffolding:
        return jsonify({"error": "Scaffolding not initialized"}), 500
    
    return jsonify(scaffolding.get_all_executions())

if __name__ == '__main__':
    app.run(debug=True)
