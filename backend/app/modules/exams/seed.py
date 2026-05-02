"""
Seed do módulo de exames.

Cria exames iniciais para testes e desenvolvimento.
"""

from datetime import date

from sqlalchemy.orm import Session

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
    doctor_id: int | None,
    status_id: int,
    exam_type: str,
    title: str,
    exam_date: date | None = None,
    description: str | None = None,
    clinical_indication: str | None = None,
    findings: str | None = None,
    conclusion: str | None = None,
    ai_analysis_status: str | None = None,
    ai_summary: str | None = None,
    file_path: str | None = None,
    file_name: str | None = None,
    file_mime_type: str | None = None,
) -> Exam:
    """
    Busca um exame pelo título, paciente e tipo ou cria um novo.
    Evita duplicidade quando o seed for executado mais de uma vez.
    """

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
        ai_analysis_status=ai_analysis_status,
        ai_summary=ai_summary,
        file_path=file_path,
        file_name=file_name,
        file_mime_type=file_mime_type,
    )

    db.add(exam)
    db.commit()
    db.refresh(exam)

    return exam


def seed_exams(
    db: Session,
    clinics: dict[str, Clinic],
    patients: dict[str, Patient],
    users: dict[str, User],
    statuses: dict[str, Status],
) -> dict[str, Exam]:
    """
    Cria exames iniciais do sistema.
    """

    primary_clinic = clinics["clinic_primary"]
    specialized_clinic = clinics["clinic_specialized"]

    return {
        "exam_endoscopy_pending": get_or_create_exam(
            db=db,
            clinic_id=primary_clinic.id,
            patient_id=patients["patient_primary"].id,
            doctor_id=users.get("doctor_primary").id if users.get("doctor_primary") else None,
            status_id=statuses["exam_pending"].id,
            exam_type="endoscopy",
            exam_date=date(2026, 5, 1),
            title="Endoscopia digestiva alta",
            description="Exame endoscópico inicial para avaliação clínica.",
            clinical_indication="Dor epigástrica persistente e refluxo.",
            findings=None,
            conclusion=None,
            ai_analysis_status="pending",
            ai_summary=None,
            file_path="uploads/exams/endoscopy_pending.jpg",
            file_name="endoscopy_pending.jpg",
            file_mime_type="image/jpeg",
        ),
        "exam_colonoscopy_completed": get_or_create_exam(
            db=db,
            clinic_id=primary_clinic.id,
            patient_id=patients["patient_secondary"].id,
            doctor_id=users.get("doctor_primary").id if users.get("doctor_primary") else None,
            status_id=statuses["exam_completed"].id,
            exam_type="colonoscopy",
            exam_date=date(2026, 5, 2),
            title="Colonoscopia completa",
            description="Colonoscopia para rastreamento e investigação diagnóstica.",
            clinical_indication="Rastreamento de lesões colorretais.",
            findings="Mucosa sem alterações relevantes.",
            conclusion="Exame sem achados significativos.",
            ai_analysis_status="completed",
            ai_summary="IA não identificou alterações suspeitas.",
            file_path="uploads/exams/colonoscopy_completed.jpg",
            file_name="colonoscopy_completed.jpg",
            file_mime_type="image/jpeg",
        ),
        "exam_endoscopy_in_analysis": get_or_create_exam(
            db=db,
            clinic_id=specialized_clinic.id,
            patient_id=patients["patient_third"].id,
            doctor_id=users.get("doctor_secondary").id if users.get("doctor_secondary") else None,
            status_id=statuses["exam_in_analysis"].id,
            exam_type="endoscopy",
            exam_date=date(2026, 5, 3),
            title="Endoscopia com análise por IA",
            description="Exame enviado para análise automatizada.",
            clinical_indication="Investigação de gastrite e lesões gástricas.",
            findings=None,
            conclusion=None,
            ai_analysis_status="processing",
            ai_summary=None,
            file_path="uploads/exams/endoscopy_ai_processing.jpg",
            file_name="endoscopy_ai_processing.jpg",
            file_mime_type="image/jpeg",
        ),
    }