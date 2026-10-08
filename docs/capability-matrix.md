# SANO Capability Matrix

This matrix describes the published SANO product and the additional local
post-main refinements. Public GitHub `main` at the dated baseline `84fb682`
already contains SANO-X2 and Product Core schema v13. The seven commits through
`089a5eb` are now integrated in the published main and do not introduce those
capabilities. The published release tags are `v0.1.0`, `v0.2.0`, and the
stable `v0.3.0` release dated 8 October 2026.

P3 is part of the published baseline.

| Capability | Status | Repository evidence or boundary |
|---|---|---|
| People | `PARTIAL` | Actor-scoped Product Core People are persisted and explicitly owner-created; broader health entities remain demo-only. |
| Family relationships | `IMPLEMENTED` | `app/family_access/` persists and policy-filters Families, memberships, and relationships without treating them as grants. |
| Health vault entities | `DEMO_ONLY` | `app/health_vault/models.py`, `app/health_vault/loader.py`, `app/health_vault/read_model.py` |
| Local JSON vault | `PARTIAL` | `app/health_vault/loader.py`, `app/health_vault/runtime_loader.py`, `app/config.py`, `app/main.py`, `docs/examples/local-family-vault.template.json` |
| Persistent editable vault | `PARTIAL` | Product Core medication/condition/lab and Visit lifecycle, active People, Family permissions, and actor-scoped JSON API are implemented; other fact families remain out of scope. |
| Document upload | `PUBLISHED` | Authenticated Person-scoped PDF/TXT/JPG/PNG upload; original bytes are immutable. Upload alone does not create a reviewed health record. |
| SANO-A1 / X1 document archive | `PUBLISHED; SUPERSEDED BY X2` | `/documents` saves originals immediately, groups by document date, supports title/date metadata and original PDF/TXT view/download. SANO-X2 is also published on `main`. `app/product_core/document_dates.py`, `app/templates/documents.html`, `app/static/sano_documents.js`. |
| SANO-X2 Document Understanding | `PUBLISHED` | Migration v13 persists text-processing and consented document summary/Q&A state. PDF/TXT/JPG/PNG originals remain immutable; bounded local OCR uses Tesseract `rus+eng`; actions use selected document text/page references and require explicit consent. They do not promote health facts. |
| Product Core schema | `v13 PUBLISHED` | Public-main migration v13 adds document text-processing and consented summary/question state, preserving the earlier migration chain. |
| Immutable source storage | `IMPLEMENTED` | `app/product_core/services.py`, `app/product_core/migrations.py`, source integrity tests, and P3 genetics source hashes. |
| Extraction and OCR | `PUBLISHED` | Bounded local OCR for image and scanned-PDF inputs with Russian and English language data (`rus+eng`); Docker includes Tesseract and both packs. Document descriptions and questions are separate consent-gated provider actions. |
| Review inbox | `IMPLEMENTED` | P2 workspace: unified medication + condition + lab candidate review at `/workspace`; broader fact families remain unsupported. |
| Canonical confirmed records | `IMPLEMENTED` | P1/P2: all three fact families (medication/condition/lab) confirm transactionally into `canonical_records` with typed detail; no other fact families. |
| Timeline | `IMPLEMENTED` | P2 workspace: medication/condition/lab confirmation and correction events with readable current/history presentation; demo read model remains separate. |
| Medications | `PARTIAL` | Product Core medication candidate/canonical lifecycle in `app/product_core/`; synthetic Health/Family Vault remains demo-only |
| Conditions | `IMPLEMENTED` | Source-backed recorded-condition lifecycle in `app/product_core/` (candidate → provenance → review → canonical condition record); explicitly a record, not a diagnosis. |
| Labs | `IMPLEMENTED` | Source-preserving lab lifecycle in `app/product_core/` (typed text values, source flags as-provided); no unit conversion or interpretation. |
| Encounters / visits | `PARTIAL` | Persistent Person-scoped Visits in `app/product_core/`; synthetic Health/Family Vault visits remain demo-only |
| Questions | `PARTIAL` | Persistent user-authored Visit Questions in `app/product_core/`; no generated answers or broad question workspace |
| Visit preparation | `IMPLEMENTED` | P2 workspace supports persistent Visits, Questions, Visit Brief revisions, all-three-type confirmed-evidence selection, preparation notes, restore history, and audited Markdown export; content schema v2 and readable v1 revisions. |
| Guarded chat | `IMPLEMENTED` | Normal lifespan wiring for `/api/chat/prepare` → exact consent → execute → scoped receipt; source-backed Product Core projection, CSRF/session boundary, replay/revocation checks, and refusal policy. No clinical correctness claim. |
| External LLM provider | `IMPLEMENTED` | Provider contract/configuration adapters bind provider identity and bounded structured output to consent and receipts. OpenRouter/DeepSeek summary and document Q&A production checks, attribution, citations, and receipts are operator-confirmed PASS results. OpenAI live X2 is unverified. See the dated validation record. |
| Model provider portability | `IMPLEMENTED` | Provider-independent G2 execution contract and shared `build_provider_execution_request` in `app/agent/providers/contract.py`; loopback/non-loopback disclosure classification in `app/agent/providers/endpoints.py`; same G1/G2 validation and Receipts for every provider; conformance and trust suites in `tests/provider_*` |
| Self-hosted model runtime | `IMPLEMENTED; OPERATOR-CONFIRMED` | A local-model inference path is available without an external API. The operator confirms local-model tests; model identifier, hardware, and benchmark results are not recorded. |
| Portable trust package (Sentient G4) | `IMPLEMENTED` | Generic trust layer with a stable public API in `app/agent_trust/api.py` and zero OpenCare coupling; generic `AuthorizationAdapter` Protocol with the OpenCare adapter in `app/agent/trust_adapter.py`; deterministic JSON Schemas in `schemas/agent-trust/` with export script and drift test; synthetic offline fixture corpus in `fixtures/agent-trust/` with deterministic regeneration; `opencare-trust` CLI (also `python -m app.agent_trust.cli`) with deterministic exit codes and no live-authorization minting path |
| Agent Plugins v1 skill package | `IMPLEMENTED` | Skill-only package at `agent-plugins/opencare-trust/` with strict 1.0.0 `plugin.json` and a `skills/` tree (including the canonical `opencare-health-agent` skill); deterministic build from the canonical skill sources with a drift test, no symlinks, package containment and secret/path scans, and no `mcp.json` |
| MCP adapter | `OUT_OF_SCOPE` | No MCP server; this remains outside the completed product sequence. |
| Agent Skills interoperability | `IMPLEMENTED / VERIFIED` | G5 evidence verifies OMP 17.3.5 and Hermes Agent 0.19.0 interoperability. |
| Root Agent Plugins interoperability | `EXTERNAL VALIDATION PENDING` | Machine gate remains exactly `READY_FOR_SECOND_CLIENT_SMOKE`; external two-client root-plugin evidence is not claimed as PASS. |
| Citation validation | `IMPLEMENTED` | `app/agent/validation.py`, `app/agent/service.py`, `app/agent/portable.py`, `tests/test_agent.py`, `tests/test_portable_agent_cli.py` |
| Audit | `IMPLEMENTED` | Metadata-only agent/report audit, current Product Core access audit, genetics review/research receipts, and denial-audit fail-closed behavior. |
| Evaluations | `IMPLEMENTED` | Deterministic G1/G2/G5/P1/P2/D1/P3 reviewers and focused tests; `python -m evals.p3_review` is offline. |
| Wheel distribution | `IMPLEMENTED` | The source checkout and non-editable wheel startup have accepted validation evidence; runtime assets are packaged. |
| Docker self-hosted distribution | `IMPLEMENTED / LIVE VALIDATION BLOCKED` | Existing Dockerfile and Compose paths are reconciled for current Product Core persistence, ephemeral sessions, Caddy proxying, non-root runtime, and optional provider configuration; live Engine acceptance remains blocked when Docker Engine is unavailable. |
| Constrained Python 3.12 | `IMPLEMENTED` | `constraints/python312.txt` pins the accepted Python 3.12 release/test environment. |
| PGx | `IMPLEMENTED/PARTIAL` | Deterministic reviewed genetics finding × exact confirmed medication intersection; association display only, no dosage/start/stop action. |
| Genetics source | `IMPLEMENTED` | Immutable local consumer-genotype Source, bounded TXT import, current Product Core dataset/observation/finding/research tables; VCF remains demo-only. |
| Genetics Workspace | `IMPLEMENTED` | `/genetics` live Person-scoped surface loading real authorized data; synthetic demo content removed; EN/RU localized; empty/access-denied states truthful. |
| Research Mode | `IMPLEMENTED` | Offline deterministic Evidence/Explore contracts with structured epistemic labels, citations, counterevidence, and no canonical mutation path. |
| Agent tools | `PARTIAL` | Existing trust tools remain unchanged; Research Mode uses a minimized genetics packet and metadata-only receipt boundary. |
| Family permissions | `IMPLEMENTED` | Legacy family-access generations remain frozen; separate explicit `genetics.read/write/research/compare/export` grants are required and revocable. |
| Username/password login | `IMPLEMENTED` | `/login` uses the existing local credential and server-side session boundary; safe browser redirects preserve a relative next path. |
| Invitation-based family sharing | `IMPLEMENTED` | `/invite` remains body-only and hash-backed; existing-account acceptance and invitation account creation preserve owner/caregiver semantics. |
| Optional public self-registration | `IMPLEMENTED` | Disabled by default; after bootstrap and explicit `OPENCARE_PUBLIC_REGISTRATION=true`, creates only Actor + own Person + owner assignment + own-Person link. |
| Email verification / password recovery | `NOT IMPLEMENTED` | No email infrastructure or self-service recovery flow. |
| Internet-scale abuse controls / SaaS tenancy | `NOT CLAIMED` | Controlled self-hosted account creation is not public SaaS readiness. |


## Reading rules

`IMPLEMENTED` means executable runtime behavior is present and covered by
inspected tests or configuration. `PARTIAL` means a bounded subset exists but
the capability is not a complete Product Core workflow. `DEMO_ONLY` means the
behavior is synthetic, read-only, reference-only, or otherwise not a complete
user-owned feature. `PLANNED` means approved future work. `OUT_OF_SCOPE` means
explicitly excluded from the current phase.

The statuses do not imply clinical validation or production readiness.
