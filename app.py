import streamlit as st
import pandas as pd
from datetime import datetime
import re
import PyPDF2
import pytesseract
from pdf2image import convert_from_bytes
import io

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF using both PDF text extraction and OCR if needed"""
    try:
        # First try direct PDF text extraction
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        # If we got meaningful text, return it
        if len(text.strip()) > 100:  # Arbitrary threshold to check if we got real text
            return text
        
        # If direct extraction didn't work well, try OCR
        images = convert_from_bytes(pdf_file.getvalue())
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image) + "\n"
        
        return text
    
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return None

def parse_deposit_section(text):
    """Parse a single deposit section with detailed fee breakdowns"""
    try:
        # Get the total collected amount
        total_match = re.search(r'Total collected[^\$]*\$([\d,.]+)', text)
        subtotal = float(total_match.group(1).replace(',', '')) if total_match else 0
        
        # Get the net deposit
        net_match = re.search(r'Pay me\s+now fee[^\$]*\$([\d,.]+)', text)
        net_deposit = float(net_match.group(1).replace(',', '')) if net_match else 0
        
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
            
            # Extract amounts in parentheses (fees)
            amounts = re.findall(r'\(\$([\d,.]+)\)', line)
            amounts = [float(amt.replace(',', '')) for amt in amounts]
            
            if 'Marketing' in line and amounts:
                marketing_fees += sum(amounts)
            elif 'Deliveries by Grubhub' in line and amounts:
                delivery_fees += sum(amounts)
            elif 'Processing' in line and amounts:
                processing_fees += sum(amounts)
            elif 'Withheld sales tax' in line and amounts:
                withheld_tax += sum(amounts)
            
            # Extract sales tax (not in parentheses)
            if 'Sales tax' in line and 'Withheld' not in line:
                tax_matches = re.findall(r'\$([\d,.]+)(?!\s*\()', line)
                collected_tax += sum(float(amt.replace(',', '')) for amt in tax_matches)
        
        # Get date
        date_match = re.search(r'Deposit (\d{1,2}/\d{1,2}/\d{4})', text)
        date = datetime.strptime(date_match.group(1), '%m/%d/%Y') if date_match else None
        
        return {
            'date': date,
            'subtotal': subtotal,
            'marketing_fees': marketing_fees,
            'delivery_fees': delivery_fees,
            'processing_fees': processing_fees,
            'total_fees': marketing_fees + delivery_fees + processing_fees,
            'collected_tax': collected_tax,
            'withheld_tax': withheld_tax,
            'net_deposit': net_deposit
        }
    
    except Exception as e:
        st.error(f"Error parsing section: {str(e)}")
        return None

def process_statement(text):
    """Process the entire statement"""
    # Clean up the text
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
    
    uploaded_file = st.file_uploader("Upload GrubHub statement PDF", type=['pdf'])
    
    if uploaded_file is not None:
        # Extract text from PDF
        with st.spinner('Processing PDF...'):
            text = extract_text_from_pdf(uploaded_file)
            
            if text:
                st.success("PDF processed successfully!")
                
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
                    
                    # Create CSV export option
                    csv_data = []
                    for deposit in deposits:
                        csv_data.append({
                            'Date': deposit['date'].strftime('%m/%d/%Y') if deposit['date'] else '',
                            'Sales': deposit['subtotal'],
                            'Marketing Fees': deposit['marketing_fees'],
                            'Delivery Fees': deposit['delivery_fees'],
                            'Processing Fees': deposit['processing_fees'],
                            'Collected Tax': deposit['collected_tax'],
                            'Withheld Tax': deposit['withheld_tax'],
                            'Net Deposit': deposit['net_deposit']
                        })
                    
                    df = pd.DataFrame(csv_data)
                    csv = df.to_csv(index=False)
                    
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name="grubhub_statement.csv",
                        mime="text/csv",
                    )

if __name__ == "__main__":
    main()
