from fastapi import APIRouter, Depends

from inventory_app.presentation.api.security import Principal, get_principal, require_admin, require_admin_or_service

router = APIRouter(prefix="/auth-check", tags=["auth check (temporary)"])

@router.get("/whoami")
async def whoami(principal: Principal = Depends(get_principal)):
    """Any valid token  """
    return {"user_id": str(principal.user_id), "roles": sorted(principal.roles)}

@router.get("/admin")
async def admin_only(_: Principal = Depends(require_admin)):
    return {"ok": True, "needs": "admin"}

@router.get("/admin-or-service")
async def admin_or_service(_: Principal = Depends(require_admin_or_service)):
    return {"ok":True, "needs": "admin or service"}
