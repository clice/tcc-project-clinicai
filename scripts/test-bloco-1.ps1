$ErrorActionPreference = 'Stop'

$RepositoryRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepositoryRoot

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Description,

        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Description"
    & $Command

    if ($LASTEXITCODE -ne 0) {
        throw "A etapa '$Description' falhou com o código $LASTEXITCODE."
    }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker não foi encontrado. Instale ou abra o Docker Desktop e tente novamente.'
}

Invoke-CheckedCommand 'Verificando o Docker Compose' { docker compose version }

if (-not (Test-Path 'backend/.env') -or -not (Test-Path 'frontend/.env')) {
    throw 'Faltam backend/.env ou frontend/.env. Crie-os a partir dos respectivos .env.example.'
}

Invoke-CheckedCommand 'Iniciando o banco de dados' { docker compose up -d db }

Write-Host ""
Write-Host '==> Aguardando o PostgreSQL ficar disponível'
$DatabaseReady = $false
for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
    docker compose exec -T db pg_isready -U clinicai -d clinicai *> $null
    if ($LASTEXITCODE -eq 0) {
        $DatabaseReady = $true
        break
    }
    Start-Sleep -Seconds 2
}

if (-not $DatabaseReady) {
    throw 'O PostgreSQL não ficou disponível dentro do tempo esperado.'
}

Invoke-CheckedCommand 'Construindo as imagens de teste' { docker compose build backend frontend }
Invoke-CheckedCommand 'Aplicando as migrations' {
    docker compose run --rm --no-deps --entrypoint alembic backend upgrade head
}
Invoke-CheckedCommand 'Executando os testes do backend' {
    docker compose run --rm --no-deps --entrypoint python backend -m pytest -q
}
Invoke-CheckedCommand 'Validando o contrato do fluxo de exames' {
    docker compose run --rm --no-deps `
        -v "${RepositoryRoot}:/workspace:ro" `
        frontend `
        node /workspace/frontend/scripts/check-exam-state-contract.mjs
}
Invoke-CheckedCommand 'Validando a navegação e as permissões' {
    docker compose run --rm --no-deps frontend npm run check:navigation
}
Invoke-CheckedCommand 'Gerando o build de produção do frontend' {
    docker compose run --rm --no-deps frontend npm run build
}

Write-Host ""
Write-Host 'SUCESSO: todos os testes do Bloco 1 foram aprovados.' -ForegroundColor Green
