# AML Copilot — Data Model Documentation

**Database**: `AML_COPILOT`
**Account**: XVKVPMF-UJ52156
**Last Updated**: 2026-10-04

---

## 1. Solution Overview

The AML Copilot is an AI-powered Anti-Money Laundering investigation assistant built on Snowflake. It combines:

- **Deterministic, rule-based signal detection** that runs incrementally as new transactions arrive
- **Pre-computed risk features** that make real-time questions fast and consistent
- **Governed document ingestion** with approval workflows for regulatory policy documents
- **Cortex Search** for full-text policy retrieval
- **Cortex Analyst** (via Semantic View) for natural-language data queries
- **Cortex Agent** that orchestrates analytics and policy search with conversational AI
- **Streamlit-in-Snowflake** command center (RiskLens AI) with AI Copilot (ChatGPT-style), dashboards, investigations, regulatory reports, evidence center, and CoCo Operations
- **PDF report generation** for audit-ready investigation reports with gradient headers and formatted tables
- **Data quality monitoring** that enables confidence annotations in responses
- **Automatic audit logging** across all pipeline events
- **Policy-backed AI responses** — every copilot answer includes Summary, Evidence, Applicable Policy, Risk Assessment, Recommended Action, and Confidence level

The fundamental design principle is **deterministic detection first, AI reasoning second**:

```
DATA PIPELINE            →  Deterministic signals with RULE_ID + TRIGGER_DETAIL
AI INVESTIGATION LAYER   →  Cortex Agent explains, summarizes, compares — never invents signals
POLICY EVIDENCE          →  ALWAYS cites specific regulatory thresholds (dual-tool: data + policy)
REPORT GENERATION        →  PDF reports with gradient headers, case summary, signals, transactions
HUMAN DECISION           →  Analyst reviews, approves, escalates, or dismisses
```

---

## 2. Schema Architecture

```
AML_COPILOT
├── RAW           Source-of-truth tables (customer, transaction, signal, case, policy data)
├── PIPELINE      Operational infrastructure (streams, tasks, staging, DQ, audit)
└── ANALYTICS     Consumer-facing layer (dynamic tables, search index, DQ view)
```

| Schema | Purpose | Who consumes it |
|--------|---------|-----------------|
| `RAW` | Immutable source data, Cortex Agent, Semantic View, Streamlit app, conversation history. | Pipeline tasks, Semantic View, Agent, Streamlit UI |
| `PIPELINE` | Operational plumbing. Streams that detect new data, tasks that process it, staging tables for documents, DQ configuration, and audit trails. | Tasks (automated), stored procedures, Streamlit UI |
| `ANALYTICS` | Pre-computed, query-optimized surfaces. Dynamic tables refresh every 5 minutes. Cortex Search indexes approved policy documents. | Semantic View / Cortex Analyst, Copilot Agent, dashboards |

---

## 3. Data Elements — RAW Schema

These are the foundational tables containing all source data.

### 3.1 Core Entity Tables

| Table | Rows | Primary Key | Purpose | Key Columns | How It's Used |
|-------|------|-------------|---------|-------------|---------------|
| **CUSTOMERS** | 10,000 | CUSTOMER_ID | Master customer registry with KYC data. Every investigation starts and ends with a customer. | CUSTOMER_TYPE (INDIVIDUAL/CORPORATE/TRUST), RISK_RATING (LOW/MEDIUM/HIGH), PEP_FLAG, SANCTIONS_FLAG, COUNTRY_CODE, INDUSTRY, ANNUAL_INCOME | Joined to every transactional query. Risk rating and PEP/sanctions flags drive investigation priority. The copilot uses FIRST_NAME + LAST_NAME for name-based lookups. |
| **BANK_ACCOUNTS** | 15,000 | ACCOUNT_ID | Bank accounts linked to customers. One customer can have multiple accounts. | ACCOUNT_TYPE (CHECKING/SAVINGS/CREDIT/LOAN), CURRENT_BALANCE, STATUS (ACTIVE/DORMANT/CLOSED) | Links transactions to customers. Account status (DORMANT) is relevant for dormant-activation detection. Balance used in risk assessments. |
| **BENEFICIARIES** | 8,126 | BENEFICIARY_ID | Counterparties that receive funds. Key entities in fund-flow analysis. | BENEFICIARY_NAME, BENEFICIARY_TYPE, COUNTRY_CODE, BANK_NAME, RISK_SCORE (0-100), TRANSACTION_COUNT | Joined to transactions via BENEFICIARY_ID. Beneficiary country risk and risk score are used to assess counterparty exposure. Used in beneficiary network visualization. |
| **COUNTRIES** | 50 | COUNTRY_CODE | Reference table for country risk classification. Maps every country to a risk tier. | RISK_TIER (LOW/MEDIUM/HIGH/VERY_HIGH), FATF_LISTED (boolean), REGION | Joined to transactions (origin + destination), customers, and beneficiaries. HIGH/VERY_HIGH risk tiers and FATF listing drive the UNUSUAL_GEOGRAPHY detection rule. Central to geographic risk scoring. |
| **CUSTOMER_RISK_PROFILE** | 10,000 | CUSTOMER_ID (unique) | Composite risk scores per customer, decomposed into risk components. | OVERALL_RISK_SCORE (0-100), GEOGRAPHIC_RISK, PRODUCT_RISK, BEHAVIOR_RISK, EDD_REQUIRED, LAST_REVIEW_DATE, NEXT_REVIEW_DATE | Provides a multi-dimensional risk assessment. The copilot references behavior risk when explaining why a customer is flagged. EDD_REQUIRED flag identifies customers needing enhanced due diligence. |

### 3.2 Transaction Data

| Table | Rows | Primary Key | Purpose | Key Columns | How It's Used |
|-------|------|-------------|---------|-------------|---------------|
| **TRANSACTIONS** | 500,000 | TRANSACTION_ID | The core fact table. Every financial movement is recorded here. This is the primary input to all detection rules. | AMOUNT_USD, TRANSACTION_TYPE (WIRE/ACH/CASH/CARD/INTERNAL), CHANNEL (ONLINE/MOBILE/BRANCH/ATM), DIRECTION (INBOUND/OUTBOUND), ORIGIN_COUNTRY, DESTINATION_COUNTRY, IS_SUSPICIOUS, BENEFICIARY_ID, TRANSACTION_TIMESTAMP | Source for all 6 detection rules. Stream captures new inserts. Joined to customers, accounts, beneficiaries, and countries for enrichment. CHANGE_TRACKING = TRUE enables the append-only stream. |

### 3.3 Signal & Investigation Tables

| Table | Rows | Primary Key | Purpose | Key Columns | How It's Used |
|-------|------|-------------|---------|-------------|---------------|
| **AML_SIGNALS** | 208 | SIGNAL_ID | Detected AML risk signals. Each signal is produced by a specific deterministic rule and traced to exact transactions. | SIGNAL_TYPE (6 types), SIGNAL_SCORE (0-100), RULE_ID (e.g., RULE_STRUCT_001), TRIGGER_DETAIL (human-readable), EVIDENCE_JSON (structured evidence), TRANSACTION_IDS (array), DETECTION_RUN_ID, STATUS (NEW/UNDER_REVIEW/ESCALATED/DISMISSED) | The primary output of the detection pipeline. Each signal is fully traceable: RULE_ID identifies which rule fired, TRIGGER_DETAIL explains why in plain English, EVIDENCE_JSON contains the specific thresholds and values, and TRANSACTION_IDS links back to the source transactions. |
| **RISK_CASES** | 50 | CASE_ID | Investigation cases opened from one or more signals. Tracks the full lifecycle from opening through filing. | CASE_TYPE (SAR/STR/INTERNAL_REVIEW), STATUS (OPEN/CLOSED/FILED), PRIORITY (HIGH/MEDIUM/LOW), ASSIGNED_TO, FINDING_SUMMARY, FILING_REFERENCE, SIGNAL_IDS (array) | Represents the investigation workflow. Cases link to signals via SIGNAL_IDS. The copilot generates audit-ready reports by joining cases with evidence and policies. |
| **CASE_EVIDENCE** | 200 | EVIDENCE_ID | Supporting evidence items linked to investigation cases. | EVIDENCE_TYPE (TRANSACTION/SIGNAL/POLICY), REFERENCE_ID, DESCRIPTION, ADDED_BY | Provides the evidence chain for each case. REFERENCE_ID points to the specific transaction, signal, or policy being cited. Essential for audit-ready reporting. |
| **AML_GROUND_TRUTH** | 500 | SCENARIO_ID | Labeled AML scenarios for validation. Contains known-bad transaction patterns injected for testing. | TYPOLOGY (matches SIGNAL_TYPE), TRANSACTION_IDS (array), START_DATE, END_DATE | Used to validate detection accuracy. By comparing detected signals against ground truth scenarios, we can measure false-positive and false-negative rates per rule. |

### 3.4 Policy & Audit Tables

| Table | Rows | Primary Key | Purpose | Key Columns | How It's Used |
|-------|------|-------------|---------|-------------|---------------|
| **POLICY_DOCUMENTS** | 12 | DOC_ID | Approved AML/regulatory policy documents. The authoritative knowledge base for the copilot. | TITLE, CATEGORY (BSA_AML/AML/SANCTIONS_AML/KYC/CTF), JURISDICTION, EFFECTIVE_DATE, FULL_TEXT, STATUS | Provides the regulatory context for investigation. The copilot cites specific policies when explaining thresholds (e.g., "$10K CTR requirement"). Content is chunked and indexed by Cortex Search. |
| **AUDIT_LOG** | 0 | AUDIT_ID | Reserved for future copilot interaction logging. | USER_ID, QUESTION, RESPONSE | Placeholder for compliance audit trail of AI interactions. |
| **CONVERSATION_HISTORY** | varies | auto | Persists AI Copilot chat conversations for multi-turn continuity. | CONVERSATION_ID, USER_ID, TITLE, MESSAGE_ROLE, MESSAGE_CONTENT, MESSAGE_ORDER, AGENT_THREAD_ID, AGENT_PARENT_MESSAGE_ID, UPDATED_TIMESTAMP | Stores all user and assistant messages. Enables conversation resumption across sessions. Displayed in the Streamlit sidebar. |

---

## 4. Data Elements — PIPELINE Schema

Operational objects that power the incremental processing engine.

### 4.1 Streams

| Object | Type | Source | Purpose |
|--------|------|--------|---------|
| **STREAM_NEW_TRANSACTIONS** | Append-only Stream | RAW.TRANSACTIONS | Detects newly inserted transactions. The DETECT_AML_SIGNALS task only fires when this stream has data, ensuring incremental processing with no reprocessing of historical records. |

### 4.2 Tasks

| Object | Schedule | Trigger | Calls | Purpose |
|--------|----------|---------|-------|---------|
| **DETECT_AML_SIGNALS** | Every 5 minutes | `SYSTEM$STREAM_HAS_DATA('STREAM_NEW_TRANSACTIONS')` | `SP_DETECT_AML_SIGNALS()` | Core detection pipeline. Reads new transactions from stream, applies 6 deterministic rules, inserts signals into AML_SIGNALS with full evidence traceability. Only runs when new data exists. |
| **RUN_DATA_QUALITY_CHECKS** | Every 15 minutes | Always (scheduled) | `SP_RUN_DATA_QUALITY_CHECKS()` | Runs all active DQ checks against RAW.TRANSACTIONS and stores results. Enables the copilot to annotate responses with data confidence. |

### 4.3 Stored Procedures

| Procedure | Language | Parameters | Purpose |
|-----------|----------|------------|---------|
| **SP_DETECT_AML_SIGNALS()** | SQL | None | Implements 6 detection rules (see Section 9). Consumes the stream, runs each rule, logs the run. Writes PIPELINE_STARTED + SIGNAL_DETECTION_COMPLETED/FAILED to audit log. |
| **SP_PROCESS_POLICY_UPLOADS()** | SQL | None | Scans @POLICY_UPLOADS stage for new files. Validates, extracts text via AI_PARSE_DOCUMENT, extracts metadata via AI_EXTRACT. Invalid files go to DOCUMENT_QUARANTINE. |
| **SP_APPROVE_POLICY_DOCUMENT()** | JavaScript | DOC_ID, ACTION, REVIEWER, NOTES | Approval workflow. APPROVE: inserts into POLICY_DOCUMENTS, chunks for search. REJECT: updates status. Both write to audit log. |
| **SP_RUN_DATA_QUALITY_CHECKS()** | JavaScript | None | Runs active DQ checks, records results. Writes DQ_CHECK_RUN to audit log. |
| **SP_EXPORT_REPORT_TO_DRIVE()** | Python | P_CASE_ID, P_FOLDER_ID | Generates a styled PDF report (case summary, signals, transactions, evidence). Stores PDF binary in GENERATED_REPORTS. Writes REPORT_EXPORTED to audit log. |
| **SP_CREATE_RISK_CASE()** | SQL | P_CUSTOMER_ID, P_CASE_TYPE, P_ASSIGNED_TO | Creates a new investigation case from active signals. Validates customer exists, no open case already exists, and active signals are present. Computes priority from max signal score (>=80=HIGH, 60-79=MEDIUM, <60=LOW). Collects signal IDs into array, inserts case, updates NEW signals to UNDER_REVIEW. Writes CASE_CREATED to audit log. |

### 4.4 Stages

| Object | Type | Purpose |
|--------|------|---------|
| **POLICY_UPLOADS** | Internal stage (directory=TRUE) | Landing zone for new policy document uploads. |
| **EXPORTED_REPORTS** | Internal stage | Staging area for generated PDF reports. |
| **STREAMLIT_STAGE** | Internal stage | Hosts the Streamlit app source code. |

### 4.5 Pipeline Tables

| Table | Rows | Purpose | Key Columns | How It's Used |
|-------|------|---------|-------------|---------------|
| **SIGNAL_DETECTION_RUNS** | 1 | Audit trail of every detection run. Enables pipeline health monitoring. | RUN_ID, START_TIME, END_TIME, RECORDS_PROCESSED, SIGNALS_GENERATED, STATUS (COMPLETED/FAILED/RUNNING), ERROR_MESSAGE | The copilot can answer "is the pipeline working?" by querying this table. Shows processing throughput and error history. |
| **POLICY_DOCUMENTS_STAGED** | 1 | Documents awaiting human approval. Central to the governed ingestion workflow. | DOC_ID, TITLE, CATEGORY, JURISDICTION, EFFECTIVE_DATE, FULL_TEXT, STATUS (PENDING_APPROVAL/APPROVED/REJECTED), VERSION, IS_DUPLICATE, UPLOADED_BY, REVIEWED_BY, REVIEWED_AT | The Streamlit UI displays pending documents for review. Only APPROVED documents enter the search index. Tracks who uploaded, who reviewed, and any version relationships. |
| **DOCUMENT_QUARANTINE** | 0 | Invalid files that failed validation (wrong type, too large). | FILE_PATH, FILE_NAME, FILE_SIZE, REJECTION_REASON | Ensures only valid documents enter the processing pipeline. Provides transparency about rejected files. |
| **DOCUMENT_PROCESSING_LOG** | 1 | Step-by-step processing audit per document. | DOC_ID, FILE_PATH, STEP (VALIDATION/TEXT_EXTRACTION/METADATA_EXTRACTION/DUPLICATE_CHECK/STAGED), STATUS, DETAIL | Enables debugging when document processing fails. Shows exactly which step succeeded or failed. |
| **DATA_QUALITY_CHECKS** | 6 | Configuration table defining what DQ checks to run. | CHECK_ID, CHECK_NAME, TABLE_NAME, CHECK_SQL, SEVERITY (CRITICAL/WARNING), IS_ACTIVE | Each row defines a check: its SQL, which table it targets, and its severity. New checks can be added without code changes. |
| **DATA_QUALITY_RESULTS** | 1,524 | Historical DQ check results. One row per check per run. | RUN_ID, CHECK_ID, CHECK_NAME, RECORDS_CHECKED, RECORDS_FAILED, PASS_RATE, STATUS (PASS/FAIL/ERROR) | Tracks data quality over time. The latest results are surfaced via V_LATEST_DATA_QUALITY for the copilot. |
| **PIPELINE_AUDIT_LOG** | varies | Central audit trail for all pipeline events. Auto-populated by all stored procedures. | EVENT_TYPE, EVENT_SOURCE, ENTITY_TYPE, ENTITY_ID, DETAIL, USER_ID (SAMEEHA for manual, SYSTEM for tasks), LOGGED_AT | Unified audit log. See Section 12 for event types. |
| **GENERATED_REPORTS** | varies | Stores generated PDF investigation reports as binary data. | REPORT_ID (UUID), CASE_ID, FILENAME, PDF_DATA (BINARY), GENERATED_BY, GENERATED_AT | Served via st.download_button in Streamlit. |

---

## 5. Data Elements — ANALYTICS Schema

Pre-computed, query-optimized surfaces consumed by the Semantic View and Copilot Agent.

### 5.1 Dynamic Tables (auto-refresh every 5 minutes)

| Table | Rows | Source Tables | Purpose | Key Columns | Why It Exists |
|-------|------|---------------|---------|-------------|---------------|
| **DT_ENRICHED_TRANSACTIONS** | 500,374 | TRANSACTIONS + CUSTOMERS + COUNTRIES (x2) + BENEFICIARIES | Pre-joined transaction fact table with all dimensional enrichment. | All 17 TRANSACTIONS columns + CUSTOMER_RISK_RATING, CUSTOMER_TENURE_DAYS, DESTINATION_RISK_TIER, DESTINATION_FATF_LISTED, BENEFICIARY_RISK_SCORE, IS_HIGH_RISK_DESTINATION, IS_CROSS_BORDER, INVOLVES_FATF_COUNTRY, IS_HIGH_RISK_CUSTOMER (38 cols total) | Eliminates the need for 4-way joins on every query. Derived boolean flags (IS_HIGH_RISK_DESTINATION, IS_CROSS_BORDER, etc.) simplify copilot query generation. |
| **DT_CUSTOMER_RISK_FEATURES** | 10,000 | TRANSACTIONS + CUSTOMERS + COUNTRIES + AML_SIGNALS | Pre-computed behavioral risk features per customer across rolling time windows. | TXN_COUNT_1H, TXN_VOLUME_1H, TXN_COUNT_24H, TXN_VOLUME_24H, MAX_SINGLE_TXN_24H, UNIQUE_BENEFICIARIES_24H, TXN_COUNT_7D, TXN_VOLUME_7D, UNIQUE_BENEFICIARIES_7D, CASH_RATIO_7D_PCT, AVG_TXN_AMOUNT_30D, VOLUME_CHANGE_PERCENT, HIGH_RISK_COUNTRY_COUNT_7D, DORMANCY_DAYS, ACTIVE_SIGNAL_COUNT, MAX_SIGNAL_SCORE (22 cols) | **Critical for performance and consistency.** Without this, every behavioral question ("who has unusual volume?") would require complex window functions scanning 500K+ transactions. With this, the copilot queries pre-computed metrics directly. Ensures all users see the same numbers. |
| **DT_CUSTOMER_RISK_SUMMARY** | 10,000 | CUSTOMERS + TRANSACTIONS + AML_SIGNALS + RISK_CASES | One-row-per-customer dashboard combining transaction stats, signal counts by status, and case counts. | CUSTOMER_NAME, RISK_RATING, TOTAL_TRANSACTIONS, TOTAL_VOLUME_USD, SUSPICIOUS_TXN_COUNT, TOTAL_SIGNALS, NEW_SIGNALS, SIGNALS_UNDER_REVIEW, MAX_SIGNAL_SCORE, LATEST_SIGNAL_DATE, SIGNAL_TYPES (array), TOTAL_CASES, OPEN_CASES (20 cols) | The go-to table for "give me an overview of this customer" questions. Pre-aggregates everything the copilot needs to present a customer risk profile in a single query. |
| **DT_DAILY_SIGNAL_DASHBOARD** | 126 | AML_SIGNALS | Operational signal metrics aggregated by date, signal type, and rule ID. | SIGNAL_DATE, SIGNAL_TYPE, RULE_ID, SIGNAL_COUNT, AVG_SCORE, MAX_SCORE, ESCALATED_COUNT, ESCALATION_RATE_PCT, NEW_COUNT, DISMISSED_COUNT, AFFECTED_CUSTOMERS (11 cols) | Powers trend analysis ("which risk types are increasing?") and operational dashboards. Small table (126 rows) for instant query response. |

### 5.2 Search & Quality

| Object | Type | Purpose | Key Details |
|--------|------|---------|-------------|
| **POLICY_DOCUMENT_CHUNKS** | Table (11 rows) | Stores chunked text from approved policy documents for Cortex Search indexing. | CHUNK_TEXT (up to 1500 chars with 200-char overlap), TITLE, CATEGORY, JURISDICTION, STATUS (ACTIVE). Each approved document is split into overlapping chunks so that search can find relevant policy sections even for partial matches. |
| **POLICY_SEARCH_SERVICE** | Cortex Search Service | Full-text semantic search over approved policy documents. Target lag = 1 hour. | Searches on CHUNK_TEXT column with attribute filters on TITLE, CATEGORY, JURISDICTION. Uses `snowflake-arctic-embed-m-v1.5` for embeddings. The copilot calls this service when the user asks about applicable policies, regulatory thresholds, or compliance requirements. |
| **V_LATEST_DATA_QUALITY** | View | Surfaces the most recent DQ check results for the copilot to reference. | CHECK_NAME, TABLE_NAME, RECORDS_CHECKED, RECORDS_FAILED, PASS_RATE, STATUS, OVERALL_PASS_RATE. Allows the copilot to say "this conclusion is based on validated data with 100% pass rate" or "confidence is reduced because beneficiary data has a 98.5% pass rate." |

### 5.3 Semantic View

| Object | Purpose |
|--------|---------|
| **AML_COPILOT_SV** (in RAW schema) | The Semantic View that powers Cortex Analyst. Contains 13 table definitions, 11 relationships, 25 facts, 80+ dimensions, 7 verified queries (VQRs), and AI SQL generation instructions. Custom SQL instruction: "PREFER pre-computed tables: DT_CUSTOMER_RISK_SUMMARY for customer overviews, DT_DAILY_SIGNAL_DASHBOARD for signal trends, V_LATEST_DATA_QUALITY for DQ status." |

---

## 6. Cortex Agent

| Object | Value |
|--------|-------|
| **Name** | `AML_COPILOT.RAW.AML_RISK_COPILOT` |
| **Tools** | `risk_analytics` (Semantic View via Cortex Analyst, warehouse: COMPUTE_WH) + `policy_search` (Cortex Search) |
| **Model** | Auto (orchestration) — currently using claude-opus-4-8 |
| **Invocation** | REST API via `_snowflake.send_snow_api_request` from Streamlit |
| **Syntax** | `CREATE OR REPLACE AGENT ... FROM SPECIFICATION $$ yaml $$` |
| **Test** | `SNOWFLAKE.CORTEX.DATA_AGENT_RUN('AML_COPILOT.RAW.AML_RISK_COPILOT', '{json}', TRUE)` |
| **Critical Config** | `tool_resources.risk_analytics` MUST include `execution_environment: {type: warehouse, warehouse: COMPUTE_WH}` |

### Response Structure (enforced by agent instructions)
Every response must contain:
1. **Summary** — Direct answer in 2-3 sentences
2. **Evidence** — Data that supports the answer with specific numbers
3. **Applicable Policy** — Which AML/BSA/FATF policy applies with exact citation
4. **Risk Assessment** — Risk level grounded in both data and policy
5. **Recommended Action** — What the compliance analyst should do next
6. **Confidence** — HIGH/MEDIUM/LOW assessment

The agent ALWAYS uses BOTH tools for every question (data + policy).

The agent has 5 behavioral skills defined in its orchestration instructions:

| Skill | Purpose |
|-------|---------|
| **Risk Analytics** | Queries the Semantic View for customer risk, signals, transactions |
| **Risk Investigator** | Deep-dives into specific customers or signals |
| **Policy Interpreter** | Searches and cites regulatory policies via Cortex Search |
| **Evidence Validator** | Cross-references signals with transaction evidence |
| **Finding Generator** | Produces audit-ready investigation summaries |

Conversation history is persisted to `RAW.CONVERSATION_HISTORY` with thread-based multi-turn via `thread_id` + `parent_message_id` from agent metadata.

---

## 7. Streamlit Application (RiskLens AI)

| Object | Value |
|--------|-------|
| **Name** | `AML_COPILOT.RAW.RISKLENS_APP` |
| **Stage** | `@AML_COPILOT.RAW.STREAMLIT_STAGE` |
| **Warehouse** | `COMPUTE_WH` |
| **Size** | ~83KB |
| **Deploy** | `PUT 'file://path/streamlit_app.py' @AML_COPILOT.RAW.STREAMLIT_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE` |
| **Streamlit Constraints** | Old version — no `st.chat_input`, `st.chat_message`, `hide_index=True`, `type="primary"`, `st.rerun()` |

### Tabs (6 tabs, AI Copilot first)

| Tab | Purpose |
|-----|--------|
| **AI Copilot** (1st) | ChatGPT/Claude-style chat with message bubbles, 8 suggested questions, clickable follow-ups, policy citation evidence panel |
| **Dashboard** | 5 KPIs, signal trend, rule distribution, live risk feed, top-10 customers, signal heatmap |
| **Investigations** | Signal queue, Customer Risk 360 (gauge + donut explainability), transaction timeline, beneficiary network, inline AI actions |
| **Regulatory Reports** | SAR narrative generation, PDF export with gradient headers, filing tracker |
| **Evidence Center** | Evidence browser, direct Cortex Search for policies, data quality dashboard |
| **CoCo Operations** | CoCo-built components checklist, multi-agent orchestration diagram, pipeline health, document governance, audit log |

### Theme

- Header: Black-to-navy gradient with amber/orange logo (`#B55D0C`)
- Sidebar: Dark gradient with orange accents and detection rule tooltips
- Charts: Orange/navy/charcoal palette
- Font: Inter (Google Fonts)

---

## 9. Detection Rules

The pipeline implements 6 deterministic AML detection rules. Each produces a signal with a specific RULE_ID and a human-readable TRIGGER_DETAIL.

| Rule ID | Signal Type | Detection Logic | Score Range | Dedup Window |
|---------|-------------|-----------------|-------------|--------------|
| **RULE_STRUCT_001** | STRUCTURING | 3+ cash transactions < $10K from same customer within 24 hours, summing > $10K | 60–95 | 24h per customer |
| **RULE_RAPID_001** | RAPID_MOVEMENT | Inbound wire > $50K followed by outbound > 80% of inbound amount within 48 hours | 65–95 | 48h per customer |
| **RULE_VELOC_001** | VELOCITY_SPIKE | Today's transaction count > 3x the customer's 30-day daily average (min 5 historical txns) | 50–90 | 24h per customer |
| **RULE_GEO_001** | UNUSUAL_GEOGRAPHY | Transaction to HIGH or VERY_HIGH risk country with no prior transaction history to that country | 70–85 | 24h per customer per country |
| **RULE_DORM_001** | DORMANT_ACTIVATION | Transaction on an account with no activity in prior 90+ days | 55–90 | 7d per account |
| **RULE_BENEF_001** | BENEFICIARY_BURST | > 5 new unique beneficiaries (not seen > 7 days ago) within 7 days | 50–85 | 7d per customer |

**Key design decisions:**
- Each signal stores the specific values that triggered it (not just the type)
- TRIGGER_DETAIL is human-readable: *"4 transactions between $9,500–$9,999 within 24 hours, total $38,950"*
- EVIDENCE_JSON contains the structured thresholds for programmatic use
- Deduplication prevents the same rule from firing repeatedly for the same customer/account within the window

---

## 10. Document Ingestion Pipeline

The governed document ingestion follows this flow:

```
User uploads file → @POLICY_UPLOADS stage
       │
       ▼
SP_PROCESS_POLICY_UPLOADS()
       │
       ├── Validate (file type: PDF/DOCX/TXT, size: <50MB)
       │     ├── INVALID → DOCUMENT_QUARANTINE (with reason)
       │     └── VALID ↓
       │
       ├── AI_PARSE_DOCUMENT → full text extraction
       ├── AI_EXTRACT → title, category, jurisdiction, effective_date
       ├── Duplicate/version check (by title)
       │
       ▼
POLICY_DOCUMENTS_STAGED (STATUS = PENDING_APPROVAL)
       │
       ▼ (Human review via Streamlit or procedure call)
SP_APPROVE_POLICY_DOCUMENT(DOC_ID, 'APPROVE'/'REJECT', REVIEWER)
       │
       ├── REJECT → status updated, logged
       └── APPROVE ↓
             ├── Insert into RAW.POLICY_DOCUMENTS
             ├── Chunk text (1500 chars, 200 overlap)
             ├── Insert into POLICY_DOCUMENT_CHUNKS
             └── Cortex Search indexes within 1 hour
                    │
                    ▼
              Available to Copilot via POLICY_SEARCH_SERVICE
```

---

## 11. Data Quality Checks

| Check ID | Check Name | Table | Severity | What It Validates |
|----------|-----------|-------|----------|-------------------|
| DQ_001 | Amount USD positive | TRANSACTIONS | CRITICAL | Every transaction has AMOUNT_USD > 0 |
| DQ_002 | Account ID not null | TRANSACTIONS | CRITICAL | No transactions with missing ACCOUNT_ID |
| DQ_003 | Customer ID referential integrity | TRANSACTIONS | CRITICAL | Every CUSTOMER_ID in transactions exists in CUSTOMERS |
| DQ_004 | Destination country referential integrity | TRANSACTIONS | WARNING | Every DESTINATION_COUNTRY exists in COUNTRIES |
| DQ_005 | Beneficiary ID referential integrity | TRANSACTIONS | WARNING | Every BENEFICIARY_ID (where not null) exists in BENEFICIARIES |
| DQ_006 | Transaction timestamp not in future | TRANSACTIONS | WARNING | No transaction timestamps more than 1 hour in the future |

Results are available via `ANALYTICS.V_LATEST_DATA_QUALITY` and include `OVERALL_PASS_RATE` for copilot confidence annotations.

---

## 12. Audit Logging

All stored procedures automatically write to `PIPELINE.PIPELINE_AUDIT_LOG`. Events are generated:

| Event Type | Source Procedure | When |
|------------|-----------------|------|
| `PIPELINE_STARTED` | SP_DETECT_AML_SIGNALS | At the start of each signal detection run |
| `SIGNAL_DETECTION_COMPLETED` | SP_DETECT_AML_SIGNALS | After successful completion with record/signal counts |
| `SIGNAL_DETECTION_FAILED` | SP_DETECT_AML_SIGNALS | On error, with error message |
| `DQ_CHECK_RUN` | SP_RUN_DATA_QUALITY_CHECKS | After each DQ run with check count and failure count |
| `DOCUMENT_APPROVED` | SP_APPROVE_POLICY_DOCUMENT | When a document is approved, with title and chunk count |
| `DOCUMENT_REJECTED` | SP_APPROVE_POLICY_DOCUMENT | When a document is rejected, with title |
| `REPORT_EXPORTED` | SP_EXPORT_REPORT_TO_DRIVE | When a PDF report is generated, with filename |
| `CASE_CREATED` | SP_CREATE_RISK_CASE | When a new investigation case is created, with priority, signal count, and max score |

Task-triggered events show `USER_ID = SYSTEM`; manual procedure calls show the actual username.

---

## 13. Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          NEW TRANSACTIONS                                │
│                               │                                          │
│                               ▼                                          │
│                    RAW.TRANSACTIONS (INSERT)                             │
│                         │          │                                     │
│                         │          ▼                                     │
│                         │   PIPELINE.STREAM_NEW_TRANSACTIONS             │
│                         │          │                                     │
│                         │          ▼ (every 5 min when data exists)      │
│                         │   TASK: DETECT_AML_SIGNALS                     │
│                         │          │                                     │
│                         │          ├── 6 deterministic rules             │
│                         │          │                                     │
│                         │          ▼                                     │
│                         │   RAW.AML_SIGNALS (new signals)                │
│                         │   PIPELINE.SIGNAL_DETECTION_RUNS (audit)       │
│                         │                                                │
│                         ▼ (every 5 min, auto-refresh)                    │
│              ┌─── ANALYTICS.DT_ENRICHED_TRANSACTIONS                     │
│              ├─── ANALYTICS.DT_CUSTOMER_RISK_FEATURES                    │
│              ├─── ANALYTICS.DT_CUSTOMER_RISK_SUMMARY                     │
│              └─── ANALYTICS.DT_DAILY_SIGNAL_DASHBOARD                    │
│                         │                                                │
│                         ▼                                                │
│              SEMANTIC VIEW (AML_COPILOT_SV)                              │
│                         │                                                │
│                         ▼                                                │
│              CORTEX ANALYST / AGENT (natural language queries)            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                       POLICY DOCUMENT UPLOAD                             │
│                               │                                          │
│                               ▼                                          │
│                    @PIPELINE.POLICY_UPLOADS (stage)                       │
│                               │                                          │
│                               ▼                                          │
│                    SP_PROCESS_POLICY_UPLOADS()                            │
│                    (validate → extract → classify → stage)                │
│                               │                                          │
│                    ┌──────────┴──────────┐                               │
│                    ▼                     ▼                                │
│              QUARANTINE            STAGED (PENDING_APPROVAL)             │
│                                          │                               │
│                                    Human Review                          │
│                                          │                               │
│                               SP_APPROVE_POLICY_DOCUMENT()               │
│                                    │           │                         │
│                                 REJECT      APPROVE                      │
│                                                │                         │
│                                    ┌───────────┤                         │
│                                    ▼           ▼                         │
│                          RAW.POLICY_DOCUMENTS  POLICY_DOCUMENT_CHUNKS    │
│                                                │                         │
│                                                ▼                         │
│                                    POLICY_SEARCH_SERVICE                  │
│                                    (Cortex Search, 1h lag)               │
│                                                │                         │
│                                                ▼                         │
│                                    Available to Copilot Agent             │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                       DATA QUALITY MONITORING                            │
│                               │                                          │
│                    TASK: RUN_DATA_QUALITY_CHECKS (every 15 min)           │
│                               │                                          │
│                    DATA_QUALITY_CHECKS (6 check definitions)             │
│                               │                                          │
│                               ▼                                          │
│                    DATA_QUALITY_RESULTS (historical)                      │
│                               │                                          │
│                               ▼                                          │
│                    V_LATEST_DATA_QUALITY (latest run only)                │
│                               │                                          │
│                               ▼                                          │
│                    Copilot cites: "Based on validated data, 100% pass"   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 14. Relationship Map

```
CUSTOMERS ──────────────┬── 1:N ── BANK_ACCOUNTS ── 1:N ── TRANSACTIONS
    │                   │                                       │
    │                   ├── 1:1 ── CUSTOMER_RISK_PROFILE         ├── N:1 ── BENEFICIARIES
    │                   │                                       │
    │                   ├── 1:N ── AML_SIGNALS                   ├── N:1 ── COUNTRIES (origin)
    │                   │              │                         │
    │                   │              └── N:1 ── DETECTION_RUNS  ├── N:1 ── COUNTRIES (dest)
    │                   │                                       │
    │                   ├── 1:N ── RISK_CASES                    └── N:1 ── BANK_ACCOUNTS
    │                   │              │
    │                   │              └── 1:N ── CASE_EVIDENCE
    │                   │
    │                   ├── 1:1 ── DT_CUSTOMER_RISK_FEATURES
    │                   │
    │                   └── 1:1 ── DT_CUSTOMER_RISK_SUMMARY
    │
    └── N:1 ── COUNTRIES (customer country)
```

---

## 15. Verified Queries (7 total)

The Semantic View includes 7 verified queries (VQRs) that Cortex Analyst uses as reference patterns.

| VQR Name | Question | Onboarding? |
|----------|----------|-------------|
| TOTAL_SIGNALS | How many AML signals are there? | Yes |
| SIGNALS_BY_TYPE | Show AML signals by type | Yes |
| HIGH_RISK_CUSTOMERS | Which customers have the highest risk? | Yes |
| OPEN_CASES | How many open investigation cases are there? | No |
| SIGNAL_TRENDS | What are the daily signal trends? | Yes |
| DATA_QUALITY_STATUS | What is the data quality status? | No |
| NEW_SIGNALS | How many new unreviewed signals are there? | No |

---

## 16. Object Inventory Summary

| Category | Count | Details |
|----------|-------|---------|
| Schemas | 3 | RAW, PIPELINE, ANALYTICS |
| Tables (RAW) | 13 | Source entity, transaction, signal, case, policy, audit, conversation history tables |
| Tables (PIPELINE) | 7 | DQ checks/results, document staging, detection runs, audit log, generated reports |
| Dynamic Tables | 4 | Enriched transactions, risk features, risk summary, signal dashboard |
| Regular Tables (ANALYTICS) | 1 | Policy document chunks |
| Views | 1 | V_LATEST_DATA_QUALITY |
| Streams | 1 | STREAM_NEW_TRANSACTIONS (append-only) |
| Tasks | 2 | DETECT_AML_SIGNALS (5 min), RUN_DATA_QUALITY_CHECKS (15 min) |
| Stored Procedures | 6 | Signal detection (SQL), document processing, document approval (JS), DQ checks (JS), PDF export (Python/fpdf2), case creation (SQL) |
| Stages | 1 | STREAMLIT_STAGE |
| Cortex Search Services | 1 | POLICY_SEARCH_SERVICE (1h lag, 13 indexed rows) |
| Cortex Agent | 1 | AML_RISK_COPILOT (2 tools, warehouse: COMPUTE_WH, policy-backed responses) |
| Semantic Views | 1 | AML_COPILOT_SV (7 VQRs, 13 tables, 11 relationships, AI_SQL_GENERATION instruction) |
| Streamlit Apps | 1 | RISKLENS_APP (6 tabs, ChatGPT-style AI Copilot, 83KB) |
| **Total objects** | **~42** | |
