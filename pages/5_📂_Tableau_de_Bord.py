import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go

# Configuration de la page
st.set_page_config(page_title="Cost3D - Tableau de Bord & Archives", layout="centered", page_icon="📂")

# Vérification de l'authentification
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔒 Veuillez vous connecter sur la page d'Accueil avant d'accéder à ce menu.")
    st.stop()

st.title("📂 Archives & Tableau de Bord Opérationnel")
st.caption("Consultez l'historique complet des devis enregistrés et analysez la santé financière de l'atelier.")
st.markdown("---")

# Lecture des données de la base SQLite commune (avec ajout de la colonne client_nom)
conn = sqlite3.connect("projets_3d.db", check_same_thread=False)
try:
    df = pd.read_sql_query("""SELECT date as 'Date', client_nom as 'Client', nom as 'Projet', 
                              filament as 'Filament(s)', cout_revient as 'Revient', 
                              prix_vente as 'Vente', poids_total as 'Poids' FROM projets ORDER BY id DESC""", conn)
except Exception:
    # Fallback de sécurité si la colonne client_nom n'est pas encore créée lors du premier appel
    df = pd.read_sql_query("""SELECT date as 'Date', nom as 'Projet', filament as 'Filament(s)', 
                              cout_revient as 'Revient', prix_vente as 'Vente', 
                              poids_total as 'Poids' FROM projets ORDER BY id DESC""", conn)
    df['Client'] = 'Client Passager'
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
        st.metric("Chiffre d'Affaires Global", f"{ca_total:.2f} CHF")
    with kpi2: 
        st.metric("Marge Nette Cumulée", f"{marge_globale:.2f} CHF", delta=f"{ratio_marge:.1f}% Efficacité")
    with kpi3: 
        st.metric("Volume Matière Consommé", f"{poids_total_kg:.2f} Kg")
else: 
    st.info("Aucune donnée disponible pour alimenter les indicateurs financiers. Enregistrez un premier projet validé.")

# --- 🟢 GRAPHIC D'ÉVOLUTION DU CA ET DE LA MARGE MENSUELLE ---
if not df.empty:
    st.markdown("---")
    st.subheader("📊 Évolution Mensuelle de l'Activité")
    
    try:
        # Copie et traitement des données de date au format "JJ/MM/AAAA HH:MM"
        df_graph = df.copy()
        df_graph['Date_Parsed'] = pd.to_datetime(df_graph['Date'], format='%d/%m/%Y %H:%M')
        
        # Groupement par Année-Mois comptable
        df_mensuel = df_graph.groupby(df_graph['Date_Parsed'].dt.to_period('M')).agg({'Vente': 'sum', 'Revient': 'sum'}).reset_index()
        df_mensuel['Date_Parsed'] = df_mensuel['Date_Parsed'].astype(str)
        df_mensuel['Marge'] = df_mensuel['Vente'] - df_mensuel['Revient']
        
        # Génération des tracés Plotly
        fig_ca = go.Figure()
        fig_ca.add_trace(go.Bar(x=df_mensuel['Date_Parsed'], y=df_mensuel['Vente'], name="Chiffre d'Affaires (CHF)", marker_color='#FF4B4B'))
        fig_ca.add_trace(go.Bar(x=df_mensuel['Date_Parsed'], y=df_mensuel['Marge'], name="Marge Nette (CHF)", marker_color='#008631'))
        
        fig_ca.update_layout(
            barmode='group',
            xaxis_title="Périodes de production",
            yaxis_title="Montant comptable (CHF)",
            margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_ca, use_container_width=True)
    except Exception as e:
        st.caption("Le graphique d'évolution se construira automatiquement lors de vos prochains enregistrements.")

st.markdown("---")

# --- HISTORIQUE COMPLET ET EXPORT EXCEL ---
st.subheader("🗄️ Journal Comptable de l'Atelier")
if not df.empty:
    # Affichage du filtre par client pour faciliter les recherches d'historique
    liste_clients_filtre = ["Tous les clients"] + df['Client'].unique().tolist()
    client_filtre = st.selectbox("Filtrer le journal par compte client :", liste_clients_filtre)
    
    df_affichage = df.copy()
    if client_filtre != "Tous les clients":
        df_affichage = df_affichage[df_affichage['Client'] == client_filtre]
        
    # Affichage du tableau interactif complet ordonné
    st.dataframe(df_affichage, use_container_width=True, hide_index=True)
    
    # Préparation du fichier d'export
    csv = df_affichage.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Exporter la sélection au format comptable (CSV/Excel)", 
        data=csv, 
        file_name="export_compta_cost3d_chf.csv", 
        mime='text/csv', 
        use_container_width=True
    )
