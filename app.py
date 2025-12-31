import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import pandas as pd

st.set_page_config(page_title="CBI Pro - Precision Mapper", layout="wide")

# --- INITIALISATION ---
if "points" not in st.session_state:
    st.session_state["points"] = []
if "image_data" not in st.session_state:
    st.session_state["image_data"] = None

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("⚙️ Configuration")
    mode = st.radio("Mode de saisie", ["Points simples", "Segments (Passes)"])
    
    st.divider()
    if st.button("🔄 Changer d'image", use_container_width=True):
        st.session_state["image_data"] = None
        st.session_state["points"] = []
        st.rerun()

    if st.button("⏪ Annuler dernier point", use_container_width=True):
        if st.session_state["points"]:
            st.session_state["points"].pop()
            st.rerun()

# --- LOGIQUE D'AFFICHAGE ---
if st.session_state["image_data"] is None:
    uploaded_file = st.file_uploader("Importer une image", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        st.session_state["image_data"] = uploaded_file
        st.rerun()
else:
    img_orig = Image.open(st.session_state["image_data"]).convert("RGB")
    orig_w, orig_h = img_orig.size
    
    # Redimensionnement pour affichage (largeur fixe 1000px)
    display_w = 1000
    ratio = display_w / orig_w
    display_h = int(orig_h * ratio)
    img_display = img_orig.resize((display_w, display_h), Image.Resampling.LANCZOS)

    canvas = img_display.copy()
    draw = ImageDraw.Draw(canvas)

    # Dessin des éléments
    for i, p in enumerate(st.session_state["points"]):
        ix, iy = p['canvas_x'], p['canvas_y']
        color = "#FF0000" if mode == "Points simples" else ("#00FF00" if i % 2 == 0 else "#FF0000")
        draw.ellipse((ix-5, iy-5, ix+5, iy+5), fill=color, outline="white")
        
        # Dessin de la ligne pour les segments
        if mode != "Points simples" and i % 2 == 1:
            prev = st.session_state["points"][i-1]
            draw.line([(prev['canvas_x'], prev['canvas_y']), (ix, iy)], fill="yellow", width=3)

    col1, col2 = st.columns([2, 1])

    with col1:
        # Capture du clic
        res = streamlit_image_coordinates(canvas, key=f"map_{len(st.session_state['points'])}")

        if res:
            cx, cy = res['x'], res['y']
            
            # --- CALCUL DES COORDONNÉES (0 à 100) ---
            scaled_x = (cx / display_w) * 100
            scaled_y = (1 - (cy / display_h)) * 100

            # --- LOGIQUE DES COLONNES ---
            nb_points = len(st.session_state["points"])
            
            if mode == "Points simples":
                v_type = "Point"
                v_shape = nb_points + 1
                v_pt = "-"
            else:
                v_type = "Segment"
                v_shape = (nb_points // 2) + 1
                # Modification ici : Départ -> 0, Arrivée -> 1
                v_pt = 0 if nb_points % 2 == 0 else 1

            new_entry = {
                "Shape": v_shape,
                "Type": v_type,
                "Point": v_pt,
                "X": round(scaled_x, 2),
                "Y": round(scaled_y, 2),
                "Commentaire": "",
                "canvas_x": cx,
                "canvas_y": cy
            }

            if not st.session_state["points"] or (cx != st.session_state["points"][-1]['canvas_x']):
                st.session_state["points"].append(new_entry)
                st.rerun()

    with col2:
        st.subheader("📊 Tableau des données")
        if st.session_state["points"]:
            df = pd.DataFrame(st.session_state["points"])
            
            # Affichage éditable
            edited_df = st.data_editor(
                df[["Shape", "Type", "Point", "X", "Y", "Commentaire"]],
                hide_index=True,
                use_container_width=True,
                key="editor"
            )
            
            # Mise à jour des commentaires
            if not edited_df.equals(df[["Shape", "Type", "Point", "X", "Y", "Commentaire"]]):
                 for idx, row in edited_df.iterrows():
                     st.session_state["points"][idx]["Commentaire"] = row["Commentaire"]

            st.download_button(
                "📥 Télécharger CSV",
                edited_df.to_csv(index=False).encode('utf-8'),
                "export_coordonnees.csv",
                use_container_width=True
            )
        else:
            st.info("Cliquez sur l'image pour enregistrer des points.")
