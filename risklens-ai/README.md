# RiskLens AI - AML Investigation Copilot

**Monitor risk. Investigate signals. Generate governed findings.**

> Built for the Snowflake CoCo Hackathon - An enterprise-grade AML Investigation Command Center powered by Snowflake Cortex Agent, Cortex Search, Dynamic Tables, and Streamlit-in-Snowflake.

### Live Application

**[Launch RiskLens AI](https://app.snowflake.com/XVKVPMF-UJ52156/#/streamlit-apps/AML_COPILOT.RAW.RISKLENS_APP)** — Deployed on Snowflake (Streamlit-in-Snowflake)

**[View App Preview (no login required)](docs/RiskLens_AI_App_Preview.html)** — Interactive mockup showing all 6 tabs with live data samples (download HTML and open in browser)

| | |
|---|---|
| **Deployed App** | [app.snowflake.com/XVKVPMF-UJ52156 > RISKLENS_APP](https://app.snowflake.com/XVKVPMF-UJ52156/#/streamlit-apps/AML_COPILOT.RAW.RISKLENS_APP) |
| **App Preview** | [Open HTML Preview](docs/RiskLens_AI_App_Preview.html) (download and open in browser) |
| **Account** | `XVKVPMF-UJ52156` |
| **Database** | `AML_COPILOT` |
| **Team** | WU ERA |
| **Track** | Risk and Regulatory Copilot |

### App Screenshots

<details>
<summary>Click to expand screenshots from the live application</summary>

#### Tab 1: AI Copilot
ChatGPT-style interface with policy-backed responses. Every answer includes Summary, Evidence, Applicable Policy, Risk Assessment, Recommended Action, and Confidence sections with citation cards.

![AI Copilot - Chat Interface](docs/screenshots/ai%20copilot%201.png)

![AI Copilot - Response Detail](docs/screenshots/ai%20copilot%202.png)

#### Tab 2: Dashboard
Real-time KPI metrics (72 Critical Alerts, 98 Suspicious Accounts, 17 Open Investigations, 14 SAR Drafts Ready, 100% Compliance Health), signal trend chart with escalation tracking, live risk feed, and signals by detection rule breakdown.

![Dashboard](docs/screenshots/dashboard.png)

#### Tab 3: Investigations
Signal-to-finding workflow pipeline, filterable signal table with status/rule/score controls, and Customer Risk 360 with transaction timeline, risk explainability, and AI-powered investigation actions.

![Investigations](docs/screenshots/Investigations.png)

#### Tab 4: Regulatory Reports
AI-generated SAR narratives via Cortex Agent, case selection, and filing tracker with case IDs, customer names, case types, priority levels, and SAR filing references.

![Regulatory Reports](docs/screenshots/regulatory%20reports.png)

#### Tab 5: Evidence Center
Cortex Search-powered policy retrieval with citation cards, case evidence timeline, and data quality dashboard with 6 automated checks.

![Evidence Center](docs/screenshots/evidence%20center.png)

#### Tab 6: CoCo Operations
Architecture checklist (10/10 CoCo-built components), multi-agent orchestration workflow diagram, and pipeline health monitoring for all system components.

![CoCo Operations](docs/screenshots/coco%20operations.png)

</details>

---

## What It Does

RiskLens AI is a complete AML (Anti-Money Laundering) compliance platform that lets analysts:

1. **Detect** - Deterministic, rule-based signal detection pipeline (6 rules, 200+ signals)
2. **Investigate** - Customer Risk 360 with transaction timelines, beneficiary networks, risk explainability
3. **Ask** - AI Copilot that answers natural language questions with policy-backed, evidence-driven responses
4. **Report** - Generate audit-ready SAR narratives and PDF regulatory reports
5. **Govern** - Policy document ingestion, approval workflow, Cortex Search for policy retrieval

Every AI answer combines **transaction data evidence** with **policy citations** - the copilot never answers without citing the applicable regulation.

---

## Architecture

```
+-----------------------------------------------------------------------------------+
|                           SNOWFLAKE ACCOUNT                                       |
|                                                                                   |
|  [RAW SCHEMA]              [PIPELINE SCHEMA]           [ANALYTICS SCHEMA]         |
|  - CUSTOMERS (10K)         - STREAM_NEW_TRANSACTIONS   - DT_ENRICHED_TRANSACTIONS |
|  - TRANSACTIONS (500K)     - SIGNAL_DETECTION_RUNS     - DT_CUSTOMER_RISK_SUMMARY |
|  - BANK_ACCOUNTS (15K)     - DATA_QUALITY_RESULTS      - DT_CUSTOMER_RISK_FEATURES|
|  - BENEFICIARIES (8K)      - POLICY_DOCUMENTS_STAGED   - DT_DAILY_SIGNAL_DASHBOARD|
|  - AML_SIGNALS (200+)      - GENERATED_REPORTS         - V_LATEST_DATA_QUALITY    |
|  - RISK_CASES (50)         - PIPELINE_AUDIT_LOG        - POLICY_DOCUMENT_CHUNKS   |
|  - CASE_EVIDENCE           - SP_DETECT_AML_SIGNALS     - POLICY_SEARCH_SERVICE    |
|  - COUNTRIES               - SP_RUN_DATA_QUALITY_CHECKS                           |
|  - CUSTOMER_RISK_PROFILE   - SP_EXPORT_REPORT_TO_DRIVE                            |
|  - POLICY_DOCUMENTS        - SP_APPROVE_POLICY_DOCUMENT                           |
|  - CONVERSATION_HISTORY    - DETECT_AML_SIGNALS (Task)                            |
|                            - RUN_DATA_QUALITY_CHECKS (Task)                       |
|                                                                                   |
|  [CORTEX AI LAYER]                                                                |
|  - AML_RISK_COPILOT (Cortex Agent)                                                |
|    - risk_analytics tool (Cortex Analyst + Semantic View)                          |
|    - policy_search tool (Cortex Search Service)                                   |
|  - AML_COPILOT_SV (Semantic View - 13 tables, 11 relationships, 7 VQRs)          |
|  - POLICY_SEARCH_SERVICE (Cortex Search - 11 policy documents)                    |
|                                                                                   |
|  [STREAMLIT APP]                                                                  |
|  - RISKLENS_APP (Streamlit-in-Snowflake)                                          |
|    - AI Copilot (ChatGPT-style interface with policy citations)                   |
|    - Dashboard (KPIs, signal trends, heatmap, risk feed)                          |
|    - Investigations (Customer 360, network analysis, risk explainability)          |
|    - Regulatory Reports (SAR generation, PDF export)                              |
|    - Evidence Center (policy search, data quality, case evidence)                 |
|    - CoCo Operations (pipeline health, architecture checklist)                    |
+-----------------------------------------------------------------------------------+
```

---

## Key Features

### Signal Detection Pipeline
- **6 deterministic rules**: Structuring, Rapid Movement, Velocity Spike, Unusual Geography, Dormant Activation, Beneficiary Burst
- Stream-triggered task runs every 5 minutes
- Each signal includes RULE_ID, TRIGGER_DETAIL, and EVIDENCE_JSON

### AI Copilot (Policy-Backed Answers)
- Every response has 5 sections: Summary, Evidence, Applicable Policy, Risk Assessment, Recommended Action
- Uses BOTH data (Cortex Analyst) and policy (Cortex Search) for every answer
- Citations show exact policy document title, jurisdiction, and quoted text
- Confidence assessment (HIGH/MEDIUM/LOW) on every response

### Investigation Workspace
- Customer Risk 360 with gauge chart and risk explainability donut
- Transaction timeline scatter plot (red = suspicious)
- Interactive beneficiary network visualization
- Signal-to-finding workflow: Signal -> Investigation -> Evidence -> Decision -> Report

### Regulatory Reporting
- AI-generated SAR narratives via Cortex Agent
- PDF reports with gradient headers via fpdf2
- Filing tracker and audit trail

---

## Tech Stack

| Component | Snowflake Feature |
|---|---|
| AI Copilot | Cortex Agent (`FROM SPECIFICATION`) |
| Data Queries | Cortex Analyst + Semantic View (13 tables, 7 VQRs) |
| Policy Search | Cortex Search Service (11 documents) |
| Signal Pipeline | Streams + Tasks + Stored Procedures |
| Real-time Analytics | Dynamic Tables (4 tables, 5-min lag) |
| Data Quality | Scheduled task (15-min) + quality checks |
| Application | Streamlit-in-Snowflake |
| PDF Generation | Python Stored Procedure (fpdf2) |
| All Development | Snowflake CoCo (Cortex Code) |

---

## Setup Instructions

### Prerequisites
- Snowflake account with Cortex AI features enabled
- ACCOUNTADMIN or equivalent role
- Warehouse (COMPUTE_WH or similar, X-Small sufficient)

### Step 1: Run the setup scripts in order

```sql
-- 1. Create database, schemas, and tables
@sql/01_schema_and_tables.sql

-- 2. Generate synthetic data
@sql/02_synthetic_data.sql

-- 3. Create pipeline objects (streams, tasks, stored procedures)
@sql/03_pipeline.sql

-- 4. Create Cortex AI objects (semantic view, search service, agent)
@sql/04_cortex_ai.sql

-- 5. Deploy the Streamlit app
@sql/05_deploy_app.sql
```

### Step 2: Access the app
Navigate to Snowsight > Streamlit > RISKLENS_APP

---

## Project Structure

```
risklens-ai/
  app/
    streamlit_app.py          # Main Streamlit application (82KB, 6 tabs)
  sql/
    01_schema_and_tables.sql   # Database, schema, table DDL
    02_synthetic_data.sql      # 500K+ rows of synthetic data
    03_pipeline.sql            # Stored procedures, streams, tasks
    04_cortex_ai.sql           # Semantic view, search service, agent
    05_deploy_app.sql          # Streamlit deployment
  docs/
    architecture.md            # Detailed architecture documentation
    MVP_SUBMISSION.md          # MVP/Prototype submission document
    RiskLens_AI_App_Preview.html  # Interactive HTML preview (no login required)
    screenshots/               # Live app screenshots for each tab
  README.md                    # This file
```

---

## Data Scale

| Object | Count |
|---|---|
| Customers | 10,000 |
| Transactions | 500,000 |
| Bank Accounts | 15,000 |
| Beneficiaries | 8,126 |
| AML Signals | 208 |
| Risk Cases | 50 |
| Case Evidence | 200 |
| Countries | 50 |
| Policy Documents | 11 |
| Detection Rules | 6 |
| Dynamic Tables | 4 |
| Scheduled Tasks | 2 |
| Verified Queries | 7 |

---

## CoCo Usage

Every component was built using Snowflake CoCo (Cortex Code):

- Synthetic data generation (500K+ transactions with realistic AML patterns)
- Complete schema design (13 tables, relationships, risk profiles)
- Semantic view with 13 tables, 11 relationships, custom instructions, 7 verified queries
- Cortex Agent with dual-tool orchestration (data + policy)
- 6-rule deterministic signal detection pipeline
- Dynamic tables for real-time analytics
- Cortex Search Service for policy document retrieval
- Streamlit-in-Snowflake application with 6 tabs
- PDF report generation stored procedure
- Data quality monitoring framework

---

## Deployed Application

- **Live App URL**: [https://app.snowflake.com/XVKVPMF-UJ52156/#/streamlit-apps/AML_COPILOT.RAW.RISKLENS_APP](https://app.snowflake.com/XVKVPMF-UJ52156/#/streamlit-apps/AML_COPILOT.RAW.RISKLENS_APP)
- **Account**: XVKVPMF-UJ52156
- **Access**: Requires Snowflake login to the account above

---

## License

Built for the Snowflake CoCo Hackathon. All data is synthetic for demonstration purposes.
