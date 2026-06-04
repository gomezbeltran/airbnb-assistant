import streamlit as st
import anthropic
import os
import imaplib
import email
from email.header import decode_header

os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
GMAIL_ADDRESS = st.secrets["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = st.secrets["GMAIL_APP_PASSWORD"]
TELEGRAM_BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

PROPERTY_INFO = """
You are an assistant that replies to guest inquiries for a vacation villa rental.
Always be warm and professional.
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
- Do NOT quote meal plan prices — direct guests to call the resort

Check in for our Montecristo Villa happens at the Clubhouse of Montecristo Estates. Please head there to the reception desk where you will be checked in.
Montecristo’s Address is:
Pueblo Bonito Montecristo Estates
Predio Paraíso Escondido, Col. Centro
23450 Cabo San Lucas, B.C.S.
Mexico

Google Maps Link: https://goo.gl/maps/YVsYMaMBVE72

ASSISTANCE DURING YOUR STAY: If you have any question or concern during your stay, please dial 7000 from the villa's phone for assistance. You can also reach them out by whatsapp text at: +526242679930

In case you haven't yet book your Airport PickUp. You can still book it by visiting: https://www.pueblobonito.com/airport-transportation or calling 1-800-990-8250
-There are both private and shared ride options.

IMPORTANT REMINDERS:

EXTRA GUEST CHARGE: Any guest added after the original booking has been made will incur an additional fee. Please make sure the number of people on your reservation corresponds to the total number of guests staying. All guests must be registered, and all applicable guest fees must be paid. The extra guest fee for guests added to the reservation after the booking is made is $50 USD a night per person. This cost will increase to $100 USD a night per person for additional guests added during or after check-in.

EARLY CHECK-INS: You are welcome to head directly to the clubhouse to the reception desk at the time you arrive. We will not be able to confirm at any point whether the villa will be ready for early check in, regardless of the circumstances. We can only confirm that it will be ready at 4:00 p.m; however, if on the day of your check-in we should manage to have it ready earlier, we will be happy to let you in. Keep in mind that you are allowed to use the facilities at the clubhouse while you wait. Our team will also store your luggage and groceries until your villa is ready.

VILLA ASSIGNMENT: Villa assignment will only be confirmed at check-in; it will not be confirmed nor guaranteed at any point before. This is because we are a multi-unit vacation rental property and our villas are assigned based on our reservation's departures and arrivals. Thank you for your understanding.

OUTSIDE SERVICES: Please be advised that outside services are not allowed in the Quivira Los Cabos Community. This includes: private chef, catering services, grocery shopping services, maid services, etc. Only the services provided by the Pueblo Bonito Resorts are permitted.

EXPERIENCE: This is a vacation rental rented experience, which is different than a timeshare or hotel "rental" booked through the Resorts. IMPORTANT: Several amenities that are included by the resorts are not included for vacation rentals. The amenities we offer for this vacation rental are in line with those offered across the vacation rental industry, as well as AirBnb's suggestions for "essential amenities."
"""

def get_reply(inquiry):
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"{PROPERTY_INFO}\n\nGuest inquiry:\n{inquiry}"
            }
        ]
    )
    return message.content[0].text

def send_to_telegram(reply, subject):
    import requests
    message = f"📧 *New Airbnb Inquiry Reply*\n\n*Subject:* {subject}\n\n*Reply:*\n{reply}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    })
 
def get_airbnb_emails():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD.replace(" ", ""))
        mail.select("inbox")
        
        # Search for unread Airbnb emails
        status1, messages1 = mail.search(None, 'SUBJECT', '"FW: Inquiry"')
        status2, messages2 = mail.search(None, 'SUBJECT', '"FW: Reservation"')
        ids1 = messages1[0].split() if messages1[0] else []
        ids2 = messages2[0].split() if messages2[0] else []
        email_ids = ids1 + ids2
        
        # Get last 10 emails
        email_ids = email_ids[-10:] if len(email_ids) > 10 else email_ids
        email_ids = email_ids[::-1]  # newest first
        
        emails = []
        for eid in email_ids:
            status, msg_data = mail.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            
            # Get subject
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")
            
            # Get body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            
            emails.append({
                "subject": subject,
                "from": msg["From"],
                "date": msg["Date"],
                "body": body[:2000]  # limit length
            })
        
        mail.close()
        mail.logout()
        return emails
    
    except Exception as e:
        return f"Error: {str(e)}"

# --- Streamlit UI ---
st.set_page_config(page_title="Quivira Vacation Rentals - AI Assistant", page_icon="🏡")

st.title("🏡 Quivira Vacation Rentals")
st.subheader("Airbnb Reply Agent")

tab1, tab2 = st.tabs(["✍️ Manual Reply", "📧 Email Inquiries"])

# --- Tab 1: Manual Reply ---
with tab1:
    st.markdown("Paste a guest inquiry below and get an instant professional reply.")
    inquiry = st.text_area("Guest Inquiry", placeholder="Paste the guest message here...", height=150)
    if st.button("Generate Reply", type="primary"):
        if not inquiry.strip():
            st.warning("Please paste a guest inquiry first!")
        else:
            with st.spinner("Generating reply..."):
                reply = get_reply(inquiry)
            st.success("Reply ready!")
            st.markdown("**Your Reply:**")
            st.markdown(reply)
            st.text_area("Copy this reply", value=reply, height=300)

# --- Tab 2: Email Inquiries ---
with tab2:
    st.markdown("Fetch your latest Airbnb inquiry emails and generate replies instantly.")

    for key, default in [("emails", []), ("generated_reply", ""), ("reply_subject", "")]:
        if key not in st.session_state:
            st.session_state[key] = default

    if st.button("Fetch Airbnb Emails", type="primary"):
        with st.spinner("Connecting to Gmail..."):
            emails = get_airbnb_emails()
        if isinstance(emails, str):
            st.error(emails)
        elif not emails:
            st.info("No Airbnb emails found.")
        else:
            st.session_state.emails = emails
            st.session_state.generated_reply = ""

    if st.session_state.emails:
        emails = st.session_state.emails
        st.success(f"Found {len(emails)} emails!")
        email_subjects = [f"{i+1}. {em['subject']}" for i, em in enumerate(emails)]
        selected = st.selectbox("Select an email to reply to:", email_subjects)
        idx = email_subjects.index(selected)
        selected_email = emails[idx]
        st.markdown(f"**From:** {selected_email['from']}")
        st.markdown(f"**Date:** {selected_email['date']}")
        st.markdown("**Message:**")
        st.text(selected_email['body'])

        if st.button("Generate Reply for Email", type="primary", key="email_reply_btn"):
            with st.spinner("Generating reply..."):
                st.session_state.generated_reply = get_reply(selected_email['body'])
                st.session_state.reply_subject = selected_email['subject']

        if st.session_state.get("generated_reply", ""):
            st.markdown("**Your Reply:**")
            st.markdown(st.session_state.generated_reply)
            st.text_area("Copy this reply", value=st.session_state.generated_reply, height=300)
            if st.button("📱 Send to Telegram", key="telegram_btn"):
                send_to_telegram(st.session_state.generated_reply, st.session_state.reply_subject)
                st.success("✅ Reply sent to Telegram!")
