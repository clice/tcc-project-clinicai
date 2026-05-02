"""
Service do módulo de pacientes.

Aqui ficam as regras de negócio e operações com o banco.
O router deve ficar mais limpo e apenas chamar essas funções.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.modules.clinics.model import Clinic
from app.modules.patients.model import Patient
from app.modules.patients.schema import PatientCreate, PatientUpdate
from app.modules.statuses.model import Status
from app.modules.statuses.service import get_status_by_name_and_applies_to
from app.modules.users.model import User


def get_patient_by_id(db: Session, patient_id: int) -> Patient:
    """
    Busca um paciente pelo ID.
    Se não existir, retorna erro 404.
    """
    patient = (
        db.query(Patient)
        .options(
            joinedload(Patient.clinic),
            joinedload(Patient.status),
            joinedload(Patient.doctor),
        )
        .filter(Patient.id == patient_id)
        .first()
    )

    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")

    return patient


def is_admin_master(user: User) -> bool:
    """
    Verifica se o usuário autenticado é admin_master.
    """
    return bool(user.role and user.role.name == "admin_master")


def validate_user_can_access_clinic(
    *,
    current_user: User,
    clinic_id: int,
) -> None:
    """
    Garante que usuários de clínica acessem apenas dados da própria clínica.
    Admin master pode acessar qualquer clínica.
    """
    if is_admin_master(current_user):
        return

    if current_user.clinic_id is None:
        raise HTTPException(
            status_code=403,
            detail="Usuário não está vinculado a uma clínica.",
        )

    if current_user.clinic_id != clinic_id:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para acessar dados desta clínica.",
        )
        
        
def validate_user_can_access_patient(
    *,
    patient: Patient,
    current_user: User,
) -> None:
    """
    Garante que o usuário autenticado pode acessar o paciente.

    - admin_master acessa todos;
    - clinic_staff acessa pacientes da própria clínica;
    - doctor acessa apenas pacientes atribuídos a ele.
    """
    role_name = current_user.role.name if current_user.role else None

    if role_name == "admin_master":
        return

    if role_name == "clinic_staff" and patient.clinic_id == current_user.clinic_id:
        return

    if role_name == "doctor" and patient.doctor_id == current_user.id:
        return

    raise HTTPException(
        status_code=403,
        detail="Você não tem permissão para acessar este paciente.",
    )


def validate_clinic_is_active(db: Session, clinic_id: int) -> Clinic:
    """
    Valida se a clínica existe e está ativa.
    Pacientes não devem ser vinculados a clínicas inativas ou bloqueadas.
    """
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()

    if not clinic:
        raise HTTPException(status_code=404, detail="Clínica não encontrada.")

    if not clinic.status or clinic.status.name != "active":
        raise HTTPException(
            status_code=400,
            detail="Não é possível vincular paciente a clínica inativa ou bloqueada.",
        )

    return clinic


def validate_doctor_can_be_assigned(
    db: Session,
    *,
    doctor_id: int | None,
    clinic_id: int,
) -> None:
    """
    Valida se o médico informado pode ser vinculado ao paciente.

    Regras:
    - doctor_id pode ser None;
    - se informado, precisa existir;
    - precisa ter role doctor;
    - precisa estar ativo;
    - precisa pertencer à mesma clínica do paciente.
    """
    if doctor_id is None:
        return

    doctor = (
        db.query(User)
        .join(Status, User.status_id == Status.id)
        .filter(User.id == doctor_id)
        .first()
    )

    if not doctor:
        raise HTTPException(status_code=404, detail="Médico não encontrado.")

    if not doctor.role or doctor.role.name != "doctor":
        raise HTTPException(
            status_code=400,
            detail="O usuário selecionado não possui perfil de médico.",
        )

    if doctor.clinic_id != clinic_id:
        raise HTTPException(
            status_code=400,
            detail="O médico selecionado não pertence à clínica do paciente.",
        )

    if not doctor.status or doctor.status.name != "active":
        raise HTTPException(
            status_code=400,
            detail="O médico selecionado não está ativo.",
        )


def check_patient_duplicate(
    db: Session,
    *,
    clinic_id: int,
    cpf: str,
    ignore_patient_id: int | None = None,
) -> None:
    """
    Verifica se já existe paciente com o mesmo CPF na mesma clínica.
    """
    query = db.query(Patient).filter(
        Patient.clinic_id == clinic_id,
        Patient.cpf == cpf,
    )

    if ignore_patient_id is not None:
        query = query.filter(Patient.id != ignore_patient_id)

    duplicated = query.first()

    if duplicated:
        raise HTTPException(
            status_code=400,
            detail="Já existe um paciente com esse CPF nesta clínica.",
        )


def build_patient_response(patient: Patient) -> dict:
    """
    Monta a resposta do paciente com dados relacionados de clínica e status.
    """
    return {
        "id": patient.id,
        "clinic_id": patient.clinic_id,
        "clinic_name": patient.clinic.name if patient.clinic else None,
        "doctor_id": patient.doctor_id,
        "doctor_name": patient.doctor.name if patient.doctor else None,
        "status_id": patient.status_id,
        "status_name": patient.status.name if patient.status else None,
        "status_display_name": patient.status.display_name if patient.status else None,
        "name": patient.name,
        "cpf": patient.cpf,
        "birth_date": patient.birth_date,
        "sex": patient.sex,
        "email": patient.email,
        "phone": patient.phone,
        "zip_code": patient.zip_code,
        "address": patient.address,
        "number": patient.number,
        "complement": patient.complement,
        "neighborhood": patient.neighborhood,
        "city": patient.city,
        "state": patient.state,
        "created_at": patient.created_at,
        "updated_at": patient.updated_at,
    }


def list_patients(
    db: Session,
    *,
    include_inactive: bool = False,
    current_user: User,
) -> list[dict]:
    """
    Lista os pacientes cadastrados.
    Admin master visualiza todos.
    Usuários vinculados a uma clínica visualizam apenas pacientes da própria clínica.
    """
    query = (
        db.query(Patient)
        .options(
            joinedload(Patient.clinic),
            joinedload(Patient.status),
            joinedload(Patient.doctor),
        )
        .join(Status, Patient.status_id == Status.id)
    )

    role_name = current_user.role.name

    if not include_inactive:
        query = query.filter(
            Status.name == "active",
            Status.applies_to == "patient",
        )

    if role_name == "admin_master":
        pass

    elif role_name == "clinic_staff":
        query = query.filter(Patient.clinic_id == current_user.clinic_id)

    elif role_name == "doctor":
        query = query.filter(Patient.doctor_id == current_user.id)

    else:
        raise HTTPException(
            status_code=403,
            detail="Usuário sem permissão para listar pacientes.",
        )

    patients = query.order_by(Patient.name.asc()).all()

    return [build_patient_response(patient) for patient in patients]


def create_patient(
    db: Session,
    payload: PatientCreate,
    current_user: User,
) -> dict:
    """
    Cria um novo paciente.
    Todo paciente novo é criado inicialmente com status active.
    """
    validate_user_can_access_clinic(
        current_user=current_user,
        clinic_id=payload.clinic_id,
    )

    validate_clinic_is_active(db=db, clinic_id=payload.clinic_id)

    active_status = get_status_by_name_and_applies_to(
        db=db,
        name="active",
        applies_to="patient",
    )

    check_patient_duplicate(
        db=db,
        clinic_id=payload.clinic_id,
        cpf=payload.cpf,
    )

    doctor_id = payload.doctor_id

    if current_user.role and current_user.role.name == "doctor":
        doctor_id = current_user.id

    validate_doctor_can_be_assigned(
        db=db,
        doctor_id=doctor_id,
        clinic_id=payload.clinic_id,
    )

    patient = Patient(
        clinic_id=payload.clinic_id,
        doctor_id=doctor_id,
        status_id=active_status.id,
        name=payload.name,
        cpf=payload.cpf,
        birth_date=payload.birth_date,
        sex=payload.sex,
        email=str(payload.email) if payload.email else None,
        phone=payload.phone,
        zip_code=payload.zip_code,
        address=payload.address,
        number=payload.number,
        complement=payload.complement,
        neighborhood=payload.neighborhood,
        city=payload.city,
        state=payload.state,
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)

    patient = get_patient_by_id(db=db, patient_id=patient.id)

    return build_patient_response(patient)


def get_patient(
    db: Session,
    patient_id: int,
    current_user: User,
) -> dict:
    """
    Busca um paciente específico pelo ID.
    """    
    patient = get_patient_by_id(db=db, patient_id=patient_id)
    
    validate_user_can_access_patient(
        patient=patient,
        current_user=current_user,
    )

    return build_patient_response(patient)


def update_patient(
    db: Session,
    patient_id: int,
    payload: PatientUpdate,
    current_user: User,
) -> dict:
    """
    Atualiza parcialmente um paciente.
    """
    patient = get_patient_by_id(db=db, patient_id=patient_id)

    validate_user_can_access_patient(
        patient=patient,
        current_user=current_user,
    )

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return build_patient_response(patient)

    new_clinic_id = update_data.get("clinic_id", patient.clinic_id)
    new_doctor_id = update_data.get("doctor_id", patient.doctor_id)

    validate_doctor_can_be_assigned(
        db=db,
        doctor_id=new_doctor_id,
        clinic_id=new_clinic_id,
    )
    
    new_cpf = update_data.get("cpf", patient.cpf)

    validate_user_can_access_clinic(
        current_user=current_user,
        clinic_id=new_clinic_id,
    )

    validate_clinic_is_active(db=db, clinic_id=new_clinic_id)

    check_patient_duplicate(
        db=db,
        clinic_id=new_clinic_id,
        cpf=new_cpf,
        ignore_patient_id=patient_id,
    )

    if "email" in update_data and update_data["email"] is not None:
        update_data["email"] = str(update_data["email"])

    for field, value in update_data.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)

    return build_patient_response(patient)


def activate_patient(
    db: Session,
    patient_id: int,
    current_user: User,
) -> dict:
    """
    Ativa um paciente, alterando seu status para active.
    """
    patient = get_patient_by_id(db=db, patient_id=patient_id)

    validate_user_can_access_patient(
        patient=patient,
        current_user=current_user,
    )

    active_status = get_status_by_name_and_applies_to(
        db=db,
        name="active",
        applies_to="patient",
    )

    patient.status_id = active_status.id

    db.commit()
    db.refresh(patient)

    return build_patient_response(patient)


def inactivate_patient(
    db: Session,
    patient_id: int,
    current_user: User,
) -> dict:
    """
    Inativa um paciente, alterando seu status para inactive.
    """
    patient = get_patient_by_id(db=db, patient_id=patient_id)

    validate_user_can_access_patient(
        patient=patient,
        current_user=current_user,
    )

    inactive_status = get_status_by_name_and_applies_to(
        db=db,
        name="inactive",
        applies_to="patient",
    )

    patient.status_id = inactive_status.id

    db.commit()
    db.refresh(patient)

    return build_patient_response(patient)