import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Cost3D - Gestion Clients", layout="centered", page_icon="👥")

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔒 Veuillez vous connecter sur la page d'Accueil avant d'accéder à ce menu.")
    st.stop()

st.title("👥 Répertoire & Gestion des Clients")
st.caption("Enregistrez les coordonnées de vos clients professionnels et particuliers pour simplifier la facturation.")

# --- FORMULAIRE D'AJOUT ---
st.subheader("🏢 Ajouter un nouveau client")
with st.form("ajout_client"):
    nom_entreprise = st.text_input("Nom de l'entreprise / Raison sociale", value="Ex: Robert SA")
    contact_nom = st.text_input("Nom & Prénom du contact principal", value="Ex: Jean Dupont")
    col_c1, col_c2 = st.columns(2)
    with col_c1: email = st.text_input("Adresse Email")
    with col_c2: telephone = st.text_input("Numéro de téléphone")
    adresse = st.text_area("Adresse de livraison / Facturation complète")
    
    if st.form_submit_button("📥 Enregistrer le client"):
        if not nom_entreprise or not contact_nom:
            st.error("⚠️ Le nom de l'entreprise et le nom du contact sont obligatoires.")
        else:
            conn = sqlite3.connect("projets_3d.db", check_same_thread=False)
            c = conn.cursor()
            c.execute("""INSERT INTO clients (nom_entreprise, contact_nom, email, telephone, adresse) 
                         VALUES (?, ?, ?, ?, ?)""", (nom_entreprise, contact_nom, email, telephone, adresse))
            conn.commit()
            conn.close()
            st.success(f"Client '{nom_entreprise}' enregistré avec succès !")
            st.rerun()

st.markdown("---")

# --- LISTE DES CLIENTS ---
st.subheader("📋 Liste des comptes clients")
conn = sqlite3.connect("projets_3d.db", check_same_thread=False)
df_clients = pd.read_sql_query("SELECT id, nom_entreprise as 'Entreprise', contact_nom as 'Contact', email as 'Email', telephone as 'Téléphone', adresse as 'Adresse' FROM clients ORDER BY nom_entreprise ASC", conn)
conn.close()

if not df_clients.empty:
    recherche = st.text_input("🔍 Rechercher un client par nom ou entreprise :")
    df_filtre = df_clients.copy()
    if recherche:
        df_filtre = df_filtre[df_filtre['Entreprise'].str.contains(recherche, case=False) | df_filtre['Contact'].str.contains(recherche, case=False)]
    
    st.dataframe(df_filtre.drop(columns=['id']), use_container_width=True, hide_index=True)
else:
    st.info("Aucun client enregistré pour le moment. Utilisez le formulaire ci-dessus.")
