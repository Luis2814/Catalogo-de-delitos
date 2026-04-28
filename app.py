import streamlit as st
import pandas as pd
import plotly.express as px
import re

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS (UI/UX)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Catálogo de Delitos Sexuales contra NNA",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Personalizado para UI sobria y profesional
st.markdown("""
    <style>
    /* Tipografía y colores base */
    .main {
        background-color: #F8F9FA;
    }
    h1, h2, h3 {
        color: #1A365D; /* Azul oscuro corporativo */
    }
    
    /* Estilos para las Tarjetas (Cards) */
    .crime-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        border-left: 5px solid #2B6CB0;
    }
    .crime-title {
        font-size: 1.25rem;
        font-weight: bold;
        color: #2D3748;
        margin-bottom: 0.5rem;
    }
    .tag-state {
        background-color: #E2E8F0;
        color: #4A5568;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 1rem;
    }
    
    /* Sección de Penas (Destacada) */
    .penalty-box {
        background-color: #EBF8FF;
        border: 1px solid #BEE3F8;
        border-radius: 6px;
        padding: 1rem;
        margin: 1rem 0;
        color: #2C5282;
    }
    .penalty-title {
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.85rem;
        letter-spacing: 0.05em;
        margin-bottom: 0.3rem;
    }
    
    /* Ajustes Streamlit Expander */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        color: #2B6CB0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. CARGA Y PROCESAMIENTO DE DATOS
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    try:
        # Cargar el archivo CSV con un nombre simple para evitar errores en la nube
        df = pd.read_csv('datos.csv')
        
        # Limpiar nombres de columnas (quitar espacios en blanco al inicio/final)
        df.columns = df.columns.str.strip()
        
        # Filtrar valores nulos en columnas críticas
        df = df.dropna(subset=['Estado', 'Delito'])
        
        # Limpiar texto de estados y delitos para homogeneizar
        df['Estado'] = df['Estado'].astype(str).str.strip().str.title()
        df['Delito'] = df['Delito'].astype(str).str.strip().str.title()
        df['Rango de edad'] = df['Rango de edad'].astype(str).str.strip()
        
        # Rellenar nulos en campos de texto descriptivo
        cols_to_fill = ['Definición', 'Pena', 'Agravante', 'Excluyente', 'Observaciones', 'Fundamento']
        for col in cols_to_fill:
            if col in df.columns:
                df[col] = df[col].fillna("No especificado")
                
        # Intento de extracción de pena máxima (numérica) para gráficos
        # Busca patrones como "14 años", "a 20 años", etc.
        def extract_max_years(text):
            if text == "No especificado": return 0
            matches = re.findall(r'(\d+)\s*años', str(text).lower())
            if matches:
                return max([int(m) for m in matches])
            return 0
            
        if 'Pena' in df.columns:
            df['Pena Maxima (Años Estimados)'] = df['Pena'].apply(extract_max_years)
            
        return df
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No se encontraron datos o el archivo no existe. Por favor verifica el archivo CSV.")
    st.stop()

# -----------------------------------------------------------------------------
# 3. BARRA LATERAL (SIDEBAR) - FILTROS
# -----------------------------------------------------------------------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/6062/6062646.png", width=80) # Icono genérico de justicia
st.sidebar.title("Filtros de Búsqueda")
st.sidebar.markdown("Utiliza estas opciones para acotar los resultados del catálogo.")

# Buscador por palabra clave
search_term = st.sidebar.text_input("🔍 Buscar palabra clave (ej. grooming, violencia):", "")

# Listas únicas para los selectores
estados_list = sorted(df['Estado'].unique())
delitos_list = sorted(df['Delito'].unique())
edades_list = sorted(df['Rango de edad'].unique())

# Filtros multiselección
selected_estados = st.sidebar.multiselect("📍 Filtrar por Estado:", estados_list)
selected_delitos = st.sidebar.multiselect("⚖️ Filtrar por Tipo de Delito:", delitos_list)
selected_edades = st.sidebar.multiselect("👤 Rango de Edad:", edades_list)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Puedes combinar múltiples filtros para búsquedas específicas.")

# -----------------------------------------------------------------------------
# 4. LÓGICA DE FILTRADO (Buscador Inteligente)
# -----------------------------------------------------------------------------
df_filtered = df.copy()

if search_term:
    # Buscar en casi todas las columnas de texto relevantes
    mask = (
        df_filtered['Delito'].str.contains(search_term, case=False, na=False) |
        df_filtered['Definición'].str.contains(search_term, case=False, na=False) |
        df_filtered['Pena'].str.contains(search_term, case=False, na=False)
    )
    df_filtered = df_filtered[mask]

if selected_estados:
    df_filtered = df_filtered[df_filtered['Estado'].isin(selected_estados)]
if selected_delitos:
    df_filtered = df_filtered[df_filtered['Delito'].isin(selected_delitos)]
if selected_edades:
    df_filtered = df_filtered[df_filtered['Rango de edad'].isin(selected_edades)]

# -----------------------------------------------------------------------------
# 5. TABLERO PRINCIPAL (MAIN DASHBOARD)
# -----------------------------------------------------------------------------
st.title("Catálogo de Delitos Sexuales contra NNA")
st.markdown("Herramienta de consulta interactiva para abogados, legisladores y activistas.")

# Pestañas de navegación principal
tab1, tab2, tab3 = st.tabs(["📋 Catálogo y Buscador", "📊 Análisis Visual", "📖 Glosario Legal"])

with tab1:
    # Métrica de Resumen
    col1, col2, col3 = st.columns(3)
    col1.metric("Delitos Encontrados", len(df_filtered))
    col2.metric("Estados Representados", df_filtered['Estado'].nunique())
    
    # Calcular promedio de años extraídos si es mayor a 0
    df_valid_years = df_filtered[df_filtered['Pena Maxima (Años Estimados)'] > 0]
    avg_years = f"{df_valid_years['Pena Maxima (Años Estimados)'].mean():.1f} años" if not df_valid_years.empty else "N/A"
    col3.metric("Promedio Pena Máxima", avg_years, help="Basado en extracción automática del texto.")
    
    st.markdown("---")
    
    # Vista de Tarjetas Interactivas
    if df_filtered.empty:
        st.info("No se encontraron delitos que coincidan con los filtros seleccionados.")
    else:
        st.markdown(f"### Mostrando {len(df_filtered)} resultados")
        
        for index, row in df_filtered.iterrows():
            # Crear la tarjeta HTML
            card_html = f"""
            <div class="crime-card">
                <div class="crime-title">{row['Delito']}</div>
                <div class="tag-state">{row['Estado']}</div>
                <p><strong>Definición:</strong> {row.get('Definición', 'No disponible')}</p>
                
                <div class="penalty-box">
                    <div class="penalty-title">Pena Establecida</div>
                    {row.get('Pena', 'No disponible')}
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            # Detalles Expandibles
            with st.expander(f"Ver detalles legales adicionales para: {row['Delito']} en {row['Estado']}"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**Agravantes:**")
                    st.write(row.get('Agravante', 'No especificado'))
                    st.markdown("**Atenuantes:**")
                    st.write(row.get('Atenuante', 'No especificado'))
                with col_b:
                    st.markdown("**Excluyentes:**")
                    st.write(row.get('Excluyente', 'No especificado'))
                    st.markdown("**Fundamento Legal:**")
                    st.write(row.get('Fundamento', 'No especificado'))
                    
                if row.get('Observaciones', 'No especificado') != 'No especificado':
                    st.markdown("**Observaciones:**")
                    st.info(row['Observaciones'])
            st.write("") # Espaciador

with tab2:
    st.header("Visualización Comparativa")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Gráfico: Cantidad de delitos por estado
        conteo_estados = df_filtered['Estado'].value_counts().reset_index()
        conteo_estados.columns = ['Estado', 'Cantidad de Delitos']
        fig_estados = px.bar(
            conteo_estados, x='Estado', y='Cantidad de Delitos',
            title="Cantidad de Tipos de Delitos por Estado",
            color='Cantidad de Delitos',
            color_continuous_scale="Blues"
        )
        fig_estados.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_estados, use_container_width=True)
        
    with col_chart2:
        # Gráfico: Distribución por rango de edad
        conteo_edades = df_filtered['Rango de edad'].value_counts().reset_index()
        conteo_edades.columns = ['Rango de Edad', 'Frecuencia']
        fig_edades = px.pie(
            conteo_edades, names='Rango de Edad', values='Frecuencia',
            title="Distribución por Rango de Edad de la Víctima",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        st.plotly_chart(fig_edades, use_container_width=True)
        
    st.markdown("---")
    st.subheader("Análisis de Penas Máximas (Estimación)")
    st.markdown("Este gráfico muestra la estimación de los años máximos de prisión extraídos automáticamente del texto legal. *Nota: Puede no reflejar la pena real debido a la complejidad de la redacción jurídica.*")
    
    if not df_valid_years.empty:
        fig_penas = px.box(
            df_valid_years, x='Estado', y='Pena Maxima (Años Estimados)',
            points="all", hover_data=["Delito"],
            title="Dispersión de Penas Máximas Estimadas por Estado"
        )
        fig_penas.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_penas, use_container_width=True)
    else:
        st.info("No hay datos numéricos suficientes en la columna de Penas para generar este gráfico con los filtros actuales.")

with tab3:
    st.header("Glosario de Términos Legales")
    st.markdown("Para facilitar el uso del catálogo, aquí se explican algunos términos comunes:")
    
    glosario = {
        "NNA": "Acrónimo que significa Niñas, Niños y Adolescentes.",
        "Agravante": "Circunstancia que aumenta la responsabilidad penal y, por tanto, la pena. Por ejemplo: uso de violencia, parentesco, etc.",
        "Atenuante": "Circunstancia que disminuye la responsabilidad penal y puede reducir la pena impuesta.",
        "Excluyente (de responsabilidad)": "Circunstancia que elimina la culpa o la responsabilidad penal del individuo que cometió el acto.",
        "Grooming": "Práctica de un adulto de ganarse la confianza de un menor de edad a través de internet con el fin de abusar de él/ella sexualmente.",
        "Fundamento Legal": "Artículo o sección del Código Penal u otra ley donde se tipifica y sanciona el delito."
    }
    
    for termino, definicion in glosario.items():
        st.markdown(f"**{termino}:** {definicion}")

# -----------------------------------------------------------------------------
# 6. FUNCIONES EXTRA: EXPORTACIÓN DE DATOS
# -----------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("📥 Exportar Resultados")
st.sidebar.markdown("Descarga los datos filtrados para tus reportes.")

@st.cache_data
def convert_df(df):
    # Función para convertir dataframe a CSV y permitir descarga
    return df.to_csv(index=False).encode('utf-8')

csv = convert_df(df_filtered)

st.sidebar.download_button(
    label="Descargar Reporte (CSV)",
    data=csv,
    file_name='reporte_delitos_nna.csv',
    mime='text/csv',
)
