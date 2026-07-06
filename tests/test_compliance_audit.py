"""
Tests for compliance and audit system.
"""

import pytest
from datetime import datetime, timedelta
from pycostaudit.compliance_audit import (
    AuditLogger,
    RetentionPolicyManager,
    ComplianceManager,
    AuditEventType,
    DataClassification,
    ComplianceStandard
)


@pytest.fixture
def audit_logger():
    """Create audit logger"""
    return AuditLogger("acme")


@pytest.fixture
def retention_manager():
    """Create retention policy manager"""
    return RetentionPolicyManager()


@pytest.fixture
def compliance_manager():
    """Create compliance manager"""
    return ComplianceManager()


class TestAuditLogger:
    """Test audit logging"""

    def test_log_event(self, audit_logger):
        """Test logging event"""
        log = audit_logger.log_event(
            AuditEventType.USER_CREATED,
            "admin",
            "user",
            "user123",
            "create",
            "User created",
            "192.168.1.1",
            "Mozilla/5.0"
        )

        assert log.log_id is not None
        assert log.user_id == "admin"
        assert log.resource_id == "user123"
        assert log.status == "success"

    def test_log_failed_event(self, audit_logger):
        """Test logging failed event"""
        log = audit_logger.log_event(
            AuditEventType.UNAUTHORIZED_ACCESS,
            "alice",
            "report",
            "report123",
            "access",
            "Unauthorized access attempt",
            "10.0.0.1",
            "Chrome",
            status="failure",
            error_message="Access denied"
        )

        assert log.status == "failure"
        assert log.error_message == "Access denied"

    def test_log_data_access(self, audit_logger):
        """Test logging data access"""
        access = audit_logger.log_access(
            "alice",
            "cost_data",
            "cost123",
            "read",
            DataClassification.CONFIDENTIAL,
            "Monthly reporting"
        )

        assert access.access_id is not None
        assert access.access_type == "read"
        assert access.data_sensitivity == DataClassification.CONFIDENTIAL
        assert access.granted is True

    def test_log_denied_access(self, audit_logger):
        """Test logging denied access"""
        access = audit_logger.log_access(
            "alice",
            "cost_data",
            "cost456",
            "delete",
            DataClassification.RESTRICTED,
            "Not authorized",
            granted=False,
            denial_reason="Insufficient permissions"
        )

        assert access.granted is False
        assert access.denial_reason == "Insufficient permissions"

    def test_get_user_events(self, audit_logger):
        """Test retrieving user events"""
        audit_logger.log_event(
            AuditEventType.USER_LOGIN,
            "alice",
            "session",
            "session1",
            "login",
            "User logged in",
            "192.168.1.1",
            "Firefox"
        )

        audit_logger.log_event(
            AuditEventType.DATA_ACCESSED,
            "alice",
            "report",
            "report1",
            "view",
            "Report viewed",
            "192.168.1.1",
            "Firefox"
        )

        events = audit_logger.get_user_events("alice")
        assert len(events) == 2

    def test_get_failed_events(self, audit_logger):
        """Test retrieving failed events"""
        for i in range(3):
            audit_logger.log_event(
                AuditEventType.UNAUTHORIZED_ACCESS,
                f"user{i}",
                "resource",
                f"res{i}",
                "access",
                "Unauthorized",
                "10.0.0.1",
                "Chrome",
                status="failure"
            )

        failed = audit_logger.get_failed_events()
        assert len(failed) == 3

    def test_get_sensitive_data_access(self, audit_logger):
        """Test retrieving sensitive data access"""
        audit_logger.log_access(
            "alice",
            "data",
            "data1",
            "read",
            DataClassification.CONFIDENTIAL,
            "Review"
        )

        audit_logger.log_access(
            "bob",
            "data",
            "data2",
            "read",
            DataClassification.RESTRICTED,
            "Analysis"
        )

        sensitive = audit_logger.get_sensitive_data_access()
        assert len(sensitive) == 2

    def test_get_unauthorized_attempts(self, audit_logger):
        """Test retrieving unauthorized attempts"""
        for i in range(5):
            audit_logger.log_event(
                AuditEventType.UNAUTHORIZED_ACCESS,
                f"hacker{i}",
                "system",
                "admin_panel",
                "access",
                "Unauthorized access",
                "203.0.113.1",
                "Unknown",
                status="failure"
            )

        attempts = audit_logger.get_unauthorized_attempts()
        assert len(attempts) == 5


class TestRetentionPolicies:
    """Test data retention policies"""

    def test_create_retention_policy(self, retention_manager):
        """Test creating retention policy"""
        policy = retention_manager.create_policy(
            "acme",
            "audit_logs",
            retention_days=365,
            archive_days=90,
            description="Annual retention for audit logs"
        )

        assert policy.policy_id is not None
        assert policy.retention_days == 365
        assert policy.archive_days == 90

    def test_get_policies_by_org(self, retention_manager):
        """Test retrieving policies by org"""
        retention_manager.create_policy("acme", "audit_logs", 365, 90)
        retention_manager.create_policy("acme", "cost_data", 730, 180)

        policies = retention_manager.get_policies_by_org("acme")
        assert len(policies) == 2

    def test_should_retain_data(self, retention_manager):
        """Test data retention check"""
        retention_manager.create_policy("acme", "audit_logs", 365, 90)

        # Recent data should be retained
        recent_date = datetime.utcnow() - timedelta(days=10)
        assert retention_manager.should_retain_data("acme", "audit_logs", recent_date)

        # Old data should be deleted
        old_date = datetime.utcnow() - timedelta(days=400)
        assert not retention_manager.should_retain_data("acme", "audit_logs", old_date)

    def test_should_archive_data(self, retention_manager):
        """Test data archival check"""
        retention_manager.create_policy("acme", "audit_logs", 365, 90)

        # Recent data should not be archived
        recent_date = datetime.utcnow() - timedelta(days=30)
        assert not retention_manager.should_archive_data("acme", "audit_logs", recent_date)

        # Older data should be archived
        old_date = datetime.utcnow() - timedelta(days=120)
        assert retention_manager.should_archive_data("acme", "audit_logs", old_date)

    def test_no_policy_defaults(self, retention_manager):
        """Test default behavior without policy"""
        # Without policy, data is retained
        date = datetime.utcnow() - timedelta(days=500)
        assert retention_manager.should_retain_data("acme", "unknown", date)

        # Without policy, data is not archived
        assert not retention_manager.should_archive_data("acme", "unknown", date)


class TestComplianceChecks:
    """Test compliance checking"""

    def test_create_checkpoint(self, compliance_manager):
        """Test creating compliance checkpoint"""
        checkpoint = compliance_manager.create_checkpoint("acme", ComplianceStandard.SOC_2)

        assert checkpoint.checkpoint_id is not None
        assert checkpoint.org_id == "acme"
        assert checkpoint.standard == ComplianceStandard.SOC_2

    def test_soc_2_compliance_check(self, audit_logger, retention_manager, compliance_manager):
        """Test SOC 2 compliance check"""
        # Set up some compliance data
        retention_manager.create_policy("acme", "audit_logs", 365, 90)

        # Log some events
        for i in range(5):
            audit_logger.log_event(
                AuditEventType.CONFIG_CHANGED,
                "admin",
                "config",
                f"config{i}",
                "update",
                "Configuration changed",
                "192.168.1.1",
                "Firefox"
            )

        checkpoint = compliance_manager.check_soc_2_compliance(
            audit_logger,
            retention_manager,
            "acme"
        )

        assert checkpoint.status in ["compliant", "non_compliant"]

    def test_soc_2_issues_detected(self, audit_logger, retention_manager, compliance_manager):
        """Test SOC 2 issues detection"""
        # No retention policies = issue
        checkpoint = compliance_manager.check_soc_2_compliance(
            audit_logger,
            retention_manager,
            "acme"
        )

        assert checkpoint.status == "non_compliant"
        assert len(checkpoint.issues) > 0

    def test_gdpr_compliance_check(self, audit_logger, compliance_manager):
        """Test GDPR compliance check"""
        # Log some sensitive data access
        audit_logger.log_access(
            "alice",
            "customer_data",
            "cust123",
            "read",
            DataClassification.CONFIDENTIAL,
            "Customer analysis"
        )

        checkpoint = compliance_manager.check_gdpr_compliance(audit_logger, "acme")

        assert checkpoint.status in ["compliant", "non_compliant"]
        assert checkpoint.standard == ComplianceStandard.GDPR

    def test_gdpr_missing_purpose_detected(self, audit_logger, compliance_manager):
        """Test GDPR missing purpose detection"""
        # Access without purpose
        audit_logger.log_access(
            "alice",
            "customer_data",
            "cust123",
            "read",
            DataClassification.RESTRICTED,
            ""  # No purpose
        )

        checkpoint = compliance_manager.check_gdpr_compliance(audit_logger, "acme")

        assert len(checkpoint.issues) > 0

    def test_get_latest_checkpoint(self, compliance_manager):
        """Test retrieving latest checkpoint"""
        cp1 = compliance_manager.create_checkpoint("acme", ComplianceStandard.SOC_2)

        # Create another checkpoint for same standard (later timestamp)
        cp2 = compliance_manager.create_checkpoint("acme", ComplianceStandard.SOC_2)

        latest = compliance_manager.get_latest_checkpoint("acme", ComplianceStandard.SOC_2)

        assert latest.checkpoint_id == cp2.checkpoint_id

    def test_generate_compliance_report(self, audit_logger, retention_manager, compliance_manager):
        """Test generating compliance report"""
        # Set up basic compliance
        retention_manager.create_policy("acme", "audit_logs", 365, 90)

        audit_logger.log_event(
            AuditEventType.CONFIG_CHANGED,
            "admin",
            "config",
            "config1",
            "update",
            "Configuration changed",
            "192.168.1.1",
            "Firefox"
        )

        # Check both standards
        compliance_manager.check_soc_2_compliance(audit_logger, retention_manager, "acme")
        compliance_manager.check_gdpr_compliance(audit_logger, "acme")

        report = compliance_manager.generate_compliance_report(
            "acme",
            [ComplianceStandard.SOC_2, ComplianceStandard.GDPR]
        )

        assert report["org_id"] == "acme"
        assert "standards" in report
        assert ComplianceStandard.SOC_2.value in report["standards"]
        assert ComplianceStandard.GDPR.value in report["standards"]


class TestAuditEventTypes:
    """Test various audit event types"""

    def test_user_lifecycle_events(self, audit_logger):
        """Test user lifecycle events"""
        audit_logger.log_event(
            AuditEventType.USER_CREATED,
            "admin",
            "user",
            "alice",
            "create",
            "User created",
            "192.168.1.1",
            "Firefox"
        )

        audit_logger.log_event(
            AuditEventType.ROLE_CHANGED,
            "admin",
            "user",
            "alice",
            "promote",
            "Role changed to manager",
            "192.168.1.1",
            "Firefox"
        )

        events = audit_logger.get_user_events("admin")
        assert len(events) == 2

    def test_data_operation_events(self, audit_logger):
        """Test data operation events"""
        audit_logger.log_event(
            AuditEventType.DATA_CREATED,
            "user1",
            "report",
            "report1",
            "create",
            "Report created",
            "192.168.1.1",
            "Chrome"
        )

        audit_logger.log_event(
            AuditEventType.DATA_EXPORTED,
            "user1",
            "report",
            "report1",
            "export",
            "Report exported to CSV",
            "192.168.1.1",
            "Chrome"
        )

        events = audit_logger.get_user_events("user1")
        assert len(events) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
