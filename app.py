import streamlit as st
import pandas as pd
from datetime import datetime
import re

def parse_deposit_section(text):
    """Parse a single deposit section with detailed fee breakdowns"""
    try:
        # Get the total collected amount
        total_match = re.search(r'Total collected\s+\$([\d.]+)', text)
        subtotal = float(total_match.group(1)) if total_match else 0
        
        # Get the net deposit (Pay me now fee amount)
        net_match = re.search(r'Pay me\s+now fee\s+\$([\d.]+)', text)
        net_deposit = float(net_match.group(1)) if net_match else 0
        
        # Initialize fee variables
        marketing_fees = 0
        delivery_fees = 0
        processing_fees = 0
        collected_tax = 0
        withheld_tax = 0
        
        # Find all lines with dollar amounts
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            
            # Look for amounts in parentheses
            if 'Marketing' in line:
                amounts = re.findall(r'\(\$([\d.]+)\)', line)
                marketing_fees += sum(float(amt) for amt in amounts)
                
            elif 'Deliveries by Grubhub' in line:
                amounts = re.findall(r'\(\$([\d.]+)\)', line)
                delivery_fees += sum(float(amt) for amt in amounts)
                
            elif 'Processing' in line:
                amounts = re.findall(r'\(\$([\d.]+)\)', line)
                processing_fees += sum(float(amt) for amt in amounts)
                
            elif 'Withheld sales tax' in line:
                amounts = re.findall(r'\(\$([\d.]+)\)', line)
                withheld_tax += sum(float(amt) for amt in amounts)
                
            elif 'Sales tax' in line and 'Withheld' not in line:
                amounts = re.findall(r'\$([\d.]+)(?!\s*\()', line)
                collected_tax += sum(float(amt) for amt in amounts)
        
        # Get date
        date_match = re.search(r'Deposit (\d{1,2}/\d{1,2}/\d{4})', text)
        date = datetime.strptime(date_match.group(1), '%m/%d/%Y') if date_match else None
        
        # Calculate total fees
        total_fees = marketing_fees + delivery_fees + processing_fees
        
        # Print raw text for debugging
        st.write("Raw section text (first 200 chars):", text[:200])
        st.write(f"""
        Parsed amounts for section:
        Marketing: ${marketing_fees:.2f}
        Delivery: ${delivery_fees:.2f}
        Processing: ${processing_fees:.2f}
        Collected Tax: ${collected_tax:.2f}
        Withheld Tax: ${withheld_tax:.2f}
        Net Deposit: ${net_deposit:.2f}
        """)
        
        return {
            'date': date,
            'subtotal': subtotal,
            'marketing_fees': marketing_fees,
            'delivery_fees': delivery_fees,
            'processing_fees': processing_fees,
            'total_fees': total_fees,
            'collected_tax': collected_tax,
            'withheld_tax': withheld_tax,
            'net_deposit': net_deposit
        }
    except Exception as e:
        st.error(f"Error parsing section: {str(e)}\nText causing error: {text[:200]}")
        return None

def process_statement(text):
    """Process the entire statement"""
    # Replace any multiple newlines with single newlines and normalize spaces
    text = re.sub(r'\n+', '\n', text.strip())
    text = re.sub(r'\s+', ' ', text)
    
    # Split into sections by deposit dates
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
            # Show raw input for debugging
            st.write("Input text length:", len(statement_text))
            st.write("First 200 characters of input:", statement_text[:200])
            
            deposits = process_statement(statement_text)
            
            if deposits:
                # Calculate totals
                total_sales = sum(d['subtotal'] for d in deposits)
                total_marketing = sum(d['marketing_fees'] for d in deposits)
                total_delivery = sum(d['delivery_fees'] for d in deposits)
                total_processing = sum(d['processing_fees'] for d in deposits)
                total_fees = sum(d['total_fees'] for d in deposits)
                total_collected_tax = sum(d['collected_tax'] for d in deposits)
                total_withheld_tax = sum(d['withheld_tax'] for d in deposits)
                total_deposits = sum(d['net_deposit'] for d in deposits)
                
                # Display totals
                st.write("### Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Sales", f"${total_sales:.2f}")
                    st.metric("Marketing Fees", f"${total_marketing:.2f}")
                with col2:
                    st.metric("Delivery Fees", f"${total_delivery:.2f}")
                    st.metric("Processing Fees", f"${total_processing:.2f}")
                with col3:
                    st.metric("Collected Tax", f"${total_collected_tax:.2f}")
                    st.metric("Withheld Tax", f"${total_withheld_tax:.2f}")
                
                st.metric("Net Deposits", f"${total_deposits:.2f}")
                
                # Display individual entries
                st.write("### Deposits")
                for deposit in deposits:
                    if deposit['date']:
                        date_str = deposit['date'].strftime('%m/%d/%Y')
                    else:
                        date_str = "Unknown Date"
                        
                    with st.expander(f"Deposit for {date_str}"):
                        st.write(f"Sales: ${deposit['subtotal']:.2f}")
                        st.write("Fees:")
                        st.write(f"- Marketing: ${deposit['marketing_fees']:.2f}")
                        st.write(f"- Delivery: ${deposit['delivery_fees']:.2f}")
                        st.write(f"- Processing: ${deposit['processing_fees']:.2f}")
                        st.write("Taxes:")
                        st.write(f"- Collected Tax: ${deposit['collected_tax']:.2f}")
                        st.write(f"- Withheld Tax: ${deposit['withheld_tax']:.2f}")
                        st.write(f"Net Deposit: ${deposit['net_deposit']:.2f}")

if __name__ == "__main__":
    main()
