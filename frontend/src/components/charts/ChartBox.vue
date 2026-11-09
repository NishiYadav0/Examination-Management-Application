<template>
  <div class="position-relative" :style="{ height: height + 'px' }">
    <canvas ref="canvas"></canvas>
    <div v-if="empty" class="position-absolute top-50 start-50 translate-middle text-muted small text-center">
      <i class="bi bi-bar-chart d-block fs-3 opacity-50"></i>No data yet
    </div>
  </div>
</template>

<script>
import Chart from 'chart.js/auto'

export const PALETTE = ['#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#64748b']

export default {
  name: 'ChartBox',
  props: {
    type: { type: String, default: 'bar' },
    labels: { type: Array, default: () => [] },
    datasets: { type: Array, default: () => [] },
    options: { type: Object, default: () => ({}) },
    height: { type: Number, default: 280 }
  },
  computed: {
    theme () { return this.$store.state.ui.theme },
    empty () { return !this.datasets.length || this.datasets.every(d => !d.data || !d.data.some(v => Number(v) > 0)) }
  },
  watch: {
    labels: { handler () { this.render() }, deep: true },
    datasets: { handler () { this.render() }, deep: true },
    theme () { this.render() }
  },
  mounted () { this.render() },
  beforeUnmount () { if (this.chart) this.chart.destroy() },
  methods: {
    render () {
      if (this.chart) this.chart.destroy()
      const dark = this.theme === 'dark'
      const text = dark ? '#94a3b8' : '#64748b'
      const grid = dark ? 'rgba(255,255,255,.06)' : 'rgba(15,23,42,.06)'
      const round = ['doughnut', 'pie', 'polarArea'].includes(this.type)
      const datasets = this.datasets.map((d, i) => {
        const color = d.color || PALETTE[i % PALETTE.length]
        const base = { borderWidth: round ? 0 : 2, ...d }
        if (round) return { backgroundColor: PALETTE, hoverOffset: 8, ...base }
        if (this.type === 'line') return { borderColor: color, backgroundColor: color + '22', fill: true, tension: .4, pointRadius: 3, pointBackgroundColor: color, ...base }
        return { backgroundColor: d.colors || color, borderRadius: 8, maxBarThickness: 38, borderWidth: 0, ...base }
      })
      this.chart = new Chart(this.$refs.canvas, {
        type: this.type,
        data: { labels: this.labels, datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: round || datasets.length > 1, position: round ? 'bottom' : 'top', labels: { color: text, usePointStyle: true, boxWidth: 8, padding: 14, font: { family: 'Plus Jakarta Sans' } } },
            tooltip: { backgroundColor: '#0f172a', padding: 10, cornerRadius: 10, titleFont: { family: 'Plus Jakarta Sans' }, bodyFont: { family: 'Plus Jakarta Sans' } }
          },
          cutout: this.type === 'doughnut' ? '68%' : undefined,
          scales: round ? {} : {
            x: { grid: { display: false }, ticks: { color: text, font: { family: 'Plus Jakarta Sans', size: 11 } }, border: { display: false } },
            y: { beginAtZero: true, grid: { color: grid }, ticks: { color: text, precision: 0, font: { family: 'Plus Jakarta Sans', size: 11 } }, border: { display: false } }
          },
          ...this.options
        }
      })
    }
  }
}
</script>
