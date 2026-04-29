import os

import pythoncom
import win32com.client

TO_EMAIL = os.environ.get("TO_EMAIL", "billing@acadiacraft.com")
CC_EMAIL = os.environ.get("CC_EMAIL", "denis@acadiacraft.com")
FROM_NAME = os.environ.get("FROM_NAME", "Vitalie")


def open_invoice_email(project_name, stage, pdf_path, project_code=""):
    """
    Opens a new email in local Outlook, pre-filled with recipients, subject,
    body, and the proposal PDF attached. The user reviews and sends manually.
    """
    pythoncom.CoInitialize()
    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)

    mail.To = TO_EMAIL
    mail.CC = CC_EMAIL
    code = project_code.strip()
    code_part = f" - {code}" if code and code.lower() not in project_name.lower() else ""
    mail.Subject = f"Invoice Request - {stage}{code_part} - {project_name}"
    mail.Body = (
        f"Hi Denis,\n\n"
        f"Please send an invoice for {stage} for {project_name} "
        f"based on the attached proposal.\n\n"
        f"Thank you,\n"
        f"{FROM_NAME}"
    )
    mail.Attachments.Add(pdf_path)
    mail.Display()
