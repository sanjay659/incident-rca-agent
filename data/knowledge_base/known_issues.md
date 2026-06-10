# Known Issues Database

## KI-001: Fraud Detection Service - Memory Leak in ML Model Loader
- **Status**: Fixed in v2.3.1
- **Affected Versions**: v2.3.0
- **Symptom**: Memory usage grows continuously, response times degrade after 15-20 minutes
- **Workaround**: Rollback to v2.2.9 or restart pods every 15 minutes
- **Fix**: Upgrade to v2.3.1 (singleton pattern for model instances)

## KI-002: Payment Service - Connection Pool Sizing
- **Status**: Open
- **Affected Versions**: All
- **Symptom**: Under high load (>1000 TPS), connection pool to fraud-detection exhausts
- **Workaround**: Scale payment-service to 8+ pods to distribute connections
- **Fix**: Planned - implement connection pooling with resilience4j (Sprint 24)

## KI-003: Order Service - Missing Index on orders.status Column
- **Status**: Fixed in DB migration v45
- **Affected Versions**: DB schema < v45
- **Symptom**: Queries filtering by order status take 10-15s instead of <100ms
- **Workaround**: None (must apply index)
- **Fix**: Run migration v45: CREATE INDEX idx_orders_status ON orders(status) INCLUDE (created_at, total_amount)

## KI-004: Azure SQL S3 Tier - DTU Throttling During Peak Hours
- **Status**: Open
- **Affected Versions**: All services using shared SQL instance
- **Symptom**: DTU usage hits 100% between 09:00-11:00 UTC, causing connection timeouts
- **Workaround**: Temporarily scale to S4 during peak hours
- **Fix**: Planned migration to Premium P1 tier (Budget approval pending)
