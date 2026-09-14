import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import math

st.set_page_config(page_title="Etiquetas", layout="wide")

## ==========================================
## RUTAS Y CONFIGURACIÓN BASE
## ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "streamlit"
GRAFICOS_DIR = DATA_DIR / "graficos"

## ==========================================
## CARGA DE DATOS CACHEADA
## ==========================================
@st.cache_data
def load_data():
    tags_global = pd.read_csv(DATA_DIR / "tag_counts_global.csv")
    df_tags_cat = pd.read_csv(DATA_DIR / "df_tags_vs_categorias_base.csv")
    df_tags_top = pd.read_parquet(DATA_DIR / "df_tags_vs_topicos_base.parquet")
    tags_solapamiento = pd.read_csv(DATA_DIR / "tags_solapamiento_prob_topicos.csv")
    tags_auto = pd.read_csv(DATA_DIR / "tags_fusiones_automaticas.csv")
    tags_manual = pd.read_csv(DATA_DIR / "tags_revision_manual.csv")
    return tags_global, df_tags_cat, df_tags_top, tags_solapamiento, tags_auto, tags_manual

(tags_global, df_tags_cat, df_tags_top, tags_solapamiento, tags_auto, tags_manual) = load_data()

def cargar_html(ruta, height=750):
    if ruta.exists():
        with open(ruta, "r", encoding="utf-8") as f:
            components.html(f.read(), height=height, scrolling=True)
    else:
        st.warning(f"Falta el gráfico: {ruta.name}")

## ==========================================
## ENCABEZADO PRINCIPAL
## ==========================================
st.title("Diagnóstico y Auditoría de Etiquetas")
st.markdown("""
Esta sección examina la cobertura de las etiquetas, su coherencia frente a las categorías y los tópicos descubiertos, junto con propuestas de consolidación.
""")

st.divider()

## ==========================================
## SECCIÓN 1: RANKING GLOBAL Y COBERTURA TEMPORAL
## ==========================================
st.subheader("1. Etiquetas por su frecuencia.")
st.write("""
Mostramos las etiquetas con mayor recurrencia histórica en los artículos.
""")

top_n_tags = st.slider("Cantidad de etiquetas a mostrar:", 5, 100, 15)

df_tags_display = (
    tags_global.head(top_n_tags)
    .copy()
    .rename(columns={
        tags_global.columns[0]: "Etiqueta",
        tags_global.columns[1]: "Frecuencia"
    })
)

st.dataframe(df_tags_display[["Etiqueta", "Frecuencia"]], use_container_width=True, hide_index=True)

st.markdown("#### Cobertura de las Etiquetas")
st.write("Proporción de articulos que cuentan con al menos una etiqueta frente a las que no.")
cargar_html(GRAFICOS_DIR / "07_pie_cobertura.html", height=450)

st.markdown("#### Evolución del Etiquetado en el tiempo")
st.write("Muestra el volumen anual de los articulos con y sin etiquetas, indicando el porcentaje de cobertura año por año.")
cargar_html(GRAFICOS_DIR / "07_evolucion_etiquetado.html", height=520)  

st.divider()

## ==========================================
## SECCIÓN 2: ETIQUETAS Y CATEGORÍAS EDITORIALES
## ==========================================
st.subheader("2. Etiquetas vs. Categorías")

st.markdown("#### Distribución de Etiquetas por Categoria")
st.write("""
Volumen de etiquetas únicas asignadas dentro de cada categoría.
""")
cargar_html(GRAFICOS_DIR / "07_distribucion_etiquetas_por_categoria.html", height=450)

st.markdown("#### Etiquetas vs. Categorías (Heatmap)")
st.write("""
Muestra la distribucion de las Top etiquetas frente a las categorias elegidas. Permite distinguir etiquetas transversales de aquellas confinadas a una única categoría.
""")
st.caption("Los valores indican la cantidad de artículos únicos en cada intersección.")

cats_disp = df_tags_cat["categoria_normalizada"].unique()
cats_sel = st.multiselect("Categorías a mostrar:", cats_disp, default=cats_disp)
top_tags_hm = st.slider("Top etiquetas a cruzar (Categorías):", 5, 50, 15)

if cats_sel:
    top_tags_list = df_tags_cat.groupby("tag")["ID"].nunique().nlargest(top_tags_hm).index
    df_hm = df_tags_cat[(df_tags_cat["tag"].isin(top_tags_list)) & (df_tags_cat["categoria_normalizada"].isin(cats_sel))]
    
    if not df_hm.empty:
        matriz = pd.crosstab(df_hm["tag"], df_hm["categoria_normalizada"])
        fig_hm = px.imshow(matriz, text_auto=True, aspect="auto", color_continuous_scale="Blues")
        st.plotly_chart(fig_hm, use_container_width=True)

st.markdown("#### Distribución de etiquetas en categorias en el tiempo")
st.write("""
Muestra la proporción de las etiquetas predominantes dentro de cada categoría, con opción de segmentar por año específico.
""")

anio_sel = st.selectbox(
    "Período a visualizar:",
    ["Global"] + sorted([str(int(a)) for a in df_tags_cat["post_year"].dropna().unique()])
)
top_dona = st.slider("Cantidad de etiquetas por gráfico:", 3, 15, 7)

if anio_sel == "Global":
    datos_dona = df_tags_cat.groupby(["categoria_normalizada", "tag"]).size()
else:
    datos_dona = df_tags_cat[df_tags_cat["post_year"] == int(anio_sel)].groupby(["categoria_normalizada", "tag"]).size()

cats_unicas = df_tags_cat["categoria_normalizada"].unique()
n_cols = 3
n_rows = math.ceil(len(cats_unicas) / n_cols)

def wrap_label(txt, max_len=14):
    if len(txt) > max_len and " " in txt:
        partes = txt.split(" ")
        medio = len(partes) // 2
        return " ".join(partes[:medio]) + "<br>" + " ".join(partes[medio:])
    return txt

fig_donas = make_subplots(
    rows=n_rows,
    cols=n_cols,
    specs=[[{"type": "domain"}] * n_cols for _ in range(n_rows)],
    subplot_titles=[f"<b>{c}</b>" for c in cats_unicas],
    vertical_spacing=0.14,
    horizontal_spacing=0.08
)

paleta_colores = px.colors.qualitative.Prism

for idx, cat in enumerate(cats_unicas):
    r, c = (idx // n_cols) + 1, (idx % n_cols) + 1
    serie = datos_dona.get(cat)
    top = serie.nlargest(top_dona) if serie is not None else pd.Series(dtype=int)
    
    if not top.empty:
        labels_raw = top.index.tolist()
        labels_plot = [wrap_label(str(l)) for l in labels_raw]
        values = top.values.tolist()
        colores = paleta_colores[:len(labels_plot)]
        
        fig_donas.add_trace(
            go.Pie(
                labels=labels_plot,
                customdata=labels_raw,
                values=values,
                hole=0.60,
                marker=dict(colors=colores, line=dict(color="#ffffff", width=2)),
                textposition="outside",
                textinfo="label+percent",
                textfont=dict(size=10),
                hovertemplate="<b>%{customdata}</b><br>Notas: %{value} (%{percent})<extra></extra>",
                showlegend=False
            ),
            row=r,
            col=c
        )
    else:
        fig_donas.add_trace(
            go.Pie(
                labels=["Sin datos"],
                values=[1],
                hole=0.60,
                marker=dict(colors=["#f3f4f6"]),
                textinfo="none",
                hoverinfo="none",
                showlegend=False
            ),
            row=r,
            col=c
        )

fig_donas.update_layout(
    height=430 * n_rows,
    margin=dict(t=50, b=40, l=30, r=30),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(fig_donas, use_container_width=True)

st.divider()

## ==========================================
## SECCIÓN 3: ETIQUETAS Y TÓPICOS MODELADOS
## ==========================================
st.subheader("3. Etiquetas vs. Tópicos")
st.write("""
Cruce entre las etiquetas  y los Tópicos identificados por el modelo.
""")
st.caption("Celdas con valores altos marcan concordancia entre la etiqueta y el tópico; dispersiones horizontales evidencian etiquetas transversales.")

top_tags_t = st.slider("Top etiquetas (Tópicos):", 5, 100, 30)
top_tops_t = st.slider("Top tópicos:", 5, 50, 10)

tt_tags = df_tags_top.groupby("tag")["doc_id"].nunique().nlargest(top_tags_t).index
tt_tops = df_tags_top.groupby("topic_name")["doc_id"].nunique().nlargest(top_tops_t).index

df_hm_t = df_tags_top[(df_tags_top["tag"].isin(tt_tags)) & (df_tags_top["topic_name"].isin(tt_tops))]
if not df_hm_t.empty:
    matriz_t = pd.crosstab(df_hm_t["tag"], df_hm_t["topic_name"])
    fig_hm_t = px.imshow(matriz_t, text_auto=True, aspect="auto", color_continuous_scale="Blues")
    st.plotly_chart(fig_hm_t, use_container_width=True)

st.divider()
## ==========================================
## SECCIÓN 4: Propuestas
## ==========================================
st.subheader("4. Propuestas de Consolidación y Normalización")
st.write("""
Detección de redundancias y variaciones morfológicas para estandarizar el vocabulario de etiquetas.
""")

st.markdown("##### Etiquetas por similitud Semántica")
st.caption("Pares de etiquetas con distribución temática similar según el modelo.")
df_solap_display = tags_solapamiento.rename(columns={
    "Tag A": "Etiqueta A",
    "Tag B": "Etiqueta B",
    "Similitud_Coseno_Prob_Topicos": "Similitud Temática"
})

with st.expander("Metodología: Detección del solapamiento"):
    st.markdown("""
    * Cada nota tiene un vector de probabilidades continuas sobre todos los tópicos del modelo. Al promediar los vectores de todas las notas asignadas a una etiqueta, se obtiene su perfil temático medio.
    * **Similitud Coseno:** Se evalúa qué tan paralelos son los perfiles de dos términos en el espacio multidimensional de tópicos.
    * **Criterio de corte:** Se muestran pares con una correlación $\ge 0.85$. Una similitud alta indica que ambas etiquetas se aplican sobre artículos con el mismo núcleo conceptual, sugiriendo redundancia temática o términos sinónimos en la redacción.
    """)
st.dataframe(df_solap_display, use_container_width=True, hide_index=True)

st.markdown("##### Fusiones Recomendadas")
st.caption("Casos directos de lematización, tildes, mayúsculas o variantes de número (singular/plural).")

df_auto_display = tags_auto.rename(columns={
    "Tag Variante": "Variante Detectada",
    "Frecuencia Variante": "Uso Variante",
    "Tag Canónico": "Etiqueta Sugerida (Canónica)",
    "Frecuencia Canónico": "Uso Sugerida",
    "Similitud Léxica": "Similitud Léxica",
    "Es Diacrítico": "Es Tilde/Acento",
    "Mismo Lema": "Mismo Lema (Singular/Plural)"
})
st.dataframe(df_auto_display, use_container_width=True, hide_index=True)

with st.expander("Metodología: ¿Cómo se determinan las fusiones y sus columnas?"):
    st.markdown("""
    * **Criterio de prevalencia:** Para decidir cuál queda como forma canónica se aplican tres reglas sucesivas:
        1. *Limpieza de sintaxis:* Las versiones sin numeral (`#`) desplazan a las que llevan hashtag (`#Eaaf` $\\rightarrow$ `Eaaf`).
        2. *Prevalencia ortográfica:* La forma acentuada válida desplaza a la que no tiene tilde (`México` $\\rightarrow$ `Mexico`).
        3. *Frecuencia histórica:* En el resto de los casos, la forma con mayor volumen de notas absorbe a la minoritaria.
    * **Es Tilde/Acento (`Es Diacrítico`):** Indica si ambas cadenas son idénticas al remover los acentos ortográficos vía Unicode `NFKD`.
    * **Mismo Lema (Singular/Plural):** Validación lingüística con **spaCy** que comprueba si comparten raíz morfológica (ej. `Cuerpo` y `Cuerpos`).
    * **Similitud Léxica:** Coeficiente de 0 a 1 (*Gestalt Pattern Matching*) que mide el parecido superficial de caracteres entre las cadenas.
    * **Capa de seguridad semántica:** Para habilitar la fusión automática, el par debe tener equivalencia gramatical indiscutible o superar un umbral de coincidencia léxica $\\ge 0.93$ respaldado por embeddings ($\ge 0.85$), evitando falsos positivos como `Periodismo` / `Peronismo`.
    """)

st.markdown("##### Casos para Revisión Editorial")
st.caption("Términos próximos conceptualmente donde la unificación requiere definir un criterio de redacción.")

df_manual_display = tags_manual.rename(columns={
    "Tag Variante": "Etiqueta A",
    "Frecuencia Variante": "Uso A",
    "Tag Canónico": "Etiqueta B",
    "Frecuencia Canónico": "Uso B",
    "Similitud Léxica": "Similitud Léxica",
    "Similitud Semántica": "Similitud Semántica",
    "Es Diacrítico": "Es Tilde/Acento",
    "Mismo Lema": "Mismo Lema"
})
st.dataframe(df_manual_display, use_container_width=True, hide_index=True)

with st.expander("Criterio editorial: ¿Por qué estos casos requieren supervisión humana?"):
    st.markdown("""
    * **Discrepancia léxica vs. conceptual:** Son términos que superaron el umbral de escritura similar y comparten contexto en embeddings (`paraphrase-multilingual-MiniLM-L12-v2`, $\\ge 0.70$), pero no son equivalencias gramaticales exactas (no son meras tildes ni plurales).
    * **Similitud Semántica:** Mide la cercanía angular entre los vectores densos de ambas palabras. Permite evaluar si dos términos refieren al mismo concepto de fondo o a campos afines.
    * **Decisión de la redacción:** Se listan aquí porque presentan relaciones de **sinonimia parcial** o **jerarquía** (un término específico vs. uno amplio). La decisión de unificarlos bajo un único tag canónico o preservarlos como categorías independientes depende de la política editorial del medio.
    """)