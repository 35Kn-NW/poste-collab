// Pastilles d'état des connexions de l'étude, lues dans l'état publié par l'agent poste-ia.
import GLib from 'gi://GLib';
import St from 'gi://St';
import Clutter from 'gi://Clutter';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

const SERVICES = [
    ['real', 'REAL'],
    ['ia', 'IA métier'],
    ['m365', 'Office 365'],
    ['vpn', 'VPN'],
    ['base', 'Base étude'],
];
const PERIODE_SECONDES = 10;
const ETAT_PERIME_SECONDES = 120;

export default class EtatConnexions extends Extension {
    enable() {
        this._indicateur = new PanelMenu.Button(0.5, 'État des connexions', false);
        const boite = new St.BoxLayout({style_class: 'pc-etats'});
        this._pastilles = new Map();
        for (const [cle, libelle] of SERVICES) {
            const pastille = new St.Label({
                text: libelle,
                style_class: 'pc-pastille pc-inconnu',
                y_align: Clutter.ActorAlign.CENTER,
            });
            this._pastilles.set(cle, pastille);
            boite.add_child(pastille);
        }
        this._indicateur.add_child(boite);
        Main.panel.addToStatusArea(this.uuid, this._indicateur, 0, 'right');

        this._actualiser();
        this._minuteur = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, PERIODE_SECONDES, () => {
            this._actualiser();
            return GLib.SOURCE_CONTINUE;
        });
    }

    disable() {
        if (this._minuteur) {
            GLib.source_remove(this._minuteur);
            this._minuteur = null;
        }
        this._indicateur?.destroy();
        this._indicateur = null;
        this._pastilles = null;
    }

    _lireEtat() {
        const chemin = GLib.build_filenamev([GLib.get_user_runtime_dir(), 'poste-collab', 'etat.json']);
        try {
            const [, contenu] = GLib.file_get_contents(chemin);
            return JSON.parse(new TextDecoder().decode(contenu));
        } catch {
            return null;
        }
    }

    _actualiser() {
        const etat = this._lireEtat();
        const maintenant = Math.floor(Date.now() / 1000);
        const perime = !etat || !etat.horodatage || maintenant - etat.horodatage > ETAT_PERIME_SECONDES;
        this._indicateur.menu.removeAll();
        for (const [cle, libelle] of SERVICES) {
            const service = (etat?.services ?? {})[cle] ?? {};
            const niveau = perime ? 'inconnu' : (service.niveau ?? 'inconnu');
            const detail = perime ? 'état indisponible (agent IA métier arrêté ?)' : (service.detail ?? '');
            this._pastilles.get(cle).style_class = `pc-pastille pc-${niveau}`;
            const ligne = new PopupMenu.PopupMenuItem(`${libelle} : ${detail}`, {reactive: false});
            this._indicateur.menu.addMenuItem(ligne);
        }
    }
}
