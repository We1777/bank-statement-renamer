# Bank Statement Naming Standards

## Complete Naming Convention

### Format
```
[交易日期] BANKBLL [水单类型] [交易对方名称] [款项用途] [金额].pdf
```

## Field Details

### 1. 交易日期 (Transaction Date)

**Format:** YYYYMMDD (8 digits, no separators)

**Examples:**
- `20260301` - March 1, 2026
- `20260303` - March 3, 2026
- `20260331` - March 31, 2026

**Extraction from PDF:**
- Look for: `交易日期：20260303` or `交易日期：2026-03-03`
- Normalize to 8-digit format

### 2. BANKBLL (Fixed Identifier)

**Value:** Always `BANKBLL`

**Purpose:**
- Identifies file as bank statement
- Enables quick search/filtering
- Standardized across all statements

### 3. 水单类型 (Statement Type)

**Values:**
- `付款水单` - Payment statement (money flows OUT)
- `收款水单` - Receipt statement (money flows IN)

**Determination Logic:**

| Scenario | Statement Type | Counterparty |
|----------|---------------|--------------|
| Company is payer (付款人) | 付款水单 | Payee name (收款人) |
| Company is payee (收款人) | 收款水单 | Payer name (付款人) |
| Bank fee collection (收费回单) | 付款水单 | Bank name or "银行" |

**Extraction from PDF:**
- Compare company account with payer/payee account
- Check document type: "收费回单" vs "客户回单"
- Look for payer/payee name fields

### 4. 交易对方名称 (Counterparty Name)

**Format:** Full entity name or recognized abbreviation

**Examples:**
- `北京合辉科技合伙企业`
- `海淀区税务局`
- `中信银行`
- `曹玮`
- `公积金中心`

**Cleaning Rules:**
- Remove extra spaces
- Keep full company name for clarity
- For individuals, use their name directly
- For government agencies, use standard abbreviations

### 5. 款项用途 (Transaction Purpose)

**Common Categories:**

#### Payment Purposes
| Purpose | Description | Typical Counterparty |
|---------|-------------|---------------------|
| 银行手续费 | Bank service fees | 银行 |
| 零星费用款 | Miscellaneous expenses | Vendors, service providers |
| 工资款 | Salary payments | Employees |
| 社保款 | Social security | 社保局/社保中心 |
| 个税费 | Individual income tax | 税务局 |
| 公积金款 | Housing fund | 公积金中心 |
| 报销款 | Reimbursements | Employees |
| 印花税费 | Stamp duty | 税务局 |
| 增值税及其附加税费 | VAT and surcharges | 税务局 |

#### Receipt Purposes
| Purpose | Description | Typical Counterparty |
|---------|-------------|---------------------|
| 关联方往来款 | Related party transactions | Related companies |
| 货款 | Payment for goods | Customers |
| 服务费 | Service fees | Customers |
| 投资款 | Investment funds | Investors |

**Extraction from PDF:**
- Look for `摘要或附言` field
- Use `业务类型` as fallback
- Apply standard terminology mapping

### 6. 金额 (Amount)

**Format Rules:**
- Always include 2 decimal places: `.00`
- Use comma as thousand separator for amounts ≥ 1,000
- No currency symbol

**Examples:**
- `3.60` - 3 yuan and 60 fen
- `210.00` - 210 yuan
- `12,960.00` - 12,960 yuan
- `126,974.65` - 126,974 yuan and 65 fen
- `5.00` - 5 yuan

**Extraction from PDF:**
- Look for: `人民币...RMB210.00` pattern
- Extract numeric value with decimals
- Apply thousand separator formatting

## Complete Examples

### Payment Statements

```
20260301 BANKBLL 付款水单 中信银行 银行手续费 3.60.pdf
20260303 BANKBLL 付款水单 北京合辉科技合伙企业 零星费用款 210.00.pdf
20260305 BANKBLL 付款水单 海淀区税务局 增值税及其附加税费 288.13.pdf
20260310 BANKBLL 付款水单 公积金中心 公积金款 12,960.00.pdf
20260310 BANKBLL 付款水单 磐旭科技 工资款 126,974.65.pdf
20260312 BANKBLL 付款水单 磐旭科技 个税费 5,035.44.pdf
```

### Receipt Statements

```
20260303 BANKBLL 收款水单 北京合辉科技合伙企业 关联方往来款 5.00.pdf
20260303 BANKBLL 收款水单 北京科旷科技有限公司 关联方往来款 5.00.pdf
```

## Validation Checklist

Before finalizing filename, verify:

- [ ] Date is 8 digits (YYYYMMDD)
- [ ] Identifier is exactly "BANKBLL"
- [ ] Statement type is "付款水单" or "收款水单"
- [ ] Counterparty name is not empty
- [ ] Purpose uses standard terminology
- [ ] Amount has exactly 2 decimal places
- [ ] Amount uses comma separator for thousands (if ≥ 1,000)
- [ ] No special characters that could cause filesystem issues
- [ ] Filename ends with ".pdf"

## Special Cases

### Bank Fee Collection (收费回单)
- Statement type: 付款水单
- Counterparty: Bank name (e.g., 中信银行)
- Purpose: 银行手续费

### Tax Payments
- Statement type: 付款水单
- Counterparty: Tax bureau name (e.g., 海淀区税务局)
- Purpose: Specific tax type (e.g., 印花税费, 增值税及其附加税费)

### Employee Transactions
- For salary: 工资款
- For reimbursement: 报销款
- Counterparty: Employee name

### Related Party Transactions
- Purpose: 关联方往来款
- Can be either payment or receipt
- Clearly identify both directions

## Benefits of Standardization

1. **Easy Search:** Find by date, counterparty, or amount
2. **Quick Identification:** Filename tells the whole story
3. **Audit Trail:** Clear documentation for compliance
4. **Reconciliation:** Match with accounting records easily
5. **Batch Processing:** Enables automated processing
6. **Consistency:** Uniform naming across all statements

## Integration with Accounting

The naming convention supports:

- **Monthly reconciliation:** Group by date range
- **Vendor tracking:** Filter by counterparty name
- **Expense categorization:** Use purpose field
- **Amount verification:** Quick visual check
- **Audit documentation:** Clear transaction trail
