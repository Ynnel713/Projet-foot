// Ticket v2-ecran-match/14b : valeurs attendues (matchStats d'EM-14a) sur la trace réelle complète, à quelques instants.
// Usage (depuis ui/) : node ../.scratch/v2-ecran-match/mesures/em14b-attendu.mjs <trace.json> <minute>...
import { readFileSync } from "node:fs";
import { holderTeams, matchStats, possessionPrefix } from "../../../ui/src/utils/matchStats.js";
const [file, ...minutes] = process.argv.slice(2);
const tr = JSON.parse(readFileSync(file));
const prefix = possessionPrefix(holderTeams(tr.ticks));
const out = {};
for (const m of minutes) out[m] = matchStats({ events: tr.events, prefix, minute: Math.floor(+m * 60) / 60, tickSeconds: tr.tick_seconds });
console.log(JSON.stringify(out));
