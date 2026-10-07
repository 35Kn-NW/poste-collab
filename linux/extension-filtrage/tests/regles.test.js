"use strict";
const test = require("node:test");
const assert = require("node:assert");
const { domaineCorrespond, pagePour } = require("../regles.js");

const regles = { extreme_droite: ["rassemblementnational.fr", "udr.fr"], ia: ["chatgpt.com", "claude.ai"] };

test("domaine et sous-domaines", () => {
  assert.ok(domaineCorrespond("rassemblementnational.fr", regles.extreme_droite));
  assert.ok(domaineCorrespond("www.rassemblementnational.fr", regles.extreme_droite));
  assert.ok(domaineCorrespond("WWW.UDR.FR.", regles.extreme_droite));
});

test("pas de faux positifs", () => {
  assert.ok(!domaineCorrespond("fudr.fr", regles.extreme_droite));
  assert.ok(!domaineCorrespond("udr.fr.exemple.com", regles.extreme_droite));
  assert.ok(!domaineCorrespond("notaires.fr", regles.extreme_droite));
});

test("page selon la catégorie", () => {
  assert.strictEqual(pagePour("www.udr.fr", regles), "calins");
  assert.strictEqual(pagePour("chatgpt.com", regles), "ia");
  assert.strictEqual(pagePour("duckduckgo.com", regles), null);
  assert.strictEqual(pagePour("chatgpt.com", { extreme_droite: [], ia: [] }), null);
});
