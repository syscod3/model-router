from __future__ import annotations

from integrations.hermes import HermesRouteTarget, apply_route


class FakeAgent:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.reasoning_config = None

    def switch_model(self, model, provider, api_key="", base_url="", api_mode="", capabilities=None):
        self.calls.append((model, provider, api_key, base_url, api_mode, capabilities))


def test_adapter_switches_provider_model_and_reasoning_without_restart():
    agent = FakeAgent()
    target = HermesRouteTarget(
        provider="zai",
        model="glm-4.7",
        base_url="https://api.z.ai/api/paas/v4",
        api_mode="openai",
        reasoning="medium",
    )

    apply_route(agent, target)

    assert agent.calls == [
        ("glm-4.7", "zai", "", "https://api.z.ai/api/paas/v4", "openai", None)
    ]
    assert agent.reasoning_config == {"effort": "medium"}
