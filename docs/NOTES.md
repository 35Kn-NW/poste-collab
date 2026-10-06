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

## 4. Antivirus : ESET Endpoint Antivirus for Linux ✅

Choix d'un **antivirus externe**, indépendant de l'écosystème Microsoft.

- **ESET Endpoint Antivirus for Linux** : protection temps réel, supporte officiellement Ubuntu LTS et Debian.
- Gestion centralisée possible via la console **ESET PROTECT** (agent ESET Management installé sur chaque poste).
- La **clé de licence** et la configuration de l'agent ne sont **jamais versionnées** : elles sont fournies au déploiement (variables locales ou Ansible Vault).

Options écartées :
- Microsoft Defender for Endpoint ❌ : choix d'un éditeur externe à Microsoft.
- ClamAV ❌ : scanner à la demande, pas de vraie protection temps réel, donc insuffisant.

---

## 5. Nettoyage des paquets ✅

- `apt purge` d'une liste déclarée dans `group_vars/all.yml` : jeux GNOME (`aisleriot`, `gnome-mines`, `gnome-sudoku`, `gnome-mahjongg`…), `rhythmbox`, `cheese`, `transmission-*`, `gnome-calculator` (remplacée par Qalculate!, cf. section 13), etc.
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
2. **PWA Edge** déployées automatiquement : Word, Excel, PowerPoint, Outlook, Teams (cf. section 12), SharePoint (icônes dans le lanceur, fenêtres dédiées).
3. **ONLYOFFICE Desktop Editors** : édition hors ligne avec la meilleure fidélité .docx/.xlsx.
4. **Polices** : `ttf-mscorefonts-installer`, Carlito et Caladea (métriquement compatibles Calibri/Cambria).

### OneDrive : interdit sur les postes ❌

**Aucune utilisation de OneDrive n'est permise.** Le déploiement l'empêche à tous les niveaux du poste :

- **Aucun client de synchronisation** : les paquets `onedrive` (abraunegg) et `insync` sont purgés s'ils sont présents, et aucun dépôt tiers les fournissant n'est ajouté.
- **Aucune PWA OneDrive** : seules Word, Excel, PowerPoint, Outlook, Teams et SharePoint sont déployées.
- **Blocage dans les navigateurs** :
  - Edge : stratégie `URLBlocklist` sur `onedrive.live.com`, `onedrive.com`, `1drv.ms` et `*-my.sharepoint.com` (espaces OneDrive Entreprise).
  - Zen : stratégie équivalente (`policies.json`, `WebsiteFilter`).
- **Aucune sauvegarde vers OneDrive** (cf. section 11).

⚠️ Points d'attention :
- Le blocage sur le poste ne suffit pas à lui seul. Pour une interdiction complète, il faut aussi **restreindre OneDrive côté tenant** (centre d'administration SharePoint/OneDrive, ou retrait de la licence OneDrive des utilisateurs). Cette action se fait hors de ce dépôt.
- Dans **Teams**, les fichiers partagés en conversation privée sont stockés dans le OneDrive de l'expéditeur. Avec OneDrive bloqué, le partage de fichiers doit passer par les **canaux d'équipe** (stockés dans SharePoint).
- Les liens Office « Enregistrer sur OneDrive » deviennent inutilisables : l'enregistrement se fait dans **SharePoint** ou en local.

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
- **Sauvegarde** : Déjà Dup vers un **NAS de l'étude** (jamais vers OneDrive ni un cloud grand public).

---

## 12. Visioconférence métier : Teams et Lifesize ✅

### Microsoft Teams
- Microsoft a retiré le client Teams natif pour Linux. La solution officielle est la **PWA Teams dans Edge** : SSO Entra ID, accès conditionnel, flou et arrière-plans, partage d'écran.
- Installée automatiquement avec les autres PWA M365 (section 9), avec icône dans le lanceur et démarrage optionnel à l'ouverture de session.
- Alternative écartée ❌ : `teams-for-linux`, un client communautaire non officiel, donc non supporté par Microsoft.

### Lifesize
- Utilisé via son **application web** (Edge est un navigateur supporté), installée en **PWA** avec icône dédiée dans le lanceur.
- 🟡 Vérifier si Lifesize propose encore un client de bureau Linux officiel (.deb). S'il existe et qu'il est maintenu, il remplacera la PWA.

### Intégration au bureau
- 🟡 **Ouverture automatique des liens de réunion** : les liens `teams.microsoft.com` et Lifesize reçus dans Evolution s'ouvriraient directement dans la bonne application (Edge/PWA) plutôt que dans Zen. Cela passe par un petit routeur de liens (gestionnaire `xdg` dédié).
- **Audio et vidéo** : PipeWire (par défaut sous Ubuntu) avec annulation d'écho activée, et partage d'écran sous Wayland via `xdg-desktop-portal`.
- 🟡 Valider le matériel de l'étude (webcams, casques, éventuelles salles Lifesize) lors du test sur VM ou poste pilote.

---

## 13. Calculatrice : Qalculate! ✅

Besoin : une calculatrice moderne qui **conserve et affiche l'historique des résultats**.

- **Qalculate!** (`qalculate-gtk`) :
  - historique visible en permanence et **conservé d'une session à l'autre** ;
  - réutilisation des résultats précédents (`ans`, clic sur une ligne de l'historique) ;
  - utile au quotidien d'une étude : **pourcentages**, **calculs de dates** (écart en jours entre deux dates, ajout de délais), conversion de devises et d'unités, fractions.
- Remplace la calculatrice GNOME, qui est purgée pour éviter les doublons. La touche « Calculatrice » du clavier ouvre Qalculate!.
- Écartée ❌ : GNOME Calculatrice, dont l'historique est perdu à la fermeture.

---

## Questions ouvertes

1. **Licence M365 exacte** (Business Standard / Business Premium / E3…) ? → conditionne Intune.
2. **Nombre de postes** et besoin de **gestion centralisée** (Intune) ou simple déploiement initial ?
3. **Chat sécurisé** : usage interne seulement, ou aussi avec clients et confrères ?
4. **snapd** : conserver ou retirer ?
5. **Fournisseur IA** par défaut au-delà de Copilot Chat ?
