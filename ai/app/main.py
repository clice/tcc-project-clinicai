"""
API de Inteligência Artificial do ClinicAI.

Este serviço será responsável por receber imagens de exames,
executar o modelo de IA e retornar o resultado da análise.
"""

from fastapi import FastAPI


app = FastAPI(
    title="ClinicAI AI Service",
    description="Serviço de inferência de IA para análise de exames endoscópicos e colonoscópicos.",
    version="0.1.0",
)


@app.get("/")
def root():
    """
    Rota inicial da API de IA.
    """
    return {
        "message": "ClinicAI AI Service is running",
        "version": "0.1.0",
    }


@app.get("/health")
def health_check():
    """
    Rota de verificação de saúde do serviço.
    """
    return {
        "status": "ok",
        "service": "clinicai-ai",
    }
