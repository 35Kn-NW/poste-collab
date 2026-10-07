# IA métier sur le poste — architecture et contrat du connecteur

_Version du contrat : `poste/v1` · agent `poste-ia` 0.2.0 (Linux)_

L'IA métier de l'étude tourne sur des **serveurs distants**. Le poste n'embarque aucun modèle : il embarque un **agent** qui rend l'IA présente partout dans le bureau et lui donne un accès **contrôlé** au poste. Le lien entre les deux est le **connecteur**, décrit ici pour que le serveur puisse l'implémenter le moment venu.

## 1. Vue d'ensemble

```
 Serveurs de l'IA métier (distants)                 Poste du collaborateur
 ┌──────────────────────────────┐   HTTPS (jeton)   ┌───────────────────────────────────────────┐
 │  /poste/v1/briefing          │◄──────────────────│ agent poste-ia (session de l'utilisateur)  │
 │  /poste/v1/conversation (SSE)│◄──────────────────│  ├─ briefing à l'ouverture de session       │
 │  /poste/v1/outils/*          │◄─ appels d'outils ─│  ├─ panneau Super+Espace                    │
 │  /poste/v1/sceller           │                   │  ├─ recherche GNOME, clic droit Fichiers    │
 └──────────────────────────────┘                   │  ├─ rappels de rendez-vous                  │
                                                    │  └─ moteur d'outils : périmètre, niveaux,   │
                                                    │     confirmation, journal, arrêt d'urgence  │
                                                    └───────────────────────────────────────────┘
```

- **Toujours à l'initiative du poste** : l'agent ouvre toutes les connexions (HTTPS sortant). Aucun port n'est ouvert sur le poste, aucune connexion entrante.
- **Sans connecteur configuré**, tout fonctionne en local : briefing à partir de l'agenda Evolution et des tâches personnelles, avec la mention « IA métier non connectée ».

## 2. Ce que voit le collaborateur

| Surface | Déclencheur | Contenu |
|---|---|---|
| **Briefing « Votre journée »** | Ouverture de session | Synthèse, vue d'ensemble chiffrée, rendez-vous, à faire, points à vérifier, échéances à 7 jours ; ajout et coche des tâches personnelles |
| **Panneau IA métier** | `Super+Espace`, dock | Conversation en flux, journal des actions de l'IA, arrêt d'urgence |
| **Recherche GNOME** | Touche `Super` puis saisie | Éléments du briefing correspondants, et « Demander à l'IA métier » |
| **Clic droit dans Fichiers** | Sur un ou plusieurs documents | Résumer, Vérifier cet acte, Préparer la réponse au client, Sceller (horodatage) |
| **Notifications** | 15 min avant un rendez-vous ; actions de l'IA | Rappel ; information sur chaque action de niveau « agir » |

## 3. Sécurité : trois niveaux d'autorisation

| Niveau | Outils | Règle |
|---|---|---|
| **Lire** | `fichiers_lister`, `fichiers_chercher`, `fichier_lire` | Libre, **dans le périmètre** : dossier personnel, sans éléments cachés (`.ssh`, `.config`, trousseaux…), liens symboliques résolus |
| **Agir** | `brouillon_ecrire`, `courriel_preparer`, `ouvrir`, `notifier` | Réversible et **signalé** par une notification. Aucun envoi : le courriel est préparé, le collaborateur l'envoie lui-même |
| **Engager** | `document_sceller` | **Confirmation explicite à chaque fois** (fenêtre « Autoriser / Refuser ») |

- **Journal** de chaque demande (outil, niveau, arguments abrégés, décision) dans `~/.local/state/poste-ia/journal.jsonl`, consultable depuis le panneau.
- **Arrêt d'urgence** : par l'utilisateur (panneau, `poste-ia arret`) ou par l'administrateur pour tout le poste (`/etc/poste-collab/poste-ia.arret`). Plus aucun outil n'est exécuté.
- **Signature REAL : jamais** exposée comme outil.
- **Jeton** du connecteur dans le **trousseau du système**, jamais dans un fichier en clair (`poste-ia jeton`).
- **Autorité de certification** du serveur, si elle est privée : reconnue pour cette seule connexion (`ia_connecteur_ca`), **jamais installée comme racine** du poste.
- **Injection de consignes** : le contenu des documents et des courriels lus par l'IA reste une donnée ; toute action qui engage l'étude passe par la confirmation humaine, quelle que soit la demande.

## 4. Contrat du connecteur `poste/v1`

Base : `{ia_connecteur_url}/poste/v1`. Toutes les requêtes portent `Authorization: Bearer <jeton du poste>` et `User-Agent: poste-ia/<version>`. Corps et réponses en JSON UTF-8 ; dates et heures en ISO 8601 (heure locale, ou avec fuseau).

### 4.1 `GET /briefing?date=AAAA-MM-JJ`

Vision globale de la journée du collaborateur, préparée par l'IA.

```json
{
  "synthese": "Trois signatures aujourd'hui, dont la vente Dupont à 10 h. Le diagnostic amiante du dossier Martin manque toujours.",
  "indicateurs": { "Dossiers en cours": 42, "Signatures cette semaine": 7 },
  "rendez_vous": [
    { "id": "r1", "titre": "Signature vente Dupont", "debut": "2026-10-07T10:00:00",
      "fin": "2026-10-07T11:00:00", "detail": "Salle des signatures", "lien": "https://exemple" }
  ],
  "a_faire":    [ { "id": "t1", "titre": "Relire le projet d'acte Martin", "priorite": "haute", "echeance": "2026-10-07" } ],
  "a_verifier": [ { "id": "v1", "titre": "Diagnostic amiante manquant", "detail": "Dossier Martin", "priorite": "haute" } ],
  "echeances":  [ { "id": "e1", "titre": "Purge du droit de préemption", "echeance": "2026-10-12" } ]
}
```

Champs d'un élément : `id`, `titre` (obligatoire), `detail`, `debut`, `fin`, `echeance`, `priorite` (`haute` ou `normale`), `lien`. Toutes les rubriques sont facultatives.

### 4.2 `POST /conversation` : réponse en flux (SSE)

- Requête : `{"messages": [{"role": "user", "content": "…"}, {"role": "assistant", "content": "…"}]}`, en-tête `Accept: text/event-stream`.
- Réponse : événements `data: {"delta": "morceau de texte"}`, terminés par `data: [DONE]`. En cas d'erreur : `data: {"erreur": "message"}`.

### 4.3 Outils : l'IA agit sur le poste

1. Au démarrage, l'agent envoie `POST /outils/catalogue` avec `{"outils": [{"name", "description", "niveau", "inputSchema"}]}` : la liste exacte des outils du poste, avec des schémas JSON compatibles MCP.
2. Il attend les demandes : `GET /outils/attente?delai=25` (attente longue). Réponse `204` s'il n'y a rien, sinon `{"id": "a1", "outil": "fichier_lire", "arguments": {"chemin": "~/Documents/…"}}`.
3. Il exécute (périmètre, niveau, confirmation, journal) puis répond : `POST /outils/resultat` avec `{"id": "a1", "resultat": {…}, "erreur": null}`, ou `erreur` renseignée en cas de refus.

Le même catalogue est exposé localement en **MCP** (`poste-ia mcp`, JSON-RPC sur l'entrée/sortie standard).

### 4.4 `POST /sceller`

Requête : `{"empreinte_sha256": "…", "nom": "acte.pdf"}`, envoyée seulement après confirmation du collaborateur. Le serveur ancre l'empreinte dans le registre d'horodatage et renvoie la preuve (format libre).

## 5. Rattachement d'un poste

En attendant le parcours définitif, l'administrateur :
- enregistre le jeton du poste dans le trousseau de l'utilisateur : `echo "<jeton>" | poste-ia jeton` ;
- renseigne `ia_connecteur_url` dans `/etc/poste-collab/local.yml`.

Cible : rattachement par **clé REAL** (défi signé, puis jeton d'appareil propre au poste et révocable côté serveur).

## 6. Par système

| | Linux | macOS | Windows 11 |
|---|---|---|---|
| Agent | Python + GTK 4 / libadwaita | à venir | à venir |
| Lancement à l'ouverture | `/etc/xdg/autostart` | LaunchAgent | Tâche planifiée |
| Recherche système | Fournisseur de recherche GNOME | Spotlight | Recherche Windows |
| Clic droit | Extension Nautilus | Action rapide du Finder | Menu contextuel de l'Explorateur |
| Trousseau | libsecret | Trousseau macOS | Gestionnaire d'identification |
