---
type: exception
tier: traceability
lifecycle: tracked-until-closed
id_prefix: EXC
singleton_key: null
source_doc_types: ["policy-doc"]
last_updated: 2026-06-24
---

# Exceptions

Conditional carve-outs that override a standard policy.

---

## EXC-001: Urgent Read-Only Access Exception

| Field | Value |
|-------|-------|
| status | superseded |
| modifies_policy | POL-001 |
| trigger_condition | Engineer needs urgent read-only access (e.g., to debug a P1 incident) |
| reconciliation_deadline | within 5 working days of the grant |

**Override behavior:** The on-call SRE may grant temporary 24-hour read-only access without a pairing session.

**Reconciliation requirement:** The pairing session must happen within 5 working days of the grant, or the access is revoked automatically.

**Superseded note:** [POL-002](policies.md#pol-002) (effective 2026-05-15) eliminated the SRE pairing session entirely — replaced by online certification + just-in-time access — so this exception's override target no longer exists. `superseded_date` set to POL-002's `effective_date`. Left pointing at [POL-001](policies.md#pol-001) since that's the policy it actually modified; not re-pointed to POL-002, which has no equivalent step to waive.

### References
- Modifies: [POL-001](policies.md#pol-001)

---
