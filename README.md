# linux-collab

Déploiement automatisé d'un poste de travail Linux **professionnel** à partir d'une installation fraîche, pensé pour un environnement de bureau soumis au secret professionnel (offices notariaux) et contraint d'utiliser Microsoft 365.

> **Statut : cadrage.** Les décisions sont consignées dans [`docs/NOTES.md`](docs/NOTES.md), le plan de travail dans [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Objectifs

Un nouveau poste doit être opérationnel avec **une seule commande** après l'installation de l'OS, et le même outil doit permettre de maintenir le parc dans le temps.

Le déploiement couvre :

- **Messagerie** : Evolution connecté à Microsoft 365 (API Graph)
- **Antivirus** : protection temps réel de niveau professionnel
- **Nettoyage** : suppression des jeux et logiciels inutiles
- **Navigateur** : Zen Browser
- **Identité visuelle** : fond d'écran maison, appliqué à tous les utilisateurs
- **Chat sécurisé** : messagerie chiffrée de bout en bout
- **Microsoft 365** : intégration maximale (SSO, conformité, applications web, OneDrive, édition hors ligne)
- **IA** : chat IA moderne accessible directement depuis le bureau

## Socle retenu

| Élément | Choix |
|---|---|
| Distribution | **Ubuntu 26.04 LTS** (GNOME) — plan B : Debian 13 |
| Orchestration | `bootstrap.sh` → **`ansible-pull`** depuis ce dépôt |
| Chiffrement disque | **LUKS** activé à l'installation (obligatoire) |

## Utilisation (cible)

```bash
curl -fsSL https://raw.githubusercontent.com/35Kn-NW/Linux-collab/main/bootstrap.sh | sudo bash
```

> Pas encore disponible : voir la [roadmap](docs/ROADMAP.md).

## Structure prévue

```
linux-collab/
├── bootstrap.sh          # installe ansible, lance ansible-pull
├── site.yml              # playbook principal
├── group_vars/all.yml    # paramètres : paquets à purger, antivirus, options…
├── roles/
│   ├── base/             # mises à jour auto, ufw, fwupd, AppArmor, sauvegarde
│   ├── purge/            # jeux et logiciels inutiles
│   ├── antivirus/        # Defender for Endpoint ou ESET
│   ├── browser/          # Zen (Flatpak) + Edge (M365)
│   ├── m365/             # Intune, broker Entra ID, PWA, OneDrive, ONLYOFFICE, polices
│   ├── mail/             # Evolution + evolution-ews (compte Microsoft 365)
│   ├── chat/             # messagerie sécurisée
│   ├── ai/               # chat IA + raccourci global
│   └── branding/         # fond d'écran, profil dconf verrouillé
└── files/
    └── wallpaper.png
```

## Confidentialité

Ce dépôt est **public** : il ne doit contenir **aucun secret** (identifiants de tenant, clés de licence, jetons d'inscription, noms de clients). Ces valeurs seront fournies localement au moment du déploiement (fichier de variables hors dépôt ou Ansible Vault).
