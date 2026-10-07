# Validation sur poste pilote (Linux)

Ce que les tests automatiques en conteneur **ne peuvent pas** vérifier, à contrôler sur une machine réelle ou une VM avec bureau, après installation **puis redémarrage**.

| # | Contrôle | Attendu |
|---|---|---|
| 1 | Lancer la commande d'installation | Fenêtre avec la vague, barre de progression, « Installation terminée » |
| 2 | Redémarrer, ouvrir la session | Briefing « Votre journée » ; assistant de messagerie ~20 s après |
| 3 | Bureau | Style clair, accent bleu-vert, dock en bas, pastilles REAL / IA métier / Office 365 / VPN / Base étude en haut à droite |
| 4 | Clic sur les pastilles | Détail de chaque connexion |
| 5 | `Super+Espace` | Panneau IA métier (« non connectée » tant que le connecteur n'est pas activé) |
| 6 | Zen : `about:policies` | Stratégies actives ; Bitwarden, Privacy Badger, uBlock installés ; `http://` refusé |
| 7 | Zen : chatgpt.com, rassemblementnational.fr | Bloqués |
| 8 | Edge : applications Outlook, Teams, Lifesize, WhatsApp dans le lanceur | Présentes, s'ouvrent en fenêtre |
| 9 | Lien Teams dans un courriel | S'ouvre dans Edge |
| 10 | Evolution, compte « Microsoft 365 » | Connexion au compte de l'étude ; l'agenda apparaît dans le briefing |
| 11 | Clé USB de stockage | Refusée ; clavier, souris, webcam, clé REAL acceptés |
| 12 | Fichier exécutable téléchargé (`./programme`) | « Permission refusée » |
| 13 | Site pour adultes ou de jeux d'argent | Introuvable (bloqué) |
| 14 | `sudo ufw status` | Actif |
| 15 | `sudo systemctl start poste-collab-extinction` | Fenêtre « Je travaille encore » ; report de 30 min |
| 16 | Arrêt du poste avec mises à jour en attente | Installées pendant l'extinction |
| 17 | Clic droit sur un document dans Fichiers | Menu « IA métier » |

Tout écart est à remonter avec une capture et le dernier journal de `/var/log/poste-collab/`.
