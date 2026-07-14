param(
    [switch]$KeepEnvironment
)

$ErrorActionPreference = "Stop"
$ProjectName = "clinicai-chk03"
$ComposeFile = "docker-compose.chk03.yml"
$ReportDir = "reports/chk-03"

function Invoke-Compose {
    param([Parameter(Mandatory = $true)][string[]]$CommandArgs)

    & docker compose -p $ProjectName -f $ComposeFile @CommandArgs
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose falhou: $($CommandArgs -join ' ')"
    }
}

function Invoke-Runner {
    param(
        [Parameter(Mandatory = $true)][string]$Entrypoint,
        [Parameter(Mandatory = $true)][string[]]$CommandArgs
    )

    $composeArgs = @(
        "run", "--rm", "--no-deps", "--entrypoint", $Entrypoint,
        "chk03-runner"
    ) + $CommandArgs
    Invoke-Compose -CommandArgs $composeArgs
}

function Invoke-Startup {
    param([Parameter(Mandatory = $true)][string]$SeedMode)

    Invoke-Compose -CommandArgs @(
        "run", "--rm", "--no-deps", "-e", "SEED_MODE=$SeedMode",
        "chk03-runner", "true"
    )
}

try {
    if (Test-Path $ReportDir) {
        Remove-Item -Recurse -Force $ReportDir
    }
    New-Item -ItemType Directory -Force $ReportDir | Out-Null

    try {
        Invoke-Compose -CommandArgs @("down", "-v", "--remove-orphans")
    }
    catch {
        Write-Host "[CHK-03] Nenhum ambiente anterior para remover."
    }

    Write-Host "[CHK-03] Construindo o runner do backend..."
    Invoke-Compose -CommandArgs @("build", "chk03-runner")

    Write-Host "[CHK-03] Iniciando PostgreSQL descartável..."
    Invoke-Compose -CommandArgs @("up", "-d", "chk03-db")

    $ready = $false
    foreach ($attempt in 1..30) {
        & docker compose -p $ProjectName -f $ComposeFile exec -T chk03-db `
            pg_isready -U clinicai_chk03 -d clinicai_chk03 *> $null
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) {
        throw "PostgreSQL não ficou pronto a tempo."
    }

    Write-Host "[CHK-03] 1/8 - Banco vazio antes das migrations."
    Invoke-Runner -Entrypoint "python" -CommandArgs @(
        "-m", "app.maintenance.database_contract", "assert-empty"
    )

    Write-Host "[CHK-03] 2/8 - Upgrade até o head e contrato do schema."
    Invoke-Runner -Entrypoint "alembic" -CommandArgs @("upgrade", "head")
    Invoke-Runner -Entrypoint "alembic" -CommandArgs @("check")
    Invoke-Runner -Entrypoint "python" -CommandArgs @(
        "-m", "app.maintenance.database_contract", "verify-schema",
        "--output", "/reports/schema-inventory.json"
    )

    Write-Host "[CHK-03] 3/8 - Downgrade/upgrade da migration de índice do CHK-03."
    Invoke-Runner -Entrypoint "alembic" -CommandArgs @(
        "downgrade", "c8d2e4f6a701"
    )
    Invoke-Runner -Entrypoint "python" -CommandArgs @(
        "-m", "app.maintenance.database_contract", "assert-index",
        "--table", "clinics", "--columns", "status_id",
        "--present", "false"
    )
    Invoke-Runner -Entrypoint "alembic" -CommandArgs @("upgrade", "head")
    Invoke-Runner -Entrypoint "python" -CommandArgs @(
        "-m", "app.maintenance.database_contract", "assert-index",
        "--table", "clinics", "--columns", "status_id",
        "--present", "true"
    )

    Write-Host "[CHK-03] 4/8 - Round-trip das migrations recentes de RBAC até o head."
    Invoke-Runner -Entrypoint "alembic" -CommandArgs @(
        "downgrade", "a1b2c3d4e5f6"
    )
    Invoke-Runner -Entrypoint "alembic" -CommandArgs @("upgrade", "head")
    Invoke-Runner -Entrypoint "alembic" -CommandArgs @("check")
    Invoke-Runner -Entrypoint "python" -CommandArgs @(
        "-m", "app.maintenance.database_contract", "verify-schema",
        "--output", "/reports/schema-after-roundtrip.json"
    )

    Write-Host "[CHK-03] 5/8 - Bootstrap estrutural, sem dados demo."
    Invoke-Startup -SeedMode "bootstrap"
    Invoke-Runner -Entrypoint "python" -CommandArgs @(
        "-m", "app.maintenance.database_contract", "assert-no-demo"
    )

    Write-Host "[CHK-03] 6/8 - Preservação de configuração em três startups."
    Invoke-Runner -Entrypoint "python" -CommandArgs @(
        "-m", "app.maintenance.database_contract", "customize"
    )
    Invoke-Runner -Entrypoint "python" -CommandArgs @(
        "-m", "app.maintenance.database_contract", "snapshot",
        "--output", "/reports/bootstrap-customized-reference.json"
    )

    foreach ($iteration in 1..3) {
        Invoke-Startup -SeedMode "bootstrap"
        Invoke-Runner -Entrypoint "python" -CommandArgs @(
            "-m", "app.maintenance.database_contract", "snapshot",
            "--output", "/reports/bootstrap-restart-$iteration.json"
        )
        Invoke-Runner -Entrypoint "python" -CommandArgs @(
            "-m", "app.maintenance.database_contract", "compare",
            "--expected", "/reports/bootstrap-customized-reference.json",
            "--actual", "/reports/bootstrap-restart-$iteration.json"
        )
    }

    Write-Host "[CHK-03] 7/8 - Massa acadêmica opcional e vínculos fictícios."
    Invoke-Startup -SeedMode "academic_demo"
    Invoke-Runner -Entrypoint "python" -CommandArgs @(
        "-m", "app.maintenance.database_contract", "assert-demo"
    )
    Invoke-Runner -Entrypoint "python" -CommandArgs @(
        "-m", "app.maintenance.database_contract", "snapshot",
        "--output", "/reports/academic-demo-reference.json"
    )

    Write-Host "[CHK-03] 8/8 - Idempotência demo em três startups."
    foreach ($iteration in 1..3) {
        Invoke-Startup -SeedMode "academic_demo"
        Invoke-Runner -Entrypoint "python" -CommandArgs @(
            "-m", "app.maintenance.database_contract", "assert-demo"
        )
        Invoke-Runner -Entrypoint "python" -CommandArgs @(
            "-m", "app.maintenance.database_contract", "snapshot",
            "--output", "/reports/academic-demo-restart-$iteration.json"
        )
        Invoke-Runner -Entrypoint "python" -CommandArgs @(
            "-m", "app.maintenance.database_contract", "compare",
            "--expected", "/reports/academic-demo-reference.json",
            "--actual", "/reports/academic-demo-restart-$iteration.json"
        )
    }

    @"
CHK-03 aprovado.

Validado em PostgreSQL 16:
- banco vazio antes de alembic upgrade head;
- head Alembic único e alembic check sem diferenças;
- downgrade/upgrade das migrations recentes;
- uniques, FKs, política de cascata e índices;
- bootstrap sem massa de demonstração;
- preservação de configuração administrativa em três startups;
- criação previsível da massa acadêmica fictícia;
- idempotência da massa acadêmica em três startups.
"@ | Set-Content -Encoding UTF8 "$ReportDir/result.txt"

    Write-Host ""
    Write-Host "CHK-03 aprovado. Evidências: $ReportDir/"
}
finally {
    if ($KeepEnvironment) {
        Write-Host "[CHK-03] Ambiente mantido por -KeepEnvironment."
    }
    else {
        try {
            Invoke-Compose -CommandArgs @("down", "-v", "--remove-orphans")
        }
        catch {
            Write-Warning "Não foi possível remover completamente o ambiente CHK-03."
        }
    }
}
