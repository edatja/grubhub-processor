def extract_fees_from_totals(self, section):
    """Extract fees from the 'Total collected' section"""
    fees = 0.0
    
    # Look for the Marketing, Deliveries by Grubhub, and Processing amounts after "Total collected"
    total_section = re.search(r'Total collected.*?\$[\d.]+([^$]+)Pay me', section, re.DOTALL)
    if total_section:
        total_text = total_section.group(1)
        
        # Extract all amounts in parentheses (excluding withheld sales tax)
        fee_pattern = r'\(([\d.]+)\)'
        matches = re.finditer(fee_pattern, total_text)
        
        for match in matches:
            amount = float(match.group(1))
            # Only add if it's in the marketing/delivery/processing lines
            if any(fee_type in total_text[:total_text.find(match.group(0))] 
                   for fee_type in ['Marketing', 'Deliveries by Grubhub', 'Processing']):
                fees += amount
    
    return fees

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
            period_match = re.search(r'Orders (\d{1,2}/\d{1,2})(?:\sto\s)(\d{1,2}/\d{1,2})', section)
            order_period = f"{period_match.group(1)} to {period_match.group(2)}" if period_match else ""

            # Find the Total collected amount
            total_match = re.search(r'Total collected\s+\$([\d.]+)', section)
            subtotal = float(total_match.group(1)) if total_match else 0

            # Extract fees using the new method
            fees = self.extract_fees_from_totals(section)

            # Extract withheld tax
            withheld_tax_match = re.search(r'Withheld\s+sales\s+tax\s+\(\$([\d.]+)\)', section)
            withheld_tax = float(withheld_tax_match.group(1)) if withheld_tax_match else 0

            # Extract collected tax (from the itemized sections)
            collected_tax_matches = re.finditer(r'Sales\s+tax\s+\$([\d.]+)', section)
            collected_tax = sum(float(match.group(1)) for match in collected_tax_matches)

            # Extract net deposit from "Pay me now fee" line
            net_match = re.search(r'Pay me\s+now fee\s+\$([\d.]+)', section)
            net_deposit = float(net_match.group(1)) if net_match else 0

            # Debug information
            st.write(f"""
            Debug information for deposit {date}:
            - Distribution ID: {distribution_id}
            - Period: {order_period}
            - Subtotal (Total Collected): ${subtotal:.2f}
            - Fees (Marketing + Delivery + Processing): ${fees:.2f}
            - Collected Tax: ${collected_tax:.2f}
            - Withheld Tax: ${withheld_tax:.2f}
            - Net Deposit: ${net_deposit:.2f}
            """)

            deposits.append({
                'date': date,
                'distribution_id': distribution_id,
                'order_period': order_period,
                'subtotal': subtotal,
                'tax': collected_tax,
                'fees': fees,
                'withheld_tax': withheld_tax,
                'net_deposit': net_deposit
            })

        except Exception as e:
            st.error(f"Error processing section: {str(e)}")
            continue

    return deposits
