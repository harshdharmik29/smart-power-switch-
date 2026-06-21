import streamlit as st
import pandas as pd
import random
import datetime as dt

st.set_page_config(page_title="Smart Power Dashboard", page_icon="⚡", layout="wide")

# ---------------------------------------------------------------------------
# DEMO DATA SETUP (will be replaced by real PZEM-004T / ESP32 readings later)
# ---------------------------------------------------------------------------

ROOM_NAMES = ["Room 101", "Room 102", "Room 103", "Room 104"]

if "rooms" not in st.session_state:
    st.session_state.rooms = {
        name: {
            "relay_on": True,
            "voltage": 230.0,
            "current": 0.0,
            "power": 0.0,
            "energy_today_kwh": round(random.uniform(0.5, 3.5), 2),
            "energy_month_kwh": round(random.uniform(20, 90), 1),
        }
        for name in ROOM_NAMES
    }

if "history" not in st.session_state:
    # seed some fake history for the chart, last 12 readings per room
    now = dt.datetime.now()
    rows = []
    for i in range(12, 0, -1):
        t = now - dt.timedelta(minutes=5 * i)
        for name in ROOM_NAMES:
            rows.append({
                "time": t,
                "room": name,
                "power_w": round(random.uniform(50, 800), 1),
            })
    st.session_state.history = pd.DataFrame(rows)


def simulate_reading():
    """Mimic a fresh PZEM-004T poll for every room and append to history."""
    now = dt.datetime.now()
    new_rows = []
    for name, r in st.session_state.rooms.items():
        if r["relay_on"]:
            power = round(random.uniform(50, 900), 1)   # watts
            current = round(power / 230.0, 2)
            r["voltage"] = round(random.uniform(218, 238), 1)
            r["current"] = current
            r["power"] = power
            # add ~5 min worth of energy
            r["energy_today_kwh"] = round(r["energy_today_kwh"] + power * (5 / 60) / 1000, 3)
            r["energy_month_kwh"] = round(r["energy_month_kwh"] + power * (5 / 60) / 1000, 2)
        else:
            r["voltage"] = 0.0
            r["current"] = 0.0
            r["power"] = 0.0
        new_rows.append({"time": now, "room": name, "power_w": r["power"]})

    st.session_state.history = pd.concat(
        [st.session_state.history, pd.DataFrame(new_rows)], ignore_index=True
    )


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------

st.sidebar.title("⚡ Settings")
view = st.sidebar.radio("View as", ["Landlord (all rooms)", "Tenant (single room)"])
rate_per_unit = st.sidebar.number_input("Rate per unit (₹/kWh)", min_value=1.0, value=8.0, step=0.5)
fixed_charge = st.sidebar.number_input("Fixed charge per room (₹/month)", min_value=0.0, value=50.0, step=10.0)

st.sidebar.divider()
if st.sidebar.button("🔄 Simulate next reading", use_container_width=True):
    simulate_reading()

st.sidebar.caption(
    "Demo mode — readings are simulated. "
    "Connect ESP32 + PZEM-004T later and replace `simulate_reading()` "
    "with live MQTT/HTTP data."
)

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def room_bill(energy_kwh):
    return round(energy_kwh * rate_per_unit + fixed_charge, 2)


def render_room_card(name, r):
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.subheader(name)
        with c2:
            status = "🟢 ON" if r["relay_on"] else "🔴 OFF"
            st.markdown(f"**{status}**")

        m1, m2, m3 = st.columns(3)
        m1.metric("Power", f"{r['power']} W")
        m2.metric("Voltage", f"{r['voltage']} V")
        m3.metric("Current", f"{r['current']} A")

        m4, m5 = st.columns(2)
        m4.metric("Today", f"{r['energy_today_kwh']} kWh")
        m5.metric("This month", f"{r['energy_month_kwh']} kWh")

        st.markdown(f"**Estimated bill:** ₹{room_bill(r['energy_month_kwh'])}")

        toggle = st.toggle("Power Switch", value=r["relay_on"], key=f"toggle_{name}")
        if toggle != r["relay_on"]:
            r["relay_on"] = toggle
            st.rerun()


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

st.title("🏠 Smart Power Switch Dashboard")
st.caption("Per-room energy monitoring & remote control — demo build")

if view == "Landlord (all rooms)":
    total_month_kwh = sum(r["energy_month_kwh"] for r in st.session_state.rooms.values())
    total_bill = sum(room_bill(r["energy_month_kwh"]) for r in st.session_state.rooms.values())

    k1, k2, k3 = st.columns(3)
    k1.metric("Total rooms", len(ROOM_NAMES))
    k2.metric("Total energy (month)", f"{round(total_month_kwh, 1)} kWh")
    k3.metric("Total expected revenue", f"₹{round(total_bill, 2)}")

    st.divider()
    cols = st.columns(2)
    for i, (name, r) in enumerate(st.session_state.rooms.items()):
        with cols[i % 2]:
            render_room_card(name, r)

else:
    selected = st.selectbox("Select your room", ROOM_NAMES)
    render_room_card(selected, st.session_state.rooms[selected])

st.divider()
st.subheader("📈 Power usage history (last readings)")

if view == "Tenant (single room)":
    chart_df = st.session_state.history[st.session_state.history["room"] == selected]
else:
    chart_df = st.session_state.history

pivot = chart_df.pivot_table(index="time", columns="room", values="power_w", aggfunc="last")
st.line_chart(pivot)

st.caption(
    "⚠️ Overload alert demo: rooms drawing over 800W trigger a warning in a real deployment "
    "(threshold configurable from this same sidebar later)."
)
