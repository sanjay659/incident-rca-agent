# Runbook: Circuit Breaker Failures

## Symptom
- Downstream service calls failing with TimeoutException
- Circuit breaker state changes to OPEN
- Connection pool exhaustion warnings
- HTTP 503 errors returned to clients

## Common Root Causes
1. **Recent deployment to downstream service** - New version introduced latency or bugs
2. **Resource exhaustion on downstream service** - CPU/memory spike causing slow responses
3. **Network issues** - DNS resolution failures, firewall rule changes, NSG updates
4. **Database connection leak** in downstream service causing thread starvation

## Diagnosis Steps
1. Check if there was a recent deployment to the failing downstream service
2. Check pod health and resource usage of the downstream service
3. Verify network connectivity between services (kubectl exec ping/curl tests)
4. Check downstream service logs for errors
5. Review circuit breaker configuration (timeout thresholds, failure count)

## Remediation
- If caused by bad deployment: **Rollback to previous version immediately**
- If resource exhaustion: Scale up pods (kubectl scale deployment) or increase resource limits
- If network: Check NSG rules, DNS resolution, service mesh configuration
- If connection leak: Restart downstream service pods as immediate fix, then patch

## Escalation
- P1: Engage on-call SRE + service owner within 15 minutes
- P2: Notify service owner, SRE reviews within 1 hour
- Rollback authority: On-call SRE can rollback without approval for P1
