/* Redirige les sites bloqués par l'étude vers les pages locales de l'extension.
   Les listes viennent des réglages imposés par l'administrateur (stratégie « 3rdparty » de Zen),
   ce qui évite de re-signer l'extension à chaque changement de liste. */
"use strict";

let regles = { extreme_droite: [], ia: [], ia_maison_url: "" };

async function chargerRegles() {
  try {
    const imposees = await browser.storage.managed.get(null);
    regles = Object.assign({ extreme_droite: [], ia: [], ia_maison_url: "" }, imposees);
  } catch (erreur) {
    /* Aucun réglage imposé : l'extension ne redirige rien (le filtrage DNS reste actif). */
  }
}

chargerRegles();
browser.storage.onChanged.addListener((_changements, zone) => {
  if (zone === "managed") {
    chargerRegles();
  }
});

browser.webRequest.onBeforeRequest.addListener(
  (requete) => {
    let hote;
    try {
      hote = new URL(requete.url).hostname;
    } catch (erreur) {
      return {};
    }
    const page = pagePour(hote, regles);
    if (!page) {
      return {};
    }
    return { redirectUrl: browser.runtime.getURL(`pages/${page}.html?site=${encodeURIComponent(hote)}`) };
  },
  { urls: ["<all_urls>"], types: ["main_frame"] },
  ["blocking"]
);
