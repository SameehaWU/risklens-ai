-- ============================================================
-- RiskLens AI - All Stored Procedures
-- Complete DDL for all pipeline stored procedures
-- ============================================================

USE DATABASE AML_COPILOT;
USE SCHEMA PIPELINE;
USE WAREHOUSE COMPUTE_WH;

-- ============================================================
-- SP_DETECT_AML_SIGNALS: 6-rule deterministic detection engine
-- Language: SQL | Trigger: Stream-based task (5-min)
-- Rules:
--   RULE_STRUCT_001: Structuring (3+ cash txns <$10K summing >$10K in 24h)
--   RULE_RAPID_001: Rapid Movement (inbound >$50K, outbound >80% in 48h)
--   RULE_VELOC_001: Velocity Spike (txn count >3x 30-day daily avg)
--   RULE_GEO_001:   Unusual Geography (txn to HIGH-risk country, no prior)
--   RULE_DORM_001:  Dormant Activation (txn after 90+ days inactivity)
--   RULE_BENEF_001: Beneficiary Burst (>5 new beneficiaries in 7 days)
-- ============================================================

CREATE OR REPLACE PROCEDURE SP_DETECT_AML_SIGNALS()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS '
BEGIN
    LET run_id VARCHAR := ''RUN_'' || TO_VARCHAR(CURRENT_TIMESTAMP(), ''YYYYMMDD_HH24MISS'');
    LET start_ts TIMESTAMP_NTZ := CURRENT_TIMESTAMP();
    LET records_processed NUMBER := 0;
    LET signals_generated NUMBER := 0;
    LET max_existing_sig NUMBER;

    INSERT INTO AML_COPILOT.PIPELINE.PIPELINE_AUDIT_LOG (EVENT_TYPE, EVENT_SOURCE, ENTITY_TYPE, ENTITY_ID, DETAIL, USER_ID)
    VALUES (''PIPELINE_STARTED'', ''SP_DETECT_AML_SIGNALS'', ''PIPELINE'', :run_id, ''Signal detection pipeline started'', CURRENT_USER());

    INSERT INTO AML_COPILOT.PIPELINE.SIGNAL_DETECTION_RUNS (RUN_ID, START_TIME, STATUS)
    VALUES (:run_id, :start_ts, ''RUNNING'');

    SELECT COALESCE(MAX(CAST(REPLACE(SIGNAL_ID, ''SIG_'', '''') AS NUMBER)), 0) INTO :max_existing_sig
    FROM AML_COPILOT.RAW.AML_SIGNALS;

    SELECT COUNT(*) INTO :records_processed FROM AML_COPILOT.PIPELINE.STREAM_NEW_TRANSACTIONS;

    -- RULE 1: STRUCTURING
    INSERT INTO AML_COPILOT.RAW.AML_SIGNALS (SIGNAL_ID, CUSTOMER_ID, SIGNAL_TYPE, SIGNAL_SCORE, RULE_ID, TRIGGER_DETAIL, EVIDENCE_JSON, TRANSACTION_IDS, DETECTION_RUN_ID, DESCRIPTION, STATUS, DETECTION_TIMESTAMP)
    SELECT
        ''SIG_'' || LPAD(ROW_NUMBER() OVER (ORDER BY s.CUSTOMER_ID) + :max_existing_sig, 8, ''0''),
        s.CUSTOMER_ID, ''STRUCTURING'',
        LEAST(95, GREATEST(60, 60 + (s.txn_count - 3) * 5 + ROUND((s.total_amount - 10000) / 5000))),
        ''RULE_STRUCT_001'',
        s.txn_count || '' cash transactions totaling $'' || ROUND(s.total_amount,0) || '' within 24h'',
        OBJECT_CONSTRUCT(''rule'',''STRUCT_001'',''threshold'',10000,''actual_total'',ROUND(s.total_amount,2),''txn_count'',s.txn_count),
        s.txn_ids, :run_id, ''Potential structuring detected'', ''NEW'', CURRENT_TIMESTAMP()
    FROM (
        SELECT t.CUSTOMER_ID, COUNT(*) AS txn_count, SUM(t.AMOUNT_USD) AS total_amount,
            ARRAY_AGG(t.TRANSACTION_ID) AS txn_ids
        FROM AML_COPILOT.PIPELINE.STREAM_NEW_TRANSACTIONS t
        WHERE t.TRANSACTION_TYPE = ''CASH'' AND t.AMOUNT_USD < 10000 AND t.AMOUNT_USD >= 2000
        GROUP BY t.CUSTOMER_ID, DATE_TRUNC(''DAY'', t.TRANSACTION_TIMESTAMP)
        HAVING COUNT(*) >= 3 AND SUM(t.AMOUNT_USD) > 10000
    ) s
    WHERE NOT EXISTS (
        SELECT 1 FROM AML_COPILOT.RAW.AML_SIGNALS ex WHERE ex.CUSTOMER_ID = s.CUSTOMER_ID AND ex.RULE_ID = ''RULE_STRUCT_001'' AND ex.DETECTION_TIMESTAMP > DATEADD(''HOUR'', -24, CURRENT_TIMESTAMP())
    );
    LET struct_count NUMBER := SQLROWCOUNT;

    -- RULE 2: RAPID MOVEMENT
    INSERT INTO AML_COPILOT.RAW.AML_SIGNALS (SIGNAL_ID, CUSTOMER_ID, SIGNAL_TYPE, SIGNAL_SCORE, RULE_ID, TRIGGER_DETAIL, EVIDENCE_JSON, TRANSACTION_IDS, DETECTION_RUN_ID, DESCRIPTION, STATUS, DETECTION_TIMESTAMP)
    SELECT
        ''SIG_'' || LPAD(ROW_NUMBER() OVER (ORDER BY r.CUSTOMER_ID) + :max_existing_sig + :struct_count, 8, ''0''),
        r.CUSTOMER_ID, ''RAPID_MOVEMENT'',
        LEAST(95, GREATEST(65, 65 + ROUND(r.outbound_pct - 80))),
        ''RULE_RAPID_001'',
        ''Inbound wire $'' || ROUND(r.inbound_amount,0) || '', outbound $'' || ROUND(r.outbound_amount,0) || '' ('' || ROUND(r.outbound_pct,0) || ''%) within 48h'',
        OBJECT_CONSTRUCT(''rule'',''RAPID_001'',''inbound'',ROUND(r.inbound_amount,2),''outbound'',ROUND(r.outbound_amount,2),''pct'',ROUND(r.outbound_pct,1)),
        r.txn_ids, :run_id, ''Rapid fund movement detected'', ''NEW'', CURRENT_TIMESTAMP()
    FROM (
        SELECT inb.CUSTOMER_ID, inb.AMOUNT_USD AS inbound_amount,
            SUM(outb.AMOUNT_USD) AS outbound_amount,
            ROUND(SUM(outb.AMOUNT_USD) / inb.AMOUNT_USD * 100, 1) AS outbound_pct,
            ARRAY_CONSTRUCT(inb.TRANSACTION_ID, ARRAY_AGG(outb.TRANSACTION_ID)[0]) AS txn_ids
        FROM AML_COPILOT.PIPELINE.STREAM_NEW_TRANSACTIONS inb
        JOIN AML_COPILOT.RAW.TRANSACTIONS outb ON inb.CUSTOMER_ID = outb.CUSTOMER_ID AND outb.DIRECTION = ''OUTBOUND''
            AND outb.TRANSACTION_TIMESTAMP BETWEEN inb.TRANSACTION_TIMESTAMP AND DATEADD(''HOUR'', 48, inb.TRANSACTION_TIMESTAMP)
        WHERE inb.TRANSACTION_TYPE = ''WIRE'' AND inb.DIRECTION = ''INBOUND'' AND inb.AMOUNT_USD > 50000
        GROUP BY inb.CUSTOMER_ID, inb.TRANSACTION_ID, inb.AMOUNT_USD
        HAVING ROUND(SUM(outb.AMOUNT_USD) / inb.AMOUNT_USD * 100, 1) >= 80
    ) r
    WHERE NOT EXISTS (SELECT 1 FROM AML_COPILOT.RAW.AML_SIGNALS ex WHERE ex.CUSTOMER_ID = r.CUSTOMER_ID AND ex.RULE_ID = ''RULE_RAPID_001'' AND ex.DETECTION_TIMESTAMP > DATEADD(''HOUR'', -48, CURRENT_TIMESTAMP()));
    LET rapid_count NUMBER := SQLROWCOUNT;

    -- RULE 3: VELOCITY SPIKE
    INSERT INTO AML_COPILOT.RAW.AML_SIGNALS (SIGNAL_ID, CUSTOMER_ID, SIGNAL_TYPE, SIGNAL_SCORE, RULE_ID, TRIGGER_DETAIL, EVIDENCE_JSON, TRANSACTION_IDS, DETECTION_RUN_ID, DESCRIPTION, STATUS, DETECTION_TIMESTAMP)
    SELECT
        ''SIG_'' || LPAD(ROW_NUMBER() OVER (ORDER BY v.CUSTOMER_ID) + :max_existing_sig + :struct_count + :rapid_count, 8, ''0''),
        v.CUSTOMER_ID, ''VELOCITY_SPIKE'',
        LEAST(90, GREATEST(50, 50 + ROUND(v.multiplier * 10))),
        ''RULE_VELOC_001'',
        v.today_count || '' transactions today vs '' || ROUND(v.avg_daily,1) || '' daily avg'',
        OBJECT_CONSTRUCT(''rule'',''VELOC_001'',''today_count'',v.today_count,''avg_count'',ROUND(v.avg_daily,1),''multiplier'',ROUND(v.multiplier,2)),
        v.txn_ids, :run_id, ''Unusual velocity spike detected'', ''NEW'', CURRENT_TIMESTAMP()
    FROM (
        SELECT n.CUSTOMER_ID, COUNT(*) AS today_count, hist.avg_daily,
            COUNT(*) / NULLIF(hist.avg_daily, 0) AS multiplier,
            ARRAY_AGG(n.TRANSACTION_ID) AS txn_ids
        FROM AML_COPILOT.PIPELINE.STREAM_NEW_TRANSACTIONS n
        JOIN (SELECT CUSTOMER_ID, COUNT(*) / NULLIF(DATEDIFF(''DAY'', MIN(TRANSACTION_TIMESTAMP), MAX(TRANSACTION_TIMESTAMP)), 0) AS avg_daily
              FROM AML_COPILOT.RAW.TRANSACTIONS WHERE TRANSACTION_TIMESTAMP >= DATEADD(''DAY'', -30, CURRENT_TIMESTAMP()) GROUP BY CUSTOMER_ID HAVING COUNT(*) >= 5
        ) hist ON n.CUSTOMER_ID = hist.CUSTOMER_ID
        WHERE DATE_TRUNC(''DAY'', n.TRANSACTION_TIMESTAMP) = CURRENT_DATE()
        GROUP BY n.CUSTOMER_ID, hist.avg_daily HAVING COUNT(*) > hist.avg_daily * 3
    ) v
    WHERE NOT EXISTS (SELECT 1 FROM AML_COPILOT.RAW.AML_SIGNALS ex WHERE ex.CUSTOMER_ID = v.CUSTOMER_ID AND ex.RULE_ID = ''RULE_VELOC_001'' AND ex.DETECTION_TIMESTAMP > DATEADD(''HOUR'', -24, CURRENT_TIMESTAMP()));
    LET veloc_count NUMBER := SQLROWCOUNT;

    -- RULE 4: UNUSUAL GEOGRAPHY
    INSERT INTO AML_COPILOT.RAW.AML_SIGNALS (SIGNAL_ID, CUSTOMER_ID, SIGNAL_TYPE, SIGNAL_SCORE, RULE_ID, TRIGGER_DETAIL, EVIDENCE_JSON, TRANSACTION_IDS, DETECTION_RUN_ID, DESCRIPTION, STATUS, DETECTION_TIMESTAMP)
    SELECT
        ''SIG_'' || LPAD(ROW_NUMBER() OVER (ORDER BY g.CUSTOMER_ID) + :max_existing_sig + :struct_count + :rapid_count + :veloc_count, 8, ''0''),
        g.CUSTOMER_ID, ''UNUSUAL_GEOGRAPHY'',
        CASE g.RISK_TIER WHEN ''VERY_HIGH'' THEN 82 ELSE 73 END,
        ''RULE_GEO_001'',
        ''Wire to '' || g.DESTINATION_COUNTRY || '' ('' || g.RISK_TIER || '' risk), no prior history'',
        OBJECT_CONSTRUCT(''rule'',''GEO_001'',''country'',g.DESTINATION_COUNTRY,''risk_tier'',g.RISK_TIER),
        ARRAY_CONSTRUCT(g.TRANSACTION_ID), :run_id, ''Unusual geography detected'', ''NEW'', CURRENT_TIMESTAMP()
    FROM (
        SELECT n.CUSTOMER_ID, n.TRANSACTION_ID, n.DESTINATION_COUNTRY, c.RISK_TIER
        FROM AML_COPILOT.PIPELINE.STREAM_NEW_TRANSACTIONS n
        JOIN AML_COPILOT.RAW.COUNTRIES c ON n.DESTINATION_COUNTRY = c.COUNTRY_CODE
        WHERE c.RISK_TIER IN (''HIGH'', ''VERY_HIGH'')
        AND NOT EXISTS (SELECT 1 FROM AML_COPILOT.RAW.TRANSACTIONS h WHERE h.CUSTOMER_ID = n.CUSTOMER_ID AND h.DESTINATION_COUNTRY = n.DESTINATION_COUNTRY AND h.TRANSACTION_ID != n.TRANSACTION_ID)
    ) g
    WHERE NOT EXISTS (SELECT 1 FROM AML_COPILOT.RAW.AML_SIGNALS ex WHERE ex.CUSTOMER_ID = g.CUSTOMER_ID AND ex.RULE_ID = ''RULE_GEO_001'' AND ex.DETECTION_TIMESTAMP > DATEADD(''HOUR'', -24, CURRENT_TIMESTAMP()));
    LET geo_count NUMBER := SQLROWCOUNT;

    -- RULE 5: DORMANT ACTIVATION
    INSERT INTO AML_COPILOT.RAW.AML_SIGNALS (SIGNAL_ID, CUSTOMER_ID, SIGNAL_TYPE, SIGNAL_SCORE, RULE_ID, TRIGGER_DETAIL, EVIDENCE_JSON, TRANSACTION_IDS, DETECTION_RUN_ID, DESCRIPTION, STATUS, DETECTION_TIMESTAMP)
    SELECT
        ''SIG_'' || LPAD(ROW_NUMBER() OVER (ORDER BY d.CUSTOMER_ID) + :max_existing_sig + :struct_count + :rapid_count + :veloc_count + :geo_count, 8, ''0''),
        d.CUSTOMER_ID, ''DORMANT_ACTIVATION'',
        LEAST(90, GREATEST(55, 55 + ROUND(d.dormancy_days / 10))),
        ''RULE_DORM_001'',
        ''Transaction after '' || d.dormancy_days || '' days of dormancy'',
        OBJECT_CONSTRUCT(''rule'',''DORM_001'',''dormancy_days'',d.dormancy_days,''threshold'',90),
        ARRAY_CONSTRUCT(d.TRANSACTION_ID), :run_id, ''Dormant account activated'', ''NEW'', CURRENT_TIMESTAMP()
    FROM (
        SELECT n.CUSTOMER_ID, n.TRANSACTION_ID, n.ACCOUNT_ID,
            DATEDIFF(''DAY'', MAX(h.TRANSACTION_TIMESTAMP), n.TRANSACTION_TIMESTAMP) AS dormancy_days
        FROM AML_COPILOT.PIPELINE.STREAM_NEW_TRANSACTIONS n
        JOIN AML_COPILOT.RAW.TRANSACTIONS h ON n.ACCOUNT_ID = h.ACCOUNT_ID AND h.TRANSACTION_ID != n.TRANSACTION_ID
        GROUP BY n.CUSTOMER_ID, n.TRANSACTION_ID, n.ACCOUNT_ID, n.TRANSACTION_TIMESTAMP
        HAVING DATEDIFF(''DAY'', MAX(h.TRANSACTION_TIMESTAMP), n.TRANSACTION_TIMESTAMP) >= 90
    ) d
    WHERE NOT EXISTS (SELECT 1 FROM AML_COPILOT.RAW.AML_SIGNALS ex WHERE ex.CUSTOMER_ID = d.CUSTOMER_ID AND ex.RULE_ID = ''RULE_DORM_001'' AND ex.DETECTION_TIMESTAMP > DATEADD(''DAY'', -7, CURRENT_TIMESTAMP()));
    LET dorm_count NUMBER := SQLROWCOUNT;

    -- RULE 6: BENEFICIARY BURST
    INSERT INTO AML_COPILOT.RAW.AML_SIGNALS (SIGNAL_ID, CUSTOMER_ID, SIGNAL_TYPE, SIGNAL_SCORE, RULE_ID, TRIGGER_DETAIL, EVIDENCE_JSON, TRANSACTION_IDS, DETECTION_RUN_ID, DESCRIPTION, STATUS, DETECTION_TIMESTAMP)
    SELECT
        ''SIG_'' || LPAD(ROW_NUMBER() OVER (ORDER BY bb.CUSTOMER_ID) + :max_existing_sig + :struct_count + :rapid_count + :veloc_count + :geo_count + :dorm_count, 8, ''0''),
        bb.CUSTOMER_ID, ''BENEFICIARY_BURST'',
        LEAST(85, GREATEST(50, 50 + (bb.new_ben_count - 5) * 5)),
        ''RULE_BENEF_001'',
        bb.new_ben_count || '' new beneficiaries within 7 days'',
        OBJECT_CONSTRUCT(''rule'',''BENEF_001'',''new_beneficiaries'',bb.new_ben_count,''window_days'',7,''threshold'',5),
        bb.txn_ids, :run_id, ''Rapid beneficiary expansion detected'', ''NEW'', CURRENT_TIMESTAMP()
    FROM (
        SELECT n.CUSTOMER_ID, COUNT(DISTINCT n.BENEFICIARY_ID) AS new_ben_count, ARRAY_AGG(DISTINCT n.TRANSACTION_ID) AS txn_ids
        FROM AML_COPILOT.PIPELINE.STREAM_NEW_TRANSACTIONS n
        WHERE n.BENEFICIARY_ID IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM AML_COPILOT.RAW.TRANSACTIONS h WHERE h.CUSTOMER_ID = n.CUSTOMER_ID AND h.BENEFICIARY_ID = n.BENEFICIARY_ID AND h.TRANSACTION_TIMESTAMP < DATEADD(''DAY'', -7, n.TRANSACTION_TIMESTAMP))
        GROUP BY n.CUSTOMER_ID HAVING COUNT(DISTINCT n.BENEFICIARY_ID) > 5
    ) bb
    WHERE NOT EXISTS (SELECT 1 FROM AML_COPILOT.RAW.AML_SIGNALS ex WHERE ex.CUSTOMER_ID = bb.CUSTOMER_ID AND ex.RULE_ID = ''RULE_BENEF_001'' AND ex.DETECTION_TIMESTAMP > DATEADD(''DAY'', -7, CURRENT_TIMESTAMP()));
    LET benef_count NUMBER := SQLROWCOUNT;

    signals_generated := :struct_count + :rapid_count + :veloc_count + :geo_count + :dorm_count + :benef_count;

    UPDATE AML_COPILOT.PIPELINE.SIGNAL_DETECTION_RUNS
    SET END_TIME = CURRENT_TIMESTAMP(), RECORDS_PROCESSED = :records_processed, SIGNALS_GENERATED = :signals_generated, STATUS = ''COMPLETED''
    WHERE RUN_ID = :run_id;

    INSERT INTO AML_COPILOT.PIPELINE.PIPELINE_AUDIT_LOG (EVENT_TYPE, EVENT_SOURCE, ENTITY_TYPE, ENTITY_ID, DETAIL, USER_ID)
    VALUES (''SIGNAL_DETECTION_COMPLETED'', ''SP_DETECT_AML_SIGNALS'', ''PIPELINE'', :run_id,
        ''Processed '' || :records_processed || '' records, generated '' || :signals_generated || '' signals'', CURRENT_USER());

    RETURN ''Completed: '' || :signals_generated || '' signals from '' || :records_processed || '' new transactions'';
EXCEPTION
    WHEN OTHER THEN
        UPDATE AML_COPILOT.PIPELINE.SIGNAL_DETECTION_RUNS SET END_TIME = CURRENT_TIMESTAMP(), STATUS = ''FAILED'', ERROR_MESSAGE = SQLERRM WHERE RUN_ID = :run_id;
        INSERT INTO AML_COPILOT.PIPELINE.PIPELINE_AUDIT_LOG (EVENT_TYPE, EVENT_SOURCE, ENTITY_TYPE, ENTITY_ID, DETAIL, USER_ID)
        VALUES (''SIGNAL_DETECTION_FAILED'', ''SP_DETECT_AML_SIGNALS'', ''PIPELINE'', :run_id, SQLERRM, CURRENT_USER());
        RETURN ''Failed: '' || SQLERRM;
END;
';


-- ============================================================
-- SP_EXPORT_REPORT_TO_DRIVE: PDF Report Generation
-- Language: Python (fpdf2) | Generates AML investigation PDF
-- ============================================================

CREATE OR REPLACE PROCEDURE SP_EXPORT_REPORT_TO_DRIVE(P_CASE_ID VARCHAR)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
ARTIFACT_REPOSITORY = snowflake.snowpark.pypi_shared_repository
PACKAGES = ('snowflake-snowpark-python','fpdf2')
HANDLER = 'main'
EXECUTE AS CALLER
AS '
import snowflake.snowpark as snowpark
from fpdf import FPDF
import uuid
from datetime import datetime

def safe_str(val):
    if val is None:
        return ""
    return str(val)

class AMLReport(FPDF):
    BR, BG, BB = 184, 101, 27

    def _gradient_rect(self, x, y, w, h, r1, g1, b1, r2, g2, b2, steps=60):
        sw = w / steps
        for i in range(steps):
            f = i / (steps - 1)
            r = int(r1 + (r2 - r1) * f)
            g = int(g1 + (g2 - g1) * f)
            b = int(b1 + (b2 - b1) * f)
            self.set_fill_color(r, g, b)
            self.rect(x + i * sw, y, sw + 0.5, h, "F")

    def _section_bar(self, title):
        self.set_fill_color(self.BR, self.BG, self.BB)
        self.set_draw_color(self.BR, self.BG, self.BB)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 11)
        x0 = self.l_margin
        w = self.w - self.l_margin - self.r_margin
        self.set_x(x0)
        self.cell(w, 8, "  " + title, ln=True, fill=True, border=1)
        self.set_text_color(0, 0, 0)
        self.set_draw_color(0, 0, 0)
        self.ln(1)

    def _table_header(self, widths, names):
        self.set_fill_color(self.BR, self.BG, self.BB)
        self.set_draw_color(80, 80, 80)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 7)
        self.set_x(self.l_margin)
        for i, n in enumerate(names):
            self.cell(widths[i], 6, n, border=1, fill=True, align="L")
        self.ln()
        self.set_text_color(0, 0, 0)

    def _table_row(self, widths, vals, fill=False):
        if fill:
            self.set_fill_color(245, 240, 235)
        else:
            self.set_fill_color(255, 255, 255)
        self.set_draw_color(180, 180, 180)
        self.set_font("Helvetica", "", 7)
        self.set_x(self.l_margin)
        for i, v in enumerate(vals):
            self.cell(widths[i], 5.5, safe_str(v)[:60], border=1, fill=True, align="L")
        self.ln()

    def footer(self):
        self.set_y(-18)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(130, 130, 130)
        self.cell(0, 8, "RiskLens AML Command Center  |  Powered by Snowflake Cortex Agent  |  Confidential", align="C")

def main(session: snowpark.Session, P_CASE_ID: str) -> str:
    case_df = session.sql(f"""
        SELECT rc.CASE_ID, rc.CUSTOMER_ID, rc.CASE_TYPE, rc.STATUS, rc.PRIORITY,
               rc.FINDING_SUMMARY, rc.FILING_REFERENCE, rc.ASSIGNED_TO, rc.OPENED_DATE,
               c.FIRST_NAME || \\'\\' \\'\\' || c.LAST_NAME AS CUSTOMER_NAME,
               c.RISK_RATING, c.COUNTRY_CODE
        FROM AML_COPILOT.RAW.RISK_CASES rc
        LEFT JOIN AML_COPILOT.RAW.CUSTOMERS c ON rc.CUSTOMER_ID = c.CUSTOMER_ID
        WHERE rc.CASE_ID = \\'{P_CASE_ID}\\'
    """).collect()

    if not case_df:
        return f"Error: Case {P_CASE_ID} not found"

    case = case_df[0]

    signals = session.sql(f"""
        SELECT SIGNAL_TYPE, SIGNAL_SCORE, STATUS, DETECTION_TIMESTAMP, TRIGGER_DETAIL
        FROM AML_COPILOT.RAW.AML_SIGNALS
        WHERE CUSTOMER_ID = \\'{case["CUSTOMER_ID"]}\\'
        ORDER BY SIGNAL_SCORE DESC LIMIT 10
    """).collect()

    txns = session.sql(f"""
        SELECT TRANSACTION_TIMESTAMP, AMOUNT_USD, TRANSACTION_TYPE, DIRECTION,
               ORIGIN_COUNTRY, DESTINATION_COUNTRY, TRANSACTION_ID
        FROM AML_COPILOT.RAW.TRANSACTIONS
        WHERE CUSTOMER_ID = \\'{case["CUSTOMER_ID"]}\\'
        ORDER BY TRANSACTION_TIMESTAMP DESC LIMIT 20
    """).collect()

    evidence = session.sql(f"""
        SELECT EVIDENCE_TYPE, REFERENCE_ID, DESCRIPTION
        FROM AML_COPILOT.RAW.CASE_EVIDENCE
        WHERE CASE_ID = \\'{P_CASE_ID}\\'
    """).collect()

    now = datetime.utcnow()
    gen_time = now.strftime("%Y-%m-%d %H:%M") + " UTC"
    ts_file = now.strftime("%Y%m%d_%H%M%S")

    pdf = AMLReport(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()
    pw = pdf.w - pdf.l_margin - pdf.r_margin

    # Header: black-to-navy gradient
    hx, hy, hh = pdf.l_margin, pdf.get_y(), 26
    pdf._gradient_rect(hx, hy, pw, hh, 0, 0, 0, 30, 58, 95)
    pdf.set_fill_color(181, 93, 12)
    pdf.rect(hx, hy + hh, pw, 1.2, "F")
    pdf.set_xy(hx + 5, hy + 3)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(pw, 10, "AML Investigation Report")
    pdf.set_xy(hx + 5, hy + 14)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(180, 195, 210)
    pdf.cell(pw, 6, f"Case {P_CASE_ID}  |  Generated {gen_time}")
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(hy + hh + 5)

    # Case Summary
    pdf._section_bar("CASE SUMMARY")
    fields = [
        ("Case ID:", safe_str(case["CASE_ID"])),
        ("Customer:", safe_str(case["CUSTOMER_NAME"])),
        ("Customer ID:", safe_str(case["CUSTOMER_ID"])),
        ("Case Type:", safe_str(case["CASE_TYPE"])),
        ("Priority:", safe_str(case["PRIORITY"])),
        ("Status:", safe_str(case["STATUS"])),
        ("Assigned To:", safe_str(case["ASSIGNED_TO"])),
        ("Opened:", safe_str(case["OPENED_DATE"])),
    ]
    box_top = pdf.get_y()
    finding = safe_str(case["FINDING_SUMMARY"])
    field_h = len(fields) * 5.5 + 4
    if finding:
        field_h += (len(finding) // 90 + 3) * 4.5 + 12
    pdf.set_fill_color(252, 248, 244)
    pdf.rect(pdf.l_margin + 1.8, box_top, pw - 1.8, field_h, "F")
    pdf.set_fill_color(184, 101, 27)
    pdf.rect(pdf.l_margin, box_top, 1.8, field_h, "F")
    pdf.set_y(box_top + 2)
    for lbl, val in fields:
        pdf.set_x(pdf.l_margin + 5)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(35, 5.5, lbl)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5.5, val, ln=True)
    if finding:
        pdf.ln(2)
        pdf.set_x(pdf.l_margin + 5)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5.5, "Finding Summary:", ln=True)
        pdf.set_x(pdf.l_margin + 5)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(pw - 10, 4.5, finding)
    pdf.set_y(box_top + field_h + 4)

    # Signals
    pdf._section_bar(f"AML SIGNALS ({len(signals)})")
    if signals:
        sw = [30, 14, 24, 24, pw - 92]
        pdf._table_header(sw, ["Type", "Score", "Status", "Date", "Description"])
        for idx, s in enumerate(signals):
            pdf._table_row(sw, [
                safe_str(s["SIGNAL_TYPE"]),
                str(int(float(safe_str(s["SIGNAL_SCORE"])))),
                safe_str(s["STATUS"]),
                safe_str(s["DETECTION_TIMESTAMP"])[:10],
                safe_str(s["TRIGGER_DETAIL"])[:80]
            ], fill=(idx % 2 == 1))
    pdf.ln(6)

    # Transactions
    pdf._section_bar(f"KEY TRANSACTIONS ({len(txns)})")
    if txns:
        tw = [22, 22, 18, 22, 16, 16, pw - 116]
        pdf._table_header(tw, ["Date", "Amount", "Type", "Dir", "Origin", "Dest", "TXN ID"])
        for idx, t in enumerate(txns):
            amt = float(t["AMOUNT_USD"]) if t["AMOUNT_USD"] else 0
            pdf._table_row(tw, [
                safe_str(t["TRANSACTION_TIMESTAMP"])[:10],
                f"${amt:,.2f}",
                safe_str(t["TRANSACTION_TYPE"]),
                safe_str(t["DIRECTION"]),
                safe_str(t["ORIGIN_COUNTRY"]),
                safe_str(t["DESTINATION_COUNTRY"]),
                safe_str(t["TRANSACTION_ID"])
            ], fill=(idx % 2 == 1))
    pdf.ln(6)

    # Evidence
    if evidence:
        pdf._section_bar(f"CASE EVIDENCE ({len(evidence)})")
        for e in evidence:
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 6, f\\'{safe_str(e["EVIDENCE_TYPE"])}  |  {safe_str(e["REFERENCE_ID"])}\\', ln=True)
            desc = safe_str(e["DESCRIPTION"])
            if desc:
                pdf.set_font("Helvetica", "", 8)
                pdf.multi_cell(0, 4.5, desc)
            pdf.ln(1.5)

    # Output
    pdf_bytes = pdf.output()
    hex_str = pdf_bytes.hex()
    filename = f"AML_Report_{P_CASE_ID}_{ts_file}.pdf"
    report_id = str(uuid.uuid4())[:20]
    session.sql(f"""
        INSERT INTO AML_COPILOT.PIPELINE.GENERATED_REPORTS
        (REPORT_ID, CASE_ID, FILENAME, PDF_DATA, GENERATED_BY, GENERATED_AT)
        SELECT \\'{report_id}\\', \\'{P_CASE_ID}\\', \\'{filename}\\',
               TO_BINARY(\\'{hex_str}\\', \\'HEX\\'), CURRENT_USER(), CURRENT_TIMESTAMP()
    """).collect()
    return f"Report generated successfully: {filename}"
';


-- ============================================================
-- SP_RUN_DATA_QUALITY_CHECKS: Automated quality monitoring
-- Language: JavaScript | Schedule: Every 15 minutes
-- ============================================================

CREATE OR REPLACE PROCEDURE SP_RUN_DATA_QUALITY_CHECKS()
RETURNS VARCHAR
LANGUAGE JAVASCRIPT
EXECUTE AS CALLER
AS '
    var run_id = "DQ_" + new Date().toISOString().replace(/[-:T.]/g, "").slice(0, 14);
    var checks = snowflake.execute({sqlText: "SELECT CHECK_ID, CHECK_NAME, TABLE_NAME, CHECK_SQL, SEVERITY FROM AML_COPILOT.PIPELINE.DATA_QUALITY_CHECKS WHERE IS_ACTIVE = TRUE"});
    var total_checks = 0;
    var total_failures = 0;

    while (checks.next()) {
        total_checks++;
        var check_id = checks.getColumnValue("CHECK_ID");
        var check_name = checks.getColumnValue("CHECK_NAME");
        var table_name = checks.getColumnValue("TABLE_NAME");
        var check_sql = checks.getColumnValue("CHECK_SQL");

        try {
            var result = snowflake.execute({sqlText: check_sql});
            result.next();
            var records_checked = result.getColumnValue(1);
            var records_failed = result.getColumnValue(2);
            var pass_rate = records_checked > 0 ? ((records_checked - records_failed) / records_checked * 100) : 100;
            var status = records_failed > 0 ? "FAIL" : "PASS";
            if (records_failed > 0) total_failures++;

            snowflake.execute({sqlText: "INSERT INTO AML_COPILOT.PIPELINE.DATA_QUALITY_RESULTS (RUN_ID, RUN_TIMESTAMP, CHECK_ID, CHECK_NAME, TABLE_NAME, RECORDS_CHECKED, RECORDS_FAILED, PASS_RATE, STATUS) VALUES (\'" + run_id + "\', CURRENT_TIMESTAMP(), \'" + check_id + "\', \'" + check_name + "\', \'" + table_name + "\', " + records_checked + ", " + records_failed + ", " + pass_rate.toFixed(4) + ", \'" + status + "\')"});
        } catch (err) {
            snowflake.execute({sqlText: "INSERT INTO AML_COPILOT.PIPELINE.DATA_QUALITY_RESULTS (RUN_ID, RUN_TIMESTAMP, CHECK_ID, CHECK_NAME, TABLE_NAME, RECORDS_CHECKED, RECORDS_FAILED, PASS_RATE, STATUS) VALUES (\'" + run_id + "\', CURRENT_TIMESTAMP(), \'" + check_id + "\', \'" + check_name + "\', \'" + table_name + "\', 0, 0, 0, \'ERROR\')"});
        }
    }

    snowflake.execute({sqlText: "INSERT INTO AML_COPILOT.PIPELINE.PIPELINE_AUDIT_LOG (EVENT_TYPE, EVENT_SOURCE, ENTITY_TYPE, ENTITY_ID, DETAIL, USER_ID) VALUES (\'DQ_CHECK_RUN\', \'SP_RUN_DATA_QUALITY_CHECKS\', \'PIPELINE\', \'" + run_id + "\', \'Ran " + total_checks + " checks, " + total_failures + " failures\', CURRENT_USER())"});

    return "DQ run " + run_id + ": " + total_checks + " checks, " + total_failures + " failures";
';


-- ============================================================
-- SP_APPROVE_POLICY_DOCUMENT: Governed document ingestion
-- Language: JavaScript | Approves/rejects staged documents
-- Chunks approved docs for Cortex Search indexing
-- ============================================================

CREATE OR REPLACE PROCEDURE SP_APPROVE_POLICY_DOCUMENT(DOC_ID VARCHAR, ACTION VARCHAR, REVIEWER VARCHAR, NOTES VARCHAR)
RETURNS VARCHAR
LANGUAGE JAVASCRIPT
EXECUTE AS CALLER
AS '
    var action = ACTION.toUpperCase();
    if (action !== "APPROVE" && action !== "REJECT") return "Invalid action: " + action;

    var doc = snowflake.execute({sqlText: "SELECT DOC_ID, TITLE, CATEGORY, JURISDICTION, FULL_TEXT FROM AML_COPILOT.PIPELINE.POLICY_DOCUMENTS_STAGED WHERE DOC_ID = \'" + DOC_ID.replace(/\'/g, "\'\'") + "\' AND STATUS = \'PENDING_APPROVAL\'"});
    if (!doc.next()) return "Document not found or not pending: " + DOC_ID;

    var title = doc.getColumnValue("TITLE");
    var category = doc.getColumnValue("CATEGORY");
    var jurisdiction = doc.getColumnValue("JURISDICTION");
    var full_text = doc.getColumnValue("FULL_TEXT");

    if (action === "REJECT") {
        snowflake.execute({sqlText: "UPDATE AML_COPILOT.PIPELINE.POLICY_DOCUMENTS_STAGED SET STATUS=\'REJECTED\', REVIEWED_BY=\'" + REVIEWER.replace(/\'/g,"\'\'") + "\', REVIEWED_AT=CURRENT_TIMESTAMP() WHERE DOC_ID=\'" + DOC_ID.replace(/\'/g,"\'\'") + "\'"});
        snowflake.execute({sqlText: "INSERT INTO AML_COPILOT.PIPELINE.PIPELINE_AUDIT_LOG (EVENT_TYPE,EVENT_SOURCE,ENTITY_TYPE,ENTITY_ID,DETAIL,USER_ID) VALUES(\'DOCUMENT_REJECTED\',\'SP_APPROVE_POLICY_DOCUMENT\',\'DOCUMENT\',\'" + DOC_ID + "\',\'Rejected: " + title.replace(/\'/g,"\'\'") + "\',\'" + REVIEWER + "\')"});
        return "Rejected: " + title;
    }

    // APPROVE: chunk the text for Cortex Search
    var chunk_size = 1500;
    var overlap = 200;
    var text = full_text || "";
    var chunks = 0;
    var pol_id = "POL_" + String(Math.floor(Math.random() * 9000) + 1000);

    for (var i = 0; i < text.length; i += (chunk_size - overlap)) {
        var chunk = text.substring(i, i + chunk_size);
        if (chunk.trim().length < 50) continue;
        snowflake.execute({sqlText: "INSERT INTO AML_COPILOT.ANALYTICS.POLICY_DOCUMENT_CHUNKS (CHUNK_ID,DOC_ID,TITLE,CATEGORY,JURISDICTION,CHUNK_TEXT,CHUNK_INDEX,STATUS) VALUES(\'" + pol_id + "_C" + chunks + "\',\'" + DOC_ID + "\',\'" + title.replace(/\'/g,"\'\'") + "\',\'" + (category||"").replace(/\'/g,"\'\'") + "\',\'" + (jurisdiction||"").replace(/\'/g,"\'\'") + "\',\'" + chunk.replace(/\'/g,"\'\'") + "\'," + chunks + ",\'ACTIVE\')"});
        chunks++;
    }

    snowflake.execute({sqlText: "UPDATE AML_COPILOT.PIPELINE.POLICY_DOCUMENTS_STAGED SET STATUS=\'APPROVED\', REVIEWED_BY=\'" + REVIEWER.replace(/\'/g,"\'\'") + "\', REVIEWED_AT=CURRENT_TIMESTAMP() WHERE DOC_ID=\'" + DOC_ID.replace(/\'/g,"\'\'") + "\'"});
    snowflake.execute({sqlText: "INSERT INTO AML_COPILOT.PIPELINE.PIPELINE_AUDIT_LOG (EVENT_TYPE,EVENT_SOURCE,ENTITY_TYPE,ENTITY_ID,DETAIL,USER_ID) VALUES(\'DOCUMENT_APPROVED\',\'SP_APPROVE_POLICY_DOCUMENT\',\'DOCUMENT\',\'" + DOC_ID + "\',\'Approved: " + title.replace(/\'/g,"\'\'") + " (" + chunks + " chunks)\',\'" + REVIEWER + "\')"});

    return "Approved: " + title + " (" + chunks + " chunks indexed)";
';
