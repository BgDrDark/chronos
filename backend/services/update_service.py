"""Service за автоматични актуализации"""

import logging
import os
from datetime import datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com/repos/bgdrdark/chronos/releases/latest"


class UpdateService:
    """Service за проверка и изпълнение на актуализации"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_for_updates(self) -> dict:
        """Проверява GitHub за налична нова версия"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(GITHUB_API_URL)
                if response.status_code != 200:
                    return {
                        "has_update": False,
                        "current_version": settings.VERSION,
                        "latest_version": None,
                        "error": f"GitHub API returned {response.status_code}",
                    }

                data = response.json()
                latest_version = data.get("tag_name", "").lstrip("v")
                current_version = settings.VERSION.lstrip("v")

                has_update = latest_version and latest_version != current_version

                return {
                    "has_update": has_update,
                    "current_version": current_version,
                    "latest_version": latest_version,
                    "release_name": data.get("name", ""),
                    "release_notes": data.get("body", ""),
                    "published_at": data.get("published_at", ""),
                }
        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            return {
                "has_update": False,
                "current_version": settings.VERSION,
                "latest_version": None,
                "error": str(e),
            }

    async def execute_update(self) -> dict:
        """Изпълнява flow: проверка → deploy → email"""
        output_lines = []

        try:
            output_lines.append(
                f"[AUTO-UPDATE] Starting at {datetime.now().isoformat()}"
            )

            # 1. Проверка за нова версия
            update_info = await self.check_for_updates()
            if not update_info.get("has_update"):
                output_lines.append(
                    f"[AUTO-UPDATE] No update available. Current: {update_info.get('current_version')}"
                )
                return {
                    "status": "skipped",
                    "output": "\n".join(output_lines),
                    "reason": "No new version available",
                }

            latest_version = update_info["latest_version"]
            output_lines.append(f"[AUTO-UPDATE] New version found: {latest_version}")

            # 2. Trigger deploy чрез deploy manager
            deploy_key = settings.get_deploy_key()
            deploy_manager_url = (
                os.environ.get("DEPLOY_MANAGER_URL")
                or os.environ.get("DEPLOY_LISTENER_URL")
                or "http://host.docker.internal:14241"
            )

            output_lines.append(
                f"[AUTO-UPDATE] Triggering deploy via {deploy_manager_url}"
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{deploy_manager_url}/deploy",
                    json={"version": latest_version},
                    headers={"Authorization": f"UpdateKey {deploy_key}"},
                )

                if response.status_code != 200:
                    output_lines.append(
                        f"[AUTO-UPDATE] Deploy failed: {response.status_code} - {response.text}"
                    )
                    await self._send_update_email(
                        version=latest_version,
                        status="failed",
                        output="\n".join(output_lines),
                    )
                    return {
                        "status": "failed",
                        "output": "\n".join(output_lines),
                    }

                output_lines.append("[AUTO-UPDATE] Deploy started successfully")

            # 3. Poll за статус (до 10 мин)
            final_status = await self._poll_deploy_status(
                deploy_manager_url, latest_version, output_lines
            )

            # 4. Email уведомление
            await self._send_update_email(
                version=latest_version,
                status=final_status,
                output="\n".join(output_lines),
            )

            return {
                "status": final_status,
                "output": "\n".join(output_lines),
                "version": latest_version,
            }

        except Exception as e:
            logger.error(f"Auto-update failed: {e}")
            output_lines.append(f"[AUTO-UPDATE] Error: {e!s}")

            await self._send_update_email(
                version="unknown",
                status="failed",
                output="\n".join(output_lines),
            )

            return {
                "status": "failed",
                "output": "\n".join(output_lines),
                "error": str(e),
            }

    async def _poll_deploy_status(
        self, manager_url: str, version: str, output_lines: list
    ) -> str:
        """Poll deploy статус до приключване"""
        import asyncio

        max_polls = 300  # 10 мин при 2 сек интервал
        for _i in range(max_polls):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{manager_url}/deploy-status")
                    if response.status_code == 200:
                        data = response.json()
                        status = data.get("status", "running")
                        progress = data.get("progress", "")
                        output_lines.append(
                            f"[AUTO-UPDATE] Status: {status} - {progress}"
                        )

                        if not data.get("is_deploying", False):
                            return "success" if status == "success" else "failed"
            except Exception as e:
                logger.debug(f"Poll error: {e}")

            await asyncio.sleep(2)

        return "timeout"

    async def _send_update_email(self, version: str, status: str, output: str):
        """Изпраща email уведомление за update"""
        from sqlalchemy import select

        from backend.database.models import UpdateSchedule

        try:
            result = await self.db.execute(
                select(UpdateSchedule).order_by(UpdateSchedule.id.desc()).limit(1),
            )
            schedule = result.scalar_one_or_none()

            if not schedule or not schedule.notify_email:
                logger.info("No notify_email configured, skipping email")
                return

            # SMTP settings
            from backend.crud.repositories import settings_repo

            smtp_server = await settings_repo.get_setting(self.db, "smtp_server")
            smtp_port = await settings_repo.get_setting(self.db, "smtp_port")
            smtp_username = await settings_repo.get_setting(self.db, "smtp_username")
            smtp_password = await settings_repo.get_setting(self.db, "smtp_password")
            sender_email = await settings_repo.get_setting(self.db, "sender_email")
            use_tls = await settings_repo.get_setting(self.db, "use_tls")

            if not all([smtp_server, smtp_port, smtp_username, smtp_password]):
                logger.warning("SMTP not configured, skipping email")
                return

            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            status_text = {
                "success": "Успешно",
                "failed": "Грешка",
                "skipped": "Пропуснато",
                "timeout": "Таймаут",
            }.get(status, status)

            msg = MIMEMultipart()
            msg["From"] = sender_email or smtp_username
            msg["To"] = schedule.notify_email
            msg["Subject"] = f"Chronos ERP Auto-Update: {status_text} (v{version})"

            body = f"""
Chronos ERP - Автоматична актуализация

Статус: {status_text}
Версия: {version}
Време: {datetime.now().isoformat()}

Лог:
{output[-2000:]}

---
Chronos ERP Auto-Update System
"""
            msg.attach(MIMEText(body, "plain", "utf-8"))

            smtp_port_int = int(smtp_port)
            if smtp_port_int == 465:
                with smtplib.SMTP_SSL(smtp_server, smtp_port_int) as server:
                    server.login(smtp_username, smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(smtp_server, smtp_port_int) as server:
                    if use_tls and use_tls.lower() == "true":
                        server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.send_message(msg)

            logger.info(f"Update email sent to {schedule.notify_email}")

        except Exception as e:
            logger.error(f"Failed to send update email: {e}")


update_service = UpdateService
