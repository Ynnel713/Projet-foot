import { Star } from "lucide-react";

// Étoiles pleines/vides -- value/max (ex. pied faible, /5). Purement
// visuel, pas de logique de calcul ici (voir starRating() dans utils/stars.js
// pour la note en étoiles par percentile, un besoin différent).
export default function StarRating({ value, max = 5, size = 12 }) {
  return (
    <span className="inline-flex items-center gap-0.5">
      {Array.from({ length: max }, (_, i) => (
        <Star key={i} size={size} className={i < value ? "text-gold" : "text-white/20"} fill={i < value ? "currentColor" : "none"} />
      ))}
    </span>
  );
}
