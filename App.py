import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Gestión Sintraopo", layout="wide")

# Función para cargar y limpiar datos
@st.cache_data
def load_data(file_path):
    try:
        # Cargamos el CSV. Nota: Se asume que el separador es la coma.
        df = pd.read_csv(file_path)
        
        # Limpieza de columna de cuotas (Quitar '$' y ',' para operar numéricamente)
        if 'SUMA_CUOTAS' in df.columns:
            df['SUMA_CUOTAS_NUM'] = df['SUMA_CUOTAS'].replace('[\$,]', '', regex=True).astype(float)
        
        # Asegurar que el estado esté normalizado
        if 'ESTADO_AFILIADO' in df.columns:
            df['ESTADO_AFILIADO'] = df['ESTADO_AFILIADO'].fillna('DESCONOCIDO').str.upper()
            
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return pd.DataFrame()

# Título y Logo (Simulado con texto si no se carga la imagen)
col1, col2 = st.columns([1, 5])
with col1:
    # Intentar cargar logo si existe en el directorio
    try:
        st.image("Logo-Sintraopo.jpeg", width=150)
    except:
        st.write("SINTRAOPO LOGO")
with col2:
    st.title("Sistema de Gestión de Afiliados y Aportes")

# Cargar base de datos
df = load_data("DB_AFILIADOS.csv")

if not df.empty:
    # --- BARRA LATERAL (GESTIÓN) ---
    st.sidebar.header("Panel de Acciones")
    menu = st.sidebar.radio("Ir a:", ["Dashboard", "Gestión de Afiliados", "Reportes por Regional"])

    if menu == "Dashboard":
        st.subheader("Indicadores Clave de Desempeño (KPIs)")
        
        # Métricas principales
        total_afiliados = len(df)
        activos = len(df[df['ESTADO_AFILIADO'] == 'ACTIVO'])
        retirados = len(df[df['ESTADO_AFILIADO'] == 'RETIRADO'])
        total_recaudo = df['SUMA_CUOTAS_NUM'].sum() if 'SUMA_CUOTAS_NUM' in df.columns else 0

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total Afiliados", total_afiliados)
        kpi2.metric("Activos", activos, f"{(activos/total_afiliados)*100:.1f}%")
        kpi3.metric("Retirados", retirados)
        kpi4.metric("Recaudo Total", f"${total_recaudo:,.2f}")

        # Gráficos del Dashboard
        st.divider()
        g1, g2 = st.columns(2)
        
        with g1:
            st.write("### Afiliados por Regional")
            fig_reg = px.bar(df['REGIONAL'].value_counts().reset_index(), 
                             x='REGIONAL', y='count', 
                             labels={'count': 'Cantidad', 'REGIONAL': 'Regional'},
                             color='REGIONAL', template="plotly_white")
            st.plotly_chart(fig_reg, use_container_width=True)
            
        with g2:
            st.write("### Distribución por Estado")
            fig_pie = px.pie(df, names='ESTADO_AFILIADO', hole=0.4,
                             color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie, use_container_width=True)

    elif menu == "Gestión de Afiliados":
        st.subheader("Registrar / Actualizar Afiliado")
        
        with st.expander("Añadir Nuevo Miembro"):
            with st.form("new_member"):
                cedula = st.text_input("Cédula")
                nombre = st.text_input("Apellidos / Nombres")
                regional = st.selectbox("Regional", df['REGIONAL'].unique())
                estado = st.selectbox("Estado", ["ACTIVO", "RETIRADO"])
                cuota = st.number_input("Valor Cuota", min_value=0.0)
                submit = st.form_submit_button("Guardar Registro")
                if submit:
                    st.success(f"Afiliado {nombre} registrado correctamente (Simulado).")
        
        st.write("### Lista General de Afiliados")
        # Filtro rápido
        search = st.text_input("Buscar por nombre o cédula")
        filtered_df = df[df['APELLIDOS / NOMBRES'].str.contains(search, case=False, na=False) | 
                         df['CEDULA'].astype(str).str.contains(search, na=False)]
        st.dataframe(filtered_df, use_container_width=True)

    elif menu == "Reportes por Regional":
        st.subheader("Análisis Detallado por Regional")
        
        # Tabla resumen por regional
        resumen_regional = df.groupby('REGIONAL').agg(
            Afiliados=('CEDULA', 'count'),
            Activos=('ESTADO_AFILIADO', lambda x: (x == 'ACTIVO').sum()),
            Recaudo_Total=('SUMA_CUOTAS_NUM', 'sum')
        ).reset_index()
        
        st.table(resumen_regional)
        
        # Gráfico comparativo de recaudos
        st.write("### Recaudo de Cuotas por Regional")
        fig_recaudo = px.bar(resumen_regional, x='REGIONAL', y='Recaudo_Total',
                             color='Recaudo_Total', text_auto='.2s',
                             title="Comparativa Financiera")
        st.plotly_chart(fig_recaudo, use_container_width=True)

else:
    st.warning("Por favor, asegúrate de que 'DB_AFILIADOS.csv' esté en la misma carpeta que este script.")