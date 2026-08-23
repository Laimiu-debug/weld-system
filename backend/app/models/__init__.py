"""
Database models for the welding system backend.
"""
from app.models.user import User
from app.models.verification_code import VerificationCode
from app.models.admin import Admin
from app.models.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionTransaction,
)
from app.models.system_announcement import SystemAnnouncement
from app.models.system_log import SystemLog
from app.models.company import Company, Factory, CompanyEmployee, CompanyInvitation
from app.models.wps_template import WPSTemplate
from app.models.custom_module import CustomModule
from app.models.shared_library import (
    SharedModule,
    SharedTemplate,
    UserRating,
    SharedDownload,
    SharedComment,
)
from app.models.welder import (
    Welder,
    WelderCertification,
    WelderCertifiedProject,
    WelderTraining,
    WelderWorkRecord,
    WelderAssessment,
    WelderWorkHistory,
)
from app.models.pqr import PQR, PQRTestSpecimen
from app.models.ppqr import PPQR, PPQRComparison
from app.models.user_notification import UserNotificationReadStatus
from app.models.approval import (
    ApprovalWorkflowDefinition,
    ApprovalInstance,
    ApprovalHistory,
    ApprovalNotification,
    ApprovalStatus,
    ApprovalAction,
    DocumentType,
)
from app.models.equipment import Equipment, EquipmentMaintenance, EquipmentUsage
from app.models.production import ProductionTask, ProductionRecord, ProductionPlan
from app.models.quality import QualityInspection, QualityStandard
from app.models.business_extensions import EmployeePerformance, ReportTemplate
from app.models.feedback import UserFeedback
from app.models.smart_import import (
    AIProviderConfig,
    EnterpriseAIPolicy,
    AIPlanEntitlement,
    AIUsageLedger,
    DocumentArtifact,
    DocumentPage,
    EntityPublishRecord,
    ExtractedEntity,
    ExtractedField,
    ExtractionJob,
    FieldEvidence,
    ImportBatch,
    ImportReviewRecord,
    SourceDocument,
)
from app.models.qualification import (
    QualificationRulePack,
    PQRQualificationResult,
    WPSPQRSupportLink,
)
from app.models.engineering import (
    EngineeringProject,
    Product,
    ProductRevision,
    Part,
    WeldJoint,
    WeldRequirement,
    DrawingParseRun,
    EngineeringReviewRecord,
    EngineeringDependencyState,
)
from app.models.matching import (
    WPSMatchRun,
    WPSMatchCandidate,
    WPSMatchCriterion,
    WPSCapabilityGap,
    WPSMatchFreeze,
)

__all__ = [
    "User",
    "VerificationCode",
    "Admin",
    "Subscription",
    "SubscriptionPlan",
    "SubscriptionTransaction",
    "SystemAnnouncement",
    "SystemLog",
    "Company",
    "Factory",
    "CompanyEmployee",
    "CompanyInvitation",
    "WPSTemplate",
    "CustomModule",
    "SharedModule",
    "SharedTemplate",
    "UserRating",
    "SharedDownload",
    "SharedComment",
    "Welder",
    "WelderCertification",
    "WelderCertifiedProject",
    "WelderTraining",
    "WelderWorkRecord",
    "WelderAssessment",
    "WelderWorkHistory",
    "PQR",
    "PQRTestSpecimen",
    "PPQR",
    "PPQRComparison",
    "UserNotificationReadStatus",
    "ApprovalWorkflowDefinition",
    "ApprovalInstance",
    "ApprovalHistory",
    "ApprovalNotification",
    "ApprovalStatus",
    "ApprovalAction",
    "DocumentType",
    "Equipment",
    "EquipmentMaintenance",
    "EquipmentUsage",
    "ProductionTask",
    "ProductionRecord",
    "ProductionPlan",
    "QualityInspection",
    "QualityStandard",
    "EmployeePerformance",
    "ReportTemplate",
    "UserFeedback",
    "ImportBatch",
    "SourceDocument",
    "DocumentArtifact",
    "DocumentPage",
    "ExtractionJob",
    "ExtractedEntity",
    "ExtractedField",
    "FieldEvidence",
    "ImportReviewRecord",
    "EntityPublishRecord",
    "AIPlanEntitlement",
    "AIUsageLedger",
    "AIProviderConfig",
    "EnterpriseAIPolicy",
    "QualificationRulePack",
    "PQRQualificationResult",
    "WPSPQRSupportLink",
    "EngineeringProject",
    "Product",
    "ProductRevision",
    "Part",
    "WeldJoint",
    "WeldRequirement",
    "DrawingParseRun",
    "EngineeringReviewRecord",
    "EngineeringDependencyState",
    "WPSMatchRun",
    "WPSMatchCandidate",
    "WPSMatchCriterion",
    "WPSCapabilityGap",
    "WPSMatchFreeze",
]
