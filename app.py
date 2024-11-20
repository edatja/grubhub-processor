import streamlit as st
import pandas as pd
from datetime import datetime
import re

def parse_amount(text):
    """Extract amount from text, handling both positive and negative (parentheses) numbers"""
    if '(' in text and ')' in text:
        # Handle negative numbers in parentheses
        amount = float(re.search(r'\(([\d.]+)\)', text).group(1)) * -1
    else:
        # Handle positive numbers
        amount = float(re.search(r'([\d.]+)', text).group(1))
    return amount

def parse_line_items(text):
    """Parse individual line items for fees and taxes"""
    items = {}
    for line in text.split('\n'):
        if 'Marketing' in line and '$' in line:
            items['marketing'] = abs(parse_amount(line))
        elif 'Deliveries by Grubhub' in line and '$' in line:
            items['delivery'] = abs(parse_amount(line))
        elif 'Processing' in line and '$' in line:
            items['processing'] = abs(parse_amount(line))
        elif 'sales tax' in line.lower() and '$' in line and 'Withheld' not in line:
            items['tax'] = abs(parse_amount(line))
    return items

def process_statement(text):
    deposits = []
    
    # Split into sections by "Total collected"
    sections = text.split('Total collected')
    
    for section in sections[1:]:
        try:
            # Get date
            date_match = re.search(r'Deposit (\d{1,2}/\d{1,2}/\d{4})', section)
            if not date_match:
                continue
            date = datetime.strptime(date_match.group(1), '%m/%d/%Y')
            
            # Get distribution ID
            dist_id = re.search(r'(\d{8}JV-UBOK)', section).group(1)
            
            # Get order period
            period = re.search(r'Orders (\d{1,2}/\d{1,2} to \d{1,2}/\d{1,2})', section).group(1)
            
            # Parse line items
            items = parse_line_items(section)
            
            # Get total collected amount
            total_match = re.search(r'\$([\d.]+)', section)
            total = float(total_match.group(1)) if total_match else 0
            
            # Get net deposit
            net_match = re.search(r'Pay me\s+now fee\s+\$([\d.]+)', section)
            net = float(net_match.group(1)) if net_match else 0
            
            # Calculate total fees
            fees = sum([
                items.get('marketing', 0),
                items.get('delivery', 0),
                items.get('processing', 0)
            ])
            
            deposits.append({
                'date': date,
                'distribution_id': dist_id,
                'order_period': period,
                'subtotal': total,
                'fees': fees,
                'tax': items.get('tax', 0),
                'net_deposit': net
            })
            
        except Exception as e:
            st.error(f"Error processing section: {str(e)}")
            
    return deposits

def main():
    st.title('🧾 Food Delivery Statement Processor')
    
    statement_text = st.text_area("Paste your GrubHub statement here:", height=300)
    
    if st.button('Process Statement'):
        if statement_text:
            deposits = process_statement(statement_text)
            
            if deposits:
                totals = {
                    'sales': sum(d['subtotal'] for d in deposits),
                    'fees': sum(d['fees'] for d in deposits),
                    'tax': sum(d['tax'] for d in deposits),
                    'net': sum(d['net_deposit'] for d in deposits)
                }
                
                cols = st.columns(4)
                cols[0].metric("Total Sales", f"${totals['sales']:.2f}")
                cols[1].metric("Total Fees", f"${totals['fees']:.2f}")
                cols[2].metric("Total Tax", f"${totals['tax']:.2f}")
                cols[3].metric("Net Deposits", f"${totals['net']:.2f}")
                
                st.write("### Journal Entries")
                for deposit in deposits:
                    with st.expander(f"Entry for {deposit['date'].strftime('%m/%d/%Y')}"):
                        st.write(f"Date: {deposit['date'].strftime('%m/%d/%Y')}")
                        st.write(f"Net Amount: ${deposit['net_deposit']:.2f}")
                        st.write(f"Fees: ${deposit['fees']:.2f}")
                        st.write(f"Sales: ${deposit['subtotal']:.2f}")
                        st.write(f"Tax: ${deposit['tax']:.2f}")

if __name__ == "__main__":
    main()
