# linux-collab

Déploiement automatisé d'un poste de travail Linux **professionnel** à partir d'une installation fraîche, pensé pour un environnement de bureau soumis au secret professionnel (offices notariaux) et contraint d'utiliser Microsoft 365.

> **Statut : lot 1 disponible (v0.1.0)** : socle, nettoyage, apparence, Zen, Qalculate!. Les décisions sont consignées dans [`docs/NOTES.md`](docs/NOTES.md), le plan de travail dans [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Objectifs

Un nouveau poste doit être opérationnel avec **une seule commande** après l'installation de l'OS, et le même outil doit permettre de maintenir le parc dans le temps.

Le déploiement couvre :

- **Messagerie** : Evolution connecté à Microsoft 365 (API Graph)
- **Antivirus** : ESET Endpoint Antivirus for Linux (protection temps réel, éditeur externe)
- **Nettoyage** : suppression des jeux et logiciels inutiles
- **Navigateur** : Zen Browser
- **Identité visuelle** : fond d'écran maison, appliqué à tous les utilisateurs
- **Chat sécurisé** : messagerie chiffrée de bout en bout
- **Microsoft 365** : intégration maximale (SSO, conformité, applications web, édition hors ligne) — **OneDrive interdit et bloqué**
- **Visioconférence** : Microsoft Teams et Lifesize intégrés au bureau
- **Calculatrice** : Qalculate!, avec historique des résultats conservé
- **IA** : uniquement l'IA maison du logiciel de l'étude, accessible depuis le bureau ; toute autre IA bloquée
- **WhatsApp** : WhatsApp Web installé par défaut (PWA)
- **Sécurité** : durcissement maximal (chiffrement, USBGuard, CIS, Bitwarden auto-hébergé)
- **Énergie** : extinction automatique le soir, avec possibilité de report

## Socle retenu

| Élément | Choix |
|---|---|
| Distribution | **Ubuntu 26.04 LTS** — plan B : Debian 13 |
| Bureau | **GNOME 50** (Wayland), style clair, accent bleu-vert, icônes Papirus, inspiré d'Archcraft sans hack GTK (cf. notes §15) |
| Orchestration | `bootstrap.sh` → `git` + **`ansible-playbook`** : le poste récupère ce dépôt et s'applique la configuration |
| Chiffrement disque | **LUKS** activé à l'installation (obligatoire) |

## Installer un poste

Sur un poste **Ubuntu 26.04** fraîchement installé (disque chiffré), depuis la session d'un utilisateur administrateur :

```bash
wget -O bootstrap.sh https://github.com/35Kn-NW/Linux-collab/releases/latest/download/bootstrap.sh
```

```bash
bash bootstrap.sh
```

Le script ouvre sa propre fenêtre de terminal (logo, barre de progression générale, défilement des étapes), demande le mot de passe administrateur puis installe le poste. Il peut être **relancé sans risque** : seules les différences sont appliquées.

- Journaux : `/var/log/linux-collab/`
- Réglages propres à l'étude, **hors dépôt** : `/etc/linux-collab/local.yml`, par exemple :

```yaml
fond_ecran_fichier: /etc/linux-collab/fond-etude.webp
logo_ecran_connexion: /etc/linux-collab/logo.png
```

- Sans interface graphique (SSH) : `LC_SANS_FENETRE=1 bash bootstrap.sh`

## Structure

```
linux-collab/
├── bootstrap.sh          # fenêtre d'installation, Ansible, récupération du dépôt
├── ansible.cfg           # affichage poste_notaire, journal
├── callback_plugins/     # affichage : logo, barre de progression, défilement des étapes
├── site.yml              # playbook principal
├── group_vars/all/
│   ├── reglages.yml      # paquets à purger, moteur de recherche, domaines bloqués…
│   └── theme.yml         # style visuel : accent, icônes, curseur, polices, fond, dock
├── roles/
│   ├── base/             # mises à jour auto, ufw, fwupd, AppArmor, sauvegarde NAS
│   ├── purge/            # jeux, logiciels inutiles, clients OneDrive
│   ├── hardening/        # USBGuard, PAM, sysctl, DNS chiffré, USG/CIS, auditd
│   ├── antivirus/        # ESET Endpoint Antivirus for Linux
│   ├── browser/          # Zen (Flatpak) + Edge (M365), blocage OneDrive
│   ├── m365/             # Intune, broker Entra ID, PWA, ONLYOFFICE, polices
│   ├── mail/             # Evolution + evolution-ews (compte Microsoft 365)
│   ├── visio/            # Teams + Lifesize (PWA), routage des liens de réunion
│   ├── tools/            # Qalculate! et utilitaires de bureau
│   ├── passwords/        # Bitwarden (Flatpak + extensions) préconfiguré sur le serveur de l'étude
│   ├── webfilter/        # Unbound + listes par catégorie, extension de redirection
│   ├── power/            # extinction automatique du soir avec fenêtre de report
│   ├── chat/             # messagerie sécurisée
│   ├── ai/               # PWA de l'IA maison + blocage de toute autre IA
│   └── branding/         # applique theme.yml : dconf système, icônes, curseur, polices, GDM
└── files/
    └── wallpaper.png
```

## Confidentialité

Ce dépôt est **public** : il ne doit contenir **aucun secret** (identifiants de tenant, clé de licence ESET, jetons d'inscription, noms de clients). Ces valeurs seront fournies localement au moment du déploiement (fichier de variables hors dépôt ou Ansible Vault).
