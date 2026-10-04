import streamlit as st
import json
import uuid
import math
from datetime import datetime, timedelta
from snowflake.snowpark.context import get_active_session
import _snowflake
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# CONFIGURATION
# ============================================================
AGENT_DATABASE = "AML_COPILOT"
AGENT_SCHEMA = "RAW"
AGENT_NAME = "AML_RISK_COPILOT"
HISTORY_TABLE = "AML_COPILOT.RAW.CONVERSATION_HISTORY"

RISK_RULES = [
    ("RULE_STRUCT_001", "Structuring", "3+ cash txns <$10K summing >$10K within 24h", "#B55D0C"),
    ("RULE_RAPID_001", "Rapid Movement", "Inbound wire >$50K, outbound >80% within 48h", "#1E3A5F"),
    ("RULE_VELOC_001", "Velocity Spike", "Txn count >3x the 30-day daily average", "#E8913A"),
    ("RULE_GEO_001", "Unusual Geography", "Txn to HIGH risk country, no prior history", "#2C3E50"),
    ("RULE_DORM_001", "Dormant Activation", "Txn after 90+ days of inactivity", "#B85A0D"),
    ("RULE_BENEF_001", "Beneficiary Burst", ">5 new beneficiaries within 7 days", "#34495E"),
]

SUGGESTED_QUESTIONS = [
    ("Which customers have the most AML signals and what policies apply?", "risk", "Signal Detection"),
    ("Investigate structuring signals — show transactions and BSA reporting rules", "alert", "Investigation"),
    ("What are the SAR filing requirements and do any current cases meet the threshold?", "policy", "Policy + Data"),
    ("Show the top 5 highest-risk customers with their risk scores and applicable EDD policy", "risk", "Risk Assessment"),
    ("What does the CTR policy say about cash reporting and how many transactions exceed it?", "policy", "Compliance"),
    ("Generate an audit-ready finding for the customer with the highest signal score", "case", "Finding"),
    ("Which customers have wire transfers to high-risk countries and what sanctions policy applies?", "risk", "Investigation"),
    ("Show all escalated signals with trigger details and the regulation that makes them reportable", "alert", "Evidence"),
]

RULE_COLORS = {
    "RULE_STRUCT_001": "#B55D0C", "RULE_RAPID_001": "#1E3A5F", "RULE_VELOC_001": "#E8913A",
    "RULE_GEO_001": "#2C3E50", "RULE_DORM_001": "#B85A0D", "RULE_BENEF_001": "#34495E",
}
RULE_NAMES = {
    "RULE_STRUCT_001": "Structuring", "RULE_RAPID_001": "Rapid Movement",
    "RULE_VELOC_001": "Velocity Spike", "RULE_GEO_001": "Unusual Geography",
    "RULE_DORM_001": "Dormant Activation", "RULE_BENEF_001": "Beneficiary Burst",
}
ICON_MAP = {"risk": "&#9888;", "chart": "&#128200;", "case": "&#128194;", "ops": "&#9881;", "policy": "&#128220;", "alert": "&#128276;"}

session = get_active_session()
_rerun = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)

# ============================================================
# CSS THEME — Premium Dark Banking
# ============================================================
st.set_page_config(page_title="RiskLens AI — AML Copilot", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    .main { background-color: #F8FAFC; font-size: 0.9rem; }
    .main > .block-container { padding-top: 0.5rem; max-width: 100%; }

    /* Header */
    .header-bar {
        background: linear-gradient(135deg, #000000 0%, #0a0a1a 30%, #111827 60%, #1E3A5F 100%);
        padding: 0.7rem 1.5rem; border-radius: 12px; margin-bottom: 0.6rem;
        box-shadow: 0 4px 24px rgba(0,0,0,0.45);
        display: flex; align-items: center; gap: 1rem;
    }
    .header-bar .logo-circle {
        width: 44px; height: 44px; border-radius: 50%;
        background: linear-gradient(135deg, #B55D0C, #E8913A);
        display: flex; align-items: center; justify-content: center;
        font-size: 1.3rem; color: #fff; flex-shrink: 0;
        box-shadow: 0 2px 14px rgba(208,108,16,0.5);
    }
    .header-bar .header-text h1 { color:#fff; font-size:1.25rem; margin:0; letter-spacing:-0.3px; }
    .header-bar .header-text p { color:#94A3B8; margin:0.05rem 0 0 0; font-size:0.72rem; }
    .header-bar .header-status { margin-left:auto; display:flex; gap:0.6rem; align-items:center; }
    .header-bar .header-status .hs { padding:3px 10px; border-radius:20px; font-size:0.65rem; font-weight:600; }
    .hs-live { background:rgba(16,185,129,0.15); color:#10B981; border:1px solid rgba(16,185,129,0.3); }
    .hs-user { background:rgba(255,255,255,0.08); color:#CBD5E1; border:1px solid rgba(255,255,255,0.12); }

    /* Sidebar */
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #000000 0%, #0a0a1a 40%, #111827 100%) !important; }
    section[data-testid="stSidebar"] * { color: #e0e8f0 !important; }
    section[data-testid="stSidebar"] .stMarkdown p, section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] .stMarkdown h4 { color: #fff !important; }
    section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.1) !important; }
    section[data-testid="stSidebar"] button {
        background: rgba(255,255,255,0.06) !important; border: 1px solid rgba(255,255,255,0.1) !important;
        color: #e0e8f0 !important; border-radius: 8px !important; font-size: 0.72rem !important; transition: all 0.2s !important;
    }
    section[data-testid="stSidebar"] button:hover { background: rgba(208,108,16,0.2) !important; border-color: rgba(208,108,16,0.35) !important; }
    .sb-section-title { font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: #B55D0C !important; margin: 0.5rem 0 0.3rem; }
    .sb-user-badge { background: rgba(208,108,16,0.1); border: 1px solid rgba(208,108,16,0.25); border-radius: 10px; padding: 0.4rem 0.6rem; text-align: center; font-size: 0.72rem; color: #B55D0C !important; }
    .sb-user-badge strong { color: #fff !important; }
    .rule-tooltip-wrap { position: relative; display: inline-block; margin: 2px 0; cursor: pointer; }
    .rule-tooltip-wrap .rule-tt { visibility: hidden; opacity: 0; position: absolute; left: 105%; top: 50%; transform: translateY(-50%); background: #0a0a1a; color: #e0e8f0; padding: 6px 10px; border-radius: 8px; font-size: 0.65rem; white-space: nowrap; z-index: 999; box-shadow: 0 2px 12px rgba(0,0,0,0.5); border: 1px solid rgba(208,108,16,0.3); pointer-events: none; transition: opacity 0.2s; }
    .rule-tooltip-wrap:hover .rule-tt { visibility: visible; opacity: 1; }

    /* KPI Cards */
    .kpi-card { background:#fff; border:1px solid #E2E8F0; border-radius:12px; padding:0.7rem 0.5rem; text-align:center; box-shadow:0 1px 3px rgba(15,23,42,0.06); }
    .kpi-card-red { background:#FEF2F2; border-color:#FECACA; }
    .kpi-card-rose { background:#FFF1F2; border-color:#FECDD3; }
    .kpi-card-amber { background:#FFFBEB; border-color:#FDE68A; }
    .kpi-card-green { background:#F0FDF4; border-color:#BBF7D0; }
    .kpi-card-blue { background:#EFF6FF; border-color:#BFDBFE; }
    .kpi-card-teal { background:#F0FDFA; border-color:#99F6E4; }
    .kpi-card-purple { background:#FAF5FF; border-color:#E9D5FF; }
    .kpi-val { font-size:1.5rem; font-weight:700; margin:0; line-height:1.2; }
    .kpi-val-red { color:#DC2626; } .kpi-val-rose { color:#BE123C; } .kpi-val-green { color:#16A34A; }
    .kpi-val-amber { color:#D97706; } .kpi-val-blue { color:#2563EB; } .kpi-val-teal { color:#0D9488; }
    .kpi-val-purple { color:#7C3AED; }
    .kpi-lbl { font-size:0.62rem; color:#64748B; margin:0.2rem 0 0; text-transform:uppercase; letter-spacing:0.6px; font-weight:500; }
    .kpi-delta { font-size:0.65rem; margin:0.1rem 0 0; }

    /* Cards */
    .card { background:#fff; border:1px solid #E2E8F0; border-radius:12px; padding:1rem; margin-bottom:0.7rem; box-shadow:0 1px 3px rgba(15,23,42,0.06); }
    .card-header { font-size:0.78rem; font-weight:700; color:#0F172A; margin-bottom:0.5rem; text-transform:uppercase; letter-spacing:0.5px; }
    .card-sub { font-size:0.68rem; font-weight:400; color:#94A3B8; text-transform:none; letter-spacing:0; }

    /* Badges */
    .status-badge { display:inline-block; padding:2px 8px; border-radius:10px; font-size:0.68rem; font-weight:600; }
    .badge-new { background:#FEF2F2; color:#DC2626; } .badge-review { background:#FFFBEB; color:#D97706; }
    .badge-escalated { background:#FFF1F2; color:#BE123C; } .badge-dismissed { background:#F0FDF4; color:#16A34A; }
    .badge-open { background:#DBEAFE; color:#1D4ED8; } .badge-closed { background:#DCFCE7; color:#16A34A; }
    .badge-filed { background:#EDE9FE; color:#7C3AED; }
    .risk-high { color:#DC2626; font-weight:700; } .risk-medium { color:#F59E0B; font-weight:700; } .risk-low { color:#16A34A; font-weight:700; }
    .rule-chip { display:inline-block; padding:2px 10px; border-radius:12px; font-size:0.7rem; font-weight:600; margin:2px; color:#fff; }

    /* Tabs */
    div[data-testid="stTabs"] button { font-size:0.85rem; font-weight:600; color:#475569; background:transparent !important; border:none !important; border-bottom:2px solid transparent !important; padding:0.5rem 0.7rem !important; }
    div[data-testid="stTabs"] button:hover { color:#B55D0C !important; border-bottom:2px solid #B55D0C !important; background:transparent !important; }
    div[data-testid="stTabs"] button:focus, div[data-testid="stTabs"] button:active { outline:none !important; box-shadow:none !important; background:transparent !important; }
    div[data-testid="stTabs"] button[aria-selected="true"] { color:#B55D0C !important; border-bottom:2px solid #B55D0C !important; background:transparent !important; font-weight:700 !important; }
    div[data-testid="stTabs"] > div[role="tablist"] { border-bottom:1px solid #E2E8F0; }

    /* Metrics */
    div[data-testid="stMetric"] { background:#fff; border:1px solid #E2E8F0; border-radius:12px; padding:0.6rem 0.4rem; text-align:center; box-shadow:0 1px 3px rgba(15,23,42,0.06); }
    div[data-testid="stMetric"] label { font-size:0.65rem; font-weight:500; text-transform:uppercase; letter-spacing:0.5px; color:#64748B; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { font-size:1.2rem; font-weight:700; color:#0F172A; }

    /* DataFrames */
    div[data-testid="stDataFrame"] { border:1px solid #E2E8F0; border-radius:12px; overflow:hidden; box-shadow:0 1px 3px rgba(15,23,42,0.06); }
    div[data-testid="stDataFrame"] table th, div[data-testid="stDataFrame"] [role="columnheader"] {
        font-weight:800 !important; color:#0F172A !important; text-transform:uppercase; letter-spacing:0.3px; background:#F1F5F9 !important; font-size:0.78rem !important;
    }

    /* Buttons */
    .stButton > button { border:1px solid #B55D0C !important; color:#B55D0C !important; border-radius:8px !important; font-weight:600 !important; font-size:0.8rem !important; }
    .stButton > button:hover { background:rgba(181,93,12,0.08) !important; }
    .stDownloadButton > button { background:linear-gradient(135deg,#B55D0C,#E8913A) !important; color:#fff !important; border:none !important; border-radius:8px !important; font-weight:600 !important; }

    /* Risk feed */
    .risk-feed-item { background:#fff; border:1px solid #E2E8F0; border-left:4px solid #DC2626; border-radius:8px; padding:0.6rem 0.8rem; margin-bottom:0.5rem; }
    .risk-feed-item.medium { border-left-color:#F59E0B; }
    .risk-feed-item.low { border-left-color:#16A34A; }
    .risk-feed-title { font-size:0.78rem; font-weight:700; color:#0F172A; margin:0; }
    .risk-feed-detail { font-size:0.7rem; color:#475569; margin:0.2rem 0 0; line-height:1.5; }
    .risk-feed-score { font-size:0.82rem; font-weight:800; }

    /* Workflow */
    .wf-step { display:inline-block; padding:0.4rem 0.8rem; border-radius:8px; font-size:0.72rem; font-weight:600; margin:0 0.15rem; }
    .wf-active { background:#DCFCE7; color:#16A34A; border:1px solid #BBF7D0; }
    .wf-done { background:#F0FDF4; color:#16A34A; border:1px solid #BBF7D0; }
    .wf-pending { background:#F1F5F9; color:#94A3B8; border:1px solid #E2E8F0; }
    .wf-arrow { color:#94A3B8; font-size:0.9rem; margin:0 0.1rem; }

    /* CoCo ops checklist */
    .coco-check { display:flex; align-items:center; gap:0.5rem; padding:0.35rem 0; border-bottom:1px solid #F1F5F9; font-size:0.78rem; }
    .coco-check .check-icon { width:22px; height:22px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.72rem; flex-shrink:0; }
    .check-pass { background:#DCFCE7; color:#16A34A; }
    .check-fail { background:#FEF2F2; color:#DC2626; }

    /* Suggest chips */
    .sq-chip { display:inline-block; padding:0.35rem 0.7rem; border:1px solid #E2E8F0; border-radius:20px; font-size:0.72rem; color:#475569; margin:0.2rem; background:#fff; cursor:default; }

    /* Evidence panel */
    .evidence-panel { background:#FFFBF5; border:1px solid #FDE68A; border-radius:10px; padding:0.7rem 1rem; margin-top:0.5rem; }
    .evidence-panel-title { font-size:0.72rem; font-weight:700; color:#92400E; text-transform:uppercase; letter-spacing:0.5px; margin:0 0 0.4rem; display:flex; align-items:center; gap:0.4rem; }
    .citation-card { background:#fff; border:1px solid #E2E8F0; border-left:3px solid #B55D0C; border-radius:6px; padding:0.5rem 0.7rem; margin:0.3rem 0; font-size:0.78rem; }
    .citation-title { font-weight:700; color:#0F172A; font-size:0.78rem; }
    .citation-meta { font-size:0.65rem; color:#64748B; margin:0.1rem 0; }
    .citation-text { font-size:0.75rem; color:#334155; line-height:1.55; margin-top:0.2rem; }
    .sources-used { display:flex; gap:0.4rem; flex-wrap:wrap; margin-top:0.3rem; }
    .source-tag { padding:2px 8px; border-radius:12px; font-size:0.62rem; font-weight:600; }
    .source-data { background:#DBEAFE; color:#1D4ED8; }
    .source-policy { background:#FEF3C7; color:#92400E; }

    .footer { text-align:center; color:#94A3B8; font-size:0.65rem; padding:0.5rem 0 0.2rem; border-top:1px solid #E2E8F0; margin-top:0.8rem; }
</style>""", unsafe_allow_html=True)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def safe_md(text):
    return text.replace("$", "\\$") if text else ""

def status_badge(status):
    s = (status or "").upper()
    cls = {"NEW":"badge-new","UNDER_REVIEW":"badge-review","ESCALATED":"badge-escalated",
           "DISMISSED":"badge-dismissed","OPEN":"badge-open","CLOSED":"badge-closed","FILED":"badge-filed"}.get(s, "badge-open")
    return f"<span class='status-badge {cls}'>{s}</span>"

def risk_class(score):
    if score is None: return "risk-low"
    return "risk-high" if score >= 70 else "risk-medium" if score >= 40 else "risk-low"

def plotly_theme(fig, height=350):
    fig.update_layout(
        template="plotly_white", height=height, margin=dict(l=20, r=20, t=30, b=20),
        font=dict(size=11, family="Inter, sans-serif", color="#334155"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

def kpi_html(label, value, color_cls="blue", card_cls="", delta_html=""):
    return (f"<div class='kpi-card {card_cls}'>"
            f"<p class='kpi-val kpi-val-{color_cls}'>{value}</p>{delta_html}"
            f"<p class='kpi-lbl'>{label}</p></div>")


# ============================================================
# AGENT API
# ============================================================
def call_agent(question, thread_id=None, parent_message_id=None):
    url = f"/api/v2/databases/{AGENT_DATABASE}/schemas/{AGENT_SCHEMA}/agents/{AGENT_NAME}:run"
    body = {"stream": False}
    if thread_id is not None and parent_message_id is not None:
        body["thread_id"] = thread_id
        body["parent_message_id"] = parent_message_id
        body["messages"] = [{"role": "user", "content": [{"type": "text", "text": question}]}]
    else:
        history = st.session_state.get("messages", [])
        msgs = [{"role": m["role"], "content": [{"type": "text", "text": m["content"]}]} for m in history[-10:]]
        msgs.append({"role": "user", "content": [{"type": "text", "text": question}]})
        body["messages"] = msgs

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    resp = _snowflake.send_snow_api_request("POST", url, headers, {}, body, {}, 600000)
    raw = resp.get("content", resp.get("body", "{}"))
    rc = json.loads(raw) if isinstance(raw, str) else (raw if isinstance(raw, dict) else {})
    if "message" in rc and isinstance(rc["message"], dict):
        rc = rc["message"]
    if "code" in rc and "message" in rc and isinstance(rc["message"], str):
        return {"text": f"Agent error: {rc['message']}", "citations": [], "tables": [], "charts": [], "suggested": [], "metadata": {}, "debug": json.dumps(rc, indent=2, default=str)[:3000]}

    text_parts, citations, tables, charts, suggested = [], [], [], [], []
    for item in (rc.get("content", []) if isinstance(rc.get("content"), list) else []):
        if not isinstance(item, dict): continue
        t = item.get("type", "")
        if t == "text":
            text_parts.append(item.get("text", ""))
            for ann in item.get("annotations", []):
                if ann.get("type") == "cortex_search_citation": citations.append(ann)
        elif t == "tool_result":
            inner = item.get("tool_result", item)
            for tc in (inner.get("content", []) if isinstance(inner.get("content"), list) else []):
                if isinstance(tc, dict) and tc.get("type") == "json":
                    rs = tc.get("json", {}).get("result_set")
                    if rs: tables.append(rs)
        elif t == "table":
            rs = item.get("table", {}).get("result_set")
            if rs: tables.append(rs)
        elif t == "chart":
            cs = item.get("chart", {}).get("chart_spec")
            if cs: charts.append(cs)
        elif t == "suggested_queries":
            for sq in item.get("suggested_queries", []):
                if isinstance(sq, dict) and sq.get("query"): suggested.append(sq["query"])

    return {"text": "\n\n".join(text_parts), "citations": citations, "tables": tables, "charts": charts,
            "suggested": suggested, "metadata": rc.get("metadata", {}), "debug": json.dumps(rc, indent=2, default=str)[:3000]}

def render_agent_tables(tables):
    for rs in tables:
        meta = rs.get("resultSetMetaData", {})
        data = rs.get("data", [])
        row_types = meta.get("rowType", [])
        cols = [r["name"] for r in row_types]
        if not data or not cols: continue
        df = pd.DataFrame(data, columns=cols)
        for rt in row_types:
            cn = rt["name"]
            if rt.get("type", "").upper() in ("NUMBER", "FIXED", "FLOAT", "REAL", "DOUBLE"):
                df[cn] = pd.to_numeric(df[cn], errors="coerce")
        st.dataframe(df, use_container_width=True)

def render_citations(citations):
    if not citations: return
    seen, unique = set(), []
    for c in citations:
        txt = c.get("text", "")
        if txt and txt[:100] not in seen:
            seen.add(txt[:100]); unique.append(c)
    if not unique: return

    # Prominent evidence panel — always expanded
    st.markdown("<div class='evidence-panel'><p class='evidence-panel-title'>&#128220; Policy Citations &amp; Evidence Sources</p>", unsafe_allow_html=True)
    st.markdown("<div class='sources-used'><span class='source-tag source-data'>Transaction Data</span><span class='source-tag source-data'>AML Signals</span><span class='source-tag source-policy'>AML Policies</span><span class='source-tag source-policy'>Regulatory Guidance</span></div>", unsafe_allow_html=True)

    for i, c in enumerate(unique):
        title = c.get("doc_title", "")
        text = c.get("text", "")
        if not title and text:
            for line in text.strip().split("\\n"):
                line = line.strip()
                if line.startswith("POLICY:"): title = line.replace("POLICY:", "").strip(); break
                elif 5 < len(line) < 200: title = line; break
        if not title: title = f"Policy Document {i+1}"
        display_text = text[:400].strip() + ("..." if len(text) > 400 else "")
        st.markdown(f"""<div class='citation-card'>
            <div class='citation-title'>{safe_md(title)}</div>
            <div class='citation-meta'>Source {i+1} of {len(unique)}</div>
            <div class='citation-text'>{safe_md(display_text)}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_evidence_sources(response):
    """Show data sources and policy sources used, even when there are no explicit citations."""
    has_tables = bool(response.get("tables"))
    has_citations = bool(response.get("citations"))
    if not has_tables and not has_citations:
        return
    tags = []
    if has_tables:
        tags.append("<span class='source-tag source-data'>Transaction Data</span>")
        tags.append("<span class='source-tag source-data'>Customer Risk Profiles</span>")
        tags.append("<span class='source-tag source-data'>AML Signal Pipeline</span>")
    if has_citations:
        tags.append("<span class='source-tag source-policy'>AML Policy Documents</span>")
        tags.append("<span class='source-tag source-policy'>Regulatory Guidance</span>")
    if tags and not has_citations:
        st.markdown(f"<div style='margin-top:0.4rem;'><span style='font-size:0.68rem;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:0.5px;'>Sources consulted: </span>{''.join(tags)}</div>", unsafe_allow_html=True)


# ============================================================
# PERSISTENCE
# ============================================================
def _esc(s):
    return s.replace("'", "''") if s else ""

def save_message(conv_id, user_id, title, role, content, order, thread_id=None, parent_msg_id=None):
    tid = f"'{thread_id}'" if thread_id else "NULL"
    pid = f"'{parent_msg_id}'" if parent_msg_id else "NULL"
    session.sql(f"""INSERT INTO {HISTORY_TABLE}
        (CONVERSATION_ID,USER_ID,TITLE,MESSAGE_ROLE,MESSAGE_CONTENT,MESSAGE_ORDER,
         AGENT_THREAD_ID,AGENT_PARENT_MESSAGE_ID,UPDATED_TIMESTAMP)
        VALUES('{conv_id}','{_esc(user_id)}','{_esc(title)}','{role}',
               '{_esc(content)}',{order},{tid},{pid},CURRENT_TIMESTAMP())""").collect()

@st.cache_data(ttl=30)
def load_conversations(user_id):
    return session.sql(f"""SELECT CONVERSATION_ID, MAX(TITLE) AS TITLE,
        MAX(UPDATED_TIMESTAMP) AS LAST_ACTIVITY,
        MIN(CASE WHEN MESSAGE_ROLE='user' AND MESSAGE_ORDER=1 THEN MESSAGE_CONTENT END) AS FIRST_Q,
        COUNT(*) AS MC FROM {HISTORY_TABLE} WHERE USER_ID='{_esc(user_id)}'
        GROUP BY CONVERSATION_ID ORDER BY MAX(UPDATED_TIMESTAMP) DESC LIMIT 30""").collect()

def load_conversation_messages(conv_id):
    return session.sql(f"""SELECT MESSAGE_ROLE,MESSAGE_CONTENT,AGENT_THREAD_ID,AGENT_PARENT_MESSAGE_ID
        FROM {HISTORY_TABLE} WHERE CONVERSATION_ID='{conv_id}' ORDER BY MESSAGE_ORDER""").collect()

def delete_conversation(conv_id):
    session.sql(f"DELETE FROM {HISTORY_TABLE} WHERE CONVERSATION_ID='{_esc(conv_id)}'").collect()
    if st.session_state.conversation_id == conv_id:
        st.session_state.conversation_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.thread_id = None
        st.session_state.parent_message_id = None
        st.session_state.conversation_title = None
        st.session_state.pending_question = None

def restore_conversation(conv_id):
    rows = load_conversation_messages(conv_id)
    st.session_state.conversation_id = conv_id
    st.session_state.messages = []
    st.session_state.thread_id = None
    st.session_state.parent_message_id = None
    st.session_state.conversation_title = None
    for r in rows:
        st.session_state.messages.append({"role": r["MESSAGE_ROLE"], "content": r["MESSAGE_CONTENT"]})
        if r["AGENT_THREAD_ID"]: st.session_state.thread_id = r["AGENT_THREAD_ID"]
        if r["AGENT_PARENT_MESSAGE_ID"]: st.session_state.parent_message_id = r["AGENT_PARENT_MESSAGE_ID"]
    for r in rows:
        if r["MESSAGE_ROLE"] == "user":
            st.session_state.conversation_title = r["MESSAGE_CONTENT"][:100]; break


# ============================================================
# CACHED DATA LOADERS
# ============================================================
@st.cache_data(ttl=300)
def get_kpi_metrics():
    rows = session.sql("""SELECT
        (SELECT COUNT(*) FROM AML_COPILOT.RAW.AML_SIGNALS WHERE STATUS IN ('NEW','UNDER_REVIEW')) AS ACTIVE_SIGNALS,
        (SELECT COUNT(*) FROM AML_COPILOT.RAW.AML_SIGNALS WHERE STATUS IN ('NEW','UNDER_REVIEW') AND SIGNAL_SCORE>=70) AS HIGH_RISK_SIGNALS,
        (SELECT COUNT(*) FROM AML_COPILOT.RAW.RISK_CASES WHERE STATUS='OPEN') AS OPEN_CASES,
        (SELECT COALESCE(ROUND(AVG(PASS_RATE),1),0) FROM AML_COPILOT.ANALYTICS.V_LATEST_DATA_QUALITY) AS DQ_PASS_RATE,
        (SELECT COUNT(*) FROM AML_COPILOT.RAW.AML_SIGNALS WHERE DETECTION_TIMESTAMP >= CURRENT_DATE()) AS SIGNALS_TODAY,
        (SELECT COUNT(*) FROM AML_COPILOT.RAW.AML_SIGNALS WHERE DETECTION_TIMESTAMP >= CURRENT_DATE()-1 AND DETECTION_TIMESTAMP < CURRENT_DATE()) AS SIGNALS_YESTERDAY,
        (SELECT COUNT(*) FROM AML_COPILOT.RAW.RISK_CASES WHERE STATUS='FILED') AS FILED_CASES,
        (SELECT COUNT(DISTINCT CUSTOMER_ID) FROM AML_COPILOT.RAW.AML_SIGNALS WHERE STATUS IN ('NEW','UNDER_REVIEW')) AS SUSPICIOUS_ACCOUNTS
    """).collect()
    return rows[0] if rows else None

@st.cache_data(ttl=300)
def get_signal_trend():
    return session.sql("""SELECT SIGNAL_DATE, SUM(SIGNAL_COUNT) AS TOTAL_SIGNALS, SUM(ESCALATED_COUNT) AS ESCALATED,
               SUM(AFFECTED_CUSTOMERS) AS CUSTOMERS
        FROM AML_COPILOT.ANALYTICS.DT_DAILY_SIGNAL_DASHBOARD
        GROUP BY SIGNAL_DATE ORDER BY SIGNAL_DATE""").to_pandas()

@st.cache_data(ttl=300)
def get_signal_by_rule():
    return session.sql("""SELECT SIGNAL_TYPE, RULE_ID, SUM(SIGNAL_COUNT) AS TOTAL, SUM(ESCALATED_COUNT) AS ESCALATED,
               ROUND(AVG(AVG_SCORE),1) AS AVG_SCORE
        FROM AML_COPILOT.ANALYTICS.DT_DAILY_SIGNAL_DASHBOARD
        GROUP BY SIGNAL_TYPE, RULE_ID ORDER BY TOTAL DESC""").to_pandas()

@st.cache_data(ttl=300)
def get_signal_heatmap():
    return session.sql("""SELECT SIGNAL_DATE, SIGNAL_TYPE, SUM(SIGNAL_COUNT) AS CNT
        FROM AML_COPILOT.ANALYTICS.DT_DAILY_SIGNAL_DASHBOARD
        GROUP BY SIGNAL_DATE, SIGNAL_TYPE ORDER BY SIGNAL_DATE""").to_pandas()

@st.cache_data(ttl=300)
def get_top_risk_customers(limit=10):
    return session.sql(f"""SELECT CUSTOMER_ID, CUSTOMER_NAME, RISK_RATING, MAX_SIGNAL_SCORE,
               TOTAL_SIGNALS, NEW_SIGNALS, TOTAL_VOLUME_USD, CUSTOMER_COUNTRY
        FROM AML_COPILOT.ANALYTICS.DT_CUSTOMER_RISK_SUMMARY
        WHERE TOTAL_SIGNALS > 0 ORDER BY MAX_SIGNAL_SCORE DESC, TOTAL_SIGNALS DESC LIMIT {limit}""").to_pandas()

@st.cache_data(ttl=300)
def get_geographic_risk():
    return session.sql("""SELECT co.COUNTRY_NAME AS COUNTRY, COUNT(*) AS CUSTOMERS,
               SUM(crs.TOTAL_SIGNALS) AS SIGNALS, ROUND(AVG(crs.MAX_SIGNAL_SCORE),1) AS AVG_SCORE
        FROM AML_COPILOT.ANALYTICS.DT_CUSTOMER_RISK_SUMMARY crs
        LEFT JOIN AML_COPILOT.RAW.COUNTRIES co ON crs.CUSTOMER_COUNTRY = co.COUNTRY_CODE
        WHERE crs.TOTAL_SIGNALS > 0
        GROUP BY co.COUNTRY_NAME ORDER BY SIGNALS DESC LIMIT 15""").to_pandas()

@st.cache_data(ttl=300)
def get_case_summary():
    return session.sql("""SELECT STATUS, PRIORITY, COUNT(*) AS CNT FROM AML_COPILOT.RAW.RISK_CASES GROUP BY STATUS, PRIORITY ORDER BY STATUS, PRIORITY""").to_pandas()

@st.cache_data(ttl=120)
def get_signals_queue(status_filter=None, rule_filter=None, min_score=0):
    where = ["1=1"]
    if status_filter and status_filter != "All": where.append(f"s.STATUS = '{_esc(status_filter)}'")
    if rule_filter and rule_filter != "All": where.append(f"s.RULE_ID = '{_esc(rule_filter)}'")
    if min_score > 0: where.append(f"s.SIGNAL_SCORE >= {int(min_score)}")
    return session.sql(f"""SELECT s.SIGNAL_ID, s.CUSTOMER_ID, c.FIRST_NAME || ' ' || c.LAST_NAME AS CUSTOMER_NAME,
               s.SIGNAL_TYPE, s.RULE_ID, s.SIGNAL_SCORE, s.STATUS, s.DETECTION_TIMESTAMP, s.TRIGGER_DETAIL, s.DESCRIPTION
        FROM AML_COPILOT.RAW.AML_SIGNALS s
        LEFT JOIN AML_COPILOT.RAW.CUSTOMERS c ON s.CUSTOMER_ID = c.CUSTOMER_ID
        WHERE {' AND '.join(where)} ORDER BY s.SIGNAL_SCORE DESC, s.DETECTION_TIMESTAMP DESC LIMIT 100""").to_pandas()

@st.cache_data(ttl=300)
def get_customer_detail(customer_id):
    rows = session.sql(f"""SELECT c.*, crp.OVERALL_RISK_SCORE, crp.GEOGRAPHIC_RISK, crp.PRODUCT_RISK,
               crp.BEHAVIOR_RISK, crp.EDD_REQUIRED, crp.LAST_REVIEW_DATE
        FROM AML_COPILOT.RAW.CUSTOMERS c
        LEFT JOIN AML_COPILOT.RAW.CUSTOMER_RISK_PROFILE crp ON c.CUSTOMER_ID = crp.CUSTOMER_ID
        WHERE c.CUSTOMER_ID = '{_esc(customer_id)}'""").to_pandas()
    return rows.iloc[0] if len(rows) > 0 else None

@st.cache_data(ttl=300)
def get_customer_transactions(customer_id, limit=50):
    return session.sql(f"""SELECT TRANSACTION_ID, TRANSACTION_TIMESTAMP, AMOUNT_USD, TRANSACTION_TYPE,
               CHANNEL, DIRECTION, ORIGIN_COUNTRY, DESTINATION_COUNTRY, BENEFICIARY_ID, IS_SUSPICIOUS
        FROM AML_COPILOT.RAW.TRANSACTIONS WHERE CUSTOMER_ID = '{_esc(customer_id)}'
        ORDER BY TRANSACTION_TIMESTAMP DESC LIMIT {limit}""").to_pandas()

@st.cache_data(ttl=300)
def get_customer_signals(customer_id):
    return session.sql(f"""SELECT SIGNAL_ID, SIGNAL_TYPE, RULE_ID, SIGNAL_SCORE, STATUS,
               DETECTION_TIMESTAMP, TRIGGER_DETAIL, DESCRIPTION
        FROM AML_COPILOT.RAW.AML_SIGNALS WHERE CUSTOMER_ID = '{_esc(customer_id)}'
        ORDER BY DETECTION_TIMESTAMP DESC""").to_pandas()

@st.cache_data(ttl=300)
def get_customer_beneficiaries(customer_id):
    return session.sql(f"""SELECT DISTINCT b.BENEFICIARY_ID, b.BENEFICIARY_NAME, b.BENEFICIARY_TYPE,
               b.COUNTRY_CODE, b.BANK_NAME, b.RISK_SCORE, b.TRANSACTION_COUNT
        FROM AML_COPILOT.RAW.TRANSACTIONS t
        JOIN AML_COPILOT.RAW.BENEFICIARIES b ON t.BENEFICIARY_ID = b.BENEFICIARY_ID
        WHERE t.CUSTOMER_ID = '{_esc(customer_id)}' AND t.BENEFICIARY_ID IS NOT NULL""").to_pandas()

@st.cache_data(ttl=300)
def get_customer_cases(customer_id):
    return session.sql(f"""SELECT CASE_ID, CASE_TYPE, STATUS, PRIORITY, ASSIGNED_TO, OPENED_DATE, FINDING_SUMMARY, FILING_REFERENCE
        FROM AML_COPILOT.RAW.RISK_CASES WHERE CUSTOMER_ID = '{_esc(customer_id)}' ORDER BY OPENED_DATE DESC""").to_pandas()

@st.cache_data(ttl=300)
def get_all_cases():
    return session.sql("""SELECT rc.CASE_ID, rc.CUSTOMER_ID, c.FIRST_NAME || ' ' || c.LAST_NAME AS CUSTOMER_NAME,
               rc.CASE_TYPE, rc.STATUS, rc.PRIORITY, rc.ASSIGNED_TO, rc.OPENED_DATE, rc.FINDING_SUMMARY, rc.FILING_REFERENCE
        FROM AML_COPILOT.RAW.RISK_CASES rc LEFT JOIN AML_COPILOT.RAW.CUSTOMERS c ON rc.CUSTOMER_ID = c.CUSTOMER_ID
        ORDER BY rc.OPENED_DATE DESC""").to_pandas()

@st.cache_data(ttl=300)
def get_case_evidence(case_id):
    return session.sql(f"""SELECT EVIDENCE_ID, EVIDENCE_TYPE, REFERENCE_ID, DESCRIPTION, ADDED_BY, ADDED_TIMESTAMP
        FROM AML_COPILOT.RAW.CASE_EVIDENCE WHERE CASE_ID = '{_esc(case_id)}' ORDER BY ADDED_TIMESTAMP DESC""").to_pandas()

@st.cache_data(ttl=300)
def get_data_quality():
    return session.sql("SELECT * FROM AML_COPILOT.ANALYTICS.V_LATEST_DATA_QUALITY ORDER BY CHECK_NAME").to_pandas()

@st.cache_data(ttl=300)
def get_dq_history():
    return session.sql("""SELECT RUN_TIMESTAMP, CHECK_NAME, STATUS, PASS_RATE, RECORDS_CHECKED, RECORDS_FAILED
        FROM AML_COPILOT.PIPELINE.DATA_QUALITY_RESULTS ORDER BY RUN_TIMESTAMP DESC LIMIT 200""").to_pandas()

@st.cache_data(ttl=300)
def get_pipeline_runs():
    return session.sql("""SELECT RUN_ID, START_TIME AS RUN_TIMESTAMP, STATUS, RECORDS_PROCESSED, SIGNALS_GENERATED,
               TIMESTAMPDIFF('SECOND', START_TIME, COALESCE(END_TIME, CURRENT_TIMESTAMP())) AS DURATION_SECONDS
        FROM AML_COPILOT.PIPELINE.SIGNAL_DETECTION_RUNS ORDER BY START_TIME DESC LIMIT 30""").to_pandas()

@st.cache_data(ttl=300)
def get_pending_documents():
    return session.sql("""SELECT DOC_ID, TITLE AS DOC_TITLE, CATEGORY AS DOC_TYPE, STATUS,
               UPLOADED_BY, UPLOADED_AT AS UPLOAD_TIMESTAMP, REVIEWED_BY AS APPROVED_BY, REVIEWED_AT AS APPROVAL_TIMESTAMP
        FROM AML_COPILOT.PIPELINE.POLICY_DOCUMENTS_STAGED ORDER BY UPLOADED_AT DESC""").to_pandas()

@st.cache_data(ttl=300)
def get_audit_log():
    return session.sql("""SELECT AUDIT_ID, EVENT_TYPE, EVENT_SOURCE, ENTITY_TYPE, ENTITY_ID, DETAIL, USER_ID, LOGGED_AT AS EVENT_TIMESTAMP
        FROM AML_COPILOT.PIPELINE.PIPELINE_AUDIT_LOG ORDER BY LOGGED_AT DESC LIMIT 50""").to_pandas()

@st.cache_data(ttl=300)
def get_live_risk_feed():
    return session.sql("""SELECT s.SIGNAL_ID, s.CUSTOMER_ID, c.FIRST_NAME || ' ' || c.LAST_NAME AS CUSTOMER_NAME,
               s.SIGNAL_TYPE, s.SIGNAL_SCORE, s.TRIGGER_DETAIL, s.RULE_ID, s.STATUS
        FROM AML_COPILOT.RAW.AML_SIGNALS s
        LEFT JOIN AML_COPILOT.RAW.CUSTOMERS c ON s.CUSTOMER_ID = c.CUSTOMER_ID
        WHERE s.STATUS IN ('NEW','UNDER_REVIEW') ORDER BY s.SIGNAL_SCORE DESC LIMIT 8""").to_pandas()


# ============================================================
# SESSION STATE
# ============================================================
current_user = session.sql("SELECT CURRENT_USER()").collect()[0][0]
defaults = {
    "conversation_id": str(uuid.uuid4()), "messages": [], "thread_id": None,
    "parent_message_id": None, "conversation_title": None, "pending_question": None,
    "selected_customer": None, "selected_case": None, "last_suggested": [],
}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v


# ============================================================
# HEADER
# ============================================================
st.markdown(f"""<div class='header-bar'>
    <div class='logo-circle'>&#128737;</div>
    <div class='header-text'>
        <h1>RiskLens AI &mdash; AML Investigation Copilot</h1>
        <p>Monitor risk &bull; Investigate signals &bull; Generate governed findings</p>
    </div>
    <div class='header-status'>
        <span class='hs hs-live'>&#9679; LIVE</span>
        <span class='hs hs-user'>{current_user}</span>
    </div>
</div>""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("<p style='font-size:1.05rem;font-weight:700;color:#fff;margin:0;'>RiskLens AI</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.68rem;color:#90caf9;margin:0 0 0.4rem;'>AML Investigation Copilot</p>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<p class='sb-section-title'>Detection Rules</p>", unsafe_allow_html=True)
    for rid, name, desc, color in RISK_RULES:
        st.markdown(f"<div class='rule-tooltip-wrap'><span class='rule-chip' style='background:{color};'>{name}</span><span class='rule-tt'>{desc}</span></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<p class='sb-section-title'>Conversations</p>", unsafe_allow_html=True)
    if st.button("+ New Chat", key="btn_new_chat", use_container_width=True):
        st.session_state.conversation_id = str(uuid.uuid4())
        st.session_state.messages = []; st.session_state.thread_id = None
        st.session_state.parent_message_id = None; st.session_state.conversation_title = None
        st.session_state.pending_question = None
        if _rerun: _rerun()
    conversations = load_conversations(current_user)
    if conversations:
        for conv in conversations[:12]:
            cid = conv["CONVERSATION_ID"]
            title = conv["TITLE"] or conv["FIRST_Q"] or "Untitled"
            dtitle = (title[:35] + "...") if len(title) > 35 else title
            col_conv, col_del = st.columns([5, 1])
            with col_conv:
                if st.button(f"{'> ' if cid == st.session_state.conversation_id else ''}{dtitle}", key=f"h_{cid}", use_container_width=True):
                    restore_conversation(cid)
                    if _rerun: _rerun()
            with col_del:
                if st.button("x", key=f"del_{cid}"):
                    delete_conversation(cid); load_conversations.clear()
                    if _rerun: _rerun()
    st.markdown("---")
    st.markdown("<p class='sb-section-title'>User</p>", unsafe_allow_html=True)
    st.markdown(f"<div class='sb-user-badge'><strong>{current_user}</strong></div>", unsafe_allow_html=True)


# ============================================================
# MAIN TABS
# ============================================================
tab_copilot, tab_dash, tab_invest, tab_reports, tab_evidence, tab_ops = st.tabs([
    "AI Copilot", "Dashboard", "Investigations",
    "Regulatory Reports", "Evidence Center", "CoCo Operations",
])


# ============================================================
# TAB 1: DASHBOARD — Risk Command Center
# ============================================================
with tab_dash:
    kpi = get_kpi_metrics()
    if kpi:
        active_signals = int(kpi["ACTIVE_SIGNALS"]); high_risk = int(kpi["HIGH_RISK_SIGNALS"])
        open_cases = int(kpi["OPEN_CASES"]); dq_rate = float(kpi["DQ_PASS_RATE"] or 0)
        today_signals = int(kpi["SIGNALS_TODAY"]); yesterday_signals = int(kpi["SIGNALS_YESTERDAY"])
        filed = int(kpi["FILED_CASES"]); suspicious_accts = int(kpi["SUSPICIOUS_ACCOUNTS"])
        delta = today_signals - yesterday_signals if yesterday_signals > 0 else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.markdown(kpi_html("Critical Alerts", high_risk, "red", "kpi-card-red"), unsafe_allow_html=True)
        with c2: st.markdown(kpi_html("Suspicious Accounts", suspicious_accts, "amber", "kpi-card-amber"), unsafe_allow_html=True)
        with c3: st.markdown(kpi_html("Open Investigations", open_cases, "purple", "kpi-card-purple"), unsafe_allow_html=True)
        with c4: st.markdown(kpi_html("SAR Drafts Ready", filed, "blue", "kpi-card-blue"), unsafe_allow_html=True)
        with c5:
            cls = "green" if dq_rate >= 90 else "amber" if dq_rate >= 70 else "red"
            st.markdown(kpi_html("Compliance Health", f"{dq_rate}%", cls, f"kpi-card-{cls}"), unsafe_allow_html=True)

    st.markdown("")
    col_left, col_right = st.columns([3, 2])

    with col_left:
        # Signal Trend
        st.markdown("<div class='card'><div class='card-header'>Signal Trend <span class='card-sub'>Daily signal volume, escalations, affected customers</span></div>", unsafe_allow_html=True)
        trend_df = get_signal_trend()
        if len(trend_df) > 0:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=trend_df["SIGNAL_DATE"], y=trend_df["TOTAL_SIGNALS"], fill='tozeroy', name="Total", line=dict(color="#3498DB", width=2.5), fillcolor="rgba(52,152,219,0.08)"))
            fig.add_trace(go.Scatter(x=trend_df["SIGNAL_DATE"], y=trend_df["ESCALATED"], mode="lines+markers", name="Escalated", line=dict(color="#E74C3C", width=2), marker=dict(size=5)))
            fig.add_trace(go.Scatter(x=trend_df["SIGNAL_DATE"], y=trend_df["CUSTOMERS"], mode="lines", name="Customers", line=dict(color="#1ABC9C", width=1.5, dash="dot")))
            plotly_theme(fig, 280)
            fig.update_layout(legend=dict(orientation="h", y=-0.15, font=dict(size=10)))
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Signals by Rule
        st.markdown("<div class='card'><div class='card-header'>Signals by Detection Rule <span class='card-sub'>Total count per rule with average risk score</span></div>", unsafe_allow_html=True)
        rule_df = get_signal_by_rule()
        if len(rule_df) > 0:
            rule_df_sorted = rule_df.sort_values("TOTAL", ascending=True)
            colors = [RULE_COLORS.get(r, "#999") for r in rule_df_sorted["RULE_ID"]]
            fig = go.Figure(go.Bar(x=rule_df_sorted["TOTAL"], y=rule_df_sorted["SIGNAL_TYPE"], orientation='h', marker_color=colors, text=rule_df_sorted["TOTAL"], textposition='auto'))
            plotly_theme(fig, 260)
            fig.update_layout(yaxis=dict(tickfont=dict(size=10)))
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        # Live Risk Feed
        st.markdown("<div class='card'><div class='card-header'>Live Risk Feed <span class='card-sub'>Highest-priority unreviewed signals</span></div>", unsafe_allow_html=True)
        feed_df = get_live_risk_feed()
        if len(feed_df) > 0:
            for _, row in feed_df.head(6).iterrows():
                score = int(row["SIGNAL_SCORE"])
                border_cls = "" if score >= 70 else "medium" if score >= 40 else "low"
                rule_name = RULE_NAMES.get(row["RULE_ID"], row["SIGNAL_TYPE"])
                trigger = str(row.get("TRIGGER_DETAIL", ""))[:120]
                st.markdown(f"""<div class='risk-feed-item {border_cls}'>
                    <div style='display:flex;justify-content:space-between;align-items:center;'>
                        <p class='risk-feed-title'>{rule_name}</p>
                        <span class='risk-feed-score {risk_class(score)}'>{score}</span>
                    </div>
                    <p class='risk-feed-detail'><strong>{row['CUSTOMER_ID']}</strong> &mdash; {row.get('CUSTOMER_NAME','')}<br>{safe_md(trigger)}</p>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No active risk signals.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Bottom row: Top customers + Heatmap
    col_top, col_heat = st.columns(2)
    with col_top:
        st.markdown("<div class='card'><div class='card-header'>Top 10 Risk Customers <span class='card-sub'>Ranked by signal score and volume</span></div>", unsafe_allow_html=True)
        top_df = get_top_risk_customers()
        if len(top_df) > 0:
            st.dataframe(top_df[["CUSTOMER_ID","CUSTOMER_NAME","RISK_RATING","MAX_SIGNAL_SCORE","TOTAL_SIGNALS","CUSTOMER_COUNTRY"]], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_heat:
        st.markdown("<div class='card'><div class='card-header'>Signal Heatmap <span class='card-sub'>Signal type intensity by date</span></div>", unsafe_allow_html=True)
        heat_df = get_signal_heatmap()
        if len(heat_df) > 0:
            heat_df["SIGNAL_DATE"] = heat_df["SIGNAL_DATE"].astype(str)
            pivot = heat_df.pivot_table(index="SIGNAL_TYPE", columns="SIGNAL_DATE", values="CNT", fill_value=0)
            pivot = pivot.reindex(sorted(pivot.columns), axis=1)
            fig = go.Figure(data=go.Heatmap(z=pivot.values.tolist(), x=pivot.columns.tolist(), y=pivot.index.tolist(),
                colorscale=[[0,'#FFF8F0'],[0.2,'#F5D5B0'],[0.4,'#E8913A'],[0.6,'#B55D0C'],[0.8,'#B85A0D'],[1,'#1E3A5F']], hoverongaps=False))
            plotly_theme(fig, 280)
            fig.update_layout(xaxis=dict(tickfont=dict(size=8)), yaxis=dict(tickfont=dict(size=10)))
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# TAB 2: INVESTIGATIONS — Full Investigation Workspace
# ============================================================
with tab_invest:
    # Workflow bar
    st.markdown("""<div style='text-align:center;padding:0.4rem 0 0.6rem;'>
        <span class='wf-step wf-active'>1. Signal Detection</span><span class='wf-arrow'>&rarr;</span>
        <span class='wf-step wf-active'>2. Investigation</span><span class='wf-arrow'>&rarr;</span>
        <span class='wf-step wf-pending'>3. Evidence</span><span class='wf-arrow'>&rarr;</span>
        <span class='wf-step wf-pending'>4. Decision</span><span class='wf-arrow'>&rarr;</span>
        <span class='wf-step wf-pending'>5. Regulatory Report</span>
    </div>""", unsafe_allow_html=True)

    # Filters
    fc1, fc2, fc3 = st.columns(3)
    with fc1: status_opt = st.selectbox("Status", ["All","NEW","UNDER_REVIEW","ESCALATED","DISMISSED"], key="inv_status")
    with fc2: rule_opt = st.selectbox("Rule", ["All"] + [r[0] for r in RISK_RULES], key="inv_rule")
    with fc3: score_min = st.slider("Min Score", 0, 100, 0, key="inv_score")

    signals_df = get_signals_queue(status_opt, rule_opt, score_min)

    if len(signals_df) > 0:
        st.dataframe(signals_df[["SIGNAL_ID","CUSTOMER_ID","CUSTOMER_NAME","SIGNAL_TYPE","SIGNAL_SCORE","STATUS","DETECTION_TIMESTAMP"]], use_container_width=True)

        customer_ids = signals_df["CUSTOMER_ID"].dropna().unique().tolist()
        selected = st.selectbox("Select customer for Risk 360 investigation", [""] + customer_ids, key="inv_cust_select")

        if selected:
            st.session_state.selected_customer = selected
            st.markdown("---")
            cust = get_customer_detail(selected)
            if cust is not None:
                st.markdown(f"### Customer Risk 360: {selected}")
                # Profile cards
                pc1, pc2, pc3, pc4, pc5, pc6 = st.columns(6)
                with pc1: st.metric("Customer", f"{cust.get('FIRST_NAME','')} {cust.get('LAST_NAME','')}")
                with pc2: st.metric("Risk Score", int(cust.get("OVERALL_RISK_SCORE",0) or 0))
                with pc3: st.metric("Risk Rating", cust.get("RISK_RATING","N/A"))
                with pc4: st.metric("KYC Status", cust.get("KYC_STATUS","N/A"))
                with pc5:
                    flags = []
                    if cust.get("PEP_FLAG"): flags.append("PEP")
                    if cust.get("SANCTIONS_FLAG"): flags.append("SANCTIONS")
                    if cust.get("EDD_REQUIRED"): flags.append("EDD")
                    st.metric("Flags", ", ".join(flags) if flags else "None")
                with pc6: st.metric("Country", cust.get("COUNTRY_CODE","N/A"))

                # Risk gauge + breakdown
                gc1, gc2 = st.columns([1, 2])
                ors = int(cust.get("OVERALL_RISK_SCORE", 0) or 0)
                with gc1:
                    fig = go.Figure(go.Indicator(mode="gauge+number", value=ors,
                        gauge=dict(axis=dict(range=[0,100]), bar=dict(color="#3498DB"),
                            steps=[dict(range=[0,40],color="#EAFAF1"),dict(range=[40,70],color="#FEF9E7"),dict(range=[70,100],color="#FDEDEC")],
                            threshold=dict(line=dict(color="#E74C3C",width=3),thickness=0.8,value=70)),
                        title=dict(text="Risk Score",font=dict(size=13))))
                    plotly_theme(fig, 230); st.plotly_chart(fig, use_container_width=True)

                with gc2:
                    risk_components = {"Geographic": float(cust.get("GEOGRAPHIC_RISK",0) or 0),
                                       "Product": float(cust.get("PRODUCT_RISK",0) or 0),
                                       "Behavior": float(cust.get("BEHAVIOR_RISK",0) or 0)}
                    rc_names = list(risk_components.keys()); rc_vals = list(risk_components.values())
                    rc_colors = ["#E74C3C" if v>=70 else "#F39C12" if v>=40 else "#27AE60" for v in rc_vals]
                    # Donut
                    total = sum(rc_vals) or 1
                    fig_d = go.Figure(go.Pie(labels=rc_names, values=rc_vals, hole=0.55,
                        marker=dict(colors=rc_colors), textinfo="label+percent", textfont=dict(size=11)))
                    plotly_theme(fig_d, 230)
                    fig_d.update_layout(title=dict(text="Risk Explainability", font=dict(size=13)), showlegend=False)
                    st.plotly_chart(fig_d, use_container_width=True)

                # Customer detail sub-tabs
                ct1, ct2, ct3, ct4 = st.tabs(["Transaction Timeline", "Signals", "Network Analysis", "Cases"])

                with ct1:
                    txn_df = get_customer_transactions(selected)
                    if len(txn_df) > 0:
                        fig = px.scatter(txn_df, x="TRANSACTION_TIMESTAMP", y="AMOUNT_USD", color="IS_SUSPICIOUS",
                            color_discrete_map={True:"#E74C3C",False:"#3498DB"},
                            hover_data=["TRANSACTION_TYPE","CHANNEL","DIRECTION"],
                            title="Transaction timeline — red = suspicious activity")
                        plotly_theme(fig, 300)
                        fig.update_traces(marker=dict(size=8, line=dict(width=0.5, color='white')))
                        fig.update_layout(legend=dict(orientation="h", y=-0.15))
                        st.plotly_chart(fig, use_container_width=True)
                        st.dataframe(txn_df, use_container_width=True)

                with ct2:
                    sig_df = get_customer_signals(selected)
                    if len(sig_df) > 0:
                        for _, row in sig_df.iterrows():
                            col_a, col_b = st.columns([3,1])
                            with col_a:
                                rule_name = RULE_NAMES.get(row["RULE_ID"], row["SIGNAL_TYPE"])
                                color = RULE_COLORS.get(row["RULE_ID"], "#999")
                                trigger = str(row.get("TRIGGER_DETAIL",""))[:200]
                                st.markdown(f"<span class='rule-chip' style='background:{color};'>{rule_name}</span> Score: **{int(row['SIGNAL_SCORE'])}** | {status_badge(row['STATUS'])}<br><span style='font-size:0.78rem;color:#475569;'>{safe_md(trigger)}</span>", unsafe_allow_html=True)
                            with col_b:
                                st.caption(str(row["DETECTION_TIMESTAMP"])[:19] if row["DETECTION_TIMESTAMP"] else "")

                with ct3:
                    ben_df = get_customer_beneficiaries(selected)
                    if len(ben_df) > 0:
                        nodes_x, nodes_y, labels, colors, sizes = [0],[0],[selected],["#3498DB"],[30]
                        edge_x, edge_y = [],[]
                        for i, (_, b) in enumerate(ben_df.iterrows()):
                            angle = 2*math.pi*i/len(ben_df)
                            bx, by = math.cos(angle)*2.2, math.sin(angle)*2.2
                            nodes_x.append(bx); nodes_y.append(by)
                            labels.append(b["BENEFICIARY_NAME"][:18] if b["BENEFICIARY_NAME"] else b["BENEFICIARY_ID"])
                            rs = b.get("RISK_SCORE",0) or 0
                            colors.append("#E74C3C" if rs>=70 else "#F39C12" if rs>=40 else "#27AE60")
                            sizes.append(max(14, min(28, int(rs/4))))
                            edge_x.extend([0,bx,None]); edge_y.extend([0,by,None])
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=edge_x,y=edge_y,mode="lines",line=dict(color="#ddd",width=1),hoverinfo="none",showlegend=False))
                        fig.add_trace(go.Scatter(x=nodes_x,y=nodes_y,mode="markers+text",marker=dict(size=sizes,color=colors,line=dict(width=1.5,color="#fff")),text=labels,textposition="top center",textfont=dict(size=9),showlegend=False))
                        plotly_theme(fig, 340)
                        fig.update_layout(xaxis=dict(visible=False),yaxis=dict(visible=False),title=dict(text="Beneficiary Network — node color/size = risk", font=dict(size=13)))
                        st.plotly_chart(fig, use_container_width=True)
                        st.dataframe(ben_df, use_container_width=True)
                    else: st.info("No beneficiaries found.")

                with ct4:
                    case_df = get_customer_cases(selected)
                    if len(case_df) > 0: st.dataframe(case_df, use_container_width=True)
                    else: st.info("No cases found.")

                # Action buttons
                st.markdown("---")
                st.markdown("**Recommended Actions**")
                ac1, ac2, ac3, ac4 = st.columns(4)
                with ac1:
                    if st.button("Generate SAR Draft", key="inv_sar", use_container_width=True):
                        st.session_state["inv_action"] = f"Generate an audit-ready SAR narrative for customer {selected}. Include subject information, activity summary, suspicious indicators, supporting evidence, and recommended action."
                        if _rerun: _rerun()
                with ac2:
                    if st.button("Escalate Case", key="inv_esc", use_container_width=True):
                        st.info("Case escalation would be triggered here in production.")
                with ac3:
                    if st.button("Request KYC Update", key="inv_kyc", use_container_width=True):
                        st.info("KYC refresh request would be submitted here.")
                with ac4:
                    if st.button("AI Investigation", key="inv_ai", use_container_width=True):
                        st.session_state["inv_action"] = f"Investigate customer {selected}. Show their risk score, recent signals with rule IDs and trigger details, suspicious transactions, and applicable policies."
                        if _rerun: _rerun()

                # Render investigation AI response inline (not in copilot)
                if st.session_state.get("inv_action"):
                    inv_prompt = st.session_state.pop("inv_action")
                    st.markdown("---")
                    st.markdown("#### AI Investigation Result")
                    with st.spinner("Investigating..."):
                        try:
                            inv_resp = call_agent(inv_prompt)
                            if inv_resp["text"]:
                                st.markdown(safe_md(inv_resp["text"]))
                                render_agent_tables(inv_resp.get("tables", []))
                                render_citations(inv_resp.get("citations", []))
                            else:
                                st.warning("No response generated.")
                        except Exception as e:
                            st.error(f"Investigation failed: {str(e)[:200]}")
    else:
        st.info("No signals match the current filters.")


# ============================================================
# TAB 1: AI COPILOT — ChatGPT/Claude-style Interface
# ============================================================
with tab_copilot:
    # Chat bubble CSS
    st.markdown("""<style>
    .chat-msg { display:flex; gap:0.6rem; margin-bottom:0.8rem; align-items:flex-start; }
    .chat-msg.user { flex-direction:row-reverse; }
    .chat-avatar { width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center;
        font-size:0.85rem; font-weight:700; flex-shrink:0; color:#fff; }
    .chat-avatar.user-av { background:linear-gradient(135deg,#1E3A5F,#2C3E50); }
    .chat-avatar.bot-av { background:linear-gradient(135deg,#B55D0C,#E8913A); }
    .chat-bubble { max-width:80%; padding:0.7rem 1rem; border-radius:12px; font-size:0.85rem; line-height:1.65; }
    .chat-bubble.user-bubble { background:#EFF6FF; border:1px solid #BFDBFE; border-top-right-radius:2px; color:#0F172A; }
    .chat-bubble.bot-bubble { background:#fff; border:1px solid #E2E8F0; border-top-left-radius:2px; color:#0F172A;
        box-shadow:0 1px 3px rgba(0,0,0,0.04); }
    .chat-bubble.bot-bubble h1,.chat-bubble.bot-bubble h2,.chat-bubble.bot-bubble h3 { font-size:0.95rem; margin:0.5rem 0 0.3rem; }
    .chat-bubble.bot-bubble ul,.chat-bubble.bot-bubble ol { margin:0.3rem 0; padding-left:1.2rem; }
    .chat-bubble.bot-bubble li { margin:0.15rem 0; }
    .chat-bubble.bot-bubble strong { color:#0F172A; }
    .chat-role { font-size:0.62rem; color:#94A3B8; margin-bottom:0.15rem; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; }
    .chat-msg.user .chat-role { text-align:right; }
    .followup-chip { display:inline-block; padding:0.3rem 0.7rem; border:1px solid #E2E8F0; border-radius:18px;
        font-size:0.72rem; color:#475569; background:#FAFBFC; margin:0.2rem 0.3rem 0.2rem 0; cursor:default;
        transition:all 0.15s; }
    .followup-chip:hover { border-color:#B55D0C; color:#B55D0C; background:#FFFBF5; }
    </style>""", unsafe_allow_html=True)

    # Welcome screen with suggested questions
    if not st.session_state.messages:
        st.markdown("""<div style='text-align:center;padding:1.2rem 0 0.6rem;'>
            <div style='font-size:2rem;margin-bottom:0.3rem;'>&#128737;</div>
            <h3 style='margin:0;color:#0F172A;font-size:1.1rem;'>AML Investigation Copilot</h3>
            <p style='color:#64748B;font-size:0.78rem;margin:0.3rem auto 0;max-width:600px;line-height:1.5;'>
                Every answer combines <strong>transaction data</strong> with <strong>policy citations</strong>.
                Ask about signals, customers, or regulations &mdash; get governed, evidence-backed responses
                with the complete flow from signal to finding.
            </p>
            <div style='margin-top:0.6rem;display:flex;justify-content:center;gap:0.4rem;flex-wrap:wrap;'>
                <span class='source-tag source-data' style='font-size:0.68rem;padding:3px 10px;'>500K+ Transactions</span>
                <span class='source-tag source-data' style='font-size:0.68rem;padding:3px 10px;'>200+ AML Signals</span>
                <span class='source-tag source-policy' style='font-size:0.68rem;padding:3px 10px;'>11 Policy Documents</span>
                <span class='source-tag source-data' style='font-size:0.68rem;padding:3px 10px;'>50 Investigation Cases</span>
            </div>
        </div>""", unsafe_allow_html=True)
        cols = st.columns(4)
        for i, (q, icon_key, cat) in enumerate(SUGGESTED_QUESTIONS):
            with cols[i % 4]:
                if st.button(q, key=f"sq_{i}"):
                    st.session_state.pending_question = q
                    if _rerun: _rerun()
        st.markdown("")

    # Chat history with bubbles
    chat_container = st.container()
    with chat_container:
        for mi, msg in enumerate(st.session_state.messages):
            if msg["role"] == "user":
                st.markdown(f"""<div class='chat-msg user'>
                    <div class='chat-avatar user-av'>{current_user[0]}</div>
                    <div><div class='chat-role'>You</div>
                    <div class='chat-bubble user-bubble'>{safe_md(msg['content'])}</div></div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class='chat-msg'>
                    <div class='chat-avatar bot-av'>R</div>
                    <div><div class='chat-role'>RiskLens AI</div>
                    <div class='chat-bubble bot-bubble'>{safe_md(msg['content'])}</div></div>
                </div>""", unsafe_allow_html=True)

    # Follow-up suggestions (rendered persistently outside the pending block)
    if st.session_state.get("last_suggested") and st.session_state.messages:
        st.markdown("")
        fcols = st.columns(min(len(st.session_state.last_suggested), 3))
        for si, sq in enumerate(st.session_state.last_suggested[:3]):
            with fcols[si]:
                if st.button(sq, key=f"followup_{si}"):
                    st.session_state.pending_question = sq
                    st.session_state.last_suggested = []
                    if _rerun: _rerun()

    # Pending question from buttons
    pending = st.session_state.pending_question
    if pending:
        st.session_state.pending_question = None

    # Input bar
    input_key = f"chat_input_{st.session_state.conversation_id}_{len(st.session_state.messages)}"
    user_input = st.text_input("Message RiskLens AI...", key=input_key, placeholder="Ask about customers, signals, policies, or request an investigation...")
    if user_input and not pending:
        pending = user_input

    # Process question
    if pending:
        st.session_state.messages.append({"role": "user", "content": pending})
        with chat_container:
            st.markdown(f"""<div class='chat-msg user'>
                <div class='chat-avatar user-av'>{current_user[0]}</div>
                <div><div class='chat-role'>You</div>
                <div class='chat-bubble user-bubble'>{safe_md(pending)}</div></div>
            </div>""", unsafe_allow_html=True)

        if not st.session_state.conversation_title:
            st.session_state.conversation_title = pending[:100]

        save_message(st.session_state.conversation_id, current_user, st.session_state.conversation_title,
                     "user", pending, len(st.session_state.messages),
                     st.session_state.thread_id, st.session_state.parent_message_id)

        with chat_container:
            with st.spinner("Thinking..."):
                try:
                    response = call_agent(pending, st.session_state.thread_id, st.session_state.parent_message_id)
                    agent_text = response["text"]

                    if agent_text:
                        st.markdown(f"""<div class='chat-msg'>
                            <div class='chat-avatar bot-av'>R</div>
                            <div><div class='chat-role'>RiskLens AI</div>
                            <div class='chat-bubble bot-bubble'>{safe_md(agent_text)}</div></div>
                        </div>""", unsafe_allow_html=True)
                        render_agent_tables(response.get("tables", []))
                        for cs in response.get("charts", []):
                            try: st.vega_lite_chart(json.loads(cs), use_container_width=True)
                            except Exception: pass
                        render_citations(response.get("citations", []))
                        render_evidence_sources(response)

                    st.session_state.last_suggested = response.get("suggested", [])

                    if not agent_text:
                        debug = response.get("debug", "")[:500]
                        st.warning(f"No text extracted. Debug: {debug}")
                        agent_text = "[Response received]"

                    meta = response.get("metadata", {})
                    if meta.get("thread_id"): st.session_state.thread_id = meta["thread_id"]
                    if meta.get("assistant_message_id"): st.session_state.parent_message_id = meta["assistant_message_id"]

                    st.session_state.messages.append({"role": "assistant", "content": agent_text})
                    save_message(st.session_state.conversation_id, current_user, st.session_state.conversation_title,
                                 "assistant", agent_text, len(st.session_state.messages),
                                 st.session_state.thread_id, st.session_state.parent_message_id)
                except Exception as e:
                    st.error(f"Unable to process the request. Please try again.")
                    st.session_state.messages.append({"role": "assistant", "content": "Error processing request."})


# ============================================================
# TAB 4: REGULATORY REPORTS
# ============================================================
with tab_reports:
    st.markdown("#### Regulatory Report Generation")
    cases_df = get_all_cases()
    if len(cases_df) > 0:
        case_options = cases_df.apply(lambda r: f"{r['CASE_ID']} -- {r['CUSTOMER_NAME']} ({r['STATUS']}, {r['PRIORITY']})", axis=1).tolist()
        selected_case = st.selectbox("Select Case", [""] + case_options, key="report_case")

        if selected_case:
            case_id = selected_case.split(" -- ")[0]
            case_row = cases_df[cases_df["CASE_ID"] == case_id].iloc[0]

            st.markdown("<div class='card'>", unsafe_allow_html=True)
            rc1, rc2, rc3, rc4 = st.columns(4)
            with rc1: st.metric("Case ID", case_id)
            with rc2: st.metric("Customer", case_row["CUSTOMER_NAME"])
            with rc3: st.metric("Priority", case_row["PRIORITY"])
            with rc4: st.metric("Status", case_row["STATUS"])
            if case_row.get("FINDING_SUMMARY"):
                st.markdown(f"**Finding:** {safe_md(str(case_row['FINDING_SUMMARY']))}")
            if case_row.get("FILING_REFERENCE"):
                st.success(f"Filing Reference: {case_row['FILING_REFERENCE']}")
            st.markdown("</div>", unsafe_allow_html=True)

            ev_df = get_case_evidence(case_id)
            if len(ev_df) > 0:
                with st.expander(f"Case Evidence ({len(ev_df)} items)", expanded=False):
                    st.dataframe(ev_df, use_container_width=True)

            st.markdown("---")
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("Generate SAR Narrative", key="gen_sar", use_container_width=True):
                    prompt = f"Generate an audit-ready SAR narrative for case {case_id} (customer {case_row['CUSTOMER_ID']}). Include: Subject Information, Activity Summary, Suspicious Indicators, Supporting Evidence, and Recommended Action."
                    with st.spinner("Generating regulatory narrative..."):
                        try:
                            resp = call_agent(prompt)
                            if resp["text"]:
                                st.markdown("### SAR Narrative")
                                st.markdown(safe_md(resp["text"]))
                                render_agent_tables(resp.get("tables", []))
                                render_citations(resp.get("citations", []))
                        except Exception: st.error("Failed to generate narrative.")

            with btn_col2:
                if st.button("Generate PDF Report", key="export_drive", use_container_width=True):
                    with st.spinner("Generating PDF report..."):
                        try:
                            result = session.sql(f"CALL AML_COPILOT.PIPELINE.SP_EXPORT_REPORT_TO_DRIVE('{_esc(case_id)}')").collect()
                            result_text = str(result[0][0]) if result else "No result"
                            if "successfully" in result_text.lower():
                                st.success(result_text)
                                import base64
                                pdf_row = session.sql(f"""SELECT FILENAME, PDF_DATA FROM AML_COPILOT.PIPELINE.GENERATED_REPORTS
                                    WHERE CASE_ID = '{_esc(case_id)}' ORDER BY GENERATED_AT DESC LIMIT 1""").collect()
                                if pdf_row:
                                    b64 = base64.b64encode(bytes(pdf_row[0]["PDF_DATA"])).decode()
                                    st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="{pdf_row[0]["FILENAME"]}">Download PDF Report</a>', unsafe_allow_html=True)
                            else: st.warning(result_text)
                        except Exception as e: st.error(f"Export failed: {str(e)[:200]}")

            existing_reports = session.sql(f"""SELECT REPORT_ID, FILENAME, PDF_DATA, GENERATED_BY, GENERATED_AT
                FROM AML_COPILOT.PIPELINE.GENERATED_REPORTS WHERE CASE_ID = '{_esc(case_id)}' ORDER BY GENERATED_AT DESC LIMIT 5""").collect()
            if existing_reports:
                st.markdown("---")
                st.markdown("#### Generated Reports")
                for rpt in existing_reports:
                    rc1, rc2, rc3 = st.columns([3,2,1])
                    with rc1: st.markdown(f"**{rpt['FILENAME']}**")
                    with rc2: st.caption(f"{rpt['GENERATED_BY']} | {str(rpt['GENERATED_AT'])[:19]}")
                    with rc3:
                        import base64
                        b64_dl = base64.b64encode(bytes(rpt["PDF_DATA"])).decode()
                        st.markdown(f'<a href="data:application/pdf;base64,{b64_dl}" download="{rpt["FILENAME"]}">Download</a>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Filing Tracker")
        filed = cases_df[cases_df["FILING_REFERENCE"].notna() & (cases_df["FILING_REFERENCE"] != "")]
        if len(filed) > 0:
            st.dataframe(filed[["CASE_ID","CUSTOMER_NAME","CASE_TYPE","PRIORITY","FILING_REFERENCE"]], use_container_width=True)
        else: st.info("No filings on record.")
    else: st.info("No cases available.")


# ============================================================
# TAB 5: EVIDENCE CENTER
# ============================================================
with tab_evidence:
    ev_tab1, ev_tab2, ev_tab3 = st.tabs(["Evidence Browser", "Policy Search", "Data Quality"])

    with ev_tab1:
        st.markdown("#### Case Evidence Browser")
        cases_df2 = get_all_cases()
        if len(cases_df2) > 0:
            ev_case = st.selectbox("Filter by Case", ["All"] + cases_df2["CASE_ID"].tolist(), key="ev_case_filter")
            if ev_case != "All":
                ev_data = get_case_evidence(ev_case)
            else:
                ev_data = session.sql("""SELECT ce.EVIDENCE_ID, ce.CASE_ID, ce.EVIDENCE_TYPE, ce.REFERENCE_ID,
                       ce.DESCRIPTION, ce.ADDED_BY, ce.ADDED_TIMESTAMP
                    FROM AML_COPILOT.RAW.CASE_EVIDENCE ce ORDER BY ce.ADDED_TIMESTAMP DESC LIMIT 100""").to_pandas()
            if len(ev_data) > 0:
                # Evidence type breakdown
                if "EVIDENCE_TYPE" in ev_data.columns:
                    ev_types = ev_data["EVIDENCE_TYPE"].value_counts().reset_index()
                    ev_types.columns = ["Type", "Count"]
                    ec1, ec2 = st.columns([1,2])
                    with ec1:
                        for _, row in ev_types.iterrows():
                            icon = {"TRANSACTION":"&#128176;","SIGNAL":"&#9888;","POLICY":"&#128220;"}.get(row["Type"],"&#128196;")
                            st.markdown(f"{icon} **{row['Type']}**: {row['Count']}", unsafe_allow_html=True)
                    with ec2:
                        st.dataframe(ev_data, use_container_width=True)
                else:
                    st.dataframe(ev_data, use_container_width=True)
            else: st.info("No evidence items found.")

    with ev_tab2:
        st.markdown("#### Policy Document Search")
        policy_query = st.text_input("Search AML policies...", key="policy_search", placeholder="e.g., structuring, wire transfer, KYC, EDD, SAR filing")
        if policy_query:
            with st.spinner("Searching policies..."):
                try:
                    search_results = session.sql(f"""SELECT PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                            'AML_COPILOT.ANALYTICS.POLICY_SEARCH_SERVICE',
                            '{{"query": "{policy_query.replace("'", "''").replace('"', '')}", "columns": ["TITLE", "CATEGORY", "JURISDICTION", "CHUNK_TEXT"], "limit": 5}}'
                        )) AS result""").collect()
                    if search_results:
                        result_json = json.loads(str(search_results[0]["RESULT"]))
                        hits = result_json.get("results", [])
                        if hits:
                            for i, hit in enumerate(hits):
                                title = hit.get("TITLE","Unknown"); category = hit.get("CATEGORY","")
                                jurisdiction = hit.get("JURISDICTION",""); chunk = hit.get("CHUNK_TEXT","")
                                st.markdown(f"---")
                                st.markdown(f"**{i+1}. {title}**")
                                st.caption(f"Category: {category}  |  Jurisdiction: {jurisdiction}")
                                st.markdown(f"<div style='background:#FFFBF5;border-left:3px solid #B55D0C;padding:0.7rem 1rem;border-radius:4px;font-size:0.82rem;line-height:1.6;white-space:pre-wrap;'>{chunk}</div>", unsafe_allow_html=True)
                        else: st.info("No matching policies found.")
                except Exception as e: st.error(f"Policy search failed: {str(e)[:200]}")

        st.markdown("---")
        st.markdown("#### Approved Policy Documents")
        docs_df = get_pending_documents()
        if len(docs_df) > 0:
            approved = docs_df[docs_df["STATUS"] == "APPROVED"]
            if len(approved) > 0:
                st.dataframe(approved[["DOC_ID","DOC_TITLE","DOC_TYPE","UPLOADED_BY","APPROVAL_TIMESTAMP"]], use_container_width=True)

    with ev_tab3:
        st.markdown("#### Data Quality Dashboard")
        dq_df = get_data_quality()
        if len(dq_df) > 0:
            avg_pass = dq_df["PASS_RATE"].mean() if "PASS_RATE" in dq_df.columns else 0
            dq_m1, dq_m2 = st.columns(2)
            with dq_m1: st.metric("Average Pass Rate", f"{avg_pass:.1f}%")
            with dq_m2: st.metric("Active Checks", len(dq_df))
            st.dataframe(dq_df, use_container_width=True)
            dq_hist = get_dq_history()
            if len(dq_hist) > 0 and "RUN_TIMESTAMP" in dq_hist.columns and "PASS_RATE" in dq_hist.columns:
                fig = px.line(dq_hist, x="RUN_TIMESTAMP", y="PASS_RATE", color="CHECK_NAME", color_discrete_sequence=px.colors.qualitative.Set2)
                plotly_theme(fig, 280)
                fig.update_layout(legend=dict(orientation="h", y=-0.2))
                st.plotly_chart(fig, use_container_width=True)


# ============================================================
# TAB 6: COCO OPERATIONS
# ============================================================
with tab_ops:
    st.markdown("#### CoCo Operations — Snowflake AI Pipeline Architecture")

    # Architecture checklist
    st.markdown("<div class='card'><div class='card-header'>CoCo-Built Components <span class='card-sub'>Every component was generated and deployed using Snowflake CoCo</span></div>", unsafe_allow_html=True)

    checks = [
        ("Synthetic Data Generated", "500K transactions, 10K customers, 8K beneficiaries, 200+ signals, 50 cases", True),
        ("Semantic View Created", "AML_COPILOT.RAW.AML_COPILOT_SV — 13 tables, 11 relationships, 7 verified queries", True),
        ("Cortex Agent Deployed", "AML_RISK_COPILOT with risk_analytics + policy_search tools", True),
        ("Cortex Search Service", "POLICY_SEARCH_SERVICE — 11 AML policy documents indexed", True),
        ("Dynamic Tables Running", "DT_ENRICHED_TRANSACTIONS, DT_CUSTOMER_RISK_FEATURES, DT_CUSTOMER_RISK_SUMMARY, DT_DAILY_SIGNAL_DASHBOARD", True),
        ("Streams Configured", "STREAM_NEW_TRANSACTIONS for incremental signal detection", True),
        ("Tasks Scheduled", "DETECT_AML_SIGNALS (5-min) + RUN_DATA_QUALITY_CHECKS (15-min)", True),
        ("Stored Procedures", "SP_DETECT_AML_SIGNALS, SP_RUN_DATA_QUALITY_CHECKS, SP_EXPORT_REPORT_TO_DRIVE, SP_APPROVE_POLICY_DOCUMENT", True),
        ("PDF Report Generation", "SP_EXPORT_REPORT_TO_DRIVE with fpdf2 gradient headers and formatted tables", True),
        ("Streamlit App Deployed", "RiskLens AI — enterprise AML investigation command center", True),
    ]
    for label, detail, passed in checks:
        icon_cls = "check-pass" if passed else "check-fail"
        icon = "&#10003;" if passed else "&#10007;"
        st.markdown(f"<div class='coco-check'><span class='check-icon {icon_cls}'>{icon}</span><span><strong>{label}</strong><br><span style='font-size:0.7rem;color:#64748B;'>{detail}</span></span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Multi-agent orchestration
    st.markdown("<div class='card'><div class='card-header'>Multi-Agent Orchestration <span class='card-sub'>Signal-to-Report investigation workflow</span></div>", unsafe_allow_html=True)
    st.markdown("""<div style='text-align:center;padding:0.6rem 0;'>
        <span class='wf-step wf-done'>Detection Agent<br><span style='font-size:0.6rem;'>SP_DETECT_AML_SIGNALS</span></span>
        <span class='wf-arrow'>&rarr;</span>
        <span class='wf-step wf-done'>Investigation Agent<br><span style='font-size:0.6rem;'>risk_analytics tool</span></span>
        <span class='wf-arrow'>&rarr;</span>
        <span class='wf-step wf-done'>Policy Agent<br><span style='font-size:0.6rem;'>policy_search tool</span></span>
        <span class='wf-arrow'>&rarr;</span>
        <span class='wf-step wf-done'>Compliance Agent<br><span style='font-size:0.6rem;'>Evidence validation</span></span>
        <span class='wf-arrow'>&rarr;</span>
        <span class='wf-step wf-done'>Reporting Agent<br><span style='font-size:0.6rem;'>SAR/PDF generation</span></span>
    </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Pipeline Health + Document Governance + Audit in sub-tabs
    ops_tab1, ops_tab2, ops_tab3 = st.tabs(["Pipeline Health", "Document Governance", "Audit Log"])

    with ops_tab1:
        runs_df = get_pipeline_runs()
        if len(runs_df) > 0:
            total_runs = len(runs_df); completed = len(runs_df[runs_df["STATUS"]=="COMPLETED"])
            success_rate = (completed/total_runs*100) if total_runs>0 else 0
            total_sigs = int(runs_df["SIGNALS_GENERATED"].sum()) if "SIGNALS_GENERATED" in runs_df.columns else 0
            om1, om2, om3, om4 = st.columns(4)
            with om1: st.metric("Total Runs", total_runs)
            with om2: st.metric("Success Rate", f"{success_rate:.0f}%")
            with om3: st.metric("Signals Generated", total_sigs)
            with om4:
                avg_dur = float(runs_df["DURATION_SECONDS"].mean()) if "DURATION_SECONDS" in runs_df.columns else 0
                st.metric("Avg Duration", f"{avg_dur:.1f}s")
            if "RUN_TIMESTAMP" in runs_df.columns:
                fig = go.Figure()
                fig.add_bar(x=runs_df["RUN_TIMESTAMP"], y=runs_df["RECORDS_PROCESSED"], name="Records", marker_color="#3498DB")
                if "SIGNALS_GENERATED" in runs_df.columns:
                    fig.add_scatter(x=runs_df["RUN_TIMESTAMP"], y=runs_df["SIGNALS_GENERATED"], mode="lines+markers", name="Signals", yaxis="y2", line=dict(color="#E74C3C"))
                plotly_theme(fig, 280)
                fig.update_layout(yaxis=dict(title="Records"), yaxis2=dict(title="Signals",overlaying="y",side="right"), legend=dict(orientation="h",y=-0.15))
                st.plotly_chart(fig, use_container_width=True)
            st.dataframe(runs_df, use_container_width=True)

    with ops_tab2:
        docs = get_pending_documents()
        if len(docs) > 0:
            pending_docs = docs[docs["STATUS"] == "PENDING_APPROVAL"]
            if len(pending_docs) > 0:
                st.warning(f"{len(pending_docs)} document(s) pending approval")
                for idx, row in pending_docs.iterrows():
                    doc_id = row["DOC_ID"]; title = row.get("DOC_TITLE", doc_id)
                    col_info, col_actions = st.columns([3,2])
                    with col_info:
                        st.markdown(f"**{title}**")
                        st.caption(f"ID: {doc_id}  |  Category: {row.get('DOC_TYPE','N/A')}  |  By: {row.get('UPLOADED_BY','')}")
                    with col_actions:
                        notes = st.text_input("Notes", key=f"notes_{doc_id}", placeholder="Review notes...")
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("Approve", key=f"approve_{doc_id}", use_container_width=True):
                                try:
                                    session.sql(f"CALL AML_COPILOT.PIPELINE.SP_APPROVE_POLICY_DOCUMENT('{doc_id}', 'APPROVE', 'SAMEEHA', '{notes.replace(chr(39), chr(39)+chr(39))}')").collect()
                                    st.success(f"Approved: {title}")
                                    if _rerun: _rerun()
                                except Exception as e: st.error(f"Failed: {e}")
                        with b2:
                            if st.button("Reject", key=f"reject_{doc_id}", use_container_width=True):
                                try:
                                    session.sql(f"CALL AML_COPILOT.PIPELINE.SP_APPROVE_POLICY_DOCUMENT('{doc_id}', 'REJECT', 'SAMEEHA', '{notes.replace(chr(39), chr(39)+chr(39))}')").collect()
                                    st.warning(f"Rejected: {title}")
                                    if _rerun: _rerun()
                                except Exception as e: st.error(f"Failed: {e}")
            else: st.success("No documents pending approval.")
            st.markdown("---")
            st.dataframe(docs, use_container_width=True)

    with ops_tab3:
        audit_df = get_audit_log()
        if len(audit_df) > 0: st.dataframe(audit_df, use_container_width=True)
        else: st.info("No audit log entries.")


# ============================================================
# FOOTER
# ============================================================
st.markdown("""<div class='footer'>
    RiskLens AI &mdash; AML Investigation Copilot &bull; Powered by Snowflake Cortex Agent, Cortex Search, Dynamic Tables &bull;
    Built with CoCo &bull; All data is synthetic for demonstration
</div>""", unsafe_allow_html=True)
