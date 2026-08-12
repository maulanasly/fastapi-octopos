from datetime import datetime, timedelta, timezone
from math import ceil
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.stock_movement import StockMovement
from app.schemas.replenishment import ReplenishmentSuggestion


def build_replenishment_suggestions(
    db: Session,
    products: List[Product],
    lookback_days: int,
) -> List[ReplenishmentSuggestion]:
    if not products:
        return []

    product_ids = [product.id for product in products]
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)

    sales_rows = (
        db.query(
            StockMovement.product_id,
            func.coalesce(func.sum(StockMovement.quantity_delta), 0).label("net_delta"),
        )
        .filter(
            StockMovement.product_id.in_(product_ids),
            StockMovement.movement_type == "sale",
            StockMovement.created_at >= cutoff,
        )
        .group_by(StockMovement.product_id)
        .all()
    )
    sales_map = {row.product_id: int(row.net_delta or 0) for row in sales_rows}

    suggestions: List[ReplenishmentSuggestion] = []
    for product in products:
        sold_quantity = max(-(sales_map.get(product.id, 0)), 0)
        daily_sales_velocity = sold_quantity / lookback_days

        reorder_point = max(int(product.reorder_point or 0), 0)
        min_stock = max(int(product.min_stock or 0), 0)
        lead_time_days = max(int(product.lead_time_days or 0), 0)
        max_stock = (
            int(product.max_stock)
            if product.max_stock is not None and product.max_stock >= 0
            else None
        )

        lead_time_demand = ceil(daily_sales_velocity * lead_time_days)
        projected_stock_at_lead_time = product.stock_quantity - lead_time_demand
        should_reorder = any(
            (
                product.stock_quantity <= reorder_point,
                product.stock_quantity <= min_stock,
                projected_stock_at_lead_time <= reorder_point,
                projected_stock_at_lead_time <= min_stock,
            )
        )

        suggested_target_stock = max(min_stock, reorder_point + lead_time_demand)
        if max_stock is not None and max_stock > 0:
            suggested_target_stock = min(suggested_target_stock, max_stock)

        recommended_order_quantity = 0
        if should_reorder:
            recommended_order_quantity = max(
                suggested_target_stock - product.stock_quantity,
                0,
            )

        suggestions.append(
            ReplenishmentSuggestion(
                product_id=product.id,
                product_name=product.name,
                sku=product.sku,
                current_stock=product.stock_quantity,
                min_stock=min_stock,
                max_stock=max_stock,
                reorder_point=reorder_point,
                lead_time_days=lead_time_days,
                lookback_days=lookback_days,
                sold_quantity=sold_quantity,
                daily_sales_velocity=round(daily_sales_velocity, 4),
                projected_stock_at_lead_time=projected_stock_at_lead_time,
                suggested_target_stock=suggested_target_stock,
                recommended_order_quantity=recommended_order_quantity,
                should_reorder=should_reorder,
            )
        )

    return suggestions
