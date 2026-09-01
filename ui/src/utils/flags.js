// Les noms de sélection viennent préfixés d'un emoji drapeau (voir
// nations.py, sourcé du classeur) -- mais les emoji drapeau ne s'affichent
// pas de façon fiable partout (Windows en particulier rend souvent le code
// pays en toutes lettres au lieu du drapeau). On décode l'emoji en code ISO
// pour afficher une vraie image de drapeau (flagcdn.com) à la place, sans
// avoir à maintenir une table de correspondance nom -> pays à la main.
const REGIONAL_INDICATOR_BASE = 0x1f1e6; // 🇦
const TAG_BASE = 0xe0000; // début du bloc "tag" Unicode
const TAG_CANCEL = 0xe007f;
const BLACK_FLAG = 0x1f3f4; // 🏴 -- préfixe des drapeaux de subdivision (Angleterre, Écosse, Pays de Galles)

function flagEmojiToCountryCode(emoji) {
  const points = Array.from(emoji);
  if (points.length === 0) return null;

  const first = points[0].codePointAt(0);

  // Cas standard : deux "regional indicator symbols" (ex. 🇫🇷 -> "fr").
  if (points.length >= 2) {
    const second = points[1].codePointAt(0);
    if (
      first >= REGIONAL_INDICATOR_BASE &&
      first <= REGIONAL_INDICATOR_BASE + 25 &&
      second >= REGIONAL_INDICATOR_BASE &&
      second <= REGIONAL_INDICATOR_BASE + 25
    ) {
      const a = String.fromCharCode(97 + (first - REGIONAL_INDICATOR_BASE));
      const b = String.fromCharCode(97 + (second - REGIONAL_INDICATOR_BASE));
      return a + b;
    }
  }

  // Cas subdivision (Angleterre/Écosse/Pays de Galles) : 🏴 + séquence de
  // "tags" épelant le code (ex. "gbeng") + tag d'annulation.
  if (first === BLACK_FLAG) {
    let code = "";
    for (let i = 1; i < points.length; i++) {
      const cp = points[i].codePointAt(0);
      if (cp === TAG_CANCEL) break;
      if (cp >= TAG_BASE + 0x61 && cp <= TAG_BASE + 0x7a) {
        code += String.fromCharCode(97 + (cp - TAG_BASE - 0x61));
      }
    }
    if (code.length > 2) return `${code.slice(0, 2)}-${code.slice(2)}`;
    return code || null;
  }

  return null;
}

// Le nom d'une sélection commence par l'emoji drapeau suivi d'un espace
// (voir nations.py) ; un nom de club n'a pas ce préfixe -- ne couper le
// premier mot que s'il se décode vraiment en drapeau, sinon un nom de club
// à espace ("Real Madrid") perdrait son premier mot pour rien.
// { code: code pays flagcdn ou null, label: le nom (sans l'emoji si trouvé) }.
export function parseFlaggedName(name) {
  const match = name.match(/^(\S+)\s+(.*)$/);
  if (!match) return { code: null, label: name };
  const code = flagEmojiToCountryCode(match[1]);
  return code ? { code, label: match[2] } : { code: null, label: name };
}

export function flagUrl(code) {
  return code ? `https://flagcdn.com/w40/${code}.png` : null;
}
