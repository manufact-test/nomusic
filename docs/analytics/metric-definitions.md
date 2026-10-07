# Metric definitions

Version: `metrics.v1-draft`  
Timezone: UTC  
Status: admin-dashboard contract; no dashboard is implemented in Stage 1.

| Metric | Versioned definition |
|---|---|
| New users | Distinct accounts whose first valid `account_registered` event falls inside the selected period. |
| Active users | Distinct entitled accounts with at least one accepted session or replacement event inside the period. Report DAU, WAU and MAU separately. |
| Returning users | Active users whose first valid activity occurred before the selected period. |
| First-period paid | Accounts whose first settled non-zero subscription payment occurred in the period and was not refunded within the reporting window. |
| Renewed paid | Accounts with a settled recurring payment after their first paid period. Count an account once per reporting period; retain transaction count separately. |
| Churned | Previously paid accounts whose entitlement expired in the period and was not restored inside the agreed grace window. Cancellation alone is not churn. |
| Full-price paid | Paid accounts whose settled period had no promo, referral or manual discount allocation. |
| Discounted paid | Paid accounts whose settled period contains a non-zero discount allocation. Segment by `promo`, `referral`, `reward` and `manual`. |
| Trial conversion | First-period paid accounts divided by trials whose decision window ended in the same cohort window. |
| Referral conversion | Qualified referred accounts divided by valid referral landings for the same qualification version. |

## Reconciliation rules

- Money uses integer minor units and an explicit ISO currency; cross-currency totals are never added without a named conversion policy.
- Refunds, disputes and chargebacks remain separate dimensions and adjust net revenue, not historical user-state events.
- Every dashboard cell records the metric definition version and data freshness timestamp.
- Admin filters include cohort, client/platform, acquisition channel, price type and discount source.
- The billing ledger is authoritative for payments; the entitlement ledger is authoritative for current access.
