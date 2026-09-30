# Model guide and review controls

## Input contract

`data/series.csv` has one row per fictional series. IDs are unique and nonempty. Fees, costs and Q1 cash are in USD millions. `budget_delivery_q` and `forecast_delivery_q` are integers 1–5: FY26 Q1–Q4 then FY27 Q1. Quarter 6 is reserved for collection. The committed actual cutoff is FY26 Q1; do not roll the cutoff simply by relabeling headers.

`budget_fee` / `forecast_fee` are total season license fees. `budget_cost` / `forecast_cost` are total production costs, with EAC meaning estimate at completion. `q1_cash_spend` is already-paid cash and cannot exceed either cost estimate. `participation_rate` is a simplified percentage of revenue, not a real collective-bargaining or talent contract calculation.

## Calculation order

For each case, series and quarter:

1. Recognize all fee revenue and the modeled production cost in the delivery quarter. Participation expense = fee × participation rate.
2. Keep Q1 production cash fixed. Allocate remaining cost equally across Q2 through delivery. This is an illustrative forecast allocation, not a source-derived production schedule.
3. Collect the fee one quarter after delivery and pay participation on collection. No customer advances, opening working capital, interest, taxes, overhead or foreign currency effects are modeled.
4. Aggregate the unique series-quarter rows in SQLite using `analysis.sql`.
5. Roll forward content asset proxy = prior balance + production spend − delivered cost; receivables = prior balance + revenue − cash receipts; participation payable = prior balance + expense − cash paid.
6. Reconcile cash = contribution − change in asset − change in receivables + change in payable.

The contribution bridge changes delivery timing at budget economics, then fee at the unchanged participation rate, then production cost. Changing the order would change interaction allocation; the chosen order is explicit and tested.

## Workbook map

- **Inputs D8:I15:** six series, with units in the row labels. D8:I9 are delivery quarters; D10:I13 are fees and costs; D14:I14 are closed-quarter cash; D15:I15 are participation rates.
- **Detail:** 72 case-series-quarter records, with visible formulas.
- **Forecast D:I:** six quarters; rows 25 and 31 are terminal reconciliation checks. They never feed financial outputs. Rows 33–35 report the headline outputs.
- **Inputs D33:** closed-delivery consistency; D34 checks numeric completeness. Spreadsheet cells are not access-controlled or protected. A reviewer must preserve the closed records; the Python validator rejects inconsistent Q1 economics.

Blue indicates editable assumptions, green cross-sheet links, and black same-sheet calculations. A dash represents numerical zero. Do not use incomplete or invalid input sets merely because a formula returns a number. The Python validator adds domain checks beyond workbook input controls.

## Review evidence

| Control | Risk addressed | Review evidence |
|---|---|---|
| Unique IDs and quarter bounds | Duplicate counting / out-of-horizon deliveries | Python validation and tests |
| EAC ≥ cash already spent | Impossible production cash forecast | Python validation |
| Closed Q1 preserved | Rewriting actuals to improve forecast | Input check, rejection test, perturbation test |
| Cash and variance reconciliation | Misstated drivers / timing | Six-quarter zero residuals |
| End-of-horizon balance runoff | Receipts dropped beyond year-end | Zero assets, receivables and participation payable |

These are portfolio model controls, not evidence of a Sony SOX control's design or operating effectiveness. For business use, add sourced contract terms, approval history, monthly timing, actuals import, documented recognition judgments, and independent Finance review.
