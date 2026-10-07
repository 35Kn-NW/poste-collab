"use strict";

const site = new URLSearchParams(location.search).get("site");
if (site) {
  document.getElementById("site").textContent = site;
}

(async function () {
  let adresse = "";
  try {
    adresse = (await browser.storage.managed.get("ia_maison_url")).ia_maison_url || "";
  } catch (erreur) {
    adresse = "";
  }
  if (adresse) {
    const bouton = document.getElementById("ouvrir");
    bouton.hidden = false;
    bouton.addEventListener("click", () => {
      location.href = adresse;
    });
  }
})();
