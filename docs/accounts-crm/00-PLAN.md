# Accounts and CRM — the full plan (2026-10-18)

Two new modules on the same product, like Store & Inventory: **Accounts**
(the company's books: ledger, receivables, payables, bank, VAT, statements)
and **CRM** (leads, opportunities, quotations, customer care, field sales).
Each is switched on per company by the platform owner, uses the same login,
branches, permissions, audit log, API conventions and look as the rest.

This is the plan of record. Phase 0 (decisions) comes first; nothing is
built before the client's accountant has answered section 11.

---

## 1. What the client gets, in plain words

### Accounts

- **One set of books per company**, double-entry, in BDT, with the
  Bangladesh fiscal year (July–June) unless the accountant chooses another.
- **Everything that already happens posts itself**: a goods receipt, a
  supplier bill, a delivery, a sales invoice, a payment, a stock adjustment,
  production, the month's salary - each makes its journal entry automatically.
  Nobody types the same thing twice.
- **Who owes us, whom we owe**: every customer's and supplier's balance,
  ageing (0–30, 31–60, 61–90, 90+ days), statements to send, reminders.
- **Money in and out**: receipts and payments by cash, cheque, bank
  transfer, bKash/Nagad; post-dated cheques tracked; bank statements
  reconciled.
- **VAT and tax at source** the Bangladesh way: input and output VAT, Mushak
  registers and invoice layouts, VDS/TDS deducted and certified, the monthly
  return worked out.
- **Fixed assets** with depreciation; **budgets** by branch and department.
- **The statements**: trial balance, profit and loss, balance sheet, cash
  flow - for any period, any branch - and month-end and year-end close.

### CRM

- **Every customer and prospect in one place** (the same customers Sales
  already uses - never two lists): companies, contact people, territories,
  who looks after them.
- **Leads to customers**: enquiries from the web, phone, email, fairs and
  the AI inbox become leads; qualified leads become customers and
  opportunities.
- **The pipeline**: opportunities by stage with value and expected date;
  calls, meetings, visits and tasks with reminders.
- **Quotations** from the price lists; an accepted quotation becomes a sales
  order in one click (the existing Sales module takes it from there).
- **Customer care**: complaints and requests as tickets, traced to the
  delivery and **batch** (product recall in minutes, using the inventory
  traceability already built).
- **Field sales**: visit plans, check-ins, targets per sales officer,
  commission from paid invoices.
- **Customer 360**: orders, deliveries, invoices, payments, balance, tickets
  and activities of one customer on one page.

### How it all connects (one line)

```
CRM: lead ─► opportunity ─► quotation ─┐
                                       ▼
Sales (built): sales order ─► delivery ─► invoice ─────► Accounts: receivable ─► receipt ─► bank
Purchase (built): PO ─► GRN ─► (supplier bill) ───────► Accounts: payable ────► payment ─► bank
Inventory (built): every stock move with its value ──► Accounts: inventory, COGS, WIP
Payroll (built): finalised salary run ───────────────► Accounts: salary expense / payable
                                                        │
                                                        ▼
                           trial balance · P&L · balance sheet · VAT return · close
```

---

## 2. How it fits the product we already have

| Already there | Accounts / CRM use it for |
|---|---|
| Companies, branches, departments | Cost centres, branch P&L, data separation (TenantOwned) |
| Branch permissions (`access_control`), feature flags | New permissions and the `accounts` / `crm` features |
| Audit log | Every posting, approval, change |
| `sales.Customer`, `purchasing.Supplier` | Customer and supplier subledgers; CRM accounts (no new customer table) |
| Sales invoices (amount, VAT, total, due date, paid) | Receivables; "mark paid" becomes a real receipt |
| GRN (supplier invoice no., cost) | Payables; goods received not invoiced |
| Stock ledger (every move valued, WAC) | Inventory, COGS, WIP entries; inventory GL = valuation report |
| Payroll runs (gross, deductions, net) | Salary journal |
| Month-end close (inventory) | Joined by the accounts period close |
| Company mail settings, AI assistant | Statements and reminders by email; CRM summaries and follow-ups |
| API (signed requests, keys, docs site) | Accounts and CRM endpoints the same way |
| ERP webhook pattern | Export to Tally or the client's other software, if they keep it |

New Django apps: `accounting` (books, AR, AP, bank, VAT, assets, budgets,
reports), `crm` (leads, opportunities, activities, quotations, tickets,
field sales). Both off until the platform owner enables them.

---

## 3. Key design decisions

| # | Decision | Recommended | Why |
|---|---|---|---|
| A1 | Book-keeping | Double-entry, one journal; every line a debit or a credit; entries balance or are refused | The only safe way; statements come from one source |
| A2 | Who writes the journal | One posting service (like `inventory.posting`); entries are never edited or deleted - a mistake is reversed | Auditable; the same rule the stock ledger follows |
| A3 | Automatic entries | Posting rules per document type, mapped to accounts the accountant chooses (settings), with sensible defaults | The accountant controls the chart; staff never pick accounts |
| A4 | Fiscal year | July–June (Bangladesh), configurable; monthly periods | NBR year; matches VAT months |
| A5 | Currency | BDT books; foreign currency on supplier bills / LCs with the rate of the day; exchange difference on payment | Imports (sugar, concentrate, packaging) are often in USD |
| A6 | Stock in the books | Perpetual: each stock move posts at its value; "goods received not invoiced" clears when the bill comes | The inventory GL always equals the valuation report (tested nightly) |
| A7 | Subledgers | Customer and supplier balances kept per invoice/bill (open items), with control accounts in the ledger | Ageing, statements, matching receipts to invoices |
| A8 | Cost centres | Branch and department on every line (from the document); project optional | Branch P&L without extra typing |
| A9 | Approvals | Manual journals and payments above a limit need a second person; nobody approves their own | Same rule as inventory |
| A10 | Periods | Accounts close per month; closing locks postings (inventory's close becomes one step of it) | One close, not two |
| A11 | VAT | Rates on items (already), Mushak registers from the documents; VDS/TDS rates in settings | Bangladesh rules, accountant confirms each rate |
| A12 | Other software | If the client keeps Tally, export vouchers (XML/CSV) instead of replacing it at first | Lower risk; choose in Phase 0 |
| C1 | One customer list | CRM accounts *are* `sales.Customer` (extended), prospects are leads until converted | No duplicates between CRM, Sales and Accounts |
| C2 | Pipeline | Configurable stages with a probability each; one pipeline per company to start | Simple; weighted forecast |
| C3 | Quotation → order | Quotation lines use the item master and price lists; accept = sales order draft | Reuses the Sales module completely |
| C4 | Tickets | Linked to customer, delivery, item and batch; SLA by priority | Traceability is the factory's strength |
| C5 | Activities | Calls, meetings, visits, tasks, notes; reminders by email/in-app | What sales teams actually use daily |
| C6 | Field sales | Visits with check-in time (and location from the phone app, optional) | Proof of visit without heavy GPS tracking |
| C7 | Commission | Rules per officer/product; earned on **paid** invoices; feeds payroll as an addition | Pay only on cash collected; payroll already exists |

---

## 4. Database design

All tables company-owned (`TenantOwned`), audited, branch where it matters.

### 4.1 The books (`accounting`)

| Table | Holds |
|---|---|
| `Account` | Chart of accounts: code, name, type (asset, liability, equity, income, expense), parent (tree), control account flag (AR/AP/inventory/bank), allow manual posting, active |
| `AccountingSettings` | Fiscal year start, currency, the posting map (which account for sales, COGS, inventory per item type, GRNI, VAT in/out, VDS/TDS payable, salary expense/payable, rounding, exchange difference …), approval limits |
| `FiscalYear`, `AccountingPeriod` | Years and months; open / closed |
| `JournalEntry` | Number (JV/RV/PV/SV…), date, period, source (document type + id, or manual), narration, status (draft, posted, reversed), posted by/at, approved by |
| `JournalLine` | Entry, account, debit, credit (one of them), branch, department, customer/supplier (for subledger), currency + foreign amount + rate, line narration |
| `PostingRule` | Document type → how lines are built (code, not data, but the accounts come from settings) |

### 4.2 Receivables and payables

| Table | Holds |
|---|---|
| `CustomerInvoice` link | Each `sales.SalesInvoice` becomes an open item (amount, VAT, due, balance) |
| `SupplierBill` + lines | The supplier's invoice: against GRNs (matched quantities and prices) or for services/expenses; VAT, VDS/TDS, due date, balance |
| `Receipt` + allocations | Money from a customer: method, bank/cash account, cheque details; allocated to invoices (partial allowed), advance if unallocated |
| `Payment` + allocations | Money to a supplier: same, allocated to bills; approval above the limit |
| `CreditNote` / `DebitNote` | Sales returns and price corrections (customer); purchase returns and claims (supplier) |
| `Cheque` | Received and issued cheques: number, bank, date, post-dated, status (in hand, deposited, cleared, bounced) |

### 4.3 Cash and bank

| Table | Holds |
|---|---|
| `BankAccount` | Bank, branch, account no., GL account, opening balance; bKash/Nagad/cash accounts too |
| `BankTransfer` | Between own accounts |
| `BankStatement` + lines | Imported CSV/Excel from the bank |
| `Reconciliation` | Matches of statement lines to journal lines; reconciled balance per date |
| `ExpenseClaim` (optional) | Petty cash / staff expense claims with receipts, approved and paid |

### 4.4 VAT and tax at source

| Table | Holds |
|---|---|
| `TaxRate` | VAT rates (15%, 10%, 7.5%, 5%, exempt, zero), VDS and TDS rates with their codes |
| `VatEntry` | One per taxable line (from bills, invoices, notes): base, VAT, rate, Mushak reference |
| `WithholdingEntry` | VDS/TDS deducted on a payment (or by a customer on our receipt): base, rate, amount, certificate (Mushak 6.6) number |
| `VatReturn` | A month's working (Mushak 9.1 figures), status, submitted reference |

### 4.5 Fixed assets and budgets

| Table | Holds |
|---|---|
| `AssetCategory` | Life, method (straight line / reducing balance), accounts |
| `Asset` | Code, name, category, branch, cost, date in use, supplier bill, residual value, status (in use, sold, scrapped) |
| `DepreciationRun` + lines | Monthly depreciation, posted as one entry |
| `Budget` + lines | Per fiscal year, account, branch/department, month |

### 4.6 CRM (`crm`)

| Table | Holds |
|---|---|
| `Customer` (extended, in `sales`) | + owner (sales officer), segment, source, lifecycle (customer, inactive, blocked), industry, website, rating |
| `Contact` | People at a customer or lead: name, designation, phone, WhatsApp, email, primary flag |
| `Lead` | Name, company, contact details, source (web, phone, email, AI inbox, fair, referral), owner, status (new, contacted, qualified, lost), score, notes; converted customer and opportunity |
| `Pipeline`, `Stage` | Stages with probability and order |
| `Opportunity` | Customer or lead, title, value, stage, expected close date, owner, competitor, lost reason |
| `Activity` | Type (call, meeting, visit, task, email, note), related record, due/at, done, outcome, reminder |
| `Quotation` + lines | Number, customer, validity, items with price list price, discount, VAT, terms; status (draft, sent, accepted, rejected, expired); sales order created |
| `Ticket` + messages | Customer, contact, type (complaint, request, return, query), priority, SLA due, status, owner; linked delivery, item, **batch**; resolution |
| `Territory`, `SalesTarget` | Areas and monthly targets per officer (amount, quantity per product group) |
| `Visit` | Planned and done visits: officer, customer, time in/out, location (optional), notes, order taken |
| `CommissionRule`, `CommissionStatement` | Rate rules; monthly statement from paid invoices, sent to payroll |
| `Campaign` (later) | Message to a segment (email/SMS/WhatsApp), responses |

---

## 5. Rules that must always hold (tested)

1. Every posted journal entry balances: total debit = total credit, to the paisa.
2. Posted entries are never changed or deleted; a reversal entry undoes one.
3. Nothing posts into a closed period.
4. The customer subledger total equals the receivables control account; the
   same for suppliers and payables (checked nightly, like `check_stock`).
5. The inventory accounts equal the stock valuation report at any date.
6. Goods received not invoiced equals the value of GRN lines without a bill.
7. A receipt or payment never allocates more than the invoice's balance.
8. A bank account's reconciled balance equals the statement's balance.
9. VAT in the registers equals VAT in the ledger for the month.
10. A converted lead points to exactly one customer; a customer is never
    duplicated by CRM (same phone/email warns).
11. An accepted quotation makes exactly one sales order.
12. Commission is earned only on paid invoice amounts, once.

---

## 6. Permissions (branch-level, granted like today)

| Code | Allows |
|---|---|
| `accounts.view` | See the books, ledgers and reports (no amounts hidden from them) |
| `accounts.journal` | Enter manual journal entries |
| `accounts.journal_approve` | Approve and post manual entries (not their own) |
| `accounts.receivable` | Receipts, credit notes, customer statements and reminders |
| `accounts.payable` | Supplier bills, payments (draft), debit notes |
| `accounts.payment_approve` | Approve payments (above the limit; not their own) |
| `accounts.bank` | Bank accounts, transfers, statements, reconciliation, cheques |
| `accounts.tax` | VAT and VDS/TDS registers, certificates, the monthly return |
| `accounts.assets` | Fixed assets and depreciation |
| `accounts.budget` | Budgets |
| `accounts.period_close` | Close months and the year |
| `crm.view` | See customers, leads, pipeline |
| `crm.leads` | Enter and work leads |
| `crm.sell` | Opportunities, activities, quotations, visits |
| `crm.quote_approve` | Approve quotations above a discount limit |
| `crm.support` | Tickets |
| `crm.manage` | Pipelines, stages, territories, targets, commission rules |

Owner and company admin hold everything; settings (chart of accounts, posting
map) are theirs and the accountant's.

---

## 7. Phases — step by step

Each phase: its own branch, tests for every rule it adds, docs, a "done
when" proven by a test, full suite green, then merged and pushed.

### Phase 0 — Decisions with the accountant and sales head (1 week)
- Chart of accounts (start from a Bangladesh manufacturing template, adjust),
  fiscal year, opening balances date, posting map, VAT/VDS/TDS rates,
  approval limits, Tally or not, which bank formats, CRM stages, ticket types,
  targets and commission rules. Answers to section 11.
- **Done when:** the decisions pack is signed and the chart of accounts is in
  an Excel template ready to import.

### Phase A1 — The books (2 weeks)
- `accounting` app, feature flag, permissions; chart of accounts (tree,
  import from Excel), fiscal years and periods, settings and posting map.
- Journal entries: manual entry with approval, posting service (balanced,
  immutable, reversal), numbering per type and year.
- Opening balances (trial balance import at the go-live date).
- Ledger page, account statement, trial balance.
- **Done when:** a manual entry posts only when balanced and approved by
  someone else, can only be reversed, and the trial balance balances.

### Phase A2 — Receivables (2 weeks)
- Sales invoices become open items; receipts (cash, cheque, bank, bKash)
  allocated to invoices, advances, credit notes from sales returns.
- Customer ledger and statement (PDF/email), ageing report, reminders.
- Credit limit check in Sales uses the real balance.
- **Done when:** an invoice, part payment and credit note leave the right
  balance and ageing, and the subledger equals the control account.

### Phase A3 — Payables (2 weeks)
- Supplier bills against GRNs (quantity and price match, differences
  flagged) or for services/expenses; payments with approval; debit notes from
  purchase returns; supplier statement and ageing.
- Goods received not invoiced report.
- **Done when:** GRN → bill → payment clears GRNI and the supplier balance, a
  price difference is flagged, and payments above the limit wait for approval.

### Phase A4 — Cash, bank and cheques (1.5 weeks)
- Bank and cash accounts (including bKash/Nagad), transfers, cheque register
  (post-dated, deposited, cleared, bounced), statement import (CSV/Excel),
  reconciliation with suggestions, cash book and bank book.
- **Done when:** a month's bank statement reconciles to the ledger and a
  bounced cheque reopens the invoice.

### Phase A5 — Automatic posting from everything built (2 weeks)
- Posting rules for: GRN, purchase return, store issue, material return,
  transfer, adjustment, count, opening stock, production consumption and
  output, delivery, sales return, sales invoice, payroll run; reversals follow
  their documents.
- Nightly checks: inventory GL = valuation, AR/AP = subledgers, GRNI.
- **Done when:** a full month of inventory, purchase, production, sales and
  payroll activity posts itself, and every nightly check reports zero.

### Phase A6 — VAT and tax at source (1.5 weeks)
- Tax rates, VAT entries from every document, Mushak 6.1 / 6.2 registers,
  Mushak 6.3 invoice layout (Sales already prints the invoice), VDS/TDS on
  payments and receipts with certificates (6.6), monthly return working (9.1),
  VAT payable entry.
- **Done when:** a month's registers equal the ledger's VAT accounts and the
  return figures add up.

### Phase A7 — Fixed assets and budgets (1.5 weeks)
- Asset register, categories, monthly depreciation run, disposal with gain
  or loss; budgets per account and cost centre, budget vs actual.
- **Done when:** a year's depreciation posts correctly and budget vs actual
  matches the ledger.

### Phase A8 — Statements, close and export (1.5 weeks)
- Profit and loss, balance sheet, cash flow (indirect), by branch and period,
  comparisons; month-end close (joins the inventory close), year-end close
  (profit to retained earnings, new year opened).
- Tally export (if chosen); dashboards (cash position, receivables,
  payables, sales vs target).
- **Done when:** statements tie to the trial balance at any date and a
  year-end close carries the right opening balances forward.

### Phase C1 — CRM foundation: customers, contacts, leads (1.5 weeks)
- `crm` app, feature flag, permissions; customer extension (owner, segment,
  source, lifecycle), contacts, leads (sources incl. the web form and AI
  inbox), duplicate warning, lead conversion.
- **Done when:** a lead from the web form is qualified and converted into
  one customer, contact and opportunity, with no duplicate created.

### Phase C2 — Pipeline and activities (1.5 weeks)
- Pipelines and stages, opportunities (kanban and list), activities with
  reminders, my day / my week, forecast by stage probability.
- **Done when:** opportunities move through stages, overdue activities
  remind their owner, and the forecast equals Σ value × probability.

### Phase C3 — Quotations to orders (1 week)
- Quotations from price lists, discount approval, PDF and email, accept →
  sales order draft, expiry.
- **Done when:** an accepted quotation becomes exactly one sales order with
  the same lines and prices.

### Phase C4 — Customer care (1.5 weeks)
- Tickets (complaint, request, return, query), SLA and escalation, link to
  delivery / item / batch, "which customers received this batch" (recall),
  resolution and customer reply by email.
- **Done when:** a complaint on a batch lists every customer who received
  it, and an overdue ticket escalates.

### Phase C5 — Field sales, targets and commission (1.5 weeks)
- Territories, visit plans and check-ins (phone app), targets per officer,
  achievement from invoices, commission statements on paid invoices sent to
  payroll as an addition.
- **Done when:** a month's commission equals the rules applied to paid
  invoices and appears once in payroll.

### Phase C6 — Customer 360, reports and AI (1 week)
- Customer 360 page; reports (pipeline, win/loss, lead sources, activity,
  ticket SLA, sales vs target); AI: customer summary, next-step suggestions,
  quotation draft from an email (reusing the AI assistant).
- **Done when:** one page shows a customer's orders, invoices, balance,
  tickets and activities, and the AI summary cites only real records.

### Phase X1 — API for both (1.5 weeks)
- Same conventions as the existing API: chart, journals, ledgers, AR/AP,
  receipts and payments, bank, reports; leads, opportunities, activities,
  quotations, tickets; docs pages and Postman.
- **Done when:** the documentation test covers every new endpoint and field.

### Phase X2 — Go-live (2 weeks)
- Chart and opening balances (trial balance at go-live), open customer and
  supplier items, bank balances and outstanding cheques, assets register,
  CRM import (customers' contacts, open opportunities); training per role;
  one month parallel with the current books; first month-end close together.
- **Done when:** the first closed month's statements match the accountant's.

**Total: about 26–27 weeks for one developer, 14–16 weeks for two** (Phase 0 1 week, Accounts
≈ 14 weeks, CRM ≈ 8, shared API and go-live ≈ 3.5). Accounts A1–A5 is the
minimum useful accounting; CRM C1–C3 the minimum useful CRM. Order
recommended: Phase 0 → A1 → A2 → A3 → A5 → C1 → C2 → C3 → A4 → A6 → A8 →
C4 → C5 → A7 → C6 → X1 → X2 (receivables and automatic posting first, because
they turn the built Sales/Purchase/Inventory into real accounting fastest).

---

## 8. Posting map (the automatic entries)

| Document | Debit | Credit |
|---|---|---|
| GRN (posted) | Inventory (by item type) | Goods received not invoiced (GRNI) |
| Supplier bill (against GRN) | GRNI; Input VAT | Supplier (AP); VDS/TDS payable if deducted |
| Supplier bill (expense) | Expense account; Input VAT | Supplier (AP) |
| Payment to supplier | Supplier (AP) | Bank / cash |
| Purchase return | Supplier (AP) or GRNI | Inventory |
| Store issue | Department consumption expense | Inventory |
| Material return | Inventory | Department consumption expense |
| Production consumption | Work in progress | Inventory (raw, packaging) |
| Production output | Inventory (finished goods) | Work in progress |
| Adjustment / count (loss) | Stock loss expense | Inventory |
| Adjustment / count (gain) | Inventory | Stock gain income |
| Delivery | Cost of goods sold | Inventory (finished goods / raw sold) |
| Sales invoice | Customer (AR) | Sales; Output VAT |
| Sales return | Sales returns; Output VAT; Inventory | Customer (AR); COGS |
| Receipt from customer | Bank / cash; VDS receivable if the customer deducts | Customer (AR) |
| Payroll run (finalised) | Salary expense (by branch/department) | Salary payable; deductions payable (PF, tax, loans) |
| Salary payment | Salary payable | Bank / cash |
| Depreciation | Depreciation expense | Accumulated depreciation |
| Reversal of any document | The same lines, swapped | |

The accountant chooses each account in settings; the defaults come from the
chart template.

---

## 9. Screens (menu)

**Accounts:** Dashboard · Journal entries · Chart of accounts · Receivables
(invoices, receipts, credit notes, statements, ageing) · Payables (bills,
payments, debit notes, ageing, GRNI) · Bank and cash (accounts, transfers,
cheques, statements, reconciliation) · VAT and tax (registers, VDS/TDS,
return) · Fixed assets · Budgets · Reports (trial balance, P&L, balance sheet,
cash flow, ledgers, cash/bank book) · Period close · Settings.

**CRM:** My day · Leads · Pipeline · Customers (360) · Activities ·
Quotations · Tickets · Visits · Targets and commission · Reports · Settings.

Each menu appears only to people with a matching permission, and only for a
company with the module on (same as Inventory).

---

## 10. Testing approach

- Every rule in section 5 has a test; the posting service is tested with
  worked examples (a month of documents, ledger and statements checked by
  hand).
- Nightly checks as management commands (`check_books`): AR/AP vs
  subledgers, inventory vs valuation, GRNI, unbalanced entries - exit 1 on
  any difference, like `check_stock`.
- Page tests for every form; API tests through the API only; the
  documentation test for every endpoint.
- The full suite green before every merge.

---

## 11. Questions for the client (before the phases that need them)

**Accountant (Phase 0 / A1):**
1. Keep Tally (export to it) or move the books here?
2. Chart of accounts: their current one, or our Bangladesh manufacturing template?
3. Fiscal year (July–June?) and the go-live date for opening balances.
4. Cost centres: branch only, or branch + department (+ project)?
5. Approval limits for payments and manual journals; who approves.

**Accountant (A3, A6):**
6. Match supplier bills to GRNs strictly (quantity and price) or with a tolerance?
7. VAT registration type, rates per item, Mushak forms they file, VDS/TDS rates in use.
8. Foreign purchases: LC handling, which costs go into inventory (freight, duty, insurance)?

**Sales head (C1–C5):**
9. Pipeline stages and what "qualified" means.
10. Lead sources to track; who owns leads.
11. Ticket types and response times (SLA).
12. Territories, targets and commission rules; paid on invoice or on payment?
13. Field app needed in the first release, or later?

---

## 12. Risks and how we handle them

| Risk | Handling |
|---|---|
| Wrong accounts in the posting map make wrong statements | Accountant signs the map; nightly checks; a month's parallel run |
| Opening balances do not match the old books | Import a trial balance; reconcile AR/AP open items to it before go-live |
| Bank formats differ per bank | Configurable column mapping; manual match always possible |
| VAT rules change (NBR circulars) | Rates and forms in settings, not code; the accountant updates them |
| Two customer lists drifting apart | One table (`sales.Customer`) for Sales, CRM and Accounts |
| Sales team does not use the CRM | Phone-friendly pages, "my day" view, reminders, quick logging; start with quotations they need anyway |
| Scope creep (payroll accounting, consolidation, multi-currency books) | Out of scope for the first release; listed as later |

**Later (not in this plan):** multi-company consolidation, multi-currency
books, costing with labour and overhead, credit card / payment gateway
collection, WhatsApp Business messaging, marketing automation.
