import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
from streamlit_autorefresh import st_autorefresh
from streamlit_geolocation import streamlit_geolocation
import streamlit.components.v1 as components

# 🔄 refresco
st_autorefresh(interval=2000, key="gps_refresh")

st.set_page_config(page_title="Modo Reflejo PRO+", layout="wide")

# =========================
# 🎛️ ESTILO GLOBAL (pantalla por color)
# =========================
def set_bg(color_hex):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {color_hex};
            transition: background-color 0.3s ease;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# beep simple (funciona en navegador)
def beep():
    components.html(
        """
        <script>
        var ctx = new (window.AudioContext || window.webkitAudioContext)();
        var o = ctx.createOscillator();
        var g = ctx.createGain();
        o.type = "sine";
        o.frequency.value = 880;
        o.connect(g);
        g.connect(ctx.destination);
        o.start();
        setTimeout(function(){ o.stop(); }, 180);
        </script>
        """,
        height=0,
    )

st.title("⚡ MODO REFLEJO PRO+")

# =========================
# 📍 Zonas
# =========================
ZONAS = {
    "Zona Romantica": (20.603, -105.234),
    "Centro": (20.611, -105.230),
    "Marina": (20.653, -105.254),
    "Hotelera": (20.640, -105.235)
}

# =========================
# 📦 Estado
# =========================
if "data" not in st.session_state:
    st.session_state.data = []
if "ruta" not in st.session_state:
    st.session_state.ruta = []
if "pago_sel" not in st.session_state:
    st.session_state.pago_sel = None
if "km_sel" not in st.session_state:
    st.session_state.km_sel = None
if "last_beep" not in st.session_state:
    st.session_state.last_beep = 0

# =========================
# 📍 GPS
# =========================
loc = streamlit_geolocation()
lat = loc.get("latitude") if loc else None
lon = loc.get("longitude") if loc else None

if lat and lon:
    st.success(f"📍 {lat:.5f}, {lon:.5f}")
    st.session_state.ruta.append([lat, lon])
    if len(st.session_state.ruta) > 120:
        st.session_state.ruta.pop(0)
else:
    st.warning("Activa GPS")

# =========================
# 📏 Funciones
# =========================
def distancia(a, b):
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5

def detectar_zona(lat, lon):
    mejor, menor = None, float("inf")
    for z, c in ZONAS.items():
        d = distancia((lat, lon), c)
        if d < menor:
            menor, mejor = d, z
    return mejor

def evaluar(pago, km):
    v = pago / km
    if v >= 12:
        return "ACEPTAR", "#0f9d58"   # verde
    elif v >= 9:
        return "DUDAR", "#f4b400"     # amarillo
    else:
        return "RECHAZAR", "#db4437"  # rojo

zona = detectar_zona(lat, lon) if lat and lon else None
if zona:
    st.info(f"📍 Zona: {zona}")

# =========================
# 🧠 ATAJOS INTELIGENTES (por zona)
# =========================
# Puedes ajustar estos presets a tu realidad
PRESETS = {
    "Centro":       {"pagos":[30,40,50,60,80], "kms":[2,3,4,5,6]},
    "Marina":       {"pagos":[40,50,60,70,90], "kms":[3,4,5,6,7]},
    "Hotelera":     {"pagos":[50,60,70,90,110],"kms":[3,4,5,6,8]},
    "Zona Romantica":{"pagos":[35,45,55,70,90],"kms":[2,3,4,5,6]},
}
pagos = PRESETS.get(zona, PRESETS["Centro"])["pagos"]
kms   = PRESETS.get(zona, PRESETS["Centro"])["kms"]

# =========================
# ⚡ UI RÁPIDA
# =========================
st.subheader("⚡ Toca y decide")

c1, c2 = st.columns(2)

with c1:
    st.markdown("### 💰 Pago")
    for p in pagos:
        if st.button(f"${p}", key=f"p_{p}", use_container_width=True):
            st.session_state.pago_sel = p

with c2:
    st.markdown("### 📏 Distancia")
    for k in kms:
        if st.button(f"{k} km", key=f"k_{k}", use_container_width=True):
            st.session_state.km_sel = k

# =========================
# ⚡ EVALUACIÓN AUTOMÁTICA
# =========================
pago = st.session_state.pago_sel
km   = st.session_state.km_sel

if pago and km:
    decision, color = evaluar(pago, km)

    # Fondo por decisión
    set_bg(color)

    # Indicador grande
    st.markdown(
        f"<h1 style='text-align:center; color:white; font-size:72px;'>{decision}</h1>",
        unsafe_allow_html=True
    )

    # $/km en vivo
    st.markdown(
        f"<h3 style='text-align:center; color:white;'>${pago} / {km} km = {pago/km:.2f} $/km</h3>",
        unsafe_allow_html=True
    )

    # 🔊 beep si ACEPTAR (evita repetir cada refresh)
    import time
    now = time.time()
    if decision == "ACEPTAR" and (now - st.session_state.last_beep) > 3:
        beep()
        st.session_state.last_beep = now

    # 💾 guardar (solo una vez por combinación nueva)
    if lat and lon:
        if not st.session_state.data or (
            st.session_state.data[-1]["pago"] != pago
            or st.session_state.data[-1]["km"] != km
        ):
            st.session_state.data.append({
                "pago": pago,
                "km": km,
                "zona": zona,
                "lat": lat,
                "lon": lon,
                "resultado": decision
            })

# =========================
# 🗺️ MAPA
# =========================
centro = [lat, lon] if lat and lon else [20.62, -105.23]
m = folium.Map(location=centro, zoom_start=16)

# tú
if lat and lon:
    folium.CircleMarker([lat, lon], radius=8, color="blue", fill=True).add_to(m)

# ruta
if len(st.session_state.ruta) > 1:
    folium.PolyLine(st.session_state.ruta, weight=4).add_to(m)

# pedidos
for d in st.session_state.data:
    col = "green" if d["resultado"]=="ACEPTAR" else "orange" if d["resultado"]=="DUDAR" else "red"
    folium.Marker(
        [d["lat"], d["lon"]],
        popup=f"${d['pago']} | {d['km']} km",
        icon=folium.Icon(color=col)
    ).add_to(m)

# heatmap
if st.session_state.data:
    HeatMap([[d["lat"], d["lon"]] for d in st.session_state.data]).add_to(m)

st_folium(m, width=900, height=500)

# =========================
# 📊 STATS RÁPIDAS
# =========================
if st.session_state.data:
    df = pd.DataFrame(st.session_state.data)
    st.subheader("📊 Resumen")
    st.write(f"Promedio pago: ${df['pago'].mean():.2f}")
    st.write(f"Promedio km: {df['km'].mean():.2f}")