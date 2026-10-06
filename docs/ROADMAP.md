# Roadmap

## Lot 0 — Cadrage
- [x] Choix de la distribution (Ubuntu 26.04 LTS)
- [x] Choix de l'orchestration (bootstrap + ansible-pull)
- [x] Notes de décision ([NOTES.md](NOTES.md))
- [x] Antivirus : ESET Endpoint Antivirus for Linux
- [x] OneDrive : interdit sur les postes
- [x] Visioconférence : Teams + Lifesize
- [x] Calculatrice : Qalculate!
- [x] Bureau : GNOME 50 + thème inspiré d'Archcraft (sans hack GTK)
- [x] Style clair, accent bleu-vert (`teal`), icônes Papirus
- [x] Durcissement maximal (section 16), Bitwarden officiel, extinction automatique
- [x] WhatsApp Web par défaut, installation d'IA impossible, snapd retiré
- [x] Moteur de recherche : DuckDuckGo France (sans IA)
- [x] IA : uniquement l'IA maison, toute autre IA bloquée (installation et web)
- [x] Filtrage web : pornographie, jeux d'argent, sites dangereux
- [ ] Réponses aux questions ouvertes (licence M365, nombre de postes, chat, domaine de l'IA maison)

## Lot 1 — Socle sans dépendance M365
- [ ] `bootstrap.sh` + `site.yml` + `group_vars/all.yml`
- [ ] Rôle `base` (unattended-upgrades, ufw, fwupd, sauvegarde vers NAS)
- [ ] Rôle `purge` (dont clients OneDrive `onedrive` / `insync`)
- [ ] `group_vars/theme.yml` (style visuel unique)
- [ ] Rôle `branding` : dconf système, icônes, curseur Bibata, polices Inter/JetBrains Mono, fond clair, icônes Papirus, palette Ptyxis claire, GDM, dock latéral gauche fixe
- [ ] Rôle `browser` : Zen Flatpak + stratégie de blocage OneDrive + DuckDuckGo France sans IA par défaut
- [ ] 🟡 Valider l'emplacement des stratégies pour Zen en Flatpak
- [ ] Rôle `tools` : Qalculate! (remplace la calculatrice GNOME, touche Calculatrice)

## Lot 2 — Microsoft 365
- [ ] Rôle `browser` : Edge + `URLBlocklist` OneDrive + DuckDuckGo France sans IA par défaut
- [ ] Rôle `m365` : Identity Broker, Intune, PWA (sans OneDrive), ONLYOFFICE, polices
- [ ] Rôle `mail` : Evolution (compte Microsoft 365 / Graph)
- [ ] Hors dépôt : restriction OneDrive côté tenant (centre d'administration SharePoint)
- [ ] PWA WhatsApp Web
- [ ] Rôle `visio` : PWA Teams + PWA Lifesize, routage des liens de réunion, PipeWire (annulation d'écho)

## Lot 3 — Sécurité et communication
- [ ] Rôle `antivirus` : ESET (licence et agent ESET PROTECT fournis hors dépôt)
- [ ] Rôle `chat`

## Lot 3 bis — Durcissement et énergie
- [ ] Procédure d'installation : Secure Boot, mot de passe UEFI, démarrage USB/réseau désactivé, LUKS2 (🟡 TPM2 + PIN), clé de récupération au coffre
- [ ] Rôle `hardening` : comptes sans sudo + compte admin distinct, verrouillage auto 5 min, pas de session invitée, pam_pwquality/faillock
- [ ] Rôle `hardening` : AppArmor strict, permissions Flatpak restreintes, sysctl, services inutiles off (Avahi, partage d'écran, Bluetooth), dépôts limités
- [ ] Rôle `hardening` : ufw entrant refusé, DNS over TLS filtrant, VPN WireGuard (télétravail)
- [ ] USBGuard (liste blanche, dont clé REAL)
- [ ] Stratégies navigateurs Zen/Edge : HTTPS uniquement, uBlock forcé, liste blanche d'extensions, mots de passe navigateur désactivés
- [ ] Ubuntu Pro : Livepatch, ESM, USG profil CIS poste de travail (🟡 disponibilité 26.04)
- [ ] Mises à jour auto installées à l'extinction, aucun redémarrage automatique (Automatic-Reboot false) + Livepatch
- [ ] journald persistant + auditd
- [ ] Sauvegarde chiffrée 3-2-1 avec copie hors ligne
- [ ] Rôle `passwords` : Bitwarden Flatpak + extensions Zen/Edge forcées, URL du serveur préconfigurée
- [ ] Rôle `power` : extinction automatique 21 h, fenêtre 60 s, report de 30 min illimité, extinction forcée sans réponse
- [ ] Hors dépôt : serveur Bitwarden officiel auto-hébergé, licence Enterprise (instance dédiée, France, sauvegardes)
- [ ] Hors dépôt : MFA obligatoire sur le tenant M365
- [ ] 🟡 Évaluer la connexion au poste avec le compte Entra ID (authd)

## Lot 4 — IA (verrouillage)
- [ ] Retrait de snapd et de la logithèque
- [ ] polkit : installation Flatpak réservée aux administrateurs
- [ ] Montage `noexec` de /home, /tmp, /var/tmp
- [ ] Stratégies navigateurs : IA intégrées désactivées, liste blanche d'extensions
- [ ] Blocage des domaines IA (navigateurs + /etc/hosts, DoH navigateur désactivé), exception pour l'IA maison
- [ ] ONLYOFFICE : greffons désactivés
- [ ] Rôle `ai` : PWA de l'IA maison (`ia_maison_url`, provisoire : https://ia.notaria.com) + raccourci global `Super+Espace`
- [ ] Hors dépôt : aucune licence Copilot, Copilot Chat désactivé dans le tenant M365

## Lot 4 bis — Filtrage web
- [ ] Rôle `webfilter` : Unbound local + listes RPZ par catégorie (pornographie, jeux, menaces, IA), mise à jour quotidienne
- [ ] Transfert DNS over TLS vers un résolveur filtrant (🟡 Cloudflare for Families)
- [ ] Extension maison `declarativeNetRequest` (Zen + Edge) : pages de redirection par catégorie
- [ ] Catégorie extrême droite (liste tenue par l'étude) → page « Pays des câlins »
- [ ] Liste d'exceptions administrateur

## Lot 5 — Validation
- [ ] Test complet sur VM fraîche Ubuntu 26.04
- [ ] Test de ré-exécution (idempotence)
- [ ] Audit Lynis + USG/CIS avec score minimal
- [ ] Audit « aucune IA » : binaires, Flatpak, snap, extensions non autorisés
- [ ] Procédure d'installation documentée pas à pas
