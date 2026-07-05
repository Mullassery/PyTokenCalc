# CostReporter + OpenTelemetry Integration

## Why OpenTelemetry Matters

Enterprise teams already monitor infrastructure with:
- Datadog
- New Relic  
- Prometheus + Grafana
- Splunk
- Dynatrace

CostReporter needs to **emit observability signals** so costs appear alongside infrastructure metrics.

---

## Architecture: OpenTelemetry Exporter

```
CostReporter Core
    ↓
OpenTelemetry SDK
    ↓
Exporters: [Datadog | Prometheus | OTLP | Jaeger]
    ↓
Observability Platforms
```

### Rust Core Exports

```rust
// beacon-core/src/otel.rs

use opentelemetry::{metrics::*, trace::*};
use opentelemetry_sdk::{metrics::MeterProvider, trace::TracerProvider};
use opentelemetry_jaeger::new_pipeline;

pub struct OTelExporter {
    meter: Meter,
    tracer: Tracer,
}

impl OTelExporter {
    pub fn new() -> Self {
        let tracer_provider = TracerProvider::default();
        let meter_provider = MeterProvider::default();
        
        Self {
            meter: meter_provider.meter("cost-guardian"),
            tracer: tracer_provider.get_tracer("cost-guardian"),
        }
    }
    
    pub fn record_operation_cost(&self, op: &OperationCost) {
        // Export as metric
        let counter = self.meter
            .f64_counter("cost_guardian.operation.cost")
            .with_description("Cost of operation in USD")
            .init();
        
        counter.add(
            op.cost_usd as f64,
            &[
                KeyValue::new("operation_type", op.operation.to_string()),
                KeyValue::new("model", op.model.clone()),
                KeyValue::new("mcp", op.mcp_name.clone()),
            ],
        );
        
        // Export as span for tracing
        let span = self.tracer.start(format!("operation:{}", op.operation));
        span.set_attribute(KeyValue::new("cost_usd", op.cost_usd));
        span.set_attribute(KeyValue::new("tokens_input", op.tokens_input));
        span.set_attribute(KeyValue::new("tokens_output", op.tokens_output));
    }
}
```

---

## Metrics Exported

### Core Metrics

```
Metric: cost_guardian.operation.cost
├─ Type: Counter (cumulative)
├─ Unit: USD
├─ Attributes:
│  ├─ operation_type: browser_scrape, file_read, ai_reasoning
│  ├─ model: claude-3-5-sonnet, claude-3-5-haiku
│  ├─ mcp: github-mcp, web-search-mcp
│  └─ status: success, error

Metric: cost_guardian.tokens.input
├─ Type: Counter
├─ Unit: tokens
├─ Attributes: [operation_type, model, mcp]

Metric: cost_guardian.tokens.output
├─ Type: Counter
├─ Unit: tokens
├─ Attributes: [operation_type, model, mcp]

Metric: cost_guardian.operation.latency
├─ Type: Histogram
├─ Unit: milliseconds
├─ Attributes: [operation_type, mcp]

Metric: cost_guardian.daily.spend
├─ Type: Gauge
├─ Unit: USD
├─ Attributes: [period: "1d", "7d", "30d"]

Metric: cost_guardian.budget.utilization
├─ Type: Gauge
├─ Unit: percent (0-100)
├─ Attributes: [limit_type: "daily", "weekly", "monthly"]
```

---

## Datadog Dashboard Example

```yaml
# datadog-dashboard.yaml
title: "Claude Code CostReporter"
widgets:
  - type: timeseries
    title: "Daily Claude Costs"
    metrics:
      - cost_guardian.daily.spend
    
  - type: pie_chart
    title: "Cost by Operation Type"
    metrics:
      - cost_guardian.operation.cost
    group_by: operation_type
    
  - type: table
    title: "Cost by MCP"
    metrics:
      - cost_guardian.operation.cost
    group_by: mcp
    
  - type: gauge
    title: "Budget Utilization"
    metrics:
      - cost_guardian.budget.utilization
    
  - type: heatmap
    title: "Token Usage Patterns"
    metrics:
      - cost_guardian.tokens.input
      - cost_guardian.tokens.output
    group_by: [operation_type, hour]
```

---

## Prometheus Queries

```promql
# Current daily cost
rate(cost_guardian_operation_cost_total[24h]) * 86400

# Cost by operation type
rate(cost_guardian_operation_cost_total[1h]) by (operation_type)

# Browser ops vs file ops (cost comparison)
rate(cost_guardian_operation_cost_total{operation_type="browser_scrape"}[1h])
/
rate(cost_guardian_operation_cost_total{operation_type="file_read"}[1h])

# Budget alert: >80% of daily limit
cost_guardian_budget_utilization > 80

# Expensive MCP detection
rate(cost_guardian_operation_cost_total[1h]) by (mcp) > 0.5
```

---

## Grafana Dashboard

```json
{
  "dashboard": {
    "title": "CostReporter - Claude Code Observability",
    "panels": [
      {
        "title": "Daily Claude Spend",
        "targets": [
          {
            "expr": "rate(cost_guardian_operation_cost_total[24h]) * 86400"
          }
        ]
      },
      {
        "title": "Top Cost Drivers",
        "targets": [
          {
            "expr": "topk(5, rate(cost_guardian_operation_cost_total[1h]) by (operation_type))"
          }
        ]
      },
      {
        "title": "MCP Cost Distribution",
        "targets": [
          {
            "expr": "rate(cost_guardian_operation_cost_total[1h]) by (mcp)"
          }
        ]
      },
      {
        "title": "Budget Status",
        "targets": [
          {
            "expr": "cost_guardian_budget_utilization"
          }
        ]
      }
    ]
  }
}
```

---

## New Relic Integration

```python
# python/src/newrelic_exporter.py
from newrelic.agent import record_custom_metric, custom_event

class NewRelicExporter:
    def record_operation_cost(self, operation: Operation, cost: float):
        # Record as metric
        record_custom_metric(
            'cost_guardian/operation/cost',
            cost,
            attributes={
                'operation_type': operation.operation_type,
                'model': operation.model,
                'mcp': operation.mcp_name,
            }
        )
        
        # Record as event for insights
        custom_event('CostGuardianOperation', {
            'cost': cost,
            'operation_type': operation.operation_type,
            'tokens_input': operation.tokens_input,
            'tokens_output': operation.tokens_output,
            'model': operation.model,
            'mcp': operation.mcp_name,
        })
```

---

## Configuration

```yaml
# cost-guardian-config.yaml
observability:
  enabled: true
  
  exporters:
    - type: prometheus
      port: 8888
      path: /metrics
    
    - type: datadog
      api_key: ${DD_API_KEY}
      enabled: true
    
    - type: otel_grpc
      endpoint: localhost:4317
      enabled: true
    
    - type: jaeger
      endpoint: localhost:6831
      enabled: false

  metrics:
    operation_cost:
      enabled: true
      export_interval_seconds: 10
    
    tokens:
      enabled: true
      track_input: true
      track_output: true
    
    latency:
      enabled: true
      export_buckets: [10, 50, 100, 500, 1000]
    
    budget:
      enabled: true
      track_utilization: true
      alert_thresholds: [50, 80, 95]
```

---

## CLI Integration

```bash
# Enable OpenTelemetry export
cost-guardian config set observability.enabled true

# Set Datadog API key
cost-guardian config set observability.exporters.datadog.api_key <key>

# Start with Prometheus exporter
cost-guardian serve --otel-prometheus-port 8888

# View Prometheus metrics at localhost:8888/metrics
```

---

## Enterprise Use Cases

### 1. Cost Allocation

```promql
# Charge back Claude Code costs by team
sum(cost_guardian_operation_cost_total) by (team)
```

### 2. Budget Enforcement

```promql
# Alert when any team exceeds $1000/month
alert: CostGuardianTeamBudgetExceeded
  expr: |
    sum(rate(cost_guardian_operation_cost_total[24h]) * 86400 * 30) by (team) > 1000
```

### 3. Trend Analysis

```promql
# MoM cost comparison
rate(cost_guardian_operation_cost_total[24h]) * 86400 * 30 
/ 
rate(cost_guardian_operation_cost_total[24h] offset 30d) * 86400 * 30
```

### 4. Efficiency Metrics

```promql
# Cost per output token (efficiency)
rate(cost_guardian_operation_cost_total[1h])
/
rate(cost_guardian_tokens_output_total[1h])
```

---

## Alerting Rules

```yaml
# prometheus-alerts.yaml
groups:
  - name: cost-guardian
    rules:
      - alert: HighDailyCost
        expr: |
          rate(cost_guardian_operation_cost_total[24h]) * 86400 > 100
        for: 5m
        annotations:
          summary: "Daily Claude Code cost exceeds $100"
      
      - alert: BrowserOpsExpensive
        expr: |
          rate(cost_guardian_operation_cost_total{operation_type="browser_scrape"}[1h])
          /
          rate(cost_guardian_operation_cost_total[1h])
          > 0.5
        annotations:
          summary: "Browser operations consuming >50% of budget"
      
      - alert: MajorMCPCostSpike
        expr: |
          rate(cost_guardian_operation_cost_total[1h]) by (mcp)
          > 10
        annotations:
          summary: "MCP {{ $labels.mcp }} costing >$10/hour"
```

---

## Roadmap: Add OpenTelemetry (Phase 2, Week 4)

```
WEEK 4:
├─ Add OpenTelemetry SDK to Rust core
├─ Implement metric exporters (Prometheus, Datadog, OTLP)
├─ Python OpenTelemetry wrapper
├─ Enterprise dashboard templates (Datadog, Grafana)
├─ Alerting rules (Prometheus, Datadog)
└─ Documentation + examples
```

---

## Why This Wins Enterprises

**Before CostReporter:**
```
Finance team: "How much are we spending on Claude Code?"
Engineering: "No idea, it's mixed with other API costs"
Result: Cannot allocate, cannot budget, cannot optimize
```

**With CostReporter + OpenTelemetry:**
```
Finance team: "Claude Code cost is $42,000/month"
CostReporter → Datadog: Breakdown by team, by operation, by MCP
Engineering: "Browser ops costing $18k. Let's optimize."
Finance: Can allocate costs, set budgets, optimize spend
Result: Enterprise-grade cost governance
```

---

## Expected Impact

**Enterprise customers will:**
1. See Claude Code costs in their existing observability stack
2. Correlate costs with infrastructure + business metrics
3. Set spending budgets + alerts automatically
4. Prove ROI of Claude Code investments to finance
5. Optimize spend without losing productivity

**Result:** Enterprise customers paying $500/month → $5,000/month 🚀


---

## CRITICAL: File Format Cost Profiling

### The Problem: Same Data, 10x Different Costs

**Reading the same PDF three ways:**

```python
guardian.get_cost_by_file_format(data_type="pdf")

# Returns:
{
    "data_type": "pdf",
    "total_cost": 28.50,
    
    "by_source": [
        {
            "source_type": "csv_pasted",
            "count": 50,
            "total_cost": 2.30,
            "avg_cost": 0.046,
            "tokens_per_op": 300,
            "status": "✅ CHEAP"
        },
        {
            "source_type": "pdf_file_local",
            "count": 35,
            "total_cost": 4.90,
            "avg_cost": 0.140,
            "tokens_per_op": 900,
            "status": "ℹ️ NORMAL"
        },
        {
            "source_type": "pdf_mcp_upload",
            "count": 12,
            "total_cost": 6.80,
            "avg_cost": 0.567,
            "tokens_per_op": 3600,  # MCP overhead
            "status": "⚠️ EXPENSIVE"
        },
        {
            "source_type": "pdf_url_browser",
            "count": 8,
            "total_cost": 14.50,
            "avg_cost": 1.813,
            "tokens_per_op": 11500,  # Browser scraping + PDF extraction
            "status": "🚨 VERY EXPENSIVE"
        }
    ],
    
    "insights": [
        {
            "finding": "PDF via URL costs 39x more than CSV pasted",
            "details": "$1.813/PDF (URL) vs $0.046/CSV (pasted)",
            "root_cause": "Browser scraping + PDF extraction overhead"
        },
        {
            "finding": "PDF via URL costing $14.50/day for 8 operations",
            "recommendation": "Convert URLs to direct file uploads",
            "savings": "$14.50 → $0.56 (96% reduction)"
        },
        {
            "finding": "MCP upload has 12x MCP overhead vs local file",
            "recommendation": "Use local file reads when possible",
            "savings": "Switch 80% to local: -$5.44/day"
        }
    ]
}
```

---

### Data Source Cost Matrix

```
Data Source              | Tokens  | Cost   | Multiplier
─────────────────────────┼─────────┼────────┼──────────
CSV pasted               | 300     | $0.046 | 1x (baseline)
JSON pasted              | 350     | $0.053 | 1.15x
Local file (text)        | 400     | $0.061 | 1.3x
Local file (CSV/JSON)    | 600     | $0.092 | 2x
PDF file local           | 900     | $0.140 | 3x
PDF via MCP upload       | 3600    | $0.567 | 12x
CSV from URL (HTML)      | 5000    | $0.770 | 16.7x
PDF from URL (browser)   | 11500   | $1.813 | 39.4x ← EXPENSIVE
Image from URL (OCR)     | 15000   | $2.310 | 50.2x ← VERY EXPENSIVE
```

---

### Implementation: Track File Format + Source

```rust
// beacon-core/src/file_format_profiler.rs

#[derive(Debug, Clone)]
pub enum FileSource {
    PastedText,         // Directly pasted into prompt
    LocalFile,          // Read from local filesystem
    MCPUpload,          // Uploaded via MCP
    URLDirect,          // Downloaded from HTTP URL
    URLBrowserRead,     // Scraped via browser
    DatabaseQuery,      // Retrieved from database
}

#[derive(Debug, Clone)]
pub enum FileFormat {
    CSV,
    JSON,
    PDF,
    XML,
    YAML,
    PlainText,
    Markdown,
    HTML,
    Image,
}

pub struct FileOperationCost {
    file_format: FileFormat,
    file_source: FileSource,
    file_size_bytes: i32,
    tokens_consumed: i32,
    cost_usd: f32,
    
    // Detailed breakdown:
    parse_tokens: i32,          // Format parsing
    content_tokens: i32,        // Actual content
    extraction_overhead: i32,   // MCP/browser overhead
}

pub async fn profile_file_costs(
    &self,
    period: Duration,
) -> Result<Vec<FileFormatProfile>> {
    // Query and group by [file_format, file_source]
    let operations = self.storage
        .query_file_operations(period)
        .await?;
    
    let mut profiles = Vec::new();
    for ((format, source), ops) in operations.group_by_format_and_source() {
        profiles.push(FileFormatProfile {
            format,
            source,
            count: ops.len(),
            total_cost: ops.iter().map(|o| o.cost_usd).sum(),
            avg_cost: ops.iter().map(|o| o.cost_usd).sum::<f32>() / ops.len() as f32,
            total_tokens: ops.iter().map(|o| o.tokens_consumed).sum(),
            overhead_percent: calculate_overhead_percent(&ops),
        });
    }
    
    // Sort by cost (highest first)
    profiles.sort_by(|a, b| b.total_cost.partial_cmp(&a.total_cost).unwrap());
    
    Ok(profiles)
}
```

---

### Python API: File Format Analysis

```python
class CostGuardian:
    def get_cost_by_file_format(self, data_type: str = None) -> Dict:
        """Break down costs by file format + source"""
        return self._core.profile_file_costs(data_type)
    
    def get_file_source_comparison(self, file_format: str) -> Dict:
        """Compare costs for same format from different sources"""
        # Returns: "PDF via URL costs 39x more than PDF local"
        return self._core.compare_file_sources(file_format)
    
    def recommend_file_optimization(self, file_format: str) -> List[Dict]:
        """How to reduce costs for this file type"""
        # Returns: ["Convert URLs to uploads", "Use CSV instead of PDF"]
        pass
```

---

### Dashboard: File Format Cost Heatmap

```
┌──────────────────────────────────────────────────────┐
│ FILE FORMAT COST MATRIX - CostReporter             │
├──────────────────────────────────────────────────────┤
│                                                       │
│ File Format    Pasted  Local   MCP    URL   Browser  │
│ ──────────────┼──────┬──────┬──────┬──────┬────────│
│ CSV           $0.05 │$0.06 │$0.57 │$0.77 │$2.31   │
│               ✅     │ ✅    │ ⚠️    │ ⚠️    │ 🚨     │
│               1x     │1.2x  │12x   │16.7x │50x    │
│                      │      │      │      │        │
│ PDF           -      │$0.14 │$0.57 │$1.81 │$2.31   │
│               -      │ ✅    │ ⚠️    │ 🚨    │ 🚨     │
│               -      │1x    │4x    │13x   │16.5x  │
│                      │      │      │      │        │
│ JSON (large)  -      │$0.09 │$0.71 │$2.45 │$3.12   │
│               -      │ ✅    │ ⚠️    │ 🚨    │ 🚨     │
│               -      │1x    │8x    │27x   │35x    │
│                      │      │      │      │        │
│ Image         -      │$0.23 │$1.15 │$4.62 │$9.24   │
│               -      │ ✅    │ ⚠️    │ 🚨    │ 🚨     │
│               -      │1x    │5x    │20x   │40x    │
│                      │      │      │      │        │
└──────────────────────────────────────────────────────┘

🔑 Key insights:
• PDF via browser: 39x more expensive than local file
• MCP upload adds 4-5x overhead vs local read
• URL scraping adds browser overhead (10-40x multiplier)
• Pasted text: cheapest when available
```

---

### CLI: File Format Analysis

```bash
# Show cost breakdown by file format + source
cost-guardian files breakdown

# Compare same format across sources
cost-guardian files compare pdf

# Get recommendations for file handling
cost-guardian files optimize

# Example output:
# ┌─ PDF Cost Analysis ────────┐
# │ Local file:   $0.14/PDF    │
# │ MCP upload:   $0.57/PDF (4x)
# │ URL browser:  $1.81/PDF (13x)
# │                            │
# │ Recommendation:            │
# │ 87% of PDFs via URL.       │
# │ Save $46/day by switching. │
# └────────────────────────────┘
```

---

### Real-World Example: Monthly Report Processing

```python
# Current workflow (EXPENSIVE)
monthly_report.pdf → Browser fetch → OCR → Analysis
Cost: $1.81 per report × 30 days = $54.30/month

# Optimized workflow (CHEAP)
monthly_report.pdf → Direct upload via MCP → Parse → Analysis
Cost: $0.57 per report × 30 days = $17.10/month

SAVINGS: $37.20/month (69% reduction)
```

---

### Metrics to Export (OpenTelemetry)

```rust
Metric: cost_guardian.file_format.cost
├─ Attributes:
│  ├─ file_format: csv, json, pdf, image, xml, text
│  └─ file_source: pasted, local, mcp, url, browser, database

Metric: cost_guardian.file_source.overhead
├─ Tracks the multiplier cost of each source
├─ Helps identify which sources are expensive

Metric: cost_guardian.file_size_efficiency
├─ Cost per byte (shows parsing overhead)
```

---

## Updated MVP (Week 1-2): NOW COMPREHENSIVE

```
WEEK 1:
├─ Cost tracking + attribution ✅
├─ Model pricing ✅
├─ By operation type ✅
├─ MCP cost profiling ✅
└─ File format + source profiling ← ADD THIS

WEEK 2:
├─ Browser operation analysis ✅
├─ File format optimization recommendations ← ADD THIS
├─ CLI commands
├─ Python API
└─ GitHub launch: "Your PDF via URL costs 39x more than local"
```

---

## Final Complete CostReporter Feature Set (MVP)

CostReporter now tracks **FIVE dimensions:**

1. **Model Choice** — Sonnet vs Haiku (3.75x difference)
2. **Operation Type** — Browser vs file (55x difference)
3. **MCP Usage** — Which MCPs eat budget
4. **File Format** — CSV vs PDF (2-50x difference)
5. **File Source** — Local vs URL via browser (40x difference)

**This is comprehensive cost visibility that doesn't exist anywhere else.**

🚀 **Result:** 10,000+ stars + Enterprise dominance

