# PyCostAudit Security Audit

**Last Audited:** July 2026  
**Status:** Multiple vulnerabilities found; see roadmap for fixes

---

## 🔴 CRITICAL Vulnerabilities

### 1. Pickle Deserialization (CVE-class Risk)
**Location:** `pycostaudit/ml_token_estimator.py:pickle.load(f)`  
**Risk:** Untrusted pickle data leads to remote code execution  
**Severity:** CRITICAL  
**Impact:** If an attacker provides a malicious pickle file, they can execute arbitrary code

```python
# VULNERABLE
data = pickle.load(f)  # Can execute arbitrary code
```

**Recommended Fix:**
```python
# SAFE
import json
data = json.load(f)  # Use JSON instead of pickle
```

**Timeline:** v1.0.1 (Q3 2026) — Remove pickle usage entirely

---

### 2. SQL Injection (5 instances found)
**Location:** Database query construction in `database.py`, `compliance_audit.py`  
**Risk:** Attacker can bypass queries, extract data, modify records  
**Severity:** CRITICAL  
**Example Pattern Found:**
```python
# Potentially vulnerable pattern (f-strings or .format() in SQL)
query = f"SELECT * FROM costs WHERE user_id = '{user_id}'"  # UNSAFE
```

**Recommended Fix:**
```python
# SAFE
cursor.execute("SELECT * FROM costs WHERE user_id = ?", (user_id,))
```

**Timeline:** v1.0.1 (Q3 2026) — Audit and parametrize all SQL queries

---

## 🟡 HIGH Priority Issues

### 3. Secrets Exposed in Logs (18 instances)
**Location:** Various logging statements  
**Risk:** API keys, passwords, tokens appear in logs/output  
**Severity:** HIGH  
**Example:**
```python
# VULNERABLE
logger.debug(f"SMTP password: {smtp_password}")
print(f"API key: {api_key}")
```

**Recommended Fix:**
```python
# SAFE
logger.debug("SMTP authentication successful")  # Don't log credentials
```

**Audit Findings:**
- `alerts_service.py`: SMTP password logged
- `anthropic_integration.py`: API keys in debug output
- 16 other instances across codebase

**Timeline:** v1.0.1 (Q3 2026) — Remove all credentials from logs

---

### 4. Broad Exception Handling (42 instances)
**Location:** Throughout codebase  
**Risk:** May mask real errors; information disclosure in exception details  
**Severity:** HIGH  
**Example:**
```python
# VULNERABLE - swallows all exceptions
try:
    process_cost()
except Exception:
    pass  # Silent failure, hard to debug
```

**Recommended Fix:**
```python
# SAFE - specific handling
try:
    process_cost()
except ValueError as e:
    logger.error("Invalid cost format")  # Don't include raw error
except Exception as e:
    logger.critical("Unexpected error in cost processing")  # Generic message
```

**Timeline:** v1.1.0 (Q3 2026) — Specific exception handling + non-disclosure error messages

---

### 5. No Dependency Version Pinning
**Location:** `pyproject.toml`  
**Risk:** Transitive dependencies can introduce vulnerabilities  
**Severity:** HIGH  
**Finding:** 0 pinned versions, 16 floating versions

```toml
# VULNERABLE
anthropic = ">=0.7.0"  # Can pull broken/vulnerable versions
fastapi = "~=0.100"    # Floating versions

# RECOMMENDED
anthropic = "0.7.6"    # Pin exact version
fastapi = "0.100.0"    # Pin exact version
```

**Action Items:**
- [ ] Pin all direct dependencies to exact versions
- [ ] Use `pip-audit` to check for known vulnerabilities
- [ ] Create dependency update policy (monthly, with security testing)

**Timeline:** v1.0.1 (Q3 2026)

---

## 🔵 MEDIUM Priority Issues

### 6. No JWT/Token Validation in API
**Location:** `pycostaudit/dashboard/app.py`  
**Risk:** Unauthenticated access to cost data, multi-tenant isolation break  
**Severity:** MEDIUM (HIGH if exposed to internet)  
**Finding:** RBAC patterns found (39 instances) but no token verification

**Recommended:**
```python
# Add token verification
from fastapi import Depends, HTTPException
from jose import jwt

async def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id

@app.get("/api/costs")
async def get_costs(user_id: str = Depends(verify_token)):
    # Only return costs for authenticated user
    return costs_for_user(user_id)
```

**Timeline:** v1.2.0 (Q3 2026) — Add JWT authentication

---

### 7. Hardcoded Configuration
**Location:** 29 instances of hardcoded values  
**Risk:** localhost/127.0.0.1 defaults may be used in production  
**Severity:** MEDIUM  
**Examples:**
```python
# VULNERABLE
jaeger_host: str = "localhost"  # Shouldn't be default for production
prometheus_port: int = 8000     # Could conflict

# RECOMMENDED
jaeger_host: str = os.getenv("JAEGER_HOST", "localhost")
prometheus_port: int = int(os.getenv("PROMETHEUS_PORT", "8000"))
```

**Timeline:** v1.1.0 (Q3 2026) — Environment-based config

---

### 8. Missing CORS/CSRF Protection (Partial)
**Location:** `pycostaudit/dashboard/app.py`  
**Status:** CORS middleware present (3 instances); CSRF protection unclear  
**Recommendation:** Explicit CSRF tokens for state-changing operations

**Timeline:** v1.2.0 (Q3 2026) — Add CSRF protection, review CORS policy

---

### 9. Information Disclosure in Errors
**Location:** Dashboard error handlers  
**Risk:** Stack traces, SQL errors, file paths exposed to users  
**Severity:** MEDIUM  
**Example:**
```python
# VULNERABLE
try:
    query_db()
except Exception as e:
    return {"error": str(e)}  # Exposes database schema!

# SAFE
except Exception as e:
    logger.exception("Query failed")  # Log full error
    return {"error": "Database error"}  # Generic user message
```

**Timeline:** v1.1.0 (Q3 2026)

---

## 🔵 LOW Priority / Best Practices

### 10. No Secrets Scanning in CI/CD
**Status:** GitHub Actions workflows don't scan for secrets  
**Recommendation:** Add `truffleHog` or `git-secrets` to CI  
**Timeline:** v1.1.0 (Q3 2026)

### 11. No Input Validation Standardization
**Instances:** 228 functions with string parameters; only 36 use validation  
**Risk:** XSS, injection attacks via untrusted input  
**Recommendation:** Pydantic models for all external input  
**Timeline:** v1.3.0 (Q4 2026)

### 12. No Rate Limiting on APIs
**Risk:** DoS attacks on dashboard endpoints  
**Recommendation:** Add rate limiting middleware  
**Timeline:** v1.3.0 (Q4 2026)

---

## Security Roadmap

| Issue | Severity | Target | Effort |
|-------|----------|--------|--------|
| Remove pickle usage | CRITICAL | v1.0.1 | 1 day |
| Audit SQL injection | CRITICAL | v1.0.1 | 2 days |
| Remove secrets from logs | HIGH | v1.0.1 | 1 day |
| Pin dependencies | HIGH | v1.0.1 | 1 day |
| Specific exception handling | HIGH | v1.1.0 | 2 days |
| Environment-based config | MEDIUM | v1.1.0 | 1 day |
| JWT authentication | MEDIUM | v1.2.0 | 3 days |
| CSRF protection | MEDIUM | v1.2.0 | 2 days |
| Input validation (Pydantic) | LOW | v1.3.0 | 3 days |
| Rate limiting | LOW | v1.3.0 | 1 day |

---

## Testing Recommendations

1. **Dependency Scanning:** Add `pip-audit` to CI
   ```bash
   pip-audit --strict
   ```

2. **SAST (Static Analysis):** Run `bandit` on Python code
   ```bash
   bandit -r pycostaudit/ -ll
   ```

3. **SQL Injection Testing:** Manual code review + `sqlmap` testing
4. **Pickle Audit:** Replace all `pickle.load()` with safe alternatives

---

## Deployment Recommendations

- ❌ Do NOT expose dashboard to internet until v1.2.0 (JWT added)
- ✓ Use environment variables for all secrets (never hardcode)
- ✓ Enable audit logging (already implemented)
- ✓ Restrict database user permissions (no admin account for application)
