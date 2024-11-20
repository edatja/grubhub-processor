def extract_fees(self, section, total_collected, net_deposit, tax):
        """Calculate fees as the difference between total collected and net deposit, accounting for tax"""
        # Fees = Total Collected - Net Deposit - Tax
        fees = total_collected - net_deposit - tax
        return round(fees, 2)

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

                # Find the Total collected amount
                total_match = re.search(r'Total collected\s+\$(\d+\.\d+)', section)
                subtotal = float(total_match.group(1)) if total_match else 0

                # Extract tax
                collected_tax, withheld_tax = self.extract_tax(section)
                
                # Extract net deposit (last amount in section)
                amount_matches = list(re.finditer(r'\$(\d+\.\d+)(?!\s*\()', section))
                if amount_matches:
                    net_deposit = float(amount_matches[-1].group(1))
                else:
                    # If we can't find the net deposit, calculate it
                    net_deposit = 0

                # Calculate fees using the new method
                fees = self.extract_fees(section, subtotal, net_deposit, collected_tax)

                # Debug information
                st.write(f"""
                Debug information for deposit {date}:
                - Distribution ID: {distribution_id}
                - Period: {order_period}
                - Subtotal (Total Collected): ${subtotal:.2f}
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
                    'tax': collected_tax,
                    'fees': fees,
                    'withheld_tax': withheld_tax,
                    'net_deposit': net_deposit
                })

            except Exception as e:
                st.error(f"Error processing section: {str(e)}")
                continue

        return deposits
