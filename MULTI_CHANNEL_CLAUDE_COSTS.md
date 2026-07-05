# Critical Features: Multi-Channel Claude Cost Tracking

## 1. Token Consuming Patterns Between Dates

Users need to see HOW spending changes over time, not just WHAT they spent:

```python
guardian.get_spending_trends(start_date="2026-07-01", end_date="2026-07-05")

# Returns:
{
    "period": "2026-07-01 to 2026-07-05",
    "daily_breakdown": [
        {
            "date": "2026-07-01",
            "spend": 12.30,
            "tokens": 42000,
            "operations": 45,
            "top_cost_driver": "browser_scrape ($6.20)"
        },
        {
            "date": "2026-07-02",
            "spend": 15.80,
            "tokens": 54000,
            "operations": 62,
            "top_cost_driver": "ai_reasoning ($8.10)",
            "change": "+28% vs yesterday"
        },
        {
            "date": "2026-07-03",
            "spend": 18.50,
            "tokens": 63000,
            "operations": 71,
            "top_cost_driver": "file_read via URL ($12.40)",
            "change": "+17% vs yesterday"
        }
    ],
    
    "trends": {
        "daily_average": 15.53,
        "trend": "↑ UP 50% from last week",
        "weekly_total": 108.71,
        "monthly_projection": 3120.00,  # If trend continues
        
        "pattern_analysis": {
            "peak_day": "2026-07-03 ($18.50)",
            "valley_day": "2026-07-01 ($12.30)",
            "peak_hour": "14:00 UTC (+45% above average)",
            "lowest_hour": "02:00 UTC (-70% below average)",
            "day_of_week": "Wednesday costs 28% more than Monday"
        },
        
        "seasonal": {
            "vs_last_week": "+50%",
            "vs_last_month": "+12%",
            "vs_trend": "accelerating"
        },
        
        "alerts": [
            "Spend up 50% this week. Root cause: 3x more browser operations",
            "Thursday typically 28% higher cost. Correlates with weekly review cycle",
            "Peak hour (14:00) coincides with team standup. Consider batch operations"
        ]
    }
}
```

---

## 2. User-Level Cost Attribution

Track costs PER DEVELOPER for team budgeting and chargeback:

```python
guardian.get_cost_by_user(period="week")

# Returns:
{
    "team_total": 847.30,
    "users": [
        {
            "user_id": "alice@company.com",
            "name": "Alice Chen",
            "spend_this_week": 312.40,
            "percent_of_team": "36.9%",
            "operations": 847,
            "trend": "↓ DOWN 5% (optimizing)",
            "daily_average": 44.63,
            "top_expense": "file_read via URL ($145.20)",
            "recommendations": "Switch to CSV pasted for daily reports - saves $89/week"
        },
        {
            "user_id": "bob@company.com",
            "name": "Bob Smith",
            "spend_this_week": 298.15,
            "percent_of_team": "35.2%",
            "operations": 723,
            "trend": "↑ UP 12% (needs attention)",
            "daily_average": 42.59,
            "top_expense": "browser_scrape ($156.80)",
            "recommendations": "Browser ops eating 52.6% of your spend. Disable for local code only"
        },
        {
            "user_id": "carol@company.com",
            "name": "Carol Davis",
            "spend_this_week": 236.75,
            "percent_of_team": "27.9%",
            "operations": 612,
            "trend": "→ STABLE",
            "daily_average": 33.82,
            "top_expense": "ai_reasoning ($118.40)",
            "recommendations": "Well-optimized. Keep current approach"
        }
    ],
    
    "team_insights": {
        "budget_allocated": 1000.00,
        "budget_used": 847.30,
        "budget_remaining": 152.70,
        "utilization": "84.7%",
        "alert": "At current spend rate, will exceed budget by 2026-07-12"
    },
    
    "chargeback_report": {
        "format": "csv",
        "team": "Data Science",
        "cost_center": "CC-4521",
        "users": [...],
        "ready_for_finance": True
    }
}
```

---

## 3. Multi-Channel Claude Cost Unification

Users consume Claude through MULTIPLE providers simultaneously. CostReporter must unify:

```python
guardian.get_unified_claude_costs(period="month")

# Returns:
{
    "total_claude_cost": 4280.50,
    "channels": [
        {
            "provider": "Claude Pro (Browser)",
            "seats": 15,
            "monthly_cost": 300.00,  # 15 × $20
            "cost_per_user": 20.00,
            "usage": "Web UI, Desktop app",
            "users": [
                {"name": "Alice Chen", "tier": "Pro", "cost": 20.00},
                {"name": "Bob Smith", "tier": "Pro", "cost": 20.00},
                # ... 13 more
            ]
        },
        {
            "provider": "Claude Max (Browser)",
            "seats": 3,
            "monthly_cost": 600.00,  # 3 × $200
            "cost_per_user": 200.00,
            "usage": "Web UI for power users",
            "users": [
                {"name": "David Lee", "tier": "Max", "cost": 200.00},
                # ... 2 more
            ]
        },
        {
            "provider": "AWS Bedrock (API)",
            "monthly_cost": 1850.20,
            "usage_breakdown": {
                "claude-3-5-sonnet": {"input": 450M, "output": 150M, "cost": 1620.00},
                "claude-3-5-haiku": {"input": 200M, "output": 50M, "cost": 230.20}
            },
            "team": "Platform Engineering",
            "account_id": "123456789012",
            "details": "Production inference + data analysis pipelines"
        },
        {
            "provider": "Azure Foundry",
            "monthly_cost": 892.30,
            "usage_breakdown": {
                "claude-3-5-sonnet": {"requests": 12400, "cost": 892.30}
            },
            "team": "ML Research",
            "subscription": "Enterprise",
            "details": "Model comparison experiments"
        },
        {
            "provider": "GCP Vertex AI",
            "monthly_cost": 638.00,
            "usage_breakdown": {
                "claude-3-5-sonnet": {"requests": 8900, "cost": 638.00}
            },
            "team": "Analytics",
            "project": "analytics-prod",
            "details": "BigQuery integration for report generation"
        }
    ],
    
    "cost_breakdown_by_model": {
        "claude-3-5-sonnet": {
            "total_cost": 3150.30,
            "breakdown": {
                "pro_browser": 0,
                "bedrock": 1620.00,
                "azure": 892.30,
                "gcp": 638.00
            },
            "tokens_input": 850M,
            "tokens_output": 200M
        },
        "claude-3-5-haiku": {
            "total_cost": 230.20,
            "breakdown": {
                "pro_browser": 0,
                "bedrock": 230.20,
                "azure": 0,
                "gcp": 0
            },
            "tokens_input": 200M,
            "tokens_output": 50M
        }
    },
    
    "efficiency_analysis": {
        "claude_pro_users": {
            "count": 18,
            "cost": 300.00,
            "cost_per_user": 20.00,
            "note": "Fixed subscription; usage not optimized per dev"
        },
        "api_users": {
            "teams": 3,
            "cost": 3380.50,
            "cost_per_request": 0.00284,
            "optimization": "Switch 30% to Haiku for cost-insensitive tasks → save $684/month"
        }
    },
    
    "recommendations": [
        {
            "finding": "Bedrock is 40% of spend but only 43% used",
            "action": "Consolidate to Azure (lower per-request cost)",
            "savings": "$740/month"
        },
        {
            "finding": "GCP 12% higher cost than Bedrock for same model",
            "action": "Migrate GCP workloads to Bedrock",
            "savings": "$240/month"
        },
        {
            "finding": "4 Claude Pro users not using their subscriptions",
            "action": "Downgrade to free tier or consolidate to API",
            "savings": "$80/month"
        }
    ],
    
    "consolidated_budget": {
        "total_monthly": 4280.50,
        "monthly_trend": "+8.2% MoM",
        "quarterly_projection": 12841.50,
        "yearly_projection": 51366.00,
        "budget_alert": "Will exceed $50K annual budget by Q4 2026"
    }
}
```

---

## 4. Trends + Users + Multi-Channel Dashboard

```
┌─────────────────────────────────────────────────────┐
│ COST GUARDIAN - UNIFIED CLAUDE DASHBOARD           │
├─────────────────────────────────────────────────────┤
│                                                      │
│ MONTHLY SPEND TREND                                │
│ ┌────────────────────────────────────────────────┐ │
│ │ $5K ┤                                ╱╱╱╱╱╱╱ │ │
│ │ $4K ┤                    ╱╱╱╱╱╱╱╱╱╱╱        │ │
│ │ $3K ┤        ╱╱╱╱╱╱╱╱╱╱                    │ │
│ │ $2K ┤ ╱╱╱╱╱╱                               │ │
│ │ $1K ┤╱                                      │ │
│ │     └────────────────────────────────────────┘ │
│ │      Jan  Feb  Mar  Apr  May  Jun  Jul       │
│ │      Projection: $51.4K/year (budget: $50K)   │
│ │                                                │
├─────────────────────────────────────────────────────┤
│ BY USER (This Week)        │ BY CHANNEL              │
│                            │                        │
│ Alice Chen   $312.40 ██    │ AWS Bedrock    $1,850  │
│ Bob Smith    $298.15 ██    │ Claude Pro     $600    │
│ Carol Davis  $236.75 █     │ Azure          $892    │
│ David Lee    $201.30 █     │ GCP Vertex     $638    │
│                            │ Claude Max     $300    │
├─────────────────────────────────────────────────────┤
│ ALERTS:                                             │
│ ⚠️  Budget 84.7% utilized (152 days until limit)  │
│ 🚨 Bob's spend UP 12% (browser ops suspicious)    │
│ 💡 GCP 12% more expensive than Bedrock → migrate  │
└─────────────────────────────────────────────────────┘
```

---

## Implementation: Tracking Model

```rust
// beacon-core/src/unified_claude_tracker.rs

pub enum ClaudeProvider {
    ClaudePro,           // Subscription ($20 or $200/month)
    BedrockAPI,          // AWS API consumption
    AzureFoundry,        // Azure AI services
    GCPVertexAI,         // Google Cloud AI
    AnthropicAPI,        // Direct API
    OpenRouter,          // Proxy service
}

pub struct ClaudeOperation {
    // Multi-channel tracking
    provider: ClaudeProvider,
    user_id: String,          // ← Track per-user
    team: String,
    cost: f32,
    tokens: i32,
    timestamp: DateTime,      // ← Track for trends
    
    // All other dimensions
    operation_type: OperationType,
    file_format: FileFormat,
    file_source: FileSource,
    mcp_name: Option<String>,
    model: String,
}

pub async fn track_unified_claude_operation(&mut self, op: ClaudeOperation) -> Result<()> {
    self.storage.insert("unified_operations", &op).await
}

pub async fn get_trends(
    &self,
    start: DateTime,
    end: DateTime,
) -> Result<TrendAnalysis> {
    // Query by user, by provider, by team
    // Compute daily averages, weekly patterns, monthly projections
}
```

---

## Python API

```python
class CostGuardian:
    def get_spending_trends(self, start_date, end_date) -> Dict:
        """Daily/weekly/monthly cost trends"""
        return self._core.analyze_trends(start_date, end_date)
    
    def get_cost_by_user(self, period="week") -> Dict:
        """Per-user cost attribution for chargeback"""
        return self._core.profile_by_user(period)
    
    def get_unified_claude_costs(self, period="month") -> Dict:
        """Unified costs across all Claude access methods"""
        return self._core.aggregate_all_providers(period)
    
    def get_team_budget_status(self, team: str) -> Dict:
        """Budget tracking per team"""
        return self._core.team_budget_report(team)
```

---

## Why This Wins

**Nobody tracks Claude costs this way:**
- Bedrock dashboard = AWS spend only (doesn't see Pro subscriptions)
- Azure Foundry = Azure spend only (doesn't see Bedrock)
- Claude Console = Pro/Max subscriptions only (doesn't see API usage)
- **CostReporter = Unified view across ALL channels**

**Enterprise value:**
- Finance needs: "We're spending $4.3K/month on Claude, here's the breakdown"
- Engineering needs: "Alice, your team's Claude costs are $847/week; Bob's up 12%"
- Ops needs: "We can save $740/month by consolidating from GCP to Bedrock"

**Chargeback capability:**
- Allocate API costs per user/team/project
- Show Pro users their actual usage vs subscription cost
- Prove ROI: "Claude inference saved us $50K vs hiring analysts"

