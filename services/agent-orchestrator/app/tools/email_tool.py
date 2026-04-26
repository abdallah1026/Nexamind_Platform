import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List, Optional

class EmailTool:
    name = "email_tool"
    description = "Send emails via SMTP"

    def __init__(self, smtp_host: str = "localhost", smtp_port: int = 587,
                 smtp_user: str = "", smtp_password: str = "", **kwargs):
        self.host = smtp_host
        self.port = smtp_port
        self.user = smtp_user
        self.password = smtp_password

    async def execute(
        self,
        to: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.user:
            return {"status": "skipped", "message": "SMTP not configured"}
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email or self.user
        msg["To"] = ", ".join(to)
        msg.attach(MIMEText(body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))
        
        try:
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                start_tls=True
            )
            return {"status": "sent", "recipients": to}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def schema(self) -> Dict:
        return {"name": self.name, "description": self.description,
                "parameters": {"to": {"type": "array"}, "subject": {"type": "string"}, "body": {"type": "string"}}}
