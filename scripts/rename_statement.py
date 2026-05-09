#!/usr/bin/env python3
"""
Bank Statement PDF Renamer

Automatically rename bank statement PDFs following standardized naming convention:
[交易日期] BANKBLL [水单类型] [交易对方名称] [款项用途] [金额].pdf
"""

import os
import sys
import re
import pdfplumber
from pathlib import Path
from typing import Optional, Dict, Tuple


class BankStatementRenamer:
    """Rename bank statement PDFs with standardized naming convention."""
    
    def __init__(self, company_account: Optional[str] = None, company_name: Optional[str] = None):
        """
        Initialize renamer.
        
        Args:
            company_account: Company bank account number to identify payment direction
            company_name: Company name to identify payment direction
        """
        self.company_account = company_account
        self.company_name = company_name
        self.naming_pattern = re.compile(
            r'^(?P<date>\d{8})\s+BANKBLL\s+(?P<type>付款水单|收款水单)\s+(?P<counterparty>.+?)\s+(?P<purpose>.+?)\s+(?P<amount>[\d,]+\.\d{2})\.pdf$'
        )
    
    def extract_transaction_info(self, pdf_path: str) -> Optional[Dict]:
        """
        Extract transaction information from bank statement PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with transaction details or None if extraction fails
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if not pdf.pages:
                    return None
                
                # Extract text from first page
                text = pdf.pages[0].extract_text()
                if not text:
                    return None
                
                info = {'raw_text': text}
                
                # Extract transaction date
                date_match = re.search(r'交易日期[：:]\s*(\d{4}[-/]?\d{2}[-/]?\d{2})', text)
                if date_match:
                    date_str = date_match.group(1).replace('-', '').replace('/', '')
                    info['date'] = date_str
                
                # Extract amount
                amount_match = re.search(r'人民币[^RMB]*RMB([\d,]+\.\d{2})', text)
                if amount_match:
                    info['amount'] = amount_match.group(1)
                
                # Extract transaction type (业务类型)
                type_match = re.search(r'业务类型[：:]\s*(\S+)', text)
                if type_match:
                    info['business_type'] = type_match.group(1)
                
                # Extract fee type (收费种类)
                fee_type_match = re.search(r'收费种类\s+(.+?)(?:\s+\d)', text)
                if fee_type_match:
                    info['fee_type'] = fee_type_match.group(1).strip()
                
                # Extract payer info (付款人)
                payer_section = re.search(r'付\s*名称\s+(.+?)\s+收\s*名称', text, re.DOTALL)
                if payer_section:
                    section_text = payer_section.group(1)
                    
                    payer_name_match = re.search(r'名称\s+(.+?)(?:\s+账号|\s+款)', text)
                    if payer_name_match:
                        info['payer_name'] = payer_name_match.group(1).strip()
                    
                    payer_account_match = re.search(r'付\s*账号\s+(\d+)', text)
                    if payer_account_match:
                        info['payer_account'] = payer_account_match.group(1)
                
                # Extract payee info (收款人)
                payee_name_match = re.search(r'收\s*名称\s+(.+?)(?:\s+账号|\s+款)', text)
                if payee_name_match:
                    info['payee_name'] = payee_name_match.group(1).strip()
                
                payee_account_match = re.search(r'收\s*账号\s+(\d+)', text)
                if payee_account_match:
                    info['payee_account'] = payee_account_match.group(1)
                
                # Extract summary/remark
                summary_match = re.search(r'摘要或附言[：:]\s*(\S+)', text)
                if summary_match:
                    info['summary'] = summary_match.group(1)
                
                # Extract transaction type (收费回单 vs 客户回单)
                if '收费回单' in text:
                    info['document_type'] = '收费回单'
                elif '客户回单' in text:
                    info['document_type'] = '客户回单'
                
                return info
                
        except Exception as e:
            print(f"Error reading {pdf_path}: {e}")
            return None
    
    def determine_statement_type(self, info: Dict) -> Tuple[str, str]:
        """
        Determine if this is a payment or receipt statement.
        
        Args:
            info: Transaction information dict
            
        Returns:
            Tuple of (statement_type, counterparty_name)
            statement_type: "付款水单" or "收款水单"
            counterparty_name: Name of the counterparty
        """
        # Check if it's a bank fee collection
        if info.get('document_type') == '收费回单':
            # Fee collection - money goes out to bank
            return "付款水单", "中信银行"
        
        # If company account is specified, use it to determine direction
        if self.company_account:
            if info.get('payer_account') == self.company_account:
                return "付款水单", info.get('payee_name', '')
            elif info.get('payee_account') == self.company_account:
                return "收款水单", info.get('payer_name', '')
        
        # If company name is specified, use it
        if self.company_name:
            payer_name = info.get('payer_name', '')
            payee_name = info.get('payee_name', '')
            
            if self.company_name in payer_name or payer_name in self.company_name:
                # Company is payer
                return "付款水单", payee_name
            elif self.company_name in payee_name or payee_name in self.company_name:
                # Company is payee
                return "收款水单", payer_name
        
        # Default heuristic: check account numbers or names
        payer_name = info.get('payer_name', '')
        payee_name = info.get('payee_name', '')
        
        # Common company name patterns
        company_patterns = ['科技', '公司', '企业', '有限', '合伙']
        is_payer_company = any(p in payer_name for p in company_patterns)
        is_payee_company = any(p in payee_name for p in company_patterns)
        
        # If one side looks more like a company and the other doesn't
        if is_payer_company and not is_payee_company:
            return "付款水单", payee_name
        elif is_payee_company and not is_payer_company:
            return "收款水单", payer_name
        
        # Last resort: ask user or use default
        return "付款水单", payee_name if payee_name else "未知"
    
    def generate_filename(self, info: Dict, statement_type: str, counterparty: str) -> str:
        """
        Generate standardized filename.
        
        Args:
            info: Transaction information dict
            statement_type: "付款水单" or "收款水单"
            counterparty: Counterparty name
            
        Returns:
            New filename
        """
        date = info.get('date', '00000000')
        amount = info.get('amount', '0.00')
        
        # Determine purpose from summary or business type
        purpose = info.get('summary', '')
        if not purpose:
            purpose = info.get('business_type', '其他')
        
        # Check for bank fees
        if info.get('document_type') == '收费回单':
            fee_type = info.get('fee_type', '')
            if '转账' in fee_type or '跨行' in fee_type:
                purpose = '银行手续费'
            elif fee_type:
                purpose = '银行手续费'
        
        # Clean purpose - standardize common terms
        purpose_mapping = {
            '转账': '往来款',
            '银行手续费': '银行手续费',
            '普通转账（跨行）': '银行手续费',
            '普通转账': '银行手续费',
        }
        purpose = purpose_mapping.get(purpose, purpose)
        
        # Add "款" suffix if not present and appropriate
        if purpose and not purpose.endswith('款') and not purpose.endswith('税') and not purpose.endswith('费'):
            purpose += '款'
        
        # Clean counterparty name - remove common suffixes for brevity
        counterparty = counterparty.strip()
        # Remove common full suffixes for display
        if counterparty.endswith('（有限合伙）'):
            counterparty = counterparty.replace('（有限合伙）', '')
        
        filename = f"{date} BANKBLL {statement_type} {counterparty} {purpose} {amount}.pdf"
        return filename
    
    def is_already_named(self, filename: str) -> bool:
        """Check if file already follows naming convention."""
        return bool(self.naming_pattern.match(filename))
    
    def rename_file(self, pdf_path: str, dry_run: bool = False) -> Optional[str]:
        """
        Rename a single PDF file.
        
        Args:
            pdf_path: Path to PDF file
            dry_run: If True, only preview without renaming
            
        Returns:
            New filename or None if renaming failed
        """
        filename = os.path.basename(pdf_path)
        
        # Skip if already properly named
        if self.is_already_named(filename):
            print(f"✓ Already properly named: {filename}")
            return filename
        
        # Extract transaction info
        info = self.extract_transaction_info(pdf_path)
        if not info:
            print(f"✗ Failed to extract info from: {filename}")
            return None
        
        # Determine statement type and counterparty
        statement_type, counterparty = self.determine_statement_type(info)
        
        # Generate new filename
        new_filename = self.generate_filename(info, statement_type, counterparty)
        
        if dry_run:
            print(f"[PREVIEW] {filename}")
            print(f"    → {new_filename}")
            return new_filename
        
        # Rename file
        directory = os.path.dirname(pdf_path)
        new_path = os.path.join(directory, new_filename)
        
        try:
            os.rename(pdf_path, new_path)
            print(f"✓ Renamed: {filename} → {new_filename}")
            return new_filename
        except Exception as e:
            print(f"✗ Failed to rename {filename}: {e}")
            return None
    
    def rename_directory(self, directory: str, dry_run: bool = False) -> Dict:
        """
        Rename all PDF files in a directory.
        
        Args:
            directory: Path to directory
            dry_run: If True, only preview without renaming
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total': 0,
            'success': 0,
            'skipped': 0,
            'failed': 0
        }
        
        # Find all PDF files
        pdf_files = list(Path(directory).glob('*.pdf'))
        stats['total'] = len(pdf_files)
        
        print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing {stats['total']} PDF files...\n")
        
        for pdf_path in sorted(pdf_files):
            result = self.rename_file(str(pdf_path), dry_run)
            
            if result:
                if self.is_already_named(pdf_path.name):
                    stats['skipped'] += 1
                else:
                    stats['success'] += 1
            else:
                stats['failed'] += 1
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"Summary:")
        print(f"  Total: {stats['total']}")
        print(f"  {'Would rename' if dry_run else 'Renamed'}: {stats['success']}")
        print(f"  Skipped (already named): {stats['skipped']}")
        print(f"  Failed: {stats['failed']}")
        print(f"{'='*60}\n")
        
        return stats


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Rename bank statement PDFs with standardized naming convention',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  # Preview renaming (no changes)
  python rename_statement.py ./bank_statements --dry-run
  
  # Actually rename files
  python rename_statement.py ./bank_statements
  
  # Specify company account for better direction detection
  python rename_statement.py ./bank_statements --account 8110701012802583187
  
  # Specify company name
  python rename_statement.py ./bank_statements --company-name "北京磐旭科技"
        """
    )
    
    parser.add_argument('directory', help='Directory containing PDF files to rename')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview renaming without making changes')
    parser.add_argument('--account', 
                       help='Company bank account number to identify transaction direction')
    parser.add_argument('--company-name', 
                       help='Company name to identify transaction direction')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: Directory not found: {args.directory}")
        sys.exit(1)
    
    renamer = BankStatementRenamer(
        company_account=args.account,
        company_name=args.company_name
    )
    stats = renamer.rename_directory(args.directory, dry_run=args.dry_run)
    
    if args.dry_run:
        print("\nThis was a dry run. Remove --dry-run to actually rename files.")
    
    sys.exit(0 if stats['failed'] == 0 else 1)


if __name__ == '__main__':
    main()
