import streamlit as st
import sqlite3

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="MAKERFAB Cost3D - Accueil", 
    layout="centered", 
    page_icon="🖨️"
)

# DESIGN & CSS PERSONNALISÉ ROBUSTE POUR L'ÉCRAN ET L'IMPRESSION
st.markdown("""
<style>
div[data-testid='stMetricValue'] { font-size: 26px !important; font-weight: bold; color: #1E1E24; } 
.stButton>button { background-color: #FF4B4B !important; color: white !important; font-weight: bold; } 
@media print { 
    /* Masquage total de l'interface Streamlit sur le PDF */
    header, [data-testid='stSidebar'], [data-testid='stHeader'], [data-testid='stDecoration'], button, .stButton, iframe { display: none !important; } 
    .main .block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; background-color: white !important; color: black !important; }
    .print-only { display: block !important; } 
}
.print-only { display: none; }
</style>
""", unsafe_allow_html=True)

# 2. 🔒 SYSTÈME DE SÉCURITÉ ET VERROUILLAGE GLOBAL
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.subheader("🔒 Accès Restreint - MAKERFAB Cost3D")
    saisie_password = st.text_input("Veuillez entrer le code d'accès de l'atelier :", type="password")
    if st.button("Se connecter", use_container_width=True):
        password_correct = False
        if "password" in st.secrets:
            if saisie_password == st.secrets["password"]: 
                password_correct = True
        elif saisie_password == "admin3d": 
            password_correct = True
            
        if password_correct:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Code d'accès incorrect. (En local, utilisez 'admin3d')")
    st.stop()

# 3. INITIALISATION DES LOGS ET SESSIONS PARTAGÉES (Accessibles sur toutes les pages)
if "temps_auto" not in st.session_state:
    st.session_state["temps_auto"] = 4.5
if "poids_auto" not in st.session_state:
    st.session_state["poids_auto"] = 150.0
if "machine_connectee" not in st.session_state:
    st.session_state["machine_connectee"] = "Aucune"

# 4. GESTION BASE DE DONNÉES UNIQUE
def initialiser_db():
    # check_same_thread=False est indispensable pour éviter les blocages multi-pages
    conn = sqlite3.connect("projets_3d.db", check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS projets (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        date TEXT, 
        nom TEXT, 
        filament TEXT, 
        cout_revient REAL, 
        prix_vente REAL, 
        poids_total REAL)''')
    try: 
        c.execute("ALTER TABLE projets ADD COLUMN poids_total REAL DEFAULT 0.0")
    except sqlite3.OperationalError: 
        pass
    
    c.execute('''CREATE TABLE IF NOT EXISTS stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        marque TEXT, 
        nom_bobine TEXT, 
        type_filament TEXT, 
        poids_restant REAL, 
        poids_initial REAL)''')
    try: 
        c.execute("ALTER TABLE stocks ADD COLUMN marque TEXT DEFAULT 'Générique'")
    except sqlite3.OperationalError: 
        pass
    conn.commit()
    conn.close()

initialiser_db()

# 5. INTERFACE DE BIENVENUE
col_titre1, col_titre2 = st.columns([0.15, 0.85], vertical_alignment="center")
with col_titre1:
    try: 
        st.image("logo.png", width=120)
    except Exception: 
        st.title("⚙️")
with col_titre2:
    st.title("MAKERFAB Cost3D")
    st.caption("ERP modulaire de chiffrage, gestion des stocks et facturation suisse")

st.markdown("---")
st.markdown("""
### 👋 Bienvenue dans l'ERP de votre atelier de fabrication 3D

Utilisez le **menu de navigation latéral** pour accéder aux différents outils :
* **📝 1_Saisie & Calcul** : Configurez votre projet, vos paramètres d'énergie, de main d'œuvre et calculez vos marges.
* **🔌 2_Connexion Machines** : Connectez vos imprimantes (**Bambu Lab, Elegoo, Anycubic, Snapmaker, Flashforge**) pour récupérer instantanément les métadonnées.
* **📊 3_Analyses & Devis** : Visualisez la décomposition des coûts et imprimez vos devis conformes aux normes CH.
* **📦 4_Gestion des Stocks** : Suivez l'état de vos bobines et soyez alerté avant la rupture de matière.
* **📂 5_Tableau de Bord** : Analysez votre rentabilité, votre chiffre d'affaires cumulé et exportez vos sauvegardes.
""")

st.info(f"🔌 **Statut de synchronisation actuel** : {st.session_state['machine_connectee']} "
        f"(Temps : {st.session_state['temps_auto']}h | Poids : {st.session_state['poids_auto']}g)")
