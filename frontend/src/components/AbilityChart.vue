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
      if (!this.chart) return
      this.chart.resize()
      // 字級跟著容器寬度走，resize 後要重畫
      this.drawChart()
    },
    drawChart() {
      const info = this.elInfo
      if (!info || !info.abMax) return

      // 依容器寬度縮放字級，窄螢幕才不會被文字擠爆
      const width = this.$refs.chartEl?.clientWidth || 600
      const compact = width < 520
      const baseFont = compact ? 11 : 14

      const option = {
        backgroundColor: 'rgb(8, 3, 20)',
        darkMode: true,
        textStyle: { color: 'rgba(180, 200, 230, 0.85)', fontSize: baseFont },
        grid: { top: '10%', bottom: '10%', left: '15%', right: '15%' },
        legend: {
          bottom: 5,
          data: [info.Name],
          itemGap: 20,
          textStyle: { color: '#fff', fontSize: compact ? 13 : 16 }
        },
        radar: {
          radius: compact ? '58%' : '65%',
          axisName: { fontSize: baseFont, color: 'rgba(180, 200, 230, 0.85)' },
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
          nameGap: compact ? 12 : 20,
          axisLabel: {
            show: !compact,
            hideOverlap: true,
            fontSize: baseFont - 2,
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
  /* 高度隨視窗縮放，但夾在合理範圍內；原本固定 min-width: 600px
     會讓窄螢幕被迫橫向捲動 */
  height: clamp(360px, 68vh, 620px);
  margin: 5px auto;
  border: 1px solid rgba(228, 251, 255, 0.15);
  border-radius: 6px;
  box-shadow: 0 0 30px rgba(70, 0, 140, 0.2), 0 0 60px rgba(0, 80, 180, 0.1);
  box-sizing: border-box;
}

@media only screen and (max-width: 600px) {
  .ability-chart {
    height: clamp(300px, 55vh, 420px);
  }
}
</style>
