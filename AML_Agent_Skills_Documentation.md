# AML Risk Copilot — Agent Skills Documentation

**Agent**: `AML_COPILOT.RAW.AML_RISK_COPILOT`
**Created**: 2026-09-04
**Updated**: 2026-09-04 (added governed investigation response pattern)
**Model**: Auto (orchestration)
**Budget**: 900 seconds / 400,000 tokens

---

## Architecture

```
                         USER QUESTION
                              │
                              ▼
                    ┌─── AML_RISK_COPILOT ───┐
                    │    (Cortex Agent)        │
                    │                         │
                    │   5 Behavioral Skills:   │
                    │   1. Risk Analytics      │
                    │   2. Risk Investigator   │
                    │   3. Policy Interpreter  │
                    │   4. Evidence Validator  │
                    │   5. Finding Generator   │
                    │                         │
                    └──────┬──────┬───────────┘
                           │      │
              ┌────────────┘      └────────────┐
              ▼                                ▼
    ┌─── risk_analytics ───┐       ┌─── policy_search ───┐
    │ (Cortex Analyst)      │       │ (Cortex Search)      │
    │                       │       │                      │
    │ Semantic View:        │       │ Search Service:      │
    │ AML_COPILOT_SV        │       │ POLICY_SEARCH_SERVICE│
    │                       │       │                      │
    │ 16 tables, 41 facts,  │       │ 11 policy docs       │
    │ 83 dims, 17 metrics,  │       │ BSA/AML, SAR, CTR    │
    │ 26 verified queries   │       │ KYC, sanctions, EDD  │
    └───────────────────────┘       └──────────────────────┘
```

---

## Tools

| Tool Name | Type | Backing Object | Purpose |
|-----------|------|----------------|---------|
| `risk_analytics` | `cortex_analyst_text_to_sql` | `AML_COPILOT.RAW.AML_COPILOT_SV` | All structured data queries: customers, transactions, signals, risk features, pipeline health, data quality |
| `policy_search` | `cortex_search` | `AML_COPILOT.ANALYTICS.POLICY_SEARCH_SERVICE` | Regulatory policy retrieval: thresholds, SAR requirements, jurisdiction rules |

---

## Skills

### Skill 1: Risk Analytics

**Purpose**: Answer governed questions about customers, accounts, transactions, and risk signals.

**Triggers**: Customer risk, transaction patterns, signal counts, operational metrics, pipeline status, data quality.

**Key behaviors**:
- Prefers pre-computed tables (DT_CUSTOMER_RISK_FEATURES, DT_CUSTOMER_RISK_SUMMARY, DT_DAILY_SIGNAL_DASHBOARD) over raw transaction scans
- Always includes RULE_ID and TRIGGER_DETAIL for signal details
- Cites data quality OVERALL_PASS_RATE for confidence

**Example questions**:
- "Which customers have the highest AML risk today?"
- "How many high-risk signals were generated this week?"
- "What is the current data quality status?"

---

### Skill 2: Risk Investigator

**Purpose**: Investigate a risk signal and assemble structured evidence.

**Triggers**: "Why was this customer flagged?", "Investigate signal X", "What triggered this alert?", "Show evidence for this signal".

**Investigation workflow**:
1. Query the **signal** (type, rule, score, trigger detail)
2. Get **supporting transactions** from TRANSACTION_IDS array
3. Get **customer context** (risk features + risk summary)
4. Get **beneficiary context** (names, countries, risk tiers)
5. Check for **prior signals** (repeat behavior)
6. Present as **structured evidence package**

**Example questions**:
- "Why was CUST_00008376 flagged?"
- "Show the transactions supporting the structuring signal"
- "Has this customer shown similar behavior before?"

---

### Skill 3: Policy Interpreter

**Purpose**: Identify applicable policy/regulatory requirements and explain their relevance.

**Triggers**: "Which policy applies?", "What are the thresholds?", "What does the regulation say?", "Is this a violation?", SAR/STR filing questions.

**Key behaviors**:
- Uses policy_search tool to find regulatory documents
- Cites specific policy TITLE, CATEGORY, JURISDICTION
- Relates policy thresholds to the specific signal/transaction being discussed
- For signal-related policy questions: queries signal first, then searches policy

**Example questions**:
- "What are the CTR filing thresholds for cash transactions?"
- "Which policy applies to this structuring signal?"
- "What are the SAR filing requirements and timelines?"

---

### Skill 4: Evidence Validator

**Purpose**: Validate that conclusions are supported by actual data and authoritative policy evidence.

**Triggers**: "Is this conclusion supported?", "Validate this finding", "Check the evidence".

**Validation checks**:
1. **Data verification**: Signal exists with stated RULE_ID, transaction amounts match, customer profile matches
2. **Policy verification**: Document exists, is APPROVED, thresholds match actual text, jurisdiction relevant
3. **Data quality**: Checks OVERALL_PASS_RATE, notes reduced confidence if <100%
4. **Gap identification**: Flags missing evidence in the chain

**Example questions**:
- "Is the structuring conclusion supported by the data?"
- "Validate the evidence for this SAR recommendation"

---

### Skill 5: Finding Generator

**Purpose**: Convert a validated investigation into a structured finding and audit-ready report.

**Triggers**: "Generate a finding", "Create a report", "Document this investigation", "Audit-ready report".

**Report structure**:
1. **FINDING SUMMARY** — One-paragraph factual conclusion
2. **SIGNAL DETAILS** — Type, rule ID, score, detection date, trigger detail
3. **SUPPORTING EVIDENCE** — Transaction table, customer profile, beneficiary exposure
4. **APPLICABLE POLICY** — Title, category, jurisdiction, specific thresholds
5. **DATA QUALITY** — Pass rate, caveats
6. **RISK ASSESSMENT** — Recommended action (escalate/dismiss/monitor)
7. **PRIOR HISTORY** — Count and types of prior signals

**Example questions**:
- "Generate an audit-ready finding for the structuring signal on CUST_00008376"
- "Create a report documenting this investigation"

---

## How Skills Chain Together

A typical investigation flow chains multiple skills:

```
User: "Investigate why CUST_00008376 was flagged and generate a finding"

Skill 2 (Risk Investigator):
  → Query signal details, transactions, customer context, prior history

Skill 3 (Policy Interpreter):
  → Search for applicable structuring/CTR policies
  → Cite specific thresholds from BSA 31 USC 5313

Skill 4 (Evidence Validator):
  → Verify all claims against actual data
  → Check data quality pass rates

Skill 5 (Finding Generator):
  → Assemble structured finding with all evidence
  → Include policy citations and risk assessment
```

---

## Testing the Agent

### In Snowsight
1. Navigate to **AML_COPILOT** > **RAW** > **Agents** > **AML_RISK_COPILOT**
2. Open the chat interface
3. Try the onboarding questions that appear

### Sample test questions (one per skill)

| Skill | Test Question |
|-------|---------------|
| 1. Risk Analytics | "Which customers have the highest AML risk today?" |
| 2. Risk Investigator | "Why was customer CUST_00008376 flagged?" |
| 3. Policy Interpreter | "What are the CTR filing thresholds for structuring?" |
| 4. Evidence Validator | "Is the data quality sufficient for this conclusion?" |
| 5. Finding Generator | "Generate an audit-ready report for the top signal" |

---

## Governed Investigation Response Pattern

The agent uses a structured, evidence-first response format for investigation questions. Simple analytical questions get concise table/chart answers.

### Response Decision

```
Is it a simple question (count, trend, top-N)?
  → Concise answer with table/chart
  
Is it an investigation question (why flagged, evidence, policy, finding)?
  → Full governed investigation format below
```

### Investigation Response Structure

| Section | Content | Source |
|---------|---------|--------|
| **Investigation Summary** | Customer ID, risk score, risk level, 2-4 sentence assessment | risk_analytics |
| **Triggered Risk Signals** | Signal ID, RULE_ID, risk level, observed behavior, threshold, why triggered | risk_analytics (AML_SIGNALS) |
| **Supporting Transactions** | Only transactions actually returned by query. Never invented. | risk_analytics (TRANSACTIONS) |
| **Policy Evidence** | Policy title, section, requirement, reference. Why it applies. | policy_search |
| **Evidence-Based Assessment** | Signal -> Transaction Evidence -> Policy Evidence chain | Combined |
| **Recommended Action** | One of: Review / Enhanced Investigation / Escalate / Continue Monitoring / No Further Action | Agent judgment |
| **Evidence Status** | COMPLETE / PARTIAL / INSUFFICIENT | Determined by evidence availability |

### Evidence References (appended to investigation responses)
- Structured Evidence: Signal IDs, Transaction IDs, Customer ID
- Policy Evidence: Document name, section, reference

### Key Guardrails
- Risk signals are NOT confirmed fraud/misconduct/violations
- Never invent transactions or policy requirements
- If evidence insufficient: "No definitive conclusion can be reached"
- Final compliance decisions remain with human reviewers
- Evidence Status explicitly communicated (COMPLETE/PARTIAL/INSUFFICIENT)

---

## Agent Spec File

The full agent specification JSON is saved at:
`c:\Users\331006\OneDrive - Western Union\AI Files\CoCo\agent_spec.json`
