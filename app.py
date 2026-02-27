import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# Configuración de la página
st.set_page_config(page_title="Gestión Sindical - Sintraopo", layout="wide")

# --- FUNCIONES DE PROCESAMIENTO ---
def clean_currency(value):
    """Limpia valores de moneda como '$17,509.00' a flotante."""
    if isinstance(value, str):
        value = value.replace('$', '').replace(',', '')
        try:
            return float(value)
        except:
            return 0.0
    return value

def load_data(file):
    """Carga y pre-procesa el DataFrame."""
    df = pd.read_csv(file)
    # Limpiar columnas de dinero
    if 'SUMA_CUOTAS' in df.columns:
        df['SUMA_CUOTAS_NUM'] = df['SUMA_CUOTAS'].apply(clean_currency)
    else:
        df['SUMA_CUOTAS_NUM'] = 0.0
    
    # Asegurar que las columnas existan con nombres estándar si varían
    df['ESTADO_AFILIADO'] = df['ESTADO_AFILIADO'].fillna('DESCONOCIDO')
    df['REGIONAL'] = df['REGIONAL'].fillna('SIN ASIGNAR')
    return df

# --- ESTADO DE LA APLICACIÓN (Simulación de DB) ---
if 'df_afiliados' not in st.session_state:
    try:
        # Intentamos cargar el archivo subido inicialmente
        st.session_state.df_afiliados = load_data('DB_AFILIADOS.csv')
    except:
        # Si no existe, creamos un DF vacío estructurado
        st.session_state.df_afiliados = pd.DataFrame(columns=[
            "CEDULA", "APELLIDOS / NOMBRES", "REGIONAL", "CIUDAD AFILIACION", 
            "ESTADO_AFILIADO", "SUMA_CUOTAS_NUM"
        ])

# --- BARRA LATERAL (Logo y Menú) ---
with st.sidebar:
    # Nota: En un entorno local podrías usar st.image("Logo-Sintraopo.jpeg")
    st.title("SINTRAOPO")
    st.subheader("Menú de Navegación")
    menu = st.radio("Ir a:", ["📊 Dashboard", "👥 Gestión de Afiliados", "📥 Importar/Exportar"])
    
    st.divider()
    st.info("Sistema de gestión administrativa para el sindicato.")

# --- SECCIÓN 1: DASHBOARD ---
if menu == "📊 Dashboard":
    st.header("Resumen General de Afiliados")
    
    df = st.session_state.df_afiliados
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Afiliados", len(df))
    with col2:
        activos = len(df[df['ESTADO_AFILIADO'].str.upper() == 'ACTIVO'])
        st.metric("Activos", activos)
    with col3:
        retirados = len(df[df['ESTADO_AFILIADO'].str.upper() == 'RETIRADO'])
        st.metric("Retirados", retirados)
    with col4:
        total_recaudo = df['SUMA_CUOTAS_NUM'].sum()
        st.metric("Recaudo Total", f"${total_recaudo:,.2f}")

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Afiliados por Regional")
        regional_counts = df['REGIONAL'].value_counts().reset_index()
        regional_counts.columns = ['Regional', 'Cantidad']
        fig_bar = px.bar(regional_counts, x='Regional', y='Cantidad', 
                         color='Regional', text_auto=True,
                         template="plotly_white")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.subheader("Recaudo por Regional")
        recaudo_reg = df.groupby('REGIONAL')['SUMA_CUOTAS_NUM'].sum().reset_index()
        fig_pie = px.pie(recaudo_reg, values='SUMA_CUOTAS_NUM', names='REGIONAL', 
                         hole=0.4, title="Distribución de Aportes")
        st.plotly_chart(fig_pie, use_container_width=True)

# --- SECCIÓN 2: GESTIÓN DE AFILIADOS ---
elif menu == "👥 Gestión de Afiliados":
    st.header("Administración de Registros")
    
    # Formulario para nuevo afiliado
    with st.expander("➕ Registrar Nuevo Afiliado"):
        with st.form("nuevo_afiliado"):
            c1, c2 = st.columns(2)
            cedula = c1.text_input("Cédula (ID)")
            nombre = c2.text_input("Nombre Completo")
            reg = c1.selectbox("Regional", ["CENTRO A", "EJE CAFETERO", "NOROCCIDENTE", "SUR", "ORIENTE"])
            estado = c2.selectbox("Estado Inicial", ["ACTIVO", "RETIRADO"])
            cuota = c1.number_input("Valor Cuota", min_value=0.0, step=100.0)
            
            submit = st.form_submit_button("Guardar Afiliado")
            if submit:
                new_row = {
                    "CEDULA": cedula, "APELLIDOS / NOMBRES": nombre, 
                    "REGIONAL": reg, "ESTADO_AFILIADO": estado, 
                    "SUMA_CUOTAS_NUM": cuota, "SUMA_CUOTAS": f"${cuota:,.2f}"
                }
                st.session_state.df_afiliados = pd.concat([st.session_state.df_afiliados, pd.DataFrame([new_row])], ignore_index=True)
                st.success("Afiliado registrado con éxito")
                st.rerun()

    st.subheader("Base de Datos Actual")
    # Buscador
    search = st.text_input("🔍 Buscar por Nombre o Cédula")
    df_display = st.session_state.df_afiliados
    if search:
        df_display = df_display[
            df_display['APELLIDOS / NOMBRES'].str.contains(search, case=False, na=False) |
            df_display['CEDULA'].astype(str).str.contains(search)
        ]
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)

# --- SECCIÓN 3: IMPORTAR / EXPORTAR ---
elif menu == "📥 Importar/Exportar":
    st.header("Gestión de Archivos CSV")
    
    col_up, col_down = st.columns(2)
    
    with col_up:
        st.subheader("Actualización Masiva")
        uploaded_file = st.file_uploader("Subir nuevo archivo .csv", type=["csv"])
        if uploaded_file is not None:
            if st.button("Confirmar Importación"):
                new_data = load_data(uploaded_file)
                st.session_state.df_afiliados = new_data
                st.success(f"Base de datos actualizada con {len(new_data)} registros.")
                st.rerun()

    with col_down:
        st.subheader("Descargar Base de Datos")
        df_to_save = st.session_state.df_afiliados.copy()
        csv_data = df_to_save.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📥 Exportar a CSV",
            data=csv_data,
            file_name="DB_AFILIADOS_ACTUALIZADA.csv",
            mime="text/csv"
        )

    st.divider()
    st.warning("Nota: La actualización masiva reemplazará los datos actuales en pantalla.")