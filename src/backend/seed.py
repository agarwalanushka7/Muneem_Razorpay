from src.backend.database import SessionLocal

from src.backend.models.platform import Platform


def seed_platforms():
    db = SessionLocal()

    platforms = [
        {
            "name": "direct",
            "display_name": "Direct Store",
            "platform_type": "sales_channel",
            "connection_type": "native",
        },
        {
            "name": "blinkit",
            "display_name": "Blinkit",
            "platform_type": "sales_channel",
            "connection_type": "manual",
        },
        {
            "name": "zepto",
            "display_name": "Zepto",
            "platform_type": "sales_channel",
            "connection_type": "manual",
        },
    ]

    try:
        for platform_data in platforms:

            existing_platform = (
                db.query(Platform)
                .filter(
                    Platform.name
                    == platform_data["name"]
                )
                .first()
            )

            if existing_platform:
                print(
                    f"Platform already exists: "
                    f"{existing_platform.display_name}"
                )
                continue

            platform = Platform(
                name=platform_data["name"],
                display_name=platform_data["display_name"],
                platform_type=platform_data["platform_type"],
                connection_type=platform_data["connection_type"],
                status="disconnected",
                is_active=False,
                last_synced_at=None,
            )

            db.add(platform)

            print(
                f"Created platform: "
                f"{platform_data['display_name']}"
            )

        db.commit()

        print("\nPlatform seeding completed successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_platforms()