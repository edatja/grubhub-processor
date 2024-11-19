import streamlit as st
import pandas as pd
from datetime import datetime
import re

st.set_page_config(page_title="Food Delivery Statement Processor", page_icon="🧾", layout="wide")

# Add custom CSS
st.markdown("""
    <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .main {
            padding: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

class DeliveryServiceProcessor:
    def __init__(self):
        self.accounts = {
            'sales': '44030',                # Grubhub Sales
            'fees': '60260',                 # Grubhub Fees
            'tax': 'Sales Tax Payable',      # Sales Tax Payable
            'bank': 'Checking - 5734 - 1'    # Bank Account
        }

    # Rest of the class implementation remains the same...

def main():
    st.title('🧾 Food Delivery Statement Processor')
    
    st.markdown("""
    ### Convert GrubHub statements into QuickBooks journal entries
    
    **Instructions:**
    1. Paste your GrubHub statement text below
    2. Click 'Process Statement'
    3. Review the entries
    4. Download the CSV file
    """)

    # Create tabs
    tab1, tab2 = st.tabs(["Process Statement", "Account Settings"])

    with tab1:
        statement_text = st.text_area(
            "Paste your GrubHub statement here:",
            height=300,
            help="Copy and paste your entire GrubHub statement, including all deposit details"
        )

        if st.button('Process Statement', type='primary'):
            if statement_text:
                processor = DeliveryServiceProcessor()
                
                # Process statement
                with st.spinner('Processing statement...'):
                    deposits = processor.parse_grubhub_statement(statement_text)
                    
                if deposits:
                    # Create journal entries
                    entries = processor.create_journal_entries(deposits)
                    
                    # Rest of the display logic remains the same...

    with tab2:
        st.markdown("### Current Account Settings")
        st.markdown("""
        The following accounts are used for journal entries:
        - **Sales Account:** 44030 (GrubHub Sales)
        - **Fees Account:** 60260 (GrubHub Fees)
        - **Bank Account:** Checking - 5734 - 1
        - **Tax Account:** Sales Tax Payable
        """)

if __name__ == "__main__":
    main()
