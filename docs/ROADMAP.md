# Roadmap

## Lot 0 — Cadrage
- [x] Choix de la distribution (Ubuntu 26.04 LTS)
- [x] Choix de l'orchestration (bootstrap + ansible-pull)
- [x] Notes de décision ([NOTES.md](NOTES.md))
- [ ] Réponses aux questions ouvertes (licence M365, nombre de postes, chat, snapd, IA)

## Lot 1 — Socle sans dépendance M365
- [ ] `bootstrap.sh` + `site.yml` + `group_vars/all.yml`
- [ ] Rôle `base` (unattended-upgrades, ufw, fwupd, sauvegarde)
- [ ] Rôle `purge`
- [ ] Rôle `branding` (fond d'écran + dconf verrouillé)
- [ ] Rôle `browser` (Zen Flatpak)

## Lot 2 — Microsoft 365
- [ ] Rôle `browser` : Edge
- [ ] Rôle `m365` : Identity Broker, Intune, PWA, OneDrive, ONLYOFFICE, polices
- [ ] Rôle `mail` : Evolution (compte Microsoft 365 / Graph)

## Lot 3 — Sécurité et communication
- [ ] Rôle `antivirus` (selon licence)
- [ ] Rôle `chat`

## Lot 4 — IA
- [ ] Rôle `ai` : PWA + raccourci global

## Lot 5 — Validation
- [ ] Test complet sur VM fraîche Ubuntu 26.04
- [ ] Test de ré-exécution (idempotence)
- [ ] Procédure d'installation documentée pas à pas
