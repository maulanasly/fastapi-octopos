from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import require_permissions
from app.core.database import get_db
from app.models.refund import Refund
from app.models.user import User
from app.schemas.refund import Refund as RefundSchema
from app.schemas.refund import RefundCreate
from app.services.refunds import create_refund as create_refund_service

router = APIRouter()


@router.get("/", response_model=list[RefundSchema])
def get_refunds(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    order_id: int | None = Query(None, ge=1),
    response: Response = None,
    current_user: User = Depends(require_permissions("refunds:view")),
):
    query = (
        db.query(Refund)
        .filter(Refund.tenant_id == current_user.tenant_id)
        .options(joinedload(Refund.items))
        .order_by(Refund.id.desc())
    )

    if not current_user.is_superuser:
        query = query.filter(Refund.user_id == current_user.id)
    if order_id:
        query = query.filter(Refund.order_id == order_id)

    limit = min(limit, 200)
    total = query.count()
    refunds = query.offset(skip).limit(limit).all()
    response.headers["X-Total-Count"] = str(total)
    return refunds


@router.get("/{refund_id}", response_model=RefundSchema)
def get_refund(
    refund_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("refunds:view")),
):
    refund = (
        db.query(Refund)
        .options(joinedload(Refund.items))
        .filter(
            Refund.id == refund_id,
            Refund.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not refund:
        raise HTTPException(status_code=404, detail="Refund not found")

    if not current_user.is_superuser and refund.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this refund"
        )

    return refund


@router.post("/", response_model=RefundSchema)
def create_refund(
    refund_in: RefundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("refunds:create")),
):
    return create_refund_service(
        db=db,
        current_user=current_user,
        refund_in=refund_in,
        tenant_id=current_user.tenant_id,
    )
