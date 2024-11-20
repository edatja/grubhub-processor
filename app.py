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

    def parse_grubhub_statement(self, text):
        deposits = []
        
        # Split into sections by Distribution ID
        sections = text.split('Distribution ID')
        
        for section in sections[1:]:  # Skip header section
            try:
                # Basic extractions first
                date_match = re.search(r'Deposit (\d{1,2}/\d{1,2}/\d{4})', section)
                if not date_match:
                    continue
                
                date = datetime.strptime(date_match.group(1), '%m/%d/%Y')
                
                # Get Distribution ID
                dist_id_match = re.search(r'(\d{8}JV-UBOK)', section)
                distribution_id = dist_id_match.group(1) if dist_id_match else ''
                
                # Get order period
                period_match = re.search(r'Orders (\d{1,2}/\d{1,2})(?:\sto\s)(\d{1,2}/\d{1,2})', section)
                order_period = f"{period_match.group(1)} to {period_match.group(2)}" if period_match else ""
                
                # Get total collected (subtotal)
                total_match = re.search(r'Total collected\s+\$([\d.]+)', section)
                subtotal = float(total_match.group(1)) if total_match else 0
                
                # Get net deposit
                net_match = re.search(r'Pay me\s+now fee\s+\$([\d.]+)', section)
                net_deposit = float(net_match.group(1)) if net_match else 0
                
                # Calculate total fees - sum all parenthetical amounts after "Total collected" but before "Pay me"
                fees_section = re.search(r'Total collected.*?Pay me', section, re.DOTALL)
                fees = 0
                if fees_section:
                    fee_matches = re.finditer(r'\(([\d.]+)\)', fees_section.group(0))
                    fees = sum(float(m.group(1)) for m in fee_matches)
                
                # Get collected tax
                tax_matches = re.finditer(r'Sales\s+tax\s+\$([\d.]+)(?!\s*\()', section)
                collected_tax = sum(float(match.group(1)) for match in tax_matches)
                
                deposits.append({
                    'date': date,
                    'distribution_id': distribution_id,
                    'order_period': order_period,
                    'subtotal': subtotal,
                    'tax': collected_tax,
                    'fees': fees,
                    'net_deposit': net_deposit
                })
                
            except Exception as e:
                st.error(f"Error processing section: {str(e)}")
                continue
                
        return deposits

    def create_journal_entries(self, deposits):
        journal_entries = []
        
        for deposit in deposits:
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
            st.warning("Please paste a GrubHub statement first.")

if __name__ == "__main__":
    main()
