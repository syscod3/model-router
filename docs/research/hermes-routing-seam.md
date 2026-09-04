# Hermes provider-switching and error-hook seam

**Verified:** 2026-09-05 against Hermes `main` commit `f159e581c7afd22a5c94652c569e3859f1b994d2` (2026-09-04). Primary docs: [Event Hooks](https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks) and [Build a Plugin](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins).

## Result

There is **no documented native plugin hook that selects/replaces a provider, model, or reasoning configuration** before a turn. The relevant plugin hooks are either turn-level context injection or observers. V1 should therefore detect a future native selection capability first, then put the present compatibility path behind `integrations/hermes.py`; it must not treat `pre_llm_call` return data as a routing override.

## Exact hooks and payloads

| Need | Hook | Timing / return | Exact payload |
|---|---|---|---|
| Classify and select once per user turn | `pre_llm_call` | Once before the tool loop. Only string or `{"context": ...}` returns are consumed, as text appended to the user message. | `session_id`, `task_id`, `turn_id`, `user_message`, `conversation_history`, `is_first_turn`, `model`, `platform`, `parent_session_id`, `sender_id` |
| Observe each assembled provider attempt | `pre_api_request` | Immediately before send; return ignored. Too late for a supported route override. | `task_id`, `turn_id`, `api_request_id`, `session_id`, `user_message`, `conversation_history`, `platform`, `model`, `provider`, `base_url`, `api_mode`, `api_call_count`, `retry_count`, `request_messages`, `system_prompt`, `message_count`, `tool_count`, `approx_input_tokens`, `request_char_count`, `max_tokens`, `started_at`, `middleware_trace`, `request` |
| Observe an API failure | `api_request_error` | Each failed provider attempt; return ignored. It fires **after** Hermes' error classification and **before** recovery routing. | `task_id`, `turn_id`, `api_request_id`, `session_id`, `platform`, `model`, `provider`, `base_url`, `api_mode`, `api_call_count`, `api_duration`, `started_at`, `ended_at`, `status_code`, `retry_count`, `max_retries`, `retryable`, `reason`, `error={"type","message"}`, `request` |
| Influence Hermes' built-in error classification only | `transform_api_error_classification` | Before the built-in classifier; first valid classification wins. Cannot name a replacement provider/model. | `provider`, `model`, `status_code`, `error_type`, `error_code`, `error_message`, `error_body`, `error`, `approx_tokens`, `context_length`, `num_messages` |

`post_llm_call` is only a successful, non-interrupted turn-finalization observer, so it is not a failure seam.

## Source anchors

* Hook catalog and stated return behavior: `website/docs/user-guide/features/hooks.md:435-457`; public URL above.
* `pre_llm_call` invocation and authoritative payload: `agent/turn_context.py:578-630`.
* `pre_api_request` actual payload and dispatch: `agent/turn_api_request.py:44-91`; request construction precedes it at `119-170`.
* `api_request_error` actual payload: `agent/api_request_hooks.py:161-196`; it is called after `classify_api_error()` and before recovery in `agent/turn_api_error.py:109-132`.
* Valid plugin hook names: `hermes_cli/plugins.py:107-125`.
* Stable source snapshot: https://github.com/NousResearch/hermes-agent/tree/f159e581c7afd22a5c94652c569e3859f1b994d2

## Present live-agent seam

Do **not** mutate only `agent.model` / `agent.provider` / `agent.reasoning_config`. Hermes supplies `AIAgent.switch_model(new_model, new_provider, api_key='', base_url='', api_mode='', capabilities=None)` (`agent/agent_runtime_helpers.py:2100-2133`, forwarded by `run_agent.py:458`). It atomically rebuilds the client, clears transport cache, reloads credential-pool state, recalculates context-compressor state, updates request/cache flags and persists the runtime route; failures roll back.

A route crossing providers must provide a fully resolved runtime target: `model`, `provider`, `api_key`, `base_url`, `api_mode`, optional `capabilities`. `switch_model` explicitly refuses a provider change with no resolved destination `base_url` (`agent/agent_runtime_helpers.py:1918-1958`). The router can then set `agent.reasoning_config` to its explicit per-route dict (for example `{"effort": "medium"}`) **after** a successful switch; reasoning is separately stored in Hermes' primary-runtime snapshot (`agent/agent_runtime_helpers.py:2024-2058`).

## Minimum isolation contract for `integrations/hermes.py`

Keep all Hermes imports/probing/mutation in this adapter. Core policy should see only:

```python
@dataclass(frozen=True)
class TurnInput:
    session_id: str
    user_message: str
    history: Sequence[Mapping[str, Any]]
    current: RouteIdentity  # model, provider, base_url, api_mode
    correlation: Mapping[str, str]  # task_id, turn_id, api_request_id when present

@dataclass(frozen=True)
class RouteTarget:
    model: str; provider: str; api_key: str; base_url: str; api_mode: str
    reasoning_config: Mapping[str, Any] | None = None
    capabilities: Mapping[str, Any] | None = None

class HermesRoutingAdapter(Protocol):
    def native_override_available(self) -> bool: ...
    def turn_input_from_hook(self, **payload: Any) -> TurnInput: ...
    def apply(self, live_agent: Any, target: RouteTarget) -> None: ...
    def api_failure_from_hook(self, **payload: Any) -> ApiFailure: ...
```

`apply()` policy: use a discovered future-native override only if its explicit contract supports route selection; otherwise call the current agent's `switch_model(...)`, then assign `reasoning_config`. The `api_request_error` path should produce telemetry/policy state or let Hermes-configured fallback act; it cannot reliably substitute a provider through a hook return.

## Local-install note

The host research shell had neither a `hermes` executable nor importable `hermes` Python module, and `/Users/giovanni/.hermes` contained no Hermes core checkout. The source anchors above are from a fresh, read-only clone of the official repository at the recorded commit; no Hermes installation was modified.
