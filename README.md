# Gradient Academy

Application web pédagogique en français pour apprendre le gradient depuis les bases jusqu'à ses applications en IA. Stack : Flask, SQLite, HTML/CSS/JavaScript sans compilation front-end.

## Fonctionnalités
- Tableau de bord responsive et 10 modules progressifs.
- Séances à une question à la fois, feedback et réessais.
- Sauvegarde SQLite des réponses, scores, historique et compétences.
- Analyse locale de secours sans API externe ; analyse de réponses libres via API compatible OpenAI en option.
- Rapport global consultable, imprimable/enregistrable en PDF depuis le navigateur et exportable en JSON.
- Certificat de parcours imprimable, avec critères de validation visibles.

## Lancer sous Windows
1. Installer Python 3.10 ou plus récent.
2. Extraire le ZIP.
3. Ouvrir PowerShell dans le dossier `gradient_academy`.
4. Exécuter :

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

5. Ouvrir http://127.0.0.1:5000 dans le navigateur.

## Lancer sous macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Puis ouvrir http://127.0.0.1:5000.

## Activer l'analyse IA
Sans clé API, l'application utilise des règles pédagogiques locales et continue de fonctionner. Pour activer l'analyse sémantique des réponses libres, définis ces variables d'environnement avant de lancer l'application :

- `OPENAI_API_KEY` : clé API du fournisseur choisi.
- `OPENAI_BASE_URL` : URL de base compatible avec `/chat/completions`.
- `OPENAI_MODEL` : nom du modèle accessible avec cette clé.

Exemple PowerShell pour la session en cours :

```powershell
$env:OPENAI_API_KEY="ta-cle-api"
$env:OPENAI_MODEL="gpt-4o-mini"
python app.py
```

Ne publie jamais ta clé API dans le code, le dépôt ou une capture d'écran. Les frais d'API éventuels dépendent du fournisseur et de ton compte. Cette application ne contient aucune clé par défaut.

## Données et rapports
La base `gradient_academy.db` est créée automatiquement au premier lancement dans le dossier de l'application. Elle conserve le profil local, les tentatives et la progression. Pour sauvegarder les données, arrête le serveur puis copie ce fichier. Le rapport est disponible dans le menu « Rapport global », avec export JSON et impression/enregistrement en PDF.

Le certificat de réussite est disponible après validation de tous les modules (au moins 7/10 de moyenne sur les exercices de chaque module). Il atteste de l'achèvement dans l'application, pas d'un diplôme ou d'une accréditation officielle.

## Limites connues / prochaines améliorations
- Le moteur de validation local est volontairement simple ; une évaluation sémantique fiable des réponses libres nécessite de configurer une API IA.
- Le profil est local au navigateur/session ; ce premier build n'inclut pas de comptes multi-utilisateurs avec authentification.
- Le programme de cours est un socle pédagogique à enrichir par des exercices de validation plus nombreux, notamment pour les modules avancés.
- Pour une mise en production publique, ajouter authentification, protection CSRF, limitation de débit, gestion des secrets et sauvegardes sécurisées.


## Déploiement sur Render

Le dépôt contient `render.yaml` pour configurer le service web, Gunicorn, le contrôle de santé et un disque persistant SQLite.

1. Publie le dossier `gradient_academy` dans un dépôt GitHub auquel tu as accès.
2. Dans Render, choisis **New + → Blueprint**, puis connecte ce dépôt.
3. Render détecte `render.yaml` et configure le service. Vérifie le plan et le disque persistant avant de confirmer : un disque persistant Render nécessite un plan compatible et peut entraîner des frais.
4. Après création, ouvre **Environment** et ajoute `OPENAI_API_KEY` si tu veux activer l'analyse IA. Ne mets jamais cette clé dans Git ou dans le code.
5. Attends que le déploiement soit terminé, puis teste `/api/health`, `/`, `/report` et `/certificate`.

Important : cette version ne possède pas de comptes utilisateurs ni d'authentification. Le stockage SQLite est persistant grâce au disque configuré, mais le profil est associé à un navigateur/session ; ce n'est pas encore une plateforme multi-utilisateurs sécurisée pour des données sensibles.
