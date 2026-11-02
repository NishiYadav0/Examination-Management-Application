<template>
  <div class="card-emp stat-card h-100 hover-lift" :style="{ color }">
    <div class="card-body d-flex align-items-center gap-3">
      <span class="icon-box" :style="{ background: color + '1a', color }"><i :class="'bi bi-' + icon"></i></span>
      <div class="min-w-0">
        <div class="stat-value text-body">{{ value }}</div>
        <div class="stat-label">{{ label }}</div>
        <div v-if="hint" class="small mt-1" style="color: var(--emp-muted)">{{ hint }}</div>
      </div>
    </div>
    <router-link v-if="to" :to="to" class="stretched-link" :aria-label="label"></router-link>
  </div>
</template>
<script>
export default {
  name: 'StatCard',
  props: { label: String, value: [Number, String], icon: String, color: { type: String, default: '#4f46e5' }, hint: String, to: String }
}
</script>
