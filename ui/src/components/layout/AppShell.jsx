import { useLocation } from "react-router-dom";
import Header from "./Header";
import BottomNav from "./BottomNav";

export default function AppShell({ children }) {
  // La vue terrain a besoin de toute la hauteur possible (terrain horizontal
  // en paysage) et affiche déjà son propre mini-en-tête (retour + score) --
  // l'en-tête global n'y apporte rien, juste 48px de terrain en moins.
  const hideHeader = useLocation().pathname.endsWith("/pitch");

  return (
    // h-dvh/w-dvw (dynamic viewport) plutôt que h-screen/100vh : évite le
    // bug où la barre d'adresse mobile fausse la hauteur réelle disponible.
    // overflow-hidden racine + overflow-x-hidden sur main : aucun défilement
    // horizontal possible, quel que soit le contenu (exigence explicite).
    // Le padding en env(safe-area-inset-*) protège des zones d'encoche/
    // indicateur home, qui passent sur les CÔTÉS en paysage sur iPhone.
    <div
      className="h-dvh w-dvw flex flex-col bg-bg text-gray-100 overflow-hidden"
      style={{ paddingLeft: "env(safe-area-inset-left)", paddingRight: "env(safe-area-inset-right)" }}
    >
      {!hideHeader && <Header />}
      {/* min-h-0 est indispensable : sans lui, un enfant flex-column ne se
          contracte jamais sous son contenu et overflow-y-auto ne fait rien. */}
      <main className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden relative">{children}</main>
      <BottomNav />
    </div>
  );
}
