#!/usr/bin/env bash
# Signature de l'extension par Mozilla, en mode « non listé » : l'extension n'est publiée nulle part,
# Mozilla appose seulement sa signature (obligatoire pour Zen et Firefox). À relancer seulement si le
# code de l'extension change (pas les listes de sites, lues dans les réglages du poste).
#
# Prérequis : compte développeur sur addons.mozilla.org et clés d'API
#   (https://addons.mozilla.org/developers/addon/api/key/), passées en variables d'environnement :
#   AMO_JWT_ISSUER=… AMO_JWT_SECRET=… bash signer.sh
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
: "${AMO_JWT_ISSUER:?Clé AMO_JWT_ISSUER manquante}"
: "${AMO_JWT_SECRET:?Clé AMO_JWT_SECRET manquante}"
sortie=../files/extension
mkdir -p "$sortie"
npx --yes web-ext@8 sign --channel=unlisted --source-dir . --artifacts-dir "$sortie" \
  --ignore-files "tests/**" signer.sh --api-key "$AMO_JWT_ISSUER" --api-secret "$AMO_JWT_SECRET"
signee=$(ls -t "$sortie"/*.xpi | head -1)
mv "$signee" "$sortie/filtrage.xpi"
echo "Extension signée : $sortie/filtrage.xpi"
echo "Passer extension_filtrage_signee à true dans group_vars/all/reglages.yml, puis publier une version."
