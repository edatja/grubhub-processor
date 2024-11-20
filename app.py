import streamlit as st
import pandas as pd
from datetime import datetime
import re
import pdfplumber
import io

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF using pdfplumber"""
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

def parse_deposit_section(text):
    """Parse a single deposit section"""
    try:
        # Get total collected amount
        total_match = re.search(r'Total collected\s+\$([\d.]+)', text)
        subtotal = float(total_match.group(1)) if total_match else 0
        
        # Get net deposit
        net_match = re.search(r'Pay me\s+now fee\s+\$([\d.]+)', text)
        net_deposit = float(net_match.group(1)) if net_match else 0
        
        # Get date
        date_match = re.search(r'Deposit (\d{1,2}/\d{1,2}/\d{4})', text)
        date = datetime.strptime(date_match.group(1), '%m/%d/%Y') if date_match else None
        
        # Extract fees (amounts in parentheses)
        marketing_fees = 0
        delivery_fees = 0
        processing_fees = 0
        collected_tax = 0
        withheld_tax = 0
        
        lines = text.split('\n')
        for line in lines:
            # Extract Marketing fees
            if 'Marketing' in line:
                fee_match = re.search(r'\(\$([\d.]+)\)', line)
                if fee_match:
                    marketing_fees += float(fee_match.group(1))
            
            # Extract Delivery fees
            elif 'Deliveries by Grubhub' in line:
                fee_match = re.search(r'\(\$([\d.]+)\)', line)
                if fee_match:
                    delivery_fees += float(fee_match.group(1))
            
            # Extract Processing fees
            elif 'Processing' in line:
                fee_match = re.search(r'\(\$([\d.]+)\)', line)
                if fee_match:
                    processing_fees += float(fee_match.group(1))
            
            # Extract Withheld tax
            elif 'Withheld sales tax' in line:
                tax_match = re.search(r'\(\$([\d.]+)\)', line)
                if tax_match:
                    withheld_tax += float(tax_match.group(1))
            
            # Extract Collected tax
            elif 'Sales tax' in line and 'Withheld' not in line:
                tax_match = re.search(r'\$([\d.]+)(?!\s*\()', line)
                if tax_match:
                    collected_tax += float(tax_match.group(1))
        
        total_fees = marketing_fees + delivery_fees + processing_fees
        
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
        st.error(f"Error parsing section: {str(e)}")
        return None

def process_statement(text):
    """Process the entire statement"""
    # Split into sections by deposit dates
    sections = re.split(r'(?=Deposit \d{1,2}/\d{1,2}/\d{4})', text)
    
    deposits = []
    for section in sections:
        if 'Total collected' in section:
            result = parse_deposit_section(section)
            if result:
                deposits.append(result)
    
    return deposits

def create_quickbooks_csv(deposits):
    """Create CSV data for QuickBooks import"""
    csv_data = []
    accounts = {
        'sales': '44030',                # Grubhub Sales
        'fees': '60260',                 # Grubhub Fees
        'tax': 'Sales Tax Payable',      # Sales Tax Payable
        'bank': 'Checking - 5734 - 1'    # Bank Account
    }
    
    for deposit in deposits:
        date_str = deposit['date'].strftime('%m/%d/%Y') if deposit['date'] else ''
        
        # Bank account debit
        csv_data.append({
            'Date': date_str,
            'Account': accounts['bank'],
            'Debit': deposit['net_deposit'],
            'Credit': '',
            'Memo': 'Net GrubHub Deposit'
        })
        
        # Fees debit
        if deposit['total_fees'] > 0:
            csv_data.append({
                'Date': date_str,
                'Account': accounts['fees'],
                'Debit': deposit['total_fees'],
                'Credit': '',
                'Memo': 'GrubHub Fees'
            })
        
        # Sales credit
        csv_data.append({
            'Date': date_str,
            'Account': accounts['sales'],
            'Debit': '',
            'Credit': deposit['subtotal'],
            'Memo': 'Food Sales'
        })
        
        # Tax credit
        if deposit['collected_tax'] > 0:
            csv_data.append({
                'Date': date_str,
                'Account': accounts['tax'],
                'Debit': '',
                'Credit': deposit['collected_tax'],
                'Memo': 'Sales Tax Collected'
            })
    
    return pd.DataFrame(csv_data)

def main():
    st.title('🧾 Food Delivery Statement Processor')
    
    st.markdown("""
    ### Instructions
    1. Upload your GrubHub statement PDF
    2. Review the processed entries
    3. Download the QuickBooks CSV file
    """)

    uploaded_file = st.file_uploader("Upload GrubHub PDF statement", type=['pdf'])
    
    if uploaded_file is not None:
        # Extract text from PDF
        text = extract_text_from_pdf(uploaded_file)
        
        if text:
            st.success("PDF processed successfully!")
            
            # Process the statement
            deposits = process_statement(text)
            
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
                
                # Display summary
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
                
                # Create QuickBooks CSV
                df = create_quickbooks_csv(deposits)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    label="📥 Download QuickBooks CSV",
                    data=csv,
                    file_name="grubhub_quickbooks.csv",
                    mime="text/csv",
                )
            else:
                st.warning("No deposits found in the statement.")
        else:
            st.error("Error processing PDF. Please check the file and try again.")

if __name__ == "__main__":
    main()
