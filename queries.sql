-- Core queries are embedded in run_project.py (section 2). Example:
SELECT zone, ROUND(100.0*AVG(sla_breach),1) AS breach_pct, COUNT(*) n FROM orders GROUP BY zone ORDER BY breach_pct DESC;
