# Eval results

Model: `groq:openai/gpt-oss-120b` · Run: 2026-11-27 00:20 · Claims: 6

| Claim | Route | Incident Date | Amount | Coverage | Clauses | Fraud | Grounded |
|---|---|---|---|---|---|---|---|
| CLM-001 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| CLM-002 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| CLM-003 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| CLM-004 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| CLM-005 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| CLM-006 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Total** | **6/6** | **6/6** | **6/6** | **6/6** | **6/6** | **6/6** | **3/6** |

## Failures

- **CLM-002** ungrounded: The loss is a pipe burst causing water damage, which is not weather‑related.
- **CLM-002** ungrounded: Missing cost estimate and photos are typical documentation gaps, not indicative of fraud.
- **CLM-003** ungrounded: Incident date: 2026-11-19, loss type: auto_theft, location: mall parking lot
- **CLM-003** ungrounded: Police report filed: true
- **CLM-003** ungrounded: Missing estimated loss amount, vehicle VIN, and photos
- **CLM-004** ungrounded: Repeat home‑theft claim on same policy within a short timeframe.