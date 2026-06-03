import streamlit as st
import anthropic
import os
import imaplib
import email
from email.header import decode_header

# Debug secrets
st.write(st.secrets)
GMAIL_APP_PASSWORD = st.secrets["GMAIL_APP_PASSWORD"]

PROPERTY_INFO = """
You are a helpful assistant that replies to guest inquiries for a vacation villa rental.
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
- Do NOT quote meal plan prices — direct guests to call the resort
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

def get_airbnb_emails():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        mail.select("inbox")
        
        # Search for unread Airbnb emails
        status, messages = mail.search(None, 'FROM', '"automated@airbnb.com"')
        email_ids = messages[0].split()
        
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
st.set_page_config(page_title="Montecristo Villa Assistant", page_icon="🏡")

st.title("🏡 Montecristo Villa")
st.subheader("Airbnb Reply Assistant")

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
    if st.button("Fetch Airbnb Emails", type="primary"):
        with st.spinner("Connecting to Gmail..."):
            emails = get_airbnb_emails()
        
        if isinstance(emails, str):
            st.error(emails)
        elif not emails:
            st.info("No Airbnb emails found.")
        else:
            st.success(f"Found {len(emails)} emails!")
            for i, em in enumerate(emails):
                with st.expander(f"📧 {em['subject']} — {em['date']}"):
                    st.markdown(f"**From:** {em['from']}")
                    st.markdown("**Message:**")
                    st.text(em['body'])
                    if st.button(f"Generate Reply for this email", key=f"reply_{i}"):
                        with st.spinner("Generating reply..."):
                            reply = get_reply(em['body'])
                        st.markdown("**Your Reply:**")
                        st.markdown(reply)
                        st.text_area("Copy this reply", value=reply, height=300, key=f"copy_{i}")
