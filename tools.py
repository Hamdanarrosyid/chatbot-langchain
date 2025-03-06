import base64
from gmailapi import service
from langchain_core.tools import tool

service = service()

def decode_base64(data):
    """Helper untuk decode base64."""
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

def extract_body(payload):
    """Ekstrak isi email dari format text/plain atau text/html."""
    body_text = ""
    body_html = ""

    if "parts" in payload:
        for part in payload["parts"]:
            mime_type = part.get("mimeType", "")

            if mime_type == "text/plain" and "body" in part:
                body_data = part["body"].get("data", "")
                if body_data:
                    body_text = decode_base64(body_data)

            elif mime_type == "text/html" and "body" in part:
                body_data = part["body"].get("data", "")
                if body_data:
                    body_html = decode_base64(body_data)


    elif payload["mimeType"] == "text/plain":
        body_data = payload["body"].get("data", "")
        if body_data:
            body_text = decode_base64(body_data)

    elif payload["mimeType"] == "text/html":
        body_data = payload["body"].get("data", "")
        if body_data:
            body_html = decode_base64(body_data)

    return body_text if body_text else body_html

def get_attachments(service, msg_id, payload):
    """Ambil attachment dari email."""
    attachments = []

    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("filename"):
                att_id = part["body"].get("attachmentId")
                if att_id:
                    attachment = service.users().messages().attachments().get(
                        userId="me", messageId=msg_id, id=att_id
                    ).execute()

                    file_data = decode_base64(attachment["data"])
                    attachments.append({
                        "filename": part["filename"],
                        "mimeType": part["mimeType"],
                        "data": file_data  # Bisa disimpan sebagai file
                    })

    return attachments

# @tool(response_format="content")
def get_messages(query: str):
    """Get messages from Gmail."""
    results = service.users().messages().list(userId="me", q=query, maxResults=1, labelIds=["INBOX"]).execute()
    messages = results.get("messages", [])
    
    email_details = []
    for message in messages:
        msg = service.users().messages().get(userId="me", id=message["id"], format="full").execute()
        
        payload = msg.get("payload", {})
        headers = payload.get("headers", [])

        # Extract important details
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
        date = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown Date")

         # Extract body (text/plain atau text/html)
        body = extract_body(payload)

        # Extract attachments jika ada
        attachments = get_attachments(service, message["id"], payload)

        email_details.append({
            "id": message["id"],
            "subject": subject,
            "from": sender,
            "date": date,
            "body": body,
            "attachments": attachments
        })

    return email_details

    
# print(get_messages("from:hamdan arosyid"))