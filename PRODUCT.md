# SANO product

SANO is an open-source, self-hosted personal and family health workspace. It helps people keep health history together, find earlier results, prepare for visits, and share a Person's information through explicit grants.

## Product purpose

People and families should be able to organize health context without depending on a closed health-AI platform. Source material remains inspectable, derived facts remain traceable to their sources, and a person reviews candidate facts before they become canonical records.

## Responsible assistance

An optional assistant can explain selected authorized evidence, draft summaries, and prepare questions. External model disclosure is minimized to explicitly selected context and requires consent for each action. Each execution is validated and receipted. A local inference option is available. Model output does not create diagnoses or mutate canonical health records.

## Product boundaries

SANO is not an AI doctor, diagnosis or treatment authority, dosage recommender, medication start/stop authority, clinical decision-support system, or clinically validated software. Self-hosting, authorization, and backups remain under the operator's control.

## Product identity

SANO is the product and GitHub repository name. `open-care-proof-kit` is the stable Python package identifier, while `opencare-*` identifiers remain stable for protocols and schemas.

## Design principles

- Keep the active Person and consequences of access visible.
- Preserve original sources, provenance, review, and audit.
- Make disclosure, high-risk grants, and exports explicit before action.
- Do not expose hidden or unauthorized Persons through totals or empty states.
- Keep the synthetic demo separate from actor-scoped user data.
- Use accessible forms, keyboard-visible focus, readable contrast, semantic status, and reduced-motion behavior.
