from fastapi import FastAPI

from licenseflow_ai.api.routes.crm import router as crm_router

app = FastAPI(
    title='LicenseFlow API',
    description='AI-assisted commercial licensing workflow API',
    version='0.1.0',
)

app.include_router(crm_router)

@app.get('/health')
def health_check() -> dict[str, str]:
    return {'status':'ok'}