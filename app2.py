import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
from streamlit_autorefresh import st_autorefresh
from streamlit_geolocation import streamlit_geolocation

# 🔄 Auto refresh cada 3s
st_autorefresh(interval=3000, key="gps_refresh")

st.set_page_config(page_title="Uber Eats Inteligente", layout="wide")

st.title("🛵 Uber Eats Inteligente PRO")

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
# 📦 Datos
# =========================
if "data" not in st.session_state:
    st.session_state.data = []

# =========================
# 📍 GPS (estable)
# =========================
st.subheader("📍 Ubicación en tiempo real")

location = streamlit_geolocation()

lat, lon = None, None

if location is not None:
    lat = location.get("latitude")
    lon = location.get("longitude")

if lat and lon:
    st.success(f"📍 Tu ubicación: {lat:.5f}, {lon:.5f}")
else:
    st.warning("📡 Activa ubicación en tu navegador")

# =========================
# 📏 Funciones
# =========================
def distancia(a, b):
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5

def detectar_zona(lat, lon):
    mejor, menor = None, float("inf")

    for zona, coords in ZONAS.items():
        d = distancia((lat, lon), coords)
        if d < menor:
            menor = d
            mejor = zona

    return mejor

zona_actual = None
if lat and lon:
    zona_actual = detectar_zona(lat, lon)
    st.info(f"📍 Estás en: {zona_actual}")

# =========================
# 💰 Inputs
# =========================
st.subheader("📥 Nuevo pedido")

pago = st.number_input("💰 Pago ($)", min_value=0.0)
km = st.number_input("📏 Distancia (km)", min_value=0.1)

def evaluar(pago, km):
    valor = pago / km
    if valor >= 12:
        return "🟢 ACEPTAR"
    elif valor >= 9:
        return "🟡 DUDAR"
    else:
        return "🔴 RECHAZAR"

# =========================
# ➕ Guardar
# =========================
if st.button("Analizar y guardar"):
    if lat and lon:
        resultado = evaluar(pago, km)

        st.session_state.data.append({
            "pago": pago,
            "km": km,
            "zona": zona_actual,
            "lat": lat,
            "lon": lon,
            "resultado": resultado
        })

        st.success(f"Resultado: {resultado}")
    else:
        st.error("❌ No hay ubicación")

# =========================
# 📊 Datos + Mapa
# =========================
if st.session_state.data:
    df = pd.DataFrame(st.session_state.data)

    st.subheader("📊 Historial")
    st.dataframe(df)

    st.subheader("🗺️ Mapa de pedidos")

    centro = [lat, lon] if lat and lon else [20.62, -105.23]
    mapa = folium.Map(location=centro, zoom_start=14)

    for _, row in df.iterrows():
        color = (
            "green" if "ACEPTAR" in row["resultado"]
            else "orange" if "DUDAR" in row["resultado"]
            else "red"
        )

        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=f"${row['pago']} | {row['km']} km",
            icon=folium.Icon(color=color)
        ).add_to(mapa)

    HeatMap(df[["lat", "lon"]].values.tolist()).add_to(mapa)

    st_folium(mapa, width=900, height=500)

    # =========================
    # 📍 Recomendación
    # =========================
    st.subheader("📍 Recomendación inteligente")

    zonas_score = df.groupby("zona")["pago"].mean()

    if lat and lon:
        mejor_zona, mejor_valor = None, 0

        for zona, promedio in zonas_score.items():
            dist = distancia((lat, lon), ZONAS[zona])
            score = promedio / (dist + 0.001)

            if score > mejor_valor:
                mejor_valor = score
                mejor_zona = zona

        st.success(f"🔥 Muévete hacia: {mejor_zona}")

    # =========================
    # 📈 Stats
    # =========================
    st.subheader("📈 Estadísticas")
    st.write(f"Promedio pago: ${df['pago'].mean():.2f}")
    st.write(f"Promedio km: {df['km'].mean():.2f}")