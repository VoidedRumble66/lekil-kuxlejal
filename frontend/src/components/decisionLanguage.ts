/** Traducción de presentación: preserva los valores y contratos de la API. */
export const agriculturalMessage = (text: string) => text === 'Factibilidad agrícola no evaluada'
  ? 'Aún no sabemos si estos recursos bastan para los cultivos' : text
export const priorityMessage = (root: boolean) => root ? 'No aplica al domo general' : 'Sin prioridad registrada'
