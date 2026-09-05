from sqlalchemy.orm import Session

from src.backend.models.merchant import Merchant


def create_merchant(
    db: Session,
    business_name: str,
    email: str,
    password: str,
) -> Merchant | None:

    existing_merchant = (
        db.query(Merchant)
        .filter(Merchant.email == email)
        .first()
    )

    if existing_merchant:
        return None

    merchant = Merchant(
        business_name=business_name,
        email=email,
        password=password,
    )

    db.add(merchant)
    db.commit()
    db.refresh(merchant)

    return merchant


def authenticate_merchant(
    db: Session,
    email: str,
    password: str,
) -> bool:

    merchant = (
        db.query(Merchant)
        .filter(Merchant.email == email)
        .first()
    )

    if not merchant:
        return False

    return merchant.password == password