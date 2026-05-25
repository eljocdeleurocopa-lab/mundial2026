var NUM_TEAMS_PER_GROUP = 4;
var TORNEIG = 'mundial';

function create2DArray(rows) {
    var arr = [];
    for (var i=0;i<rows;i++) { arr[i] = []; }
    return arr;
}

function genera_resultats(formulari) {
    var acabat = 1;
    var resultats = create2DArray(49);
    for (var i=0; i<6; i++) {
        var id_equip1 = parseInt(formulari.elements["form-"+i+"-equip-1"].value);
        var id_equip2 = parseInt(formulari.elements["form-"+i+"-equip-2"].value);
        var gols_equip1 = parseInt(formulari.elements["form-"+i+"-gols1"].value);
        var gols_equip2 = parseInt(formulari.elements["form-"+i+"-gols2"].value);
        if (gols_equip1 >= 0 && gols_equip2 >= 0) {
            resultats[id_equip1][id_equip2] = gols_equip1;
            resultats[id_equip2][id_equip1] = gols_equip2;
        } else { acabat = 0; }
    }
    return [resultats, acabat];
}

function ordena(ids_equips, resultats) {
    // Calcula punts, diferència i gols TOTALS per cada equip
    var equips = [];
    for (var i = 0; i < ids_equips.length; i++) {
        equips.push({'id': ids_equips[i], 'punts': 0, 'gols': 0, 'diferencia': 0});
    }
    for (var i = 0; i < ids_equips.length; i++) {
        for (var j = i + 1; j < ids_equips.length; j++) {
            var id1 = ids_equips[i]; var id2 = ids_equips[j];
            var g1 = resultats[id1][id2]; var g2 = resultats[id2][id1];
            if (g1 == null || g2 == null) continue;
            if (g1 > g2) { _.findWhere(equips,{'id':id1}).punts += 3; }
            else if (g2 > g1) { _.findWhere(equips,{'id':id2}).punts += 3; }
            else { _.findWhere(equips,{'id':id1}).punts += 1; _.findWhere(equips,{'id':id2}).punts += 1; }
            _.findWhere(equips,{'id':id1}).gols += g1;
            _.findWhere(equips,{'id':id2}).gols += g2;
            _.findWhere(equips,{'id':id1}).diferencia += (g1 - g2);
            _.findWhere(equips,{'id':id2}).diferencia += (g2 - g1);
        }
    }
    return _(equips).chain().sortBy('gols').sortBy('diferencia').sortBy('punts').reverse().value();
}

function stats_cap_a_cap(ids_equips, resultats) {
    // Calcula punts, diferència i gols NOMÉS entre els equips donats
    var stats = {};
    for (var i = 0; i < ids_equips.length; i++) {
        stats[ids_equips[i]] = {id: ids_equips[i], punts: 0, diferencia: 0, gols: 0};
    }
    for (var i = 0; i < ids_equips.length; i++) {
        for (var j = i + 1; j < ids_equips.length; j++) {
            var id1 = ids_equips[i]; var id2 = ids_equips[j];
            var g1 = resultats[id1][id2]; var g2 = resultats[id2][id1];
            if (g1 == null || g2 == null) continue;
            if (g1 > g2) { stats[id1].punts += 3; }
            else if (g2 > g1) { stats[id2].punts += 3; }
            else { stats[id1].punts += 1; stats[id2].punts += 1; }
            stats[id1].gols += g1; stats[id2].gols += g2;
            stats[id1].diferencia += (g1 - g2); stats[id2].diferencia += (g2 - g1);
        }
    }
    return stats;
}

function classifica(equips_ordenats_totals, resultats) {
    /*
     * Implementació de l'Article 13 del Reglament FIFA 2026.
     *
     * Step 1: Cap a cap (punts, diferència, gols) entre empatats
     * Step 2: Totals (diferència, gols) — fair play i FIFA ranking no implementats
     *
     * Retorna [equips_ordenats, hi_ha_empat_irresolt]
     */

    var resultat_final = [];
    var error = 0;

    // Agrupem per punts totals (primer criteri)
    var grups_per_punts = {};
    for (var i = 0; i < equips_ordenats_totals.length; i++) {
        var e = equips_ordenats_totals[i];
        var k = e.punts;
        if (!grups_per_punts[k]) grups_per_punts[k] = [];
        grups_per_punts[k].push(e);
    }

    // Processem cada grup d'equips amb els mateixos punts
    var punts_keys = Object.keys(grups_per_punts).map(Number).sort(function(a,b){return b-a;});

    for (var ki = 0; ki < punts_keys.length; ki++) {
        var grup = grups_per_punts[punts_keys[ki]];

        if (grup.length === 1) {
            resultat_final.push(grup[0]);
            continue;
        }

        // Hi ha empat — apliquem Step 1: cap a cap
        var ids = grup.map(function(e){ return e.id; });
        var cac = stats_cap_a_cap(ids, resultats);
        var cac_array = ids.map(function(id){ return cac[id]; });
        cac_array = _(cac_array).chain().sortBy('gols').sortBy('diferencia').sortBy('punts').reverse().value();

        // Comprovem si el cap a cap ha resolt l'empat
        var sub_grups = {};
        for (var i = 0; i < cac_array.length; i++) {
            var e = cac_array[i];
            var k = e.punts + '_' + e.diferencia + '_' + e.gols;
            if (!sub_grups[k]) sub_grups[k] = [];
            sub_grups[k].push(e.id);
        }

        if (Object.keys(sub_grups).length === cac_array.length) {
            // Cap a cap ha resolt tot
            for (var i = 0; i < cac_array.length; i++) {
                resultat_final.push(_.findWhere(equips_ordenats_totals, {id: cac_array[i].id}));
            }
            continue;
        }

        // Empat parcial — Step 2: diferència i gols totals per als que segueixen empatats
        // Construïm l'ordre final combinant cap a cap i totals
        var sub_keys = Object.keys(sub_grups);
        // Ordenem sub_grups per punts cac desc
        sub_keys.sort(function(a, b) {
            var pa = parseInt(a.split('_')[0]); var pb = parseInt(b.split('_')[0]);
            var da = parseInt(a.split('_')[1]); var db = parseInt(b.split('_')[1]);
            var ga = parseInt(a.split('_')[2]); var gb = parseInt(b.split('_')[2]);
            if (pa !== pb) return pb - pa;
            if (da !== db) return db - da;
            return gb - ga;
        });

        for (var si = 0; si < sub_keys.length; si++) {
            var sub_ids = sub_grups[sub_keys[si]];
            if (sub_ids.length === 1) {
                resultat_final.push(_.findWhere(equips_ordenats_totals, {id: sub_ids[0]}));
            } else {
                // Segueixen empatats — Step 2: totals (diferència i gols)
                var sub_equips = sub_ids.map(function(id){
                    return _.findWhere(equips_ordenats_totals, {id: id});
                });
                sub_equips = _(sub_equips).chain().sortBy('gols').sortBy('diferencia').reverse().value();

                // Comprovem si els totals han resolt l'empat
                var tots_diferents = true;
                for (var i = 0; i < sub_equips.length - 1; i++) {
                    if (sub_equips[i].diferencia === sub_equips[i+1].diferencia &&
                        sub_equips[i].gols === sub_equips[i+1].gols) {
                        tots_diferents = false;
                        break;
                    }
                }

                if (!tots_diferents) {
                    error = 1; // Empat irresolt (necessitaria fair play o FIFA ranking)
                }

                for (var i = 0; i < sub_equips.length; i++) {
                    resultat_final.push(sub_equips[i]);
                }
            }
        }
    }

    return [resultat_final, error];
}

function actualitza_grups() {
    var formulari = document.getElementById("f1");
    var ids_equips = [
        parseInt(formulari.elements["form-0-equip-1"].value),
        parseInt(formulari.elements["form-0-equip-2"].value),
        parseInt(formulari.elements["form-1-equip-1"].value),
        parseInt(formulari.elements["form-1-equip-2"].value)
    ];
    var noms_equips = Array(49); var banderes_equips = Array(49);
    for (var i = 0; i<ids_equips.length; i++) {
        if (typeof noms_fixos !== 'undefined' && noms_fixos[ids_equips[i]]) {
            noms_equips[ids_equips[i]] = noms_fixos[ids_equips[i]];
            banderes_equips[ids_equips[i]] = banderes_fixes[ids_equips[i]];
        } else if (formulari.elements["nom-equip-"+ids_equips[i]]) {
            noms_equips[ids_equips[i]] = formulari.elements["nom-equip-"+ids_equips[i]].value;
            banderes_equips[ids_equips[i]] = formulari.elements["bandera-equip-"+ids_equips[i]].value;
        }
    }
    var tupla_resultats = genera_resultats(formulari);
    var resultats = tupla_resultats[0]; var acabat = tupla_resultats[1];
    var classificats_totals = ordena(ids_equips, resultats);
    var resultat_classificats = classifica(classificats_totals, resultats);
    var classificats = resultat_classificats[0]; var error = resultat_classificats[1];
    document.ban0.src = banderes_equips[classificats[0].id];
    document.ban1.src = banderes_equips[classificats[1].id];
    document.ban2.src = banderes_equips[classificats[2].id];
    document.ban3.src = banderes_equips[classificats[3].id];
    formulari.elements["c0"].value = noms_equips[classificats[0].id];
    formulari.elements["c1"].value = noms_equips[classificats[1].id];
    formulari.elements["c2"].value = noms_equips[classificats[2].id];
    formulari.elements["c3"].value = noms_equips[classificats[3].id];
    formulari.elements["p0"].value = classificats[0].punts;
    formulari.elements["p1"].value = classificats[1].punts;
    formulari.elements["p2"].value = classificats[2].punts;
    formulari.elements["p3"].value = classificats[3].punts;
    formulari.elements["d0"].value = classificats[0].diferencia;
    formulari.elements["d1"].value = classificats[1].diferencia;
    formulari.elements["d2"].value = classificats[2].diferencia;
    formulari.elements["d3"].value = classificats[3].diferencia;
    formulari.elements["g0"].value = classificats[0].gols;
    formulari.elements["g1"].value = classificats[1].gols;
    formulari.elements["g2"].value = classificats[2].gols;
    formulari.elements["g3"].value = classificats[3].gols;
    formulari.elements["id0"].value = classificats[0].id;
    formulari.elements["id1"].value = classificats[1].id;
    formulari.elements["id2"].value = classificats[2].id;
    formulari.elements["id3"].value = classificats[3].id;
    if (acabat == 1) { formulari.elements["seguent"].removeAttribute('disabled'); }
    else { formulari.elements["seguent"].disabled = true; }
    if (acabat == 1 && error == 1) {
        alert("EP! Hi ha 2 o més equips empatats a tot! Si t'agrada com ha quedat la classificació pots seguir al següent, sinó segur que canviant un resultat ja desfà l'empat.");
    }
}

function actualitza_eliminatoria() {
    var formulari = document.getElementById("f1");
    var num_partits = formulari.elements["num-partits"].value;
    acabat = 1;
    for (var i=0;i<num_partits;i++) {
        var gols1 = "form-"+i+"-gols1"; var gols2 = "form-"+i+"-gols2"; var form = "form-"+i+"-empat";
        if (formulari.elements[gols1].value < 0 || formulari.elements[gols2].value < 0) { acabat = 0; }
        else if (formulari.elements[gols1].value == formulari.elements[gols2].value) {
            empat_seleccionat = 0;
            for (var j=0, iLen=formulari.elements[form].length; j<iLen; j++) {
                formulari.elements[form][j].disabled = false;
                if (formulari.elements[form][j].checked) { empat_seleccionat = 1; }
            }
            if (!empat_seleccionat) { acabat = 0; }
        } else {
            for (var j=0, iLen=formulari.elements[form].length; j<iLen; j++) {
                formulari.elements[form][j].disabled = true;
                formulari.elements[form][j].checked = false;
            }
        }
    }
    if (acabat == 1) { formulari.elements["seguent"].removeAttribute('disabled'); }
    else { formulari.elements["seguent"].disabled = true; }
}

function comprova_boto_inicial() {
    var formulari = document.getElementById("f1");
    if (!formulari) return;
    var boto = formulari.elements["seguent"];
    if (!boto) return;

    // Distingim fase de grups de rondes eliminatòries pel camp nom-grup
    var nom_grup_el = document.getElementById("nom-grup");
    var nom_grup = nom_grup_el ? nom_grup_el.value : '';
    var grups_fase = ['A','B','C','D','E','F','G','H','I','J','K','L'];
    if (grups_fase.indexOf(nom_grup) === -1) {
        // Ronda eliminatòria
        actualitza_eliminatoria();
        return;
    }

    // Fase de grups: comprova si tots els gols estan entrats
    var num_partits = parseInt(formulari.elements["num-partits"].value);
    for (var i = 0; i < num_partits; i++) {
        var g1 = formulari.elements["form-"+i+"-gols1"];
        var g2 = formulari.elements["form-"+i+"-gols2"];
        if (!g1 || !g2) return;
        if (g1.value == "-1" || g2.value == "-1") return;
        // A la fase de grups l'empat no requereix selecció addicional
    }
    // Tots els partits ok — però la classificació de grups també ha d'estar completa
    // (el botó ja s'habilita via actualitza_grups quan es canvia un resultat)
    // Aquí només l'habilitem si la classificació ja estava feta (posicions != 0)
    var classificacio_ok = true;
    for (var i = 0; i < 4; i++) {
        var id_el = formulari.elements["id"+i];
        if (!id_el || id_el.value == "" || parseInt(id_el.value) <= 0) {
            classificacio_ok = false;
            break;
        }
    }
    if (classificacio_ok) {
        boto.removeAttribute('disabled');
    }
}

function guanyador_partit(formulari, i) {
    var el_equip1 = formulari.elements["form-"+i+"-equip-1"];
    var el_equip2 = formulari.elements["form-"+i+"-equip-2"];
    if (!el_equip1 || !el_equip2) return null;
    var equip1_id = parseInt(el_equip1.value);
    var equip2_id = parseInt(el_equip2.value);
    var gols1 = parseInt(formulari.elements["form-"+i+"-gols1"].value);
    var gols2 = parseInt(formulari.elements["form-"+i+"-gols2"].value);
    if (gols1 > gols2) return {guanyador: equip1_id, perdedor: equip2_id};
    if (gols2 > gols1) return {guanyador: equip2_id, perdedor: equip1_id};
    var empat_els = formulari.elements["form-"+i+"-empat"];
    if (empat_els) {
        for (var j = 0; j < empat_els.length; j++) {
            if (empat_els[j].checked) {
                if (empat_els[j].value == "1") return {guanyador: equip1_id, perdedor: equip2_id};
                else return {guanyador: equip2_id, perdedor: equip1_id};
            }
        }
    }
    return null;
}

function afegeix_equips_submit() {
    var formulari = document.getElementById("f1");
    if (!formulari) return;
    if (!formulari.elements["form-0-equip-1"]) return;

    formulari.onsubmit = function() {
        var num_partits = parseInt(formulari.elements["num-partits"].value);
        var nom_grup_el = document.getElementById("nom-grup");
        var nom_grup = nom_grup_el ? nom_grup_el.value : '';

        if (nom_grup === 'Q' || nom_grup === 'R') {
            var resultat = guanyador_partit(formulari, 0);
            if (resultat !== null) {
                if (nom_grup === 'R') {
                    var inp1 = document.createElement("input");
                    inp1.type = "hidden"; inp1.name = "equip_1"; inp1.value = resultat.guanyador;
                    formulari.appendChild(inp1);
                    var inp2 = document.createElement("input");
                    inp2.type = "hidden"; inp2.name = "equip_2"; inp2.value = resultat.perdedor;
                    formulari.appendChild(inp2);
                } else {
                    var inp3 = document.createElement("input");
                    inp3.type = "hidden"; inp3.name = "equip_3"; inp3.value = resultat.guanyador;
                    formulari.appendChild(inp3);
                    var inp4 = document.createElement("input");
                    inp4.type = "hidden"; inp4.name = "equip_4"; inp4.value = resultat.perdedor;
                    formulari.appendChild(inp4);
                }
            }
        } else {
            var equip_index = 0;
            var participant_index = 0;
            for (var i = 0; i < num_partits; i++) {
                var el_equip1 = formulari.elements["form-"+i+"-equip-1"];
                var el_equip2 = formulari.elements["form-"+i+"-equip-2"];

                // Enviem els 2 participants de cada partit
                if (el_equip1 && el_equip2) {
                    var p1 = document.createElement("input");
                    p1.type = "hidden"; p1.name = "participant_" + participant_index; p1.value = el_equip1.value;
                    formulari.appendChild(p1);
                    participant_index++;
                    var p2 = document.createElement("input");
                    p2.type = "hidden"; p2.name = "participant_" + participant_index; p2.value = el_equip2.value;
                    formulari.appendChild(p2);
                    participant_index++;
                }

                // Enviem el guanyador
                var resultat = guanyador_partit(formulari, i);
                if (resultat !== null) {
                    var input = document.createElement("input");
                    input.type = "hidden";
                    input.name = "equip_" + equip_index;
                    input.value = resultat.guanyador;
                    formulari.appendChild(input);
                    equip_index++;
                }
            }
        }
        return true;
    };
}

// Inicialitza quan el DOM estigui llest
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        afegeix_equips_submit();
        comprova_boto_inicial();
    });
} else {
    afegeix_equips_submit();
    comprova_boto_inicial();
}
