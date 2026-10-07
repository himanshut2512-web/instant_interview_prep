// Small formatting helpers shared by pages.

export function timeAgo(iso) {
  if (!iso) return ''
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return ''
  const seconds = Math.round((Date.now() - then) / 1000)
  if (seconds < 45) return 'just now'
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours} h ago`
  const days = Math.round(hours / 24)
  if (days < 7) return `${days} day${days === 1 ? '' : 's'} ago`
  return new Date(iso).toLocaleDateString()
}

export function initials(name) {
  const words = String(name || '?')
    .replace(/[^\p{L}\p{N}\s]/gu, ' ')
    .split(/\s+/)
    .filter(Boolean)
  if (!words.length) return '?'
  return (words.length === 1 ? words[0].slice(0, 2) : words[0][0] + words[1][0]).toUpperCase()
}

// Curated gradients that keep white initials readable.
const AVATAR_GRADIENTS = [
  ['#4f46e5', '#7c3aed'],
  ['#2563eb', '#0e7490'],
  ['#0f766e', '#047857'],
  ['#be185d', '#9d174d'],
  ['#c2410c', '#9a3412'],
  ['#6d28d9', '#a21caf'],
  ['#1d4ed8', '#4338ca'],
  ['#334155', '#1e293b'],
]

export function avatarStyle(name) {
  let hash = 0
  for (const ch of String(name || '')) hash = (hash * 31 + ch.codePointAt(0)) >>> 0
  const [a, b] = AVATAR_GRADIENTS[hash % AVATAR_GRADIENTS.length]
  return { background: `linear-gradient(140deg, ${a}, ${b})` }
}

export function seniority(years) {
  const y = Number(years)
  if (Number.isNaN(y)) return ''
  if (y < 1) return 'Fresher / entry level'
  if (y < 3) return 'Junior'
  if (y < 6) return 'Mid-level'
  if (y < 10) return 'Senior'
  return 'Lead / principal'
}

export function pct(part, total) {
  return total > 0 ? Math.round((100 * part) / total) : 0
}

export function plural(n, word, pluralWord) {
  return `${n} ${n === 1 ? word : pluralWord || `${word}s`}`
}
