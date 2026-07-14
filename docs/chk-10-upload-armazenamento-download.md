# CHK-10 — Upload, armazenamento e download

**Data da revisão:** 15 de julho de 2026
**Branch de referência:** `feature/fix`
**Perfil do sistema:** protótipo acadêmico e demonstrativo

## 1. Resultado executivo

A CHK-10 remove a confiança em metadados controlados pelo cliente durante o
upload de imagens de exames. O backend passa a derivar MIME, extensão canônica,
dimensões e hash a partir dos bytes reais, além de validar a estrutura do
arquivo antes de persistir qualquer registro ou chamar o serviço de IA.

O nome original continua disponível apenas durante a requisição para conferir a
extensão declarada. Ele não participa do caminho físico. O arquivo persistido
recebe um UUID aleatório e é criado com operação exclusiva, impedindo
sobrescrita silenciosa.

## 2. Política de arquivos aceita

| Item | Regra |
| --- | --- |
| Formatos | JPEG (`.jpg`/`.jpeg`) e PNG (`.png`) |
| MIME real | Derivado da assinatura e da estrutura interna |
| MIME declarado | Deve coincidir com o MIME real |
| Extensão | Deve coincidir com o conteúdo real |
| Tamanho | Até `MAX_UPLOAD_SIZE_MB`, padrão de 10 MB |
| Largura | Até `MAX_IMAGE_WIDTH_PX`, padrão de 12.000 px |
| Altura | Até `MAX_IMAGE_HEIGHT_PX`, padrão de 12.000 px |
| Pixels | Até `MAX_IMAGE_PIXELS`, padrão de 40.000.000 |
| PNG | CRC, chunks, IDAT e tamanho descompactado validados |
| JPEG | Assinatura, segmentos, SOF, SOS, EOI e dimensões validados |
| PNG entrelaçado | Rejeitado neste protótipo para validação determinística |

Entradas vazias, incompatíveis, corrompidas, truncadas ou acima dos limites
retornam erro 4xx antes da gravação.

## 3. Armazenamento físico

A hierarquia interna é:

```text
uploads/exams/<clinic_id>/<patient_id>/<exam_id>/<uuid-aleatorio>.<extensao-canonica>
```

O nome original não aparece na hierarquia nem no nome físico. A criação usa modo
exclusivo (`xb`) e tenta outro UUID diante de uma colisão, em vez de substituir
um arquivo existente.

Permissões aplicadas no Linux:

```text
Diretórios: 0750
Arquivos:    0640
```

O arquivo é sincronizado com `fsync` antes de ser associado ao registro.

## 4. Path traversal e links simbólicos

Todos os caminhos usados para download, análise ou exclusão são resolvidos em
relação à raiz segura de uploads. Caminhos que escapam dessa raiz retornam HTTP
403. Links simbólicos usados como arquivo final também são rejeitados.

A exclusão segura ignora caminhos externos e remove apenas arquivos regulares
internos. Diretórios vazios criados para clínica, paciente e exame são limpos
após a remoção.

## 5. Download e isolamento entre clínicas

A autorização do exame é validada antes da resolução e entrega do arquivo:

- Administrador Master pode acessar os exames previstos pela administração;
- Funcionário da Clínica acessa apenas exames da própria clínica;
- Médico acessa apenas exames atribuídos a ele.

O endpoint de download continua exigindo `exams:download`. Uma tentativa de
baixar um exame de outra clínica retorna HTTP 403 e não cria log de download.

## 6. Exclusão e retenção

A política adotada para o protótipo é conservadora:

- cancelamento é lógico e preserva o arquivo;
- restauração reutiliza o mesmo arquivo retido;
- substituição bem-sucedida remove a versão anterior somente depois do commit;
- falha de banco após gravar um arquivo novo remove o arquivo órfão;
- não existe exclusão física pública de exame nesta etapa;
- limpeza por prazo/SLA permanece uma rotina administrativa futura.

Assim, a CHK-10 não introduz apagamento automático que possa eliminar evidência
clínica do protótipo.

## 7. Testes automatizados

O arquivo `backend/tests/test_exam_file_security.py` cobre:

1. PNG e JPEG válidos;
2. MIME declarado falso;
3. extensão incompatível;
4. conteúdo não-imagem renomeado;
5. PNG e JPEG truncados;
6. CRC PNG inválido;
7. tamanho excedido;
8. largura, altura e quantidade de pixels;
9. nome original malicioso sem controle do caminho;
10. nome UUID e criação sem sobrescrita;
11. modos `0750` e `0640`;
12. path traversal e symlink;
13. exclusão limitada à raiz segura;
14. download bloqueado entre clínicas;
15. auditoria de download permitido;
16. retenção no cancelamento;
17. remoção da versão anterior após substituição.

## 8. Execução no Docker

Na raiz do projeto:

```bash
chmod +x scripts/verify_chk10_file_security.sh
./scripts/verify_chk10_file_security.sh
```

O script executa os testes específicos, a suíte completa do backend, os
contratos acumulados do frontend, o build do Vite e a compilação dos módulos
Python.

Resultado final esperado:

```text
[CHK-10] Validação concluída com sucesso.
```

## 9. Critério de conclusão

A CHK-10 é considerada concluída quando:

- conteúdo real, MIME e extensão são coerentes;
- imagens corrompidas e entradas maliciosas retornam 4xx;
- tamanho e dimensões respeitam os limites configurados;
- o nome original não controla o caminho físico;
- uma gravação não sobrescreve outra;
- paths externos e links simbólicos são rejeitados;
- arquivos de outra clínica não podem ser baixados;
- cancelamento retém o arquivo e substituição remove somente a versão anterior;
- o script Docker termina sem falhas.

## 10. Limites conscientes

- A validação JPEG é estrutural e detecta assinaturas, segmentos e truncamentos;
  não pretende substituir ferramentas forenses de reconstrução de imagem.
- A retenção por prazo não foi automatizada porque o TCC não define um SLA de
  descarte e a remoção automática seria inadequada sem requisito explícito.
- O armazenamento permanece em volume Docker local, adequado à demonstração
  acadêmica; object storage e antivírus ficam fora do escopo atual.
