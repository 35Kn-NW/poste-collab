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
- [ ] Réponses aux questions ouvertes (licence M365, nombre de postes, chat, snapd, IA)

## Lot 1 — Socle sans dépendance M365
- [ ] `bootstrap.sh` + `site.yml` + `group_vars/all.yml`
- [ ] Rôle `base` (unattended-upgrades, ufw, fwupd, sauvegarde vers NAS)
- [ ] Rôle `purge` (dont clients OneDrive `onedrive` / `insync`)
- [ ] `group_vars/theme.yml` (style visuel unique)
- [ ] Rôle `branding` : dconf système, icônes, curseur Bibata, polices Inter/JetBrains Mono, fond clair, icônes Papirus, palette Ptyxis claire, GDM
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

## Lot 4 — IA
- [ ] Rôle `ai` : PWA + raccourci global

## Lot 5 — Validation
- [ ] Test complet sur VM fraîche Ubuntu 26.04
- [ ] Test de ré-exécution (idempotence)
- [ ] Procédure d'installation documentée pas à pas
