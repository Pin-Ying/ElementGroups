import { reactive } from 'vue'
import { getElements } from '../api'
import { ELEMENT_SYMBOLS } from '../data/elementSymbols'

const state = reactive({
  elements: ELEMENT_SYMBOLS,  // pre-populated; enriched later when API responds
  loaded: false
})

export async function ensureElements() {
  if (state.loaded) return
  try {
    const res = await getElements()
    state.elements = res.data.elements  // richer data (Name, CPKHexColor, etc.)
    state.loaded = true
  } catch {
    // keep static fallback; do not mark loaded so a future call can retry
  }
}

export const elementsState = state
