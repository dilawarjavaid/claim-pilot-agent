# Eval results

Model: `groq:openai/gpt-oss-120b` · Run: 2026-11-27 00:30 · Claims: 6

| Claim | Route | Incident Date | Amount | Coverage | Clauses | Fraud | Grounded |
|---|---|---|---|---|---|---|---|
| CLM-001 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| CLM-002 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| CLM-003 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| CLM-004 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| CLM-005 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| CLM-006 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Total** | **6/6** | **6/6** | **6/6** | **6/6** | **6/6** | **5/6** | **2/6** |

## Failures

- **CLM-002** ungrounded: Incident is a pipe burst water damage, not weather-related.
- **CLM-002** ungrounded: Missing location detail is not a fraud red flag.
- **CLM-003** ungrounded: Auto theft claim filed only 3 days after policy inception.
- **CLM-004** ungrounded: Prior theft claim on the same policy within the past 14 months.
- **CLM-004** ungrounded: Missing police report number and proof of value documentation.
- **CLM-004** ungrounded: Current claim missing police report number, photos of stolen items, and receipts/proof of value.
- **CLM-005** fraud: expected low, got medium
- **CLM-005** ungrounded: Missing police report for a rear‑end collision with reported injuries
- **CLM-005** ungrounded: Current claim lacks a police report despite reported injuries.