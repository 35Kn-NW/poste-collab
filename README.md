# poste-collab

Scripts de déploiement d'un **poste de travail professionnel de collaborateur d'office notarial**, à partir d'une installation fraîche du système, pour **trois systèmes d'exploitation** :

| Système | Dossier | État |
|---|---|---|
| **Linux** (Ubuntu 26.04 LTS, GNOME 50) | [`linux/`](linux/) | ✅ Lot 1 disponible, IA métier en cours (v0.2.0) |
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

Prérequis : Ubuntu 26.04 fraîchement installé (disque chiffré), et les deux fichiers fournis par l'administrateur, placés dans le même dossier :

- `installer-linux.sh` : le script d'installation, figé sur une version publiée ;
- `cle-depot` : la **clé de lecture** du dépôt (le dépôt est privé ; la clé ne permet que la lecture).

Puis, depuis la session d'un utilisateur administrateur :

```bash
bash installer-linux.sh
```

Le script ouvre sa propre fenêtre de terminal (logo, barre de progression générale, défilement des étapes), demande le mot de passe administrateur puis installe le poste. Il peut être **relancé sans risque** : seules les différences sont appliquées.

- Journaux : `/var/log/poste-collab/`
- Réglages propres à l'étude, **hors dépôt** : `/etc/poste-collab/local.yml`, par exemple :

```yaml
fond_ecran_fichier: /etc/poste-collab/fond-etude.webp
logo_ecran_connexion: /etc/poste-collab/logo.png
ia_connecteur_url: https://ia.exemple.fr
```

- Sans interface graphique (SSH) : `LC_SANS_FENETRE=1 bash installer-linux.sh`

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

Le dépôt est **privé**. Il ne contient néanmoins **aucun secret** (identifiants de tenant, clé de licence ESET, jetons, noms de clients) : ces valeurs sont fournies sur chaque poste, hors dépôt (`/etc/poste-collab/local.yml`, trousseau du système).
