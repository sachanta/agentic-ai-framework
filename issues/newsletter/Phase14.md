# Phase 14: Scheduling & Background Jobs

## Goal
Automated newsletter generation and delivery

## Status
- [ ] Not Started

## Files to Create
```
backend/app/platforms/newsletter/services/scheduler.py
backend/app/platforms/newsletter/services/jobs.py
```

## Features
- Frequency-based scheduling (daily/weekly/monthly)
- Timezone-aware delivery times
- Background job processing (asyncio tasks)
- Scheduler health monitoring
- Manual trigger support
- Retry on failure

## Job Types

### `generate_scheduled_newsletter`
Auto-generate newsletter at scheduled time based on user preferences.
```python
async def generate_scheduled_newsletter(user_id: str):
    preferences = await get_user_preferences(user_id)
    await orchestrator.start_newsletter_generation(
        user_id=user_id,
        topics=preferences.topics,
        tone=preferences.tone,
        auto_approve=preferences.auto_approve,  # Skip HITL if enabled
    )
```

### `send_campaign`
Send scheduled campaign to all recipients.
```python
async def send_campaign(campaign_id: str):
    campaign = await campaign_repo.find_by_id(campaign_id)
    subscribers = await subscriber_repo.find_active_by_user(
        user_id=campaign.user_id,
        tags=campaign.subscriber_tags,
    )
    for subscriber in subscribers:
        await email_service.send(campaign, subscriber)
```

### `process_analytics`
Aggregate engagement data from email provider.
```python
async def process_analytics(campaign_id: str):
    events = await resend_client.get_events(campaign_id)
    await campaign_repo.update_analytics(campaign_id, events)
```

### `cleanup_old_data`
Data retention management.
```python
async def cleanup_old_data(days: int = 90):
    await newsletter_repo.delete_old(days)
    await cache_repo.cleanup_expired()
```

## Scheduler Configuration
```python
class SchedulerConfig:
    # Check for scheduled jobs every N seconds
    POLL_INTERVAL: int = 60

    # Max concurrent jobs
    MAX_WORKERS: int = 5

    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 300
```

## How It Helps The Project

The Scheduler enables **hands-off newsletter automation**:

### Use Cases

| Use Case | How Scheduler Helps |
|----------|---------------------|
| Weekly digest | Auto-generate every Monday at 9am |
| Scheduled sends | Queue campaign for optimal send time |
| Analytics sync | Periodically fetch open/click data |
| Maintenance | Auto-cleanup old newsletters and cache |

### User Flow
1. User sets preferences: topics, frequency, send time, timezone
2. Scheduler triggers generation at configured time
3. If auto-approve disabled, user gets notification to review
4. If auto-approve enabled, newsletter sends automatically

## Dependencies
- All previous phases
- APScheduler or similar (add to pyproject.toml)

## Verification
- [ ] Scheduled jobs execute on time
- [ ] Timezone handling is correct
- [ ] Retry mechanism works
- [ ] Concurrent job limits respected
- [ ] Analytics sync works
- [ ] Tests passing
