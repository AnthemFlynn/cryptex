Crystal clear. You want session-scoped, in-memory secret handling only—no persistence, no static/long-lived secret storage in the core. All persistence, external stores, or static secrets get punted to optional plugins. You want the base library to be purely ephemeral: secrets and their placeholder mappings are created, used, and obliterated with each session.

Let’s revise the PRD accordingly—trimming away all references to static secret storage, at-rest encryption, and long-term mapping. The focus is session-only. Plug-in extensibility is emphasized for any persistence or advanced secret source integration.

⸻

Codename Library: Session-Scoped AI/LLM Secret Middleware

Senior Software Architect | Python 3.13+ | FastMCP Integration | Zero Implementation Baseline

⸻

Executive Summary

Codename is an ephemeral, in-memory secret sanitization and temporal isolation engine for AI/LLM applications.
No secret or mapping persists beyond the scope of a session—not on disk, not in logs, not in cache.
All extended storage, cloud integrations, or static secrets are delivered via optional plugins, keeping the core library simple, lightweight, and ultra-secure.

Purpose: Prevent accidental or malicious LLM access to any sensitive value by redacting secrets with short, random, per-session placeholders, then restoring them after model inference.
When the session ends, all secret data and mappings are wiped—no residue, no audit risk.

⸻

Architecture and Design Principles
	•	Session-Scoped Only:
	•	All secret registration, placeholder generation, and mapping occurs in memory and is destroyed with the session context.
	•	No disk, no database, no persistent cache—no exception.
	•	No Long-Term Storage:
	•	No built-in support for static/long-lived secrets.
	•	All external secret stores, file sources, or static configs must be loaded via plugin (optional, not required, and not part of the session core).
	•	Simple Placeholder Scheme:
	•	Placeholders are randomly generated (default 5 digits, e.g., <43210>) and unique within a session.
	•	Mapping to secrets is kept in the session context and never serialized.
	•	Extensible Plugin Model:
	•	The library exposes hooks for plugins to handle:
	•	Loading secrets from static stores
	•	Integrating with cloud vaults
	•	Persisting session logs or secrets (if absolutely necessary, but never by default)

⸻

Core Workflow
	1.	Session Start:
	•	User/developer initiates a secure session context.
	2.	Secret Registration:
	•	Secrets are registered for the session (manually or via plugin).
	3.	Sanitization:
	•	Input data is scanned; secrets replaced with per-session placeholders (e.g., <39817>).
	4.	AI/LLM Processing:
	•	The prompt with placeholders is sent to the LLM; no real secrets ever leave session context.
	5.	Resolution:
	•	After AI processing, placeholders are swapped back for the original secrets using the session mapping.
	6.	Session End:
	•	All mappings and secret data are purged from memory. Session context is destroyed.
	7.	Plugins (Optional):
	•	If external secret retrieval or persistence is desired, plugins may handle it—but the base library doesn’t touch disk or retain anything.

⸻

Example Code/Interface

with codename.secure_session() as session:
    session.register_secret("api_key", value="sk-xxx")
    sanitized = session.sanitize(input_data)
    ai_result = llm(sanitized)
    resolved = session.resolve(ai_result)
# After the `with` block, all secrets and mappings are gone


⸻

Config Example (codename.toml)

[placeholder]
pattern = "<{digits}>"
length = 5

[plugin]
enabled_plugins = ["cloud_secrets", "audit_logger"] # Optional; base library has zero persistence


⸻

Core Feature List
	•	Ephemeral Session Contexts
	•	Random, Per-Session Placeholders
	•	In-Memory Only Secret Handling
	•	No Persistence—Ever
	•	Strict Type Safety, Async-Ready
	•	Extensible Plugin Hooks for Any Persistence or Static Secret Features

⸻

Security and Compliance
	•	Session isolation by default: No cross-session leakage.
	•	No logs or traces with secrets: All audit/logging plugins are opt-in and can be configured for in-memory-only.
	•	Red Team/Audit support: Adversarial test suite for session-only operations.
	•	Any risk of data retention is only introduced by plugins, not by core.

⸻

Success Criteria
	•	No secret or placeholder mapping exists outside of a live session.
	•	Sanitization and resolution operate under 5–10ms per op.
	•	No built-in disk I/O or static storage.
	•	Plugin API is documented, stable, and allows for external secret sources or audit logging as needed.

⸻

Not Included in Core (Plugin-Only)
	•	Static secret files or vault integration
	•	Persistent audit or compliance logs
	•	Secret rotation, external KMS/HSM
	•	Cross-session secret reuse or retention

⸻

Summary Table

Feature	Core	Plugin Only
In-memory secrets/mapping	Yes	
Session-scoped placeholder	Yes	
Disk/database cache		Yes
Static secrets, cloud vaults		Yes
Audit logging		Yes
Secret rotation		Yes


⸻

In short:
This is session-scoped, ephemeral AI/LLM secret protection—no persistence, no residue, no excuses. Anything persistent lives outside the core as a plugin.
