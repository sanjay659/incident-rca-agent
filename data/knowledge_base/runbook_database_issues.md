# Runbook: Database Connection Pool Exhaustion

## Symptom
- "Connection pool exhausted" or "Connection timeout expired" errors
- High active connection count approaching pool maximum
- Slow query warnings in logs
- Deadlock detection messages
- Elevated P95/P99 latency

## Common Root Causes
1. **Missing database indexes** - Queries doing full table scans, holding connections longer
2. **Deadlocks** - Multiple transactions competing for same rows
3. **Connection leak** - Application not properly closing/returning connections
4. **Undersized database tier** - DTU/vCore limits reached under load
5. **Sudden traffic spike** - More requests than connection pool can handle
6. **Long-running queries** - Batch jobs or reports running during peak hours

## Diagnosis Steps
1. Check DTU/vCore usage in Azure Portal (>90% indicates undersized tier)
2. Review slow query logs - identify queries taking >5 seconds
3. Check for missing indexes using Azure SQL recommendations
4. Look for deadlock graphs in SQL Server logs
5. Verify connection pool settings (min/max size, timeout values)
6. Check if batch jobs or reports are running during the incident window

## Remediation
- **Immediate**: Kill long-running queries blocking others (ALTER DATABASE SET SINGLE_USER with rollback)
- **If undersized**: Scale up database tier (S3→S4 or switch to Premium)
- **If missing indexes**: Apply recommended indexes from Azure SQL advisor
- **If deadlocks**: Review transaction isolation levels, optimize query order
- **If connection leak**: Restart application pods, then fix connection disposal in code
- **If traffic spike**: Enable auto-scaling on application tier, add read replicas

## Escalation
- P1: DBA + Service Owner + SRE within 15 minutes
- P2: DBA reviews within 1 hour, service owner notified
- Database scaling requires approval from team lead (cost impact)
