import imaplib
import email
import requests
import anthropic
import os
from email.header import decode_header

# Credentials from environment variables
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

PROCESSED_EMAILS_FILE = "processed_emails.txt"

INQUIRY_PROMPT = """
You are a helpful assistant that replies to guest inquiries for a vacation villa rental.
Always be warm, friendly and professional. Sign off messages as "Saul & Team".
Write in plain conversational text only — no bullet points, no bold text, no asterisks, no markdown formatting, no emojis, no symbols.
Write exactly as a person would type a natural message in the Airbnb messaging box.
IMPORTANT: Do NOT include any phone numbers, email addresses, or any other contact information in your reply.

PROPERTY: 3BR - Montecristo Villa at Quivira Los Cabos
HOST: Saul González (Superhost, 4.76 stars, 181 reviews)

PROPERTY DETAILS:
- 3 bedrooms, 3.5 bathrooms, up to 10 guests, 4 beds
- Check-in: 4:00 PM | Check-out: 11:00 AM
- Self check-in via building staff
- Private infinity pool + indoor/outdoor Jacuzzi
- Ocean & mountain views (views may vary per villa)
- Located in Montecristo, an exclusive gated community at Quivira Los Cabos

PRICING & FEES:
- Pricing is based on number of guests declared at booking
- Extra guest fee doubles if not declared before check-in
- Housekeeping: not included, available for $80 USD/day
- Environmental sanitation tax: ~$1.70 USD/room/night, charged at check-in
- We do not stock coffee, condiments, cooking oils, sugar, salt, pepper, etc.

HOUSE RULES:
- No pets
- No parties or events
- No smoking
- Montecristo community rules are strictly enforced

MINIMUM STAY:
- No minimum stay requirement
- EXCEPT December 20 to January 2 (holiday season minimum applies)

VILLA NOTES:
- Listings are not linked to a specific villa — all have same amenities and layout
- Views may vary; we cannot guarantee exact view shown in photos
- We do not take location requests
- We manage villas in both Phase I and Phase II

PUEBLO BONITO RESORT ACCESS:
- Guests have complimentary access to Pueblo Bonito resort facilities (pools, beach, gym, etc.)
- Restaurants and bars: guests pay per item unless they purchase the all-inclusive meal plan
- All-inclusive meal plan available for purchase directly through the resort (no minimum days)
- Meal plan covers all restaurants and bars at Pueblo Bonito Montecristo, Sunset Beach, Rosé, and Los Cabos
- For meal plan pricing and purchase, guests must contact Pueblo Bonito directly — do not include contact details
"""

RESERVATION_PROMPT = """
You are a helpful assistant that replies to guests who have already made a reservation for a vacation villa rental.
Always be warm, friendly and professional. Sign off messages as "Saul & Team".
Write in plain conversational text only — no bullet points, no bold text, no asterisks, no markdown formatting, no emojis, no symbols.
Write exactly as a person would type a natural message in the Airbnb messaging box.

PROPERTY: 3BR - Montecristo Villa at Quivira Los Cabos
HOST: Saul González (Superhost, 4.76 stars, 181 reviews)

PROPERTY DETAILS:
- 3 bedrooms, 3.5 bathrooms, up to 10 guests, 4 beds
- Check-in: 4:00 PM | Check-out: 11:00 AM
- Self check-in via building staff
- Private infinity pool + indoor/outdoor Jacuzzi
- Ocean & mountain views (views may vary per villa)
- Located in Montecristo, an exclusive gated community at Quivira Los Cabos

PRICING & FEES:
- Pricing is based on number of guests declared at booking
- Extra guest fee doubles if not declared before check-in
- Housekeeping: not included, available for $80 USD/day
- Environmental sanitation tax: ~$1.70 USD/room/night, charged at check-in
- We do not stock coffee, condiments, cooking oils, sugar, salt, pepper, etc.

HOUSE RULES:
- No pets
- No parties or events
- No smoking
- Montecristo community rules are strictly enforced

MINIMUM STAY:
- No minimum stay requirement
- EXCEPT December 20 to January 2 (holiday season minimum applies)

VILLA NOTES:
- Listings are not linked to a specific villa — all have same amenities and layout
- Views may vary; we cannot guarantee exact view shown in photos
- We do not take location requests
- We manage villas in both Phase I and Phase II

PUEBLO BONITO RESORT ACCESS:
- Guests have complimentary access to Pueblo Bonito resort facilities (pools, beach, gym, etc.)
- Restaurants and bars: guests pay per item unless they purchase the all-inclusive meal plan
- All-inclusive meal plan available for purchase directly through the resort (no minimum days)
- Meal plan covers all restaurants and bars at:
  * Pueblo Bonito Montecristo
  * Pueblo Bonito Sunset Beach
  * Pueblo Bonito Rosé
  * Pueblo Bonito Los Cabos
- For meal plan pricing and purchase, guests must contact Pueblo Bonito directly:
  * USA: 1-800-990-8250
  * Canada: 1-855-478-2811
  * Mexico: 800-966-0606
"""

def load_processed_emails():
    if os.path.exists(PROCESSED_EMAILS_FILE):
        with open(PROCESSED_EMAILS_FILE, "r") as f:
            return set(line.strip() for line in f.readlines())
    return set()

def save_processed_email(email_id):
    with open(PROCESSED_EMAILS_FILE, "a") as f:
        f.write(email_id + "\n")

def get_reply(inquiry, is_reservation=False):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = RESERVATION_PROMPT if is_reservation else INQUIRY_PROMPT
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"{prompt}\n\nGuest message:\n{inquiry}"
            }
        ]
    )
    return message.content[0].text

def send_to_telegram(reply, subject, is_reservation=False):
    email_type = "Reservation" if is_reservation else "Inquiry"
    message = f"📧 New Airbnb {email_type}\n\nSubject: {subject}\n\nSuggested Reply:\n{reply}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    })

def get_new_emails():
    mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    mail.login(GMAIL_ADDRESS.strip(), GMAIL_APP_PASSWORD.strip().replace(" ", ""))
    mail.select("inbox")

    status1, messages1 = mail.search(None, 'SUBJECT', '"FW: Inquiry for"')
    status2, messages2 = mail.search(None, 'SUBJECT', '"FW: Reservation for"')

    ids1 = messages1[0].split() if messages1[0] else []
    ids2 = messages2[0].split() if messages2[0] else []

    emails = []

    for eid in ids1:
        status, msg_data = mail.fetch(eid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        message_id = msg.get("Message-ID", "").strip()
        if not message_id:
            continue
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
        emails.append({
            "message_id": message_id,
            "subject": subject,
            "body": body[:2000],
            "is_reservation": False
        })

    for eid in ids2:
        status, msg_data = mail.fetch(eid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        message_id = msg.get("Message-ID", "").strip()
        if not message_id:
            continue
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
        emails.append({
            "message_id": message_id,
            "subject": subject,
            "body": body[:2000],
            "is_reservation": True
        })

    mail.close()
    mail.logout()
    return emails

def main():
    print("Checking for new Airbnb emails...")

    processed_emails = load_processed_emails()
    emails = get_new_emails()

    if not emails:
        print("No emails found.")
        return

    new_count = 0
    for em in emails:
        if em["message_id"] in processed_emails:
            print(f"Already processed: {em['subject']}")
            continue

        print(f"New email found: {em['subject']}")
        reply = get_reply(em['body'], em['is_reservation'])
        send_to_telegram(reply, em['subject'], em['is_reservation'])
        save_processed_email(em["message_id"])
        new_count += 1
        print(f"Reply sent to Telegram!")

    if new_count == 0:
        print("No new unprocessed emails found.")
    else:
        print(f"Processed {new_count} new emails!")

if __name__ == "__main__":
    main()
