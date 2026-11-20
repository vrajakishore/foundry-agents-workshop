# Woodgrove Finance — Collections and Early-Warning Policy

Document ID: WFL-POL-COL-07 · Version 3.2 · Owner: Head of Retail Collections · Effective: 1 April 2026

> Fictional document for a Microsoft Foundry workshop. Woodgrove Finance is not a real company.
> This document is not legal or regulatory advice.

## 1. Purpose and scope

This policy tells Woodgrove Finance staff, collection agencies and AI assistants how to find early signs of repayment stress and how to respond. It applies to all retail loans: home loans, loans against property, used car loans, unsecured business loans and personal loans.

## 2. Early-warning signals and limits

The early-warning system checks four signals for every active account each month.

| Signal | Meaning | Limit (maximum) |
| --- | --- | --- |
| `days_past_due` | Days since the oldest unpaid EMI was due | 0 |
| `emi_bounces_6m` | EMI payment mandates that bounced in the last 6 months | 1 |
| `bureau_score_drop_90d` | Fall in the credit bureau score over the last 90 days, in points | 50 for home loans, loans against property and used car loans. 40 for unsecured business loans and personal loans |
| `credit_enquiries_90d` | New credit enquiries from other lenders in the last 90 days | 3 |

A value that is equal to the limit is within the limit.

### 2.1 Early-warning status

| Status | Rule |
| --- | --- |
| **NORMAL** | Every signal is at or below its limit. |
| **WATCH** | One or two signals are above their limits, and `days_past_due` is 30 or less. |
| **CRITICAL** | `days_past_due` is more than 30, **or** three or more signals are above their limits. |

Apply the rules exactly. Do not use any other information to set the status.

## 3. Response by pattern

Find the pattern that matches the account. Use the procedure ID in all case notes.

| Pattern | Procedure | Urgency | Owner |
| --- | --- | --- | --- |
| One bounce and `days_past_due` of 7 or less | **COL-PRC-01** Payment reminder. Send template TPL-REM-01 by SMS or WhatsApp. | MONITOR | Collections operations |
| Two or more bounces, bureau score stable | **COL-PRC-02** Mandate check. Confirm that the NACH mandate and the bank account are still valid. Re-register the mandate if needed. | WITHIN 7 DAYS | Branch operations |
| Bureau score drop and new credit enquiries, no days past due | **COL-PRC-03** Early outreach call. Use call script TPL-CALL-03. Do not offer new credit or a top-up. Flag the account "no top-up" for 90 days. | WITHIN 7 DAYS | Relationship manager |
| `days_past_due` from 1 to 30 with bounces | **COL-PRC-04** Payment discussion. Find the reason. Agree a promise-to-pay date. If the borrower reports a loss of income, start a payment plan assessment (see WFL-GDL-RS-02). | WITHIN 7 DAYS | Collections officer |
| Status CRITICAL | **COL-PRC-05** Priority resolution. A collections officer contacts the borrower within 24 hours. Inform the branch collections manager. Assess the account for a payment plan (see WFL-GDL-RS-02). If there is no contact in 3 days, arrange a field visit with an appointment. | IMMEDIATE | Collections officer and branch collections manager |

Urgency levels:

- **IMMEDIATE**: first contact within 24 hours.
- **WITHIN 7 DAYS**: first contact within 7 calendar days.
- **MONITOR**: no contact needed. Check the account again in the next monthly scan.

## 4. Conduct rules

All staff, agencies and AI assistants must follow these rules. There are no exceptions.

1. Contact only the borrower, a co-borrower or a guarantor on the loan.
2. Never discuss the loan with the borrower's employer, neighbours, friends or family members who are not on the loan.
3. Call or visit only between 08:00 and 19:00 local time.
4. State your name and that you represent Woodgrove Finance at the start of every contact.
5. Never threaten, shame or use abusive language. Never suggest police action or legal action that has not been approved by the Legal team.
6. Use the borrower's preferred language where possible.
7. Record every contact in the collections system within 24 hours.

## 5. Approvals

Staff and AI assistants can **recommend** a waiver or a payment plan. Only the approvers below can **approve** one.

| Request | Approver |
| --- | --- |
| Waiver of bounce charges or penal charges up to ₹5,000 | Branch collections manager |
| Waiver from ₹5,001 to ₹50,000 | Zonal collections head |
| Waiver above ₹50,000, or any waiver of interest or principal | Credit risk committee |
| Payment plan or restructuring | As set in WFL-GDL-RS-02 |
| Legal notice | Legal team only, and only after 90 days past due |

## 6. Customer data

1. Share account details only with the verified borrower, co-borrower or guarantor.
2. Show only the last four characters of PAN, Aadhaar or bank account numbers. Never write a full ID number in case notes, chat messages or prompts to AI assistants.
3. Collect only the data that the task needs.

## 7. Fair treatment

Early-warning status, urgency and the recommended action must depend only on the signals in section 2 and the facts of the loan. Never use religion, caste, gender, age, marital status, disability, place of origin or language to make a decision or to change its priority.

## 8. Complaints

The borrower can complain to the branch, by email or through the grievance redressal officer. Woodgrove Finance acknowledges every complaint within 2 working days and resolves it within 30 days.
