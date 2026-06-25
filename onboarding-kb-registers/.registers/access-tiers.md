---
type: access-tier
tier: domain
lifecycle: evolving
id_prefix: AT
singleton_key: "tier_name"
source_doc_types: ["policy-doc", "onboarding-handbook"]
last_updated: 2026-06-24
---

# Access Tiers

The access-level taxonomy, with eligibility criteria pointing at the currently governing policy.

---

## AT-001: read-only

| Field | Value |
|-------|-------|
| tier_name | read-only |
| governing_policy | POL-002 |

**Current eligibility:** 3 working days of tenure, plus completion of the "Prod Access Foundations" certification (self-paced, 90 minutes) and passing assessment. Access is granted just-in-time, scoped to a 4-hour window per request, via the IAM platform — no SRE pairing session, no Slack ticket. Updated 2026-05-15 per [POL-002](policies.md#pol-002), supersedes the prior 2-week-tenure + SRE-pairing criteria.

**Use cases:** Debugging, observability, log access.

### References
- Governing policy: [POL-002](policies.md#pol-002)

---

## AT-002: read-write

| Field | Value |
|-------|-------|
| tier_name | read-write |
| governing_policy | POL-002 |

**Current eligibility:** 6 weeks of tenure, read-only level held, plus tech lead sign-off and SRE sign-off. Unchanged by [POL-002](policies.md#pol-002) — repointed only because POL-001 was superseded.

**Use cases:** Configuration changes, restart commands.

### References
- Governing policy: [POL-002](policies.md#pol-002)

---

## AT-003: privileged

| Field | Value |
|-------|-------|
| tier_name | privileged |
| governing_policy | POL-002 |

**Current eligibility:** On-call certification (typically 12 weeks of tenure). Unchanged by [POL-002](policies.md#pol-002) — repointed only because POL-001 was superseded.

**Use cases:** Incident response, emergency rollback, IAM changes.

### References
- Governing policy: [POL-002](policies.md#pol-002)

---
