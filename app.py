import streamlit as st
import pandas as pd
from datetime import datetime
import re

st.set_page_config(page_title="Food Delivery Statement Processor", page_icon="🧾", layout="wide")

class DeliveryServiceProcessor:
    def __init__(self):
        self.accounts = {
            'sales': '44030',                # Grubhub Sales
            'fees': '60260',                 # Grubhub Fees
            'tax': 'Sales Tax Payable',      # Sales Tax Payable
            'bank': 'Checking - 5734 - 1'    # Bank Account
        }

    def extract_amount(self, text, pattern):
        """Helper function to extract dollar amounts"""
        match = re.search(pattern, text)
        if match:
            # Remove $ and parentheses, convert to float
            amount = match.group(1).replace('$', '').replace('(', '').replace(')', '')
            return float(amount)
        return 0.0

    def extract_fees(self, section):
        """Extract all types of GrubHub fees"""
        fees = 0.0
        
        # Define fee patterns
        fee_patterns = [
            r'Marketing\s+\$\((\d+\.\d+)\)',
            r'Delivery by Grubhub\s+\$\((\d+\.\d+)\)',
            r'Processing\s+\$\((\d+\.\d+)\)',
            r'Commission\s+\$\((\d+\.\d+)\)',  # Added in case they use this term
            r'Service Fee\s+\$\((\d+\.\d+)\)'  # Added in case they use this term
        ]
        
        for pattern in fee_patterns:
            matches = re.finditer(pattern, section, re.IGNORECASE)
            for match in matches:
                fees += float(match.group(1))
        
        return fees

    def extract_tax(self, section):
        """Extract different types of tax amounts"""
        collected_tax = 0.0
        withheld_tax = 0.0
        
        # Pattern for collected sales tax
        collected_matches = re.finditer(r'Sales Tax\s+\$(\d+\.\d+)(?!\s*\()', section, re.IGNORECASE)
        collected_tax = sum(float(match.group(1)) for match in collected_matches)
        
        # Pattern for withheld sales tax
        withheld_matches = re.finditer(r'Withheld Sales Tax\s+\$\((\d+\.\d+)\)', section, re.IGNORECASE)
        withheld_tax = sum(float(match.group(1)) for match in withheld_matches)
        
        return collected_tax, withheld_tax

    def parse_grubhub_statement(self, text):
        deposits = []
        
        # Find deposit sections
        sections = text.split('Distribution ID')
        for section in sections[1:]:  # Skip header section
            try:
                # Extract deposit date
                date_match = re.search(r'Deposit (\d{1,2}/\d{1,2}/\d{4})', section)
                if not date_match:
                    continue
                date = datetime.strptime(date_match.group(1), '%m/%d/%Y')

                # Extract distribution ID
                dist_id_match = re.search(r'(\d{8}JV-UBOK)', section)
                distribution_id = dist_id_match.group(1) if dist_id_match else ''

                # Extract order period
                period_match = re.search(r'Orders (\d{1,2}/\d{1,2}) to (\d{1,2}/\d{1,2})', section)
                order_period = f"{period_match.group(1)} to {period_match.group(2)}" if period_match else ""

                # Find the Total collected line
                total_match = re.search(r'Total collected\s+\$(\d+\.\d+)', section)
                subtotal = float(total_match.group(1)) if total_match else 0

                # Extract fees using the new method
                fees = self.extract_fees(section)

                # Extract tax using the new method
                collected_tax, withheld_tax = self.extract_tax(section)
                total_tax = collected_tax  # We'll use collected tax for journal entries

                # Extract net deposit (last amount in section)
                amount_matches = list(re.finditer(r'\$(\d+\.\d+)(?!\s*\()', section))
                if amount_matches:
                    net_deposit = float(amount_matches[-1].group(1))
                else:
                    net_deposit = subtotal - fees - total_tax - withheld_tax

                # Debug information
                st.write(f"""
                Debug information for deposit {date}:
                - Distribution ID: {distribution_id}
                - Period: {order_period}
                - Subtotal: ${subtotal:.2f}
                - Fees: ${fees:.2f}
                - Collected Tax: ${collected_tax:.2f}
                - Withheld Tax: ${withheld_tax:.2f}
                - Net Deposit: ${net_deposit:.2f}
                """)

                deposits.append({
                    'date': date,
                    'distribution_id': distribution_id,
                    'order_period': order_period,
                    'subtotal': subtotal,
                    'tax': total_tax,
                    'fees': fees,
                    'withheld_tax': withheld_tax,
                    'net_deposit': net_deposit
                })

            except Exception as e:
                st.error(f"Error processing section: {str(e)}")
                continue

        return deposits

    def create_journal_entries(self, deposits):
        journal_entries = []
        
        for deposit in deposits:
            # Create the journal entry
            entry = {
                'date': deposit['date'].strftime('%m/%d/%Y'),
                'memo': f'GrubHub Deposit {deposit["distribution_id"]} - Orders {deposit["order_period"]}',
                'lines': [
                    {
                        'account': self.accounts['bank'],
                        'debit': round(deposit['net_deposit'], 2),
                        'credit': 0,
                        'description': 'Net GrubHub Deposit'
                    },
                    {
                        'account': self.accounts['fees'],
                        'debit': round(deposit['fees'], 2),
                        'credit': 0,
                        'description': 'GrubHub Fees'
                    },
                    {
                        'account': self.accounts['sales'],
                        'debit': 0,
                        'credit': round(deposit['subtotal'], 2),
                        'description': 'Food Sales'
                    },
                    {
                        'account': self.accounts['tax'],
                        'debit': 0,
                        'credit': round(deposit['tax'], 2),
                        'description': 'Sales Tax Collected'
                    }
                ]
            }

            # Debug information for journal entry
            st.write(f"""
            Debug - Journal Entry for {entry['date']}:
            - Bank Debit: ${entry['lines'][0]['debit']:.2f}
            - Fees Debit: ${entry['lines'][1]['debit']:.2f}
            - Sales Credit: ${entry['lines'][2]['credit']:.2f}
            - Tax Credit: ${entry['lines'][3]['credit']:.2f}
            """)

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
                    total_withheld_tax = sum(d['withheld_tax'] for d in deposits)
                    total_deposits = sum(d['net_deposit'] for d in deposits)
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("Total Sales", f"${total_sales:.2f}")
                    with col2:
                        st.metric("Total Fees", f"${total_fees:.2f}")
                    with col3:
                        st.metric("Collected Tax", f"${total_tax:.2f}")
                    with col4:
                        st.metric("Withheld Tax", f"${total_withheld_tax:.2f}")
                    with col5:
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
