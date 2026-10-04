-- ============================================================
-- RiskLens AI - Step 2: Synthetic Data Generation
-- NOTE: This generates realistic AML patterns at scale.
-- Run after 01_schema_and_tables.sql
-- ============================================================

USE DATABASE AML_COPILOT;
USE WAREHOUSE COMPUTE_WH;

-- Countries (50 countries with risk tiers)
INSERT INTO RAW.COUNTRIES (COUNTRY_CODE, COUNTRY_NAME, REGION, RISK_TIER, FATF_LISTED)
SELECT C.* FROM (
    SELECT 'USA' AS COUNTRY_CODE, 'United States' AS COUNTRY_NAME, 'North America' AS REGION, 'LOW' AS RISK_TIER, FALSE AS FATF_LISTED UNION ALL
    SELECT 'GBR', 'United Kingdom', 'Europe', 'LOW', FALSE UNION ALL
    SELECT 'DEU', 'Germany', 'Europe', 'LOW', FALSE UNION ALL
    SELECT 'FRA', 'France', 'Europe', 'LOW', FALSE UNION ALL
    SELECT 'CAN', 'Canada', 'North America', 'LOW', FALSE UNION ALL
    SELECT 'AUS', 'Australia', 'Asia Pacific', 'LOW', FALSE UNION ALL
    SELECT 'JPN', 'Japan', 'Asia Pacific', 'LOW', FALSE UNION ALL
    SELECT 'SGP', 'Singapore', 'Asia Pacific', 'LOW', FALSE UNION ALL
    SELECT 'CHE', 'Switzerland', 'Europe', 'LOW', FALSE UNION ALL
    SELECT 'NLD', 'Netherlands', 'Europe', 'LOW', FALSE UNION ALL
    SELECT 'BRA', 'Brazil', 'South America', 'MEDIUM', FALSE UNION ALL
    SELECT 'MEX', 'Mexico', 'North America', 'MEDIUM', FALSE UNION ALL
    SELECT 'IND', 'India', 'Asia Pacific', 'MEDIUM', FALSE UNION ALL
    SELECT 'CHN', 'China', 'Asia Pacific', 'MEDIUM', FALSE UNION ALL
    SELECT 'RUS', 'Russia', 'Europe', 'HIGH', TRUE UNION ALL
    SELECT 'ARE', 'United Arab Emirates', 'Middle East', 'MEDIUM', FALSE UNION ALL
    SELECT 'SAU', 'Saudi Arabia', 'Middle East', 'MEDIUM', FALSE UNION ALL
    SELECT 'TUR', 'Turkey', 'Europe', 'MEDIUM', FALSE UNION ALL
    SELECT 'ZAF', 'South Africa', 'Africa', 'MEDIUM', FALSE UNION ALL
    SELECT 'NGA', 'Nigeria', 'Africa', 'HIGH', TRUE UNION ALL
    SELECT 'KEN', 'Kenya', 'Africa', 'MEDIUM', FALSE UNION ALL
    SELECT 'PAK', 'Pakistan', 'Asia Pacific', 'HIGH', TRUE UNION ALL
    SELECT 'AFG', 'Afghanistan', 'Asia Pacific', 'VERY_HIGH', TRUE UNION ALL
    SELECT 'IRN', 'Iran', 'Middle East', 'VERY_HIGH', TRUE UNION ALL
    SELECT 'PRK', 'North Korea', 'Asia Pacific', 'VERY_HIGH', TRUE UNION ALL
    SELECT 'MMR', 'Myanmar', 'Asia Pacific', 'HIGH', TRUE UNION ALL
    SELECT 'SYR', 'Syria', 'Middle East', 'VERY_HIGH', TRUE UNION ALL
    SELECT 'LBY', 'Libya', 'Africa', 'HIGH', TRUE UNION ALL
    SELECT 'YEM', 'Yemen', 'Middle East', 'VERY_HIGH', TRUE UNION ALL
    SELECT 'SOM', 'Somalia', 'Africa', 'VERY_HIGH', TRUE UNION ALL
    SELECT 'PAN', 'Panama', 'Central America', 'HIGH', FALSE UNION ALL
    SELECT 'CYM', 'Cayman Islands', 'Caribbean', 'HIGH', FALSE UNION ALL
    SELECT 'VGB', 'British Virgin Islands', 'Caribbean', 'HIGH', FALSE UNION ALL
    SELECT 'HKG', 'Hong Kong', 'Asia Pacific', 'MEDIUM', FALSE UNION ALL
    SELECT 'KOR', 'South Korea', 'Asia Pacific', 'LOW', FALSE UNION ALL
    SELECT 'ITA', 'Italy', 'Europe', 'LOW', FALSE UNION ALL
    SELECT 'ESP', 'Spain', 'Europe', 'LOW', FALSE UNION ALL
    SELECT 'POL', 'Poland', 'Europe', 'LOW', FALSE UNION ALL
    SELECT 'SWE', 'Sweden', 'Europe', 'LOW', FALSE UNION ALL
    SELECT 'NOR', 'Norway', 'Europe', 'LOW', FALSE UNION ALL
    SELECT 'COL', 'Colombia', 'South America', 'HIGH', FALSE UNION ALL
    SELECT 'VEN', 'Venezuela', 'South America', 'HIGH', TRUE UNION ALL
    SELECT 'ARG', 'Argentina', 'South America', 'MEDIUM', FALSE UNION ALL
    SELECT 'CHL', 'Chile', 'South America', 'LOW', FALSE UNION ALL
    SELECT 'PER', 'Peru', 'South America', 'MEDIUM', FALSE UNION ALL
    SELECT 'EGY', 'Egypt', 'Africa', 'MEDIUM', FALSE UNION ALL
    SELECT 'ISR', 'Israel', 'Middle East', 'MEDIUM', FALSE UNION ALL
    SELECT 'THA', 'Thailand', 'Asia Pacific', 'MEDIUM', FALSE UNION ALL
    SELECT 'IDN', 'Indonesia', 'Asia Pacific', 'MEDIUM', FALSE UNION ALL
    SELECT 'MYS', 'Malaysia', 'Asia Pacific', 'MEDIUM', FALSE
) C;

-- Customers (10,000)
-- NOTE: This is a representative excerpt. The full generation uses a GENERATOR(ROWCOUNT => 10000)
-- with randomized names, types, countries, risk ratings, PEP/sanctions flags.
-- For the actual deployment, run:
INSERT INTO RAW.CUSTOMERS
SELECT
    'CUST_' || LPAD(SEQ4(), 8, '0'),
    CASE MOD(SEQ4(), 20) WHEN 0 THEN 'James' WHEN 1 THEN 'Maria' WHEN 2 THEN 'Robert' WHEN 3 THEN 'Sarah'
        WHEN 4 THEN 'William' WHEN 5 THEN 'Jennifer' WHEN 6 THEN 'Michael' WHEN 7 THEN 'Linda'
        WHEN 8 THEN 'David' WHEN 9 THEN 'Elizabeth' WHEN 10 THEN 'Richard' WHEN 11 THEN 'Susan'
        WHEN 12 THEN 'Joseph' WHEN 13 THEN 'Karen' WHEN 14 THEN 'Thomas' WHEN 15 THEN 'Nancy'
        WHEN 16 THEN 'Charles' WHEN 17 THEN 'Lisa' WHEN 18 THEN 'Daniel' ELSE 'Patricia' END,
    CASE MOD(SEQ4(), 25) WHEN 0 THEN 'Smith' WHEN 1 THEN 'Johnson' WHEN 2 THEN 'Williams' WHEN 3 THEN 'Brown'
        WHEN 4 THEN 'Jones' WHEN 5 THEN 'Garcia' WHEN 6 THEN 'Miller' WHEN 7 THEN 'Davis'
        WHEN 8 THEN 'Rodriguez' WHEN 9 THEN 'Martinez' WHEN 10 THEN 'Hernandez' WHEN 11 THEN 'Lopez'
        WHEN 12 THEN 'Gonzalez' WHEN 13 THEN 'Wilson' WHEN 14 THEN 'Anderson' WHEN 15 THEN 'Thomas'
        WHEN 16 THEN 'Taylor' WHEN 17 THEN 'Moore' WHEN 18 THEN 'Jackson' WHEN 19 THEN 'Martin'
        WHEN 20 THEN 'Lee' WHEN 21 THEN 'Thompson' WHEN 22 THEN 'White' WHEN 23 THEN 'Harris'
        ELSE 'Clark' END,
    CASE MOD(SEQ4(), 10) WHEN 0 THEN 'CORPORATE' WHEN 1 THEN 'TRUST' ELSE 'INDIVIDUAL' END,
    (SELECT COUNTRY_CODE FROM RAW.COUNTRIES ORDER BY RANDOM() LIMIT 1),
    CASE MOD(SEQ4(), 15) WHEN 0 THEN 'New York' WHEN 1 THEN 'London' WHEN 2 THEN 'Dubai' WHEN 3 THEN 'Singapore'
        WHEN 4 THEN 'Tokyo' WHEN 5 THEN 'Sydney' WHEN 6 THEN 'Frankfurt' WHEN 7 THEN 'Toronto'
        WHEN 8 THEN 'Mumbai' WHEN 9 THEN 'Sao Paulo' WHEN 10 THEN 'Hong Kong' WHEN 11 THEN 'Zurich'
        WHEN 12 THEN 'Paris' WHEN 13 THEN 'Lagos' ELSE 'Mexico City' END,
    CASE WHEN RANDOM() > 0.85 THEN 'HIGH' WHEN RANDOM() > 0.5 THEN 'MEDIUM' ELSE 'LOW' END,
    RANDOM() > 0.97,
    RANDOM() > 0.99,
    CASE MOD(SEQ4(), 12) WHEN 0 THEN 'Banking' WHEN 1 THEN 'Real Estate' WHEN 2 THEN 'Import/Export'
        WHEN 3 THEN 'Technology' WHEN 4 THEN 'Healthcare' WHEN 5 THEN 'Retail'
        WHEN 6 THEN 'Construction' WHEN 7 THEN 'Legal Services' WHEN 8 THEN 'Consulting'
        WHEN 9 THEN 'Manufacturing' WHEN 10 THEN 'Energy' ELSE 'Entertainment' END,
    ROUND(UNIFORM(15000, 500000, RANDOM()), 2),
    DATEADD('DAY', -UNIFORM(30, 1800, RANDOM()), CURRENT_DATE()),
    CASE WHEN RANDOM() > 0.1 THEN 'CURRENT' ELSE 'EXPIRED' END,
    CURRENT_TIMESTAMP()
FROM TABLE(GENERATOR(ROWCOUNT => 10000));

-- Transactions (500,000) - NOTE: Full generation below. Runs ~30 seconds on X-Small.
INSERT INTO RAW.TRANSACTIONS
SELECT
    'TXN_' || LPAD(SEQ4(), 10, '0'),
    'CUST_' || LPAD(UNIFORM(0, 9999, RANDOM()), 8, '0'),
    'ACCT_' || LPAD(UNIFORM(0, 14999, RANDOM()), 8, '0'),
    ROUND(CASE
        WHEN RANDOM() > 0.99 THEN UNIFORM(50000, 500000, RANDOM())
        WHEN RANDOM() > 0.95 THEN UNIFORM(8000, 50000, RANDOM())
        WHEN RANDOM() > 0.7 THEN UNIFORM(1000, 10000, RANDOM())
        ELSE UNIFORM(10, 2000, RANDOM())
    END, 2),
    CASE MOD(SEQ4(), 5) WHEN 0 THEN 'WIRE' WHEN 1 THEN 'ACH' WHEN 2 THEN 'CASH' WHEN 3 THEN 'CARD' ELSE 'INTERNAL' END,
    CASE MOD(SEQ4(), 4) WHEN 0 THEN 'ONLINE' WHEN 1 THEN 'MOBILE' WHEN 2 THEN 'BRANCH' ELSE 'ATM' END,
    CASE WHEN RANDOM() > 0.5 THEN 'INBOUND' ELSE 'OUTBOUND' END,
    (SELECT COUNTRY_CODE FROM RAW.COUNTRIES ORDER BY RANDOM() LIMIT 1),
    (SELECT COUNTRY_CODE FROM RAW.COUNTRIES ORDER BY RANDOM() LIMIT 1),
    CASE WHEN RANDOM() > 0.6 THEN 'BEN_' || LPAD(UNIFORM(0, 8125, RANDOM()), 6, '0') ELSE NULL END,
    RANDOM() > 0.97,
    DATEADD('SECOND', -UNIFORM(0, 15552000, RANDOM()), CURRENT_TIMESTAMP()),
    'Transaction ' || SEQ4(),
    'REF' || LPAD(SEQ4(), 10, '0'),
    CURRENT_TIMESTAMP()
FROM TABLE(GENERATOR(ROWCOUNT => 500000));

-- Bank Accounts (15,000)
INSERT INTO RAW.BANK_ACCOUNTS
SELECT
    'ACCT_' || LPAD(SEQ4(), 8, '0'),
    'CUST_' || LPAD(MOD(SEQ4(), 10000), 8, '0'),
    CASE MOD(SEQ4(), 4) WHEN 0 THEN 'CHECKING' WHEN 1 THEN 'SAVINGS' WHEN 2 THEN 'CREDIT' ELSE 'LOAN' END,
    CASE WHEN RANDOM() > 0.05 THEN 'ACTIVE' WHEN RANDOM() > 0.5 THEN 'DORMANT' ELSE 'CLOSED' END,
    ROUND(UNIFORM(100, 500000, RANDOM()), 2),
    DATEADD('DAY', -UNIFORM(30, 2000, RANDOM()), CURRENT_DATE()),
    CURRENT_TIMESTAMP()
FROM TABLE(GENERATOR(ROWCOUNT => 15000));

-- Beneficiaries (8,126)
INSERT INTO RAW.BENEFICIARIES
SELECT
    'BEN_' || LPAD(SEQ4(), 6, '0'),
    CASE MOD(SEQ4(), 10) WHEN 0 THEN 'Global Trading Co' WHEN 1 THEN 'Apex Holdings' WHEN 2 THEN 'Maritime Services'
        WHEN 3 THEN 'Pacific Imports' WHEN 4 THEN 'Euro Finance Ltd' WHEN 5 THEN 'Gulf Trading'
        WHEN 6 THEN 'Atlas Logistics' WHEN 7 THEN 'Crown Financial' WHEN 8 THEN 'Diamond Corp' ELSE 'Phoenix Intl' END
        || ' ' || SEQ4(),
    CASE MOD(SEQ4(), 4) WHEN 0 THEN 'INDIVIDUAL' WHEN 1 THEN 'CORPORATE' WHEN 2 THEN 'TRUST' ELSE 'FINANCIAL_INSTITUTION' END,
    (SELECT COUNTRY_CODE FROM RAW.COUNTRIES ORDER BY RANDOM() LIMIT 1),
    CASE MOD(SEQ4(), 8) WHEN 0 THEN 'HSBC' WHEN 1 THEN 'Deutsche Bank' WHEN 2 THEN 'Barclays'
        WHEN 3 THEN 'Standard Chartered' WHEN 4 THEN 'Citibank' WHEN 5 THEN 'JPMorgan'
        WHEN 6 THEN 'UBS' ELSE 'BNP Paribas' END,
    ROUND(UNIFORM(0, 100, RANDOM()), 2),
    UNIFORM(1, 500, RANDOM()),
    CURRENT_TIMESTAMP()
FROM TABLE(GENERATOR(ROWCOUNT => 8126));

-- Customer Risk Profiles (10,000)
INSERT INTO RAW.CUSTOMER_RISK_PROFILE
SELECT
    'CUST_' || LPAD(SEQ4(), 8, '0'),
    ROUND(UNIFORM(5, 95, RANDOM()), 2),
    ROUND(UNIFORM(0, 100, RANDOM()), 2),
    ROUND(UNIFORM(0, 100, RANDOM()), 2),
    ROUND(UNIFORM(0, 100, RANDOM()), 2),
    RANDOM() > 0.85,
    DATEADD('DAY', -UNIFORM(0, 365, RANDOM()), CURRENT_DATE()),
    CURRENT_TIMESTAMP()
FROM TABLE(GENERATOR(ROWCOUNT => 10000));

-- Policy Documents (11 approved AML policies)
-- NOTE: These contain realistic policy text for Cortex Search indexing.
-- See full text in the deployed version; abbreviated here for brevity.
INSERT INTO RAW.POLICY_DOCUMENTS (DOC_ID, TITLE, CATEGORY, JURISDICTION, FULL_TEXT, EFFECTIVE_DATE, STATUS, UPLOADED_BY)
VALUES
('POL_001', 'BSA/AML Currency Transaction Reporting', 'BSA_AML', 'United States',
 'CTR POLICY: Financial institutions must file a Currency Transaction Report (CTR) for each transaction in currency of more than $10,000. Multiple transactions that aggregate to more than $10,000 in a single business day must also be reported. Structuring transactions to evade CTR reporting is a federal crime. Institutions must file CTRs within 15 days of the transaction.',
 '2024-01-01', 'APPROVED', 'COMPLIANCE_TEAM'),
('POL_002', 'Suspicious Activity Report Filing Guidelines', 'BSA_AML', 'United States',
 'SAR FILING GUIDELINES: Financial institutions must file a SAR for any transaction of $5,000 or more involving a known suspect, or $25,000 or more regardless of suspect identification. SARs must be filed within 30 calendar days of initial detection. Continuing activity SARs must be filed every 90 days. Supporting documentation must be retained for 5 years.',
 '2024-01-01', 'APPROVED', 'COMPLIANCE_TEAM'),
('POL_003', 'Enhanced Due Diligence Requirements', 'KYC', 'United States',
 'EDD REQUIREMENTS: Enhanced Due Diligence must be performed for high-risk customers, PEPs, correspondent banking relationships, and private banking accounts. EDD includes understanding source of wealth, source of funds, ongoing monitoring, and senior management approval. Reviews must be conducted at least annually.',
 '2024-01-01', 'APPROVED', 'COMPLIANCE_TEAM'),
('POL_004', 'Wire Transfer Monitoring Standards', 'AML', 'International (FATF-aligned)',
 'WIRE TRANSFER MONITORING: All wire transfers must include complete originator and beneficiary information. Rapid movement indicators include large inbound wire followed by outbound transfer of 80% or more within 48 hours. Cross-border wires to high-risk jurisdictions require enhanced monitoring. Funds passed through with minimal hold time are suspicious.',
 '2024-01-01', 'APPROVED', 'COMPLIANCE_TEAM'),
('POL_005', 'Sanctions Screening Requirements', 'SANCTIONS_AML', 'United States',
 'SANCTIONS SCREENING: All customers, beneficiaries, and transactions must be screened against OFAC SDN list, EU sanctions, and UN Security Council consolidated list. Screening must occur at onboarding, periodic review, and for every transaction. Positive matches require immediate escalation and potential blocking.',
 '2024-01-01', 'APPROVED', 'COMPLIANCE_TEAM'),
('POL_006', 'KYC/CDD Standards', 'KYC', 'International (FATF-aligned)',
 'KYC/CDD STANDARDS: Customer identification and verification required at onboarding. Ongoing due diligence must include periodic review of customer information, risk reassessment, and transaction monitoring. Beneficial ownership must be identified for legal entities. Risk-based approach determines frequency of reviews.',
 '2024-01-01', 'APPROVED', 'COMPLIANCE_TEAM'),
('POL_007', 'Transaction Monitoring Program', 'AML', 'United States',
 'TRANSACTION MONITORING: Institutions must implement automated transaction monitoring covering all products and services. Alerts must be reviewed within established timeframes. Structuring detection requires monitoring for multiple transactions below reporting thresholds. Velocity monitoring detects unusual transaction frequency.',
 '2024-01-01', 'APPROVED', 'COMPLIANCE_TEAM'),
('POL_008', 'UAE AML/CFT Framework', 'AML', 'United Arab Emirates',
 'UAE AML/CFT: Financial institutions in UAE must file Suspicious Transaction Reports (STRs) to the Financial Intelligence Unit within 2 business days of detection. The framework aligns with FATF 40 Recommendations. Cross-border wire transfers require enhanced due diligence. PEP screening is mandatory.',
 '2024-01-01', 'APPROVED', 'COMPLIANCE_TEAM'),
('POL_009', 'Counter-Terrorist Financing Guidelines', 'CTF', 'International (FATF-aligned)',
 'CTF GUIDELINES: Institutions must screen all customers and transactions against terrorist financing lists. Unusual patterns of small transactions to conflict zones require investigation. Charities and NPOs require enhanced monitoring. Immediate reporting required for suspected terrorist financing.',
 '2024-01-01', 'APPROVED', 'COMPLIANCE_TEAM'),
('POL_010', 'Trade-Based Money Laundering Indicators', 'AML', 'International (FATF-aligned)',
 'TBML INDICATORS: Red flags include over/under-invoicing, multiple invoicing, phantom shipments, misrepresentation of goods. Trade finance transactions with significant price discrepancies or unusual counterparties in high-risk jurisdictions require enhanced review.',
 '2024-01-01', 'APPROVED', 'COMPLIANCE_TEAM'),
('POL_011', 'Correspondent Banking Due Diligence', 'AML', 'International (FATF-aligned)',
 'CORRESPONDENT BANKING: Enhanced due diligence required for all correspondent banking relationships. Must assess the respondent institution AML/CFT controls, reputation, and regulatory history. Shell bank relationships are prohibited. Nested relationships require approval and ongoing monitoring.',
 '2024-01-01', 'APPROVED', 'COMPLIANCE_TEAM');

-- NOTE: AML_SIGNALS, RISK_CASES, CASE_EVIDENCE are populated by the detection pipeline (03_pipeline.sql)
-- Initial seed signals should be generated by running SP_DETECT_AML_SIGNALS after the pipeline is set up.
