---
type: policy
tier: core
lifecycle: evolving
id_prefix: POL
singleton_key: "scope"
source_doc_types: ["policy-doc"]
last_updated: 2026-06-24
---

# Policies

Versioned governance documents. At most one status:active entry per scope.

---

## POL-001: Production Access Policy

| Field | Value |
|-------|-------|
| status | superseded |
| scope | prod-access |
| effective_date | 2026-01-01 |
| superseded_date | 2026-05-15 |
| owner | PER-001 |
| supersedes | null |
| superseded_by | POL-002 |
| source_incident | null |
| migration_deadline | null |

**What it governs:** Production access at BTS-Synthetic, granted in three tiers (read-only, read-write, privileged).

**Statement:** Read-only requires 2 weeks of tenure plus a completed pairing session with an SRE; used for debugging, observability, and log access. Read-write requires 6 weeks of tenure, read-only level, tech lead sign-off, and SRE sign-off; used for configuration changes and restart commands. Privileged requires on-call certification (typically 12 weeks); used for incident response, emergency rollback, and IAM changes. Standard read-only request flow: engineer opens a ticket in `#sre-access-requests`, tags their manager and the SRE on rota, the SRE schedules a 30-minute pairing session within 2 working days, then files the access via Okta — provisioning typically completes within 4 hours. See [EXC-001](exceptions.md#exc-001) for the urgent-access carve-out.

**Review cadence:** Reviewed quarterly by Security and SRE leads. Last review: 2025-12-15.

### References
- Owner: [PER-001](people.md#per-001)
- Superseded by: [POL-002](policies.md#pol-002)
- Modified by: [EXC-001](exceptions.md#exc-001)

---

## POL-002: Production Access Policy — Updated

| Field | Value |
|-------|-------|
| status | active |
| scope | prod-access |
| effective_date | 2026-05-15 |
| superseded_date | null |
| owner | PER-001, PER-003 |
| supersedes | POL-001 |
| superseded_by | null |
| source_incident | INC-001 |
| migration_deadline | 2026-06-30 |

**What it governs:** Production access at BTS-Synthetic, granted in three tiers (read-only, read-write, privileged). Same scope as POL-001.

**Statement:** Read-only: complete the self-paced "Prod Access Foundations" course (90 minutes) in the BTS Learning portal, pass the assessment, then request access through the IAM platform. Access is granted just-in-time, scoped to a 4-hour window per request; engineers re-request as needed. The engineer's manager is notified of each request but sign-off is only required for the initial certification — no per-request manager or SRE sign-off, no Slack ticket, no pairing session. Tenure requirement reduced from 2 weeks to 3 working days; engineers can certify and request access from day 4. Read-write and privileged requirements are unchanged from POL-001 (read-write: 6 weeks tenure + read-only level + tech lead sign-off + SRE sign-off; privileged: on-call certification, ~12 weeks).

**What changed and why:** Following [INC-001](incidents.md#inc-001) (the April incident review, PROD-INC-04-2026), the SRE-pairing-session model was eliminated — it had become a bottleneck (3-week backlog) at 280 engineers, up from the 40-engineer org it was designed for. Replaced with online certification + JIT access, centralized in the IAM platform instead of Slack, for auditability and SOC2 alignment. Engineers who already hold read-only access under POL-001 retain it only through the `migration_deadline` (2026-06-30), after which they must complete the new certification or lose access.

**Review cadence:** [UNVERIFIED] Not restated in this update — see POL-001 for the prior quarterly Security/SRE review cadence; assume unchanged unless a future document says otherwise.

### References
- Supersedes: [POL-001](policies.md#pol-001)
- Triggered by: [INC-001](incidents.md#inc-001)
- Decision: [DEC-001](decisions.md#dec-001)
- Owner: [PER-001](people.md#per-001), [PER-003](people.md#per-003)
- Governs: [AT-001](access-tiers.md#at-001), [AT-002](access-tiers.md#at-002), [AT-003](access-tiers.md#at-003)

---
