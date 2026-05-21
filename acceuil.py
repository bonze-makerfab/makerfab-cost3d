import streamlit as st
import sqlite3
import os
import shutil
from datetime import datetime, timedelta

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="MAKERFAB Cost3D - Accueil", 
    layout="centered", 
    page_icon="🖨️"
)

# DESIGN & CSS PERSONNALISÉ UNIQUE (ÉCRAN ET IMPRESSION PDF)
st.markdown("""
<style>
div[data-testid='stMetricValue'] { font-size: 26px !important; font-weight: bold; color: #1E1E24; } 
.stButton>button { background-color: #FF4B4B !important; color: white !important; font-weight: bold; } 
@media print { 
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

# 3. INITIALISATION DES LOGS ET SESSIONS PARTAGÉES
if "temps_auto" not in st.session_state: st.session_state["temps_auto"] = 4.5
if "poids_auto" not in st.session_state: st.session_state["poids_auto"] = 150.0
if "machine_connectee" not in st.session_state: st.session_state["machine_connectee"] = "Aucune"
if "machine_active_data" not in st.session_state: st.session_state["machine_active_data"] = None

# 4. FONCTION DE SAUVEGARDE AUTOMATIQUE DE LA BASE DE DONNÉES
def executer_sauvegarde_auto():
    db_source = "projets_3d.db"
    backup_dir = "backups"
    
    if not os.path.exists(db_source):
        return
        
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    date_str = datetime.now().strftime("%Y%m%d")
    db_destination = os.path.join(backup_dir, f"backup_{date_str}.db")
    
    if not os.path.exists(db_destination):
        try:
            shutil.copy2(db_source, db_destination)
            
            # Nettoyage des anciennes sauvegardes (> 30 jours)
            limite_retention = datetime.now() - timedelta(days=30)
            for fichier in os.listdir(backup_dir):
                chemin_fichier = os.path.join(backup_dir, fichier)
                if os.path.isfile(chemin_fichier) and fichier.startswith("backup_"):
                    try:
                        date_fichier_str = fichier.replace("backup_", "").replace(".db", "")
                        date_fichier = datetime.strptime(date_fichier_str, "%Y%m%d")
                        if date_fichier < limite_retention:
                            os.remove(chemin_fichier)
                    except ValueError:
                        pass
        except Exception:
            pass

# 5. GESTION BASE DE DONNÉES UNIQUE
def initialiser_db():
    conn = sqlite3.connect("projets_3d.db", check_same_thread=False)
    c = conn.cursor()
    
    # Table des projets
    c.execute('''CREATE TABLE IF NOT EXISTS projets (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        date TEXT, 
        nom TEXT, 
        filament TEXT, 
        cout_revient REAL, 
        prix_vente REAL, 
        poids_total REAL,
        client_nom TEXT DEFAULT 'Client Passager')''')
    
    # Table des clients
    c.execute('''CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nom_entreprise TEXT, 
        contact_nom TEXT, 
        email TEXT, 
        telephone TEXT, 
        adresse TEXT)''')
        
    # Table des machines de la flotte d'atelier
    c.execute('''CREATE TABLE IF NOT EXISTS machines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom_machine TEXT,
        marque TEXT,
        ip_adresse TEXT,
        puissance_watts INTEGER,
        amortissement_horaire REAL,
        cle_api TEXT,
        bambu_serial TEXT,
        bambu_code TEXT)''')
        
    # Fallbacks d'adaptation pour les anciennes bases de données existantes
    try: c.execute("ALTER TABLE projets ADD COLUMN poids_total REAL DEFAULT 0.0")
    except sqlite3.OperationalError: pass
    try: c.execute("ALTER TABLE projets ADD COLUMN client_nom TEXT DEFAULT 'Client Passager'")
    except sqlite3.OperationalError: pass
    
    # Table des stocks de filaments
    c.execute('''CREATE TABLE IF NOT EXISTS stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        marque TEXT, 
        nom_bobine TEXT, 
        type_filament TEXT, 
        poids_restant REAL, 
        poids_initial REAL)''')
    try: c.execute("ALTER TABLE stocks ADD COLUMN marque TEXT DEFAULT 'Générique'")
    except sqlite3.OperationalError: pass
    
    conn.commit()
    conn.close()
    
    # Lancement de la sauvegarde automatique quotidienne de sécurité
    executer_sauvegarde_auto()

initialiser_db()

# 6. INTERFACE DE BIENVENUE
col_titre1, col_titre2 = st.columns([0.15, 0.85], vertical_alignment="center")
with col_titre1:
    try: st.image("logo.png", width=120)
    except Exception: st.title("⚙️")
with col_titre2:
    st.title("MAKERFAB Cost3D")
    st.caption("ERP modulaire de chiffrage, gestion des stocks et facturation suisse")

st.markdown("---")
st.markdown("""
### 👋 Bienvenue dans l'ERP de votre atelier de fabrication 3D

Utilisez le **menu de navigation latéral** pour accéder aux différents outils :
* **📝 1_Saisie & Calcul** : Configurez votre projet, liez un client et préparez les variables de fabrication.
* **🔌 2_Connexion Machines** : Gérez votre flotte d'imprimantes et interrogez-les en direct sur le réseau local.
* **📊 3_Analyses & Devis** : Visualisez la décomposition des coûts et imprimez vos factures PDF aux normes CH.
* **📦 4_Gestion des Stocks** : Suivez l'état de vos bobines et soyez alerté avant la rupture de matière (<150g).
* **📂 5_Tableau de Bord** : Analysez votre chiffre d'affaires, votre rentabilité mensuelle et exportez le journal.
* **👥 6_Gestion Clients** : Enregistrez et gérez les coordonnées de vos clients professionnels et particuliers.
""")

st.info(f"🔌 **Machine active** : {st.session_state['machine_connectee']} "
        f"| **Temps chargé** : {st.session_state['temps_auto']}h | **Poids chargé** : {st.session_state['poids_auto']}g")
