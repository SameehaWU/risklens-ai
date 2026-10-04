-- ============================================================
-- RiskLens AI - Step 5: Deploy Streamlit App
-- ============================================================

USE DATABASE AML_COPILOT;
USE SCHEMA RAW;
USE WAREHOUSE COMPUTE_WH;

-- Create stage for Streamlit files
CREATE OR REPLACE STAGE STREAMLIT_STAGE;

-- Upload the app file (run from your local machine)
-- PUT 'file:///path/to/streamlit_app.py' @STREAMLIT_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- Create the Streamlit app
CREATE OR REPLACE STREAMLIT RISKLENS_APP
    ROOT_LOCATION = '@AML_COPILOT.RAW.STREAMLIT_STAGE'
    MAIN_FILE = 'streamlit_app.py'
    QUERY_WAREHOUSE = COMPUTE_WH
    COMMENT = 'RiskLens AI - AML Investigation Copilot';

-- Grant access if needed
-- GRANT USAGE ON STREAMLIT RISKLENS_APP TO ROLE <role_name>;
