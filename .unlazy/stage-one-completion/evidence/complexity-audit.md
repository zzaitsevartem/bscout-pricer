# Lightweight Ponytail complexity audit

Scope: a targeted whole-project inventory of backend/frontend production source, not a line-by-line review. Searched for factories, strategies, adapters, protocols, abstract bases and pure async forwarding wrappers; reviewed the modified sanitizer separately.

- No confirmed over-engineering cut in the sampled patterns. `BaseParser`, `Mailer`, and `Notifier` have multiple implementations. `VerificationMailer` and `VKClient` each have a production implementation but are injected contracts used by test doubles; removing them would reduce testability without a confirmed maintenance win.
- The new `_safe_validation_message` helper is a small shared policy point used by the global 422 handler. Its branches distinguish field-required, email, password, length, pattern, and fallback cases; compressing it into a dense table would save little and make field-specific behavior less direct.
- Controller `return await` wrappers inspected are route/dependency boundaries, not pass-through functions that can be deleted without changing FastAPI behavior.

No unrelated simplification or dependency removal is justified by this scan. No speculative changes made.

Net verified cut: -0 lines, -0 dependencies.
