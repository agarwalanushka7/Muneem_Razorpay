from sqlalchemy.orm import Session

from src.backend.models.customer import Customer


def get_all_customers(db: Session):
    return db.query(Customer).order_by(Customer.id.desc()).all()


def get_customer_by_id(db: Session, customer_id: int):
    return (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )


def get_customer_by_email(db: Session, email: str):
    return (
        db.query(Customer)
        .filter(Customer.email == email)
        .first()
    )


def create_customer(
    db: Session,
    name: str,
    email: str,
    phone: str = "",
):
    customer = Customer(
        name=name,
        email=email,
        phone=phone,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def update_customer(
    db: Session,
    customer: Customer,
    name: str,
    email: str,
    phone: str = "",
):
    customer.name = name
    customer.email = email
    customer.phone = phone

    db.commit()
    db.refresh(customer)

    return customer


def delete_customer(
    db: Session,
    customer: Customer,
):
    db.delete(customer)
    db.commit()