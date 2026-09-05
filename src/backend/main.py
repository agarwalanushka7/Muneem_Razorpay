from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.core.config import settings
from src.backend.core.errors import general_exception_handler

from src.backend.database import Base, engine

# =========================================================
# MODELS
# =========================================================

from src.backend.models.product import Product
from src.backend.models.customer import Customer
from src.backend.models.order import Order
from src.backend.models.transaction import Transaction
from src.backend.models.opportunity import Opportunity
from src.backend.models.ai_policy import AIPolicy
from src.backend.models.agent_action import AgentAction
from src.backend.models.audit_log import AuditLog
from src.backend.models.platform import Platform
from src.backend.models.merchant import Merchant

# =========================================================
# API ROUTERS
# =========================================================

from src.backend.api.health import router as health_router
from src.backend.api.auth import router as auth_router
from src.backend.api.products import router as product_router
from src.backend.api.customers import router as customer_router
from src.backend.api.dashboard import router as dashboard_router
from src.backend.api.orders import router as order_router
from src.backend.api.transactions import router as transaction_router
from src.backend.api.payments import router as payment_router
from src.backend.api.opportunities import router as opportunity_router
from src.backend.api.agent import router as agent_router
from src.backend.api.ai_policy import router as ai_policy_router
from src.backend.api.agent_actions import router as agent_action_router
from src.backend.api.audit import router as audit_router
from src.backend.api.platforms import router as platform_router
from src.backend.routes.data_routes import router as data_router
from src.backend.api.payment_sync import router as payment_sync_router


from src.backend.services.database_migration_service import (
    migrate_agent_actions,
)
# =========================================================
# APP
# =========================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    exception_handlers={
        Exception: general_exception_handler,
    },
)


# =========================================================
# DATABASE
# =========================================================

Base.metadata.create_all(
    bind=engine
)

# =========================================================
# DATABASE MIGRATION
# =========================================================

migrate_agent_actions()

# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# ROUTERS
# =========================================================

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(product_router)
app.include_router(customer_router)
app.include_router(dashboard_router)
app.include_router(order_router)
app.include_router(transaction_router)
app.include_router(payment_router)
app.include_router(opportunity_router)
app.include_router(agent_router)
app.include_router(ai_policy_router)
app.include_router(agent_action_router)
app.include_router(audit_router)
app.include_router(data_router)
app.include_router(payment_sync_router)
# PLATFORM ROUTER
app.include_router(platform_router)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "message": f"{settings.app_name} API is running"
    }