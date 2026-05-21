import streamlit as st
import plotly.graph_objects as go
import sqlite3
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Cost3D - Analyses & Devis", layout="centered", page_icon="📊")

# Style CSS spécial impression PDF
st.markdown("""
<style>
@media print { 
    header, [data-testid='stSidebar'], [data-testid='stHeader'], [data-testid='stDecoration'], iframe, button, .stButton, [data-testid='stExpander'], .stForm, .stMarkdown hr { display: none !important; } 
    body, .main, .block-container { background-color: white !important; color: black !important; padding: 0 !important; } 
    div[data-testid='stMetricValue'] { font-size: 28px !important; color: black !important; } 
    .print-only { display: block !important; } 
} 
.print-only { display: none; }
</style>
""", unsafe_allow_html=True)

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔒 Veuillez vous connecter sur la page d'Accueil avant d'accéder à ce menu.")
    st.stop()

if "calcul_actif" not in st.session_state:
    st.info("💡 Aucun calcul n'est actif. Veuillez d'abord configurer un projet dans le menu **'1_Saisie_&_Calcul'**.")
    st.stop()

# Extraction des données
c = st.session_state["calcul_actif"]

# ==================== LOGIQUE MATHÉMATIQUE AVEC FRAIS DE PORT ====================
poids_total_p = (c["poids_p"] * (1 + c["perte_p"] / 100)) * c["quantite_pieces"]
poids_total_s = (c["poids_s"] * (1 + c["loss_s"] / 100)) * c["quantite_pieces"] if c["activer_support"] else 0.0
total_poids_matiere_plateau = poids_total_p + poids_total_s

cout_fil_p = (c["prix_p"] / 1000) * poids_total_p
cout_fil_s = (c["prix_s"] / 1000) * poids_total_s if c["activer_support"] else 0.0

cout_electricite = ((c["puissance_machine"] / 1000) * c["heures_impression"] * c["prix_kwh_moyen"]) * c["quantite_pieces"]
cout_amortissement = (c["heures_impression"] * c["amortissement_horaire"]) * c["quantite_pieces"]
cout_maintenance = (c["heures_impression"] * c["maintenance_horaire"]) * c["quantite_pieces"]
cout_travail = (c["h_preparation"] + c["h_post_prod"]) * c["taux_horaire"] * c["quantite_pieces"]
cout_total_quincaillerie = c["cout_quincaillerie"] * c["quantite_pieces"]

# Coût de revient interne et prix de vente H.T. (hors livraison)
cout_revient_total = cout_fil_p + cout_fil_s + cout_electricite + (c["cout_recuit_elec"] * c["quantite_pieces"]) + cout_amortissement + cout_maintenance + cout_travail + cout_total_quincaillerie
prix_avec_marge_total = cout_revient_total * (1 + c["marge_pourcent"] / 100)

# Selon la loi suisse, les frais de port sont soumis au taux du bien principal
prix_total_hors_taxe_avec_port = prix_avec_marge_total + c["frais_port_net"]
prix_brut_tva_total = prix_total_hors_taxe_avec_port * (1 + c["taxe_pourcent"] / 100)

# Arrondi comptable suisse (5 centimes)
prix_vente_total_arrondi = round(prix_brut_tva_total * 20) / 20
benefice_net_total = prix_avec_marge_total - cout_revient_total

revient_unitaire = cout_revient_total / c["quantite_pieces"]
vente_unitaire_arrondi = round((prix_vente_total_arrondi / c["quantite_pieces"]) * 20) / 20
benefice_unitaire = benefice_net_total / c["quantite_pieces"]

# ==================== EN-TÊTE D'IMPRESSION ====================
st.html(f"""
<div class="print-only" style="border-bottom: 2px solid #1E1E24; padding-bottom: 15px; margin-bottom: 25px;">
    <h2 style="margin:0; color:#1E1E24;">PROPOSITION COMMERCIALE / DEVIS</h2>
    <p style="margin:5px 0 0 0; font-size:14px; color:#555;">Date d'édition : {datetime.now().strftime("%d.%m.%Y")} | Document généré via Cost3D Pro</p>
    <p style="margin:15px 0 0 0; font-size:16px;"><b>Référence Projet :</b> {c['nom_projet']}</p>
    <p style="margin:2px 0 0 0; font-size:16px;"><b>Série :</b> {c['quantite_pieces']} exemplaire(s) | <b>Matériau :</b> {c['fil_p']}</p>
    <p style="margin:2px 0 0 0; font-size:14px;"><b>Mode de livraison :</b> {c['mode_envoi']}</p>
</div>
""")

st.title("📊 Rapport Analytique & Devis")
st.markdown(f"#### Référence du calcul : **{c['nom_projet']}**")

if c["quantite_pieces"] > 1:
    st.markdown(f"##### 📦 Analyse de la série complète ({c['quantite_pieces']} pièces)")
    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1: st.metric("Coût de Revient Total", f"{cout_revient_total:.2f} CHF")
    with col_g2: st.metric("Bénéfice Net Total", f"{benefice_net_total:.2f} CHF")
    with col_g3: st.metric("Prix de Vente Final (Port & TVA incl.)", f"{prix_vente_total_arrondi:.2f} CHF")
    st.markdown("---")
    st.markdown("##### 🔍 Valeurs Unitaires (Par pièce, port inclus au prorata)")

col_m1, col_m2, col_m3 = st.columns(3)
with col_m1: st.metric("Coût de Revient / pc", f"{revient_unitaire:.2f} CHF")
with col_m2: st.metric("Bénéfice Net / pc", f"{benefice_unitaire:.2f} CHF")
with col_m3: st.metric("Prix de Vente / pc", f"{vente_unitaire_arrondi:.2f} CHF")

st.markdown("---")
act1, act2 = st.columns(2)
with act1:
    if st.button("💾 Enregistrer la tâche & déduire des stocks", use_container_width=True):
        conn = sqlite3.connect("projets_3d.db", check_same_thread=False)
        c_db = conn.cursor()
        date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        txt_filament = f"{c['fil_p']} / {c['fil_s']}" if c["activer_support"] else c["fil_p"]
        
        c_db.execute("""INSERT INTO projets (date, nom, filament, cout_revient, prix_vente, poids_total) 
                        VALUES (?, ?, ?, ?, ?, ?)""", 
                     (date_str, c['nom_projet'], txt_filament, cout_revient_total, prix_vente_total_arrondi, total_poids_matiere_plateau))
        
        # 🟢 ICI LE DÉTAIL 2 INTÉGRÉ : Déduction intelligente de la bobine entamée disponible
        poids_deduction_p = poids_total_p + 10
        c_db.execute("""UPDATE stocks SET poids_restant = MAX(0, poids_restant - ?) 
                        WHERE id = (SELECT id FROM stocks WHERE type_filament = ? AND poids_restant > 0 ORDER BY id ASC LIMIT 1)""", 
                     (poids_deduction_p, c['fil_p']))
        
        if c["activer_support"]:
            c_db.execute("""UPDATE stocks SET poids_restant = MAX(0, poids_restant - ?) 
                            WHERE id = (SELECT id FROM stocks WHERE type_filament = ? AND poids_restant > 0 ORDER BY id ASC LIMIT 1)""", 
                         (poids_total_s, c['fil_s']))
            
        conn.commit()
        conn.close()
        st.toast("✅ Projet archivé et inventaire ajusté !", icon="💾")

with act2:
    st.html('<button onclick="window.print()" style="width:100%; height:38px; background-color:#1E1E24; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">🖨️ Générer la facture PDF</button>')

st.markdown("---")

# --- GRAPHIQUE PLOTLY ---
palette_couleurs = ['#FF4B4B', '#992222', '#1E1E24', '#4E4E5A', '#8E8E9A', '#C2C2CD', '#E2E2EA']
categories = ['Filament Principal', 'Filament Support', 'Énergie Globale', 'Amortissement', 'Maintenance', 'Main d\'œuvre', 'Fournitures']
valeurs = [cout_fil_p, cout_fil_s, (cout_electricite + (c["cout_recuit_elec"] * c["quantite_pieces"])), cout_amortissement, cout_maintenance, cout_travail, cout_total_quincaillerie]

fig = go.Figure(data=[go.Pie(labels=categories, values=valeurs, hole=.5, textinfo='percent', marker=dict(colors=palette_couleurs))])
fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
st.plotly_chart(fig, use_container_width=True)

# --- TABLEAU DE FACTURATION COMMERCIALE ---
st.html(f"""
<div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #FF4B4B; margin-top: 25px;">
    <h4 style="margin-top:0; color:#1E1E24;">🧾 Bordereau de Facturation Détaillé (Normes CH)</h4>
    <table style="width: 100%; font-size: 15px; border-collapse: collapse;">
        <tr style="border-bottom: 1px solid #ddd; height: 35px;">
            <td><b>Poste de coût</b></td>
            <td style="text-align: right;"><b>Montant Global ({c['quantite_pieces']} pc)</b></td>
        </tr>
        <tr style="height: 30px;">
            <td>• Matière Première principale ({c['fil_p']})</td>
            <td style="text-align: right;">{cout_fil_p:.2f} CHF</td>
        </tr>
        <tr style="height: 30px;">
            <td>• Matière Première support ({c['fil_s']})</td>
            <td style="text-align: right;">{cout_fil_s:.2f} CHF</td>
        </tr>
        <tr style="height: 30px;">
            <td>• Énergie active (Impression & Recuit)</td>
            <td style="text-align: right;">{(cout_electricite + (c['cout_recuit_elec'] * c['quantite_pieces'])):.2f} CHF</td>
        </tr>
        <tr style="height: 30px;">
            <td>• Amortissement machine et usure</td>
            <td style="text-align: right;">{cout_amortissement:.2f} CHF</td>
        </tr>
        <tr style="height: 30px;">
            <td>• Maintenance prédictive d'atelier</td>
            <td style="text-align: right;">{cout_maintenance:.2f} CHF</td>
        </tr>
        <tr style="height: 30px;">
            <td>• Main d'œuvre qualifiée (CAO + Post-prod)</td>
            <td style="text-align: right;">{cout_travail:.2f} CHF</td>
        </tr>
        <tr style="height: 30px; border-bottom: 1px solid #eee;">
            <td>• Fournitures logistiques et inserts quincaillerie</td>
            <td style="text-align: right;">{cout_total_quincaillerie:.2f} CHF</td>
        </tr>
        <tr style="height: 35px;">
            <td><b>COÛT DE REVIENT TOTAL INTERNE H.T.</b></td>
            <td style="text-align: right;"><b>{cout_revient_total:.2f} CHF</b></td>
        </tr>
        <tr style="height: 30px; color: #555;">
            <td>• Marge commerciale d'atelier appliquée ({c['marge_pourcent']}%)</td>
            <td style="text-align: right;">{prix_avec_marge_total - cout_revient_total:.2f} CHF</td>
        </tr>
        <tr style="height: 30px; color: #008631; border-bottom: 2px dashed #ccc;">
            <td>• Frais d'expédition ({c['mode_envoi'].split(' - ')[0]})</td>
            <td style="text-align: right;">{c['frais_port_net']:.2f} CHF</td>
        </tr>
        <tr style="height: 30px; color: #555;">
            <td>• TVA Suisse réglementaire ({c['taxe_pourcent']}%) sur total facture</td>
            <td style="text-align: right;">{prix_brut_tva_total - prix_total_hors_taxe_avec_port:.2f} CHF</td>
        </tr>
        <tr style="height: 40px; font-size: 18px; border-top: 2px solid #1E1E24; color: #FF4B4B;">
            <td><b>PRIX DE VENTE TOTAL FINAL (Arrondi 5 cts)</b></td>
            <td style="text-align: right;"><b>{prix_vente_total_arrondi:.2f} CHF</b></td>
        </tr>
    </table>
</div>
""")
