import streamlit as st
import json
import sqlite3
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Cost3D - Saisie & Calcul", layout="centered", page_icon="📝")

# Vérification de l'authentification
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔒 Veuillez vous connecter sur la page d'Accueil avant d'accéder à ce menu.")
    st.stop()

# Sécurité d'initialisation des variables de session
if "temps_auto" not in st.session_state: st.session_state["temps_auto"] = 4.5
if "poids_auto" not in st.session_state: st.session_state["poids_auto"] = 150.0
if "machine_connectee" not in st.session_state: st.session_state["machine_connectee"] = "Aucune"

# Chargement du dictionnaire des filaments
try:
    with open("filaments.json", "r", encoding="utf-8") as f:
        data_filaments = json.load(f)
except Exception:
    data_filaments = {
        "PLA": {"prix": 24.90, "perte": 5}, "ASA": {"prix": 29.90, "perte": 12},
        "PETG": {"prix": 26.90, "perte": 8}, "PAHT-CF": {"prix": 64.90, "perte": 15}
    }

st.title("📝 Paramétrage du Projet & Calcul des Coûts")
st.caption("Saisissez les paramètres de fabrication. Les données de temps, poids, puissance et amortissement s'adaptent si une machine est liée.")

if st.session_state["machine_connectee"] != "Aucune":
    st.success(f"🔗 Données synchronisées depuis l'appareil : **{st.session_state['machine_connectee']}**")

# --- 1. IDENTIFICATION & CLIENT ---
with st.container(border=True):
    st.subheader("1. Identification & Client")
    
    # Récupération dynamique des clients existants depuis la base de données SQLite
    conn = sqlite3.connect("projets_3d.db", check_same_thread=False)
    try:
        df_c_list = pd.read_sql_query("SELECT nom_entreprise FROM clients ORDER BY nom_entreprise ASC", conn)
        liste_clients_choix = ["Client Passager"] + df_c_list["nom_entreprise"].tolist()
    except Exception:
        liste_clients_choix = ["Client Passager"]
    conn.close()
    
    client_selectionne = st.selectbox("Attribuer ce projet à un client :", liste_clients_choix)
    
    col_id1, col_id2 = st.columns(2)
    with col_id1: 
        nom_projet = st.text_input("Nom du projet / Référence Devis", value="Boîtier Technique ASA")
    with col_id2: 
        quantite_pieces = st.number_input("Quantité de pièces à produire", min_value=1, value=1, step=1)

# --- 2. MATIÈRES PREMIÈRES & PERTES ---
with st.container(border=True):
    st.subheader("2. Matières Premières & Pertes")
    liste_filaments = list(data_filaments.keys())
    
    st.markdown("**Filament Principal (Modèle)**")
    col_m1, col_m2 = st.columns(2)
    with col_m1: 
        fil_p = st.selectbox("Type de filament principal", liste_filaments, index=1)
    with col_m2: 
        poids_p = st.number_input("Poids du modèle seul (g)", min_value=0.0, value=float(st.session_state["poids_auto"]))
    
    perte_p = st.slider("Taux de perte Modèle (%)", min_value=0, max_value=100, value=int(data_filaments[fil_p]["perte"]))
    prix_p = data_filaments[fil_p]["prix"]
    
    st.markdown("---")
    activer_support = st.toggle("Activer un second filament (Supports)", value=False)
    poids_s, loss_s, prix_s, fil_s = 0.0, 0, 0.0, "Aucun"
    if activer_support:
        col_s1, col_s2 = st.columns(2)
        with col_s1: 
            fil_s = st.selectbox("Type de filament de support", liste_filaments, index=3)
        with col_s2: 
            poids_s = st.number_input("Poids des supports (g)", min_value=0.0, value=30.0)
        loss_s = st.slider("Taux de perte Support (%)", min_value=0, max_value=100, value=int(data_filaments[fil_s]["perte"])+10)
        prix_s = data_filaments[fil_s]["prix"]

# --- 3. TEMPS & ÉNERGIE DYNAMIQUE ---
with st.container(border=True):
    st.subheader("3. Temps & Énergie Dynamique")
    heures_impression = st.number_input("Temps d'impression machine (Heures)", min_value=0.0, value=float(st.session_state["temps_auto"]), step=0.1)
    
    col_e1, col_e2 = st.columns(2)
    with col_e1: 
        prix_kwh_plein = st.number_input("Tarif Plein kWh (CHF)", min_value=0.0, value=0.34, format="%.4f")
    with col_e2: 
        ratio_heures_pleines = st.slider("Heures d'impression en Tarif Plein (%)", min_value=0, max_value=100, value=70)
    
    prix_kwh_creux = prix_kwh_plein * 0.75
    prix_kwh_moyen = (prix_kwh_plein * (ratio_heures_pleines / 100)) + (prix_kwh_creux * ((100 - ratio_heures_pleines) / 100))
    
    # 📡 Récupération de la puissance injectée par le hub de flotte
    p_defaut = 350
    if "machine_active_data" in st.session_state and st.session_state["machine_active_data"]:
        p_defaut = st.session_state["machine_active_data"]["puissance"]
        
    puissance_machine = st.number_input("Consommation moyenne machine (W)", min_value=0, value=int(p_defaut))
    
    appliquer_recuit = st.toggle("Activer le recuit thermique (Annealing)", value=False)
    cout_recuit_elec = 0.0
    if appliquer_recuit:
        col_rec1, col_rec2 = st.columns(2)
        with col_rec1: puissance_four = st.number_input("Puissance four (W)", min_value=0, value=500)
        with col_rec2: heures_recuit = st.number_input("Durée recuit (h)", min_value=0.0, value=4.0)
        cout_recuit_elec = (puissance_four / 1000) * heures_recuit * prix_kwh_plein

# --- 4. AMORTISSEMENT, MAINTENANCE & CONSOMMABLES ---
with st.container(border=True):
    st.subheader("4. Amortissement, Maintenance & Consommables")
    est_abrasif = any(x in fil_p for x in ["-CF", "-GF", "PPS", "PAHT", "316L", "Titane", "Glow", "WOOD", "COPPER", "BRONZE", "SILK"]) or (activer_support and any(x in fil_s for x in ["-CF", "-GF"]))
    est_haute_temp = any(x in fil_p for x in ["PEEK", "PEKK", "PEI", "Ultem", "PVDF"])
    frais_maintenance_base = 0.75 if est_haute_temp else (0.45 if est_abrasif else 0.15)
    
    col_maint1, col_maint2 = st.columns(2)
    with col_maint1: 
        # 📡 Récupération de l'amortissement injecté par le hub de flotte
        a_defaut = 0.25
        if "machine_active_data" in st.session_state and st.session_state["machine_active_data"]:
            a_defaut = st.session_state["machine_active_data"]["amortissement"]
            
        amortissement_horaire = st.number_input("Amortissement machine (CHF/h)", min_value=0.0, value=float(a_defaut), format="%.2f")
    with col_maint2: 
        maintenance_horaire = st.number_input("Frais d'usure prédictifs (CHF/h)", min_value=0.0, value=frais_maintenance_base)
        
    st.markdown("---")
    st.markdown("**Consommables d'atelier (Plaques PEI, Buses, Filtres HEPA/Charbon)**")
    col_cons1, col_cons2 = st.columns(2)
    with col_cons1:
        type_consommable = st.selectbox("Type d'équipement d'atelier usé :", ["Buse Standard Laiton", "Buse Acier Durci / ObXidian", "Kit filtration COV actif", "Revêtement Plaque PEI texturée"])
    with col_cons2:
        cout_cons_horaire = st.number_input("Forfait consommable (CHF/h)", min_value=0.0, value=0.10, format="%.2f")

# --- 5. LOGISTIQUE, MAIN D'ŒUVRE & RISQUES ---
with st.container(border=True):
    st.subheader("5. Logistique, Post-Traitement & Risques")
    col9, col10 = st.columns(2)
    with col9: h_preparation = st.number_input("Préparation, CAO & Slicing (Heures)", min_value=0.0, value=0.5, step=0.1)
    with col10: h_post_prod = st.number_input("Ébavurage & Post-traitement manuel (Heures)", min_value=0.0, value=0.5, step=0.1)
    
    taux_horaire = st.number_input("Tarif horaire de main-d'œuvre (CHF/h)", min_value=0.0, value=90.0)
    cout_quincaillerie = st.number_input("Fournitures complémentaires par pièce (Vis, inserts...)", min_value=0.0, value=5.0)
    
    st.markdown("---")
    st.markdown("**Sécurisation des risques d'impression**")
    risque_echec = st.slider("Taux d'échec statistique prédictif (%)", min_value=0, max_value=50, value=5, 
                             help="Anticipation des risques de décollement, warping ou coupures de courant sur les géométries complexes.")

# --- 6. PARAMÈTRES DE VENTE & EXPÉDITION ---
with st.container(border=True):
    st.subheader("6. Paramètres de Vente & Expédition (Poste CH)")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        marge_pourcent = st.slider("Marge bénéficiaire (%)", min_value=0, max_value=300, value=40)
    with col_v2:
        taxe_pourcent = st.number_input("TVA Suisse standard (%)", min_value=0.0, value=8.1, format="%.1f")
        
    st.markdown("---")
    st.markdown("**Options de livraison**")
    
    # Calcul automatique du poids du colis (Pièces + Pertes + 250g emballage carton)
    poids_brut_p = (poids_p * (1 + perte_p / 100)) * quantite_pieces
    poids_brut_s = (poids_s * (1 + loss_s / 100)) * quantite_pieces if activer_support else 0.0
    poids_colis_estime_g = poids_brut_p + poids_brut_s + 250.0
    
    if poids_colis_estime_g <= 250.0 and poids_p <= 50.0:
        index_recommande = 1 # Courrier A Petit
    elif poids_colis_estime_g <= 2250.0:
        index_recommande = 2 # PostPac B < 2kg
    else:
        index_recommande = 3 # PostPac B < 10kg
        
    st.caption(f"⚖️ Poids estimé du colis (avec emballage) : **{poids_colis_estime_g/1000:.3f} kg**")
    
    mode_envoi = st.selectbox(
        "Sélectionnez le mode de transport (Tranche recommandée pré-sélectionnée) :",
        [
            "Pas d'expédition (Retrait à l'atelier MAKERFAB)",
            "Courrier A - Petit colis (Moins de 250g, max 5cm) - CHF 2.40",
            "PostPac Standard B (2 à 3 jours) - Jusqu'à 2 kg - CHF 8.50",
            "PostPac Standard B (2 à 3 jours) - Jusqu'à 10 kg - CHF 11.50",
            "PostPac Priority A (Le lendemain) - Jusqu'à 2 kg - CHF 10.50",
            "PostPac Priority A (Le lendemain) - Jusqu'à 10 kg - CHF 13.50"
        ],
        index=index_recommande
    )

# Table de correspondance stricte des coûts de livraison
tarifs_poste = {
    "Pas d'expédition (Retrait à l'atelier MAKERFAB)": 0.0,
    "Courrier A - Petit colis (Moins de 250g, max 5cm) - CHF 2.40": 2.40,
    "PostPac Standard B (2 à 3 jours) - Jusqu'à 2 kg - CHF 8.50": 8.50,
    "PostPac Standard B (2 à 3 jours) - Jusqu'à 10 kg - CHF 11.50": 11.50,
    "PostPac Priority A (Le lendemain) - Jusqu'à 2 kg - CHF 10.50": 10.50,
    "PostPac Priority A (Le lendemain) - Jusqu'à 10 kg - CHF 13.50": 13.50
}
frais_port_net = tarifs_poste[mode_envoi]

# --- STOCKAGE TEMPORAIRE POUR TRANSMISSION ---
st.session_state["calcul_actif"] = {
    "nom_projet": nom_projet, "quantite_pieces": quantite_pieces, "fil_p": fil_p, "poids_p": poids_p,
    "perte_p": perte_p, "prix_p": prix_p, "activer_support": activer_support, "fil_s": fil_s, "poids_s": poids_s,
    "loss_s": loss_s, "prix_s": prix_s, "heures_impression": heures_impression, "prix_kwh_moyen": prix_kwh_moyen,
    "puissance_machine": puissance_machine, "cout_recuit_elec": cout_recuit_elec, "amortissement_horaire": amortissement_horaire,
    "maintenance_horaire": maintenance_horaire, "h_preparation": h_preparation, "h_post_prod": h_post_prod,
    "taux_horaire": taux_horaire, "cout_quincaillerie": cout_quincaillerie, "marge_pourcent": marge_pourcent, 
    "taxe_pourcent": taxe_pourcent, "frais_port_net": frais_port_net, "mode_envoi": mode_envoi,
    "client_nom": client_selectionne,
    "risque_echec": risque_echec,
    "cout_cons_horaire": cout_cons_horaire
}

st.markdown("---")
st.info("👉 **Données mémorisées.** Accédez au menu **'3_Analyses_&_Devis'** pour consulter votre devis révisé.")
