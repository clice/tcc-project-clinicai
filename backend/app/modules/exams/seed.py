"""Exames coerentes da massa acadêmica demonstrativa."""

from datetime import (
    date,
    datetime,
    time,
    timezone,
)

from sqlalchemy.orm import Session

from app.modules.academic_demo_assets import (
    exam_asset_target,
    get_demo_exam_definitions,
    install_exam_asset,
)
from app.modules.clinics.model import Clinic
from app.modules.exams.model import Exam
from app.modules.patients.model import Patient
from app.modules.statuses.model import Status
from app.modules.users.model import User


def get_or_create_exam(
    db: Session,
    *,
    clinic_id: int,
    patient_id: int,
    doctor_id: int,
    status_id: int,
    exam_type: str,
    title: str,
    asset_entry: dict,
    exam_date: date,
    description: str,
    clinical_indication: str,
    findings: str | None = None,
    conclusion: str | None = None,
    reviewed_by_id: int | None = None,
    reviewed_at: datetime | None = None,
) -> Exam:
    """Cria um exame demo sem alterar registro existente."""

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
        expected_path = exam_asset_target(
            exam,
            asset_entry,
        ).resolve(strict=False)

        if exam.file_path == str(expected_path):
            install_exam_asset(
                exam,
                asset_entry,
                assign_fields=False,
            )

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

    install_exam_asset(
        exam,
        asset_entry,
        assign_fields=True,
    )

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
    """Cria os 90 exames definidos no manifesto v2."""

    result: dict[str, Exam] = {}

    for definition in get_demo_exam_definitions():
        clinic = clinics[
            definition["clinic_key"]
        ]
        doctor = users[
            definition["doctor_key"]
        ]
        patient = patients[
            definition["patient_key"]
        ]
        status = statuses[
            "exam_" + definition["status"]
        ]
        exam_date = date.fromisoformat(
            definition["exam_date"]
        )
        review = definition.get("review")

        reviewed_at = None
        findings = None
        conclusion = None

        if review is not None:
            reviewed_at = datetime.combine(
                exam_date,
                time(
                    hour=14,
                    minute=30,
                    tzinfo=timezone.utc,
                ),
            )
            findings = str(
                review["review_notes"]
            )
            conclusion = (
                "Revisão acadêmica concluída "
                "com concordância."
                if review["agrees_with_ai"]
                else
                "Revisão acadêmica concluída "
                "com divergência."
            )

        source_label = definition[
            "source_asset"
        ]["label"]

        result[
            definition["exam_key"]
        ] = get_or_create_exam(
            db=db,
            clinic_id=clinic.id,
            patient_id=patient.id,
            doctor_id=doctor.id,
            status_id=status.id,
            exam_type=definition[
                "exam_type"
            ],
            title=definition["title"],
            asset_entry=definition[
                "source_asset"
            ],
            exam_date=exam_date,
            description=(
                "Exame fictício da massa acadêmica "
                f"com imagem de referência {source_label}."
            ),
            clinical_indication=(
                "Demonstração técnica do estado "
                f"{definition['status']}."
            ),
            findings=findings,
            conclusion=conclusion,
            reviewed_by_id=(
                doctor.id
                if review is not None
                else None
            ),
            reviewed_at=reviewed_at,
        )

    if len(result) != 90:
        raise RuntimeError(
            "O seed acadêmico deve produzir 90 exames."
        )

    return result
