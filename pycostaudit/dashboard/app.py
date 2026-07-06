"""
FastAPI backend for PyCostAudit Dashboard
Provides REST API for cost tracking, budgeting, and alerting.
"""

from fastapi import FastAPI, Depends, HTTPException, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, desc, and_
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import json

from .models import Base, User, Cost, Budget, Alert, CostSummary

# Database setup
DATABASE_URL = "sqlite:///./pycostaudit.db"  # SQLite for dev (use PostgreSQL in prod)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="PyCostAudit Dashboard API",
    description="Real-time cost tracking and alerting for LLM APIs",
    version="0.5.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()


# ============================================================================
# Dependencies
# ============================================================================

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    # In production, verify JWT token
    # For demo, use token as user_id
    user_id = credentials.credentials

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return user


# ============================================================================
# Auth Endpoints
# ============================================================================

@app.post("/api/auth/register")
def register(email: str, name: str, password: str, db: Session = Depends(get_db)):
    """Register new user"""
    # Check if user exists
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = User(email=email, name=name, password_hash=password)  # Hash in production
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"id": user.id, "email": user.email, "name": user.name}


@app.post("/api/auth/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    """Login user"""
    user = db.query(User).filter(User.email == email).first()
    if not user or user.password_hash != password:  # Verify hash in production
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"token": user.id, "user": {"id": user.id, "email": user.email, "name": user.name}}


@app.get("/api/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return {"id": current_user.id, "email": current_user.email, "name": current_user.name}


# ============================================================================
# Cost Endpoints
# ============================================================================

@app.get("/api/costs")
def get_costs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    period: str = Query("7d"),
    provider: Optional[str] = None,
    model: Optional[str] = None,
    limit: int = 100
):
    """Get costs with optional filters"""
    # Calculate date range
    if period == "24h":
        start_date = datetime.utcnow() - timedelta(hours=24)
    elif period == "7d":
        start_date = datetime.utcnow() - timedelta(days=7)
    elif period == "30d":
        start_date = datetime.utcnow() - timedelta(days=30)
    else:
        start_date = datetime.utcnow() - timedelta(days=7)

    # Build query
    query = db.query(Cost).filter(
        and_(
            Cost.user_id == current_user.id,
            Cost.timestamp >= start_date
        )
    )

    if provider:
        query = query.filter(Cost.provider == provider)
    if model:
        query = query.filter(Cost.model == model)

    costs = query.order_by(desc(Cost.timestamp)).limit(limit).all()

    return {
        "data": [
            {
                "id": c.id,
                "timestamp": c.timestamp.isoformat(),
                "provider": c.provider,
                "model": c.model,
                "input_tokens": c.input_tokens,
                "output_tokens": c.output_tokens,
                "input_cost": c.input_cost,
                "output_cost": c.output_cost,
                "total_cost": c.total_cost,
            }
            for c in costs
        ],
        "count": len(costs),
        "period": period,
    }


@app.get("/api/costs/summary")
def get_cost_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get cost summary for dashboard"""
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Get costs for different periods
    total_today = db.query(Cost).filter(
        and_(
            Cost.user_id == current_user.id,
            Cost.timestamp >= today
        )
    ).with_entities(lambda: func.sum(Cost.total_cost)).scalar() or 0

    total_7d = db.query(Cost).filter(
        and_(
            Cost.user_id == current_user.id,
            Cost.timestamp >= week_ago
        )
    ).with_entities(lambda: func.sum(Cost.total_cost)).scalar() or 0

    total_30d = db.query(Cost).filter(
        and_(
            Cost.user_id == current_user.id,
            Cost.timestamp >= month_ago
        )
    ).with_entities(lambda: func.sum(Cost.total_cost)).scalar() or 0

    # Get provider breakdown
    costs = db.query(Cost).filter(
        and_(
            Cost.user_id == current_user.id,
            Cost.timestamp >= month_ago
        )
    ).all()

    provider_breakdown = {}
    model_breakdown = {}
    for cost in costs:
        provider_breakdown[cost.provider] = provider_breakdown.get(cost.provider, 0) + cost.total_cost
        model_breakdown[cost.model] = model_breakdown.get(cost.model, 0) + cost.total_cost

    return {
        "total_today": float(total_today),
        "total_7d": float(total_7d),
        "total_30d": float(total_30d),
        "by_provider": provider_breakdown,
        "by_model": model_breakdown,
        "num_operations": len(costs),
    }


@app.get("/api/breakdown")
def get_breakdown(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    group_by: str = Query("provider"),
    period: str = Query("30d"),
):
    """Get cost breakdown by provider, model, or operation"""
    # Calculate date range
    if period == "7d":
        start_date = datetime.utcnow() - timedelta(days=7)
    elif period == "30d":
        start_date = datetime.utcnow() - timedelta(days=30)
    else:
        start_date = datetime.utcnow() - timedelta(days=7)

    costs = db.query(Cost).filter(
        and_(
            Cost.user_id == current_user.id,
            Cost.timestamp >= start_date
        )
    ).all()

    breakdown = {}
    for cost in costs:
        if group_by == "provider":
            key = cost.provider
        elif group_by == "model":
            key = cost.model
        else:
            key = cost.provider

        if key not in breakdown:
            breakdown[key] = {
                "total_cost": 0,
                "count": 0,
                "input_tokens": 0,
                "output_tokens": 0,
            }

        breakdown[key]["total_cost"] += cost.total_cost
        breakdown[key]["count"] += 1
        breakdown[key]["input_tokens"] += cost.input_tokens
        breakdown[key]["output_tokens"] += cost.output_tokens

    return {
        "breakdown": breakdown,
        "group_by": group_by,
        "period": period,
    }


# ============================================================================
# Budget Endpoints
# ============================================================================

@app.get("/api/budget/status")
def get_budget_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get budget status"""
    budget = db.query(Budget).filter(Budget.user_id == current_user.id).first()

    if not budget:
        return {"error": "No budget set"}

    # Get current spend
    start_date = budget.period_start
    spent = db.query(Cost).filter(
        and_(
            Cost.user_id == current_user.id,
            Cost.timestamp >= start_date,
            Cost.timestamp <= budget.period_end
        )
    ).with_entities(lambda: func.sum(Cost.total_cost)).scalar() or 0

    percent_used = (spent / budget.amount * 100) if budget.amount > 0 else 0

    # Forecast
    days_in_period = (budget.period_end - start_date).days or 1
    days_elapsed = (datetime.utcnow() - start_date).days or 1
    daily_rate = spent / days_elapsed if days_elapsed > 0 else 0
    projected_end = spent + (daily_rate * (days_in_period - days_elapsed))

    return {
        "budget_amount": budget.amount,
        "spent": float(spent),
        "remaining": float(max(0, budget.amount - spent)),
        "percent_used": float(percent_used),
        "period": budget.period,
        "period_start": budget.period_start.isoformat(),
        "period_end": budget.period_end.isoformat(),
        "forecast_end_amount": float(projected_end),
        "daily_rate": float(daily_rate),
    }


@app.post("/api/budget/update")
def update_budget(
    amount: float,
    period: str = "monthly",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update budget"""
    budget = db.query(Budget).filter(Budget.user_id == current_user.id).first()

    now = datetime.utcnow()
    if period == "monthly":
        period_end = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
    elif period == "weekly":
        period_end = now + timedelta(days=7 - now.weekday())
    else:
        period_end = now + timedelta(days=1)

    if budget:
        budget.amount = amount
        budget.period = period
        budget.period_end = period_end
    else:
        budget = Budget(
            user_id=current_user.id,
            amount=amount,
            period=period,
            period_start=now,
            period_end=period_end,
        )
        db.add(budget)

    db.commit()
    db.refresh(budget)

    return {"id": budget.id, "amount": budget.amount, "period": budget.period}


# ============================================================================
# Alert Endpoints
# ============================================================================

@app.get("/api/alerts")
def get_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
):
    """Get recent alerts"""
    alerts = db.query(Alert).filter(
        Alert.user_id == current_user.id
    ).order_by(desc(Alert.created_at)).limit(limit).all()

    return {
        "data": [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "provider": a.provider,
                "cost_amount": a.cost_amount,
                "created_at": a.created_at.isoformat(),
                "acknowledged": bool(a.acknowledged),
            }
            for a in alerts
        ],
        "count": len(alerts),
    }


@app.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark alert as acknowledged"""
    alert = db.query(Alert).filter(
        and_(
            Alert.id == alert_id,
            Alert.user_id == current_user.id
        )
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.acknowledged = 1
    alert.acknowledged_at = datetime.utcnow()
    db.commit()

    return {"id": alert.id, "acknowledged": True}


# ============================================================================
# WebSocket for Real-Time Updates
# ============================================================================

connected_clients = set()


@app.websocket("/ws/costs")
async def websocket_costs(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time cost updates"""
    await websocket.accept()
    connected_clients.add((websocket, user_id))

    try:
        while True:
            # Keep connection open
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        connected_clients.discard((websocket, user_id))


async def broadcast_cost_update(user_id: str, cost_data: dict):
    """Broadcast cost update to all connected clients of a user"""
    for websocket, client_user_id in connected_clients:
        if client_user_id == user_id:
            try:
                await websocket.send_json({
                    "type": "cost_update",
                    "data": cost_data
                })
            except Exception as e:
                print(f"Error broadcasting: {e}")


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "0.6.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
