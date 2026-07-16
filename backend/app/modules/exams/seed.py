"""Massa acadêmica coerente do módulo de exames."""

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.common.constants import StatusName, StatusScope
from app.modules.academic_demo_assets import exam_asset_target, install_exam_asset
from app.modules.clinics.model import Clinic
from app.modules.exams.model import Exam
from app.modules.patients.model import Patient
from app.modules.statuses.model import Status
from app.modules.users.model import User


def get_exam_status(
    db: Session,
    name: StatusName,
) -> Status | None:
    """Busca status de exame pelo nome oficial."""

    return (
        db.query(Status)
        .filter(
            Status.name == name.value,
            Status.applies_to == StatusScope.EXAM.value,
        )
        .first()
    )


def get_or_create_exam(
    db: Session,
    *,
    clinic_id: int,
    patient_id: int,
    doctor_id: int,
    status_id: int,
    exam_type: str,
    title: str,
    asset_key: str,
    exam_date: date | None = None,
    description: str | None = None,
    clinical_indication: str | None = None,
    findings: str | None = None,
    conclusion: str | None = None,
    reviewed_by_id: int | None = None,
    reviewed_at: datetime | None = None,
) -> Exam:
    """Cria um exame demo sem alterar registros já existentes."""

    exam = (
        db.query(Exam)
        .filter(
            Exam.patient_id == patient_id,
            Exam.exam_type == exam_type,
            Exam.title == title,
        )
        .first()
    )

    if exam:
        expected_path = exam_asset_target(exam, asset_key).resolve(strict=False)
        if exam.file_path == str(expected_path):
            install_exam_asset(exam, asset_key, assign_fields=False)
        return exam

    exam = Exam(
        clinic_id=clinic_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        status_id=status_id,
        exam_type=exam_type,
        exam_date=exam_date,
        title=title,
        description=description,
        clinical_indication=clinical_indication,
        findings=findings,
        conclusion=conclusion,
        reviewed_by_id=reviewed_by_id,
        reviewed_at=reviewed_at,
        analysis_in_progress=False,
        analysis_started_at=None,
    )

    db.add(exam)
    db.flush()
    install_exam_asset(exam, asset_key, assign_fields=True)
    db.flush()
    db.refresh(exam)

    return exam


def seed_exams(
    db: Session,
    clinics: dict[str, Clinic],
    patients: dict[str, Patient],
    users: dict[str, User],
    statuses: dict[str, Status],
) -> dict[str, Exam]:
    """Cria sete estados demonstrativos com arquivos físicos válidos."""

    primary_clinic = clinics.get("clinic_primary")
    doctor_primary = users.get("doctor_primary")

    required_patients = {
        "pending": patients.get("patient_example_1"),
        "awaiting_normal": patients.get("patient_example_2"),
        "awaiting_abnormal": patients.get("patient_elderly"),
        "completed": patients.get("patient_young"),
        "divergence": patients.get("patient_fictitious_cpf"),
        "failed": patients.get("patient_minimal"),
        "canceled": patients.get("patient_complete"),
    }

    required_statuses = {
        "pending": statuses.get("exam_pending")
        or get_exam_status(db, StatusName.PENDING),
        "awaiting_review": statuses.get("exam_awaiting_review")
        or get_exam_status(db, StatusName.AWAITING_REVIEW),
        "completed": statuses.get("exam_completed")
        or get_exam_status(db, StatusName.COMPLETED),
        "divergence": statuses.get("exam_completed_with_divergence")
        or get_exam_status(db, StatusName.COMPLETED_WITH_DIVERGENCE),
        "failed": statuses.get("exam_failed")
        or get_exam_status(db, StatusName.FAILED),
        "canceled": statuses.get("exam_canceled")
        or get_exam_status(db, StatusName.CANCELED),
    }

    if (
        not primary_clinic
        or not doctor_primary
        or not all(required_patients.values())
        or not all(required_statuses.values())
    ):
        return {}

    reviewed_confirmed_at = datetime(
        2026,
        7,
        10,
        14,
        30,
        tzinfo=timezone.utc,
    )
    reviewed_divergence_at = datetime(
        2026,
        7,
        11,
        15,
        45,
        tzinfo=timezone.utc,
    )

    definitions = {
        "exam_pending": {
            "patient": required_patients["pending"],
            "status": required_statuses["pending"],
            "asset_key": "normal_image",
            "exam_date": date(2026, 7, 6),
            "title": "Demo — colonoscopia pronta para análise",
            "description": "Registro acadêmico aguardando execução do modelo.",
            "clinical_indication": "Demonstração técnica do estado pending.",
        },
        "exam_awaiting_review_normal": {
            "patient": required_patients["awaiting_normal"],
            "status": required_statuses["awaiting_review"],
            "asset_key": "normal_image",
            "exam_date": date(2026, 7, 7),
            "title": "Demo — predição normal aguardando revisão",
            "description": "Predição real do modelo sobre ativo acadêmico Kvasir.",
            "clinical_indication": "Demonstração técnica do estado awaiting_review.",
        },
        "exam_awaiting_review_abnormal": {
            "patient": required_patients["awaiting_abnormal"],
            "status": required_statuses["awaiting_review"],
            "asset_key": "abnormal_image",
            "exam_date": date(2026, 7, 8),
            "title": "Demo — predição abnormal aguardando revisão",
            "description": "Predição real do modelo sobre ativo acadêmico Kvasir.",
            "clinical_indication": "Demonstração técnica do estado awaiting_review.",
        },
        "exam_completed_confirmed": {
            "patient": required_patients["completed"],
            "status": required_statuses["completed"],
            "asset_key": "normal_image",
            "exam_date": date(2026, 7, 9),
            "title": "Demo — revisão confirmatória concluída",
            "description": "Exemplo acadêmico de confirmação médica.",
            "clinical_indication": "Demonstração técnica do estado completed.",
            "findings": (
                "A revisão acadêmica confirmou a classificação normal "
                "apresentada pelo modelo."
            ),
            "conclusion": "Exemplo acadêmico encerrado sem divergência.",
            "reviewed_by_id": doctor_primary.id,
            "reviewed_at": reviewed_confirmed_at,
        },
        "exam_completed_with_divergence": {
            "patient": required_patients["divergence"],
            "status": required_statuses["divergence"],
            "asset_key": "abnormal_image",
            "exam_date": date(2026, 7, 10),
            "title": "Demo — revisão concluída com divergência",
            "description": "Exemplo acadêmico de divergência médica.",
            "clinical_indication": (
                "Demonstração técnica do estado completed_with_divergence."
            ),
            "findings": (
                "A revisão acadêmica registrou divergência em relação "
                "à classificação abnormal."
            ),
            "conclusion": "Exemplo acadêmico encerrado com divergência médica.",
            "reviewed_by_id": doctor_primary.id,
            "reviewed_at": reviewed_divergence_at,
        },
        "exam_failed": {
            "patient": required_patients["failed"],
            "status": required_statuses["failed"],
            "asset_key": "abnormal_image",
            "exam_date": date(2026, 7, 11),
            "title": "Demo — falha de processamento restaurável",
            "description": (
                "Registro acadêmico com arquivo preservado para restauração."
            ),
            "clinical_indication": "Demonstração técnica do estado failed.",
        },
        "exam_canceled": {
            "patient": required_patients["canceled"],
            "status": required_statuses["canceled"],
            "asset_key": "normal_image",
            "exam_date": date(2026, 7, 12),
            "title": "Demo — exame cancelado restaurável",
            "description": "Registro acadêmico cancelado com arquivo preservado.",
            "clinical_indication": "Demonstração técnica do estado canceled.",
        },
    }

    result: dict[str, Exam] = {}
    for key, definition in definitions.items():
        result[key] = get_or_create_exam(
            db=db,
            clinic_id=primary_clinic.id,
            patient_id=definition["patient"].id,
            doctor_id=doctor_primary.id,
            status_id=definition["status"].id,
            exam_type="colonoscopy",
            asset_key=definition["asset_key"],
            exam_date=definition["exam_date"],
            title=definition["title"],
            description=definition["description"],
            clinical_indication=definition["clinical_indication"],
            findings=definition.get("findings"),
            conclusion=definition.get("conclusion"),
            reviewed_by_id=definition.get("reviewed_by_id"),
            reviewed_at=definition.get("reviewed_at"),
        )

    return result
