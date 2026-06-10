# Past Incident: INC-2025-623 - Order Service Database Deadlocks

## Summary
Order service experienced intermittent 500 errors for 2 hours due to database deadlocks during end-of-month batch processing.

## Timeline
- 14:00 - Monthly order reconciliation batch job started
- 14:15 - First deadlock warnings in order-service logs
- 14:30 - Connection pool reaching 90% capacity
- 14:45 - P2 alert triggered (P95 latency > 8s)
- 15:00 - DBA identified batch job as cause of deadlocks
- 15:15 - Batch job paused, deadlocks cleared within 5 minutes
- 16:00 - Batch job rescheduled to run during off-peak hours (02:00 UTC)

## Root Cause
Monthly reconciliation batch job was performing large UPDATE operations on the orders table with SERIALIZABLE isolation level, conflicting with real-time order processing transactions. The batch job locked thousands of rows, causing real-time queries to wait and eventually deadlock.

## Fix Applied
- Immediate: Paused batch job
- Permanent: Changed batch job to use READ COMMITTED SNAPSHOT isolation, process in smaller batches of 500 rows, scheduled to 02:00 UTC off-peak window

## Lessons Learned
- Batch jobs must use appropriate isolation levels (never SERIALIZABLE for bulk operations)
- Batch processing should be scheduled during off-peak hours
- Connection pool alerts should trigger at 80%, not 95%
- Consider read replicas for reporting/reconciliation queries
