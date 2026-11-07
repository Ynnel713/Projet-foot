// Rejeu de développement (ticket v2-ecran-match/00) : charge une trace de match RÉELLE enregistrée par
// `scripts/record_v2_trace.py` dans ./fixtures (ignoré par git). Importé uniquement derrière `import.meta.env.DEV` :
// absent du build de production. Les fichiers pèsent ~20 Mo : on les lit par `fetch` (JSON natif) plutôt que par un
// `import`, que Vite transformerait en module JavaScript (plus de 20 s).
const urls = import.meta.glob("./fixtures/*.json", { query: "?url", import: "default", eager: true });

export async function loadFixture(name) {
  const url = urls[`./fixtures/${name}.json`];
  if (!url) throw new Error(`Trace introuvable : ${name}`);
  return (await fetch(url)).json();
}
