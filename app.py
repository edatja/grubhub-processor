import streamlit as st
import pandas as pd
from datetime import datetime
import re
import pdfplumber
import io

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF using pdfplumber with enhanced text extraction"""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                # Extract text with better preservation of formatting
                text += page.extract_text(x_tolerance=3, y_tolerance=3) + "\n"
                
                # Debug: Show extracted text
                st.write("Extracted text sample:", text[:500])
                
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

def parse_amounts(text):
    """Parse all amounts in a text section"""
    amounts = {
        'total': 0,
        'marketing': 0,
        'delivery': 0,
        'processing': 0,
        'tax_collected': 0,
        'tax_withheld': 0,
        'net_deposit': 0
    }
    
    # Look for amounts line by line
    lines = text.split('\n')
    for i, line in enumerate(lines):
        # Debug line contents
        st.write(f"Processing line: {line}")
        
        # Marketing fees
        if 'Marketing' in line:
            match = re.search(r'\(\$?([\d,]+\.?\d*)\)', line)
            if match:
                amounts['marketing'] += float(match.group(1).replace(',', ''))
                st.write(f"Found marketing fee: ${amounts['marketing']}")
                
        # Delivery fees
        elif 'Deliveries by Grubhub' in line:
            match = re.search(r'\(\$?([\d,]+\.?\d*)\)', line)
            if match:
                amounts['delivery'] += float(match.group(1).replace(',', ''))
                st.write(f"Found delivery fee: ${amounts['delivery']}")
                
        # Processing fees
        elif 'Processing' in line:
            match = re.search(r'\(\$?([\d,]+\.?\d*)\)', line)
            if match:
                amounts['processing'] += float(match.group(1).replace(',', ''))
                st.write(f"Found processing fee: ${amounts['processing']}")
                
        # Total collected
        elif 'Total collected' in line:
            match = re.search(r'\$?([\d,]+\.?\d*)', line)
            if match:
                amounts['total'] = float(match.group(1).replace(',', ''))
                st.write(f"Found total: ${amounts['total']}")
                
        # Pay me now fee (net deposit)
        elif 'Pay me\s+now fee' in line:
            match = re.search(r'\$?([\d,]+\.?\d*)', line)
            if match:
                amounts['net_deposit'] = float(match.group(1).replace(',', ''))
                st.write(f"Found net deposit: ${amounts['net_deposit']}")
                
        # Tax amounts
        elif 'Sales tax' in line:
            if 'Withheld' in line:
                match = re.search(r'\(\$?([\d,]+\.?\d*)\)', line)
                if match:
                    amounts['tax_withheld'] += float(match.group(1).replace(',', ''))
            else:
                match = re.search(r'\$?([\d,]+\.?\d*)', line)
                if match:
                    amounts['tax_collected'] += float(match.group(1).replace(',', ''))
    
    return amounts

def process_statement(text):
    """Process the entire statement"""
    # Split into sections by Distribution ID or Deposit
    sections = re.split(r'(?=Distribution ID|Deposit \d{1,2}/\d{1,2}/\d{4})', text)
    
    deposits = []
    for section in sections:
        if 'Total collected' in section:
            # Debug each section
            st.write("\nProcessing new section:")
            st.write(section[:200])
            
            try:
                # Get date
                date_match = re.search(r'Deposit (\d{1,2}/\d{1,2}/\d{4})', section)
                date = datetime.strptime(date_match.group(1), '%m/%d/%Y') if date_match else None
                
                # Parse amounts
                amounts = parse_amounts(section)
                
                deposits.append({
                    'date': date,
                    'subtotal': amounts['total'],
                    'marketing_fees': amounts['marketing'],
                    'delivery_fees': amounts['delivery'],
                    'processing_fees': amounts['processing'],
                    'total_fees': amounts['marketing'] + amounts['delivery'] + amounts['processing'],
                    'collected_tax': amounts['tax_collected'],
                    'withheld_tax': amounts['tax_withheld'],
                    'net_deposit': amounts['net_deposit']
                })
                
                # Debug deposit info
                st.write(f"Processed deposit for {date}:")
                st.write(deposits[-1])
                
            except Exception as e:
                st.error(f"Error processing section: {str(e)}")
                st.error(f"Problematic section text: {section[:200]}")
                continue
    
    return deposits

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
        with st.spinner('Processing PDF...'):
            text = extract_text_from_pdf(uploaded_file)
            
            if text:
                st.success("PDF processed successfully!")
                
                # Process the statement with debug output
                st.write("### Debug Output")
                st.write("Processing statement text...")
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
                    
                    # Create CSV export
                    csv_data = []
                    for deposit in deposits:
                        if deposit['date']:
                            date_str = deposit['date'].strftime('%m/%d/%Y')
                        else:
                            date_str = ""
                            
                        csv_data.append({
                            'Date': date_str,
                            'Sales': f"${deposit['subtotal']:.2f}",
                            'Marketing Fees': f"${deposit['marketing_fees']:.2f}",
                            'Delivery Fees': f"${deposit['delivery_fees']:.2f}",
                            'Processing Fees': f"${deposit['processing_fees']:.2f}",
                            'Total Fees': f"${deposit['total_fees']:.2f}",
                            'Collected Tax': f"${deposit['collected_tax']:.2f}",
                            'Withheld Tax': f"${deposit['withheld_tax']:.2f}",
                            'Net Deposit': f"${deposit['net_deposit']:.2f}"
                        })
                    
                    df = pd.DataFrame(csv_data)
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
