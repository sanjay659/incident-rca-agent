# Past Incident: INC-2025-847 - Payment Service Outage due to Fraud Detection Deployment

## Summary
Payment service experienced 35 minutes of downtime after fraud-detection-service v2.3.0 was deployed.
The new version had a memory leak that caused response times to degrade from 200ms to 15s within 20 minutes of deployment.

## Timeline
- 09:00 - fraud-detection-service v2.3.0 deployed via CI pipeline
- 09:15 - First slow response warnings in payment-service logs
- 09:20 - Circuit breaker opened for fraud-detection-service
- 09:22 - Payment processing error rate hit 30%
- 09:25 - P1 alert triggered
- 09:30 - On-call SRE identified recent deployment as probable cause
- 09:32 - Rollback initiated to v2.2.9
- 09:35 - fraud-detection-service v2.2.9 deployed, circuit breaker reset
- 09:40 - Payment service fully recovered

## Root Cause
Memory leak in fraud-detection-service v2.3.0 - new ML model loading code was creating duplicate model instances on each request instead of reusing a singleton. Memory usage grew from 512MB to 3.8GB in 20 minutes, causing garbage collection pauses and extreme latency.

## Fix Applied
- Immediate: Rollback to v2.2.9
- Permanent: Fixed singleton pattern in model loader (PR #1247), added memory usage alerts at 80% threshold

## Lessons Learned
- Deployment to downstream services should trigger automated canary testing
- Circuit breaker thresholds should be tuned per-service (fraud-detection needs 3s timeout, not 5s)
- Memory usage monitoring was missing for fraud-detection-service
