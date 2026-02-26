from models import db, OrderItem
from sqlalchemy import func


def recommend_products(company_id: int | None, limit: int = 5):
    """Return top-selling product names for the provided company."""
    if company_id is None:
        return []

    results = (
        db.session.query(OrderItem.product_name)
        .filter(OrderItem.company_id == company_id)
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
        .all()
    )
    return [r[0] for r in results]
