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
- [ ] Réponses aux questions ouvertes (licence M365, nombre de postes, chat, snapd, IA)

## Lot 1 — Socle sans dépendance M365
- [ ] `bootstrap.sh` + `site.yml` + `group_vars/all.yml`
- [ ] Rôle `base` (unattended-upgrades, ufw, fwupd, sauvegarde vers NAS)
- [ ] Rôle `purge` (dont clients OneDrive `onedrive` / `insync`)
- [ ] `group_vars/theme.yml` (style visuel unique)
- [ ] Rôle `branding` : dconf système, icônes, curseur Bibata, polices Inter/JetBrains Mono, fond clair, icônes Papirus, palette Ptyxis claire, GDM, dock latéral gauche fixe
- [ ] Rôle `browser` : Zen Flatpak + stratégie de blocage OneDrive
- [ ] Rôle `tools` : Qalculate! (remplace la calculatrice GNOME, touche Calculatrice)

## Lot 2 — Microsoft 365
- [ ] Rôle `browser` : Edge + `URLBlocklist` OneDrive
- [ ] Rôle `m365` : Identity Broker, Intune, PWA (sans OneDrive), ONLYOFFICE, polices
- [ ] Rôle `mail` : Evolution (compte Microsoft 365 / Graph)
- [ ] Hors dépôt : restriction OneDrive côté tenant (centre d'administration SharePoint)
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

## Lot 4 — IA
- [ ] Rôle `ai` : PWA + raccourci global

## Lot 5 — Validation
- [ ] Test complet sur VM fraîche Ubuntu 26.04
- [ ] Test de ré-exécution (idempotence)
- [ ] Audit Lynis + USG/CIS avec score minimal
- [ ] Procédure d'installation documentée pas à pas
