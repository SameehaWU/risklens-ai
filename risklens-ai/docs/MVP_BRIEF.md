# RiskLens AI — Prototype MVP Brief

**Snowflake CoCo Hackathon | Risk and Regulatory Copilot Track**

---

## Executive Summary

**RiskLens AI** is an enterprise-grade AML Investigation Copilot that transforms how compliance teams detect, investigate, and report financial crime. Built entirely on Snowflake and developed end-to-end using Snowflake CoCo (Cortex Code), it is the first platform to combine transactional data with regulatory policy text in a single AI-driven workflow — delivering governed, evidence-backed, policy-cited answers from a natural language interface.

| | |
|---|---|
| **Team** | WU ERA |
| **Track** | Risk and Regulatory Copilot for Banking / NBFC |
| **Account** | XVKVPMF-UJ52156 |
| **Deployed App** | `AML_COPILOT.RAW.RISKLENS_APP` (Streamlit-in-Snowflake) |
| **GitHub** | *(link to be inserted)* |

---

## Problem

Compliance teams across banking and NBFCs face a fragmented landscape:

- **Volume**: Hundreds of thousands of transactions daily require monitoring against BSA, FATF, FinCEN, and local AML regulations
- **Speed**: SAR filings due within 30 days, CTR within 15 days, continuing activity reviews every 90 days
- **Silos**: Transaction monitoring, policy lookup, case management, and regulatory reporting exist in separate tools
- **Auditability**: Every decision must trace back to specific evidence and specific policy — no tool connects data to regulation to finding in one place

**No single platform lets a compliance user ask a question in natural language and receive a governed, explainable, evidence-backed answer that combines data and policy.**

---

## Solution

RiskLens AI closes that gap with a complete signal-to-report workflow:

```
Signal Detection  -->  Investigation  -->  Evidence  -->  Decision  -->  Regulatory Report
6 deterministic        Customer 360        Data + Policy   Risk rating    SAR narrative
rules (RULE_ID)        Txn timeline        citations       Confidence     PDF export
                       Network graph                       Next steps     Filing tracker
```

### Core Innovation: Data + Policy Combined

Every AI Copilot answer uses **BOTH** tools on every question:

1. **Cortex Analyst** (risk_analytics) — queries 500K+ transactions across 13 tables via Semantic View
2. **Cortex Search** (policy_search) — retrieves relevant regulation from 11 indexed AML policy documents

No answer is ever given without a policy citation. Every response contains six mandatory sections:

| Section | Purpose |
|---------|---------|
| **Summary** | Direct answer in 2-3 sentences |
| **Evidence** | Specific data with numbers and identifiers |
| **Applicable Policy** | Exact regulation citation with jurisdiction |
| **Risk Assessment** | HIGH / MEDIUM / LOW grounded in data + policy |
| **Recommended Action** | File SAR, escalate, open investigation, request EDD |
| **Confidence Level** | Assessment of data-policy alignment |

---

## What the Prototype Demonstrates

### 6-Tab Application

| Tab | Capability |
|-----|------------|
| **AI Copilot** | ChatGPT-style conversational interface with policy-backed responses, 8 suggested questions, clickable follow-ups, evidence citation panels |
| **Dashboard** | KPI command center (5 metrics), signal trend charts, live risk feed, geographic heatmap, top-risk customer table |
| **Investigations** | Customer Risk 360 with gauge chart, risk explainability donut, transaction timeline scatter, beneficiary network graph, inline AI investigation actions |
| **Regulatory Reports** | AI-generated SAR narratives, PDF export with gradient headers (fpdf2), case filing tracker |
| **Evidence Center** | Direct Cortex Search for policy lookup, case evidence browser, data quality dashboard |
| **CoCo Operations** | Architecture checklist (10 items), multi-agent workflow diagram, pipeline health, document governance |

### Detection Pipeline

6 deterministic rules running on a 5-minute stream-triggered cadence:

| Rule | Signal | Logic |
|------|--------|-------|
| RULE_STRUCT_001 | Structuring | 3+ cash txns <$10K summing >$10K within 24h |
| RULE_RAPID_001 | Rapid Movement | Inbound wire >$50K, outbound >80% within 48h |
| RULE_VELOC_001 | Velocity Spike | Txn count >3x 30-day daily average |
| RULE_GEO_001 | Unusual Geography | Txn to HIGH-risk country, no prior history |
| RULE_DORM_001 | Dormant Activation | Txn after 90+ days of inactivity |
| RULE_BENEF_001 | Beneficiary Burst | >5 new beneficiaries within 7 days |

Each signal stores RULE_ID, TRIGGER_DETAIL, EVIDENCE_JSON, and TRANSACTION_IDS for full traceability.

---

## Snowflake Tech Stack

| Feature | Implementation |
|---------|----------------|
| **Cortex Agent** | `AML_RISK_COPILOT` — `FROM SPECIFICATION` YAML with dual-tool orchestration, 5 behavioral skills |
| **Cortex Analyst** | Semantic View: 13 tables, 11 relationships, 7 verified queries, AI_SQL_GENERATION instruction |
| **Cortex Search** | 11 AML policy documents indexed with `snowflake-arctic-embed-m-v1.5` (13 chunks) |
| **Dynamic Tables** | 4 tables with 5-min refresh: enriched transactions, risk features, risk summary, signal dashboard |
| **Streams + Tasks** | Incremental detection (5-min, stream-triggered) + DQ monitoring (15-min scheduled) |
| **Stored Procedures** | 6 procedures: SQL (detection), Python/fpdf2 (PDF), JavaScript (DQ, document approval) |
| **Streamlit-in-Snowflake** | 83KB app, 6 tabs, ChatGPT-style chat, Plotly charts, policy evidence panels |
| **Verified Queries** | 7 VQRs for Cortex Analyst accuracy on common AML questions |

---

## Data Scale

| Metric | Value |
|--------|-------|
| Transactions | 500,000 |
| Customers | 10,000 |
| Bank Accounts | 15,000 |
| Beneficiaries | 8,126 |
| AML Signals | 208 (6 rules) |
| Risk Cases | 50 |
| Policy Documents | 11 (BSA, FATF, FinCEN, UAE AML/CFT) |
| Countries | 50 (with FATF risk tiers) |
| Dynamic Tables | 4 (auto-refreshing) |
| Stored Procedures | 6 (SQL + Python + JavaScript) |
| Verified Queries | 7 |

All data is synthetic — generated by CoCo with realistic AML patterns, referential integrity, and regulatory-accurate thresholds.

---

## CoCo Lifecycle Coverage

Every component was built using Snowflake CoCo across all four lifecycle phases:

### Planning
- Data model design (13-table schema with risk tiers, KYC attributes, referential integrity)
- AML ontology (6 signal types, case lifecycle states, evidence types, policy categories)
- Workflow design: Signal -> Investigation -> Evidence -> Decision -> Report

### Development
- 500K+ synthetic transactions with realistic AML patterns
- 6 stored procedures across 3 languages (SQL, Python, JavaScript)
- Semantic View with 13 tables, 11 relationships, 7 verified queries
- Cortex Agent YAML spec with dual-tool orchestration and policy-backed response enforcement
- 11 policy documents with chunking pipeline and Cortex Search indexing
- 83KB Streamlit application with ChatGPT-style chat UI

### Execution
- Automated tasks: signal detection (5-min) + DQ checks (15-min)
- Dynamic table auto-refresh for near-real-time analytics
- Cortex Search indexing with governed document approval
- Streamlit deployment to Snowflake stage

### Testing and Validation
- Agent debugging via `DATA_AGENT_RUN()` — diagnosed and fixed execution environment error
- Policy search verification via `SEARCH_PREVIEW()`
- Response structure validation (6 mandatory sections)
- PDF generation iteration (3 versions)
- UI iteration: tab ordering, chat bubble styling, action isolation, follow-up flow

---

## CoCo Ingenuity

| Category | Implementation |
|----------|----------------|
| **Multi-agent orchestration** | 5 behavioral skills: Risk Analytics -> Investigator -> Policy Interpreter -> Evidence Validator -> Finding Generator |
| **Automations** | Stream-triggered detection (5-min), scheduled DQ checks (15-min), 4 auto-refreshing dynamic tables |
| **Custom tools** | Agent uses risk_analytics (text-to-SQL) + policy_search (semantic search). Investigation tab has inline AI action buttons |
| **Guardrails** | Dual-tool enforcement, confidence levels, error diagnostics, DQ annotations, document quarantine, signal deduplication |
| **Document processing** | 11 policy documents chunked (1500 chars, 200 overlap), governed approval workflow, Cortex Search indexing |
| **Reusable components** | Semantic View reusable across consumers. Search service callable from any app. Fully reproducible from SQL scripts |

---

## Demo Walkthrough (8 Steps)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open **AI Copilot**, click a suggested question | Structured response: Summary, Evidence, Policy Citation, Risk Assessment, Recommended Action |
| 2 | Click a follow-up suggestion | Seamless multi-turn conversation with data tables + policy citations |
| 3 | Switch to **Dashboard** | KPI command center with 5 metrics, signal trends, live risk feed, heatmap |
| 4 | Switch to **Investigations**, filter by STRUCTURING, select customer | Customer Risk 360: gauge, explainability donut, transaction timeline, network graph |
| 5 | Click **AI Investigation** button | Inline AI analysis rendered in Investigations tab (isolated from Copilot) |
| 6 | Switch to **Regulatory Reports**, select a case | SAR narrative generated by AI, downloadable PDF with gradient header |
| 7 | Switch to **Evidence Center**, search "structuring" | Cortex Search results with policy titles, categories, and quoted text |
| 8 | Switch to **CoCo Operations** | 10-item checklist (all green), agent workflow diagram, pipeline health |

---

## Repository Structure

```
risklens-ai/
  app/
    streamlit_app.py              # Main application (83KB, 6 tabs)
  sql/
    01_schema_and_tables.sql      # Database, schema, table DDL
    02_synthetic_data.sql         # 500K+ rows synthetic data
    03_pipeline.sql               # Stored procedures, streams, tasks
    04_cortex_ai.sql              # Semantic view, search service, agent
    05_deploy_app.sql             # Streamlit deployment
    stored_procedures.sql         # Complete SP DDL (SQL + Python + JS)
  docs/
    MVP_SUBMISSION.md             # Full submission document
    MVP_BRIEF.md                  # This brief
    AML_Copilot_Data_Model_Documentation.md
    RiskLens_AI_Solution_Deck.html  # 12-slide presentation
  README.md
```

All SQL scripts are idempotent (`CREATE OR REPLACE`) — the entire system is reproducible from scratch in a clean Snowflake account.

---

## Key Differentiators

1. **Policy-backed AI** — Every answer cites specific regulation. The agent is architecturally incapable of answering from data alone.
2. **Complete lifecycle** — Not a chatbot. A full signal -> investigation -> evidence -> decision -> report workflow.
3. **Deterministic detection** — AI does not invent signals. 6 rules with explicit thresholds, RULE_IDs, and evidence JSON.
4. **Enterprise UI** — Production-grade interface modeled on Palantir/Actimize, not a demo template.
5. **100% CoCo-built** — Every line of SQL, Python, JavaScript, YAML, and Streamlit code authored with Snowflake CoCo.
6. **Fully reproducible** — 5 SQL scripts recreate the entire system from scratch in any Snowflake account.

---

*Built entirely with Snowflake CoCo | Team WU ERA | Account XVKVPMF-UJ52156*
