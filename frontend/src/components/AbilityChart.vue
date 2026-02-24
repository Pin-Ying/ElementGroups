<template>
  <div ref="chartEl" class="ability-chart"></div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  props: {
    elInfo: { type: Object, required: true }
  },
  mounted() {
    this.chart = echarts.init(this.$refs.chartEl)
    this.drawChart()
    window.addEventListener('resize', this.handleResize)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize)
    if (this.chart) this.chart.dispose()
  },
  watch: {
    elInfo: {
      handler() { this.drawChart() },
      deep: true
    }
  },
  methods: {
    handleResize() {
      if (this.chart) this.chart.resize()
    },
    drawChart() {
      const info = this.elInfo
      if (!info || !info.abMax) return

      const option = {
        backgroundColor: 'rgb(8, 3, 20)',
        darkMode: true,
        textStyle: { color: 'rgba(180, 200, 230, 0.85)', fontSize: 15 },
        grid: { top: '10%', bottom: '10%', left: '15%', right: '15%' },
        title: {
          text: 'ABILITY',
          top: 5,
          left: 'center',
          textStyle: { color: '#fff', fontSize: 30 }
        },
        legend: {
          bottom: 5,
          data: [info.Name],
          itemGap: 20,
          textStyle: { color: '#fff', fontSize: 20 }
        },
        radar: {
          radius: '60%',
          indicator: [
            { name: 'MP(K)', max: info.abMax.MeltingPoint },
            { name: 'BP(K)', max: info.abMax.BoilingPoint },
            { name: 'EA(eV)', max: info.abMax.ElectronAffinity },
            { name: 'χ(Pauling Scale)', max: info.abMax.Electronegativity },
            { name: 'r(van der Waals)', max: info.abMax.AtomicRadius },
            { name: 'IE(eV)', max: info.abMax.IonizationEnergy },
            { name: 'D(g/cm³)', max: info.abMax.Density }
          ],
          splitNumber: 4,
          nameGap: 25,
          axisLabel: {
            show: true,
            hideOverlap: true,
            formatter(value) {
              return value > 0 ? value.toFixed(1) : ''
            }
          }
        },
        series: [
          {
            name: info.Name,
            type: 'radar',
            color: '#64b8e8',
            areaStyle: { opacity: 0.35 },
            data: [
              {
                value: [
                  info.MeltingPoint, info.BoilingPoint,
                  info.ElectronAffinity, info.Electronegativity,
                  info.AtomicRadius, info.IonizationEnergy, info.Density
                ],
                name: info.Name
              }
            ]
          }
        ]
      }
      this.chart.setOption(option)
    }
  }
}
</script>

<style scoped>
.ability-chart {
  width: 100%;
  min-width: 600px;
  min-height: 80vh;
  margin: 5px auto;
  border: 1px solid rgba(228, 251, 255, 0.15);
  border-radius: 6px;
  box-shadow: 0 0 30px rgba(70, 0, 140, 0.2), 0 0 60px rgba(0, 80, 180, 0.1);
}

@media only screen and (max-width: 800px) {
  .ability-chart {
    min-width: 90%;
    overflow: auto;
  }
}
</style>
