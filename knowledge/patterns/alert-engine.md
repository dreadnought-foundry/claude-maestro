# Recipe: Alert Engine Configuration

**Category**: pattern
**Version**: 1.0
**Last Updated**: 2025-12-14
**Sprints**: Sprint 7 (initial implementation)
**ADRs**: [ADR-013: Rule-Based Alert Engine with Escalation](../../architecture/decisions/ADR-013-alert-engine-architecture.md)

## Context

**When to use this recipe:**
- You need to configure alert rules for pipeline monitoring (CP readings, anomaly growth, environmental conditions)
- You want to set up escalation chains for unacknowledged alerts
- You need to prevent alert fatigue through deduplication
- You're integrating new data sources that require monitoring
- You need multi-channel notification delivery (email, SMS, Slack, push)

**When NOT to use this recipe:**
- For simple one-off notifications (use direct email/notification instead)
- For logging or audit trails (use observability module)
- For user-initiated notifications (use notification service directly)
- For real-time streaming alerts at high volume (consider event-driven architecture with message queues)

## Ingredients

Before starting, ensure you have:

- [ ] Database models loaded (`corrdata.db.alert_models`)
- [ ] At least one notification channel configured (`corrdata.alerting.channels`)
- [ ] Asset UUIDs for testing rule evaluation
- [ ] Understanding of the asset type and measurement types you're monitoring
- [ ] Appropriate thresholds defined (consult domain experts for CP, anomaly, etc.)

## Steps

### Step 1: Define Alert Rule

Create an alert rule in the database with appropriate trigger configuration.

```python
from corrdata.db.alert_models import (
    AlertRule,
    AlertCategory,
    AlertPriority,
    TriggerType,
)
from uuid import uuid4

# Example: CP reading below protection threshold
rule = AlertRule(
    uuid=uuid4(),
    name="CP Below Protection Threshold",
    description="Alert when pipe-to-soil potential exceeds -850mV (insufficient protection)",
    category=AlertCategory.CP,
    priority=AlertPriority.HIGH,
    trigger_type=TriggerType.THRESHOLD,
    trigger_config={
        "measurement_type": "pipe_to_soil_potential",
        "operator": "greater_than",  # More positive than -850mV is bad
        "threshold": -850,
        "consecutive_readings": 1,  # Alert immediately
    },
    enabled=True,
    cooldown_minutes=240,  # Don't repeat alert for 4 hours
    escalation_minutes=30,  # Escalate if not acknowledged in 30 min
)

session.add(rule)
await session.commit()
```

**Expected outcome**: Rule is persisted and will be evaluated by the alert engine.

### Step 2: Configure Rule Type-Specific Parameters

Different trigger types require different configuration keys.

#### Threshold Rules

```python
# Simple threshold
trigger_config = {
    "measurement_type": "pipe_to_soil_potential",
    "operator": "greater_than",  # Options: greater_than, less_than, equals
    "threshold": -850,
    "consecutive_readings": 1,
}

# Multiple consecutive readings required
trigger_config = {
    "measurement_type": "temperature",
    "operator": "greater_than",
    "threshold": 150,  # Fahrenheit
    "consecutive_readings": 3,  # Must see 3 consecutive high readings
}
```

#### Trend Rules

```python
# Anomaly growth rate acceleration
trigger_config = {
    "measurement_type": "wall_loss_percentage",
    "direction": "increasing",  # Options: increasing, decreasing
    "threshold": 0.05,  # 5% wall loss per year
    "min_samples": 3,  # Need at least 3 data points
    "window_days": 90,  # Look at last 90 days
}
```

#### Absence Rules

```python
# Missing readings from test station
trigger_config = {
    "asset_type": "test_station",
    "measurement_type": "pipe_to_soil_potential",
    "max_age_hours": 2160,  # 90 days
}
```

#### Pattern Rules

```python
# Complex multi-condition pattern
trigger_config = {
    "conditions": [
        {"field": "risk_score", "operator": "greater_than", "value": 70},
        {"field": "cp_reading", "operator": "greater_than", "value": -850},
        {"field": "ili_anomaly_count", "operator": "greater_than", "value": 0},
    ],
    "match_all": True,  # All conditions must be met (AND logic)
}
```

**Expected outcome**: Rules trigger correctly based on their configured conditions.

### Step 3: Set Up Deduplication

Configure cooldown periods to prevent alert storms.

```python
from corrdata.alerting.engine import AlertEngine

engine = AlertEngine(session)

# The engine automatically checks for active alerts
# within the cooldown window before creating new ones
new_alerts = await engine.evaluate_rules_for_asset(
    asset_uuid=asset_uuid,
    categories=[AlertCategory.CP]  # Optional: limit to specific categories
)

# Behind the scenes, the engine calls:
# await engine._has_active_alert(rule.uuid, asset_uuid)
# which checks for existing alerts within cooldown_minutes
```

**Deduplication logic** (from `/Volumes/Foundry/Development/CorrData/POC/src/corrdata/alerting/engine.py`):

```python
async def _has_active_alert(
    self,
    rule_uuid: UUID,
    asset_uuid: UUID,
) -> bool:
    """Check if there's already an active alert for this rule/asset."""
    rule = await self.session.get(AlertRule, rule_uuid)
    if not rule:
        return False

    cutoff = datetime.now(UTC) - timedelta(minutes=rule.cooldown_minutes)

    stmt = (
        select(Alert)
        .where(Alert.rule_uuid == rule_uuid)
        .where(Alert.asset_uuid == asset_uuid)
        .where(Alert.created_at > cutoff)
        .where(Alert.status.in_([AlertStatus.ACTIVE, AlertStatus.ESCALATED]))
    )

    result = await self.session.execute(stmt)
    return result.scalar_one_or_none() is not None
```

**Expected outcome**: Duplicate alerts are suppressed within the cooldown window.

### Step 4: Configure Escalation Logic

Set up escalation chains for unacknowledged alerts.

```python
from corrdata.db.alert_models import AlertEscalation

# Define escalation chain
escalation = AlertEscalation(
    uuid=uuid4(),
    rule_uuid=rule.uuid,
    level=1,  # First escalation
    delay_minutes=30,
    channels=[ChannelType.EMAIL, ChannelType.SMS],
    recipient_role="shift_supervisor",  # Or specific user IDs
)

session.add(escalation)

# Second level escalation
escalation_2 = AlertEscalation(
    uuid=uuid4(),
    rule_uuid=rule.uuid,
    level=2,
    delay_minutes=60,
    channels=[ChannelType.SMS, ChannelType.SLACK],
    recipient_role="operations_manager",
)

session.add(escalation_2)
await session.commit()
```

**Run escalation check** (typically via scheduled job):

```python
from corrdata.alerting.engine import AlertEngine
from corrdata.alerting.channels import NotificationDispatcher

engine = AlertEngine(session)
dispatcher = NotificationDispatcher()

# Check for alerts that need escalation
unacknowledged = await engine.check_escalations()

for alert in unacknowledged:
    # Get escalation level
    escalation = await engine._get_escalation_for_alert(alert)

    # Send notifications
    await dispatcher.send(
        channels=escalation.channels,
        recipients=await engine._resolve_recipients(escalation.recipient_role),
        template="escalation",
        context={"alert": alert, "level": escalation.level}
    )
```

**Expected outcome**: Unacknowledged alerts escalate to higher levels after configured delays.

### Step 5: Configure Multi-Channel Delivery

Set up notification channels for alert delivery.

```python
from corrdata.alerting.channels import (
    NotificationDispatcher,
    EmailChannel,
    SMSChannel,
    SlackChannel,
    PushChannel,
)

# Initialize dispatcher with available channels
dispatcher = NotificationDispatcher()

# Channels are registered automatically (see /Volumes/Foundry/Development/CorrData/POC/src/corrdata/alerting/channels.py)
# But you can customize them:

class CustomEmailChannel(EmailChannel):
    async def send(self, recipients: list[str], template: str, context: dict):
        # Custom email logic (e.g., SendGrid, SES)
        message = self._render_template(template, context)
        # Send via your email service
        pass

# Override default channel
dispatcher.channels["email"] = CustomEmailChannel()

# Send notification across multiple channels
await dispatcher.send(
    channels=["email", "sms", "slack"],
    recipients=["user@example.com", "+15551234567", "#alerts"],
    template="critical_alert",
    context={
        "alert": alert,
        "asset": asset,
        "measurement": measurement,
    }
)
```

**Expected outcome**: Alerts are delivered through configured notification channels.

## Code Examples

### Complete Alert Rule Creation

```python
from corrdata.db.alert_models import (
    AlertRule,
    AlertCategory,
    AlertPriority,
    TriggerType,
    AlertEscalation,
    ChannelType,
)
from uuid import uuid4

async def create_cp_monitoring_rule(session: AsyncSession):
    """Create a complete CP monitoring alert with escalation."""

    # Create the rule
    rule = AlertRule(
        uuid=uuid4(),
        name="CP Below Protection Threshold",
        description="Critical: Pipe-to-soil potential exceeds -850mV",
        category=AlertCategory.CP,
        priority=AlertPriority.CRITICAL,
        trigger_type=TriggerType.THRESHOLD,
        trigger_config={
            "measurement_type": "pipe_to_soil_potential",
            "operator": "greater_than",
            "threshold": -850,
            "consecutive_readings": 1,
        },
        enabled=True,
        cooldown_minutes=240,  # 4 hours
        escalation_minutes=30,  # Escalate after 30 min
    )
    session.add(rule)

    # Add escalation levels
    escalations = [
        AlertEscalation(
            uuid=uuid4(),
            rule_uuid=rule.uuid,
            level=1,
            delay_minutes=30,
            channels=[ChannelType.EMAIL, ChannelType.PUSH],
            recipient_role="field_technician",
        ),
        AlertEscalation(
            uuid=uuid4(),
            rule_uuid=rule.uuid,
            level=2,
            delay_minutes=60,
            channels=[ChannelType.EMAIL, ChannelType.SMS],
            recipient_role="shift_supervisor",
        ),
        AlertEscalation(
            uuid=uuid4(),
            rule_uuid=rule.uuid,
            level=3,
            delay_minutes=120,
            channels=[ChannelType.SMS, ChannelType.SLACK],
            recipient_role="operations_manager",
        ),
    ]

    for esc in escalations:
        session.add(esc)

    await session.commit()
    return rule
```

### Evaluating Rules After New Measurement

```python
from corrdata.alerting.engine import AlertEngine
from corrdata.db.models import Measurement

async def process_new_measurement(
    session: AsyncSession,
    measurement: Measurement
) -> list[Alert]:
    """Process new measurement and trigger alerts if needed."""

    engine = AlertEngine(session)

    # Evaluate all rules for the asset
    new_alerts = await engine.evaluate_rules_for_asset(
        asset_uuid=measurement.asset_uuid,
        # Optionally filter by measurement category
        categories=[AlertCategory.CP] if measurement.measurement_type.startswith("pipe_to_soil") else None
    )

    if new_alerts:
        # Send notifications for new alerts
        dispatcher = NotificationDispatcher()
        for alert in new_alerts:
            await dispatcher.send_alert_notification(alert)

    return new_alerts
```

### Scheduled Escalation Check

```python
from corrdata.alerting.engine import AlertEngine
from corrdata.alerting.channels import NotificationDispatcher

async def check_alert_escalations(session: AsyncSession):
    """Scheduled job to check for alerts needing escalation."""

    engine = AlertEngine(session)
    dispatcher = NotificationDispatcher()

    # Find all unacknowledged alerts past escalation threshold
    alerts_to_escalate = await engine.get_alerts_needing_escalation()

    for alert in alerts_to_escalate:
        # Update alert status
        alert.status = AlertStatus.ESCALATED

        # Get next escalation level
        escalation = await engine._get_next_escalation_level(alert)

        if escalation:
            # Send escalation notifications
            recipients = await engine._resolve_recipients(escalation.recipient_role)
            await dispatcher.send(
                channels=escalation.channels,
                recipients=recipients,
                template="escalation",
                context={
                    "alert": alert,
                    "level": escalation.level,
                    "previous_level": escalation.level - 1,
                }
            )

    await session.commit()
```

## Verification

Verify the alert engine is working correctly:

```bash
# Run alert engine tests
pytest tests/test_alerting.py -v

# Test specific rule evaluation
pytest tests/test_alerting.py::test_threshold_rule_evaluation -v

# Test deduplication
pytest tests/test_alerting.py::test_alert_deduplication -v

# Test escalation
pytest tests/test_alerting.py::test_alert_escalation -v
```

Expected output:
```
tests/test_alerting.py::test_threshold_rule_evaluation PASSED
tests/test_alerting.py::test_alert_deduplication PASSED
tests/test_alerting.py::test_alert_escalation PASSED
```

## Learnings

### From Sprint 7 (Initial Implementation)
- Start with simple threshold rules before implementing complex pattern rules
- Deduplication is critical - without it, you get alert storms (hundreds of duplicate alerts)
- Cooldown period should be 2-4x the measurement frequency
- Escalation delays should account for shift changes and response times
- Always include full context in alert messages (asset details, reading values, thresholds)
- Test with real data to tune thresholds - synthetic data doesn't reveal edge cases

### Performance Considerations
- Index `alert.created_at`, `alert.status`, and `alert.rule_uuid` for fast deduplication queries
- Use database-level pagination for historical alert queries
- Cache rule configurations to avoid repeated database lookups during evaluation
- Consider partitioning alerts table by date for high-volume scenarios

### Operational Learnings
- False positives erode trust - tune thresholds conservatively
- Operators need ability to suppress alerts temporarily (maintenance windows)
- Include "why" information in alerts - don't just state the threshold violation
- Different asset types may need different thresholds for the same rule
- Keep escalation chains short (3 levels max) to avoid alert fatigue

## Anti-Patterns

### Don't: Create Rules Without Deduplication

**What it looks like**: Setting `cooldown_minutes=0` or not checking for active alerts before creating new ones.

**Why it's bad**: Creates alert storms. A single malfunctioning sensor can generate thousands of duplicate alerts in minutes, overwhelming operators and notification channels.

**Instead**: Always set appropriate cooldown periods based on:
- Measurement frequency (e.g., if measurements come every 15 min, use 60+ min cooldown)
- Response time needed (how long does it take to investigate/fix?)
- Shift patterns (don't spam new shift with alerts from previous shift)

### Don't: Set Escalation Too Fast

**What it looks like**: `escalation_minutes=5` with level 1 going to CEO.

**Why it's bad**: Operators need time to respond. Unrealistic escalation creates alert fatigue and trains people to ignore notifications.

**Instead**:
- Level 1: 30-60 min (field technicians have time to investigate)
- Level 2: 60-120 min (supervisors can coordinate response)
- Level 3: 120+ min (management for unresolved critical issues)

### Don't: Alert on Every Threshold Crossing

**What it looks like**: `consecutive_readings=1` for noisy sensors.

**Why it's bad**: Sensor noise causes false positives. Single outlier readings don't indicate real problems.

**Instead**: Use `consecutive_readings=3` or trend-based rules for noisy data. Require sustained threshold violations before alerting.

### Don't: Create Ambiguous Alert Messages

**What it looks like**: "Alert triggered for asset ABC-123"

**Why it's bad**: Operators can't act without context. They waste time investigating what the alert means.

**Instead**: Include full context:
```
CP Protection Lost - Test Station TS-42
Location: Mile Marker 12.5, West Texas Line
Reading: -820mV (threshold: -850mV)
Last Normal: 2 hours ago (-890mV)
Action: Investigate rectifier and check anode bed
```

### Don't: Use Generic Priorities

**What it looks like**: Everything marked as `CRITICAL` or everything as `LOW`.

**Why it's bad**: Destroys prioritization. If everything is critical, nothing is.

**Instead**: Use priorities consistently:
- `CRITICAL`: Immediate safety/environmental risk, requires action within 1 hour
- `HIGH`: Significant risk, requires action within 8 hours
- `MEDIUM`: Moderate concern, address within 24 hours
- `LOW`: Informational, address during next scheduled maintenance

## Variations

### For High-Volume Real-Time Monitoring

If you have high-frequency measurements (e.g., SCADA data every second):

1. Use event-driven architecture with message queue (Kafka/RabbitMQ)
2. Pre-filter measurements before rule evaluation (moving window aggregation)
3. Batch alert creation to reduce database writes
4. Use time-series database for measurement storage
5. Implement circuit breakers to prevent alert storms

### For Multi-Tenant Deployments

If you have multiple operators managing different pipeline networks:

1. Add `tenant_id` to alert rules and alerts
2. Filter rules by tenant during evaluation
3. Route notifications based on tenant-specific channels
4. Implement tenant-specific escalation chains
5. Isolate alert data per tenant for compliance

### For Offline/Mobile Field Operations

If field technicians work in areas with limited connectivity:

1. Store alerts locally on mobile devices
2. Sync alerts when connectivity is restored
3. Use SMS as primary channel for critical alerts
4. Implement offline alert acknowledgment
5. Queue notifications for retry if delivery fails

## Related Recipes

- [Configuration Management](./configuration-management.md) - Environment-based alert channel configuration
- [Database Migrations](../workflows/database-migrations.md) - Adding new alert rule types

## References

- **Source Code**: `/Volumes/Foundry/Development/CorrData/POC/src/corrdata/alerting/`
  - `engine.py` - Alert engine implementation
  - `channels.py` - Notification channel implementations
- **Database Models**: `/Volumes/Foundry/Development/CorrData/POC/src/corrdata/db/alert_models.py`
- **ADR**: [ADR-013: Rule-Based Alert Engine](../../architecture/decisions/ADR-013-alert-engine-architecture.md)

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-14 | Initial version based on Sprint 7 implementation and ADR-013 |
