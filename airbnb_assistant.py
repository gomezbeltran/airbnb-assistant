import streamlit as st
import anthropic
import os

os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

PROPERTY_INFO = """
You are a helpful assistant that replies to guest inquiries for a vacation villa rental.
Always be professional. Sign off messages as "Saul & Team".
Write in plain conversational text only — no bullet points, no bold text, no asterisks, no markdown formatting, no emojis, no symbols. 
Write exactly as a person would type a natural message in the Airbnb messaging box.

PROPERTY: 3BR - Montecristo Villa at Quivira Los Cabos
HOST: Saul González (Superhost, 4.76 stars, 181 reviews)

PROPERTY DETAILS:
- 3 bedrooms, 3.5 bathrooms, up to 10 guests, 4 beds
- Check-in: 4:00 PM | Check-out: 11:00 AM
- Check-in is at Montecristo Front Desk
- Private infinity pool + indoor/outdoor Jacuzzi
- Ocean & mountain views (views may vary per villa)
- Located in Montecristo, an exclusive gated community at Quivira Los Cabos

PRICING & FEES:
- Pricing is based on number of guests declared at booking
- Extra guest fee doubles if not declared before day of arrival
- Housekeeping: not included, available for $80 USD/day
- Environmental sanitation tax: ~$1.70 USD/room/night, charged at check-in
- We do not stock coffee, condiments, cooking oils, sugar, salt, pepper, etc.
- Cribs available for rent. Please contact Concierge.
- Golf carts available for rent. Please contact Concierge.

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
- Guests have complimentary access to Pueblo Bonito Resorts facilities (pools, beach, gym, etc.)
- Restaurants and bars: guests pay per item unless they purchase the all-inclusive meal plan
- All-inclusive meal plan available for purchase directly through the resort (no minimum days)
- Meal plan covers all restaurants and bars at the following Resorts:
  * Pueblo Bonito Montecristo
  * Pueblo Bonito Sunset Beach
  * Pueblo Bonito Rosé
  * Pueblo Bonito Los Cabos
- For meal plan pricing and purchase, guests must contact Pueblo Bonito directly:
  * USA: 1-800-990-8250
  * Canada: 1-855-478-2811
  * Mexico: 800-966-0606
- Do NOT quote meal plan prices — direct guests to call the resort
- Additionals services like babysitting, private chef, catering service, etc. can be arranged through Concierge. Please contact Concierge to quote and more information
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

# --- Streamlit UI ---
st.set_page_config(page_title="Montecristo Villa Assistant", page_icon="🏡")

st.title("🏡 Montecristo Villa")
st.subheader("Airbnb Reply Assistant")
st.markdown("Paste a guest inquiry below and get an instant professional reply.")

inquiry = st.text_area("Guest Inquiry", placeholder="Paste the guest message here...", height=150)

if st.button("Generate Reply", type="primary"):
    if not inquiry.strip():
        st.warning("Please paste a guest inquiry first!")
    else:
        with st.spinner("Generating reply..."):
            reply = get_reply(inquiry)
        st.success("Reply ready! Copy it and paste into Airbnb.")
        st.text_area("Your Reply", value=reply, height=300)
