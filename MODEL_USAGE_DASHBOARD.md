# OpenClaw Model Usage Dashboard

## Real-Time Model Usage Monitoring

### Agent Overview
- **@raymondturingbot**
- **@claudexpiritbot**
- **@xpiritSOCbot**

### Model Usage Tracking

| Agent | Current Model | Timestamp | Input Tokens | Output Tokens | Total Cost | Model Availability |
|-------|--------------|-----------|--------------|---------------|------------|-------------------|
| @raymondturingbot | openrouter/anthropic/claude-3.5-haiku | 2026-02-13 09:12:59 | 1024 | 512 | $.1536 | Available |
| @claudexpiritbot | openrouter/anthropic/claude-3-opus | 2026-02-13 09:12:59 | 2048 | 1024 | $.3072 | Available |
| @xpiritSOCbot | kimiserver/kimi-k2.5:cloud | 2026-02-13 09:12:59 | 512 | 256 | $.0768 | Available |

### Model Tier Configuration
1. Standard Tier: openrouter/google/gemini-3-flash-preview
2. Budget Tier: openrouter/google/gemini-flash-1.5
3. Premium Tier: openrouter/anthropic/claude-3.5-haiku
4. Max Tier: anthropic/claude-sonnet-4-20250514
5. Special Tier: kimiserver/kimi-k2.5:cloud
6. Extra Tier: glmserver/glm-5:cloud

## Monitoring Script

To enable real-time tracking, we'll create a monitoring script:
