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
    
    # Clean up text - remove extra spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    
    # Find total collected
    total_match = re.search(r'Total collected[\s$]*(\d+\.\d+)', text)
    if total_match:
        amounts['total'] = float(total_match.group(1))
    
    # Find net deposit (Pay me now fee)
    net_match = re.search(r'now fee\s*\$?(\d+\.\d+)', text)
    if net_match:
        amounts['net_deposit'] = float(net_match.group(1))
    
    # Find Marketing fees - looking specifically in the line containing "Marketing"
    marketing_match = re.search(r'Marketing.*?\(\$?(\d+\.\d+)\)', text)
    if marketing_match:
        amounts['marketing'] = float(marketing_match.group(1))
    
    # Find Delivery fees
    delivery_match = re.search(r'Deliveries by Grubhub.*?\(\$?(\d+\.\d+)\)', text)
    if delivery_match:
        amounts['delivery'] = float(delivery_match.group(1))
    
    # Find Processing fees
    processing_match = re.search(r'Processing.*?\(\$?(\d+\.\d+)\)', text)
    if processing_match:
        amounts['processing'] = float(processing_match.group(1))
    
    # Find Sales tax
    tax_matches = re.finditer(r'Sales tax\s*\$?(\d+\.\d+)', text)
    for match in tax_matches:
        amounts['tax_collected'] += float(match.group(1))
    
    # Find Withheld tax
    withheld_match = re.search(r'Withheld sales tax.*?\(\$?(\d+\.\d+)\)', text)
    if withheld_match:
        amounts['tax_withheld'] = float(withheld_match.group(1))
    
    # Debug output
    st.write("Found amounts:", amounts)
    
    return amounts

def parse_deposit_section(section):
    """Parse a single deposit section with debug output"""
    try:
        # Get date
        date_match = re.search(r'Deposit (\d{1,2}/\d{1,2}/\d{4})', section)
        date = datetime.strptime(date_match.group(1), '%m/%d/%Y') if date_match else None
        
        # Debug the section text
        st.write(f"\nProcessing deposit for {date}:")
        st.write("Section text sample:", section[:200])
        
        # Parse amounts
        amounts = parse_amounts(section)
        
        return {
            'date': date,
            'subtotal': amounts['total'],
            'marketing_fees': amounts['marketing'],
            'delivery_fees': amounts['delivery'],
            'processing_fees': amounts['processing'],
            'total_fees': amounts['marketing'] + amounts['delivery'] + amounts['processing'],
            'collected_tax': amounts['tax_collected'],
            'withheld_tax': amounts['tax_withheld'],
            'net_deposit': amounts['net_deposit']
        }
        
    except Exception as e:
        st.error(f"Error processing section: {str(e)}")
        return None
