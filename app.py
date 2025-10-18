import os
import re
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# =========================
# Config + credenciales
# =========================
st.set_page_config(page_title="HappyThings Dashboard", layout="wide")

# Lee user/pass desde Secrets (Streamlit Cloud) o variables de entorno
ADMIN_USER = st.secrets.get("DASH_USER", os.getenv("DASH_USER", "admin"))
ADMIN_PASS = st.secrets.get("DASH_PASS", os.getenv("DASH_PASS", "admin"))

# =========================
# Login simple
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_form():
    st.title("HappyThings Dashboard")
    st.caption("Demo con autenticación simple. No usar en producción.")
    with st.form("login"):
        u = st.text_input("Usuario", value="", placeholder="Usuario")
        p = st.text_input("Contraseña", value="", type="password", placeholder="••••••")
        submitted = st.form_submit_button("Ingresar")
        if submitted:
            if u == ADMIN_USER and p == ADMIN_PASS:
                st.session_state.logged_in = True
                st.success("Ingreso correcto ✅")
                st.rerun()
            else:
                st.error("Usuario/contraseña inválidos")

if not st.session_state.logged_in:
    login_form()
    st.stop()

# =========================
# Lectura de datos
# =========================
st.sidebar.header("Fuente de datos")

load_mode = st.sidebar.radio(
    "¿Cómo cargar los datos?",
    ["Subir archivo (.xlsx)", "Archivo local (ruta)"],
    index=0
)

@st.cache_data(ttl=60)
def read_all_sheets(xlsx_file):
    xls = pd.ExcelFile(xlsx_file)
    data = {}
    for sh in xls.sheet_names:
        data[sh] = pd.read_excel(xlsx_file, sheet_name=sh)
    return data

data = {}
excel_file = None

if load_mode == "Subir archivo (.xlsx)":
    up = st.sidebar.file_uploader("Sube el Excel", type=["xlsx"])
    if up is not None:
        excel_file = up
        data = read_all_sheets(excel_file)
else:
    default_path = "HappyThings (2).xlsx"
    excel_path = st.sidebar.text_input("Ruta al Excel", value=default_path)
    if st.sidebar.button("Cargar"):
        if not os.path.exists(excel_path):
            st.sidebar.error(f"No se encontró el archivo: {excel_path}")
        else:
            excel_file = excel_path
            data = read_all_sheets(excel_file)

if not data:
    st.info("Cargá el Excel (subiéndolo o por ruta) para ver el tablero.")
    st.stop()

ventas = data.get("Ventas", pd.DataFrame())
inventario = data.get("Inventario", pd.DataFrame())
gastos = data.get("Gastos", pd.DataFrame())
retiro = data.get("Retiro", pd.DataFrame())

# =========================
# Helpers de limpieza
# =========================
def clean_ventas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    for c in ["Monto Neto", "Envío (UYU)", "Ventas totales"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "Cantidad" in df.columns:
        df["Cantidad"] = pd.to_numeric(df["Cantidad"], errors="coerce").fillna(1)
    else:
        df["Cantidad"] = 1.0
    return df

def clean_inventario(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in ["Stock real", "Precio Venta Publico", "Precio Venta Mayorista", "Costo"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df

def clean_gastos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

    def detect_moneda(row):
        m = str(row.get("Moneda", "")).strip()
        if m in ["USD", "UYU", "EUR"]:
            return m
        m2 = str(row.get("Monto", ""))
        m_match = re.search(r"(USD|UYU|EUR)", m2)
        if m_match:
            return m_match.group(1)
        return "UYU"

    df["Moneda_detect"] = df.apply(detect_moneda, axis=1)
    df["Monto_num"] = pd.to_numeric(df.get("Monto.1", np.nan), errors="coerce")
    return df

ventas = clean_ventas(ventas)
inventario = clean_inventario(inventario)
gastos = clean_gastos(gastos)

# =========================
# Filtros
# =========================
st.sidebar.header("Filtros")

# Fechas seguras aunque no haya datos
min_date = ventas["Fecha"].min() if "Fecha" in ventas.columns else None
max_date = ventas["Fecha"].max() if "Fecha" in ventas.columns else None
if pd.isna(min_date) or pd.isna(max_date):
    today = pd.to_datetime("today").normalize()
    min_date, max_date = today, today

date_rng = st.sidebar.date_input(
    "Rango de fechas",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_rng, tuple) and len(date_rng) == 2:
    d1, d2 = [pd.to_datetime(date_rng[0]), pd.to_datetime(date_rng[1])]
else:
    d1, d2 = min_date, max_date

canales = sorted([c for c in ventas.get("Canal de venta", pd.Series(dtype=str)).dropna().unique()])
sel_canales = st.sidebar.multiselect("Canales", canales, default=canales)

formas = sorted([c for c in ventas.get("Forma de pago", pd.Series(dtype=str)).dropna().unique()])
sel_formas = st.sidebar.multiselect("Formas de pago", formas, default=formas)

vf = ventas.copy()
if "Fecha" in vf.columns:
    vf = vf[(vf["Fecha"] >= d1) & (vf["Fecha"] <= d2)]
if sel_canales and "Canal de venta" in vf.columns:
    vf = vf[vf["Canal de venta"].isin(sel_canales)]
if sel_formas and "Forma de pago" in vf.columns:
    vf = vf[vf["Forma de pago"].isin(sel_formas)]

# =========================
# KPIs
# =========================
total_ventas = float(vf.get("Monto Neto", pd.Series(dtype=float)).sum())
total_envios = float(vf.get("Envío (UYU)", pd.Series(dtype=float)).sum())
num_ventas = int(len(vf))

# COGS aprox a partir de inventario.Costo por Item
cogs_total = 0.0
if "Item" in vf.columns and "Item" in inventario.columns and "Costo" in inventario.columns:
    costo_por_item = inventario[["Item", "Costo"]].drop_duplicates()
    vf_costeadas = vf.merge(costo_por_item, on="Item", how="left")
    vf_costeadas["COGS"] = vf_costeadas["Costo"] * vf_costeadas["Cantidad"]
    cogs_total = float(vf_costeadas["COGS"].sum())

margen_bruto = total_ventas - cogs_total
aov = total_ventas / max(num_ventas, 1)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Ventas (UYU)", f"{total_ventas:,.0f}")
c2.metric("Órdenes", f"{num_ventas}")
c3.metric("AOV (UYU)", f"{aov:,.0f}")
c4.metric("COGS aprox (UYU)", f"{cogs_total:,.0f}")
c5.metric("Margen bruto aprox (UYU)", f"{margen_bruto:,.0f}")

# =========================
# Gráficos y tablas
# =========================
if "Fecha" in vf.columns:
    vf["YMonth"] = vf["Fecha"].dt.to_period("M").astype(str)
    vent_m = vf.groupby("YMonth")["Monto Neto"].sum().reset_index()
    fig_month = px.line(vent_m, x="YMonth", y="Monto Neto", title="Ventas mensuales (UYU)")
    st.plotly_chart(fig_month, use_container_width=True)

c6, c7 = st.columns(2)

if "Canal de venta" in vf.columns:
    canal_counts = vf["Canal de venta"].value_counts().reset_index()
    canal_counts.columns = ["Canal", "Ventas"]
    c6.plotly_chart(px.pie(canal_counts, values="Ventas", names="Canal",
                           title="Participación por canal"), use_container_width=True)

if "Forma de pago" in vf.columns:
    forma_counts = vf["Forma de pago"].value_counts().reset_index()
    forma_counts.columns = ["Forma de pago", "Ventas"]
    c7.plotly_chart(px.bar(forma_counts, x="Forma de pago", y="Ventas",
                           title="Ventas por forma de pago"), use_container_width=True)

if "YMonth" in vf.columns:
    top_meses = vf.groupby("YMonth")["Monto Neto"].sum().reset_index() \
                  .sort_values("Monto Neto", ascending=False).head(5)
    st.subheader("Top 5 períodos de mayor facturación (mes)")
    st.dataframe(top_meses, use_container_width=True)

if "Item" in vf.columns and "Monto Neto" in vf.columns:
    top_prod = vf.groupby("Item")["Monto Neto"].sum().reset_index() \
                 .sort_values("Monto Neto", ascending=False).head(10)
    st.subheader("Top 10 productos por ingreso")
    st.dataframe(top_prod, use_container_width=True)

# Inventario KPIs
st.subheader("Inventario")
stock_total_unid = float(inventario.get("Stock real", pd.Series(dtype=float)).sum())
valor_inv_costo = float((inventario.get("Stock real", 0) * inventario.get("Costo", 0)).sum()) \
                  if "Stock real" in inventario.columns and "Costo" in inventario.columns else 0.0
valor_inv_publico = float((inventario.get("Stock real", 0) * inventario.get("Precio Venta Publico", 0)).sum()) \
                    if "Stock real" in inventario.columns and "Precio Venta Publico" in inventario.columns else 0.0

ci1, ci2, ci3 = st.columns(3)
ci1.metric("Stock total (unid.)", f"{stock_total_unid:,.0f}")
ci2.metric("Valor inventario a COSTO (UYU)", f"{valor_inv_costo:,.0f}")
ci3.metric("Valor inventario a PVP (UYU)", f"{valor_inv_publico:,.0f}")

with st.expander("Ver inventario completo"):
    st.dataframe(inventario, use_container_width=True)

# Gastos
st.subheader("Gastos")
g_mon = gastos.groupby("Moneda_detect")["Monto_num"].sum(min_count=1).reset_index()
g_pag = gastos.groupby("Pago por")["Monto_num"].sum(min_count=1).reset_index().sort_values("Monto_num", ascending=False)

cg1, cg2 = st.columns(2)
with cg1:
    st.caption("Por moneda (usa columna 'Monto.1')")
    st.dataframe(g_mon, use_container_width=True)
with cg2:
    st.caption("Por 'Pago por' (usa columna 'Monto.1')")
    st.dataframe(g_pag, use_container_width=True)

st.caption("📌 El tablero se recalcula cada vez que cargás el Excel (subida o ruta).")
