# Matriz rota × permissão × role — ClinicAI

Esta matriz foi extraída das dependências registradas no FastAPI e da matriz padrão de permissões. 
O backend é a fonte autoritativa; as colunas de roles representam o **bootstrap padrão**. 
Permissões granulares de `doctor` e `clinic_staff` podem ser administradas, enquanto `admin_master` permanece fixo. 
A revisão médica é não delegável: exige simultaneamente role `doctor` e `exams:review`.

- Rotas HTTP catalogadas: **65** (61 protegidas e 4 públicas).
- Combinações protegidas verificadas automaticamente: **183** (61 rotas × 3 roles).
- Catálogo oficial: **27 permissões**.
- Matriz padrão: `doctor` com **18** permissões; `clinic_staff` com **8**.

## API/backend

| Método | Rota | Política autoritativa | Permissão | ADM | MED | FNC | Observação |
| --- | --- | --- | --- | :---: | :---: | :---: | --- |
| `GET` | `/` | `Pública` | `` | 🌐 | 🌐 | 🌐 | Não exige sessão autenticada. |
| `GET` | `/health` | `Pública` | `` | 🌐 | 🌐 | 🌐 | Não exige sessão autenticada. |
| `POST` | `/auth/login` | `Pública` | `` | 🌐 | 🌐 | 🌐 | Não exige sessão autenticada. |
| `POST` | `/auth/refresh` | `Pública` | `` | 🌐 | 🌐 | 🌐 | Não exige sessão autenticada. |
| `POST` | `/auth/logout` | `get_current_user` | `` | ✅ | ✅ | ✅ | Exige sessão válida; usuário e clínica precisam estar ativos. |
| `GET` | `/auth/me` | `get_current_user` | `` | ✅ | ✅ | ✅ | Autoatendimento restrito ao próprio usuário ou à clínica vinculada. |
| `GET` | `/statuses/` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `GET` | `/statuses/{status_id}` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `PATCH` | `/statuses/{status_id}` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `GET` | `/roles/` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `GET` | `/roles/{role_id}` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `PATCH` | `/roles/{role_id}` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `GET` | `/permissions/` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `GET` | `/permissions/{permission_id}` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `PATCH` | `/permissions/{permission_id}` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `POST` | `/role-permissions/` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `GET` | `/role-permissions/` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `GET` | `/role-permissions/{role_permission_id}` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `PATCH` | `/role-permissions/{role_permission_id}` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `DELETE` | `/role-permissions/{role_permission_id}` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `PUT` | `/role-permissions/roles/{role_id}` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `GET` | `/audit-logs/` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `POST` | `/clinics/` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `GET` | `/clinics/` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `GET` | `/clinics/me` | `require_permission("clinics:read_profile")` | `clinics:read_profile` | ✅ | ✅ | ✅ | Autoatendimento restrito ao próprio usuário ou à clínica vinculada. |
| `PATCH` | `/clinics/me` | `require_permission("clinics:update_profile")` | `clinics:update_profile` | ✅ | ✅ | ✅ | Autoatendimento restrito ao próprio usuário ou à clínica vinculada. |
| `GET` | `/clinics/{clinic_id}` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `PATCH` | `/clinics/{clinic_id}` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `PATCH` | `/clinics/{clinic_id}/inactivate` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `PATCH` | `/clinics/{clinic_id}/activate` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `POST` | `/users/` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `GET` | `/users/` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `GET` | `/users/doctors` | `require_permission("patients:read")` | `patients:read` | ✅ | ✅ | ✅ | Lista auxiliar filtrada pelo escopo autorizado do solicitante. |
| `GET` | `/users/me` | `require_permission("users:read_profile")` | `users:read_profile` | ✅ | ✅ | ✅ | Autoatendimento restrito ao próprio usuário ou à clínica vinculada. |
| `PATCH` | `/users/me` | `require_permission("users:update_profile")` | `users:update_profile` | ✅ | ✅ | ✅ | Autoatendimento restrito ao próprio usuário ou à clínica vinculada. |
| `PATCH` | `/users/me/password` | `require_permission("users:update_profile")` | `users:update_profile` | ✅ | ✅ | ✅ | Autoatendimento restrito ao próprio usuário ou à clínica vinculada. |
| `GET` | `/users/{user_id}` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `PATCH` | `/users/{user_id}` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `PATCH` | `/users/{user_id}/password` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `PATCH` | `/users/{user_id}/inactivate` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `PATCH` | `/users/{user_id}/activate` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `POST` | `/patients/` | `require_permission("patients:create")` | `patients:create` | ✅ | ✅ | ✅ | Permissão de rota + escopo de clínica/médico validado no serviço. |
| `GET` | `/patients/` | `require_permission("patients:read")` | `patients:read` | ✅ | ✅ | ✅ | Permissão de rota + escopo de clínica/médico validado no serviço. |
| `GET` | `/patients/{patient_id}` | `require_permission("patients:read")` | `patients:read` | ✅ | ✅ | ✅ | Permissão de rota + escopo de clínica/médico validado no serviço. |
| `PATCH` | `/patients/{patient_id}` | `require_permission("patients:update")` | `patients:update` | ✅ | ✅ | ✅ | Permissão de rota + escopo de clínica/médico validado no serviço. |
| `PATCH` | `/patients/{patient_id}/activate` | `require_permission("patients:change_status")` | `patients:change_status` | ✅ | ✅ | ✅ | Permissão de rota + escopo de clínica/médico validado no serviço. |
| `PATCH` | `/patients/{patient_id}/inactivate` | `require_permission("patients:change_status")` | `patients:change_status` | ✅ | ✅ | ✅ | Permissão de rota + escopo de clínica/médico validado no serviço. |
| `GET` | `/exams/form-options` | `require_permission("exams:read")` | `exams:read` | ✅ | ✅ | ❌ | Permissão de rota + escopo do exame, clínica e médico validado no serviço. |
| `POST` | `/exams/` | `require_permission("exams:create")` | `exams:create` | ✅ | ✅ | ❌ | Permissão de rota + escopo do exame, clínica e médico validado no serviço. |
| `GET` | `/exams/` | `require_permission("exams:read")` | `exams:read` | ✅ | ✅ | ❌ | Permissão de rota + escopo do exame, clínica e médico validado no serviço. |
| `GET` | `/exams/{exam_id}` | `require_permission("exams:read")` | `exams:read` | ✅ | ✅ | ❌ | Permissão de rota + escopo do exame, clínica e médico validado no serviço. |
| `GET` | `/exams/{exam_id}/history` | `require_permission("exams:read")` | `exams:read` | ✅ | ✅ | ❌ | Permissão de rota + escopo do exame, clínica e médico validado no serviço. |
| `PATCH` | `/exams/{exam_id}` | `require_permission("exams:update")` | `exams:update` | ✅ | ✅ | ❌ | Permissão de rota + escopo do exame, clínica e médico validado no serviço. |
| `PATCH` | `/exams/{exam_id}/cancel` | `require_permission("exams:change_status")` | `exams:change_status` | ✅ | ✅ | ❌ | Permissão de rota + escopo do exame, clínica e médico validado no serviço. |
| `PATCH` | `/exams/{exam_id}/restore` | `require_permission("exams:change_status")` | `exams:change_status` | ✅ | ✅ | ❌ | Permissão de rota + escopo do exame, clínica e médico validado no serviço. |
| `POST` | `/exams/{exam_id}/analyze` | `require_permission("ai_analysis:create")` | `ai_analysis:create` | ✅ | ✅ | ❌ | Permissão de rota + escopo do exame, clínica e médico validado no serviço. |
| `PATCH` | `/exams/{exam_id}/review` | `require_doctor_permission("exams:review")` | `exams:review` | ❌ | ✅ | ❌ | Permissão de rota + escopo do exame, clínica e médico validado no serviço. |
| `GET` | `/exams/{exam_id}/download` | `require_permission("exams:download")` | `exams:download` | ✅ | ✅ | ❌ | Permissão de rota + escopo do exame, clínica e médico validado no serviço. |
| `POST` | `/exams/{exam_id}/replace-file` | `require_permission("exams:upload")` | `exams:upload` | ✅ | ✅ | ❌ | Permissão de rota + escopo do exame, clínica e médico validado no serviço. |
| `GET` | `/ai-analysis/metrics` | `require_admin` | `` | ✅ | ❌ | ❌ | Módulo estrutural; barreira fixa de Administrador Master. |
| `POST` | `/ai-analysis/` | `require_permission("ai_analysis:create")` | `ai_analysis:create` | ✅ | ✅ | ❌ | Permissão de rota + escopo do exame, clínica e médico validado no serviço. |
| `GET` | `/ai-analysis/` | `require_permission("ai_analysis:read")` | `ai_analysis:read` | ✅ | ✅ | ❌ | Permissão de rota + escopo do exame, clínica e médico validado no serviço. |
| `GET` | `/ai-analysis/exam/{exam_id}` | `require_permission("ai_analysis:read")` | `ai_analysis:read` | ✅ | ✅ | ❌ | Permissão de rota + escopo do exame, clínica e médico validado no serviço. |
| `GET` | `/ai-analysis/{ai_analysis_id}` | `require_permission("ai_analysis:read")` | `ai_analysis:read` | ✅ | ✅ | ❌ | Permissão de rota + escopo do exame, clínica e médico validado no serviço. |
| `PATCH` | `/ai-analysis/{ai_analysis_id}` | `require_permission("ai_analysis:update")` | `ai_analysis:update` | ✅ | ✅ | ❌ | Permissão de rota + escopo do exame, clínica e médico validado no serviço. |

## Rotas de interface/frontend

| Rota React | Regra do frontend | ADM | MED | FNC | Correspondência |
| --- | --- | :---: | :---: | :---: | --- |
| `/dashboard` | `Autenticado` | ✅ | ✅ | ✅ | APIs internas continuam sujeitas às permissões e ao escopo. |
| `/profile` | `Autenticado` | ✅ | ✅ | ✅ | Usa permissões de perfil próprio e clínica vinculada. |
| `/clinics*` | `Role admin_master` | ✅ | ❌ | ❌ | Espelha require_admin do backend. |
| `/users*` | `Role admin_master` | ✅ | ❌ | ❌ | Espelha require_admin do backend. |
| `/audit-logs` | `Role admin_master` | ✅ | ❌ | ❌ | Espelha require_admin do backend. |
| `/roles*` | `Role admin_master` | ✅ | ❌ | ❌ | Catálogo estrutural fechado. |
| `/permissions*` | `Role admin_master` | ✅ | ❌ | ❌ | Catálogo estrutural fechado. |
| `/statuses*` | `Role admin_master` | ✅ | ❌ | ❌ | Catálogo estrutural fechado. |
| `/patients` | `patients:read` | ✅ | ✅ | ✅ | Matriz padrão; dados ainda filtrados pelo escopo. |
| `/patients/create` | `patients:create` | ✅ | ✅ | ✅ | Matriz padrão. |
| `/patients/:id/edit` | `patients:update` | ✅ | ✅ | ✅ | Matriz padrão; escopo validado no backend. |
| `/patients/:id` | `patients:read` | ✅ | ✅ | ✅ | Matriz padrão; escopo validado no backend. |
| `/exams` | `exams:read` | ✅ | ✅ | ❌ | Funcionário não recebe permissões de exames na matriz padrão. |
| `/exams/create` | `exams:create` | ✅ | ✅ | ❌ | Funcionário não recebe permissões de exames na matriz padrão. |
| `/exams/:id/edit` | `exams:update` | ✅ | ✅ | ❌ | Escopo e estado validados no backend. |
| `/exams/:id` | `exams:read` | ✅ | ✅ | ❌ | Inclui RF36 por meio do cartão de histórico protegido. |

## Leitura correta da matriz

- Uma marca positiva na rota não substitui as regras de escopo do serviço. Por exemplo, o médico só acessa pacientes e exames autorizados pelas regras de vínculo.
- `admin_master` possui bypass para permissões granulares, mas não para revisão médica. Sua matriz é fixa no backend e somente leitura no frontend.
- O Funcionário da Clínica não recebe `exams:*` nem `ai_analysis:*` no bootstrap padrão; por isso o frontend não apresenta o módulo de exames para esse perfil.
- A planilha CSV ao lado deste documento facilita filtragem e anexação às evidências do TCC.
