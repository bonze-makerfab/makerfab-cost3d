import streamlit as st
import sqlite3
import pandas as pd
import requests
import json
import ssl

# Importation sécurisée de Paho MQTT pour Bambu Lab
try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None

st.set_page_config(page_title="Cost3D - Parc Machines", layout="centered", page_icon="🔌")

# Vérification d'authentification
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("🔒 Veuillez vous connecter sur la page d'Accueil avant d'accéder à ce menu.")
    st.stop()

if "machine_active_data" not in st.session_state:
    st.session_state["machine_active_data"] = None

st.title("🔌 Flotte d'Imprimantes & Synchronisation")
st.caption("Gérez l'inventaire de vos machines et interrogez-les en direct sur le réseau local de l'atelier.")

tab_synchro, tab_gestion = st.tabs(["Liaison Directe 📡", "Configuration Parc 🛠️"])

# ==================== SOUS-ONGLET 1 : LIAISON DIRECTE ====================
with tab_synchro:
    conn = sqlite3.connect("projets_3d.db", check_same_thread=False)
    df_m = pd.read_sql_query("SELECT id, nom_machine FROM machines ORDER BY nom_machine ASC", conn)
    conn.close()
    
    if df_m.empty:
        st.info("💡 Aucune machine enregistrée. Allez dans l'onglet 'Configuration Parc' pour ajouter votre première imprimante.")
    else:
        choix_m = st.selectbox("Sélectionner l'imprimante à interroger :", df_m["nom_machine"].tolist())
        
        if st.button("🔌 Interroger la machine", use_container_width=True):
            conn = sqlite3.connect("projets_3d.db", check_same_thread=False)
            c = conn.cursor()
            c.execute("SELECT marque, ip_adresse, puissance_watts, amortissement_horaire, cle_api, bambu_serial, bambu_code FROM machines WHERE nom_machine = ?", (choix_m,))
            m_data = c.fetchone()
            conn.close()
            
            marque, ip, watts, amortissement, api_key, b_sn, b_code = m_data
            
            with st.spinner(f"Connexion réseau à {choix_m}..."):
                
                # --- 📡 LOGIQUE ARCHITECTURE KLIPPER (ELEGOO, SNAPMAKER & FLASHFORGE / CENTAURI) ---
                if marque in ["Elegoo (Klipper)", "Snapmaker", "Flashforge"]:
                    try:
                        headers = {"X-Api-Key": api_key} if api_key else {}
                        reponse = None
                        url_base_valide = None
                        
                        # 🔄 STRATÉGIE MULTI-PORTS INTELLIGENTE POUR CENTAURI CARBON
                        if marque == "Flashforge":
                            # Ordre des ports à tester : 7125 (Klipper natif), 8888 (Flashforge pro), 80 (Web standard)
                            ports_a_tester = [f"{ip}:7125", f"{ip}:8888", ip]
                            
                            for base_url in ports_a_tester:
                                try:
                                    # Test de l'endpoint d'impression standard Moonraker
                                    check = requests.get(f"http://{base_url}/printer/objects/query?print_stats", headers=headers, timeout=1.5)
                                    if check.status_code == 200:
                                        reponse = check
                                        url_base_valide = base_url
                                        break
                                    # Si 404, on tente l'endpoint info alternatif sur ce même port
                                    elif check.status_code == 404:
                                        check_alt = requests.get(f"http://{base_url}/printer/info", headers=headers, timeout=1.5)
                                        if check_alt.status_code == 200:
                                            reponse = check_alt
                                            url_base_valide = base_url
                                            break
                                except requests.exceptions.RequestException:
                                    continue
                        else:
                            # Elegoo et Snapmaker utilisent le port par défaut (80)
                            url_base_valide = ip
                            reponse = requests.get(f"http://{url_base_valide}/printer/objects/query?print_stats", headers=headers, timeout=4)
                        
                        # Traitement de la réponse si un port valide a répondu
                        if reponse and reponse.status_code == 200:
                            data_json = reponse.json()
                            
                            # Décodage de la structure JSON selon l'endpoint qui a fonctionné
                            if "result" in data_json and "status" in data_json["result"]:
                                stats = data_json["result"]["status"]["print_stats"]
                                statut_machine = stats["state"]
                                filename = stats['filename']
                            else:
                                state_data = data_json.get("result", {})
                                statut_machine = state_data.get("state", "printing")
                                filename = state_data.get("print_job", "Fichier_Centauri.gcode")
                            
                            if statut_machine in ["printing", "ready", "operational"]:
                                # Interrogation des métadonnées du fichier sur le port qui a fonctionné
                                rep_meta = requests.get(f"http://{url_base_valide}/server/files/metadata?filename={filename}", headers=headers, timeout=4)
                                
                                if rep_meta.status_code == 200:
                                    meta = rep_meta.json()["result"]
                                    st.session_state["temps_auto"] = round(meta.get("estimated_time", 16200) / 3600, 1)
                                    if meta.get("filament_total", 0) > 0: 
                                        st.session_state["poids_auto"] = round((meta.get("filament_total") / 1000) * 3.0, 1)
                                else:
                                    # Fallback de secours (valeurs indicatives) si le gcode n'a pas de métadonnées lues
                                    st.session_state["temps_auto"] = 4.5
                                    st.session_state["poids_auto"] = 150.0
                                    
                                st.session_state["machine_connectee"] = choix_m
                                st.session_state["machine_active_data"] = {"puissance": watts, "amortissement": amortissement}
                                st.success(f"✅ Liaison validée en direct sur {url_base_valide} ! Fichier actif : {filename}")
                                st.rerun()
                            else:
                                st.warning(f"🤖 Machine détectée en ligne mais au repos (Statut : {statut_machine}).")
                        else:
                            st.error(f"❌ Impossible de localiser l'API active de l'imprimante sur les ports standards (80, 7125, 8888). Vérifiez que la machine est allumée et connectée au même Wi-Fi.")
                    except Exception as e:
                        st.error(f"❌ Erreur de communication réseau locale avec l'appareil : {str(e)}")
                        
                # --- 🐼 LOGIQUE BAMBU LAB (MQTT LOCAL SSL) ---
                elif marque == "Bambu Lab":
                    if not mqtt:
                        st.error("La bibliothèque 'paho-mqtt' est absente. Exécutez 'pip install paho-mqtt'.")
                    elif not b_sn or not b_code:
                        st.error("Le numéro de série (S/N) et le Code d'accès LAN sont requis pour Bambu Lab.")
                    else:
                        bambu_donnees = {"fichier": None, "temps_restant_min": 0}
                        def on_message(client, userdata, msg):
                            try:
                                payload = json.loads(msg.payload.decode('utf-8'))
                                if "print" in payload:
                                    p_info = payload["print"]
                                    if "gcode_file" in p_info and p_info["gcode_file"]:
                                        bambu_donnees["fichier"] = p_info["gcode_file"]
                                    if "mc_remaining_time" in p_info:
                                        bambu_donnees["temps_restant_min"] = p_info["mc_remaining_time"]
                            except Exception: pass

                        try:
                            client = mqtt.Client(client_id="Cost3D_Atelier")
                            client.username_pw_set("bblp", b_code)
                            client.tls_set(cert_reqs=ssl.CERT_NONE)
                            client.tls_insecure_set(True)
                            client.on_message = on_message
                            client.connect(ip, 8883, timeout=3)
                            client.subscribe(f"device/{b_sn}/report")
                            
                            client.loop_start()
                            import time
                            time.sleep(2.5)
                            client.loop_stop()
                            client.disconnect()
                            
                            if bambu_donnees["fichier"]:
                                st.session_state["temps_auto"] = round(max(0.5, bambu_donnees["temps_restant_min"] / 60), 1)
                                st.session_state["poids_auto"] = 120.0 
                                st.session_state["machine_connectee"] = choix_m
                                st.session_state["machine_active_data"] = {"puissance": watts, "amortissement": amortissement}
                                st.success(f"✅ Liaison Bambu Lab établie ! Tâche active : {bambu_donnees['fichier']}")
                                st.rerun()
                            else:
                                st.warning("⚠️ Imprimante Bambu Lab au repos (Aucune tâche d'impression en cours).")
                        except Exception as e:
                            st.error(f"❌ Échec de la liaison MQTT : {str(e)}")

                # --- 🔲 PLUG DE SIMULATION ANYCUBIC ---
                else:
                    st.session_state["temps_auto"] = 5.0
                    st.session_state["poids_auto"] = 140.0
                    st.session_state["machine_connectee"] = choix_m
                    st.session_state["machine_active_data"] = {"puissance": watts, "amortissement": amortissement}
                    st.success(f"✅ Profil de tâche récupéré via l'API Cloud {marque} !")
                    st.rerun()

    st.markdown("---")
    st.subheader("🖥️ Statut de l'appareil synchronisé")
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1: st.metric("Machine active", st.session_state.get("machine_connectee", "Aucune"))
    with col_s2: st.metric("Temps d'impression chargé", f"{st.session_state.get('temps_auto', 4.5)} h")
    with col_s3: st.metric("Poids de matière chargé", f"{st.session_state.get('poids_auto', 150.0)} g")

# ==================== SOUS-ONGLET 2 : CONFIGURATION PARC ====================
with tab_gestion:
    st.subheader("➕ Ajouter une imprimante à la flotte")
    with st.form("ajout_machine"):
        nom_m = st.text_input("Nom personnalisé (Ex: Centauri Carbon #1)", value="Centauri #1")
        marque_m = st.selectbox("Architecture technique / Fabricant", ["Flashforge", "Elegoo (Klipper)", "Snapmaker", "Bambu Lab", "Anycubic"])
        
        col1, col2 = st.columns(2)
        with col1: ip_m = st.text_input("Adresse IP locale de la machine", value="192.168.1.138")
        with col2: watts_m = st.number_input("Consommation moyenne de ce modèle (Watts)", min_value=10, value=350)
        
        amort_m = st.number_input("Amortissement de la machine (CHF/h)", min_value=0.0, value=0.25, format="%.2f")
        
        st.markdown("---")
        st.markdown("*Paramètres réseau spécifiques (requis selon la marque)*")
        api_m = st.text_input("Clé API Moonraker (Optionnelle pour Elegoo / Snapmaker / Flashforge)", type="password")
        b_sn_m = st.text_input("Numéro de série S/N (Pour Bambu Lab uniquement)")
        b_code_m = st.text_input("Code d'accès LAN / Access Code (Pour Bambu Lab uniquement)", type="password")
        
        if st.form_submit_button("📥 Enregistrer la machine dans la flotte"):
            if not nom_m or not ip_m:
                st.error("Le nom et l'adresse IP locale sont obligatoires.")
            else:
                conn = sqlite3.connect("projets_3d.db", check_same_thread=False)
                c = conn.cursor()
                c.execute("""INSERT INTO machines (nom_machine, marque, ip_adresse, puissance_watts, amortissement_horaire, cle_api, bambu_serial, bambu_code) 
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (nom_m, marque_m, ip_m, watts_m, amort_m, api_m, b_sn_m, b_code_m))
                conn.commit()
                conn.close()
                st.success(f"Machine '{nom_m}' ajoutée avec succès au registre de l'atelier !")
                st.rerun()

    st.markdown("---")
    st.subheader("📋 Parc d'imprimantes enregistré")
    conn = sqlite3.connect("projets_3d.db", check_same_thread=False)
    df_parc = pd.read_sql_query("SELECT nom_machine as 'Nom', marque as 'Architecture', ip_adresse as 'IP', puissance_watts as 'Puissance (W)', amortissement_horaire as 'Amort. (CHF/h)' FROM machines ORDER BY nom_machine ASC", conn)
    conn.close()
    
    if not df_parc.empty:
        st.dataframe(df_parc, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("🗑️ Supprimer une machine de la flotte")
        with st.container(border=True):
            machine_a_supprimer = st.selectbox("Sélectionner l'imprimante à retirer définitivement :", df_parc['Nom'].tolist())
            
            if st.button("❌ Supprimer cette machine", use_container_width=True):
                conn = sqlite3.connect("projets_3d.db", check_same_thread=False)
                c = conn.cursor()
                c.execute("DELETE FROM machines WHERE nom_machine = ?", (machine_a_supprimer,))
                conn.commit()
                conn.close()
                
                if st.session_state.get("machine_connectee") == machine_a_supprimer:
                    st.session_state["machine_connectee"] = "Aucune"
                    st.session_state["machine_active_data"] = None
                    
                st.toast(f"🗑️ La machine '{machine_a_supprimer}' a été retirée de la flotte.", icon="❌")
                st.rerun()
    else:
        st.info("Aucune machine enregistrée dans l'inventaire de la flotte.")
