from sqlalchemy import func
from sqlalchemy.orm import Session

from src.backend.models.order import Order
from src.backend.models.platform import Platform


class PlatformAnalyticsService:

    def get_platform_analysis(
        self,
        db: Session,
    ) -> dict:

        # =====================================================
        # GET ALL PLATFORMS
        # =====================================================

        platforms = (
            db.query(Platform)
            .order_by(Platform.id.asc())
            .all()
        )

        # =====================================================
        # TOTAL REVENUE
        # =====================================================

        total_revenue = (
            db.query(
                func.coalesce(
                    func.sum(Order.total_amount),
                    0.0,
                )
            )
            .filter(
                Order.status.in_(
                    [
                        "completed",
                        "confirmed",
                        "paid",
                        "success",
                        "successful",
                        "delivered",
                    ]
                )
            )
            .scalar()
            or 0.0
        )

        total_revenue = float(total_revenue)

        # =====================================================
        # PLATFORM ANALYSIS
        # =====================================================

        platform_results = []

        for platform in platforms:

            platform_name = platform.name

            platform_revenue = (
                db.query(
                    func.coalesce(
                        func.sum(
                            Order.total_amount
                        ),
                        0.0,
                    )
                )
                .filter(
                    Order.platform
                    == platform_name
                )
                .filter(
                    Order.status.in_(
                        [
                            "completed",
                            "confirmed",
                            "paid",
                            "success",
                            "successful",
                            "delivered",
                        ]
                    )
                )
                .scalar()
                or 0.0
            )

            platform_orders = (
                db.query(Order)
                .filter(
                    Order.platform
                    == platform_name
                )
                .count()
            )

            platform_revenue = float(
                platform_revenue
            )

            if platform_orders > 0:
                average_order_value = (
                    platform_revenue
                    / platform_orders
                )
            else:
                average_order_value = 0.0

            if total_revenue > 0:
                revenue_percentage = (
                    platform_revenue
                    / total_revenue
                ) * 100
            else:
                revenue_percentage = 0.0

            platform_results.append(
                {
                    "platform": platform_name,
                    "revenue": round(
                        platform_revenue,
                        2,
                    ),
                    "orders": platform_orders,
                    "average_order_value": round(
                        average_order_value,
                        2,
                    ),
                    "revenue_percentage": round(
                        revenue_percentage,
                        2,
                    ),
                }
            )

        # =====================================================
        # RETURN
        # =====================================================

        return {
            "total_revenue": round(
                total_revenue,
                2,
            ),
            "platform_count": len(
                platforms
            ),
            "platforms": platform_results,
        }


platform_analytics_service = (
    PlatformAnalyticsService()
)