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
    var equips = [];
    for (var i = 0; i<ids_equips.length; i++) {
        equips.push({'id': ids_equips[i], 'punts': 0, 'gols': 0, 'diferencia': 0});
    }
    for (var i = 0; i<ids_equips.length; i++) {
        for (var j = i + 1; j<ids_equips.length; j++) {
            id_equip1 = ids_equips[i]; id_equip2 = ids_equips[j];
            gols_equip1 = resultats[id_equip1][id_equip2];
            gols_equip2 = resultats[id_equip2][id_equip1];
            if (gols_equip1 == null || gols_equip2 == null) { continue; }
            if (gols_equip1 > gols_equip2) { _.findWhere(equips, {'id':id_equip1}).punts += 3; }
            else if (gols_equip2 > gols_equip1) { _.findWhere(equips, {'id':id_equip2}).punts += 3; }
            else { _.findWhere(equips, {'id':id_equip1}).punts += 1; _.findWhere(equips, {'id':id_equip2}).punts += 1; }
            _.findWhere(equips, {'id':id_equip1}).gols += gols_equip1;
            _.findWhere(equips, {'id':id_equip2}).gols += gols_equip2;
            _.findWhere(equips, {'id':id_equip1}).diferencia += gols_equip1 - gols_equip2;
            _.findWhere(equips, {'id':id_equip2}).diferencia += gols_equip2 - gols_equip1;
        }
    }
    return _(equips).chain().sortBy('gols').sortBy('diferencia').sortBy('punts').reverse().value();
}

function classifica(resultats, equips, tipus, equips_totals) {
    var error = 0;
    if (TORNEIG == 'mundial') {
        var agrupa = function(objA, objB) { return objA.punts == objB.punts && objA.diferencia == objB.diferencia && objA.gols == objB.gols; };
        var agrupats = _.groupBy(equips, function(obj){ return obj.punts+"-"+obj.diferencia+"-"+obj.gols; });
    } else {
        if (tipus == 'punts') {
            var agrupa = function(objA, objB) { return objA.punts == objB.punts; };
            var agrupats = _.groupBy(equips, 'punts');
        } else {
            var agrupa = function(objA, objB) { return objA.diferencia == objB.diferencia && objA.gols == objB.gols; };
            var agrupats = _.groupBy(equips, function(obj){ return obj.diferencia+"-"+obj.gols; });
        }
    }
    if (Object.keys(agrupats).length == equips.length) { return [equips, error]; }
    else if (Object.keys(agrupats).length == 1) {
        if (TORNEIG == 'mundial' && equips.length == NUM_TEAMS_PER_GROUP) { error = 1; }
        else if (TORNEIG == 'euro' && equips.length == NUM_TEAMS_PER_GROUP && tipus == 'altres') { error = 1; }
        else if (equips.length < NUM_TEAMS_PER_GROUP) { error = 1; }
        else {
            var new_classificats = Array();
            var resultat_sub_classifica = classifica(resultats, equips, 'altres', equips_totals);
            var sub_classifica = resultat_sub_classifica[0]; error = resultat_sub_classifica[1];
            for (var j = 0; j < sub_classifica.length; j++) { new_classificats.push(_.findWhere(equips, {'id':sub_classifica[j].id})); }
            equips = new_classificats;
        }
    } else {
        var i = 0; var new_classificats = Array();
        while(i < equips.length) {
            if (i == (equips.length - 1) || !agrupa(equips[i], equips[i + 1])) { new_classificats.push(equips[i]); }
            else {
                var sub_ids = Array(); sub_ids.push(equips[i].id); i++;
                while(i < (equips.length - 1) && agrupa(equips[i], equips[i + 1])) { sub_ids.push(equips[i].id); i++; }
                sub_ids.push(equips[i].id);
                var sub_equips = ordena(sub_ids, resultats);
                var resultat_sub_classifica = classifica(resultats, sub_equips, 'punts', equips_totals);
                var sub_classifica = resultat_sub_classifica[0]; error = resultat_sub_classifica[1];
                if (error == 1) {
                    var resultat_sub_classifica2 = classifica(resultats, sub_equips, 'altres', equips_totals);
                    var sub_classifica2 = resultat_sub_classifica2[0]; error2 = resultat_sub_classifica2[1];
                    if (error2 == 0) { error = 0; sub_classifica = sub_classifica2; }
                    else {
                        var sub_equips2 = Array();
                        for (var j = 0; j < equips_totals.length; j++) {
                            var t = _.findWhere(sub_equips, {'id': equips_totals[j].id});
                            if (t != null) { sub_equips2.push(_.findWhere(equips_totals, {'id': equips_totals[j].id})); }
                        }
                        var resultat_sub_classifica3 = classifica(resultats, sub_equips2, 'altres', equips_totals);
                        var sub_classifica3 = resultat_sub_classifica3[0]; error3 = resultat_sub_classifica3[1];
                        if (error3 == 0) { error = 0; sub_classifica = sub_classifica3; }
                    }
                }
                for (var j = 0; j < sub_classifica.length; j++) { new_classificats.push(_.findWhere(equips, {'id':sub_classifica[j].id})); }
            }
            i++;
        }
        equips = new_classificats;
    }
    return [equips, error];
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
    var classificats = ordena(ids_equips, resultats);
    var classificats_totals = classificats;
    var resultat_classificats = classifica(resultats, classificats, 'punts', classificats_totals);
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
                formulari.elements[form][j].disabled = true; formulari.elements[form][j].checked = false;
            }
        }
    }
    if (acabat == 1) { formulari.elements["seguent"].removeAttribute('disabled'); }
    else { formulari.elements["seguent"].disabled = true; }
}

// Inicialitza quan es carrega la pàgina
window.onload = function() {
    if (document.getElementById("f1")) {
        var formulari = document.getElementById("f1");
        if (formulari.elements["form-0-gols1"]) {
            var boto = formulari.elements["seguent"];
            if (boto && boto.disabled) {
                var tots_ok = true;
                for (var i = 0; i < formulari.elements["num-partits"].value; i++) {
                    if (formulari.elements["form-"+i+"-gols1"].value == "-1" ||
                        formulari.elements["form-"+i+"-gols2"].value == "-1") { tots_ok = false; break; }
                }
                if (tots_ok) { boto.disabled = false; }
            }
        } else if (formulari.elements["form-0-equip-1"]) {
            actualitza_eliminatoria();
        }
    }
};

// Afegeix els equips classificats/posicionats com a camps ocults abans d'enviar
document.addEventListener('DOMContentLoaded', function() {
    var formulari = document.getElementById("f1");
    if (!formulari) return;
    if (!formulari.elements["form-0-equip-1"]) return;

    formulari.addEventListener('submit', function() {
        var num_partits = parseInt(formulari.elements["num-partits"].value);
        var nom_grup_el = document.getElementById("nom-grup");
        var nom_grup = nom_grup_el ? nom_grup_el.value : '';

        // Grups Q (tercer/quart) i R (final): enviem per posició
        if (nom_grup === 'Q' || nom_grup === 'R') {
            // Només hi ha 1 partit
            var equip1_id = parseInt(formulari.elements["form-0-equip-1"].value);
            var equip2_id = parseInt(formulari.elements["form-0-equip-2"].value);
            var gols1 = parseInt(formulari.elements["form-0-gols1"].value);
            var gols2 = parseInt(formulari.elements["form-0-gols2"].value);

            var guanyador_id = null;
            var perdedor_id = null;

            if (gols1 > gols2) {
                guanyador_id = equip1_id; perdedor_id = equip2_id;
            } else if (gols2 > gols1) {
                guanyador_id = equip2_id; perdedor_id = equip1_id;
            } else {
                var empat_els = formulari.elements["form-0-empat"];
                if (empat_els) {
                    for (var j = 0; j < empat_els.length; j++) {
                        if (empat_els[j].checked) {
                            if (empat_els[j].value == "1") {
                                guanyador_id = equip1_id; perdedor_id = equip2_id;
                            } else {
                                guanyador_id = equip2_id; perdedor_id = equip1_id;
                            }
                            break;
                        }
                    }
                }
            }

            if (guanyador_id !== null) {
                if (nom_grup === 'R') {
                    // Final: campió=1, subcampió=2
                    var inp1 = document.createElement("input");
                    inp1.type = "hidden"; inp1.name = "equip_1"; inp1.value = guanyador_id;
                    formulari.appendChild(inp1);
                    var inp2 = document.createElement("input");
                    inp2.type = "hidden"; inp2.name = "equip_2"; inp2.value = perdedor_id;
                    formulari.appendChild(inp2);
                } else {
                    // Tercer/quart lloc: 3r=3, 4t=4
                    var inp3 = document.createElement("input");
                    inp3.type = "hidden"; inp3.name = "equip_3"; inp3.value = guanyador_id;
                    formulari.appendChild(inp3);
                    var inp4 = document.createElement("input");
                    inp4.type = "hidden"; inp4.name = "equip_4"; inp4.value = perdedor_id;
                    formulari.appendChild(inp4);
                }
            }
        } else {
            // Resta de rondes eliminatòries: enviem els guanyadors
            var equip_index = 0;
            for (var i = 0; i < num_partits; i++) {
                var el_equip1 = formulari.elements["form-"+i+"-equip-1"];
                var el_equip2 = formulari.elements["form-"+i+"-equip-2"];
                if (!el_equip1 || !el_equip2) continue;

                var equip1_id = parseInt(el_equip1.value);
                var equip2_id = parseInt(el_equip2.value);
                var gols1 = parseInt(formulari.elements["form-"+i+"-gols1"].value);
                var gols2 = parseInt(formulari.elements["form-"+i+"-gols2"].value);
                var guanyador_id = null;

                if (gols1 > gols2) {
                    guanyador_id = equip1_id;
                } else if (gols2 > gols1) {
                    guanyador_id = equip2_id;
                } else {
                    var empat_els = formulari.elements["form-"+i+"-empat"];
                    if (empat_els) {
                        for (var j = 0; j < empat_els.length; j++) {
                            if (empat_els[j].checked) {
                                guanyador_id = (empat_els[j].value == "1") ? equip1_id : equip2_id;
                                break;
                            }
                        }
                    }
                }

                if (guanyador_id !== null) {
                    var input = document.createElement("input");
                    input.type = "hidden";
                    input.name = "equip_" + equip_index;
                    input.value = guanyador_id;
                    formulari.appendChild(input);
                    equip_index++;
                }
            }
        }
    });
});
