import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import pandas as pd

st.set_page_config(page_title="CBI Pro - Extracteur", layout="wide")

# Initialisation
if "points" not in st.session_state:
    st.session_state["points"] = []
if "image_data" not in st.session_state:
    st.session_state["image_data"] = None

st.title("📍 Extracteur X/Y Ultra-Rapide")

with st.sidebar:
    st.header("⚙️ Configuration")
    mode = st.radio("Mode", ["Points simples", "Segments (A->B)"])
    st.divider()
    use_scale = st.checkbox("Activer l'échelle", value=False)
    max_x = st.number_input("Max X", value=100.0)
    max_y = st.number_input("Max Y", value=100.0)
    
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state["points"] = []
        st.session_state["image_data"] = None
        st.rerun()

if st.session_state["image_data"] is None:
    uploaded = st.file_uploader("Choisir une image", type=["png", "jpg", "jpeg"])
    if uploaded:
        st.session_state["image_data"] = uploaded
        st.rerun()
else:
    img = Image.open(st.session_state["image_data"]).convert("RGB")
    w, h = img.size
    ratio = 1000 / w
    display_img = img.resize((1000, int(h * ratio)), Image.Resampling.LANCZOS)

    canvas = display_img.copy()
    draw = ImageDraw.Draw(canvas)

    # Dessin des points
    for i, p in enumerate(st.session_state["points"]):
        ix, iy = p['x'], p['y']
        color = "red" if mode == "Points simples" else ("#00FF00" if i % 2 == 0 else "#FF0000")
        draw.ellipse((ix-5, iy-5, ix+5, iy+5), fill=color, outline="white")
        if mode != "Points simples" and i % 2 == 1:
            draw.line([(st.session_state["points"][i-1]['x'], st.session_state["points"][i-1]['y']), (ix, iy)], fill="yellow", width=3)

    col1, col2 = st.columns([3, 1])
    with col1:
        # Utilisation de l'index pour forcer la mise à jour immédiate au clic
        res = streamlit_image_coordinates(canvas, key=f"c_{len(st.session_state['points'])}")
        
        if res:
            curr_x, curr_y = res['x'], res['y']
            # Vérification anti-doublon
            if not st.session_state["points"] or (curr_x != st.session_state["points"][-1]['x']):
                real_x, real_y = curr_x / ratio, curr_y / ratio
                st.session_state["points"].append({
                    "Type": "Point" if mode == "Points simples" else ("A" if len(st.session_state["points"]) % 2 == 0 else "B"),
                    "x_scaled": round((real_x / w) * max_x if use_scale else real_x, 2),
                    "y_scaled": round((real_y / h) * max_y if use_scale else real_y, 2),
                    "x": curr_x, "y": curr_y
                })
                st.rerun()

    with col2:
        st.subheader("📊 Données")
        df = pd.DataFrame(st.session_state["points"])
        if not df.empty:
            st.dataframe(df[["Type", "x_scaled", "y_scaled"]], hide_index=True)
            st.download_button("📥 Export", df.to_csv(index=False), "data.csv")
