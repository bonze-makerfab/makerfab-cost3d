# 🖨️ MAKERFAB Cost3D — ERP Multi-Machines pour Atelier d'Impression 3D

**MAKERFAB Cost3D** est un système ERP (Enterprise Resource Planning) modulaire, moderne et léger, développé en Python avec le framework Streamlit. Conçu spécifiquement pour la gestion d'un atelier de fabrication additive ou d'une ferme d'impression 3D en Suisse, cet outil centralise le chiffrage commercial, le suivi des stocks, la facturation réglementaire et la rentabilité financière.

---

## 🚀 Fonctionnalités principales

### 📝 1. Saisie de projet & Chiffrage analytique
*   **Moteur de calcul complet** : Prise en compte exhaustive de la matière principale, des filaments de support, des taux de perte techniques, de l'amortissement horaire machine, de la quincaillerie (vis, inserts) et du temps de main-d'œuvre (CAO, slicing, post-traitement).
*   **Énergie dynamique** : Gestion de la consommation électrique de l'atelier basée sur une répartition personnalisable des tarifs de l'électricité (Heures Pleines / Heures Creuses) et prise en charge de l'énergie nécessaire au recuit thermique (*annealing*).
*   **Maintenance prédictive** : Ajustement automatique et prédictif des frais d'usure des buses et de l'extrudeur selon l'abrasivité (ex: filaments carbone -CF, fibre de verre -GF, bois, métaux, phosphorescents) ou la température du polymère sélectionné (ex: PEEK, Ultem).

### 🔌 2. Hub de connexion Multi-Machines
*   **Interrogation réseau en temps réel** : Liaison en direct avec l'imprimante 3D active dans l'atelier pour importer instantanément le fichier en cours, le temps restant estimé et le poids précis du modèle.
*   **Compatibilité multi-constructeurs** :
    *   *Écosystèmes Moonraker/Klipper* : Intégration HTTP native pour les machines **Elegoo** et **Snapmaker**.
    *   *Protocoles locaux & Cloud* : Points d'ancrage structurés pour **Bambu Lab (MQTT Local/AMS)**, **Anycubic** et **Flashforge**.

### 📊 3. Proposition commerciale, TVA & Logistique CH
*   **Intégration de la Poste Suisse** : Calculateur logistique automatique qui évalue le poids du colis (pièces + emballage) pour pré-sélectionner la tranche tarifaire exacte (Courrier A, PostPac Standard B ou Priority A, <2kg ou <10kg).
*   **Normes comptables suisses** : Application automatique du taux de TVA à 8.1% (les frais d'expédition suivent légalement le taux de TVA du bien principal) et formule d'arrondi comptable stricte à 5 centimes (0.05).
*   **Édition de facture PDF** : Feuille de style CSS intégrée permettant d'utiliser la fonction d'impression native (`window.print()`) pour générer instantanément un devis ou une facture propre, expurgée de toute interface logicielle.

### 📦 4. Gestion dynamique des stocks
*   **Inventaire par fabricant** : Base de données pré-configurée intégrant les marques courantes ainsi que les filaments industriels haut de gamme (ex: *Polymaker*, *BASF Forward AM*, *3DXTECH*, *Kimya*, etc.).
*   **Déduction intelligente** : Algorithme SQL qui cible et déduit le plastique consommé en priorité sur la bobine entamée en cours d'utilisation dans l'atelier (`poids_restant > 0`).
*   **Alertes de rupture** : Notification visuelle immédiate à l'équipe dès qu'une bobine passe sous le seuil critique des 150g.

### 📂 5. Archives & Dashboard de rentabilité
*   **Indicateurs clés (KPI)** : Visualisation du Chiffre d'Affaires cumulé, de la marge nette globale de l'atelier, de l'efficacité financière de la production et de la masse totale de plastique consommée (en Kg).
*   **Journal comptable** : Historique complet modifiable avec fonction d'exportation en un clic au format CSV compatible Microsoft Excel.

---

## 📁 Architecture modulaire du projet

L'application utilise l'architecture multi-pages native de Streamlit. Cette structure isole le code par tâche, améliore drastiquement la vitesse d'exécution et évite les conflits réseau :

```text
├── 🏠 Accueil.py             # Hub central, initialisation DB et sécurité
├── 📁 .streamlit/
│   └── 📄 secrets.toml       # Coffre-fort pour le mot de passe d'atelier (en local)
├── 📁 pages/
│   ├── 1_📝_Saisie_&_Calcul.py      # Configuration des pièces et de la main-d'œuvre
│   ├── 2_🔌_Connexion_Machines.py  # Hub d'interrogation réseau des imprimantes
│   ├── 3_📊_Analyses_&_Devis.py     # Graphiques Plotly, calculs TVA et bordereau d'impression
│   ├── 4_📦_Gestion_des_Stocks.py   # Entrée des bobines, filtres marques et alertes <150g
│   └── 5_📂_Tableau_de_Bord.py     # Indicateurs de performance financiers et exports CSV
├── 📄 filaments.json         # Catalogue des prix et taux de perte par plastique (PLA, ASA, PEEK...)
├── 📄 marques.txt            # Liste ordonnée des fabricants de filaments de l'atelier
└── 🗄️ projets_3d.db          # Base de données relationnelle locale SQLite
```

---

## 🛠️ Installation et lancement sous Windows

### Prérequis
1. Disposer de **Python 3.10** ou supérieur.
2. Avoir installé **Git** sur votre machine.

### 1. Clonage et installation des dépendances
Ouvrez votre terminal (PowerShell) et exécutez :
```powershell
git clone https://github.com
cd makerfab-cost3d
pip install streamlit plotly pandas requests
```

### 2. Premier lancement local
Assurez-vous d'avoir créé le fichier `.streamlit/secrets.toml` contenant votre mot de passe d'atelier, puis lancez le serveur :
```powershell
streamlit run Accueil.py
```
L'interface s'ouvre à l'adresse locale `http://localhost:8501`. Utilisez le mot de passe configuré (ou `admin3d` par défaut) pour déverrouiller l'accès.

---
💡 *Développé pour l'atelier MAKERFAB. Modifiable et extensible pour toute infrastructure d'impression 3D.*
