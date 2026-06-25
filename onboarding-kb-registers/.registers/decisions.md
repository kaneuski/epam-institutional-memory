---
type: decision
tier: core
lifecycle: evolving
id_prefix: DEC
singleton_key: null
source_doc_types: ["policy-doc", "team-directory-update"]
last_updated: 2026-06-24
---

# Decisions

Explicit decisions, their rationale, and the registers they changed.

---

## DEC-001: Replace SRE-pairing access model with certification + JIT access

| Field | Value |
|-------|-------|
| status | active |
| decision_type | policy |
| date | 2026-05-15 |
| participants | PER-001, PER-003 |
| trigger | INC-001 |
| reversibility | costly-to-reverse |

**Decision:** Replace the SRE-pairing-session requirement for read-only production access with a self-paced online certification ("Prod Access Foundations") plus just-in-time access, scoped to 4-hour windows and requested directly through the IAM platform instead of a Slack ticket. Tenure requirement for read-only reduced from 2 weeks to 3 working days.

**Rationale:** [DIRECT] The pairing-session model was built for a 40-engineer org; at 280 engineers the backlog grew to 3 weeks. The new model is auditable, faster, and aligns with SOC2 controls.

**Alternatives eliminated:** [INFERRED] Continuing the manual SRE-pairing model — rejected as a bottleneck that didn't scale with headcount.

**Consequences:** Engineers can request read-only access from day 4 of tenure. Existing read-only holders under the old policy retain access only through 2026-06-30, after which they must complete the new certification or lose it.

### References
- Triggered by: [INC-001](incidents.md#inc-001)
- Produces: [POL-002](policies.md#pol-002)
- Participants: [PER-001](people.md#per-001), [PER-003](people.md#per-003)

---

## DEC-002: May 2026 Engineering leadership re-org

| Field | Value |
|-------|-------|
| status | active |
| decision_type | org-change |
| date | 2026-04-15 |
| participants | PER-002, PER-004, PER-005, PER-012 |
| trigger | null |
| reversibility | costly-to-reverse |

**Decision:** Anika Reddy moves from Head of Engineering into a newly created Chief AI Officer role (effective 2026-04-01); Yuki Tanaka becomes Head of Engineering (effective 2026-04-15); Tom Bryce is promoted to Head of Platform, replacing Yuki; Priya Shah becomes Engineering Ops Lead, replacing Tom, having moved over from leading the Web team. As a consequence, tech-lead ownership of payment-service and frontend also changes hands (Tom Bryce → Maya Patel; Priya Shah → Daniel Okonkwo), since both outgoing leads were stepping into new leadership roles.

**Rationale:** [UNVERIFIED] Not stated in the source document beyond labeling it "the May 2026 re-org" — no strategic justification given for the Chief AI Officer role or the leadership chain reshuffle.

**Alternatives eliminated:** null — not stated.

**Consequences:** New leadership chain across Engineering, Platform, and Engineering Ops. Two services (payment-service, frontend) get new tech leads as a side effect of their prior leads moving into the new roles.

### References
- Produces: [POS-006](role-assignments.md#pos-006), [POS-007](role-assignments.md#pos-007), [POS-008](role-assignments.md#pos-008), [POS-009](role-assignments.md#pos-009), [OWN-006](service-ownership.md#own-006), [OWN-007](service-ownership.md#own-007)
- Participants: [PER-002](people.md#per-002), [PER-004](people.md#per-004), [PER-005](people.md#per-005), [PER-012](people.md#per-012)

---
