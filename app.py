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
    
    def parse_grubhub_statement(self, text):
    """Parse GrubHub statement into individual deposits"""
    deposits = []
    try:
        # Find all deposit sections
        deposit_sections = re.finditer(
            r'Deposit (\d{1,2}/\d{1,2}/\d{4})\s+.*?Orders (\d{1,2}/\d{1,2}) to (\d{1,2}/\d{1,2})', 
            text, 
            re.DOTALL
        )

        for section in deposit_sections:
            # Basic deposit info
            date = datetime.strptime(section.group(1), '%m/%d/%Y')
            order_period = f"{section.group(2)} to {section.group(3)}"
            
            # Get section text
            section_end = text.find('Deposit', section.end())
            if section_end == -1:
                section_end = len(text)
            section_text = text[section.start():section_end]

            # Find distribution ID
            dist_id_match = re.search(r'(\d{8}JV-UBOK)', section_text)
            distribution_id = dist_id_match.group(1) if dist_id_match else ''

            # Initialize variables
            subtotal = 0
            tax = 0
            fees = 0
            net_deposit = 0

            # Parse the Total collected line
            total_collected_match = re.search(r'Total collected\s+\$(\d+\.\d+)', section_text)
            if total_collected_match:
                subtotal = float(total_collected_match.group(1))

            # Find tax amounts - look for specific tax references
            tax_matches = re.finditer(r'Sales tax\s+\$(\d+\.\d+)|tax\s+\$(\d+\.\d+)', section_text, re.IGNORECASE)
            for tax_match in tax_matches:
                tax_amount = tax_match.group(1) or tax_match.group(2)
                tax += float(tax_amount)

            # Find fees - look for all amounts in parentheses
            fee_matches = re.finditer(r'\((\d+\.\d+)\)', section_text)
            for fee_match in fee_matches:
                fees += float(fee_match.group(1))

            # Extract net deposit amount (the final amount in the section)
            net_matches = re.finditer(r'\$(\d+\.\d+)', section_text)
            net_amounts = [float(match.group(1)) for match in net_matches]
            if net_amounts:
                net_deposit = net_amounts[-1]  # Take the last dollar amount in the section

            # Add deposit details
            deposit = {
                'date': date,
                'distribution_id': distribution_id,
                'order_period': order_period,
                'subtotal': subtotal,
                'tax': tax,
                'fees': fees,
                'net_deposit': net_deposit
            }

            # Debug information
            st.write(f"Debug - Processing deposit for {date}:")
            st.write(f"Subtotal: ${subtotal:.2f}")
            st.write(f"Tax: ${tax:.2f}")
            st.write(f"Fees: ${fees:.2f}")
            st.write(f"Net Deposit: ${net_deposit:.2f}")

            deposits.append(deposit)

    except Exception as e:
        st.error(f"Error parsing statement: {str(e)}")
        return []

    return deposits

    def create_journal_entries(self, deposits):
    """Convert deposits into QuickBooks journal entry format"""
    journal_entries = []
    
    for deposit in deposits:
        entry = {
            'date': deposit['date'].strftime('%m/%d/%Y'),
            'memo': f'GrubHub Deposit {deposit["distribution_id"]} - Orders {deposit["order_period"]}',
            'lines': [
                {
                    'account': self.accounts['bank'],
                    'debit': deposit['net_deposit'],
                    'credit': 0,
                    'description': 'Net GrubHub Deposit'
                },
                {
                    'account': self.accounts['fees'],
                    'debit': deposit['fees'],
                    'credit': 0,
                    'description': 'GrubHub Fees'
                },
                {
                    'account': self.accounts['sales'],
                    'debit': 0,
                    'credit': deposit['subtotal'],
                    'description': 'Food Sales'
                },
                {
                    'account': self.accounts['tax'],
                    'debit': 0,
                    'credit': deposit['tax'],
                    'description': 'Sales Tax Collected'
                }
            ]
        }
        
        # Verify entry balances
        total_debits = sum(line['debit'] for line in entry['lines'])
        total_credits = sum(line['credit'] for line in entry['lines'])
        st.write(f"Debug - Journal Entry for {entry['date']}:")
        st.write(f"Total Debits: ${total_debits:.2f}")
        st.write(f"Total Credits: ${total_credits:.2f}")
        
        journal_entries.append(entry)
    
    return journal_entries

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
                    
                    # Display entries
                    st.success(f"Found {len(deposits)} deposits!")
                    
                    # Show summary
                    total_sales = sum(d['subtotal'] for d in deposits)
                    total_fees = sum(d['fees'] for d in deposits)
                    total_tax = sum(d['tax'] for d in deposits)
                    total_deposits = sum(d['net_deposit'] for d in deposits)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Sales", f"${total_sales:.2f}")
                    with col2:
                        st.metric("Total Fees", f"${total_fees:.2f}")
                    with col3:
                        st.metric("Total Tax", f"${total_tax:.2f}")
                    with col4:
                        st.metric("Net Deposits", f"${total_deposits:.2f}")
                    
                    # Display journal entries
                    st.markdown("### Journal Entries Preview")
                    for entry in entries:
                        with st.expander(f"Entry for {entry['date']} - ${entry['lines'][0]['debit']:.2f}"):
                            st.write("Date:", entry['date'])
                            st.write("Memo:", entry['memo'])
                            st.markdown("```")
                            for line in entry['lines']:
                                if line['debit'] > 0:
                                    st.write(f"{line['account']} {' ' * (25-len(line['account']))} {line['debit']:.2f}")
                                else:
                                    st.write(f"{line['account']} {' ' * (25-len(line['account']))} {' ' * 12} {line['credit']:.2f}")
                            st.markdown("```")
                    
                    # Create CSV file
                    csv_data = []
                    for entry in entries:
                        for line in entry['lines']:
                            csv_data.append({
                                'Date': entry['date'],
                                'Journal No.': '',
                                'Memo': entry['memo'],
                                'Account': line['account'],
                                'Debit': f"{line['debit']:.2f}" if line['debit'] > 0 else '',
                                'Credit': f"{line['credit']:.2f}" if line['credit'] > 0 else '',
                                'Description': line['description']
                            })
                    
                    df = pd.DataFrame(csv_data)
                    csv = df.to_csv(index=False)
                    
                    st.download_button(
                        label="📥 Download QuickBooks CSV",
                        data=csv,
                        file_name="grubhub_journal_entries.csv",
                        mime="text/csv",
                    )
                else:
                    st.warning("No deposits found in the statement. Please check the statement format.")
            else:
                st.warning("Please paste a GrubHub statement first.")

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
