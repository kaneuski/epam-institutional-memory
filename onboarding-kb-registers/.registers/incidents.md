---
type: incident
tier: core
lifecycle: tracked-until-closed
id_prefix: INC
singleton_key: null
source_doc_types: ["policy-doc"]
last_updated: 2026-06-24
---

# Incidents

Trigger events behind policy and process changes.

---

## INC-001: April Access-Request Backlog (PROD-INC-04-2026)

| Field | Value |
|-------|-------|
| status | resolved |
| severity | P2 |
| date | 2026-04-01 |
| postmortem_link | null |

**Summary:** Referenced in policy-update-2026-05-15.md as "the April incident review (PROD-INC-04-2026)" that triggered a rewrite of the production access policy. [UNVERIFIED] Severity, exact date, and postmortem link are not stated in the source document — `date` uses April 2026 as a placeholder, `severity` defaults to P2 rather than asserting an unconfirmed P0/P1, and `postmortem_link` is left null.

**Impact:** [INFERRED] The source ties this review to the read-only access request backlog growing to 3 weeks under the old SRE-pairing model — likely the actual impact driving the review, though the document doesn't explicitly label that backlog itself as the incident.

**Root cause:** [INFERRED] SRE-pairing-session model didn't scale past ~40 engineers; at 280 engineers it became a bottleneck.

### References
- Drove: [DEC-001](decisions.md#dec-001)
- Related policy: [POL-002](policies.md#pol-002)

---
