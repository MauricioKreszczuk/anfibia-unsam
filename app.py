# PARCHE OBLIGATORIO PARA QUE NO CRASHEE UMAP/NUMBA
import coverage.types as ct
for name, fallback in {
    'Tracer': getattr(ct, 'TTracer', object),
    'TShouldTraceFn': object,
    'TShouldStartContextFn': object,
    'TFileDisposition': object,
}.items():
    if not hasattr(ct, name):
        setattr(ct, name, fallback)

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
from pathlib import Path
from bertopic import BERTopic
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings("ignore")

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Revista Anfibia - Inteligencia Editorial", layout="wide")
st.title("🐸 Revista Anfibia: Análisis Editorial y Recomendador")
st.markdown("Exploración interactiva del archivo histórico usando Inteligencia Artificial.")

# --- FUNCIONES DE CARGA Y CACHÉ ---
# st.cache_data guarda dataframes en memoria.
@st.cache_data
def cargar_datos():
    ruta = Path("data/processed/corpus_anfibia_lematizado.csv")
    if not ruta.exists():
        st.error(f"Falta el corpus en {ruta}.")
        st.stop()
    df = pd.read_csv(ruta)
    df["doc_id"] = df.index
    return df

# st.cache_resource guarda modelos pesados para no recargarlos en cada click.
@st.cache_resource
def cargar_modelo():
    ruta = Path("outputs/bertopic_hibrido/bertopic_hibrido_model")
    if not ruta.exists():
        st.error(f"Falta el modelo en {ruta}. Ejecutá el notebook 06.5 primero.")
        st.stop()
    return BERTopic.load(str(ruta))

# st.cache_data para la matriz pesada, se calcula solo al arrancar la app.
@st.cache_data
def calcular_distribucion(_model, textos):
    # _model tiene guion bajo para que Streamlit no intente hashear el objeto entero
    doc_topic_dist, _ = _model.approximate_distribution(textos, use_embedding_model=False)
    return doc_topic_dist

def cargar_grafico_html(ruta):
    path = Path(ruta)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            html_data = f.read()
        components.html(html_data, height=750, scrolling=True)
    else:
        st.warning(f"Todavía no generaste el gráfico: `{ruta}`.")

# --- CARGA INICIAL DE DATOS ---
with st.spinner('Cargando el corpus, el modelo y calculando distribuciones (esto puede tardar un poco la primera vez)...'):
    df_corpus = cargar_datos()
    modelo = cargar_modelo()
    textos_docs = df_corpus["document_text_final"].fillna("").astype(str).tolist()
    distribucion_topicos = calcular_distribucion(modelo, textos_docs)

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Recomendador de Notas", 
    "🗺️ Mapa Semántico", 
    "📈 Evolución de Temas",
    "🏷️ Auditoría de Etiquetas"
])

# --- TAB 1: RECOMENDADOR ---
with tab1:
    st.header("Motor de Recomendación por Perfil de Tópicos")
    st.markdown("Elegí un artículo. El motor va a calcular la distancia coseno entre la distribución de tópicos de esta nota y todas las demás del archivo para encontrar las 10 más similares.")
    
    # Armamos un diccionario para el selectbox {doc_id: "Título de la nota"}
    notas_dict = dict(zip(df_corpus['doc_id'], df_corpus['title_text']))
    
    # Buscador integrado
    nota_elegida = st.selectbox("Buscá por título:", options=list(notas_dict.keys()), format_func=lambda x: notas_dict[x])
    
    if st.button("Buscar Similares", type="primary"):
        # 1. Extraer vector de distribución temática de la nota elegida
        target_vector = distribucion_topicos[nota_elegida].reshape(1, -1)
        
        # 2. Calcular Similitud Coseno contra todo el corpus
        similitudes = cosine_similarity(target_vector, distribucion_topicos).flatten()
        
        # 3. Ordenar índices de mayor a menor y agarrar el top 10 (excluyendo la misma nota)
        indices_similares = similitudes.argsort()[::-1][:11]
        indices_similares = [idx for idx in indices_similares if idx != nota_elegida][:10]
        
        # 4. Mostrar Resultados
        st.subheader(f"Resultados para: *{notas_dict[nota_elegida]}*")
        
        for rank, idx in enumerate(indices_similares, start=1):
            row = df_corpus.iloc[idx]
            similitud = similitudes[idx]
            
            tagline = str(row.get("tagline", "")).strip()
            if tagline.lower() == "nan" or not tagline:
                tagline = "Sin bajada editorial."
                
            tags = str(row.get("post_tag", "")).strip()
            if tags.lower() == "nan" or not tags:
                tags = "Ninguna"
            
            with st.container():
                st.markdown(f"### #{rank} - {row['title_text']}")
                st.markdown(f"**Similitud:** `{similitud:.4f}` | **Etiquetas:** `{tags}`")
                st.info(f"*{tagline}*")
                st.divider()

# --- TAB 2: MAPA SEMÁNTICO ---
with tab2:
    st.header("El Universo de Anfibia (Embeddings)")
    st.markdown("Cada punto es un artículo. Los que están agrupados comparten núcleo semántico y temática.")
    cargar_grafico_html("outputs/bertopic_hibrido/graficos/03_espacio_documentos.html")

# --- TAB 3: EVOLUCIÓN TEMPORAL ---
with tab3:
    st.header("De qué se habló a lo largo del tiempo")
    cargar_grafico_html("outputs/bertopic_hibrido/graficos/02_evolucion_topicos_completa.html")

# --- TAB 4: ETIQUETAS ---
with tab4:
    st.header("Auditoría y Caos de Etiquetas")
    st.markdown("Diagnóstico de la cantidad de etiquetas únicas inventadas para cada tópico.")
    cargar_grafico_html("outputs/analisis_etiquetas/05_ranking_caos_etiquetas.html")

'''

python -m pip install streamlit


python -m streamlit run app.py  

'''