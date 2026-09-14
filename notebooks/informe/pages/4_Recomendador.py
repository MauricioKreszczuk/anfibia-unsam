import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path

st.set_page_config(page_title="Recomendador", layout="wide")

# ==========================================
# RUTAS
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "streamlit"

# ==========================================
# CARGA DE DATOS CACHEADA
# ==========================================
@st.cache_data
def load_data():
    df_rec = pd.read_csv(DATA_DIR / "df_recomendador_base.csv")
    df_rec["post_date"] = pd.to_datetime(df_rec["post_date"], errors="coerce")
    matriz_dist = np.load(DATA_DIR / "doc_topic_dist.npy")
    return df_rec, matriz_dist

df_rec, matriz_dist = load_data()

# ==========================================
# VISTA Y LÓGICA
# ==========================================
st.subheader("Motor de Recomendación")

opciones_articulos = df_rec["doc_id"].astype(str) + " - " + df_rec["title_text"]
articulo_sel = st.selectbox("Buscar artículo por ID o Título:", opciones_articulos)
target_id = int(articulo_sel.split(" - ")[0])

def graficar_constelacion(target_id, recomendados_ids, df_completo, col_x, col_y, titulo):
    df_resto = df_completo[~df_completo["doc_id"].isin([target_id] + recomendados_ids)]
    df_rec_local = df_completo.loc[df_completo["doc_id"].isin(recomendados_ids)].copy()
    df_target = df_completo[df_completo["doc_id"] == target_id]
    
    fig = px.scatter(
        df_resto, 
        x=col_x, 
        y=col_y, 
        color='topic_label', 
        color_discrete_sequence=px.colors.qualitative.Alphabet, 
        custom_data=['topic_label', 'title_text', 'tagline']
    )
    fig.update_traces(
        marker=dict(size=6, opacity=0.3), 
        hovertemplate="<b>%{customdata[0]}</b><br><b>%{customdata[1]}</b><br><i>%{customdata[2]}</i><extra></extra>"
    )
    
    fig.add_trace(go.Scatter(
        x=df_rec_local[col_x], 
        y=df_rec_local[col_y], 
        mode="markers", 
        name="Recomendados", 
        marker=dict(symbol="circle", size=14, line=dict(width=2, color="#1f77b4")), 
        customdata=df_rec_local[["title_text", "topic_label", "tagline"]], 
        hovertemplate="<b>Recomendación</b><br><b>Tópico:</b> %{customdata[1]}<br><b>%{customdata[0]}</b><br><i>%{customdata[2]}</i><extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=df_target[col_x], 
        y=df_target[col_y], 
        mode="markers", 
        name="Original", 
        marker=dict(color="#d62728", size=18, symbol="diamond", line=dict(width=2, color="black")), 
        customdata=df_target[["title_text", "topic_label", "tagline"]], 
        hovertemplate="<b>ORIGINAL</b><br><b>Tópico:</b> %{customdata[1]}<br><b>%{customdata[0]}</b><br><i>%{customdata[2]}</i><extra></extra>"
    ))
    
    fig.update_layout(title=f"<b>{titulo}</b>", height=700, xaxis=dict(showticklabels=False), yaxis=dict(showticklabels=False))
    return fig
    
def graficar_temporal(target_id, similitudes_array, top_n=100):
    df_temp = df_rec.copy()
    df_temp["Similitud"] = similitudes_array
    
    df_origen = df_temp[df_temp["doc_id"] == target_id]
    df_recs = df_temp[df_temp["doc_id"] != target_id].sort_values("Similitud", ascending=False).head(top_n).copy()
    df_recs["Rank"] = range(1, top_n + 1)
    
    df_top10 = df_recs[df_recs["Rank"] <= 10]
    df_resto = df_recs[df_recs["Rank"] > 10]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_resto["post_date"], 
        y=df_resto["Similitud"], 
        mode="markers", 
        name="Rank 11-100", 
        marker=dict(color="#ab63fa", size=10, opacity=0.4), 
        customdata=df_resto[["title_text", "Rank", "topic_label"]], 
        hovertemplate="<b>Rank #%{customdata[1]}</b><br>%{customdata[0]}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=df_top10["post_date"], 
        y=df_top10["Similitud"], 
        mode="markers", 
        name="Top 10", 
        marker=dict(symbol="circle", color="#FFD700", size=16, line=dict(width=1, color="black")), 
        customdata=df_top10[["title_text", "Rank", "topic_label"]], 
        hovertemplate="<b>Rank #%{customdata[1]}</b><br>%{customdata[0]}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=df_origen["post_date"], 
        y=df_origen["Similitud"], 
        mode="markers", 
        name="Original", 
        marker=dict(symbol="diamond", color="#d62728", size=18, line=dict(width=2, color="black")), 
        customdata=df_origen[["title_text", "topic_label"]], 
        hovertemplate="<b>ORIGINAL</b><br>%{customdata[0]}<extra></extra>"
    ))
    
    fig.update_layout(title="Distribución Temporal de Similitud", height=500)
    return fig

if target_id is not None:
    target_idx = df_rec[df_rec["doc_id"] == target_id].index[0]
    target_vector = matriz_dist[target_idx].reshape(1, -1)
    sims = cosine_similarity(target_vector, matriz_dist).flatten()
    
    indices_top = sims.argsort()[::-1][:11]
    indices_top = [i for i in indices_top if i != target_idx][:10]
    recs_ids = df_rec.iloc[indices_top]["doc_id"].tolist()
    
    st.write("### Top 10 Recomendaciones")
    df_mostrar = df_rec.iloc[indices_top][["doc_id", "title_text", "topic_label", "post_date"]].copy()
    df_mostrar["Similitud"] = sims[indices_top].round(4)
    st.dataframe(df_mostrar, use_container_width=True)
    
    st.plotly_chart(graficar_constelacion(target_id, recs_ids, df_rec, "umap_sem_x", "umap_sem_y", "Constelación Semántica"), use_container_width=True)
    st.plotly_chart(graficar_constelacion(target_id, recs_ids, df_rec, "umap_tem_x", "umap_tem_y", "Constelación Temática"), use_container_width=True)
    st.plotly_chart(graficar_temporal(target_id, sims), use_container_width=True)