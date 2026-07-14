"""Secure configuration management using environment variables."""

import os
from pathlib import Path
from typing import Optional

class Config:
    """Application configuration from environment variables."""
    
    # Server
    SERVER_HOST = os.getenv("PYCOSTAUDIT_HOST", "localhost")
    SERVER_PORT = int(os.getenv("PYCOSTAUDIT_PORT", "8000"))
    DEBUG = os.getenv("PYCOSTAUDIT_DEBUG", "false").lower() == "true"
    
    # Database
    DATABASE_URL = os.getenv("PYCOSTAUDIT_DATABASE_URL", "sqlite:///~/.pycostaudit/costs.db")
    
    # SMTP (Email)
    SMTP_HOST = os.getenv("PYCOSTAUDIT_SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("PYCOSTAUDIT_SMTP_PORT", "587"))
    SMTP_USER = os.getenv("PYCOSTAUDIT_SMTP_USER")
    SMTP_PASSWORD = os.getenv("PYCOSTAUDIT_SMTP_PASSWORD")
    FROM_EMAIL = os.getenv("PYCOSTAUDIT_FROM_EMAIL", SMTP_USER)
    
    # Slack
    SLACK_WEBHOOK_URL = os.getenv("PYCOSTAUDIT_SLACK_WEBHOOK_URL")
    
    # Twilio (SMS)
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
    
    # Telemetry
    JAEGER_HOST = os.getenv("JAEGER_HOST", "localhost")
    JAEGER_PORT = int(os.getenv("JAEGER_PORT", "6831"))
    PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "8000"))
    
    @staticmethod
    def validate():
        """Validate required configuration."""
        if not Config.SMTP_USER and not Config.SLACK_WEBHOOK_URL:
            print("Warning: No SMTP or Slack credentials configured")
        return True

config = Config()
