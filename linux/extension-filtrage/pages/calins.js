"use strict";

document.getElementById("retour").addEventListener("click", () => {
  if (history.length > 1) {
    history.back();
  } else {
    window.close();
  }
});

(function () {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return;
  }
  const symboles = ["\u2665", "\u2661", "\u2726"];
  for (let i = 0; i < 14; i++) {
    const coeur = document.createElement("span");
    coeur.className = "coeur";
    coeur.setAttribute("aria-hidden", "true");
    coeur.textContent = symboles[i % symboles.length];
    coeur.style.left = Math.round(Math.random() * 100) + "vw";
    coeur.style.animationDelay = (Math.random() * 9).toFixed(1) + "s";
    coeur.style.fontSize = 16 + Math.round(Math.random() * 16) + "px";
    document.body.appendChild(coeur);
  }
})();
