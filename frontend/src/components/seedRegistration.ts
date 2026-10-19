/** Sugerencia de interfaz. La API conserva la validación definitiva de unicidad. */
export function suggestSeedIdentifier(kind: 'real' | 'hypothetical', existing: readonly string[],
  randomId: () => string = () => crypto.randomUUID()): string {
  const prefix = kind === 'real' ? 'SEM' : 'EST'
  const used = new Set(existing)
  let suggestion: string
  do { suggestion = `${prefix}-${randomId().replaceAll('-', '').slice(0, 12).toUpperCase()}` } while (used.has(suggestion))
  return suggestion
}
