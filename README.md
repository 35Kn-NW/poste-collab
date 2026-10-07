# poste-collab

Scripts de déploiement d'un **poste de travail professionnel de collaborateur d'office notarial**, à partir d'une installation fraîche du système, pour **trois systèmes d'exploitation** :

| Système | Dossier | État |
|---|---|---|
| **Linux** (Ubuntu 26.04 LTS, GNOME 50) | [`linux/`](linux/) | ✅ Cahier des charges codé (v0.3.0) — validation sur poste pilote : [docs/VALIDATION.md](docs/VALIDATION.md) |
| **macOS** | `macos/` | 🔜 À venir |
| **Windows 11** | `windows/` | 🔜 À venir |

Les trois scripts partagent les **mêmes décisions** (sécurité, Microsoft 365, IA métier, filtrage, apparence), consignées dans [`docs/NOTES.md`](docs/NOTES.md), et le même plan de travail : [`docs/ROADMAP.md`](docs/ROADMAP.md). Chaque système les applique avec ses outils natifs.

## Objectifs communs

Un nouveau poste doit être opérationnel avec **une seule commande** après l'installation du système, et le même outil doit permettre de maintenir le parc dans le temps.

- **IA métier** de l'étude présente partout sur le poste : briefing de la journée à l'ouverture de session, panneau (Super+Espace), recherche, clic droit sur les documents ; aucune autre IA possible ([`docs/IA-POSTE.md`](docs/IA-POSTE.md))
- **Microsoft 365** : intégration maximale, **OneDrive interdit**
- **Messagerie** : Evolution (Linux) connectée à Microsoft 365
- **Antivirus** : ESET
- **Navigateur** : Zen, moteur DuckDuckGo France sans IA
- **Visioconférence** : Teams et Lifesize · **WhatsApp** : WhatsApp Web
- **Sécurité** : durcissement maximal, Bitwarden auto-hébergé, filtrage web
- **Énergie** : extinction automatique le soir, mises à jour installées à l'extinction, jamais de redémarrage automatique
- **Apparence** : style clair, accent bleu-vert, fond d'écran de l'étude

## Installer un poste Linux

Sur Ubuntu 26.04 fraîchement installé (disque chiffré), depuis la session d'un utilisateur administrateur, dans un terminal :

```bash
wget -qO /tmp/installer-linux.sh https://github.com/35Kn-NW/poste-collab/releases/latest/download/installer-linux.sh && bash /tmp/installer-linux.sh
```

La commande télécharge le script de la **dernière version publiée** (figé sur cette version du dépôt), puis lance l'installation. Le script ouvre sa propre fenêtre de terminal (logo, barre de progression générale, défilement des étapes), demande le mot de passe administrateur puis installe le poste. Il peut être **relancé sans risque** : seules les différences sont appliquées.

- Journaux : `/var/log/poste-collab/`
- Réglages propres à l'étude, **hors dépôt** : `/etc/poste-collab/local.yml`, par exemple :

```yaml
fond_ecran_fichier: /etc/poste-collab/fond-etude.webp
logo_ecran_connexion: /etc/poste-collab/logo.png
ia_connecteur_url: https://ia.exemple.fr
```

- Sans interface graphique (SSH) : `LC_SANS_FENETRE=1 bash /tmp/installer-linux.sh`

## Structure

```
poste-collab/
├── docs/                     # décisions communes, roadmap, architecture de l'IA métier
├── linux/
│   ├── bootstrap.sh          # publié comme « installer-linux.sh » dans chaque release
│   ├── ansible.cfg, site.yml, inventaire.ini
│   ├── callback_plugins/     # affichage : logo, barre de progression, défilement des étapes
│   ├── group_vars/all/       # reglages.yml, theme.yml
│   ├── roles/                # base, purge, branding, browser, tools, agent…
│   ├── agent/                # agent IA métier du poste (briefing, panneau, outils, connecteur)
│   └── files/                # logo, icône, fond provisoire
├── macos/                    # à venir
└── windows/                  # à venir
```

## Versions

Chaque release publie le script d'installation de chaque système disponible (`installer-linux.sh`, puis `installer-macos.sh`, `installer-windows.ps1`), **figé sur la version du dépôt correspondante**.

## Confidentialité

Le dépôt est **public**. Il ne contient **aucun secret** (identifiants de tenant, clé de licence ESET, jetons, noms de clients) : ces valeurs sont fournies sur chaque poste, hors dépôt (`/etc/poste-collab/local.yml`, trousseau du système).
