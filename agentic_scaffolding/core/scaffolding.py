"""
Main Agentic Scaffolding class that ties all components together.
"""
from typing import Dict, Any, List, Optional, Callable, Type
import asyncio
import logging
import uuid
from datetime import datetime

from .agent import Agent
from .decomposition import TaskDecomposer, LLMTaskDecomposer
from .planning import Planner, LLMPlanner
from .coordination import TaskAllocator, CapabilityBasedAllocator, ProgressMonitor
from .resources import AgentRegistry, ToolRegistry, KnowledgeSourceRegistry
from .communication import Message, MessageBroker, InMemoryMessageBroker, SharedContext

logger = logging.getLogger(__name__)

class AgenticScaffolding:
    """
    Main class that implements the Agentic Scaffolding framework.
    """
    
    def __init__(self, 
                 decomposer: Optional[TaskDecomposer] = None,
                 planner: Optional[Planner] = None,
                 allocator: Optional[TaskAllocator] = None,
                 message_broker: Optional[MessageBroker] = None,
                 llm_client = None):
        """
        Initialize the Agentic Scaffolding.
        
        Args:
            decomposer: Task decomposer component
            planner: Planner component
            allocator: Task allocator component
            message_broker: Message broker component
            llm_client: LLM client for components that need it
        """
        self.llm_client = llm_client
        
        # Initialize components
        self.decomposer = decomposer or (LLMTaskDecomposer(llm_client) if llm_client else None)
        self.planner = planner or (LLMPlanner(llm_client) if llm_client else None)
        self.allocator = allocator or CapabilityBasedAllocator()
        self.message_broker = message_broker or InMemoryMessageBroker()
        
        # Initialize registries
        self.agent_registry = AgentRegistry()
        self.tool_registry = ToolRegistry()
        self.knowledge_source_registry = KnowledgeSourceRegistry()
        
        # Initialize monitoring
        self.progress_monitor = ProgressMonitor()
        
        # Initialize shared context
        self.shared_context = SharedContext()
        
        # Initialize task storage
        self.tasks = {}
        self.plans = {}
        self.executions = {}
        
        # Initialize scaffolding ID
        self.scaffolding_id = str(uuid.uuid4())
        
        logger.info(f"Initialized Agentic Scaffolding with ID: {self.scaffolding_id}")
        
    async def register_agent(self, agent: Agent) -> None:
        """
        Register an agent with the scaffolding.
        
        Args:
            agent: The agent to register
        """
        metadata = agent.get_metadata()
        agent_id = metadata["agent_id"]
        
        # Register with the agent registry
        self.agent_registry.register_agent(
            agent_id=agent_id,
            name=metadata["name"],
            description=metadata["description"],
            capabilities=metadata["capabilities"]
        )
        
        # Register with the progress monitor
        self.progress_monitor.register_agent(agent_id, metadata)
        
        # Subscribe the agent to messages
        await self.message_broker.subscribe(agent_id, self._create_agent_message_handler(agent))
        
        logger.info(f"Registered agent: {agent_id}")
        
    def _create_agent_message_handler(self, agent: Agent) -> Callable[[Message], None]:
        """
        Create a message handler for an agent.
        
        Args:
            agent: The agent to create a handler for
            
        Returns:
            Async callback function that handles messages for the agent
        """
        async def handle_message(message: Message) -> None:
            try:
                # Process the message
                result = await agent.process(message.content, {"message": message})
                
                # Send a response if needed
                if message.message_type == "request":
                    response = Message(
                        sender_id=agent.agent_id,
                        receiver_id=message.sender_id,
                        content=result,
                        message_type="response",
                        conversation_id=message.conversation_id
                    )
                    await self.message_broker.publish(response)
            except Exception as e:
                logger.error(f"Error processing message in agent {agent.agent_id}: {e}")
                
                # Send an error response
                if message.message_type == "request":
                    error_response = Message(
                        sender_id=agent.agent_id,
                        receiver_id=message.sender_id,
                        content={"error": str(e)},
                        message_type="error",
                        conversation_id=message.conversation_id
                    )
                    await self.message_broker.publish(error_response)
                    
        return handle_message
    
    async def process_goal(self, goal: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a high-level goal through the scaffolding.
        
        Args:
            goal: The high-level goal to process
            context: Additional context for processing
            
        Returns:
            Execution ID for tracking the goal's execution
        """
        if not self.decomposer:
            raise ValueError("Task decomposer not initialized")
        if not self.planner:
            raise ValueError("Planner not initialized")
            
        context = context or {}
        
        # Generate a unique execution ID
        execution_id = str(uuid.uuid4())
        
        # Store execution metadata
        self.executions[execution_id] = {
            "goal": goal,
            "context": context,
            "status": "initializing",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "subtasks": [],
            "plan": None,
            "result": None,
            "errors": []
        }
        
        # Start the execution process asynchronously
        asyncio.create_task(self._execute_goal(execution_id, goal, context))
        
        return execution_id
    
    async def _execute_goal(self, execution_id: str, goal: str, context: Dict[str, Any]) -> None:
        """
        Execute a goal through the complete scaffolding workflow.
        
        Args:
            execution_id: Unique identifier for this execution
            goal: The high-level goal to execute
            context: Additional context for execution
        """
        try:
            # Update execution status
            self.executions[execution_id]["status"] = "decomposing"
            
            # Step 1: Decompose the goal into subtasks
            logger.info(f"Decomposing goal: {goal}")
            subtasks = await self.decomposer.decompose(goal, context)
            
            # Assign task IDs and register with monitor
            for i, subtask in enumerate(subtasks):
                task_id = f"{execution_id}-task-{i}"
                subtask["task_id"] = task_id
                self.tasks[task_id] = subtask
                self.progress_monitor.register_task(task_id, subtask)
                
            # Update execution with subtasks
            self.executions[execution_id]["subtasks"] = [task["task_id"] for task in subtasks]
            self.executions[execution_id]["status"] = "planning"
            
            # Step 2: Create a plan for executing the subtasks
            logger.info(f"Planning execution for {len(subtasks)} subtasks")
            plan = await self.planner.create_plan(subtasks, context)
            
            # Store the plan
            plan_id = f"{execution_id}-plan"
            self.plans[plan_id] = plan
            self.executions[execution_id]["plan"] = plan_id
            self.executions[execution_id]["status"] = "allocating"
            
            # Step 3: Allocate tasks to agents
            logger.info("Allocating tasks to agents")
            available_agents = [
                {"agent_id": agent_id, **metadata}
                for agent_id, metadata in self.agent_registry.resources.items()
            ]
            
            allocations = await self.allocator.allocate(subtasks, available_agents)
            
            # Update task assignments in the monitor
            for agent_id, task_ids in allocations.items():
                for task_id in task_ids:
                    self.progress_monitor.update_task_status(task_id, {"assigned_agent": agent_id})
                    
                # Update agent status
                self.progress_monitor.update_agent_status(agent_id, {
                    "status": "assigned",
                    "current_tasks": task_ids
                })
                
            self.executions[execution_id]["status"] = "executing"
            
            # Step 4: Execute the plan
            logger.info("Executing plan")
            result = await self._execute_plan(execution_id, plan, allocations)
            
            # Update execution with result
            self.executions[execution_id]["result"] = result
            self.executions[execution_id]["status"] = "completed"
            self.executions[execution_id]["end_time"] = datetime.now().isoformat()
            
            logger.info(f"Goal execution completed: {execution_id}")
            
        except Exception as e:
            logger.error(f"Error executing goal: {e}")
            self.executions[execution_id]["status"] = "failed"
            self.executions[execution_id]["errors"].append(str(e))
            self.executions[execution_id]["end_time"] = datetime.now().isoformat()
    
    async def _execute_plan(self, execution_id: str, plan: Dict[str, Any], 
                           allocations: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Execute a plan by coordinating agent activities.
        
        Args:
            execution_id: Unique identifier for this execution
            plan: The plan to execute
            allocations: Task allocations to agents
            
        Returns:
            Execution results
        """
        # In a real implementation, this would handle the complex logic of
        # executing the plan steps, potentially in parallel, handling dependencies,
        # monitoring progress, and adapting to failures.
        
        # For this demo, we'll implement a simplified sequential execution
        results = {}
        
        # Create a reverse mapping from task_id to agent_id
        task_to_agent = {}
        for agent_id, task_ids in allocations.items():
            for task_id in task_ids:
                task_to_agent[task_id] = agent_id
                
        # Execute each step in the plan
        for step_index, step in enumerate(plan.get("steps", [])):
            step_id = f"{execution_id}-step-{step_index}"
            logger.info(f"Executing step {step_id}: {step.get('name', 'Unnamed step')}")
            
            # Get the tasks for this step
            step_tasks = step.get("tasks", [])
            if isinstance(step_tasks, str):
                # Handle the case where tasks might be a comma-separated string
                step_tasks = [task.strip() for task in step_tasks.split(",")]
                
            # Execute each task in this step
            step_results = {}
            for task_id in step_tasks:
                if task_id in self.tasks and task_id in task_to_agent:
                    agent_id = task_to_agent[task_id]
                    task = self.tasks[task_id]
                    
                    # Update task status
                    self.progress_monitor.update_task_status(task_id, {
                        "status": "in_progress",
                        "start_time": datetime.now().isoformat()
                    })
                    
                    # Send a task execution message to the agent
                    message = Message(
                        sender_id=self.scaffolding_id,
                        receiver_id=agent_id,
                        content={
                            "task_id": task_id,
                            "execution_id": execution_id,
                            "task": task
                        },
                        message_type="task_execution"
                    )
                    
                    # In a real implementation, we would await the agent's response
                    # For this demo, we'll simulate a successful execution
                    await asyncio.sleep(0.1)  # Simulate processing time
                    
                    # Update task status to completed
                    self.progress_monitor.update_task_status(task_id, {
                        "status": "completed",
                        "end_time": datetime.now().isoformat(),
                        "result": {"message": f"Simulated execution of task {task_id}"}
                    })
                    
                    # Store the result
                    step_results[task_id] = {"status": "completed", "message": f"Simulated execution of task {task_id}"}
                else:
                    logger.warning(f"Task {task_id} not found or not allocated to any agent")
                    step_results[task_id] = {"status": "skipped", "message": "Task not found or not allocated"}
                    
            # Store the results for this step
            results[step_id] = step_results
            
        return {
            "execution_id": execution_id,
            "steps_completed": len(plan.get("steps", [])),
            "results": results
        }
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a goal execution.
        
        Args:
            execution_id: Unique identifier for the execution
            
        Returns:
            Dictionary containing the execution status, or None if not found
        """
        return self.executions.get(execution_id)
    
    def get_all_executions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the status of all executions.
        
        Returns:
            Dictionary mapping execution IDs to their status dictionaries
        """
        return self.executions.copy()
