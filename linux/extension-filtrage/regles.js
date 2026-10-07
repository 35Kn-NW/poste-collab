/* Correspondance des domaines bloqués (sous-domaines compris). Partagé avec les tests (Node). */
"use strict";

function domaineCorrespond(hote, domaines) {
  const nom = String(hote || "").toLowerCase().replace(/\.$/, "");
  return (domaines || []).some((domaine) => {
    const d = String(domaine).toLowerCase().replace(/^\*\./, "");
    return nom === d || nom.endsWith("." + d);
  });
}

/* Page locale à afficher pour cet hôte, ou null s'il n'est pas bloqué. */
function pagePour(hote, regles) {
  if (domaineCorrespond(hote, regles.extreme_droite)) {
    return "calins";
  }
  if (domaineCorrespond(hote, regles.ia)) {
    return "ia";
  }
  return null;
}

if (typeof module !== "undefined") {
  module.exports = { domaineCorrespond, pagePour };
}
