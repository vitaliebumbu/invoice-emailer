import pythoncom
import win32com.client

TO_EMAIL = "billing@acadiacraft.com"
CC_EMAIL = "denis@acadiacraft.com"


def open_invoice_email(project_name, stage, pdf_path):
    """
    Opens a new email in the local Outlook application, pre-filled with
    recipients, subject, body, and the proposal PDF attached.
    The user reviews and clicks Send manually.
    """
    pythoncom.CoInitialize()
    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)  # 0 = olMailItem

    mail.To      = TO_EMAIL
    mail.CC      = CC_EMAIL
    mail.Subject = f"Invoice Request – {stage} – {project_name}"
    mail.Body    = (
        f"Hi Denis,\n\n"
        f"Please send an invoice for {stage} for {project_name} "
        f"based on the attached proposal.\n\n"
        f"Thank you,\n"
        f"Vitalie"
    )
    mail.Attachments.Add(pdf_path)
    mail.Display()  # Opens in Outlook — does NOT send automatically
