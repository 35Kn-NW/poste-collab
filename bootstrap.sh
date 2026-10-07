#!/usr/bin/env bash
# Installation du poste collaborateur notaire : point d'entrée.
#
# Usage, depuis la session de l'utilisateur (sans sudo), avec le fichier
# « cle-depot » (clé de lecture du dépôt privé) placé à côté du script :
#   bash bootstrap.sh
# Le script ouvre sa propre fenêtre de terminal, demande le mot de passe
# administrateur, prépare Ansible puis applique le dépôt sur le poste.
# Il peut être relancé sans risque : chaque étape est idempotente.
#
# Variables d'environnement (facultatives) :
#   LC_DEPOT_URL      dépôt à appliquer
#   LC_DEPOT_REF      branche ou étiquette (figée sur la version publiée)
#   LC_CLE_DEPOT      chemin de la clé de lecture, si elle n'est pas à côté du script
#   LC_SANS_FENETRE   1 = rester dans le terminal courant
set -Eeuo pipefail

readonly DEPOT_URL="${LC_DEPOT_URL:-git@github.com:35Kn-NW/Linux-collab.git}"
readonly DEPOT_REF="${LC_DEPOT_REF:-main}"
readonly SCRIPT_URL="https://github.com/35Kn-NW/Linux-collab/releases/latest/download/bootstrap.sh"
readonly DEPOT=/var/lib/linux-collab/depot
readonly JOURNAUX=/var/log/linux-collab
readonly REGLAGES_LOCAUX=/etc/linux-collab/local.yml
readonly CLE_DEPOT=/etc/linux-collab/cle-depot
readonly HOTES_CONNUS=/etc/linux-collab/known_hosts
# Clé d'hôte officielle de GitHub (api.github.com/meta) : aucune confiance aveugle au premier contact.
readonly CLE_HOTE_GITHUB='github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl'
readonly TITRE="Installation poste collaborateur notaire"
readonly VERSION_UBUNTU=26.04

# Copie de files/ui/logo.txt : le dépôt n'est pas encore récupéré à ce stade.
readonly LOGO_VAGUE='                               ▄▄▄▄▄▄▄▄
                        ▄▄▀▀▀▀▀        ▀▀▄▄
                  ▄▄▀▀▀▀                   ▀▄
            ▄▄▀▀▀▀                  ▄▄▄▄     █
      ▄▄▀▀▀▀                      ▄▀    ▀▄   █
▀▀▀▀▀▀                             ▀▄▄   ▀▄▄▀
                                      ▀▀▀'

case "${LANG:-}" in *UTF-8*|*utf8*) ;; *) export LANG=C.UTF-8 ;; esac

if [[ "${COLORTERM:-}" == truecolor || "${COLORTERM:-}" == 24bit ]]; then
  VAGUE=$'\e[38;2;168;134;90m'; SARCELLE=$'\e[38;2;33;144;164m'
else
  VAGUE=$'\e[38;5;137m'; SARCELLE=$'\e[38;5;31m'
fi
VERT=$'\e[38;5;71m'; ROUGE=$'\e[38;5;167m'; GRAS=$'\e[1m'; DOUX=$'\e[2m'; RAZ=$'\e[0m'
readonly ROUE='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'

LIGNES=24; COLONNES=80; RANG_BARRE=1; ETAPE=0; ETAPES=6
JOURNAL_PREPA=$(mktemp -t linux-collab-preparation.XXXXXX.log)
SUDO=()

# --- Fenêtre dédiée ---------------------------------------------------------

ouvrir_fenetre() {
  [[ -z "${LC_DANS_FENETRE:-}" && -z "${LC_SANS_FENETRE:-}" ]] || return 1
  [[ -n "${WAYLAND_DISPLAY:-}${DISPLAY:-}" ]] || return 1

  local script
  if [[ -f "${BASH_SOURCE[0]:-}" ]]; then
    script=$(readlink -f "${BASH_SOURCE[0]}")
  else
    # Lancé par « curl … | bash » : on récupère le script pour la nouvelle fenêtre.
    script=$(mktemp -t linux-collab-bootstrap.XXXXXX.sh)
    wget -qO "$script" "$SCRIPT_URL" 2>/dev/null || curl -fsSLo "$script" "$SCRIPT_URL" || return 1
  fi

  local commande=(env LC_DANS_FENETRE=1 LC_DEPOT_URL="$DEPOT_URL" LC_DEPOT_REF="$DEPOT_REF"
    LC_CLE_DEPOT="${LC_CLE_DEPOT:-}" bash "$script")
  if command -v ptyxis >/dev/null; then
    ptyxis --new-window -- "${commande[@]}" >/dev/null 2>&1 &
  elif command -v gnome-terminal >/dev/null; then
    gnome-terminal --title="$TITRE" --geometry=110x36 -- "${commande[@]}" >/dev/null 2>&1 &
  elif command -v x-terminal-emulator >/dev/null; then
    x-terminal-emulator -e "${commande[@]}" >/dev/null 2>&1 &
  else
    return 1
  fi
  echo "L'installation s'ouvre dans une nouvelle fenêtre."
}

# --- Affichage -------------------------------------------------------------

centrer() {  # centrer <texte coloré> <longueur visible>
  local marge=$(( (COLONNES - $2) / 2 ))
  (( marge < 0 )) && marge=0
  printf '%*s%s\n' "$marge" '' "$1"
}

couper() {  # couper <texte> <longueur max>
  local texte=$1
  (( ${#texte} > $2 )) && texte="${texte:0:$(( $2 - 1 ))}…"
  printf '%s' "$texte"
}

repeter() {  # repeter <caractère> <nombre>
  local i
  for (( i = 0; i < $2; i++ )); do printf '%s' "$1"; done
}

ui_init() {
  if [[ -t 1 ]]; then
    read -r LIGNES COLONNES < <(stty size 2>/dev/null || echo "24 80")
  fi
  printf '\e]0;%s\a\e[?25l\e[2J\e[H' "$TITRE"
  local n=0 ligne
  if (( LIGNES >= 26 )); then
    echo; n=1
    while IFS= read -r ligne; do centrer "$VAGUE$ligne$RAZ" "${#ligne}"; n=$((n + 1)); done <<< "$LOGO_VAGUE"
  fi
  local titre=${TITRE^^} sous="Ubuntu $VERSION_UBUNTU · GNOME 50 · déploiement automatisé"
  echo
  centrer "$GRAS$SARCELLE$titre$RAZ" "${#titre}"
  centrer "$DOUX$sous$RAZ" "${#sous}"
  echo
  n=$((n + 4))
  RANG_BARRE=$((n + 1))
  printf '\e[%d;1H%s%s%s' "$((RANG_BARRE + 2))" "$DOUX" "$(repeter '─' "$COLONNES")" "$RAZ"
  printf '\e[%d;%dr\e[%d;1H' "$((RANG_BARRE + 3))" "$LIGNES" "$((RANG_BARRE + 3))"
  ui_barre ""
}

ui_barre() {  # ui_barre <libellé en cours>
  local pct=$(( ETAPE * 100 / ETAPES )) infos largeur plein barre libelle
  infos=$(printf ' %3d %%  préparation %d/%d' "$pct" "$ETAPE" "$ETAPES")
  largeur=$(( COLONNES - ${#infos} - 4 ))
  (( largeur < 10 )) && largeur=10
  plein=$(( largeur * pct / 100 ))
  barre="  $SARCELLE$(repeter '█' "$plein")$DOUX$(repeter '░' $(( largeur - plein )))$RAZ$GRAS$infos$RAZ"
  libelle=$(couper "$1" $(( COLONNES - 4 )))
  printf '\e7\e[%d;1H\e[2K%s\e[%d;1H\e[2K  %s\e8' "$RANG_BARRE" "$barre" "$((RANG_BARRE + 1))" "$libelle"
}

ui_ligne() {  # ui_ligne <icône colorée> <texte>
  printf '  %s %s\n' "$1" "$(couper "$2" $(( COLONNES - 6 )))"
}

ui_fin() {
  printf '\e[r\e[%d;1H\e[?25h\n' "$LIGNES"
}

# Exécute une étape avec animation ; la sortie va dans le journal de préparation.
etape() {  # etape <libellé> <commande…>
  local libelle=$1; shift
  "$@" >>"$JOURNAL_PREPA" 2>&1 &
  local pid=$! i=0
  while kill -0 "$pid" 2>/dev/null; do
    ui_barre "$SARCELLE${ROUE:$(( i % ${#ROUE} )):1}$RAZ $libelle"
    i=$((i + 1)); sleep 0.12
  done
  if wait "$pid"; then
    ETAPE=$((ETAPE + 1)); ui_ligne "$VERT✓$RAZ" "$libelle"; ui_barre ""
  else
    ui_ligne "$ROUGE✗$RAZ" "$libelle"
    echec "Échec de l'étape « $libelle »."
  fi
}

echec() {
  ui_fin
  echo "${ROUGE}${GRAS}✗ $1${RAZ}"
  echo "  Détails : $JOURNAL_PREPA"
  echo "  Le script peut être relancé sans risque une fois le problème corrigé."
  attendre_fermeture
  exit 1
}

attendre_fermeture() {
  if [[ -n "${LC_DANS_FENETRE:-}" ]]; then
    echo; read -rp "Appuyez sur Entrée pour fermer cette fenêtre." _ </dev/tty || true
  fi
}

# --- Étapes de préparation -------------------------------------------------

verifier_systeme() {
  # Lu dans un sous-shell pour ne pas mélanger ses variables avec celles du script.
  local id version nom
  IFS='|' read -r id version nom < <(. /etc/os-release && echo "${ID:-}|${VERSION_ID:-}|${PRETTY_NAME:-inconnu}")
  if [[ "$id" != ubuntu || "$version" != "$VERSION_UBUNTU" ]]; then
    ui_ligne "$VAGUE!$RAZ" "Système détecté : $nom (prévu : Ubuntu $VERSION_UBUNTU)."
    local reponse
    read -rp "  Continuer quand même ? [o/N] " reponse </dev/tty || reponse=n
    [[ "$reponse" == [oO]* ]] || echec "Installation annulée."
  fi
  getent hosts github.com >/dev/null || echec "Pas d'accès à Internet (github.com introuvable)."
}

obtenir_droits() {
  (( EUID == 0 )) && return
  SUDO=(sudo)
  ui_fin
  sudo -v -p "  Mot de passe administrateur : " || echec "Droits administrateur refusés."
  # Garde les droits actifs pendant toute l'installation.
  while kill -0 $$ 2>/dev/null; do sudo -n true 2>/dev/null; sleep 50; done &
  ui_init
  ui_ligne "$VERT✓$RAZ" "Droits administrateur obtenus"
}

# Installe la clé de lecture du dépôt (fichier « cle-depot » à côté du script,
# ou LC_CLE_DEPOT) et la clé d'hôte de GitHub. Arrêt clair si elle manque.
installer_cle() {
  [[ "$DEPOT_URL" == git@* ]] || return 0
  local source="${LC_CLE_DEPOT:-}"
  if [[ -z "$source" && -f "${BASH_SOURCE[0]:-}" ]]; then
    source="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/cle-depot"
  fi
  if [[ -n "$source" && -f "$source" ]]; then
    "${SUDO[@]}" install -D -m 600 -o root -g root "$source" "$CLE_DEPOT"
  fi
  "${SUDO[@]}" test -f "$CLE_DEPOT" ||
    echec "Clé de lecture du dépôt introuvable : placez le fichier « cle-depot » à côté de bootstrap.sh."
  printf '%s\n' "$CLE_HOTE_GITHUB" | "${SUDO[@]}" tee "$HOTES_CONNUS" >/dev/null
  "${SUDO[@]}" chmod 644 "$HOTES_CONNUS"
}

recuperer_depot() {
  # Jamais d'invite interactive ; abandon si le débit reste nul 30 s.
  local ssh="ssh -i $CLE_DEPOT -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=20"
  ssh+=" -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$HOTES_CONNUS"
  local git=(env GIT_TERMINAL_PROMPT=0 GIT_HTTP_LOW_SPEED_LIMIT=1000 GIT_HTTP_LOW_SPEED_TIME=30
    "GIT_SSH_COMMAND=$ssh" git)
  "${SUDO[@]}" mkdir -p "$(dirname "$DEPOT")" "$JOURNAUX"
  if [[ -d "$DEPOT/.git" ]]; then
    "${SUDO[@]}" "${git[@]}" -C "$DEPOT" fetch -q --depth 1 origin "$DEPOT_REF" &&
      "${SUDO[@]}" "${git[@]}" -C "$DEPOT" checkout -qf FETCH_HEAD
  else
    "${SUDO[@]}" "${git[@]}" clone -q --depth 1 --branch "$DEPOT_REF" "$DEPOT_URL" "$DEPOT"
  fi
}

appliquer() {
  local options=() horodatage
  horodatage=$(date +%Y-%m-%d_%H%M)
  [[ -f "$REGLAGES_LOCAUX" ]] && options+=(-e "@$REGLAGES_LOCAUX")
  "${SUDO[@]}" cp "$JOURNAL_PREPA" "$JOURNAUX/preparation-$horodatage.log" 2>/dev/null || true
  ui_fin
  cd "$DEPOT"
  "${SUDO[@]}" env ANSIBLE_CONFIG="$DEPOT/ansible.cfg" LC_JOURNAL="$JOURNAUX/etapes-$horodatage.log" \
    TERM="${TERM:-xterm-256color}" COLORTERM="${COLORTERM:-}" COLUMNS="$COLONNES" LINES="$LIGNES" \
    ansible-playbook "$DEPOT/site.yml" "${options[@]}"
}

main() {
  if ouvrir_fenetre; then exit 0; fi
  trap 'printf "\e[r\e[?25h"' EXIT
  ui_init
  ETAPE=1; ui_barre ""
  ui_ligne "$VERT✓$RAZ" "Fenêtre d'installation ouverte"
  verifier_systeme
  ETAPE=2; ui_ligne "$VERT✓$RAZ" "Système vérifié"
  obtenir_droits
  ETAPE=3; ui_barre ""
  etape "Mise à jour de la liste des logiciels" "${SUDO[@]}" apt-get -o DPkg::Lock::Timeout=600 update
  etape "Installation d'Ansible et de Git" "${SUDO[@]}" env DEBIAN_FRONTEND=noninteractive \
    apt-get -o DPkg::Lock::Timeout=600 install -y ansible git openssh-client
  installer_cle
  etape "Récupération du dépôt de configuration ($DEPOT_REF)" recuperer_depot
  local code=0
  appliquer || code=$?
  attendre_fermeture
  exit "$code"
}

main "$@"
