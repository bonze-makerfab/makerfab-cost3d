# ==============================================================================
# SCRIPT DE DÉPLOIEMENT GITHUB WINDOWS - MAKERFAB Cost3D
# ==============================================================================

Write-Host "🤖 Préparation du déploiement Windows pour l'ERP MAKERFAB Cost3D..." -ForegroundColor Cyan

# 1. Création automatique du fichier .gitignore si absent
if (-not (Test-Path .gitignore)) {
    Write-Host "📝 Création du fichier .gitignore pour protéger vos données sensibles..." -ForegroundColor Yellow
    $gitignoreContent = @"
# Base de données locale (Contient vos devis et stocks réels)
*.db
*.db-journal

# Secrets et mots de passe d'atelier
.streamlit/secrets.toml

# Fichiers temporaires Python et caches
__pycache__/
*.pyc
.ipynb_checkpoints/
.streamlit/config.toml
"@
    Set-Content -Path .gitignore -Value $gitignoreContent -Encoding utf8
    Write-Host "✅ Fichier .gitignore créé avec succès." -ForegroundColor Green
} else {
    Write-Host "ℹ️ Fichier .gitignore déjà présent. Étape sautée." -ForegroundColor Gray
}

# 2. Demande de l'URL du dépôt GitHub à l'utilisateur
Write-Host "------------------------------------------------------------------------------" -ForegroundColor Gray
$GITHUB_URL = Read-Host "https://github.com/bonze-makerfab/makerfab-cost3d.git"

if ([string]::IsNullOrWhiteSpace($GITHUB_URL)) {
    Write-Host "❌ Erreur : L'URL GitHub ne peut pas être vide. Script interrompu." -ForegroundColor Red
    Exit
}

# 3. Exécution des commandes Git
Write-Host "------------------------------------------------------------------------------" -ForegroundColor Gray
Write-Host "📦 Initialisation du dépôt Git local..." -ForegroundColor Cyan
git init

Write-Host "🔍 Indexation des fichiers de l'application..." -ForegroundColor Cyan
git add .

Write-Host "💾 Création du premier point de sauvegarde (Commit)..." -ForegroundColor Cyan
git commit -m "Initial release: MAKERFAB Cost3D ERP Multi-pages"

Write-Host "🔗 Liaison avec le serveur distant GitHub..." -ForegroundColor Cyan
# Supprime l'ancienne liaison 'origin' si elle existe pour éviter les conflits
git remote remove origin 2>$null
git remote add origin $GITHUB_URL

Write-Host "🚀 Envoi des fichiers vers la branche principale (main)..." -ForegroundColor Cyan
git branch -M main
git push -u origin main

# 4. Fin de la procédure
Write-Host "------------------------------------------------------------------------------" -ForegroundColor Gray
Write-Host "🎉 Terminé ! Votre code Windows est sécurisé en ligne sur GitHub." -ForegroundColor Green
Write-Host "🌐 Vous pouvez maintenant connecter votre dépôt sur share.streamlit.io." -ForegroundColor Yellow
