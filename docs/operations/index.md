# Operations Runbook

[→ Monitoring, Analytics & Logs](monitoring_analytics_logs.md)

## Monitoring & Alerting

### Health Checks

The system provides several health check endpoints:

- `/health` - Basic health check
- `/health/detailed` - Detailed system status
- `/metrics` - Prometheus metrics

### Key Metrics to Monitor

- API response time (target: <200ms P95)
- Database connection pool
- Memory usage
- Container health
- Disk space
- Error rates

## Incident Response

### Common Issues

#### 1. High API Response Times

**Symptoms:**
- API responses >500ms
- User complaints about slow loading

**Investigation:**
1. Check database performance
2. Review API logs
3. Check Redis cache hit rates
4. Monitor container resources

**Resolution:**
1. Restart slow services
2. Clear cache if needed
3. Scale containers if necessary

#### 2. Database Connection Issues

**Symptoms:**
- Connection timeouts
- "Too many connections" errors

**Investigation:**
1. Check connection pool status
2. Review database logs
3. Monitor active connections

**Resolution:**
1. Restart database connections
2. Increase connection pool size
3. Kill long-running queries

#### 3. Container Issues

**Symptoms:**
- Containers not starting
- OOMKilled errors
- High CPU usage

**Investigation:**
1. Check container logs
2. Monitor resource usage
3. Review Docker daemon logs

**Resolution:**
1. Restart containers
2. Increase resource limits
3. Check for memory leaks

## Backup & Recovery

### Database Backups

Automated backups run daily at 2 AM UTC:

```bash
# Manual backup
docker exec wakedock_postgres pg_dump -U postgres wakedock > backup.sql

# Restore
docker exec -i wakedock_postgres psql -U postgres wakedock < backup.sql
```

### Configuration Backups

Configuration is stored in Git and backed up automatically.

## Security Procedures

### Security Incident Response

1. **Immediate Response:**
   - Isolate affected systems
   - Preserve evidence
   - Notify security team

2. **Investigation:**
   - Review security logs
   - Check access patterns
   - Analyze attack vectors

3. **Recovery:**
   - Patch vulnerabilities
   - Update security policies
   - Monitor for further activity

### Regular Security Tasks

- Weekly security scans
- Monthly dependency updates
- Quarterly penetration testing
- Annual security audits

## Maintenance Windows

### Scheduled Maintenance

- **Monthly:** Third Saturday, 2-4 AM UTC
- **Quarterly:** Security updates and patches
- **Annually:** Major version upgrades

### Maintenance Procedures

1. **Pre-maintenance:**
   - Notify users
   - Backup systems
   - Prepare rollback plan

2. **During maintenance:**
   - Follow maintenance checklist
   - Monitor system health
   - Document changes

3. **Post-maintenance:**
   - Verify system health
   - Update documentation
   - Notify completion

## Contact Information

- **On-call Engineer:** [Pager/Phone]
- **Security Team:** [Email]
- **Database Admin:** [Email]
- **DevOps Team:** [Email]
