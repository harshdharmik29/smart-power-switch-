# ⚡ Smart Power Switch Dashboard

A Streamlit-based dashboard for per-room/per-flat energy monitoring and remote
power control — built for rental setups (PG, hostel, flats) where one
electricity meter needs to be split into individually billed, individually
switchable rooms.

This is the **demo/UI layer**. It currently runs on simulated readings so the
dashboard, billing logic, and controls can be tested before hardware is wired up.

---

## Features

- **Landlord view** — see all rooms at once: live power draw, total monthly
  energy, total expected revenue
- **Tenant view** — single room dashboard with live readings and bill
- **Remote ON/OFF switch** per room (relay control, simulated for now)
- **Auto bill calculation** — `(energy × rate/unit) + fixed charge`,
  both configurable from the sidebar
- **Usage history chart** — power draw over recent readings, per room
- Architecture designed to map directly onto real hardware later
  (see [Hardware Integration](#hardware-integration) below)

---

## Project structure

```
smartpower/
├── app.py             # Streamlit dashboard (main app)
└── requirements.txt    # Python dependencies
```

---

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

App opens at `http://localhost:8501`.

## Deploying (free)

1. Push `app.py` and `requirements.txt` to a GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect the repo, point it to `app.py`, deploy

---

## How the demo data works

- `st.session_state.rooms` holds live state per room: voltage, current,
  power, today's kWh, month's kWh, relay status
- `st.session_state.history` holds a rolling log of power readings used
  for the chart
- Clicking **"🔄 Simulate next reading"** in the sidebar calls
  `simulate_reading()`, which generates a random power draw for each room
  that's switched ON and adds it to history — standing in for a real
  PZEM-004T poll

---

## Hardware Integration

Planned hardware: **ESP32 + PZEM-004T (energy meter module) + relay**, one
ESP32 per flat talking to multiple PZEM-004T units over RS485/Modbus (one
per room), with a relay per room for remote cutoff.

To go from demo → live data, only `simulate_reading()` in `app.py` needs to
change:

1. ESP32 polls each PZEM-004T over Modbus, publishes readings (voltage,
   current, power, kWh) via **MQTT** or an **HTTP POST** to a small backend
2. Replace `simulate_reading()` with a function that fetches the latest
   values from that backend/MQTT broker instead of `random.uniform(...)`
3. Wire the relay toggle (`st.toggle`) to publish an MQTT command /
   HTTP request back to the ESP32 instead of just flipping
   `r["relay_on"]` in memory

Everything else — bill calculation, layout, landlord/tenant views, the
chart — stays the same.

### Suggested next features
- Overload protection (auto-cutoff above a current/power threshold)
- Prepaid balance mode with auto-disconnect at zero
- Tamper/disconnect alerts
- Scheduled ON/OFF timers
- Push notifications for high usage

---

## Notes

- Default demo rooms: `Room 101–104` — edit `ROOM_NAMES` in `app.py` to
  match your actual flat layout
- Rate per unit and fixed charge are adjustable live from the sidebar,
  no code changes needed for billing tweaks
