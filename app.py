import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import os

st.set_page_config(page_title="Filtro Contable", layout="wide")
st.title("Filtro de Fechas - BD_JDT1_ok")

# Ruta del archivo CSV local
csv_path = "BD_JDT1_ok.csv"
if not os.path.exists(csv_path):
    st.error(f"No se pudo encontrar el archivo {csv_path}")
    st.stop()

# Cargar datos desde CSV
try:
    df = pd.read_csv(csv_path, encoding="latin1", parse_dates=["Fecha"])
except Exception as e:
    st.error(f"Error al leer el archivo: {e}")
    st.stop()

# Asegurar que las fechas sean objetos datetime.date
df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
df = df.dropna(subset=['Fecha'])
df['Fecha'] = df['Fecha'].dt.date

# Fecha mínima y máxima para limitar selección
date_min = df['Fecha'].min()
date_max = df['Fecha'].max()

# Widgets para seleccionar fechas
col1, col2 = st.columns(2)
with col1:
    desde = st.date_input("Desde", value=date_min, min_value=date_min, max_value=date_max)
with col2:
    hasta = st.date_input("Hasta", value=date_max, min_value=date_min, max_value=date_max)

if desde > hasta:
    st.warning("La fecha 'Desde' debe ser anterior o igual a la fecha 'Hasta'.")
    st.stop()

# Filtrado y cálculos
anteriores = df[df['Fecha'] < desde]
entre_fechas = df[(df['Fecha'] >= desde) & (df['Fecha'] <= hasta)].copy()

suma_debe = anteriores['Debe'].sum()
suma_haber = anteriores['Haber'].sum()
inicial = suma_debe - suma_haber

resumen = pd.DataFrame([{
    "Acumulado Debe Previo": suma_debe,
    "Acumulado Haber Previo": suma_haber
}])

# Calcular columna acumulada
entre_fechas["Acumulado"] = entre_fechas.apply(
    lambda row: row["Debe"] - row["Haber"], axis=1
).cumsum() + inicial

# Insertar columna después de "Haber"
haber_index = entre_fechas.columns.get_loc("Haber")
cols = list(entre_fechas.columns)
cols.insert(haber_index + 1, cols.pop(cols.index("Acumulado")))
entre_fechas = entre_fechas[cols]

# Combinar resultados
resultado = pd.concat([resumen, entre_fechas], ignore_index=True)

# Mostrar resultados
st.subheader("Vista Previa de Resultados")
st.dataframe(resultado)

# Exportar a Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultado')
    return output.getvalue()

excel_data = to_excel(resultado)
st.download_button(
    label="📥 Descargar Excel",
    data=excel_data,
    file_name="resultado_filtrado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.success("Archivo listo para descarga.")
