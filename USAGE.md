# PyCostAudit Usage Guide

Complete documentation for using PyCostAudit to track, analyze, and optimize your Claude Code costs.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Core Concepts](#core-concepts)
4. [CLI Usage](#cli-usage)
5. [Python API](#python-api)
6. [Common Workflows](#common-workflows)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

- **Python:** 3.9 or higher
- **Pip/Uv:** Package manager (comes with Python)
- **Claude Code:** Running Claude API calls to track

### Install Methods

**Method 1: Using pip (Recommended)**
```bash
pip install pycostaudit
```

**Method 2: Using uv (Faster)**
```bash
uv pip install pycostaudit
```

**Method 3: Development Installation (from source)**
```bash
git clone https://github.com/Mullassery/PyCostAudit.git
cd PyCostAudit
pip install -e .
```

### Verify Installation

```bash
python3 -c "import pycostaudit; print(pycostaudit.__version__)"
# Output: 0.7.0
```

---

## Quick Start

### Choose Your Setup

#### 👤 **I'm an Individual Developer**

```bash
# Install
pip install pycostaudit

# See today's costs
python3 demo_claude_code.py

# Set up daily email reports
python3 -c "
from pycostaudit import PyCostAudit
auditor = PyCostAudit()
auditor.setup_daily_email('your-email@example.com')
"
```

---

#### 👥 **I'm a Team Lead / Manager**

```bash
# Install
pip install pycostaudit

# Set up team monitoring
python3 -c "
from pycostaudit.multi_org_manager import OrganizationManager
manager = OrganizationManager()
org = manager.create_organization('My Company')
eng_dept = manager.create_department(org.id, 'Engineering')
sales_dept = manager.create_department(org.id, 'Sales')

# Assign team members
manager.assign_user_to_department('alice@company.com', eng_dept.id, 'manager')
manager.assign_user_to_department('bob@company.com', sales_dept.id, 'member')
"

# Get team costs daily
python3 -c "
from pycostaudit.multi_org_manager import CostAggregator
agg = CostAggregator()
breakdown = agg.get_org_cost_breakdown('your-org-id')
print(breakdown)
"
```

---

#### 🏢 **I'm an Enterprise / Compliance Officer**

```bash
# Install with compliance features
pip install pycostaudit[compliance]

# Set up audit logging
python3 -c "
from pycostaudit.compliance_audit import AuditLogger, AuditEventType
import sqlite3

logger = AuditLogger()

# Log access events
logger.log_event(
    event_type=AuditEventType.DATA_ACCESSED,
    user_id='user123',
    resource_type='report',
    resource_id='report456',
    description='User accessed financial report'
)

# Retrieve audit trail
events = logger.get_user_events('user123')
for event in events:
    print(f'{event.timestamp}: {event.action} on {event.resource_type}')
"

# Generate compliance reports
python3 -c "
from pycostaudit.compliance_audit import ComplianceManager
manager = ComplianceManager()
report = manager.generate_compliance_report('SOC_2')
print(report)
"
```

---

## Core Concepts

### Cost Tracking Dimensions

PyCostAudit tracks costs across **50+ dimensions**:

| Dimension | Examples | Multiplier |
|-----------|----------|-----------|
| **File Format** | CSV vs PDF URL | 3.6x variance |
| **Operation Type** | Browser vs API | 55x variance |
| **Timing** | Peak vs Off-peak | 1.3x variance |
| **Region** | US vs EU | 1.15x variance |
| **Model** | Haiku vs Sonnet | 4x variance |
| **Billing Plan** | API vs Pro vs Max | 2x variance |

### Key Objects

#### Operation
Represents a single Claude API call or interaction.

```python
from pycostaudit import Operation, OperationType

op = Operation(
    operation_type=OperationType.ApiCall,
    tokens_input=450,
    tokens_output=150,
    model="claude-3-5-sonnet",
    user="alice@company.com",
    timestamp=datetime.now()
)
```

#### CostData
Result of calculating cost for an operation.

```python
from pycostaudit import CostData

# Created by the cost tracker
cost = CostData(
    cost=0.0225,  # USD
    currency="USD",
    tokens_actual=600,
    multiplier=1.0
)
```

#### Session
Groups related operations together for analysis.

```python
from pycostaudit import SessionManager

sessions = SessionManager()
session_id = sessions.create_session("debug-auth-flow")

# Track operations in session
# ...later...
summary = sessions.finalize_session(session_id)
# Returns: costs, count, breakdown
```

---

## CLI Usage

### Command: `cost-report`

See today's cost breakdown by operation type and model.

```bash
cost-report

# Output:
# Today's Costs: $47.50
# By Operation Type:
# ├─ api_call: $25.00 (52%)
# ├─ file_read: $15.20 (32%)
# ├─ browser_op: $5.30 (11%)
# └─ mcp_invocation: $2.00 (5%)
```

### Command: `cost-forecast`

Predict costs for next 30, 60, 90 days.

```bash
cost-forecast --days 30

# Output:
# 30-Day Forecast: $1,425
# 60-Day Forecast: $2,850
# 90-Day Forecast: $4,275
# Recommended Plan: Pro ($100/mo)
```

### Command: `cost-alert`

Set up automatic alerts when costs exceed threshold.

```bash
# Set daily budget alert
cost-alert set --daily 100 --slack-webhook https://hooks.slack.com/...

# Set weekly alert
cost-alert set --weekly 600 --email your-email@company.com

# List alerts
cost-alert list

# Remove alert
cost-alert remove --id alert123
```

---

## Python API

### Basic Usage

```python
from pycostaudit import PyCostAudit
from datetime import datetime

# Initialize tracker
auditor = PyCostAudit(db_path="~/.pycostaudit/costs.db")

# Track an operation
cost = auditor.track_operation(
    operation_type="api_call",
    tokens_input=450,
    tokens_output=150,
    model="claude-3-5-sonnet"
)
print(f"Cost: ${cost.cost:.4f}")

# Start a session (for grouping related operations)
session_id = auditor.start_session("debug-session")

# ...perform operations...

# End session and get summary
summary = auditor.end_session(session_id)
print(f"Session total: ${summary['total_cost']}")
```

### Getting Analysis

```python
# Today's breakdown
breakdown = auditor.analyze_daily()
print(breakdown)
# {
#   "by_operation_type": {...},
#   "by_model": {...},
#   "by_file_format": {...},
#   "total_cost": 47.50
# }

# Session analysis with recommendations
analysis = auditor.analyze_session("debug-session")
print(analysis)
# {
#   "total_cost": 12.50,
#   "breakdown": {...},
#   "recommendations": [...]
# }

# MCP cost ranking
mcp_costs = auditor.analyze_mcp_costs()
print(mcp_costs)
# Ranks skills by cost impact

# Get recommendations
recs = auditor.get_recommendations()
for rec in recs:
    print(f"Save ${rec['savings']}: {rec['suggestion']}")

# Detect anomalies
anomalies = auditor.detect_anomalies()
for anomaly in anomalies:
    print(f"Anomaly: {anomaly}")
```

---

## Common Workflows

### Workflow 1: Set Up Department Tracking

```python
from pycostaudit.multi_org_manager import OrganizationManager, UserRole

manager = OrganizationManager()

# Create organization
org = manager.create_organization("ACME Corp")

# Create departments
eng = manager.create_department(org.id, "Engineering")
data = manager.create_department(org.id, "Data Science")
sales = manager.create_department(org.id, "Sales")

# Create sub-departments
backend = manager.create_department(eng.id, "Backend", parent_dept_id=eng.id)
frontend = manager.create_department(eng.id, "Frontend", parent_dept_id=eng.id)

# Assign users
manager.assign_user_to_department(
    "alice@acme.com",
    backend.id,
    UserRole.MANAGER
)

manager.assign_user_to_department(
    "bob@acme.com",
    frontend.id,
    UserRole.MEMBER
)

# Get org costs
costs = manager.get_org_total_cost(org.id)
print(f"Total org cost: ${costs}")

# Get breakdown by department
breakdown = manager.get_org_cost_breakdown(org.id)
for dept, cost in breakdown.items():
    print(f"{dept}: ${cost}")
```

### Workflow 2: Create Custom Reports

```python
from pycostaudit.custom_report_builder import (
    CustomReport, ReportType, ExportFormat
)
from pycostaudit.advanced_filters import AdvancedFilter, FilterOperator

# Create report
report_builder = CustomReport(
    "Weekly Cost Report",
    ReportType.COST_BREAKDOWN,
    "Analysis of costs this week"
)

# Add filter: costs > $5
report_builder.with_filter(
    FilterOperator.GT, "total_cost", 5.0
)

# Add aggregation
report_builder.with_aggregation("total_cost", "SUM")

# Add custom section
report_builder.add_section(
    title="Top Operations",
    description="Operations costing most",
    data=top_operations
)

# Build report
built_report = report_builder.build()

# Export in multiple formats
json_output = built_report.export(ExportFormat.JSON)
html_output = built_report.export(ExportFormat.HTML)
pdf_bytes = built_report.export(ExportFormat.PDF)
excel_bytes = built_report.export(ExportFormat.EXCEL)

# Save files
with open("report.pdf", "wb") as f:
    f.write(pdf_bytes)

with open("report.xlsx", "wb") as f:
    f.write(excel_bytes)
```

### Workflow 3: Set Up Compliance Monitoring

```python
from pycostaudit.compliance_audit import (
    AuditLogger, AuditEventType, ComplianceManager
)

logger = AuditLogger()

# Log user access
logger.log_event(
    event_type=AuditEventType.DATA_ACCESSED,
    user_id="alice@company.com",
    org_id="org123",
    resource_type="report",
    resource_id="report456",
    description="User downloaded cost report"
)

# Log permission changes
logger.log_event(
    event_type=AuditEventType.PERMISSION_GRANTED,
    user_id="admin@company.com",
    org_id="org123",
    resource_type="department",
    resource_id="dept789",
    description="Granted alice access to Engineering dept"
)

# Retrieve logs
events = logger.get_user_events("alice@company.com")

# Check compliance
compliance = ComplianceManager()
checkpoint = compliance.create_checkpoint(
    org_id="org123",
    standard="SOC_2"
)

soc2_status = compliance.check_soc_2_compliance(org_id="org123")
print(f"SOC 2 Compliant: {soc2_status}")

# Generate reports for auditors
report = compliance.generate_compliance_report("org123")
```

### Workflow 4: Export to Observability

```python
from pycostaudit.observability_export import ObservabilityExporter, ExportFormat

exporter = ObservabilityExporter()

# Export to Prometheus
config = {
    "format": ExportFormat.PROMETHEUS,
    "endpoint": "http://localhost:9090",
    "batch_size": 100
}

metrics = exporter.export_metrics(config)

# Export to Datadog
config = {
    "format": ExportFormat.DATADOG,
    "endpoint": "https://api.datadoghq.com",
    "api_key": "your-datadog-key",
    "batch_size": 50
}

traces = exporter.export_traces(config)

# Export to New Relic
config = {
    "format": ExportFormat.NEW_RELIC,
    "api_key": "your-nr-key",
    "account_id": "123456"
}

exporter.export_metrics(config)
```

---

## API Reference

### PyCostAudit Class

Main entry point for cost tracking.

```python
class PyCostAudit:
    def __init__(self, db_path: str = "~/.pycostaudit/costs.db")
    def track_operation(self, operation: Operation) -> CostData
    def start_session(self, name: Optional[str]) -> str
    def end_session(self, session_id: str) -> dict
    def analyze_daily() -> dict
    def analyze_session(session_id: str) -> dict
    def get_recommendations() -> List[dict]
    def detect_anomalies() -> List[dict]
    def compare_models(tokens_input: int, tokens_output: int) -> dict
    def forecast_quarterly() -> dict
    def compare_billing_plans() -> dict
```

### AdvancedFilter Class

Build complex cost analysis queries.

```python
from pycostaudit.advanced_filters import (
    AdvancedFilter, FilterOperator, Aggregator
)

# Create filter
f = AdvancedFilter()
f.add_condition(FilterOperator.GT, "total_cost", 5.0)
f.add_condition(FilterOperator.BETWEEN, "timestamp", [start, end])

# Group and aggregate
agg = Aggregator()
agg.group_by("operation_type")
agg.add_aggregation("total_cost", AggregationFunction.SUM)
agg.add_aggregation("count", AggregationFunction.COUNT)

# Time bucket
agg.time_bucket_by(TimeBucket.DAILY)

# Execute
results = agg.execute(data)
```

### OrganizationManager Class

Multi-org and department management.

```python
from pycostaudit.multi_org_manager import OrganizationManager

manager = OrganizationManager()

# Org management
org = manager.create_organization("Company Name")
dept = manager.create_department(org.id, "Dept Name")

# User management
manager.assign_user_to_department(user_id, dept.id, role)

# Cost aggregation
total_cost = manager.get_org_total_cost(org.id)
breakdown = manager.get_org_cost_breakdown(org.id)
```

---

## Troubleshooting

### Problem: "Module not found" after installation

**Solution:**
```bash
# Reinstall
pip uninstall pycostaudit
pip install pycostaudit

# Verify
python3 -c "import pycostaudit; print('OK')"
```

### Problem: Database file permissions error

**Solution:**
```bash
# Check permissions
ls -la ~/.pycostaudit/

# Fix permissions
chmod 755 ~/.pycostaudit/
```

### Problem: No costs being tracked

**Solution:**
```python
# Verify database is initialized
from pycostaudit import PyCostAudit
auditor = PyCostAudit()

# Check if operations exist
breakdown = auditor.analyze_daily()
print(breakdown)  # Should show costs if tracking

# If empty, start tracking:
auditor.track_operation(
    operation_type="api_call",
    tokens_input=100,
    tokens_output=50,
    model="claude-3-5-sonnet"
)
```

### Problem: Alerts not triggering

**Solution:**
```bash
# Check alert setup
cost-alert list

# Verify webhook/email configuration
# For Slack: Test webhook URL manually
curl -X POST -d '{"text":"Test"}' YOUR_WEBHOOK_URL

# For Email: Check SMTP settings
python3 -c "
from pycostaudit import PyCostAudit
auditor = PyCostAudit()
auditor.test_email_alert('your-email@example.com')
"
```

---

## Next Steps

- 📖 [Read ARCHITECTURE.md](./ARCHITECTURE.md) for technical details
- 🔧 [Check ALERTS_SETUP.md](./ALERTS_SETUP.md) for alert configuration
- 📊 [See REPORTS_SETUP.md](./REPORTS_SETUP.md) for automated reports
- 🌐 [View OPENTELEMETRY_INTEGRATION.md](./OPENTELEMETRY_INTEGRATION.md) for observability

For questions or issues, visit: https://github.com/Mullassery/PyCostAudit/issues
