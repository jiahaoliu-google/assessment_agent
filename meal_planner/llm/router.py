"""
Strategic Model Router for Multi-Agent LLM Task Allocation and Provider Fallback.
Routes tasks to appropriate LLM tiers based on task complexity and agent responsibilities.
"""

import logging
from typing import Dict, Any, List, Optional
from meal_planner.llm.provider import (
    BaseLLMProvider, MockLLMProvider, GeminiLLMProvider, OpenAILLMProvider,
    ModelTier, LLMResponse
)


class StrategicModelRouter:
    """
    Strategic Model Router that maps agent roles/tasks to specific model tiers
    (FAST, BALANCED, REASONING) and handles seamless multi-provider fallback.
    """

    DEFAULT_AGENT_TIER_MAPPING: Dict[str, ModelTier] = {
        "ProfileAnalyzerAgent": ModelTier.FAST,
        "NutritionistAgent": ModelTier.BALANCED,
        "ChefMealPlannerAgent": ModelTier.BALANCED,
        "DietaryAuditorAgent": ModelTier.REASONING,  # High reasoning tier for output guardrails & allergen auditing
        "GroceryPrepAgent": ModelTier.FAST
    }

    def __init__(self, primary_provider: Optional[BaseLLMProvider] = None, fallback_providers: Optional[List[BaseLLMProvider]] = None):
        # Default fallback chain: Gemini -> OpenAI -> Offline Mock
        if primary_provider:
            self.providers = [primary_provider] + (fallback_providers if fallback_providers else [])
        else:
            self.providers = []
            # Try initializing Gemini
            try:
                self.providers.append(GeminiLLMProvider())
            except ValueError:
                pass

            # Try initializing OpenAI
            try:
                self.providers.append(OpenAILLMProvider())
            except ValueError:
                pass

            # Always add MockLLMProvider as deterministic offline fallback
            self.providers.append(MockLLMProvider())

    def get_tier_for_agent(self, agent_name: str) -> ModelTier:
        """Determines model tier based on agent task complexity."""
        return self.DEFAULT_AGENT_TIER_MAPPING.get(agent_name, ModelTier.BALANCED)

    def route_and_generate(
        self,
        agent_name: str,
        prompt: str,
        system_prompt: str = "",
        json_schema: Optional[Dict[str, Any]] = None,
        override_tier: Optional[ModelTier] = None
    ) -> LLMResponse:
        """
        Routes the prompt to the mapped model tier and executes generation
        with automatic fallback across configured providers.
        """
        tier = override_tier if override_tier else self.get_tier_for_agent(agent_name)
        logging.info(f"Routing request for agent '{agent_name}' to Model Tier '{tier.value}'")

        last_error = None
        for provider in self.providers:
            try:
                response = provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    tier=tier,
                    json_schema=json_schema
                )
                logging.info(f"Generation successful via provider '{response.provider_name}' using model '{response.model_name}'")
                return response
            except Exception as e:
                logging.warning(f"Provider '{provider.__class__.__name__}' failed for tier '{tier.value}': {e}. Falling back...")
                last_error = e

        # Fallback to offline mock guaranteed
        mock_provider = MockLLMProvider()
        return mock_provider.generate(prompt=prompt, system_prompt=system_prompt, tier=tier, json_schema=json_schema)
