# Rules Comparison and Merge Report

## 1. Purpose

This report documents how the original `Pasted text.txt` rules and the expanded `GLOBAL_AGENT_RULES.md` were combined into `GLOBAL_AGENT_RULES_MERGED.md`.

The goal of the merge was to retain the user's explicit requirements while organizing them into a more complete, reusable set of standards for AI coding agents.

## 2. Comparison summary

The original rules supplied the user's concrete expectations and project-wide defaults. The expanded rules added structure, clearer engineering workflows, and broader implementation guidance.

| Area | Original rules | Expanded rules | Merge decision |
|---|---|---|---|
| Agent behavior | User-defined expectations for how coding agents should work | More structured workflow and implementation guidance | Preserve explicit user requirements and use the expanded structure to organize them |
| UI and visual design | Professional, clean UI; simple palettes; no glow effects; light/white default; avoid cramped tabs | Broader design consistency and usability guidance | Retain the visual constraints and incorporate the wider usability guidance |
| UI documentation | Keep UI decisions, bookmarks, and documents separately documented | More systematic documentation expectations | Preserve the separate documentation requirement and clarify that bookmark identifiers and UI decisions must be recorded |
| Hardware and firmware | Arduino C++ by default; do not use PlatformIO unless project documentation says otherwise | Broader implementation and reliability guidance | Keep Arduino C++ as the default and retain the project-documentation exception |
| Device provisioning and connectivity | AP provisioning, credential handling, fallback behavior, reconnection and alert timing | More structured reliability and recovery expectations | Preserve the specified behavior and timings as configurable defaults, not universal constants |
| Sensor and process design | Keep sensor/process behavior independent and retry in the background | Broader modularity and fault-handling guidance | Combine as independent modules with non-blocking recovery |
| Privacy and security | Data export/deletion, policies, consent, permissions, SDK review, security requirements | Broader secure-development practices | Combine without removing the user's explicit privacy requirements |
| Performance | Concrete frontend, backend, database, API, and abuse-prevention optimizations | More systematic performance engineering guidance | Consolidate overlapping items and retain the concrete optimization checklist |
| Architecture | Separate database and application infrastructure where appropriate; encryption, authentication, environment separation, secrets | Broader architecture and deployment guidance | Keep the conditional separation requirement and combine with secure configuration practices |
| Documentation | Document changes and everything built | More systematic implementation and verification reporting | Retain the requirement and make it part of the normal completion workflow |

## 3. Explicit requirements retained

The merged rules retain the following specific requirements from the user's original rules.

### UI and design
- Build neat, professional interfaces.
- Do not use emojis unless project documentation explicitly requires them.
- Do not use glowing edges or decorative glow effects.
- Use a simple, clearly defined color palette.
- Use a white/light background by default unless project requirements specify otherwise.
- If a palette has not been specified and the choice materially affects the design, ask the user rather than inventing a complex palette.
- Do not compress or overcrowd tabs. Prefer grouping under a parent item or using a collapsible sidebar.
- Keep UI decisions, bookmarks, and document-related information separately documented.

### Hardware and firmware
- Use Arduino C++ by default for Arduino/ESP32 firmware.
- Do not introduce PlatformIO unless project documentation or the user explicitly requires it.
- Use `tone()` and `noTone()` for buzzer behavior where appropriate.
- Use access-point provisioning rather than hardcoding Wi-Fi credentials.
- A device on first setup should expose its provisioning access point immediately.
- A previously configured device should attempt its saved network first and fall back to its access point after the specified boot timeout.
- Use background retry behavior so connectivity recovery does not block unrelated device functions.
- Preserve the specified default recovery and alert timings: retry for up to 30 minutes, issue alerts at 10-minute intervals, and use the 5-minute device-unavailability threshold only after normal operation has been confirmed.
- Make timing values configurable where the implementation allows it.
- Where a SIM module is available, use SMS as an additional recovery/alert channel when appropriate.
- Provide a physical means to reset or reconfigure provisioning where required.
- Keep sensor and process modules independent so one failing subsystem does not unnecessarily stop the rest of the device.

### Privacy, security, and responsible product behavior
- Support appropriate user data export and deletion requests.
- Provide applicable terms of service and privacy policy documentation.
- Do not create fake reviews, unsupported product claims, unnecessary data collection, dark patterns, or hidden fees.
- Check color contrast and accessibility.
- Review third-party SDKs and their data practices.
- Provide meaningful alternative text for relevant images.
- Implement consent, forms, cookie notices, and policy disclosures where applicable.
- Explain why permissions are needed and obtain user acceptance before accessing them.

### Performance and reliability
- Cache API responses and expensive queries where appropriate.
- Index database fields used for frequent queries.
- Compress images and API payloads.
- Use loading skeletons where they improve perceived responsiveness.
- Split bundles and defer non-critical scripts.
- Use a CDN where appropriate.
- Lazy-load suitable content.
- Minify JavaScript and CSS for production.
- Use database connection pooling where appropriate.
- Remove unused dependencies.
- Paginate long lists.
- Debounce frequent event handlers.
- Avoid N+1 database queries and unnecessary UI re-renders.
- Apply request limits, rate limiting, throttling, and abuse protection.
- Use message queues where asynchronous workloads justify them.

### Architecture and security
- Separate database infrastructure from application/web infrastructure when the deployment needs it; do not impose unnecessary separation on small projects.
- Encrypt data in transit and at rest where supported and appropriate.
- Use strong authentication and authorization.
- Keep development, testing, and production credentials separate.
- Store secrets securely; do not commit credentials or hardcode them into source code.
- Research relevant security guidance, books, and incident lessons when useful, and apply the relevant hardening measures.

### Documentation
- Document every meaningful change.
- Document what was built, how it works, and important implementation decisions.
- Keep documentation aligned with the actual implementation.

## 4. Conflict and precedence decisions

The merged rules should be interpreted using this order:

1. Explicit instructions from the user for the current task.
2. Applicable project documentation, requirements, and established architecture.
3. The global rules in `GLOBAL_AGENT_RULES_MERGED.md`.
4. The coding agent's ordinary defaults.

The global rules are defaults, not permission to contradict a project's documented requirements. For example, Arduino C++ is the default, but a project that explicitly requires another firmware toolchain takes precedence.

Timing values for connectivity and alerts are defaults supplied by the user. They should be configurable where practical and should not be treated as universal values for every device.

Rules that do not apply to a project should be marked `N/A` with a short reason rather than silently ignored.

## 5. What the merge improves

- Brings the user's concrete requirements into one canonical rules document.
- Groups related rules so agents can locate the relevant requirements.
- Reduces repeated or overlapping guidance.
- Makes defaults and exceptions clearer.
- Establishes precedence between user instructions, project documentation, and global defaults.
- Makes the rules reusable across multiple coding agents and projects.

## 6. Important implementation note

A single master Markdown file can serve as the source of truth, but different coding agents use different global instruction mechanisms and file locations. Each agent must be configured to read the master file or a generated native-format copy of it. Adding the file to a ChatGPT conversation or Project does not automatically configure local coding applications.

When the master rules are changed, regenerate or refresh any agent-specific copies so that all agents use the same current version.

## 7. Scope and verification note

This report records the merge decisions and requirements documented during the rules consolidation. It is not a line-by-line diff, and it does not claim that every sentence in the two source documents was independently reconciled in this regeneration. For a literal line-by-line audit, both source files must be available for direct comparison.
