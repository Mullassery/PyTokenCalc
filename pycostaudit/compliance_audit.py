"""
Compliance and audit system for SOC 2 readiness.
Comprehensive logging, tracking, and compliance reporting for enterprise deployments.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib


class AuditEventType(Enum):
    """Types of audit events"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"
    USER_UPDATED = "user_updated"
    ROLE_CHANGED = "role_changed"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    DATA_ACCESSED = "data_accessed"
    DATA_CREATED = "data_created"
    DATA_UPDATED = "data_updated"
    DATA_DELETED = "data_deleted"
    DATA_EXPORTED = "data_exported"
    CONFIG_CHANGED = "config_changed"
    API_KEY_CREATED = "api_key_created"
    API_KEY_DELETED = "api_key_deleted"
    ALERT_TRIGGERED = "alert_triggered"
    REPORT_GENERATED = "report_generated"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class DataClassification(Enum):
    """Data classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class ComplianceStandard(Enum):
    """Supported compliance standards"""
    SOC_2 = "soc_2"
    HIPAA = "hipaa"
    GDPR = "gdpr"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"


@dataclass
class AuditLog:
    """Single audit log entry"""
    log_id: str
    timestamp: datetime
    event_type: AuditEventType
    user_id: str
    org_id: str
    dept_id: Optional[str]
    resource_type: str  # e.g., "user", "organization", "report"
    resource_id: str  # ID of resource being acted upon
    action: str  # Specific action taken
    description: str
    ip_address: str
    user_agent: str
    status: str  # "success", "failure"
    error_message: Optional[str] = None
    data_classification: DataClassification = DataClassification.INTERNAL
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessLog:
    """Access logging for sensitive operations"""
    access_id: str
    timestamp: datetime
    user_id: str
    org_id: str
    resource_type: str
    resource_id: str
    access_type: str  # "read", "write", "delete", "export"
    data_sensitivity: DataClassification
    purpose: str  # Why the access was needed
    granted: bool
    denial_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataRetentionPolicy:
    """Data retention policy"""
    policy_id: str
    org_id: str
    resource_type: str
    retention_days: int  # How long to keep data
    archive_days: int  # Move to archive after N days
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    description: str = ""


@dataclass
class ComplianceCheckpoint:
    """Compliance status checkpoint"""
    checkpoint_id: str
    org_id: str
    standard: ComplianceStandard
    check_date: datetime
    status: str  # "compliant", "non_compliant", "remediation_in_progress"
    issues: List[str] = field(default_factory=list)
    remediation_steps: List[str] = field(default_factory=list)
    evidence: Dict[str, str] = field(default_factory=dict)


class AuditLogger:
    """Comprehensive audit logging"""

    def __init__(self, org_id: str):
        self.org_id = org_id
        self.logs: List[AuditLog] = []
        self.access_logs: List[AccessLog] = []

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        description: str,
        ip_address: str,
        user_agent: str,
        status: str = "success",
        error_message: Optional[str] = None,
        dept_id: Optional[str] = None,
        data_classification: DataClassification = DataClassification.INTERNAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Log an audit event"""
        log_id = self._generate_log_id(
            user_id,
            event_type,
            resource_id,
            datetime.utcnow()
        )

        log = AuditLog(
            log_id=log_id,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            user_id=user_id,
            org_id=self.org_id,
            dept_id=dept_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message,
            data_classification=data_classification,
            metadata=metadata or {}
        )

        self.logs.append(log)
        return log

    def log_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        access_type: str,
        data_sensitivity: DataClassification,
        purpose: str,
        granted: bool = True,
        denial_reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AccessLog:
        """Log data access"""
        access_id = self._generate_access_id(
            user_id,
            resource_id,
            datetime.utcnow()
        )

        access = AccessLog(
            access_id=access_id,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            org_id=self.org_id,
            resource_type=resource_type,
            resource_id=resource_id,
            access_type=access_type,
            data_sensitivity=data_sensitivity,
            purpose=purpose,
            granted=granted,
            denial_reason=denial_reason,
            metadata=metadata or {}
        )

        self.access_logs.append(access)
        return access

    def get_user_events(self, user_id: str, days: int = 30) -> List[AuditLog]:
        """Get all events for a user"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [
            log for log in self.logs
            if log.user_id == user_id and log.timestamp >= cutoff
        ]

    def get_failed_events(self, days: int = 7) -> List[AuditLog]:
        """Get all failed events"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [
            log for log in self.logs
            if log.status == "failure" and log.timestamp >= cutoff
        ]

    def get_sensitive_data_access(self, days: int = 30) -> List[AccessLog]:
        """Get access to sensitive data"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [
            access for access in self.access_logs
            if access.data_sensitivity in [
                DataClassification.CONFIDENTIAL,
                DataClassification.RESTRICTED
            ] and access.timestamp >= cutoff
        ]

    def get_unauthorized_attempts(self, days: int = 7) -> List[AuditLog]:
        """Get unauthorized access attempts"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [
            log for log in self.logs
            if log.event_type == AuditEventType.UNAUTHORIZED_ACCESS and
               log.timestamp >= cutoff
        ]

    def get_suspicious_activity(self, days: int = 7) -> List[AuditLog]:
        """Get suspicious activity"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [
            log for log in self.logs
            if log.event_type == AuditEventType.SUSPICIOUS_ACTIVITY and
               log.timestamp >= cutoff
        ]

    def _generate_log_id(
        self,
        user_id: str,
        event_type: AuditEventType,
        resource_id: str,
        timestamp: datetime
    ) -> str:
        """Generate unique log ID"""
        data = f"{user_id}:{event_type.value}:{resource_id}:{timestamp.timestamp()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _generate_access_id(
        self,
        user_id: str,
        resource_id: str,
        timestamp: datetime
    ) -> str:
        """Generate unique access ID"""
        data = f"{user_id}:{resource_id}:{timestamp.timestamp()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


class RetentionPolicyManager:
    """Manage data retention policies"""

    def __init__(self):
        self.policies: Dict[str, DataRetentionPolicy] = {}

    def create_policy(
        self,
        org_id: str,
        resource_type: str,
        retention_days: int,
        archive_days: int,
        description: str = ""
    ) -> DataRetentionPolicy:
        """Create retention policy"""
        policy_id = f"policy_{org_id}_{resource_type}_{datetime.utcnow().timestamp()}"

        policy = DataRetentionPolicy(
            policy_id=policy_id,
            org_id=org_id,
            resource_type=resource_type,
            retention_days=retention_days,
            archive_days=archive_days,
            description=description
        )

        self.policies[policy_id] = policy
        return policy

    def get_policies_by_org(self, org_id: str) -> List[DataRetentionPolicy]:
        """Get all policies for organization"""
        return [
            policy for policy in self.policies.values()
            if policy.org_id == org_id and policy.is_active
        ]

    def should_retain_data(
        self,
        org_id: str,
        resource_type: str,
        created_at: datetime
    ) -> bool:
        """Check if data should be retained"""
        policies = self.get_policies_by_org(org_id)
        matching = [p for p in policies if p.resource_type == resource_type]

        if not matching:
            return True  # No policy = retain

        policy = matching[0]
        age_days = (datetime.utcnow() - created_at).days

        return age_days <= policy.retention_days

    def should_archive_data(
        self,
        org_id: str,
        resource_type: str,
        created_at: datetime
    ) -> bool:
        """Check if data should be archived"""
        policies = self.get_policies_by_org(org_id)
        matching = [p for p in policies if p.resource_type == resource_type]

        if not matching:
            return False  # No policy = don't archive

        policy = matching[0]
        age_days = (datetime.utcnow() - created_at).days

        return age_days > policy.archive_days


class ComplianceManager:
    """Manage compliance checks and reporting"""

    def __init__(self):
        self.checkpoints: Dict[str, ComplianceCheckpoint] = {}

    def create_checkpoint(
        self,
        org_id: str,
        standard: ComplianceStandard
    ) -> ComplianceCheckpoint:
        """Create compliance checkpoint"""
        checkpoint_id = f"cp_{org_id}_{standard.value}_{datetime.utcnow().timestamp()}"

        checkpoint = ComplianceCheckpoint(
            checkpoint_id=checkpoint_id,
            org_id=org_id,
            standard=standard,
            check_date=datetime.utcnow(),
            status="compliant"
        )

        self.checkpoints[checkpoint_id] = checkpoint
        return checkpoint

    def check_soc_2_compliance(
        self,
        audit_logger: AuditLogger,
        retention_manager: RetentionPolicyManager,
        org_id: str
    ) -> ComplianceCheckpoint:
        """Check SOC 2 compliance"""
        checkpoint = self.create_checkpoint(org_id, ComplianceStandard.SOC_2)
        issues = []

        # CC6.1: Logical Access Controls
        unauthorized_attempts = audit_logger.get_unauthorized_attempts(days=90)
        if len(unauthorized_attempts) > 10:
            issues.append("High number of unauthorized access attempts")

        # CC7.2: Change Management
        config_changes = [
            log for log in audit_logger.logs
            if log.event_type == AuditEventType.CONFIG_CHANGED
        ]
        if len(config_changes) == 0:
            issues.append("No configuration change logging detected")

        # CC9.1: Audit Logs
        audit_logs = audit_logger.logs
        if len(audit_logs) < 100:
            issues.append("Insufficient audit logging history")

        # A1.1: Information & Assets
        retention_policies = retention_manager.get_policies_by_org(org_id)
        if len(retention_policies) == 0:
            issues.append("No data retention policies configured")

        checkpoint.status = "compliant" if not issues else "non_compliant"
        checkpoint.issues = issues

        if issues:
            checkpoint.remediation_steps = [
                "Review access control logs for suspicious patterns",
                "Implement configuration change management",
                "Establish data retention policies",
                "Enable comprehensive audit logging"
            ]

        return checkpoint

    def check_gdpr_compliance(
        self,
        audit_logger: AuditLogger,
        org_id: str
    ) -> ComplianceCheckpoint:
        """Check GDPR compliance"""
        checkpoint = self.create_checkpoint(org_id, ComplianceStandard.GDPR)
        issues = []

        # Article 32: Security of processing
        sensitive_access = audit_logger.get_sensitive_data_access(days=30)
        if len(sensitive_access) > 0:
            # Check if purpose is documented
            missing_purpose = [
                a for a in sensitive_access
                if not a.purpose or a.purpose == ""
            ]
            if missing_purpose:
                issues.append(f"{len(missing_purpose)} accesses without documented purpose")

        # Article 24: Responsibility
        failed_events = audit_logger.get_failed_events(days=30)
        if len(failed_events) > 5:
            issues.append("Multiple failed access attempts detected")

        checkpoint.status = "compliant" if not issues else "non_compliant"
        checkpoint.issues = issues

        if issues:
            checkpoint.remediation_steps = [
                "Document purpose for all data processing",
                "Review and improve access controls",
                "Implement data minimization practices",
                "Establish data subject rights procedures"
            ]

        return checkpoint

    def get_latest_checkpoint(
        self,
        org_id: str,
        standard: ComplianceStandard
    ) -> Optional[ComplianceCheckpoint]:
        """Get latest checkpoint for standard"""
        matching = [
            cp for cp in self.checkpoints.values()
            if cp.org_id == org_id and cp.standard == standard
        ]

        if not matching:
            return None

        return max(matching, key=lambda x: x.check_date)

    def generate_compliance_report(
        self,
        org_id: str,
        standards: List[ComplianceStandard]
    ) -> Dict[str, Any]:
        """Generate compliance report"""
        report = {
            "org_id": org_id,
            "report_date": datetime.utcnow().isoformat(),
            "standards": {}
        }

        for standard in standards:
            checkpoint = self.get_latest_checkpoint(org_id, standard)

            if checkpoint:
                report["standards"][standard.value] = {
                    "status": checkpoint.status,
                    "check_date": checkpoint.check_date.isoformat(),
                    "issues_count": len(checkpoint.issues),
                    "issues": checkpoint.issues,
                    "remediation_steps": checkpoint.remediation_steps
                }
            else:
                report["standards"][standard.value] = {
                    "status": "not_checked",
                    "message": "No compliance check performed"
                }

        return report
