# Roadmap

_État au 7 octobre 2026 — Linux 0.3.0. ✅ fait et testé en conteneur · 🔧 prêt, attend une information de l'étude · 🧪 à valider sur poste pilote · ⏳ à faire._

## Linux (Ubuntu 26.04 / GNOME 50)

| Domaine | État | Détail |
|---|---|---|
| Installation en une commande | ✅ | Fenêtre (vague, barre, défilement), journaux, relance sans risque, release figée par version |
| Socle | ✅ | Mises à jour installées à l'extinction, aucun redémarrage automatique, pare-feu, AppArmor, micrologiciels, Flatpak à jour |
| Nettoyage | ✅ | Jeux, logiciels inutiles, OneDrive, logithèque, snap |
| Apparence | ✅ 🧪 | Style clair verrouillé, accent bleu-vert, Papirus, Bibata, Inter, **dock en bas**, pastilles d'état en haut |
| Fond d'écran de l'étude | 🔧 | `fond_ecran_fichier` (fichier haute définition à fournir) |
| Zen | ✅ 🧪 | Par défaut, DuckDuckGo France sans IA, HTTPS imposé, Bitwarden + Privacy Badger + uBlock, autres extensions bloquées, IA et OneDrive bloqués |
| Messagerie Evolution + Microsoft 365 | ✅ 🧪 | Module Graph, assistant de première connexion ; 🔧 consentement administrateur Entra ID éventuel |
| Microsoft 365 (Edge) | ✅ 🧪 | Edge, applications Microsoft 365, Outlook, Word, Excel, PowerPoint, **Teams**, **Lifesize**, **WhatsApp** ; liens de réunion routés vers Edge |
| Intune / authentification unique | 🔧 | `intune_actif` selon la licence Microsoft 365 |
| Bureautique | ✅ | ONLYOFFICE, polices Carlito / Caladea ; 🔧 polices Microsoft (licence à accepter par l'étude) |
| Mots de passe | ✅ 🔧 | Bitwarden (application + extensions) ; adresse du serveur de l'étude à fournir |
| Messagerie sécurisée | ✅ | Signal |
| Sécurité | ✅ 🧪 | Noyau durci, mots de passe ≥ 12 caractères, audit, journaux persistants, Flatpak réservé aux administrateurs, **USBGuard**, programmes téléchargés non exécutables (au redémarrage) ; 🔧 Livepatch (jeton Ubuntu Pro) |
| Filtrage web | ✅ 🧪 | Unbound : pornographie, jeux d'argent, menaces, arnaques, contournement DNS, IA externes, RN / UDR, OneDrive ; DNS chiffré filtrant ; listes mises à jour chaque jour |
| Antivirus | 🔧 | ESET : adresse de l'installateur et licence à fournir (poste signalé tant qu'il manque) |
| Extinction du soir | ✅ 🧪 | 21 h, fenêtre d'une minute, report de 30 min sans limite |
| Sauvegarde | 🔧 | Déjà Dup chiffrée vers le NAS : adresse à fournir |
| IA métier | ✅ 🔧 | Briefing, panneau `Super+Espace`, recherche, clic droit, rappels, outils encadrés, pastilles ; connecteur à activer (`ia_connecteur_url`) |
| Pastilles REAL / Base étude / VPN | 🔧 | `sondes_etat` : hôtes à tester à fournir |

## Restant à faire (Linux)
- [x] Pages locales de blocage (« Pays des câlins », IA → IA métier) installées sur le poste, et extension de redirection écrite (`linux/extension-filtrage/`)
- [ ] 🔧 Signer l'extension une fois (compte développeur Mozilla de l'étude, mode « non listé ») : `signer.sh`, puis `extension_filtrage_signee: true`
- [ ] ⏳ Retrait du greffon IA d'ONLYOFFICE
- [ ] ⏳ Blocage des comptes après échecs répétés (pam_faillock) : à valider sur poste pilote avant activation
- [ ] ⏳ Palette claire du terminal
- [ ] ⏳ Rattachement du poste à l'IA métier par clé REAL
- [ ] 🧪 **Validation sur poste pilote** : liste dans [docs/VALIDATION.md](VALIDATION.md)

## Hors dépôt (administration Microsoft 365 et étude)
- [ ] Aucune licence Copilot, Copilot Chat désactivé dans le tenant
- [ ] OneDrive restreint dans le tenant ; MFA obligatoire
- [ ] Serveur Bitwarden auto-hébergé (instance dédiée, France, sauvegardes)
- [ ] Clé de récupération LUKS de chaque poste conservée au coffre

## Autres systèmes
- [ ] macOS (`macos/`)
- [ ] Windows 11 (`windows/`)
