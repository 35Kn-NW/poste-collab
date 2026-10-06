# Notes de cadrage et décisions

_Dernière mise à jour : 7 octobre 2026_

Chaque décision indique son **statut** : ✅ retenue · 🟡 à confirmer · ❌ écartée.

---

## 1. Distribution : Ubuntu 26.04 LTS ✅

### Pourquoi pas Arch ❌
- **Rolling release** : une mise à jour peut casser un poste sans préavis ; inacceptable sans DSI dédiée.
- **AUR** : la plupart des outils nécessaires (Zen, clients M365) y sont empaquetés par des tiers non vérifiés → risque de chaîne d'approvisionnement sur des postes manipulant des actes.
- **Aucun support éditeur** : ni Microsoft (Intune, Defender) ni les antivirus professionnels.

### Pourquoi Ubuntu LTS plutôt que Debian
- **Microsoft Intune et le Microsoft Identity Broker (Entra ID) ne supportent que Ubuntu LTS et RHEL.** Sans eux, pas de poste « conforme » → pas d'accès conditionnel M365 → intégration Office 365 dégradée.
- 5 ans de mises à jour de sécurité, 10 ans avec **Ubuntu Pro** (gratuit jusqu'à 5 postes).
- Base Debian : compétences et paquets transposables.

**Plan B :** Debian 13 si l'inscription Intune est abandonnée.

---

## 2. Orchestration : bootstrap bash + `ansible-pull` ✅

- **Idempotent** : relançable sans risque ; un seul outil pour l'installation initiale et la maintenance du parc.
- **Modulaire** : un rôle Ansible par besoin, activable/désactivable via `group_vars/all.yml`.
- `bootstrap.sh` reste minimal : prérequis, installation d'Ansible, `ansible-pull` sur ce dépôt.
- Les valeurs sensibles ne sont jamais dans le dépôt (cf. README, section Confidentialité).

---

## 3. Messagerie : Evolution ✅

- Paquets : `evolution`, `evolution-ews`.
- Type de compte : **« Microsoft 365 »** (API Microsoft Graph).
- ⚠️ **Ne pas utiliser le type « Exchange Web Services »** : Microsoft désactive EWS par défaut sur Exchange Online depuis le 1er octobre 2026, extinction complète prévue en 2027.
- 🟡 Vérifier si l'inscription d'une application Entra ID dédiée est nécessaire (selon la politique de consentement du tenant).

---

## 4. Antivirus 🟡

| Option | Avantages | Inconvénients |
|---|---|---|
| **Microsoft Defender for Endpoint** | Temps réel, EDR, console unifiée avec les postes Windows ; inclus dans *Defender for Business* (M365 Business Premium) | Dépend de la licence |
| **ESET Endpoint Antivirus for Linux** | Solide, supporte Ubuntu/Debian, console ESET PROTECT | Licence payante séparée |
| ClamAV ❌ | Gratuit | Scanner à la demande, pas de vraie protection temps réel : insuffisant |

**Décision dépendante de la licence M365** (cf. questions ouvertes).

---

## 5. Nettoyage des paquets ✅

- `apt purge` d'une liste déclarée dans `group_vars/all.yml` : jeux GNOME (`aisleriot`, `gnome-mines`, `gnome-sudoku`, `gnome-mahjongg`…), `rhythmbox`, `cheese`, `transmission-*`, etc.
- `apt autoremove --purge` ensuite.
- Firefox (snap) retiré si Zen est le navigateur par défaut.
- 🟡 Décider du sort de **snapd** (conserver ou retirer complètement).

---

## 6. Navigateurs ✅

- **Zen Browser** : Flatpak officiel `app.zen_browser.zen` (Flathub), navigateur par défaut du quotidien.
- **Microsoft Edge** (dépôt Microsoft officiel) : réservé à Microsoft 365 (SSO Entra ID, conformité Intune, PWA).

---

## 7. Identité visuelle ✅

- Image installée dans `/usr/share/backgrounds/<etude>/`.
- Profil **dconf système** (`/etc/dconf/db/local.d/`) + **verrouillage** (`locks/`) : appliqué à tous les utilisateurs, y compris ceux créés plus tard.
- Option : fond de l'écran de verrouillage et délai de verrouillage automatique imposés.

---

## 8. Chat sécurisé 🟡

| Option | Profil |
|---|---|
| **Signal** (dépôt apt officiel) | Le plus simple, chiffrement de référence |
| **Element / Matrix** | Serveur auto-hébergé possible, contrôle total des données |
| **Olvid** | Solution française certifiée **CSPN par l'ANSSI** — 🟡 vérifier la disponibilité d'un client Linux |

Dépend de l'usage : interne à l'étude uniquement, ou aussi avec clients et confrères.

---

## 9. Microsoft 365 : intégration maximale ✅

Il n'existe pas d'Office de bureau natif sous Linux. Combinaison retenue :

1. **Edge + Microsoft Identity Broker + inscription Intune** : SSO Entra ID et poste conforme (accès conditionnel).
2. **PWA Edge** déployées automatiquement : Word, Excel, PowerPoint, Outlook, Teams, SharePoint (icônes dans le lanceur, fenêtres dédiées).
3. **OneDrive** : client `onedrive` (abraunegg, open source) en service systemd utilisateur — alternative payante : Insync.
4. **ONLYOFFICE Desktop Editors** : édition hors ligne avec la meilleure fidélité .docx/.xlsx.
5. **Polices** : `ttf-mscorefonts-installer`, Carlito et Caladea (métriquement compatibles Calibri/Cambria).

---

## 10. Chat IA sur le bureau 🟡

Contrainte : **secret professionnel** → le choix du fournisseur compte autant que l'ergonomie.

- **Par défaut : Microsoft 365 Copilot Chat** avec protection des données entreprise (inclus avec la licence, données restant dans le tenant).
- **Accès bureau** : PWA ouverte par un **raccourci global** (ex. `Super+Espace`) en fenêtre flottante.
- **Alternatives** : Claude ou ChatGPT en offre Team/Enterprise (PWA), **Newelle** (application GNOME multi-fournisseurs), **Jan** (modèle 100 % local pour les données les plus sensibles).

---

## 11. Socle de sécurité (ajouts) ✅

- **LUKS** à l'installation : non négociable.
- `unattended-upgrades` (mises à jour de sécurité automatiques).
- `ufw` activé, entrant refusé par défaut.
- `fwupd` (firmwares), AppArmor actif.
- **Sauvegarde** : Déjà Dup vers OneDrive ou NAS.

---

## Questions ouvertes

1. **Licence M365 exacte** (Business Standard / Business Premium / E3…) ? → conditionne l'antivirus et Intune.
2. **Nombre de postes** et besoin de **gestion centralisée** (Intune) ou simple déploiement initial ?
3. **Chat sécurisé** : usage interne seulement, ou aussi avec clients et confrères ?
4. **snapd** : conserver ou retirer ?
5. **Fournisseur IA** par défaut au-delà de Copilot Chat ?
