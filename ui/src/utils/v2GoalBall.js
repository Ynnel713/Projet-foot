// Ballon d'un but marqué entre deux images (~1 s d'écart) : le moteur remet le ballon au centre dans le pas même où il
// franchit la ligne, aucune image ne le montre donc dans le but. Avant la minute du but, le ballon file vers le centre du
// but adverse de l'équipe qui marque (domicile attaque vers x = longueur, D-V03) ; après, il reste au fond jusqu'à
// l'image suivante. Renvoie null s'il n'y a pas de but entre les deux images (interpolation ordinaire).
export function goalBall(a, b, minute, goals, length, width) {
  const goal = goals.find((g) => g.minute > a.minute && g.minute <= b.minute);
  if (!goal) return null;
  const target = { x: goal.team === "home" ? length : 0, y: width / 2 };
  if (minute >= goal.minute) return target;
  const f = (minute - a.minute) / (goal.minute - a.minute);
  return { x: a.ball.x + (target.x - a.ball.x) * f, y: a.ball.y + (target.y - a.ball.y) * f };
}
