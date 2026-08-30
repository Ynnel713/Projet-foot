import { useGameStore } from "../../store/useGameStore";

export default function Header() {
  const activeCompetitionLabel = useGameStore((s) => s.activeCompetitionLabel);

  return (
    <header className="h-12 shrink-0 flex items-center justify-between px-4 bg-surface border-b border-white/5">
      <div className="flex items-center gap-2 min-w-0">
        <img src="/icons/logo-mark.png" alt="" className="h-7 w-7 rounded-md shrink-0" />
        <span className="font-semibold text-sm tracking-tight truncate">Simulafoot</span>
      </div>
      <span className="text-xs text-gray-400 truncate px-2">
        {activeCompetitionLabel ?? "Saison 2026-2027"}
      </span>
    </header>
  );
}
