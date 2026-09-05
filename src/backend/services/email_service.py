import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid, formatdate
from html import escape


class EmailService:

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", self.smtp_username)

    def send_offer_email(
        self,
        to_email: str,
        customer_name: str,
        product_name: str,
        original_amount: float,
        discount_percentage: float,
        discount_amount: float,
        final_amount: float,
        payment_link: str,
        purchase_history: list | None = None,
    ):
        try:
            to_email = (to_email or "").strip()
            if not to_email:
                return {"success": False, "sent": False, "message": "Customer email address is missing."}
            if not self.smtp_username:
                return {"success": False, "sent": False, "message": "SMTP username is not configured."}
            if not self.smtp_password:
                return {"success": False, "sent": False, "message": "SMTP password is not configured."}

            purchase_history = purchase_history or []

            text_purchases = []
            html_purchases = []
            for purchase in purchase_history:
                name = str(purchase.get("product_name", "Previous purchase"))
                qty = purchase.get("quantity", 1) or 1
                amount = float(purchase.get("amount", 0) or 0)
                text_purchases.append(f"• {name} · Qty {qty} · ₹{amount:,.2f}")
                html_purchases.append(
                    f"<li><strong>{escape(name)}</strong> · Qty {escape(str(qty))} · ₹{amount:,.2f}</li>"
                )

            previous_text = "\n".join(text_purchases) or (
                "Your recent shopping activity helped us personalize this recommendation."
            )
            previous_html = (
                "<ul>" + "".join(html_purchases) + "</ul>"
                if html_purchases
                else "<p>Your recent shopping activity helped us personalize this recommendation.</p>"
            )

            if discount_percentage > 0:
                offer_text = (
                    f"Original price: ₹{original_amount:,.2f}\n"
                    f"You save: ₹{discount_amount:,.2f}\n"
                    f"Your personalized price: ₹{final_amount:,.2f}"
                )
                offer_html = (
                    f"<p><strong>{discount_percentage:g}% personalized discount</strong></p>"
                    f"<p><s>₹{original_amount:,.2f}</s> "
                    f"<strong>₹{final_amount:,.2f}</strong></p>"
                    f"<p>You save <strong>₹{discount_amount:,.2f}</strong>.</p>"
                )
            else:
                offer_text = f"Your personalized price is ₹{final_amount:,.2f}."
                offer_html = f"<p>Your personalized price is <strong>₹{final_amount:,.2f}</strong>.</p>"

            subject = f"A personalized offer on {product_name} from MUNEEM"
            safe_name = escape(customer_name or "Customer")
            safe_product = escape(product_name or "your recommended product")
            safe_link = escape(payment_link or "", quote=True)

            body = (
                f"Hi {customer_name},\n\n"
                "MUNEEM noticed your recent shopping activity and selected "
                f"{product_name} as a relevant next purchase for you.\n\n"
                "YOUR RECENT PURCHASES\n----------------------\n"
                f"{previous_text}\n\n"
                "YOUR PERSONALIZED OFFER\n-------------------------\n"
                f"{offer_text}\n\n"
                "COMPLETE YOUR PURCHASE\n----------------------\n"
                "Use the secure Razorpay payment link below:\n\n"
                f"{payment_link}\n\n"
                "Best,\nMUNEEM"
            )

            html_body = f"""<!doctype html>
<html><body style="margin:0;background:#f5f5f1;color:#111;font-family:Arial,Helvetica,sans-serif;">
<div style="max-width:640px;margin:0 auto;padding:36px 24px;">
<div style="font-size:11px;letter-spacing:2px;font-weight:700;margin-bottom:28px;">MUNEEM · PERSONALIZED OFFER</div>
<h1 style="font-family:Georgia,serif;font-size:36px;line-height:1.05;font-weight:400;margin:0 0 14px;">Hi {safe_name},</h1>
<p style="font-size:16px;line-height:1.65;">We noticed your recent shopping activity and selected <strong>{safe_product}</strong> as a relevant next purchase for you.</p>
<div style="border-top:1px solid #d6d6d0;border-bottom:1px solid #d6d6d0;padding:22px 0;margin:28px 0;">
<div style="font-size:10px;letter-spacing:1.8px;font-weight:700;margin-bottom:10px;">YOUR RECENT PURCHASES</div>
{previous_html}</div>
<div style="background:#fff;border:1px solid #deded7;padding:24px;margin:24px 0;">
<div style="font-size:10px;letter-spacing:1.8px;font-weight:700;margin-bottom:12px;">YOUR PERSONALIZED OFFER</div>
<h2 style="font-family:Georgia,serif;font-size:28px;font-weight:400;margin:0 0 10px;">{safe_product}</h2>
{offer_html}</div>
<p style="font-size:15px;line-height:1.6;">Complete your purchase securely using Razorpay:</p>
<p style="margin:28px 0;"><a href="{safe_link}" style="display:inline-block;background:#111;color:#fff;text-decoration:none;padding:15px 22px;font-size:13px;font-weight:700;">COMPLETE PURCHASE →</a></p>
<p style="font-size:12px;color:#666;word-break:break-all;">Or open this link directly:<br>{safe_link}</p>
<div style="border-top:1px solid #d6d6d0;margin-top:36px;padding-top:18px;font-size:12px;color:#777;">This offer was selected by MUNEEM using your recent shopping activity.</div>
<p>Best,<br><strong>MUNEEM</strong></p>
</div></body></html>"""

            message = MIMEMultipart("alternative")
            message["From"] = self.from_email
            message["To"] = to_email
            message["Subject"] = subject
            message["Date"] = formatdate(localtime=True)
            message["Message-ID"] = make_msgid()
            message.attach(MIMEText(body, "plain", "utf-8"))
            message.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.from_email, [to_email], message.as_string())

            return {
                "success": True,
                "sent": True,
                "to": to_email,
                "subject": subject,
                "message_id": message["Message-ID"],
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "provider": "smtp",
                "payment_link": payment_link,
                "purchase_count": len(purchase_history),
                "message": "Personalized offer email sent successfully.",
            }

        except Exception as exc:
            print("EMAIL SEND ERROR:", repr(exc))
            return {
                "success": False,
                "sent": False,
                "to": to_email,
                "message": "Failed to send personalized offer email.",
                "error": str(exc),
            }


email_service = EmailService()
