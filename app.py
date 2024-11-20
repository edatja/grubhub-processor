import streamlit as st
import pandas as pd
from datetime import datetime
import re

def parse_deposit_section(text):
    """Parse a single deposit section"""
    try:
        # Get the total collected amount
        total_match = re.search(r'Total collected\s+\$([\d.]+)', text)
        subtotal = float(total_match.group(1)) if total_match else 0
        
        # Get the net deposit (Pay me now fee amount)
        net_match = re.search(r'Pay me\s+now fee\s+\$([\d.]+)', text)
        net_deposit = float(net_match.group(1)) if net_match else 0
        
        # Extract all fees (amounts in parentheses)
        fees = 0
        fee_matches = re.finditer(r'\(\$([\d.]+)\)', text)
        for match in fee_matches:
            fees += float(match.group(1))
        
        # Get date
        date_match = re.search(r'Deposit (\d{1,2}/\d{1,2}/\d{4})', text)
        date = datetime.strptime(date_match.group(1), '%m/%d/%Y') if date_match else None
        
        return {
            'date': date,
            'subtotal': subtotal,
            'fees': fees,
            'net_deposit': net_deposit
        }
    except Exception as e:
        st.error(f"Error parsing section: {str(e)}")
        return None

def process_statement(text):
    # Split into sections by "Distribution ID" or "Deposit"
    sections = re.split(r'(?=Deposit \d{1,2}/\d{1,2}/\d{4})', text)
    
    deposits = []
    for section in sections:
        if 'Total collected' in section:
            result = parse_deposit_section(section)
            if result:
                deposits.append(result)
    
    return deposits

def main():
    st.title('🧾 Food Delivery Statement Processor')
    
    statement_text = st.text_area("Paste your GrubHub statement here:", height=300)
    
    if st.button('Process Statement'):
        if statement_text:
            deposits = process_statement(statement_text)
            
            if deposits:
                # Calculate totals
                total_sales = sum(d['subtotal'] for d in deposits)
                total_fees = sum(d['fees'] for d in deposits)
                total_deposits = sum(d['net_deposit'] for d in deposits)
                
                # Display totals
                cols = st.columns(3)
                cols[0].metric("Total Sales", f"${total_sales:.2f}")
                cols[1].metric("Total Fees", f"${total_fees:.2f}")
                cols[2].metric("Net Deposits", f"${total_deposits:.2f}")
                
                # Display individual entries
                st.write("### Deposits")
                for deposit in deposits:
                    if deposit['date']:
                        date_str = deposit['date'].strftime('%m/%d/%Y')
                    else:
                        date_str = "Unknown Date"
                        
                    with st.expander(f"Deposit for {date_str}"):
                        st.write(f"Sales: ${deposit['subtotal']:.2f}")
                        st.write(f"Fees: ${deposit['fees']:.2f}")
                        st.write(f"Net Deposit: ${deposit['net_deposit']:.2f}")
                
                # Verify the math
                st.write("### Verification")
                expected_net = total_sales - total_fees
                actual_net = total_deposits
                if abs(expected_net - actual_net) < 0.01:
                    st.success("✅ Numbers balance!")
                else:
                    st.warning(f"⚠️ Discrepancy found: Expected ${expected_net:.2f}, Got ${actual_net:.2f}")
                
if __name__ == "__main__":
    main()
