"""
Base orchestrator class for coordinating multiple agents.
Provides workflow management and agent coordination.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable

from app.common.base.agent import BaseAgent
from app.common.providers.llm import LLMProvider, LLMProviderType, get_llm_provider

logger = logging.getLogger(__name__)


class WorkflowStep:
    """
    A step in an orchestrator workflow.

    Steps can execute agents, run functions, or branch based on conditions.
    """

    def __init__(
        self,
        name: str,
        agent: Optional[str] = None,
        func: Optional[Callable] = None,
        input_mapping: Optional[Dict[str, str]] = None,
        output_mapping: Optional[Dict[str, str]] = None,
        condition: Optional[Callable[[Dict], bool]] = None,
        next_step: Optional[str] = None,
        on_success: Optional[str] = None,
        on_failure: Optional[str] = None,
    ):
        """
        Initialize a workflow step.

        Args:
            name: Unique step name
            agent: Name of agent to execute (mutually exclusive with func)
            func: Function to execute (mutually exclusive with agent)
            input_mapping: Map workflow state keys to step input keys
            output_mapping: Map step output keys to workflow state keys
            condition: Optional condition function for branching
            next_step: Default next step name
            on_success: Step to execute on success
            on_failure: Step to execute on failure
        """
        self.name = name
        self.agent = agent
        self.func = func
        self.input_mapping = input_mapping or {}
        self.output_mapping = output_mapping or {}
        self.condition = condition
        self.next_step = next_step
        self.on_success = on_success
        self.on_failure = on_failure


class BaseOrchestrator(ABC):
    """
    Base class for all orchestrators in the framework.

    Orchestrators coordinate multiple agents to accomplish complex tasks.
    They manage:
    - Agent registration and lifecycle
    - Task distribution and routing
    - Workflow execution
    - State management
    """

    def __init__(
        self,
        name: str,
        description: str,
        llm: Optional[LLMProvider] = None,
    ):
        self.name = name
        self.description = description
        self._llm = llm
        self.agents: Dict[str, BaseAgent] = {}
        self.state: Dict[str, Any] = {}
        self.workflow_steps: Dict[str, WorkflowStep] = {}
        self._initialized = False

    @property
    def llm(self) -> LLMProvider:
        """Get the LLM provider, initializing if needed."""
        if self._llm is None:
            self._llm = get_llm_provider(LLMProviderType.OLLAMA)
        return self._llm

    @llm.setter
    def llm(self, value: LLMProvider) -> None:
        """Set the LLM provider."""
        self._llm = value

    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the orchestrator."""
        self.agents[agent.name] = agent
        logger.debug(f"Registered agent '{agent.name}' with orchestrator '{self.name}'")

    def unregister_agent(self, agent_name: str) -> None:
        """Unregister an agent from the orchestrator."""
        if agent_name in self.agents:
            del self.agents[agent_name]
            logger.debug(f"Unregistered agent '{agent_name}' from orchestrator '{self.name}'")

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get a registered agent by name."""
        return self.agents.get(agent_name)

    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self.agents.keys())

    def add_workflow_step(self, step: WorkflowStep) -> None:
        """Add a workflow step."""
        self.workflow_steps[step.name] = step

    def get_workflow_step(self, name: str) -> Optional[WorkflowStep]:
        """Get a workflow step by name."""
        return self.workflow_steps.get(name)

    @abstractmethod
    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the orchestrator workflow with the given input.

        Args:
            input: Dictionary containing the input data for the workflow

        Returns:
            Dictionary containing the workflow output
        """
        pass

    async def initialize(self) -> None:
        """Initialize the orchestrator and all registered agents."""
        if self._initialized:
            return

        logger.info(f"Initializing orchestrator: {self.name}")

        # Initialize all agents
        for agent in self.agents.values():
            await agent.initialize()

        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup the orchestrator and all registered agents."""
        logger.info(f"Cleaning up orchestrator: {self.name}")

        for agent in self.agents.values():
            await agent.cleanup()

        self.state = {}
        self._initialized = False

    async def execute_agent(
        self,
        agent_name: str,
        input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a specific agent.

        Args:
            agent_name: Name of the agent to execute
            input: Input data for the agent

        Returns:
            Agent output
        """
        agent = self.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")

        return await agent.run(input)

    async def execute_step(
        self,
        step: WorkflowStep,
        workflow_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a workflow step.

        Args:
            step: The workflow step to execute
            workflow_state: Current workflow state

        Returns:
            Step output
        """
        # Prepare input using mapping
        step_input = {}
        for step_key, state_key in step.input_mapping.items():
            step_input[step_key] = workflow_state.get(state_key)

        # Add unmapped state values
        for key, value in workflow_state.items():
            if key not in step_input:
                step_input[key] = value

        # Execute step
        if step.agent:
            result = await self.execute_agent(step.agent, step_input)
        elif step.func:
            if asyncio.iscoroutinefunction(step.func):
                result = await step.func(step_input)
            else:
                result = step.func(step_input)
            if not isinstance(result, dict):
                result = {"output": result, "success": True}
        else:
            result = {"success": True, "output": None}

        # Apply output mapping
        mapped_output = {}
        for step_key, state_key in step.output_mapping.items():
            if step_key in result:
                mapped_output[state_key] = result[step_key]

        # Add unmapped output values
        for key, value in result.items():
            if key not in mapped_output and key not in ["success", "error"]:
                mapped_output[key] = value

        mapped_output["success"] = result.get("success", True)
        if "error" in result:
            mapped_output["error"] = result["error"]

        return mapped_output

    async def run_workflow(
        self,
        start_step: str,
        input: Dict[str, Any],
        max_steps: int = 100,
    ) -> Dict[str, Any]:
        """
        Run a workflow starting from a specific step.

        Args:
            start_step: Name of the starting step
            input: Initial input data
            max_steps: Maximum number of steps to prevent infinite loops

        Returns:
            Final workflow output
        """
        workflow_state = input.copy()
        current_step_name = start_step
        steps_executed = 0

        while current_step_name and steps_executed < max_steps:
            step = self.get_workflow_step(current_step_name)
            if not step:
                logger.error(f"Workflow step '{current_step_name}' not found")
                return {
                    "success": False,
                    "error": f"Step '{current_step_name}' not found",
                    "state": workflow_state,
                }

            # Check condition if present
            if step.condition:
                try:
                    if asyncio.iscoroutinefunction(step.condition):
                        should_execute = await step.condition(workflow_state)
                    else:
                        should_execute = step.condition(workflow_state)

                    if not should_execute:
                        current_step_name = step.next_step
                        continue
                except Exception as e:
                    logger.error(f"Condition evaluation failed for step '{step.name}': {e}")

            # Execute step
            try:
                result = await self.execute_step(step, workflow_state)
                workflow_state.update(result)
                steps_executed += 1

                # Determine next step
                if result.get("success", True):
                    current_step_name = step.on_success or step.next_step
                else:
                    current_step_name = step.on_failure or step.next_step

            except Exception as e:
                logger.error(f"Step '{step.name}' failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "failed_step": step.name,
                    "state": workflow_state,
                }

        if steps_executed >= max_steps:
            logger.warning(f"Workflow reached max steps ({max_steps})")

        return {
            "success": True,
            "steps_executed": steps_executed,
            "state": workflow_state,
        }

    def get_state(self) -> Dict[str, Any]:
        """Get the current orchestrator state."""
        return self.state.copy()

    def set_state(self, state: Dict[str, Any]) -> None:
        """Set the orchestrator state."""
        self.state = state.copy()

    def update_state(self, **kwargs) -> None:
        """Update specific state values."""
        self.state.update(kwargs)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, agents={len(self.agents)})>"


class SimpleOrchestrator(BaseOrchestrator):
    """
    A simple orchestrator that routes to a single agent.

    Good for simple use cases where only one agent is needed.
    """

    def __init__(
        self,
        name: str,
        description: str,
        default_agent: Optional[str] = None,
    ):
        super().__init__(name, description)
        self.default_agent = default_agent

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the default agent with the input.

        Args:
            input: Input data

        Returns:
            Agent output
        """
        await self.initialize()

        agent_name = input.get("agent") or self.default_agent

        if not agent_name:
            # Use the first registered agent
            if self.agents:
                agent_name = list(self.agents.keys())[0]
            else:
                return {
                    "success": False,
                    "error": "No agents registered",
                }

        try:
            result = await self.execute_agent(agent_name, input)
            return {
                "success": result.get("success", True),
                "result": result,
                "agent": agent_name,
                "orchestrator": self.name,
            }
        except Exception as e:
            logger.error(f"Orchestrator {self.name} error: {e}")
            return {
                "success": False,
                "error": str(e),
                "orchestrator": self.name,
            }


class SequentialOrchestrator(BaseOrchestrator):
    """
    An orchestrator that runs agents in sequence.

    Each agent's output is passed to the next agent.
    """

    def __init__(
        self,
        name: str,
        description: str,
        agent_sequence: Optional[List[str]] = None,
    ):
        super().__init__(name, description)
        self.agent_sequence = agent_sequence or []

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run agents in sequence.

        Args:
            input: Initial input data

        Returns:
            Final output after all agents have run
        """
        await self.initialize()

        sequence = input.get("sequence") or self.agent_sequence
        if not sequence:
            sequence = list(self.agents.keys())

        current_input = input.copy()
        all_results = {}

        for agent_name in sequence:
            try:
                result = await self.execute_agent(agent_name, current_input)
                all_results[agent_name] = result

                if not result.get("success", True):
                    return {
                        "success": False,
                        "error": f"Agent '{agent_name}' failed: {result.get('error')}",
                        "failed_agent": agent_name,
                        "partial_results": all_results,
                        "orchestrator": self.name,
                    }

                # Pass output to next agent
                current_input.update(result)

            except Exception as e:
                logger.error(f"Agent {agent_name} error: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "failed_agent": agent_name,
                    "partial_results": all_results,
                    "orchestrator": self.name,
                }

        return {
            "success": True,
            "result": current_input,
            "all_results": all_results,
            "orchestrator": self.name,
        }


class ParallelOrchestrator(BaseOrchestrator):
    """
    An orchestrator that runs agents in parallel.

    All agents receive the same input and run concurrently.
    """

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all agents in parallel.

        Args:
            input: Input data for all agents

        Returns:
            Combined results from all agents
        """
        await self.initialize()

        agents_to_run = input.get("agents") or list(self.agents.keys())

        # Create tasks for all agents
        tasks = []
        for agent_name in agents_to_run:
            if agent_name in self.agents:
                tasks.append(self.execute_agent(agent_name, input))

        if not tasks:
            return {
                "success": False,
                "error": "No agents to run",
                "orchestrator": self.name,
            }

        # Run all agents in parallel
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            all_results = {}
            errors = []

            for agent_name, result in zip(agents_to_run, results):
                if isinstance(result, Exception):
                    errors.append(f"{agent_name}: {str(result)}")
                    all_results[agent_name] = {
                        "success": False,
                        "error": str(result),
                    }
                else:
                    all_results[agent_name] = result
                    if not result.get("success", True):
                        errors.append(f"{agent_name}: {result.get('error')}")

            return {
                "success": len(errors) == 0,
                "results": all_results,
                "errors": errors if errors else None,
                "orchestrator": self.name,
            }

        except Exception as e:
            logger.error(f"Parallel orchestrator error: {e}")
            return {
                "success": False,
                "error": str(e),
                "orchestrator": self.name,
            }
