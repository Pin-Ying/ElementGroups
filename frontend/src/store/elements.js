import { reactive } from 'vue'
import { getElements } from '../api'

const state = reactive({ elements: [], loaded: false })

export async function ensureElements() {
  if (state.loaded) return
  const res = await getElements()
  state.elements = res.data.elements
  state.loaded = true
}

export const elementsState = state
