import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px       
import plotly.graph_objects as go 
from pathlib import Path

st.set_page_config(page_title="Modelado de Tópicos - Revista Anfibia", layout="wide")

# ==========================================
# RUTAS
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "streamlit"
GRAFICOS_DIR = DATA_DIR / "graficos"

# ==========================================
# CARGA DE DATOS CACHEADA
# ==========================================
@st.cache_data
def load_data():
    topicos_info = pd.read_csv(DATA_DIR / "topicos_info.csv")
    
    df_timeline = pd.read_csv(DATA_DIR / "timeline_topicos.csv")
    df_timeline["Fecha"] = pd.to_datetime(df_timeline["Fecha"])
    
    df_mapa = pd.read_csv(DATA_DIR / "mapa_topicos.csv") 
    
    return topicos_info, df_timeline, df_mapa

topicos_info, df_timeline, df_mapa = load_data()

topicos_disponibles = df_timeline[["Topic", "clean_name"]].drop_duplicates().sort_values("Topic")
mapeo_nombres = dict(zip(topicos_disponibles["Topic"], topicos_disponibles["clean_name"]))
TODOS_LOS_TOPICOS = topicos_disponibles["Topic"].tolist()

# --- MAPA DE COLORES GLOBAL Y FIJO ---
paleta_global = px.colors.qualitative.Alphabet
MAPA_COLORES_GLOBAL = {t_id: paleta_global[i % len(paleta_global)] for i, t_id in enumerate(sorted(TODOS_LOS_TOPICOS))}

def cargar_html(ruta, height=750):
    if ruta.exists():
        with open(ruta, "r", encoding="utf-8") as f:
            components.html(f.read(), height=height, scrolling=True)
    else:
        st.warning(f"Falta el gráfico interactivo: `{ruta.name}`. Verificá su exportación desde el notebook 06.5.")

# ==========================================
# ENCABEZADO Y EXPLICACIÓN METODOLÓGICA
# ==========================================
st.title("2. Modelado de Tópicos")

st.markdown("""
Consiste en el agrupamiento automático de los artículos según la similitud de su contenido.  

El algoritmo que utilizamos (BERTopic) lee los textos de los articulos y los reúne según su parecido temático. Luego, a cada grupo le asigna las palabras clave que mejor resumen de qué se habló en esas publicaciones.
""")
with st.expander("Detalles del modelo", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**1. Clustering y Embeddings Naturales**")
        st.write("""
        • **Generación de Embeddings:** Se procesan los cuerpos de los articulos con `paraphrase-multilingual-MiniLM-L12-v2`, generando la representación vectorial de cada articulo, que se utilizara para decidir el agrupamiento (Clustering).
        
        • **Tratamiento de outliers (-1):** Más de 1600 articulos quedaban bajo el Tópico -1 (reservado para aquellas que el modelo no supo agrupar con las demas). Se reasignaron a su tópico más cercano calculando similitud coseno contra los centroides vectoriales de cada Tópico.
        """)
    with c2:
        st.markdown("**2. Descriptores**")
        st.write("""
        • **Palabras Clave:** Se extraen sobre el texto unificado, saltando las palabras redundantes.
        """)

    st.caption("""
    Recordatorio: 
    
    Texto unificado: Título + Copete + Tagline + Cuerpo
    """)

st.divider()

# ==========================================
# SECCIÓN 1: TABLA CENTRALIZADA DE TÓPICOS
# ==========================================
st.subheader("1. Tópicos Encontrados")
st.write("Estos son los tópicos resultantes del modelo y sus características principales.")

# Ajuste visual de columnas para legibilidad
column_config = {
    "Topic": st.column_config.NumberColumn("ID Tópico", format="%d"),
    "Name": st.column_config.TextColumn("Palabras Clave"),
    "Docs": st.column_config.NumberColumn("Artículos", format="%d"),
    "% Corpus": st.column_config.NumberColumn("% Artículos", format="%.2f %%"),
    "Articulos_Representativos": st.column_config.TextColumn("Artículo Representativo"),
    "Tagline_Representativo": st.column_config.TextColumn("Tagline"),
    "URL_Articulo": st.column_config.LinkColumn(
        "Enlace",
        display_text="Ver nota ↗"
    )
}

columnas_visibles = [
    "Topic", 
    "Name", 
    "Docs", 
    "% Corpus", 
    "Articulos_Representativos", 
    "Tagline_Representativo",
    "URL_Articulo"
]

df_tabla = topicos_info[[c for c in columnas_visibles if c in topicos_info.columns]]

st.dataframe(
    df_tabla,
    use_container_width=True,
    hide_index=True,
    column_config=column_config
)

st.caption("""
Nota: Se determinaron los artículos clave de cada tópico (junto con su bajada o tagline) calculando el centroide vectorial de cada tema (el "promedio semántico" de todos sus textos) y seleccionando las publicaciones con mayor similitud coseno respecto a ese centro. Representan el núcleo del tema, no necesariamente los artículos más leídos.
""")

st.divider()

# ==========================================
# SECCIÓN 2: PALABRAS CLAVE DE LOS TÓPICOS
# ==========================================
st.subheader("2. Palabras Clave de los Tópicos Principales (Top 16)")
st.write("Observamos el peso de cada palabra clave sobre el tópico y cómo estas definen su identidad.")

cargar_html(GRAFICOS_DIR / "01_barchart_topicos.html", height=850)

# ----------------------------------------------------
# Ficha de consulta para tópicos fuera del Top 16
# ----------------------------------------------------
st.markdown("#### Detalles:")
#st.write("Para explorar temas específicos que no ingresaron en los 16 principales de arriba:")

opciones_topicos = {
    row["Topic"]: f"Tópico {row['Topic']} — {row['Name']}"
    for _, row in topicos_info.iterrows()
    if row["Topic"] != -1
}

topico_sel = st.selectbox(
    "Seleccioná un tópico:",
    options=list(opciones_topicos.keys()),
    format_func=lambda x: opciones_topicos[x],
    label_visibility="collapsed"
)

fila = topicos_info[topicos_info["Topic"] == topico_sel].iloc[0]
palabras = [p.strip() for p in str(fila.get("Name", "")).split(",") if p.strip()]

c1, c2, c3 = st.columns([1, 1, 3])
c1.metric("Volumen", f"{int(fila.get('Docs', 0))} notas")
c2.metric("Volumen (%)", f"{float(fila.get('% Corpus', 0)):.2f} %")
with c3:
    st.caption("Palabras clave del tópico:")
    st.pills("Términos", palabras, selection_mode="multi", disabled=True, label_visibility="collapsed")

# Artículo representativo del tópico seleccionado
art = fila.get("Articulos_Representativos", "")
tag = fila.get("Tagline_Representativo", "")
url = fila.get("URL_Articulo", "")

if pd.notna(art) and str(art).strip():
    st.markdown(f"**Artículo representativo:** {art}")
    if pd.notna(tag) and str(tag).strip() and str(tag).lower() != "nan":
        st.caption(f"_{tag}_")
    if pd.notna(url) and str(url).strip() and str(url).startswith("http"):
        st.link_button("Ver Nota ↗", str(url).strip())

st.divider()

# ==========================================
# SECCIÓN 3: EVOLUCIÓN TEMPORAL Y COYUNTURA
# ==========================================
st.subheader("3. Evolución Temporal de los Tópicos")
st.write("""
Graficamos la frecuencia de cada Tópico según su fecha.
Los marcadores en forma de diamante (◆) señalan el **máximo histórico** de cada tópico.
""")
st.caption("Al pasar el cursor sobre los picos, se muestran los articulos representativos de ese pico.")

st.caption("Podés usar la opción **`Select all`** adentro del menú para ver todos los tópicos a la vez, o tocar la **`x`** a la derecha de la caja para limpiar todos.")

# --- LÓGICA DE SELECCIÓN ---
paleta = px.colors.qualitative.Alphabet
# Asignamos a cada ID de tópico un color fijo de la paleta
mapa_colores_fijo = {t_id: paleta[i % len(paleta)] for i, t_id in enumerate(sorted(TODOS_LOS_TOPICOS))}




# Por defecto mostramos los primeros 3 tópicos
topicos_default = topicos_disponibles["Topic"].head(3).tolist()

topicos_seleccionados = st.multiselect(
    "Seleccioná los tópicos a comparar:",
    options=topicos_disponibles["Topic"].tolist(),
    default=topicos_default,
    format_func=lambda t_id: f"{t_id}: {mapeo_nombres.get(t_id, '')}"
)

# --- CREACIÓN DEL GRÁFICO DINÁMICO ---
if not topicos_seleccionados:
    st.info("Elegí al menos un tópico para visualizar el gráfico.")
else:
    fig = go.Figure()
    colors = px.colors.qualitative.G10

    for idx, t_id in enumerate(topicos_seleccionados):
        c = MAPA_COLORES_GLOBAL[t_id]
        df_t = df_timeline[df_timeline["Topic"] == t_id].sort_values("Fecha")
        clean_name = mapeo_nombres.get(t_id, f"Tópico {t_id}")

        # Traza de la Línea Continua
        fig.add_trace(go.Scatter(
            x=df_t["Fecha"],
            y=df_t["Frecuencia"],
            mode="lines",
            name=clean_name,
            legendgroup=f"g{t_id}",
            line=dict(color=c, width=3),
            customdata=df_t["hover_linea"],
            hovertemplate=(
                f"<b>{clean_name}</b><br>"
                "Fecha: %{x|%Y-%m}<br>"
                "Artículos: %{y}"
                "%{customdata}<extra></extra>"
            )
        ))

        # Traza de los Rombos (Máximos Históricos)
        df_max = df_t[df_t["Es_Maximo"] == True]
        if not df_max.empty:
            fig.add_trace(go.Scatter(
                x=df_max["Fecha"],
                y=df_max["Frecuencia"],
                mode="markers",
                name=f"Máximo - {clean_name}",
                legendgroup=f"g{t_id}",
                showlegend=False,
                marker=dict(size=12, color=c, symbol="diamond", line=dict(width=1.5, color="#111")),
                customdata=df_max["hover_rombo"],
                hovertemplate=(
                    f"<b> Máximo Histórico: {clean_name}</b><br>"
                    "Fecha: %{x|%Y-%m}<br>"
                    "Artículos: %{y}<br>"
                    "<b>Artículos representativos:</b>%{customdata}"
                    "<extra></extra>"
                )
            ))

    # Diseño del Gráfico corregido
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="#fff",
        height=650,
        font=dict(family="Arial, sans-serif", size=14, color="#333"), 
        hovermode="closest",
        hoverlabel=dict(bgcolor="white", font_size=14, font_family="Arial"),
        legend=dict(
            title="<b>Tópicos referenciados</b>", 
            orientation="v", 
            yanchor="top", 
            y=1, 
            xanchor="left", 
            x=1.02 
        ),
        margin=dict(t=20, b=20, r=200) 
    )
    
    # Eje X limpio: 
    fig.update_xaxes(
        showgrid=True, 
        gridcolor="#ebebeb", 
        tickformat="%Y", 
        dtick="M12" 
    )
    fig.update_yaxes(
        showgrid=True, 
        gridcolor="#ebebeb",
        title="Número de Artículos (por período)"
    )

    # CRÍTICO: theme=None apaga la interferencia de Streamlit sobre Plotly
    st.plotly_chart(fig, use_container_width=True, theme=None)

with st.expander("Detalles: Metodológia para calcular los articulos de cada pico"):
    st.markdown("""
    Se aplicó el siguiente criterio:

    * **Ventanas temporales dinámicas (*bins*):** Se segmentaron los articulos en intervalos de tiempo mediante *Dynamic Topic Modeling*, agrupando el volumen de articulos en cada ventana.
    * **Identificación de picos y máximos:** 
        * **Máximo Histórico (◆):** El punto temporal con el volumen absoluto más alto de publicaciones del tópico.
        * **Picos locales:** Momentos donde la cantidad de publicaciones superó al período previo y al posterior.
    * **Artículos representativos:** Para cada período se calcularon los embeddings de los articulos publicados en esa ventana y se obtuvo su **centroide semántico local** (el promedio vectorial del intervalo).
    Mediante similitud coseno contra dicho centroide, se extrajo el *Top 3* de publicaciones más cercanas, buscando explicar que notica ocasiono el pico.
    """)

st.divider()

# ==========================================
# SECCIÓN 4: ESPACIO SEMÁNTICO (UMAP)
# ==========================================
st.subheader("4. Mapa de los artículos (Proyección 2D)")
st.write("""
Proyección bidimensional de los artículos.
Cada punto representa un artículo publicado, su ubicación está dada por el vector representativo de cada artículo (embeddings). Entonces los artículos que sean cercanos serán similares (porque sus representaciones vectoriales lo son).
Los colores corresponden a los tópicos del modelo.
""")
st.caption("Seleccioná un área para hacer zoom y hacé doble clic sobre el gráfico para restablecer la vista. Posá el mouse sobre un artículo para ver su Tópico, nombre y tagline correspondiente.")



# Tip visual para el usuario
st.caption("Podés usar la opción **`Select all`** adentro del menú para ver todos los tópicos a la vez, o tocar la **`x`** a la derecha de la caja para limpiar todos.")

# Multiselect nativo
topicos_seleccionados_mapa = st.multiselect(
    "Seleccioná los tópicos a visualizar en el mapa:",
    options=TODOS_LOS_TOPICOS,
    default=TODOS_LOS_TOPICOS[:], 
    format_func=lambda t_id: f"{t_id}: {mapeo_nombres.get(t_id, '')}",
    placeholder="Buscá o elegí los tópicos..."
)

# --- RENDERIZADO DEL MAPA ---
if not topicos_seleccionados_mapa:
    st.warning("Elegí al menos un tópico para visualizar el mapa.")
else:
    # Filtramos el DataFrame con las coordenadas
    df_plot = df_mapa[df_mapa["topic"].isin(topicos_seleccionados_mapa)].copy()
    
    # Recreamos la etiqueta para asegurarnos de que coincida 100% con los nombres limpios
    df_plot['topic_label'] = df_plot['topic'].apply(lambda t: f"{t}: {mapeo_nombres.get(t, '')}")
    
    # Aseguramos que el orden de la leyenda sea categórico y prolijo
    categorias_validas = [f"{t}: {mapeo_nombres.get(t, '')}" for t in sorted(topicos_seleccionados_mapa)]
    df_plot['topic_label'] = pd.Categorical(df_plot['topic_label'], categories=categorias_validas, ordered=True)
    df_plot = df_plot.sort_values('topic_label')

    todas_las_categorias_posibles = [f"{t}: {mapeo_nombres.get(t, '')}" for t in sorted(TODOS_LOS_TOPICOS)]
    paleta = px.colors.qualitative.Alphabet
    # Asignamos a cada tópico posible un color fijo de la paleta
    mapa_colores_fijo = {cat: paleta[i % len(paleta)] for i, cat in enumerate(todas_las_categorias_posibles)}


    # Creamos la figura con WebGL para máximo rendimiento
    mapa_colores_scatter = {f"{t}: {mapeo_nombres.get(t, '')}": MAPA_COLORES_GLOBAL[t] for t in TODOS_LOS_TOPICOS}

    fig_mapa = px.scatter(
        df_plot, 
        x='x', 
        y='y', 
        color='topic_label', 
        custom_data=['topic_label', 'title', 'tagline'],
        color_discrete_map=mapa_colores_scatter,
        render_mode='webgl'
    )

    # Formato del hover y tamaño de puntos
    fig_mapa.update_traces(
        hovertemplate=(
            "<b>Tópico:</b> %{customdata[0]}<br>"
            "<b>Título:</b> %{customdata[1]}<br>"
            "<i>%{customdata[2]}</i>"
            "<extra></extra>"
        ), 
        marker=dict(size=7, opacity=0.85, line=dict(width=0.5, color='white'))
    )

    # Diseño del gráfico
    fig_mapa.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='#fff', 
        height=700,
        font=dict(family="Arial, sans-serif", size=14, color="#333"),
        hovermode="closest",
        xaxis=dict(showticklabels=False, zeroline=False, showgrid=False, title=""),
        yaxis=dict(showticklabels=False, zeroline=False, showgrid=False, title=""),
        legend=dict(
            title="<b>Tópicos</b>", 
            orientation="v", 
            y=1, 
            x=1.02,
            itemsizing='constant'
        ),
        margin=dict(r=200, t=20, b=20)
    )

    st.plotly_chart(fig_mapa, use_container_width=True, theme=None)


with st.expander("Detalles: Como se construyo el mapa"):
    st.markdown("""
    * **Espacio vectorial original:** Cada articulo se convierte en un vector (embedding), que representara su contexto. Pero, con muchas dimensiones (cientos de variables).
    * **Reducción dimensional (UMAP):** Para poder graficarlo en dos dimensiones, se utiliza el algoritmo **UMAP** (*Uniform Manifold Approximation and Projection*). Reduciendo la dimensinalidad de los vectores a 2, sin perder sus relaciónes.
    """)