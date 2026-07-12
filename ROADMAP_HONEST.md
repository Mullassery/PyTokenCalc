# PyCostAudit Roadmap

**Current Version:** v1.0.0  
**Last Updated:** July 2026  
**Status:** Stable for core tracking; dashboard and advanced features in development

---

## Known Limitations (v1.0.0)

### 🔴 Blocking Issues
- **Dashboard React frontend:** Built but **not production-ready**
  - [ ] Error handling incomplete
  - [ ] Limited test coverage
  - [ ] Authentication not fully wired
  - **Impact:** Use CLI/API only for production; web UI for evaluation
  - **Fix timeline:** v1.2.0 (Q3 2026)

### 🟡 Experimental Features
- **ML forecasting:** ARIMA/Exponential Smoothing/Ensemble implemented but unvalidated
  - [ ] Confidence intervals (claims 95% accuracy) need statistical validation
  - [ ] Only tested on 30-180 day forecasts
  - [ ] Not suitable for <30 day or >1 year predictions
  - **Impact:** Use for trend detection only, not financial planning
  - **Fix timeline:** v1.1.0 (Q3 2026) with actual validation

- **Compliance frameworks:** Only 3 of 6 fully implemented
  - ✅ SOC 2, HIPAA, GDPR (functional)
  - ❌ ISO 27001, PCI DSS (templates only, not validated)
  - ❌ Custom (framework structure exists, not tested)
  - **Impact:** Only use for SOC 2/HIPAA/GDPR audits
  - **Fix timeline:** v1.3.0 (Q4 2026) for ISO 27001 + PCI DSS

### 🟢 Shipping/Stable (v1.0.0)
- ✅ Core cost tracking by operation/model/user
- ✅ Anomaly detection (Z-score based)
- ✅ CSV/JSON export
- ✅ Multi-tenant support
- ✅ CLI interface

---

## TODOs in Code (2 found)

1. **ml_forecasting_service.py:** Confidence interval calculation needs statistical review
2. **compliance_reporting.py:** PCI DSS compliance scoring stub

---

## 🔒 Security Issues (See SECURITY_AUDIT.md)

### CRITICAL — v1.0.1
- [ ] **Remove pickle deserialization** (RCE vulnerability)
- [ ] **Audit all SQL injection patterns** (5 instances found)
- [ ] **Remove secrets from logs** (18 instances of API key/password logging)

### HIGH — v1.0.1
- [ ] **Pin all dependency versions** (0 pinned, 16 floating)

### HIGH — v1.1.0
- [ ] **Add specific exception handling** (42 broad exception handlers)
- [ ] **JWT authentication on dashboard** (no token validation currently)
- [ ] **Environment-based configuration** (29 hardcoded values)

### MEDIUM — v1.2.0
- [ ] **Add CSRF protection** (partial CORS only)
- [ ] **Fix error information disclosure** (stack traces visible)

---

## Roadmap

### v1.0.1 (Q3 2026) — Security + Bug Fixes
- [ ] **[SECURITY]** Remove pickle usage; use JSON instead
- [ ] **[SECURITY]** Audit and parametrize all SQL queries
- [ ] **[SECURITY]** Strip API keys/passwords from logs
- [ ] **[SECURITY]** Pin all dependency versions
- [ ] Fix dashboard error handling
- [ ] Add missing test cases for forecasting
- [ ] Document authentication setup

### v1.1.0 (Q3 2026) — Forecasting Validation
- [ ] Statistical validation of confidence intervals
- [ ] Add more test data (various forecast horizons)
- [ ] Update README with accuracy disclaimers
- [ ] Add forecasting performance benchmarks

### v1.2.0 (Q3 2026) — Dashboard Production Ready
- [ ] Complete error handling and retry logic
- [ ] Add comprehensive test suite (>80% coverage)
- [ ] Production deployment guide
- [ ] Performance optimization for 1M+ cost events

### v1.3.0 (Q4 2026) — Full Compliance Support
- [ ] ISO 27001 compliance framework
- [ ] PCI DSS compliance validation
- [ ] Custom framework builder
- [ ] Compliance scoring validation

### v2.0.0 (Q4 2026) — Advanced Features
- [ ] Real-time streaming cost ingestion
- [ ] Predictive budget alerts
- [ ] Cost optimization recommendations with ROI
- [ ] Integration with cloud cost management tools

---

## Not Planned
- Real-time billing replacement (use Anthropic's official billing)
- Auto-optimization (recommendations only)
- Multi-model provider support (Claude only for now)
