"""
Base chain class for LLM chains.
Provides prompt templating and LLM execution.
"""
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.common.providers.llm import (
    LLMProvider,
    LLMProviderType,
    LLMResponse,
    get_llm_provider,
)

logger = logging.getLogger(__name__)


class PromptTemplate:
    """
    A template for creating prompts with variable substitution.

    Uses {variable_name} syntax for placeholders.
    """

    def __init__(
        self,
        template: str,
        input_variables: Optional[List[str]] = None,
    ):
        self.template = template

        # Extract variables from template if not provided
        if input_variables is None:
            self.input_variables = self._extract_variables(template)
        else:
            self.input_variables = input_variables

    def _extract_variables(self, template: str) -> List[str]:
        """Extract variable names from template."""
        pattern = r'\{(\w+)\}'
        return list(set(re.findall(pattern, template)))

    def format(self, **kwargs) -> str:
        """
        Format the template with the given variables.

        Args:
            **kwargs: Variable values to substitute

        Returns:
            The formatted prompt string
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            missing = str(e).strip("'")
            raise ValueError(f"Missing required variable: {missing}")

    def partial(self, **kwargs) -> "PromptTemplate":
        """
        Create a new template with some variables filled in.

        Args:
            **kwargs: Variables to fill in

        Returns:
            A new PromptTemplate with remaining variables
        """
        new_template = self.template
        for key, value in kwargs.items():
            new_template = new_template.replace(f"{{{key}}}", str(value))

        remaining_vars = [v for v in self.input_variables if v not in kwargs]
        return PromptTemplate(new_template, remaining_vars)


class BaseChain(ABC):
    """
    Base class for all chains in the framework.

    Chains represent a sequence of LLM calls and transformations.
    They can:
    - Process prompts through templates
    - Chain multiple LLM calls
    - Transform outputs
    - Handle memory/context
    """

    def __init__(
        self,
        name: str,
        llm: Optional[LLMProvider] = None,
        prompt_template: Optional[PromptTemplate] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ):
        self.name = name
        self._llm = llm
        self.prompt_template = prompt_template
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Chain memory for passing context between runs
        self.memory: Dict[str, Any] = {}

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

    @abstractmethod
    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the chain with the given input.

        Args:
            input: Dictionary containing input variables for the chain

        Returns:
            Dictionary containing the chain's output
        """
        pass

    def format_prompt(self, **kwargs) -> str:
        """Format the prompt template with the given variables."""
        if self.prompt_template:
            return self.prompt_template.format(**kwargs)
        return ""

    def add_to_memory(self, key: str, value: Any) -> None:
        """Add a value to the chain's memory."""
        self.memory[key] = value

    def get_from_memory(self, key: str, default: Any = None) -> Any:
        """Get a value from the chain's memory."""
        return self.memory.get(key, default)

    def clear_memory(self) -> None:
        """Clear the chain's memory."""
        self.memory = {}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name})>"


class LLMChain(BaseChain):
    """
    A simple chain that formats a prompt and calls the LLM.

    This is the most basic chain type.
    """

    def __init__(
        self,
        name: str,
        prompt_template: PromptTemplate,
        llm: Optional[LLMProvider] = None,
        output_key: str = "output",
        **kwargs,
    ):
        super().__init__(name, llm, prompt_template, **kwargs)
        self.output_key = output_key

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the chain: format prompt -> call LLM -> return output.

        Args:
            input: Dictionary with values for prompt template variables

        Returns:
            Dictionary with the LLM output
        """
        try:
            # Format the prompt
            prompt = self.format_prompt(**input)

            # Call the LLM
            response = await self.llm.generate(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            return {
                "success": True,
                self.output_key: response.content,
                "prompt": prompt,
                "model": response.model,
                "usage": response.usage,
            }
        except Exception as e:
            logger.error(f"Chain {self.name} error: {e}")
            return {
                "success": False,
                "error": str(e),
            }


class SequentialChain(BaseChain):
    """
    A chain that runs multiple chains in sequence.

    The output of each chain is passed as input to the next.
    """

    def __init__(
        self,
        name: str,
        chains: List[BaseChain],
        input_key: str = "input",
        output_key: str = "output",
    ):
        super().__init__(name)
        self.chains = chains
        self.input_key = input_key
        self.output_key = output_key

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run chains in sequence, passing outputs to inputs.

        Args:
            input: Initial input dictionary

        Returns:
            Final output dictionary with all intermediate results
        """
        current_input = input.copy()
        all_outputs = {}

        for i, chain in enumerate(self.chains):
            try:
                result = await chain.run(current_input)

                if not result.get("success", True):
                    return {
                        "success": False,
                        "error": f"Chain {chain.name} failed: {result.get('error')}",
                        "failed_at": i,
                        "partial_outputs": all_outputs,
                    }

                # Store output and prepare for next chain
                all_outputs[chain.name] = result
                current_input.update(result)

            except Exception as e:
                logger.error(f"Sequential chain error at {chain.name}: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "failed_at": i,
                    "partial_outputs": all_outputs,
                }

        return {
            "success": True,
            self.output_key: current_input.get(self.output_key),
            "all_outputs": all_outputs,
        }


class TransformChain(BaseChain):
    """
    A chain that transforms input without calling an LLM.

    Useful for data preprocessing or postprocessing.
    """

    def __init__(
        self,
        name: str,
        transform_func: callable,
        input_keys: List[str],
        output_keys: List[str],
    ):
        super().__init__(name)
        self.transform_func = transform_func
        self.input_keys = input_keys
        self.output_keys = output_keys

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the transform function on input.

        Args:
            input: Dictionary with input values

        Returns:
            Dictionary with transformed outputs
        """
        try:
            # Extract only the required inputs
            transform_input = {k: input.get(k) for k in self.input_keys}

            # Run transform (support both sync and async)
            if callable(self.transform_func):
                import asyncio
                if asyncio.iscoroutinefunction(self.transform_func):
                    result = await self.transform_func(**transform_input)
                else:
                    result = self.transform_func(**transform_input)

            if isinstance(result, dict):
                return {"success": True, **result}
            elif len(self.output_keys) == 1:
                return {"success": True, self.output_keys[0]: result}
            else:
                return {"success": True, "output": result}

        except Exception as e:
            logger.error(f"Transform chain {self.name} error: {e}")
            return {
                "success": False,
                "error": str(e),
            }


class ConditionalChain(BaseChain):
    """
    A chain that selects which chain to run based on a condition.
    """

    def __init__(
        self,
        name: str,
        condition_func: callable,
        true_chain: BaseChain,
        false_chain: BaseChain,
    ):
        super().__init__(name)
        self.condition_func = condition_func
        self.true_chain = true_chain
        self.false_chain = false_chain

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate condition and run appropriate chain.

        Args:
            input: Dictionary with input values

        Returns:
            Output from the selected chain
        """
        try:
            # Evaluate condition
            import asyncio
            if asyncio.iscoroutinefunction(self.condition_func):
                condition_result = await self.condition_func(input)
            else:
                condition_result = self.condition_func(input)

            # Run appropriate chain
            if condition_result:
                result = await self.true_chain.run(input)
                result["branch"] = "true"
            else:
                result = await self.false_chain.run(input)
                result["branch"] = "false"

            return result

        except Exception as e:
            logger.error(f"Conditional chain {self.name} error: {e}")
            return {
                "success": False,
                "error": str(e),
            }
