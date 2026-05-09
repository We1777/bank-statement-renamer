---
name: bank-statement-renamer
description: Rename bank statement PDF files following standardized naming convention. Use this skill when user provides unorganized bank statement PDFs that need to be renamed with proper format: date + transaction type + counterparty + purpose + amount.
---

# Bank Statement Renamer

## Overview

Standardize bank statement PDF file names according to a consistent naming convention for easy management, searching, and reconciliation. This skill handles both payment (付款水单) and receipt (收款水单) statements from bank transaction records.

## When to Use This Skill

Trigger this skill when:
- User asks to rename bank statement PDF files
- User provides unorganized bank statement files
- User mentions "银行水单", "付款水单", "收款水单", "银行回单"
- User wants to standardize bank document naming

## Naming Convention

### Standard Format

```
[交易日期] BANKBLL [水单类型] [交易对方名称] [款项用途] [金额].pdf
```

### Field Specifications

| Field | Format | Description | Example |
|-------|--------|-------------|---------|
| **交易日期** | YYYYMMDD | 8-digit transaction date | `20260303` |
| **BANKBLL** | Fixed identifier | Bank statement marker | `BANKBLL` |
| **水单类型** | 付款水单/收款水单 | Payment or receipt type | `付款水单` |
| **交易对方名称** | Entity name | Counterparty in transaction | `北京合辉科技合伙企业` |
| **款项用途** | Business purpose | Transaction purpose | `零星费用款` |
| **金额** | Number with decimals | Amount with 2 decimal places | `210.00`, `12,960.00` |

### Transaction Direction Logic

**Payment Statement (付款水单)** - Money flows OUT:
```
20260303 BANKBLL 付款水单 北京合辉科技合伙企业 零星费用款 210.00.pdf
                      ↓
        Recipient: 北京合辉科技合伙企业 (party receiving money)
```

**Receipt Statement (收款水单)** - Money flows IN:
```
20260303 BANKBLL 收款水单 北京合辉科技合伙企业 关联方往来款 5.00.pdf
                      ↓
        Payer: 北京合辉科技合伙企业 (party sending money)
```

### Common Purpose Categories

**Payment purposes:**
- 银行手续费
- 零星费用款
- 工资款
- 社保款
- 个税费
- 公积金款
- 报销款
- 印花税费
- 增值税及其附加税费

**Receipt purposes:**
- 关联方往来款
- 货款
- 服务费

## Workflow

### Step 1: Extract Information from PDF

When user provides a bank statement PDF:

1. Read the PDF file using pdfplumber
2. Extract key fields:
   - Transaction date (交易日期)
   - Transaction type (业务类型)
   - Payer information (付款人名称、账号)
   - Payee information (收款人名称、账号)
   - Amount (金额)
   - Summary/Remark (摘要或附言)

3. Determine statement type:
   - If company account is the payer → **付款水单**
   - If company account is the payee → **收款水单**

4. Identify counterparty:
   - For payment statements: use payee name
   - For receipt statements: use payer name

### Step 2: Generate New Filename

Construct filename following the standard format:

```python
new_filename = f"{date} BANKBLL {statement_type} {counterparty} {purpose} {amount}.pdf"
```

### Step 3: Rename File

Execute the renaming operation:
- Confirm with user before making changes
- Use OS rename function
- Report success or any errors

## Example Usage

### Example 1: Single File Rename

**User:** "请帮我重命名这个银行水单PDF"

**Process:**
1. Read PDF and extract: date=20260303, payer=北京磐旭科技, payee=北京合辉科技, amount=210.00, remark=零星费用
2. Identify: 北京磐旭科技 is payer → 付款水单
3. Counterparty: 北京合辉科技合伙企业
4. Purpose: 零星费用款
5. Generate: `20260303 BANKBLL 付款水单 北京合辉科技合伙企业 零星费用款 210.00.pdf`

### Example 2: Batch Rename

**User:** "我有多个未命名的银行水单，请帮我批量重命名"

**Process:**
1. Scan all PDF files in the directory
2. For each file:
   - Extract information
   - Generate new filename
   - Display renaming plan
3. After user confirmation:
   - Rename all files
   - Report summary

## Validation Rules

Before finalizing filename, validate:

1. **Date format**: Must be 8 digits (YYYYMMDD)
2. **Statement type**: Must be "付款水单" or "收款水单"
3. **Counterparty**: Should not be empty
4. **Purpose**: Use standard categories when possible
5. **Amount**: 
   - Include 2 decimal places
   - Use thousand separator for amounts ≥ 1,000
   - Example: `3.60`, `210.00`, `12,960.00`

## Scripts

### `rename_statement.py`

Python script for automated batch renaming with validation.

**Usage:**
```bash
python scripts/rename_statement.py <directory> [--dry-run]
```

**Options:**
- `directory`: Path to folder containing PDF files
- `--dry-run`: Preview renaming without making changes

The script:
1. Scans all PDF files in directory
2. Extracts transaction details from each file
3. Generates standardized filenames
4. Validates each new filename
5. Renames files (or shows preview with --dry-run)

## Benefits

✅ **Consistency**: Uniform naming across all bank statements  
✅ **Searchability**: Easy to find files by date, counterparty, or amount  
✅ **Transparency**: Filename reveals transaction direction and purpose  
✅ **Reconciliation**: Simplifies matching transactions with accounting records  
✅ **Audit Trail**: Clear naming supports compliance requirements

## Notes

- Always confirm with user before renaming files
- Handle special characters in counterparty names appropriately
- For ambiguous transactions, ask user to clarify
- Keep original filename available in case of rollback needs
