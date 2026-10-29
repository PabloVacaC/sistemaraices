from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.seed import init_db
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.trabajadores.router import router as trabajadores_router
from app.modules.bitacora.router import router as bitacora_router
from app.modules.pagos.router import router as pagos_router
from app.modules.inventario.router import router as inventario_router
from app.modules.contabilidad.router import router as contabilidad_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Asegura que las tablas y el Super Administrador existan
    try:
        init_db()
    except Exception as e:
        print(f"Error al inicializar la base de datos en el inicio: {e}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="API de Gestión Empresarial - Sistemas Raíces",
    lifespan=lifespan,
)

# Configuración de CORS para Angular (localhost:4200) y clientes móviles
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de rutas de la API
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(trabajadores_router, prefix="/api")
app.include_router(bitacora_router, prefix="/api")
app.include_router(pagos_router, prefix="/api")
app.include_router(inventario_router, prefix="/api")
app.include_router(contabilidad_router, prefix="/api")


@app.get("/")
def raiz():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "docs": "/docs",
        "version": "1.0.0",
    }
