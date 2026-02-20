<template>
  <div v-if="elInfo">
    <div class="element-btns">
      <div>
        <router-link
          class="button"
          :to="'/stroy/' + fEl.Symbol"
          :style="{ borderColor: '#' + fEl.CPKHexColor }"
        >
          PREVIOUS ELEMENT
        </router-link>
      </div>
      <div class="title column">{{ elInfo.Symbol }}'s Story</div>
      <div>
        <router-link
          class="button"
          :to="'/stroy/' + bEl.Symbol"
          :style="{ borderColor: '#' + bEl.CPKHexColor }"
        >
          NEXT ELEMENT
        </router-link>
      </div>
    </div>

    <div class="element-story">
      <div class="element-grid">
        <img
          :style="{ borderColor: '#' + elInfo.CPKHexColor }"
          :src="imgSrc || altImage"
          :title="elInfo.Name"
          alt="Still Creating..."
        />
        <div
          class="element-grid-info"
          :style="{
            borderColor: '#' + elInfo.CPKHexColor,
            backgroundColor: '#' + elInfo.CPKHexColor + '33'
          }"
          id="main-content"
        >
          <div class="title">Atomic NUMBER: {{ elInfo.AtomicNumber }}</div>
          <div class="subtitle">
            {{ elInfo.Name }} / {{ elInfo.Symbol }} / {{ elInfo.ElectronConfiguration }}
          </div>
          <div>
            <template v-if="story">
              <span v-html="story.replace(/\\n/g, '<br>')"></span>
            </template>
            <template v-else>Still Creating...</template>
          </div>
        </div>
      </div>

      <div id="element-ability" :style="{ borderColor: '#' + elInfo.CPKHexColor }">
        <template v-for="ab in abilities" :key="ab.key">
          <div>{{ ab.label }}</div>
          <div class="ability-bar" :style="{ width: abilityWidth(ab.key) }"></div>
        </template>
      </div>

      <AbilityChart v-if="abilityData" :elInfo="abilityData" />
    </div>
  </div>
</template>

<script>
import { getElementDetail, getElementAbility } from '../api'
import AbilityChart from '../components/AbilityChart.vue'

const ABILITIES = [
  { key: 'MeltingPoint', label: 'MeltingPoint (K)' },
  { key: 'BoilingPoint', label: 'BoilingPoint (K)' },
  { key: 'ElectronAffinity', label: 'ElectronAffinity (eV)' },
  { key: 'Electronegativity', label: 'Electronegativity (Pauling Scale)' },
  { key: 'AtomicRadius', label: 'AtomicRadius (van der Waals)' },
  { key: 'IonizationEnergy', label: 'IonizationEnergy (eV)' },
  { key: 'Density', label: 'Density (g/cm³)' }
]

export default {
  components: { AbilityChart },
  props: { symbol: { type: String, required: true } },
  data() {
    return {
      elInfo: null,
      fEl: {},
      bEl: {},
      story: null,
      imgSrc: null,
      altImage: '',
      abilityData: null,
      abilities: ABILITIES
    }
  },
  watch: {
    symbol: {
      immediate: true,
      handler() { this.loadData() }
    }
  },
  methods: {
    async loadData() {
      try {
        const [detailRes, abilityRes] = await Promise.all([
          getElementDetail(this.symbol),
          getElementAbility(this.symbol)
        ])

        const detail = detailRes.data
        this.elInfo = detail.el_info
        this.fEl = detail.f_el
        this.bEl = detail.b_el
        this.story = detail.story
        this.imgSrc = detail.img_src
        this.altImage = detail.alt_image

        this.abilityData = abilityRes.data
      } catch (e) {
        console.error('Failed to load element data:', e)
      }
    },
    abilityWidth(key) {
      if (!this.abilityData || !this.abilityData.abMax) return '0%'
      const value = this.abilityData[key] / this.abilityData.abMax[key] * 100
      return (isNaN(value) ? 0 : value) + '%'
    }
  }
}
</script>

<style scoped>
#main-content {
  display: grid;
  text-align: left;
  border: #ffffff solid 2px;
  border-radius: 2px;
  font-size: 20px;
  margin: 5px;
  padding: 20px 10px;
}

#element-ability {
  display: grid;
  grid-template-columns: 1fr 2fr;
  grid-auto-rows: 50px;
  gap: 5px;
  text-align: left;
  width: 100%;
  margin: 5px auto;
  padding: 20px 10px;
  border: #e4fbff solid 2px;
  border-radius: 2px;
}

.button {
  border-width: 2px;
  min-width: 200px;
}

.element-btns {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
  align-items: center;
}

.element-story {
  width: 100%;
  display: grid;
}

.element-grid {
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 2fr;
  align-items: center;
  justify-items: center;
  gap: 10px;
  margin: 5px auto;
}

.element-grid-info {
  height: 100%;
  width: 100%;
  grid-template-rows: 1fr 0.5fr 2.5fr;
}

.ability-bar {
  background-color: #e4fbff;
  color: #000000;
}

@media only screen and (max-width: 800px) {
  img,
  #element-ability {
    width: 90%;
  }

  .element-btns {
    display: block;
  }

  .element-grid {
    grid-template-columns: 1fr;
  }

  .element-grid-info {
    width: 90%;
  }
}
</style>
