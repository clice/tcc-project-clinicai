"""Catálogo oficial e fechado de permissões do ClinicAI."""

from dataclasses import dataclass

from app.common.constants import PermissionAction, SystemModule


@dataclass(frozen=True)
class PermissionDefinition:
    """Definição versionada de uma permissão reconhecida pelo sistema."""

    module: SystemModule
    action: PermissionAction
    display_name: str
    description: str

    @property
    def name(self) -> str:
        return f"{self.module.value}:{self.action.value}"


OFFICIAL_PERMISSION_DEFINITIONS = (
    PermissionDefinition(SystemModule.USERS, PermissionAction.CREATE, "Criar Usuários", "Permite cadastrar novos usuários no sistema."),
    PermissionDefinition(SystemModule.USERS, PermissionAction.READ, "Visualizar Usuários", "Permite visualizar usuários cadastrados."),
    PermissionDefinition(SystemModule.USERS, PermissionAction.UPDATE, "Atualizar Usuários", "Permite editar dados de usuários."),
    PermissionDefinition(SystemModule.USERS, PermissionAction.CHANGE_STATUS, "Alterar Status dos Usuários", "Permite ativar, inativar ou bloquear usuários."),
    PermissionDefinition(SystemModule.USERS, PermissionAction.READ_PROFILE, "Visualizar Próprio Perfil", "Permite visualizar os dados do próprio usuário autenticado."),
    PermissionDefinition(SystemModule.USERS, PermissionAction.UPDATE_PROFILE, "Atualizar Próprio Perfil", "Permite editar dados do próprio usuário autenticado."),
    PermissionDefinition(SystemModule.CLINICS, PermissionAction.CREATE, "Criar Clínicas", "Permite cadastrar novas clínicas."),
    PermissionDefinition(SystemModule.CLINICS, PermissionAction.READ, "Visualizar Clínicas", "Permite visualizar clínicas cadastradas."),
    PermissionDefinition(SystemModule.CLINICS, PermissionAction.UPDATE, "Atualizar Clínicas", "Permite editar dados de clínicas."),
    PermissionDefinition(SystemModule.CLINICS, PermissionAction.CHANGE_STATUS, "Alterar Status das Clínicas", "Permite ativar, inativar ou bloquear clínicas."),
    PermissionDefinition(SystemModule.CLINICS, PermissionAction.READ_PROFILE, "Visualizar Própria Clínica", "Permite visualizar os dados da clínica vinculada ao usuário autenticado."),
    PermissionDefinition(SystemModule.CLINICS, PermissionAction.UPDATE_PROFILE, "Atualizar Própria Clínica", "Permite editar os dados da clínica vinculada ao usuário autenticado."),
    PermissionDefinition(SystemModule.PATIENTS, PermissionAction.CREATE, "Criar Pacientes", "Permite cadastrar novos pacientes."),
    PermissionDefinition(SystemModule.PATIENTS, PermissionAction.READ, "Visualizar Pacientes", "Permite visualizar pacientes cadastrados."),
    PermissionDefinition(SystemModule.PATIENTS, PermissionAction.UPDATE, "Atualizar Pacientes", "Permite editar dados de pacientes."),
    PermissionDefinition(SystemModule.PATIENTS, PermissionAction.CHANGE_STATUS, "Alterar Status dos Pacientes", "Permite ativar ou inativar pacientes."),
    PermissionDefinition(SystemModule.EXAMS, PermissionAction.CREATE, "Criar Exames", "Permite cadastrar exames."),
    PermissionDefinition(SystemModule.EXAMS, PermissionAction.LIST, "Listar Exames", "Permite acompanhar a listagem e os status dos exames sem acessar detalhes clínicos."),
    PermissionDefinition(SystemModule.EXAMS, PermissionAction.READ, "Visualizar Exames", "Permite visualizar os detalhes clínicos dos exames cadastrados."),
    PermissionDefinition(SystemModule.EXAMS, PermissionAction.UPDATE, "Atualizar Exames", "Permite editar dados de exames."),
    PermissionDefinition(SystemModule.EXAMS, PermissionAction.CHANGE_STATUS, "Alterar Status dos Exames", "Permite cancelar, concluir ou alterar status de exames."),
    PermissionDefinition(SystemModule.EXAMS, PermissionAction.REVIEW, "Revisar Exames", "Permite realizar a revisão médica do resultado da análise de IA."),
    PermissionDefinition(SystemModule.EXAMS, PermissionAction.UPLOAD, "Upload de Exames", "Permite fazer o upload dos exames."),
    PermissionDefinition(SystemModule.EXAMS, PermissionAction.DOWNLOAD, "Baixar Exames", "Permite baixar os exames."),
    PermissionDefinition(SystemModule.AI_ANALYSIS, PermissionAction.CREATE, "Criar Análise por IA", "Permite solicitar análise automatizada de exames por IA."),
    PermissionDefinition(SystemModule.AI_ANALYSIS, PermissionAction.READ, "Visualizar Análise por IA", "Permite visualizar resultados de análises por IA."),
    PermissionDefinition(SystemModule.AI_ANALYSIS, PermissionAction.UPDATE, "Atualizar Análise por IA", "Permite atualizar ou revisar análise por IA."),
    PermissionDefinition(SystemModule.AUDIT_LOGS, PermissionAction.READ, "Visualizar Logs de Auditoria", "Permite visualizar registros de auditoria do sistema."),
)


OFFICIAL_PERMISSION_NAMES = frozenset(
    definition.name for definition in OFFICIAL_PERMISSION_DEFINITIONS
)
