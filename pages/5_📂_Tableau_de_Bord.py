import streamlit as st
import sqlite3
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Cost3D - Tableau de Bord & Archives", layout="centered", page_icon="📂")

# Vérification de l'authentification
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔒 Veuillez vous connecter sur la page d'Accueil avant d'accéder à ce menu.")
    st.stop()

st.title("📂 Archives & Tableau de Bord Opérationnel")
st.caption("Consultez l'historique complet des devis enregistrés et analysez la santé financière de l'atelier.")
st.markdown("---")

# Lecture des données de la base SQLite commune
conn = sqlite3.connect("projets_3d.db", check_same_thread=False)
df = pd.read_sql_query("""SELECT date as 'Date', nom as 'Projet', filament as 'Filament(s)', 
                          cout_revient as 'Revient', prix_vente as 'Vente', 
                          poids_total as 'Poids' FROM projets ORDER BY id DESC""", conn)
conn.close()

st.subheader("📈 Indicateurs de Performance (KPI)")
if not df.empty:
    ca_total = df['Vente'].sum()
    cout_total = df['Revient'].sum()
    marge_globale = ca_total - cout_total
    poids_total_kg = df['Poids'].sum() / 1000
    
    # Calcul du ratio d'efficacité financière
    ratio_marge = ((marge_globale / ca_total) * 100) if ca_total > 0 else 0
    
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1: 
        st.metric("Chiffre d'Affaires Globale", f"{ca_total:.2f} CHF")
    with kpi2: 
        st.metric("Marge Nette Cumulée", f"{marge_globale:.2f} CHF", delta=f"{ratio_marge:.1f}% Éfficacité")
    with kpi3: 
        st.metric("Volume Matière Consommé", f"{poids_total_kg:.2f} Kg")
else: 
    st.info("Aucune donnée disponible pour alimenter les indicateurs financiers. Enregistrez un premier projet validé.")

st.markdown("---")

# --- HISTORIQUE COMPLET ET EXPORT BANQUE ---
st.subheader("🗄️ Journal comptable de l'Atelier")
if not df.empty:
    # Affichage du tableau interactif complet
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Préparation du fichier d'export
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Exporter l'historique au format comptable (CSV/Excel)", 
        data=csv, 
        file_name="export_compta_cost3d_chf.csv", 
        mime='text/csv', 
        use_container_width=True
    )
