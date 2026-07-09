import streamlit as st
import sqlite3
import pandas as pd
import json

# Configuration de la page
st.set_page_config(page_title="Cost3D - Gestion des Stocks", layout="centered", page_icon="📦")

# Vérification de l'authentification
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔒 Veuillez vous connecter sur la page d'Accueil avant d'accéder à ce menu.")
    st.stop()

st.title("📦 Suivi et Gestion de l'Inventaire Plastique")
st.caption("Ajoutez vos nouvelles bobines de matière et surveillez les niveaux d'usure en temps réel.")

# Chargement du dictionnaire des filaments pour avoir la liste des plastiques configurés
try:
    with open("filaments.json", "r", encoding="utf-8") as f:
        data_filaments = json.load(f)
except Exception:
    data_filaments = {
        "PLA": {"prix": 24.90, "perte": 5}, "ASA": {"prix": 29.90, "perte": 12},
        "PETG": {"prix": 26.90, "perte": 8}, "PAHT-CF": {"prix": 64.90, "perte": 15}
    }
liste_filaments = list(data_filaments.keys())

# Lecture ou fallback des fabricants de bobines
try:
    with open("marques.txt", "r", encoding="utf-8") as file:
        marques_celebres = [line.strip() for line in file if line.strip()]
except Exception:
    marques_celebres = ["Bambu Lab", "eSUN", "Polymaker", "Prusament (Prusa)", "Extrudr", "Générique / Autre"]

# --- FORMULAIRE D'ENTRÉE EN STOCK ---
st.subheader("📥 Enregistrer une nouvelle bobine")
with st.form("ajout_bobine"):
    marque_bobine = st.selectbox("Fabricant / Marque du filament", marques_celebres)
    nom_bobine = st.text_input("Référence / Couleur (ex: Noir RAL 9005)", value="Noir Lot #1")
    type_mat_stock = st.selectbox("Type de plastique", liste_filaments, index=1)
    poids_init_stock = st.number_input("Poids net initial du plastique (g)", min_value=1, value=1000)
    
    if st.form_submit_button("📥 Valider l'entrée en stock"):
        conn = sqlite3.connect("projets_3d.db", check_same_thread=False)
        c = conn.cursor()
        c.execute("""INSERT INTO stocks (marque, nom_bobine, type_filament, poids_restant, poids_initial) 
                     VALUES (?, ?, ?, ?, ?)""", 
                  (marque_bobine, nom_bobine, type_mat_stock, poids_init_stock, poids_init_stock))
        conn.commit()
        conn.close()
        st.success(f"Bobine [{marque_bobine}] '{nom_bobine}' ajoutée à l'inventaire de l'atelier !")
        st.rerun()

st.markdown("---")

# --- LISTING ET FILTRAGE DE L'INVENTAIRE ---
st.subheader("📊 État actuel de vos réserves")

conn = sqlite3.connect("projets_3d.db", check_same_thread=False)
df_stock = pd.read_sql_query("""SELECT marque as 'Marque', nom_bobine as 'Référence / Couleur', 
                                type_filament as 'Matériau', poids_restant as 'Quantité restante (g)', 
                                poids_initial as 'Capacité (g)' FROM stocks ORDER BY id DESC""", conn)
conn.close()

if not df_stock.empty:
    col_f1, col_f2 = st.columns(2)
    with col_f1: 
        filtre_marque = st.multiselect("Filtrer par Marque", options=df_stock['Marque'].unique())
    with col_f2: 
        filtre_mat = st.multiselect("Filtrer par Plastique", options=df_stock['Matériau'].unique())
        
    df_filtre = df_stock.copy()
    if filtre_marque: df_filtre = df_filtre[df_filtre['Marque'].isin(filtre_marque)]
    if filtre_mat: df_filtre = df_filtre[df_filtre['Matériau'].isin(filtre_mat)]
        
    st.dataframe(df_filtre, use_container_width=True, hide_index=True)
    
    # Alertes visuelles automatiques de fin de bobine
    for index, row in df_filtre.iterrows():
        if row['Quantité restante (g)'] < 150:
            st.warning(f"⚠️ **Seuil critique** : La bobine **{row['Marque']}** - *{row['Référence / Couleur']}* est bientôt épuisée ({row['Quantité restante (g)']}g restants). Prévoyez un réapprovisionnement.")
else:
    st.info("Aucune bobine enregistrée dans votre inventaire suisse pour le moment.")
