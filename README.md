# GrubHub Statement Processor

A Streamlit app that processes GrubHub statements and generates QuickBooks journal entries.

## Dependencies
```
streamlit==1.40.1
pandas==2.2.3
python-dateutil==2.9.0
pdfplumber==0.10.3
```

## System Requirements
- python3-dev
- libpq-dev

## Features
- Upload GrubHub PDF statements
- Automatically extracts:
  - Sales amounts
  - Marketing fees
  - Delivery fees
  - Processing fees
  - Sales tax (collected and withheld)
  - Net deposits
- Generates QuickBooks-compatible CSV file
- Provides detailed summary and breakdown of each deposit

## Usage
1. Upload your GrubHub statement PDF
2. Review the processed entries and totals
3. Download the QuickBooks-ready CSV file

## Account Mappings
- Sales Account: 44030 (GrubHub Sales)
- Fees Account: 60260 (GrubHub Fees)
- Bank Account: Checking - 5734 - 1
- Tax Account: Sales Tax Payable

## Journal Entry Format
Each deposit creates entries for:
- Bank deposit (debit)
- Fees (debit)
- Sales (credit)
- Sales tax (credit)
