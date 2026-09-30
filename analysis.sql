-- SQLite. Each input row is one series-quarter, no join fan-out.
SELECT quarter,
       SUM(revenue) AS revenue,
       SUM(delivered_cost) AS delivered_cost,
       SUM(participation) AS participation,
       SUM(revenue-delivered_cost-participation) AS contribution,
       SUM(production_cash) AS production_cash,
       SUM(receipts) AS receipts,
       SUM(participation_cash) AS participation_cash,
       SUM(receipts-production_cash-participation_cash) AS net_cash
FROM detail
GROUP BY quarter
ORDER BY quarter;
