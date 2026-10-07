# Notes de cadrage et décisions

_Décisions communes aux scripts Linux, macOS et Windows 11 ; les détails de mise en œuvre concernent d'abord Linux, premier système livré._

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

## 2. Orchestration : bootstrap bash + Ansible en mode « pull » ✅

- **Idempotent** : relançable sans risque ; un seul outil pour l'installation initiale et la maintenance du parc.
- **Modulaire** : un rôle Ansible par besoin, activable/désactivable via `group_vars/all/reglages.yml`.
- `bootstrap.sh` reste minimal : fenêtre d'installation, droits administrateur, installation d'Ansible, récupération de ce dépôt (`git`, version figée par la release) puis `ansible-playbook` en local. Même principe qu'`ansible-pull`, avec un affichage maîtrisé de bout en bout.
- **Affichage** : plugin Ansible `poste_notaire` (logo de vague, barre de progression générale fixe, défilement des étapes, journal dans `/var/log/poste-collab/`).
- **Réglages propres à l'étude** hors dépôt : `/etc/poste-collab/local.yml`, chargé automatiquement.
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

- `apt purge` d'une liste déclarée dans `group_vars/all/reglages.yml` : jeux GNOME (`aisleriot`, `gnome-mines`, `gnome-sudoku`, `gnome-mahjongg`…), `rhythmbox`, `cheese`, `transmission-*`, `gnome-calculator` (remplacée par Qalculate!, cf. section 13), etc.
- `apt autoremove --purge` ensuite.
- Firefox (snap) retiré si Zen est le navigateur par défaut.
- **snapd** retiré complètement, ainsi que la logithèque (section 19).

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

### WhatsApp : installé par défaut ✅
- **Il n'existe pas d'application WhatsApp officielle pour Linux.** On utilise **WhatsApp Web** (service officiel de Meta), installé en **PWA Edge** : icône dans le lanceur, fenêtre dédiée, notifications. Zen ne sait pas installer de PWA sous Linux.
- Clients non officiels (ZapZap, WasIstLos…) écartés ❌ : ce sont des tiers qui manipulent la session WhatsApp.
- ⚠️ WhatsApp chiffre les messages, mais Meta collecte les métadonnées (qui parle à qui, quand). À réserver aux échanges courants, **jamais aux pièces d'un dossier** couvertes par le secret professionnel.

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

## 10. IA : uniquement l'IA métier de l'étude, présente partout sur le poste ✅

**Seule IA autorisée : l'IA métier propriétaire de l'étude, sur des serveurs distants.** Aucune autre IA ne doit pouvoir être utilisée, ni installée, ni ouverte dans un navigateur (section 19).

- Sur le poste, un **agent** (poste-ia) rend l'IA présente partout : **briefing de la journée à l'ouverture de session** (synthèse, vue d'ensemble, rendez-vous, à faire, points à vérifier, échéances), panneau Super+Espace, recherche du système, clic droit sur les documents, rappels.
- Il lui donne un accès **contrôlé** au poste : trois niveaux (lire, agir, engager), confirmation humaine pour tout ce qui engage l'étude, journal, arrêt d'urgence.
- Le **connecteur** vers les serveurs de l'IA sera activé le moment venu ; son contrat est fixé dans [docs/IA-POSTE.md](IA-POSTE.md). Sans connecteur, le briefing fonctionne à partir de l'agenda et des tâches du poste.
- Écartés ❌ : Microsoft 365 Copilot (Chat compris), ChatGPT, Claude, Mistral (Le Chat), Gemini, Perplexity, DeepSeek, Duck.ai, Meta AI, modèles locaux et toute autre IA.

---

## 11. Socle de sécurité (ajouts) ✅

- **LUKS** à l'installation : non négociable.
- `unattended-upgrades` : mises à jour de sécurité téléchargées automatiquement, **installées à l'extinction** (section 18), **jamais de redémarrage automatique**.
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
- **Vérifié (octobre 2026) : il n'existe pas de client Lifesize natif pour Linux.** La page officielle des téléchargements ne propose l'application de bureau que pour Windows et macOS (et des applications mobiles Android/iOS).
- Lifesize fournit une **application web** officielle pour **Google Chrome et Microsoft Edge**. Elle sera installée en **PWA Edge**, avec une icône dédiée dans le lanceur.
- ⚠️ Lifesize ne cite pas Linux parmi les systèmes officiellement supportés pour son application web. Elle fonctionne sous Edge pour Linux, mais **un test sur poste pilote est indispensable** (caméra, micro, partage d'écran, rejoindre une salle Lifesize).

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

## 14. Environnement de bureau : GNOME 50, retravaillé ✅

Objectif : un bureau **très moderne**, qui donne envie de travailler dessus.

### Contrainte décisive
**Intune n'accepte que les postes Ubuntu sous GNOME** (Ubuntu 24.04 et 26.04 LTS, depuis la version 3.0.2 du 27 avril 2026). Choisir KDE ou COSMIC revient à renoncer à Intune, et donc au poste « conforme » pour l'accès conditionnel M365.

### Comparatif

| | GNOME 50 | KDE Plasma 6 | COSMIC |
|---|---|---|---|
| Esthétique | Épurée, très actuelle (libadwaita) | Moderne, proche de Windows 11 | Moderne, en tuiles |
| Compatible Intune | ✅ | ❌ | ❌ |
| Prise en main depuis Windows | Moyenne : demande une courte formation | Excellente : barre des tâches et menu Démarrer | Moyenne |
| Stabilité, maturité | Très élevée, défaut d'Ubuntu | Élevée | Jeune (1.0 fin 2025) |
| Verrouillage des réglages | dconf (simple) | Kiosk (plus complexe) | Limité |

### Proposition : GNOME 50 « signé » par l'étude
Ubuntu 26.04 livre GNOME 50 en **Wayland uniquement** : animations fluides, gestes du pavé tactile, mise à l'échelle par écran, pas de déchirement d'image. Pour le rendre vraiment moderne et propre à l'étude :

- **Style clair** par défaut, sans bascule automatique (l'utilisateur peut passer en sombre manuellement s'il le souhaite). **Couleur d'accent bleu-vert** (teinte native GNOME `teal`, clé dconf `org.gnome.desktop.interface accent-color`).
- **Fond d'écran maison clair**.
- **Dock vertical sur le côté gauche**, toujours visible, comme la barre latérale de Zen : il ne prend pas de hauteur aux documents (les écrans sont plus larges que hauts). C'est la position native du Dock Ubuntu, donc aucun réglage fragile. Seules les applications métier y sont épinglées (Zen, Evolution, Teams, Lifesize, Word, Excel, ONLYOFFICE, Fichiers, Qalculate!, IA maison).
- **Peu d'extensions**, choisies parmi les plus maintenues (icônes de la zone de notification, flou du shell), car chaque extension peut casser à une mise à jour.
- **Applications modernes** (libadwaita) partout : Fichiers, Calendrier, Showtime, Ressources.
- **Raccourcis métier** : `Super+Espace` pour l'IA maison, touche Calculatrice pour Qalculate!.

**Plan B** : KDE Plasma 6 (Kubuntu 26.04) si l'étude renonce à Intune et privilégie une prise en main immédiate par des utilisateurs venant de Windows.

---

## 15. Thème visuel inspiré d'Archcraft ✅

Objectif : retrouver l'allure d'Archcraft (coloré, icônes et curseurs soignés, fonds d'écran graphiques) en **version claire** **sur GNOME 50**, en restant **léger et insensible aux mises à jour**.

### Ce qu'est le thème Archcraft
Archcraft ne crée presque aucun thème lui-même : il **réempaquette des thèmes libres existants** (paquets `archcraft-gtk-theme-*`, `archcraft-icons-*`, `archcraft-cursor-*`) et les applique à des gestionnaires de fenêtres légers (Openbox, bspwm, Hyprland…), pas à GNOME. Par exemple, sa session bspwm utilise le thème GTK Arc-Dark, les icônes Arc-Circle et le curseur Qogirr. On réutilise donc **les composants d'origine**, pas les paquets Archcraft (réservés à Arch).

### Règle d'or : ne pas « thémer » GTK ni le shell ❌
Les applications GNOME modernes (libadwaita / GTK 4) **ne supportent pas les thèmes GTK**. Les thèmes d'Archcraft (Orchis, Sweet, Catppuccin, Tokyo Night…) ne s'y appliquent qu'en injectant du CSS (`~/.config/gtk-4.0/gtk.css`) ou via l'extension *User Themes* pour le shell. **Ces deux méthodes cassent régulièrement à chaque mise à jour de GNOME** : elles sont exclues.

### Ce qu'on reprend, par niveau de robustesse

| Composant | Choix | Source | Robustesse |
|---|---|---|---|
| Couleur d'accent **bleu-vert (`teal`)**, **style clair** | Réglages natifs GNOME | dconf | ✅ Totale (API officielle) |
| Icônes | **Papirus** ✅ (variante claire `Papirus-Light`) | Paquet Ubuntu `papirus-icon-theme` (mis à jour avec le système) | ✅ Fichiers statiques ; si absent, GNOME revient aux icônes par défaut sans casser |
| Curseur | **Bibata** (ou Qogir, défaut Archcraft bspwm) | Version figée + somme de contrôle | ✅ Fichiers statiques |
| Polices | **Inter** (interface), **JetBrains Mono** (terminal), **Noto** (déjà fournie) | Paquets Ubuntu `fonts-inter`, `fonts-jetbrains-mono` | ✅ |
| Fonds d'écran | Création maison **dans l'esprit Archcraft** (graphique, lumineux), **version claire** | `files/` du dépôt + fichier XML GNOME | ✅ — les fonds d'Archcraft ne sont pas réutilisés, faute de licence claire |
| Terminal | Palette de couleurs du thème dans **Ptyxis** (terminal par défaut) | dconf | ✅ |
| Écran de connexion (GDM) | Logo de l'étude, couleur d'accent | Profil dconf `gdm` (clé officielle `logo`) | ✅ — pas de modification des ressources GDM (fragile) |
| Écran de démarrage et de saisie LUKS | Thème Plymouth Ubuntu conservé, logo de l'étude en option | 🟡 À valider : le remplacement du logo peut être écrasé par une mise à jour | 🟡 |
| Lanceur (rofi chez Archcraft) | Recherche native GNOME (touche `Super`) | — | ✅ Pas de rofi : inadapté à GNOME Wayland |
| Notifications (dunst chez Archcraft) | Notifications natives GNOME | — | ✅ |

### Mécanique reprise d'Archcraft : le « style » comme source unique
Archcraft change d'un coup tout un « style » (fond d'écran, icônes, curseur, couleurs du terminal) à partir d'un seul fichier. On reprend cette idée proprement :

- Un fichier **`group_vars/all/theme.yml`** décrit le style : couleur d'accent, style clair, icônes, curseur, polices, fonds d'écran, palette du terminal.
- Le rôle `branding` le traduit en **valeurs par défaut dconf système** (`/etc/dconf/db/local.d/`), éventuellement verrouillées.
- Changer de style = modifier ce fichier et relancer `bootstrap.sh` sur le parc.
- **Retour arrière** immédiat : supprimer le fichier dconf système et lancer `dconf update` ramène le bureau Ubuntu d'origine.

### Garde-fous
- **Extensions : deux au maximum**, et uniquement si elles sont **empaquetées dans l'archive Ubuntu** (mises à jour avec le système) : icônes de la zone de notification (`gnome-shell-extension-appindicator`) et, si disponible en paquet, flou du shell (Blur my Shell). Sinon, on s'en passe.
- **Aucun script `install.sh` exécuté depuis Internet** : les thèmes non empaquetés sont téléchargés en **version figée**, vérifiés par **somme de contrôle**, puis installés dans `/usr/share/icons`.
- Tout composant absent ou cassé doit laisser GNOME revenir à son apparence par défaut, jamais bloquer la session.

---

## 16. Durcissement maximal du poste ✅

**Toutes les mesures ci-dessous sont retenues** ; les points marqués 🟡 restent à valider techniquement sur poste pilote.

Principe : **défense en profondeur**. Chaque couche suppose que la précédente peut tomber. Tout est appliqué par Ansible (rôle `hardening`) et vérifié automatiquement.

### Démarrage et disque
- **Secure Boot** activé, **mot de passe UEFI**, démarrage sur USB/réseau désactivé.
- **LUKS2** (déjà retenu). 🟡 Déverrouillage **TPM2 + code PIN** si l'installeur d'Ubuntu 26.04 le propose de façon stable ; sinon phrase de passe.
- **Clé de récupération LUKS** conservée hors ligne (coffre de l'étude), jamais sur le poste ni dans le dépôt.

### Comptes et sessions
- Utilisateurs **standard, sans droits `sudo`** ; un compte d'administration distinct.
- **Verrouillage automatique** après 5 minutes, verrouillé (dconf) ; pas de session invitée.
- Politique de mots de passe (`pam_pwquality`) et blocage après échecs répétés (`pam_faillock`).
- **MFA obligatoire** sur Microsoft 365 (côté tenant).
- 🟡 Connexion au poste avec le compte Entra ID via **authd** (Ubuntu), à évaluer.

### Système
- **Ubuntu Pro** : correctifs noyau à chaud (**Livepatch**), maintenance de sécurité étendue (ESM) et **Ubuntu Security Guide (USG)**, qui applique et audite automatiquement le référentiel **CIS** (profil poste de travail). 🟡 Vérifier la disponibilité d'USG pour 26.04.
- Mises à jour de sécurité automatiques, **installées à l'extinction du poste**. **Aucun redémarrage ni rallumage automatique** (`Unattended-Upgrade::Automatic-Reboot "false"`) : un poste ne doit jamais redémarrer seul, ni en pleine journée ni pendant les vacances. Les failles du noyau sont corrigées sans redémarrage par **Livepatch**.
- **AppArmor** en mode strict ; applications Flatpak avec permissions restreintes.
- Services inutiles désactivés (Avahi, partage d'écran entrant, Bluetooth si inutile).
- Paramètres noyau durcis (`sysctl`) et sources de logiciels limitées aux dépôts officiels listés.

### Réseau
- `ufw` : **tout entrant refusé**.
- **DNS chiffré (DNS over TLS)** vers un résolveur filtrant les domaines malveillants.
- Télétravail : **VPN WireGuard** vers l'étude uniquement.

### Périphériques
- **USBGuard** : seuls les périphériques USB autorisés fonctionnent (clavier, souris, webcam, **clé REAL**). Les clés USB de stockage inconnues sont bloquées, principale voie d'entrée des rançongiciels et de fuite de données.

### Navigateurs et applications
- Stratégies imposées dans Zen et Edge : **HTTPS uniquement**, **uBlock Origin** forcé, extensions limitées à une liste blanche, enregistrement des mots de passe désactivé.
- **Gestionnaire de mots de passe** d'équipe auto-hébergé (section 17).
- **ESET** (temps réel) et **Intune** (conformité). ⚠️ Intune ne permet pas l'effacement à distance d'un poste Linux : en cas de vol, c'est **LUKS** qui protège les données.

### Données et sauvegarde
- **Sauvegarde 3-2-1** : NAS de l'étude, **chiffrée**, plus une copie **hors ligne** (protection contre les rançongiciels).
- OneDrive interdit (section 9).

### Contrôle
- Audit automatique **Lynis** et **USG/CIS** après chaque déploiement, avec un score minimal à atteindre (lot 5).
- Journaux persistants (`journald`) et `auditd` sur les événements sensibles.

### Ordre de priorité
1. LUKS + Secure Boot + mot de passe UEFI
2. Utilisateurs sans droits d'administration + verrouillage automatique
3. Mises à jour automatiques + Livepatch
4. USBGuard
5. Sauvegarde chiffrée avec copie hors ligne

---

## 17. Gestionnaire de mots de passe : Bitwarden officiel auto-hébergé ✅

Exigence : les coffres doivent être **stockés sur les serveurs de l'étude / de son éditeur**, avec une ergonomie au niveau de Proton Pass. Proton Pass ne peut pas être auto-hébergé : il est écarté ❌ pour l'étude.

### Le « protocole » : Bitwarden
- **Chiffrement de bout en bout, à connaissance nulle** : le coffre est chiffré sur le poste (AES-256, dérivation de clé Argon2id) avant envoi. Le serveur ne stocke que des données chiffrées et ne connaît jamais le mot de passe maître.
- **Clients officiels** sur tous les systèmes : application de bureau Linux (Flatpak), extensions Zen/Firefox et Edge, Android, iOS, macOS, Windows.
- Fonctions équivalentes à Proton Pass : **passkeys**, **codes TOTP**, **partage par collections** entre collaborateurs, générateur d'**alias e-mail** (intégration SimpleLogin ou addy.io), remplissage automatique.

### Serveur : deux options
| | **Bitwarden officiel auto-hébergé** ✅ | Vaultwarden ❌ |
|---|---|---|
| Nature | Serveur de l'éditeur, audité | Réimplémentation communautaire (Rust) |
| Déploiement | Standard (plusieurs conteneurs) ou *Bitwarden lite* (un seul conteneur, sorti de bêta en décembre 2025) | Un seul conteneur, très léger |
| Organisations, partage | Licence Teams ou Enterprise | Gratuit |
| SSO Entra ID | Licence Enterprise | Oui, OpenID Connect depuis la v1.35 |
| Support, audits | ✅ | ❌ |

**Décision : serveur Bitwarden officiel** (audits de sécurité, support éditeur), avec une licence **Enterprise** pour le SSO Entra ID, les stratégies imposées et la récupération de compte par l'administrateur. Vaultwarden est écarté ❌.

### Hébergement (fourni par l'éditeur du LRA)
- **Instance séparée** du LRA (machine ou VM dédiée) : un coffre de mots de passe ne doit pas tomber en même temps que l'application métier.
- Hébergement **en France**, HTTPS uniquement, interface d'administration accessible seulement depuis le réseau de l'étude ou le VPN.
- **2FA obligatoire** pour tous les comptes, politique de mot de passe maître imposée.
- **Sauvegardes chiffrées quotidiennes** de la base, avec test de restauration.
- 🟡 **Récupération de compte** : prévoir la procédure en cas d'oubli du mot de passe maître (récupération par l'administrateur, licence Enterprise) ; sinon le coffre de l'utilisateur est perdu.

### Sur le poste
- Application **Bitwarden** (Flatpak) et extension imposée dans Zen et Edge, **préconfigurées sur l'adresse du serveur de l'étude**.
- Enregistrement des mots de passe dans les navigateurs désactivé (section 16).

---

## 18. Extinction automatique du soir ✅

Objectif : **économiser l'énergie** et ne pas laisser de poste allumé (et déverrouillable) la nuit en cas d'oubli, sans jamais couper quelqu'un qui travaille encore.

### Fonctionnement
1. À **21 h** (paramétrable), un minuteur systemd déclenche la procédure.
2. **Aucune session ouverte** (écran de connexion) : extinction immédiate.
3. **Session ouverte** : une fenêtre bien visible s'affiche au premier plan, avec un **compte à rebours d'une minute** et un bouton **« Je travaille encore »**.
   - Clic sur le bouton : extinction **reportée de 30 minutes**, puis la fenêtre réapparaît. **Reports illimités**.
   - Pas de réponse en 60 secondes (poste oublié, écran verrouillé) : **extinction forcée**, même si une application la bloque (`systemctl poweroff --ignore-inhibitors`).
4. Le message prévient que **les documents non enregistrés seront perdus**.

### Mise en œuvre (rôle `power`)
- Minuteur et service **systemd** système (`etude-extinction.timer`) : aucune extension GNOME, donc insensible aux mises à jour du bureau.
- Fenêtre affichée dans la session de l'utilisateur par un service systemd utilisateur, avec **zenity** (fourni par Ubuntu).
- Règle **polkit** autorisant l'extinction forcée par ce seul service.
- Paramètres dans `group_vars/all/reglages.yml` : heure, durée du compte à rebours (60 s), durée du report (30 min), reports illimités.
- ✅ **Mises à jour installées à l'extinction** (`Unattended-Upgrade::InstallOnShutdown "true"`), qu'elle soit automatique ou manuelle : le poste est à jour au prochain allumage, sans jamais redémarrer en journée.
- ❌ **Aucun rallumage ni redémarrage automatique** : un poste éteint reste éteint (week-ends, vacances).

---

## 19. Aucune autre IA que l'IA maison ✅

Objectif : **aucune IA autre que celle du logiciel de l'étude ne doit pouvoir être utilisée**, ni installée (ChatGPT, Claude, Mistral, Gemini, Perplexity, DeepSeek, Copilot, modèles locaux…), ni ouverte dans un navigateur. Seul l'administrateur décide de ce qui est installé.

Une liste noire d'applications ne suffit pas (de nouvelles apparaissent chaque mois). Le principe est donc l'inverse : **l'utilisateur ne peut rien installer du tout**, et chaque porte d'entrée est fermée.

| Voie d'installation | Blocage |
|---|---|
| Paquets système (apt) | Utilisateurs **sans droits `sudo`** (section 16) |
| Snap (application ChatGPT, Claude…) | **snapd retiré** du poste |
| Flatpak (Flathub) | Installation système réservée aux administrateurs (**polkit**) ; installation « utilisateur » impossible (voir ligne suivante) |
| Programmes téléchargés, AppImage, Flatpak utilisateur, modèles locaux (Ollama, LM Studio, Jan) | `/home`, `/tmp` et `/var/tmp` montés en **`noexec`** : rien de ce que l'utilisateur télécharge ne peut s'exécuter |
| Logithèque (App Center, GNOME Logiciels) | **Retirée** du poste |
| Extensions de navigateur (barres latérales IA) | **Liste blanche** d'extensions dans Zen et Edge, tout le reste interdit |
| IA intégrées aux navigateurs | Edge : barre latérale et Copilot désactivés (`HubsSidebarEnabled`, stratégies Copilot) ; Zen : chatbot IA désactivé (stratégie `GenerativeAI` 🟡 si supportée par la version de Zen) |
| Sites installés comme application (PWA) | Blocage des domaines IA (ligne suivante) ; seules les PWA déployées par l'administrateur sont présentes |
| Sites web d'IA | ✅ Blocage des domaines (`chatgpt.com`, `openai.com`, `claude.ai`, `anthropic.com`, `chat.mistral.ai`, `gemini.google.com`, `perplexity.ai`, `deepseek.com`, `duck.ai`, `copilot.microsoft.com`, `meta.ai`…) dans les stratégies des navigateurs **et** dans `/etc/hosts`, avec DNS over HTTPS des navigateurs désactivé pour qu'ils ne contournent pas ce blocage. 🟡 Compléter par la **catégorie « IA »** du résolveur DNS filtrant (section 16) si elle existe, pour suivre les nouveaux services automatiquement. **Exception : le domaine de l'IA maison.** |
| Copilot dans Microsoft 365 (Word, Outlook, Teams web) | Côté tenant (hors dépôt) : **aucune licence Copilot**, **Copilot Chat désactivé/masqué** dans le centre d'administration Microsoft 365 🟡 selon les options offertes par Microsoft |
| Greffons IA d'ONLYOFFICE | Gestionnaire de greffons désactivé, greffon IA retiré |

### Contrôle
- La liste des domaines et des extensions autorisées est dans `group_vars/all/reglages.yml`, mise à jour sans toucher au code.
- L'audit de fin de déploiement (lot 5) vérifie qu'aucun binaire, Flatpak, snap ou extension non autorisé n'est présent.

⚠️ Limites techniques :
- **Meta AI dans WhatsApp** passe par les serveurs de WhatsApp : on ne peut pas la bloquer sans bloquer WhatsApp. Son usage est interdit par la charte.
- Aucun blocage n'empêche un collaborateur d'utiliser une IA **sur son téléphone personnel**.

Une **charte d'usage de l'IA** signée par chaque collaborateur complète donc ces mesures.

---

## 20. Moteur de recherche : DuckDuckGo France ✅

**DuckDuckGo, en français et région France, par défaut dans tous les navigateurs** (Zen et Edge).

- Adresse utilisée : **`https://noai.duckduckgo.com/?q={searchTerms}&kl=fr-fr&kad=fr_FR`**
  - `noai.duckduckgo.com` : version officielle de DuckDuckGo **sans IA** (pas de réponses générées « Search Assist », pas d'accès à **Duck.ai**, pas d'images générées par IA). Cohérent avec la section 19, car Duck.ai donne accès aux modèles d'OpenAI, d'Anthropic et d'autres.
  - `kl=fr-fr` : résultats de la région France ; `kad=fr_FR` : interface en français.
  - Suggestions de recherche : `https://duckduckgo.com/ac/?q={searchTerms}&type=list&kl=fr-fr`.
- **Zen** : stratégie `SearchEngines` (`Add` + `Default`), disponible sur toutes les versions de Firefox depuis la 139 (auparavant réservée à l'ESR).
- **Edge** : stratégies `DefaultSearchProviderEnabled`, `DefaultSearchProviderName`, `DefaultSearchProviderSearchURL`, `DefaultSearchProviderSuggestURL`, dans `/etc/opt/edge/policies/`.
- Par défaut **modifiable** par l'utilisateur (stratégies « recommandées » côté Edge). 🟡 Peut être verrouillé si l'étude le souhaite.
- `duck.ai` est ajouté à la liste des domaines IA bloqués (section 19).

⚠️ **Point technique à valider pour toutes les stratégies de Zen** (moteur de recherche, blocage OneDrive, extensions, IA) : Zen est installé en Flatpak, qui ne lit pas forcément le fichier `policies.json` du système. Emplacement retenu : l'extension `app.zen_browser.zen.systemconfig` prévue par le Flatpak de Zen (`/var/lib/flatpak/extension/app.zen_browser.zen.systemconfig/<arch>/stable/policies/policies.json`). 🟡 Sa prise en compte reste à vérifier sur le poste pilote (`about:policies`) ; à défaut, Zen sera installé depuis son paquet officiel hors Flatpak.

---

## 21. Filtrage web : sites interdits et dangereux ✅

Objectif : bloquer sur tous les postes les **sites pornographiques**, les **sites dangereux** (logiciels malveillants, hameçonnage, arnaques) et les **jeux d'argent**, en plus des IA (section 19). La mesure doit fonctionner **au bureau comme en télétravail**, et pour toutes les applications, pas seulement les navigateurs.

### Architecture en deux couches
1. **Résolveur DNS local sur chaque poste : Unbound** (paquet Ubuntu), avec :
   - des **listes de blocage par catégorie** (listes publiques maintenues de type HaGeZi : pornographie, jeux d'argent, menaces/hameçonnage, IA), chargées au format RPZ et **mises à jour chaque jour** par un minuteur systemd. En cas d'échec du téléchargement, la dernière liste valide est conservée ;
   - un **transfert chiffré (DNS over TLS)** vers un résolveur filtrant de second niveau (🟡 Cloudflare for Families, qui bloque déjà logiciels malveillants et contenus adultes) ;
   - les navigateurs ne peuvent pas le contourner : **DNS over HTTPS désactivé** par stratégie, utilisateurs sans droits administrateur.
2. **Extension maison de filtrage**, imposée dans Zen et Edge (seule extension ajoutée à la liste blanche), pour afficher une **page de redirection lisible** au lieu d'une erreur de connexion (un blocage DNS seul ne peut pas afficher de page sur un site HTTPS). Elle utilise l'API standard `declarativeNetRequest`, commune à Firefox et Edge.

### Pages de redirection (« intelligentes »)
| Catégorie bloquée | Redirection |
|---|---|
| IA externes | Vers **l'IA maison** du logiciel de l'étude : « Cette IA n'est pas autorisée. Utilisez celle de l'étude. » |
| Hameçonnage, logiciels malveillants, arnaques | Vers **cybermalveillance.gouv.fr** (dispositif national d'assistance), avec un message : « Ce site a été identifié comme dangereux. Bonne nouvelle : vous n'avez rien risqué. » |
| Pornographie, jeux d'argent | Page interne neutre : « Ce site n'est pas accessible depuis les postes de l'étude. » |

### Contrôle
- Catégories, listes, exceptions et pages de redirection paramétrées dans `group_vars/all/reglages.yml`.
- Un site bloqué par erreur est débloqué par l'administrateur via une **liste d'exceptions**.
- 🟡 Pas de journal nominatif des sites consultés sur le poste (proportionnalité, RGPD) ; seuls les compteurs de blocage sont conservés.
- ⚠️ À mentionner dans la **charte informatique** de l'étude : les salariés doivent être informés du filtrage.

### Filtrage des sites d'extrême droite ✅ (décision assumée par l'étude)
- **Décision de l'étude du 7 octobre 2026** : bloquer uniquement les sites de partis et mouvements d'extrême droite.
- La **liste des domaines est définie et tenue par l'étude** dans `group_vars/all/reglages.yml` (variable `blocage_extreme_droite`). Le dépôt fournit le mécanisme, pas le classement politique.
- Redirection vers une **page interne « Pays des câlins »** (`files/blockpages/calins.html`) : arcs-en-ciel, nuages et message bienveillant. Page originale, sans personnage ni marque protégés (« Bisounours » est une marque déposée).
- ⚠️ **Risques signalés et acceptés** : discrimination liée aux opinions politiques (Code du travail, art. L1132-1), obligation d'impartialité du notaire en tant qu'officier public, besoin professionnel éventuel de consulter ces sites (client). Recommandé : mentionner ce filtrage dans la **charte informatique** et prévoir une **exception** sur demande pour un besoin professionnel.

---

## Questions ouvertes

1. **Licence M365 exacte** (Business Standard / Business Premium / E3…) ? → conditionne Intune.
2. **Nombre de postes** et besoin de **gestion centralisée** (Intune) ou simple déploiement initial ?
3. **Chat sécurisé** : usage interne seulement, ou aussi avec clients et confrères ?
4. ✅ **snapd** : retiré (section 19).
5. **IA maison** : adresse provisoire `ia.notaria.com` ; confirmer l'adresse définitive et la propriété du domaine.
6. ✅ **Filtrage extrême droite** : RN (`rassemblementnational.fr`) et UDR (`udr.fr`), sous-domaines compris ; liste complétable dans `group_vars/all/reglages.yml`.
7. **Charte graphique** de l'étude (logo, couleurs) pour le fond d'écran et l'écran de connexion ?
7. ✅ **Outils notariaux** : la clé REAL fonctionne sous tous les systèmes ; le LRA actuel ne fonctionne pas sous Linux, un **nouveau LRA 100 % web** (Linux, macOS, Windows) est en développement. Le déploiement Linux suit son calendrier.
