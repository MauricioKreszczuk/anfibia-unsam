# Diccionario de columnas 

Dataset generado por `src/extract_posteos_anfibia.py` a partir de `revistaanfibia_prod_database_2026-06-17.sql` y enriquecido en el pipeline de modelado.
Solo contiene posts con `post_type = "post"` y `post_status = "publish"` (3.622 filas).

---

## Identidad del post

| Columna | Qué es |
|---|---|
| `ID` | ID numérico interno de WordPress |
| `doc_id` | Índice posicional único en el pipeline de datos (0 a N-1) |
| `source_url` | URL pública reconstruida (`https://www.revistaanfibia.com/slug/`) |
| `guid` | URL original guardada por WordPress (puede ser de staging) |
| `post_name` | El slug de la URL (`la-china-invisible`) |
| `post_status` | Siempre `publish` en este dataset |
| `post_type` | Siempre `post` en este dataset |

---

## Texto editorial

| Columna | Qué es | Útil para topic modelling |
|---|---|---|
| `post_title` | Título original con HTML sin limpiar | No |
| `title_text` | Título limpio (sin HTML) | Sí |
| `post_content` | Cuerpo original con HTML, Gutenberg, shortcodes | No |
| `body_text` | Cuerpo limpio (sin HTML) — el texto principal | Sí |
| `post_excerpt` | Extracto original sin limpiar | No |
| `excerpt_text` | Extracto limpio | Opcional |
| `document_text` | `title_text + ". " + body_text` — texto listo para modelar | Sí |
| `document_text_original` | Texto completo sin procesar (`title_text + ". " + body_text`) | Sí |
| `document_text_final` | Texto lematizado, normalizado y sin stopwords para el modelo | Sí (Input directo) |
| `word_count` | Cantidad de palabras en `document_text` | Sí (para filtrar) |
| `copete` | Subtítulo editorial corto (campo custom de WordPress) | Opcional |
| `tagline` | Bajada o frase de presentación (otro campo custom) | Opcional |

---

## Fechas y tiempo

| Columna | Qué es |
|---|---|
| `post_date` | Fecha y hora de publicación (zona horaria local) |
| `post_date_gmt` | Ídem en UTC |
| `post_modified` | Última modificación |
| `post_modified_gmt` | Ídem en UTC |
| `post_date_calendar` | Solo la fecha (`2023-04-25`) |
| `post_year` | Año como entero |
| `post_month` | Mes como entero |
| `post_year_month` | Año y mes (`2023-04`) |
| `post_quarter` | Trimestre como entero |
| `post_year_quarter` | Año y trimestre (`2023Q2`) |
| `post_weekday` | Día de la semana (`Monday`) |
| `days_to_modified` | Días entre publicación y última edición |

---

## Autoría

| Columna | Qué es | Útil |
|---|---|---|
| `post_author` | ID numérico del usuario WordPress que creó el post | No |
| `autor_ids` | Lista de IDs del tipo de post `autor` (campo custom de Anfibia) | No |
| `autor_id_list` | Ídem como string separado por `;` | No |
| `autor_names` | Nombres resueltos de los autores | Sí |
| `autor_ids_raw` | Valor crudo de `wp_postmeta` antes de parsear | No |
| `autor_ids_field` | Campo ACF asociado al anterior | No |
| `illustrator_ids` | Lista de IDs de ilustradores | No |
| `illustrator_id_list` | Ídem como string separado por `;` | No |
| `illustrator_names` | Nombres resueltos de los ilustradores | Opcional |
| `illustrator_ids_raw` | Valor crudo de `wp_postmeta` | No |
| `illustrator_ids_field` | Campo ACF asociado al anterior | No |

---

## Taxonomías editoriales

| Columna | Qué es | Cobertura |
|---|---|---|
| `category` | Categoría principal (`Política y Economía`, `Culturas`, etc.) | 100% |
| `post_tag` | Tags editoriales (`Feminismos`, `Javier Milei`, etc.) | ~44% (1.592 notas) |
| `text_type` | Género textual (`Ensayo`, `Crónica`) | ~45% |
| `tipo-de-cronica` | Subtipo de crónica | Muy pocos casos |

---

## Taxonomías de display y plugins (no útiles para topic modelling)

| Columna | Qué es |
|---|---|
| `destacado` | Posición editorial en homepage |
| `destacado-arriba` | Slot superior de destacados |
| `destacado-medio` | Slot medio de destacados |
| `super-destacado` | Slot de super destacado |
| `home-slider` | Slider de homepage |
| `slider-en-home` | Ídem (taxonomía alternativa) |
| `recomendado` | Widget de recomendados |
| `etiquetas-de-recomendados` | Tags del widget de recomendados |
| `nav_menu` | Menú de navegación donde aparece |
| `post_format` | Formato WordPress (casi siempre vacío) |
| `spnl_log_type` | Taxonomía del plugin de newsletter |
| `web_story_category` | Categoría de Web Stories (no aplica a posts) |
| `web_story_media_source` | Fuente de media de Web Stories |
| `web_story_tag` | Tags de Web Stories |
| `wp_pattern_category` | Interna de WordPress |
| `wp_theme` | Interna de WordPress |

---

## SEO (Yoast)

| Columna | Qué es | Útil |
|---|---|---|
| `yoast_metadesc` | Descripción SEO escrita por el editor — similar al copete | Opcional |
| `yoast_focuskw` | Palabra clave SEO principal | Opcional |
| `yoast_reading_time_minutes` | Tiempo de lectura estimado por Yoast | No |
| `thumbnail_id` | ID numérico de la imagen de portada (no es la URL) | No |

---

## Columnas técnicas de WordPress (ignorar)

| Columna | Qué es |
|---|---|
| `comment_count` | Cantidad de comentarios |
| `comment_status` | Si los comentarios están abiertos o cerrados |
| `ping_status` | Si el post acepta pingbacks |
| `pinged` | URLs que ya recibieron pingback |
| `to_ping` | URLs pendientes de pingback |
| `post_content_filtered` | Versión filtrada del contenido (uso interno de plugins) |
| `post_mime_type` | Tipo MIME (solo relevante para attachments) |
| `post_parent` | ID del post padre (relevante para páginas, no para posts) |
| `post_password` | Contraseña si el post es protegido (vacío en todos estos) |
| `menu_order` | Orden en menús (siempre 0 en posts) |

---

## Modelado de Tópicos y Recomendación (BERTopic)

| Columna / Variable | Qué es | Uso |
|---|---|---|
| `topic` | ID numérico del tópico asignado (0-21, 100 es outlier) | Agrupamiento temático |
| `topic_name` | Tópico + Las 3 palabras clave más pesadas (c-TF-IDF) | Descriptor algorítmico del clúster |
| `embeddings_naturales.npy` | Matriz de embeddings densos por documento | Base del espacio semántico |
| `doc_topic_dist.npy` | Matriz de distribución continua de probabilidad por tópico | Base del espacio temático |
| `umap_sem_x` / `y` | Coordenadas 2D de embeddings proyectados | Visualización de constelación semántica |
| `umap_tem_x` / `y` | Coordenadas 2D de probabilidades proyectadas | Visualización de constelación temática |