# RiskLens AI — MVP Submission

## Snowflake CoCo Hackathon | Risk and Regulatory Copilot Track

---

## Project Identity

| Field | Value |
|-------|-------|
| **Project Name** | RiskLens AI — AML Investigation Copilot |
| **Tagline** | Monitor risk. Investigate signals. Generate governed findings. |
| **Track** | Risk and Regulatory Copilot for Banking / NBFC |
| **Team** | WU ERA |
| **Account** | XVKVPMF-UJ52156 |
| **Deployed App** | Snowsight > Streamlit > `AML_COPILOT.RAW.RISKLENS_APP` |
| **GitHub** | *(link to be inserted after push)* |

---

## 1. Problem Statement

Banking and NBFC teams manage real-time fraud, liquidity, credit risk, and regulatory reporting (AML, Basel, local regulations) — largely manual today. Compliance analysts must:

- Monitor **hundreds of thousands of daily transactions** for suspicious patterns
- Cross-reference activity against **multiple overlapping regulations** (BSA, FATF, FinCEN, UAE AML/CFT)
- Meet **strict filing deadlines** (SAR within 30 days, continuing activity every 90 days, CTR within 15 days)
- Produce **audit-ready documentation** where every decision traces back to specific evidence and policy
- Use **siloed tools** — transaction monitoring is separate from policy lookup, case management, and regulatory reporting

There is no single platform that lets a compliance user ask a natural language question and get a governed, explainable, evidence-backed answer that combines data and policy.

---

## 2. Solution: What We Built

RiskLens AI is an end-to-end AML copilot built entirely on Snowflake that:

**Combines transaction and account data with policy and filing text:**
- 500K+ transactions, 10K customers, 15K accounts, 8K beneficiaries — all queryable via Cortex Analyst through a 13-table Semantic View
- 11 AML regulatory policy documents (BSA/AML CTR, SAR filing, EDD, wire monitoring, sanctions, KYC, UAE AML/CFT, CTF, TBML, correspondent banking) indexed via Cortex Search

**Lets a business or compliance user ask questions and get governed, explainable, evidence-backed answers:**
- Every AI Copilot response uses BOTH data tools AND policy search — no answer is given without a policy citation
- Structured responses with 6 mandatory sections: Summary, Evidence, Applicable Policy, Risk Assessment, Recommended Action, Confidence Level
- ChatGPT/Claude-style conversational interface with follow-up suggestions and conversation history

**Covers the flow from signal to evidence to a documented finding or report:**

```
Signal Detection          Investigation              Evidence                Decision              Report
6 deterministic    -->    Customer Risk 360    -->    Policy citations  -->   Risk assessment  -->  SAR narrative
rules with                Transaction timeline        Data evidence           Confidence score      PDF export
RULE_ID +                 Beneficiary network          Source tags            Recommended action    Filing tracker
TRIGGER_DETAIL            Risk explainability
```

---

## 3. Judging Focus Alignment

### 3.1 Real World Relevance

| Criterion | How We Address It |
|-----------|-------------------|
| Real AML workflow | Complete Signal -> Investigation -> Evidence -> Decision -> Report flow across 6 application tabs |
| Realistic typologies | 6 deterministic detection rules: Structuring, Rapid Movement, Velocity Spike, Unusual Geography, Dormant Activation, Beneficiary Burst |
| Actual regulations | 11 policy documents reflecting real BSA/AML, FATF, FinCEN, and UAE AML/CFT requirements with specific thresholds ($10K CTR, $5K/$25K SAR, 30-day filing deadline, 90-day continuing activity) |
| How analysts actually work | Triage signals by score/type -> Investigate customer 360 -> Review transactions and counterparties -> Map to applicable policy -> Document finding -> Generate SAR/PDF |
| Enterprise-grade UI | Premium banking theme (Palantir/Actimize-inspired), KPI command center, interactive Plotly charts, beneficiary network graphs, risk explainability donuts |

### 3.2 Technical Execution

| Snowflake Feature | Implementation |
|-------------------|----------------|
| **Cortex Agent** | `AML_RISK_COPILOT` with `FROM SPECIFICATION $$yaml$$` — dual-tool orchestration enforcing data + policy on every response |
| **Cortex Analyst** | Semantic View (`AML_COPILOT_SV`) with 13 tables, 11 relationships, 7 verified queries, `AI_SQL_GENERATION` custom instruction |
| **Cortex Search** | `POLICY_SEARCH_SERVICE` indexing 11 policy documents (13 chunks) with `snowflake-arctic-embed-m-v1.5` embeddings |
| **Dynamic Tables** | 4 tables (DT_ENRICHED_TRANSACTIONS 500K, DT_CUSTOMER_RISK_FEATURES 10K, DT_CUSTOMER_RISK_SUMMARY 10K, DT_DAILY_SIGNAL_DASHBOARD 174) with 5-min refresh |
| **Streams** | `STREAM_NEW_TRANSACTIONS` (append-only) for incremental signal detection |
| **Tasks** | `DETECT_AML_SIGNALS` (5-min, stream-triggered) + `RUN_DATA_QUALITY_CHECKS` (15-min scheduled) |
| **Stored Procedures** | 6 procedures: SQL (signal detection, case creation), Python/fpdf2 (PDF report generation), JavaScript (DQ checks, document approval with chunking) |
| **Streamlit-in-Snowflake** | 83KB application with 6 tabs, ChatGPT-style chat UI, interactive Plotly charts, policy citation evidence panels |
| **Verified Queries (VQRs)** | 7 onboarding/reference queries for Cortex Analyst accuracy |

### 3.3 Solution Completeness

| AML Lifecycle Stage | Feature | Tab |
|---------------------|---------|-----|
| **Detection** | 6-rule deterministic pipeline, stream-triggered, 5-min cadence, each signal has RULE_ID + TRIGGER_DETAIL + EVIDENCE_JSON | Pipeline (automated) |
| **Monitoring** | 5 KPIs (Critical Alerts, Suspicious Accounts, Open Investigations, SAR Drafts Ready, Compliance Health), live risk feed, signal trend, heatmap | Dashboard |
| **Investigation** | Signal queue with filters, Customer Risk 360 (gauge + donut explainability), transaction timeline scatter, beneficiary network graph, inline AI investigation | Investigations |
| **Policy Lookup** | Direct Cortex Search across 11 regulatory documents, approved policy library, category/jurisdiction filtering | Evidence Center |
| **AI Analysis** | Natural language copilot with structured policy-backed responses, 8 suggested questions, clickable follow-ups, conversation persistence | AI Copilot |
| **Evidence** | Case evidence browser with type breakdown (Transaction/Signal/Policy), source tags on every AI response, citation cards with policy quotes | Evidence Center |
| **Reporting** | AI-generated SAR narratives, PDF reports with gradient headers and formatted tables, filing tracker, generated reports archive | Regulatory Reports |
| **Governance** | Document approval workflow (Pending -> Approved/Rejected), data quality monitoring (6 checks, 15-min cadence), pipeline audit log | CoCo Operations |

---

## 4. CoCo Usage Across Full Lifecycle

Every component of RiskLens AI was built using Snowflake CoCo (Cortex Code). Below is how CoCo was used in each lifecycle phase:

### 4.1 Planning (CoCo for exploration and design)

| Activity | CoCo Usage |
|----------|------------|
| Problem framing | Used CoCo to explore existing Snowflake capabilities (Cortex Agent, Search, Analyst) and determine the architecture |
| Data model design | CoCo designed the 13-table schema with referential integrity, risk tiers, and KYC attributes |
| Ontology definition | CoCo defined the AML ontology: 6 signal types, risk rating tiers, case lifecycle states, evidence types, policy categories |
| Workflow design | CoCo outlined the Signal -> Investigation -> Evidence -> Decision -> Report flow |
| Semantic View planning | CoCo planned table relationships, fact/dimension classification, and verified query strategy |

### 4.2 Development (CoCo for building all components)

| Component | CoCo Built |
|-----------|------------|
| **Synthetic data generation** | CoCo generated 500K+ referentially consistent transactions with realistic AML patterns (structuring sequences, rapid movement, velocity spikes), 10K customers with KYC/PEP/sanctions attributes, 8K beneficiaries with risk scores, 50 countries with FATF risk tiers |
| **Data pipeline creation** | CoCo built the complete incremental pipeline: Stream on TRANSACTIONS, 6-rule SQL stored procedure (SP_DETECT_AML_SIGNALS), stream-triggered task with 5-min cadence, 4 dynamic tables for real-time analytics |
| **Semantic model and ontology authoring** | CoCo created the Semantic View (AML_COPILOT_SV) with 13 tables, 11 relationships, 25 facts, 80+ dimensions, sample values, IS_ENUM flags, AI_SQL_GENERATION custom instruction, and 7 verified queries |
| **Cortex Agent specification** | CoCo authored the full agent YAML spec with dual-tool orchestration instructions, 5 behavioral skills, policy-backed response structure, and tool_resources configuration |
| **Cortex Search setup** | CoCo created the policy document chunking pipeline and POLICY_SEARCH_SERVICE with column descriptions and filter configuration |
| **Stored procedures** | CoCo developed 6 procedures across 3 languages: SQL (signal detection with 6 rules, case creation), Python/fpdf2 (PDF report generation with gradient headers), JavaScript (data quality checks, document approval with text chunking) |
| **Streamlit app** | CoCo built the entire 83KB Streamlit application: 6 tabs, ChatGPT-style chat UI, CSS theme, Plotly charts, agent API integration, conversation persistence, evidence panels |
| **Policy documents** | CoCo generated 11 realistic AML policy documents covering BSA/AML CTR, SAR filing, EDD, wire monitoring, sanctions, KYC, UAE AML/CFT, CTF, TBML, correspondent banking |

### 4.3 Execution (CoCo for running and orchestrating)

| Activity | CoCo Usage |
|----------|------------|
| Pipeline orchestration | Tasks run automatically: DETECT_AML_SIGNALS every 5 min (stream-triggered), RUN_DATA_QUALITY_CHECKS every 15 min |
| Dynamic table refresh | 4 dynamic tables auto-refresh with 5-min target lag, managed by Snowflake |
| Cortex Search indexing | POLICY_SEARCH_SERVICE indexes approved documents with 1-hour target lag |
| Agent testing | CoCo tested the agent via `SNOWFLAKE.CORTEX.DATA_AGENT_RUN()` to verify both tools work and responses are policy-backed |
| App deployment | CoCo deployed the Streamlit app via `PUT` to stage + `CREATE STREAMLIT` |

### 4.4 Testing and Validation (CoCo for correctness)

| Activity | CoCo Usage |
|----------|------------|
| Agent debugging | CoCo diagnosed the "missing execution environment" error via `DATA_AGENT_RUN` test, identified the root cause (warehouse not specified in tool_resources), and fixed it |
| Response validation | CoCo verified that agent responses contain all 6 required sections (Summary, Evidence, Policy, Risk Assessment, Recommended Action, Confidence) |
| Policy search validation | CoCo tested `SNOWFLAKE.CORTEX.SEARCH_PREVIEW()` to verify policy retrieval returns correct documents |
| Data quality | CoCo validated pipeline outputs: 208 signals across 6 rules, correct deduplication, proper EVIDENCE_JSON |
| UI iteration | CoCo iterated on Streamlit UI across multiple sessions: tab ordering, chat bubble styling, investigation action isolation, follow-up suggestion flow |
| PDF verification | CoCo iterated PDF generation 3 times: brown header -> exact format match -> black-to-navy gradient |

---

## 5. Recommended CoCo Tasks Demonstrated

| Recommended Task | How We Demonstrated It |
|------------------|----------------------|
| **Synthetic data generation** | CoCo generated 500K+ referentially consistent transactions, 10K customers with KYC/PEP/sanctions attributes, 8K beneficiaries, 50 countries with FATF tiers, 11 policy documents — all synthetic, no production data needed |
| **Data pipeline creation** | Stream-triggered incremental detection pipeline (STREAM_NEW_TRANSACTIONS -> SP_DETECT_AML_SIGNALS -> AML_SIGNALS), 4 dynamic tables for near-real-time analytics, 2 scheduled tasks |
| **Semantic model and ontology authoring** | Semantic View with 13 tables, 11 relationships, sample values, IS_ENUM flags, AI_SQL_GENERATION instruction, 7 verified queries — validated against natural language questions via agent testing |
| **Streamlit report and app generation** | 83KB Streamlit-in-Snowflake application with 6 tabs: AI Copilot (ChatGPT-style), Dashboard (KPI command center), Investigations (Customer 360), Regulatory Reports (SAR + PDF), Evidence Center, CoCo Operations |
| **Document and unstructured processing** | 11 AML policy documents chunked (1500 chars, 200 overlap), indexed by Cortex Search, used for policy-backed AI responses. Document approval workflow with governed ingestion pipeline |

---

## 6. Ingenuity in CoCo Tool Usage

| Capability | Implementation |
|------------|----------------|
| **Multi-agent orchestration** | Cortex Agent orchestrates 5 behavioral skills: Risk Analytics, Risk Investigator, Policy Interpreter, Evidence Validator, Finding Generator — with clear handoffs between data query and policy search tools. Workflow visualized in CoCo Operations tab: Detection Agent -> Investigation Agent -> Policy Agent -> Compliance Agent -> Reporting Agent |
| **Automations and scheduled runs** | 2 automated tasks running unattended: Signal detection every 5 min (stream-triggered, only fires when new data exists), Data quality checks every 15 min. 4 dynamic tables auto-refresh |
| **Custom tools and function calling** | Agent uses 2 custom tools: `risk_analytics` (Cortex Analyst text-to-SQL via Semantic View) and `policy_search` (Cortex Search over policy corpus). Investigation tab has inline AI action buttons that call the agent and render results directly |
| **Guardrails and graceful fallback** | Agent enforces dual-tool usage (NEVER answers from one tool alone). Confidence assessment (HIGH/MEDIUM/LOW) on every response. Error responses show debug info. Data quality checks annotate data freshness. Document quarantine rejects invalid uploads. Deduplication prevents repeated signals within time windows |
| **Reusable components** | Semantic View is reusable across any Cortex Analyst or Agent consumer. Cortex Search Service is callable from any application. Stored procedures are independently callable. The entire architecture is documented and reproducible from SQL scripts |

---

## 7. Technical Architecture

```
                          SNOWFLAKE ACCOUNT (XVKVPMF-UJ52156)

  [RAW SCHEMA]              [PIPELINE SCHEMA]           [ANALYTICS SCHEMA]
  13 base tables             Stream + 2 Tasks            4 Dynamic Tables
  - CUSTOMERS (10K)          - STREAM_NEW_TRANSACTIONS   - DT_ENRICHED_TRANSACTIONS (500K)
  - TRANSACTIONS (500K)      - DETECT_AML_SIGNALS (5m)   - DT_CUSTOMER_RISK_FEATURES (10K)
  - BANK_ACCOUNTS (15K)      - RUN_DQ_CHECKS (15m)       - DT_CUSTOMER_RISK_SUMMARY (10K)
  - BENEFICIARIES (8K)       6 Stored Procedures          - DT_DAILY_SIGNAL_DASHBOARD (174)
  - AML_SIGNALS (208)        - SP_DETECT_AML_SIGNALS      Search Index
  - RISK_CASES (50)          - SP_RUN_DQ_CHECKS           - POLICY_SEARCH_SERVICE (13 chunks)
  - CASE_EVIDENCE (200)      - SP_EXPORT_REPORT_PDF       - POLICY_DOCUMENT_CHUNKS
  - COUNTRIES (50)           - SP_APPROVE_POLICY_DOC      View
  - CUSTOMER_RISK_PROFILE    - SP_CREATE_RISK_CASE        - V_LATEST_DATA_QUALITY
  - POLICY_DOCUMENTS (12)    - SP_PROCESS_UPLOADS
  - CONVERSATION_HISTORY     Operational Tables
  - AML_GROUND_TRUTH         - SIGNAL_DETECTION_RUNS
                             - DATA_QUALITY_RESULTS
                             - GENERATED_REPORTS (PDF)
                             - PIPELINE_AUDIT_LOG
                             - POLICY_DOCUMENTS_STAGED

  [CORTEX AI LAYER]
  Agent: AML_RISK_COPILOT (FROM SPECIFICATION, dual-tool, policy-backed)
    Tool 1: risk_analytics (Cortex Analyst + AML_COPILOT_SV)
    Tool 2: policy_search (Cortex Search + POLICY_SEARCH_SERVICE)
  Semantic View: AML_COPILOT_SV (13 tables, 11 rels, 7 VQRs)

  [STREAMLIT APPLICATION]
  RISKLENS_APP (83KB, 6 tabs)
    1. AI Copilot      - ChatGPT-style, policy-backed answers
    2. Dashboard        - KPI command center, live risk feed
    3. Investigations   - Customer 360, network analysis, inline AI
    4. Regulatory Reports - SAR generation, PDF export
    5. Evidence Center  - Policy search, data quality
    6. CoCo Operations  - Architecture checklist, pipeline health
```

---

## 8. Detection Rules (Deterministic, Not AI)

| Rule ID | Signal Type | Logic | Score |
|---------|-------------|-------|-------|
| RULE_STRUCT_001 | STRUCTURING | 3+ cash txns <$10K summing >$10K within 24h | 60-95 |
| RULE_RAPID_001 | RAPID_MOVEMENT | Inbound wire >$50K, outbound >80% within 48h | 65-95 |
| RULE_VELOC_001 | VELOCITY_SPIKE | Txn count >3x 30-day daily average | 50-90 |
| RULE_GEO_001 | UNUSUAL_GEOGRAPHY | Txn to HIGH-risk country, no prior history | 70-85 |
| RULE_DORM_001 | DORMANT_ACTIVATION | Txn after 90+ days of inactivity | 55-90 |
| RULE_BENEF_001 | BENEFICIARY_BURST | >5 new beneficiaries within 7 days | 50-85 |

Each signal stores: RULE_ID, TRIGGER_DETAIL (human-readable), EVIDENCE_JSON (structured thresholds), TRANSACTION_IDS (source traceability).

---

## 9. Policy-Backed AI Response Structure

Every copilot answer MUST contain:

| Section | Purpose | Example |
|---------|---------|---------|
| **Summary** | Direct answer in 2-3 sentences | "There are 208 AML signals, with structuring being the most common type (35 signals)." |
| **Evidence** | Data with specific numbers | "Richard Johnson: 4 cash deposits totaling $38,950, signal score 95" |
| **Applicable Policy** | Exact policy citation | "Per BSA/AML CTR Reporting (United States): transactions exceeding $10,000 require CTR filing within 15 days" |
| **Risk Assessment** | Grounded in data + policy | "HIGH — structuring is independently reportable under BSA regardless of fund legitimacy" |
| **Recommended Action** | Next step for analyst | "File SAR within 30 days, open investigation case, request EDD review" |
| **Confidence** | HIGH/MEDIUM/LOW | "HIGH — data and policy match directly with explicit RULE_ID-to-regulation mapping" |

---

## 10. How to Demo (Judge Walkthrough)

| Step | Action | What Judge Sees |
|------|--------|-----------------|
| 1 | Open **AI Copilot** tab, click "What are the SAR filing requirements and do any current cases meet the threshold?" | Structured response with policy citations from SAR Filing Guidelines, cross-referenced against actual case data |
| 2 | Ask follow-up: "Show the top 5 highest-risk customers with their risk scores and applicable EDD policy" | Data table + EDD policy citation, confidence assessment |
| 3 | Switch to **Dashboard** | KPI command center: Critical Alerts, Suspicious Accounts, Open Investigations, SAR Drafts, Compliance Health. Live risk feed with trigger details |
| 4 | Switch to **Investigations**, filter by STRUCTURING, select a customer | Customer Risk 360: gauge chart, risk explainability donut, transaction timeline, beneficiary network |
| 5 | Click **"AI Investigation"** button | Inline policy-backed analysis rendered directly in Investigations tab (NOT routed to Copilot) |
| 6 | Switch to **Regulatory Reports**, select a case | Case summary card, generate SAR narrative (AI-powered), generate PDF report with gradient header |
| 7 | Switch to **Evidence Center**, search "structuring" | Direct Cortex Search results with policy document titles, categories, jurisdictions, and quoted text |
| 8 | Switch to **CoCo Operations** | 10-item CoCo-built checklist (all green), multi-agent orchestration workflow diagram, pipeline health metrics |

---

## 11. Data Scale

| Object | Count |
|--------|-------|
| Customers | 10,000 |
| Transactions | 500,000 |
| Bank Accounts | 15,000 |
| Beneficiaries | 8,126 |
| AML Signals | 208 (6 rules) |
| Risk Cases | 50 |
| Case Evidence | 200 |
| Countries | 50 (with FATF risk tiers) |
| Policy Documents | 11 (indexed, 13 chunks) |
| Detection Rules | 6 (deterministic) |
| Dynamic Tables | 4 (5-min refresh) |
| Scheduled Tasks | 2 (5-min + 15-min) |
| Verified Queries | 7 |
| Stored Procedures | 6 (SQL + Python + JavaScript) |

---

## 12. Built With

| Technology | Usage |
|------------|-------|
| Snowflake Cortex Agent | `FROM SPECIFICATION` with dual-tool orchestration, policy-backed response enforcement |
| Snowflake Cortex Analyst | Semantic View (13 tables, 11 relationships, 7 VQRs, AI_SQL_GENERATION) |
| Snowflake Cortex Search | Policy document indexing (snowflake-arctic-embed-m-v1.5), 11 documents |
| Snowflake Dynamic Tables | 4 real-time analytics tables (5-min target lag) |
| Snowflake Streams + Tasks | Incremental signal detection pipeline + scheduled DQ monitoring |
| Snowflake Stored Procedures | SQL (detection), Python/fpdf2 (PDF), JavaScript (DQ, document approval) |
| Streamlit-in-Snowflake | 83KB enterprise application, 6 tabs, ChatGPT-style UI |
| **Snowflake CoCo** | **Entire project — planning, development, execution, testing, debugging, iteration** |
