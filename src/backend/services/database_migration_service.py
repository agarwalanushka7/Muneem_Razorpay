from sqlalchemy import inspect, text

from src.backend.database import engine


def migrate_agent_actions():
    """
    Safely add the new customer/offer fields to the
    existing agent_actions table.

    This is intentionally idempotent:
    running it multiple times will not recreate
    columns that already exist.
    """

    inspector = inspect(engine)

    if "agent_actions" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns(
            "agent_actions"
        )
    }

    columns_to_add = {
        "customer_id": "INTEGER",
        "product_id": "INTEGER",
        "original_amount": "FLOAT",
        "discount_percentage": "FLOAT DEFAULT 0",
        "discount_amount": "FLOAT DEFAULT 0",
        "final_amount": "FLOAT",
        "customer_message": "TEXT",
    }

    with engine.begin() as connection:

        for column_name, column_definition in columns_to_add.items():

            if column_name not in existing_columns:

                connection.execute(
                    text(
                        f"""
                        ALTER TABLE agent_actions
                        ADD COLUMN {column_name}
                        {column_definition}
                        """
                    )
                )