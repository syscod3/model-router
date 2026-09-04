# Hermes provider and model contract research

**Scope:** local Hermes Agent `v0.19.0` inspection on 2026-09-05 plus official Hermes documentation/source. No configuration, credentials, or network model requests were changed or made.

## Use these canonical provider identifiers

| Product name in bootstrap notes | Canonical Hermes provider slug | Status verified locally | Model discovery contract |
|---|---|---|---|
| OpenAI Codex | `openai-codex` | Bundled provider; OAuth credential is present; active main provider | `hermes model --refresh` / picker calls the account-scoped Codex model endpoint. Source fallback is Codex config/cache/bundled catalog. |
| z.ai / GLM | `zai` | Bundled provider; API-key credential is present, but not selected in `config.yaml` | Picker uses the API-key provider profile's live model discovery and merges curated entries; cache refresh is via `hermes model --refresh`. |
| LM Studio | `lmstudio` | Documented and implemented in the installed picker/runtime; no local LM Studio configuration or credential was found | The configured server's native `GET /api/v1/models`; Hermes uses each non-embedding entry's `key`, falling back to `id`. |
| OpenRouter | `openrouter` | Bundled provider; no configured credential or selected model found | Curated remote model manifest/cache for picker plus the provider's `https://openrouter.ai/api/v1/models` API; `--refresh` bypasses picker caches. |
| DeepInfra | `deepinfra` | Bundled provider; no configured credential or selected model found | `GET https://api.deepinfra.com/v1/openai/models?filter=true&sort_by=hermes` (or `DEEPINFRA_BASE_URL` override), then retain chat-tagged models. Authentication is optional for public catalog entries. |

Aliases are not the configuration contract: `z.ai`/`z-ai` are aliases of `zai`; `codex` is an alias of `openai-codex`; `or` is an alias of `openrouter`; DeepInfra aliases include `deep-infra` and `deepinfra-ai`.

## Locally configured facts (not guesses)

- Active main/delegation routing is **`openai-codex` + `gpt-5.6-terra`**.
- Image generation is **`openai-codex` + `gpt-image-2-medium`**.
- A `zai` credential is registered, but `zai` has no selected/configured main model.
- No model/provider selection was found for `lmstudio`, `openrouter`, or `deepinfra`.
- Existing local caches for provider models, the curated catalog, and Codex models are present, but were intentionally not read: a cache is discovery evidence, not proof that a model is usable for the current account.

## Validation rule for model-router bootstrap

1. Store only the provider slugs above, never display names such as “OpenAI Codex,” “z.ai,” or “LM Studio.”
2. Treat all bootstrap model names—including the README's five default tiers—as **human-readable candidate placeholders** until their exact provider-scoped IDs appear in the relevant Hermes picker/discovery result. They must not be marked verified merely because they look like vendor model names.
3. For a non-interactive, no-quota verification pass, use local config/cache inspection only. To validate availability later, run `hermes model --refresh`, select the authenticated provider, and copy the exact displayed ID; do not send a model request. The command's help explicitly says it wipes picker cache and re-fetches provider `/v1/models` lists. It may write cache state, so it was not run for this research ticket.
4. `/model` is a session switch command for already configured providers; it is not the setup/discovery mechanism for a new provider. `--global` persists a choice, so do not use it for discovery.

## Sources

- Installed CLI: `/Users/giovanni/.hermes/venv/bin/hermes --version`, `hermes model --help`, and safe config/auth metadata inspection (no values printed).
- Installed source: `hermes_cli/models.py` (`provider_model_ids`, LM Studio probe, DeepInfra catalog); `hermes_cli/codex_models.py`; `providers/__init__.py` registry, all from Hermes Agent `v0.19.0`.
- Official docs: [AI Providers](https://hermes-agent.nousresearch.com/docs/integrations/providers/), [Model Catalog](https://hermes-agent.nousresearch.com/docs/reference/model-catalog), [Configuring Models](https://hermes-agent.nousresearch.com/docs/user-guide/configuring-models), and [Provider Runtime Resolution](https://hermes-agent.nousresearch.com/docs/developer-guide/provider-runtime/).
- Official source: [NousResearch/hermes-agent `hermes_cli/models.py`](https://github.com/NousResearch/hermes-agent/blob/main/hermes_cli/models.py).
