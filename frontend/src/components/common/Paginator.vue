<template>
  <div v-if="pages > 1" class="d-flex flex-wrap justify-content-between align-items-center gap-2 p-3 border-top small">
    <span class="text-muted">Showing {{ from }}–{{ to }} of {{ total }}</span>
    <ul class="pagination pagination-sm mb-0">
      <li class="page-item" :class="{ disabled: modelValue === 1 }"><a class="page-link" href="#" @click.prevent="go(modelValue - 1)">‹</a></li>
      <li v-for="p in visible" :key="p" class="page-item" :class="{ active: p === modelValue }"><a class="page-link" href="#" @click.prevent="go(p)">{{ p }}</a></li>
      <li class="page-item" :class="{ disabled: modelValue === pages }"><a class="page-link" href="#" @click.prevent="go(modelValue + 1)">›</a></li>
    </ul>
  </div>
</template>
<script>
export default {
  name: 'Paginator',
  props: { modelValue: Number, total: Number, perPage: { type: Number, default: 10 } },
  emits: ['update:modelValue'],
  computed: {
    pages () { return Math.max(1, Math.ceil(this.total / this.perPage)) },
    from () { return this.total ? (this.modelValue - 1) * this.perPage + 1 : 0 },
    to () { return Math.min(this.total, this.modelValue * this.perPage) },
    visible () {
      const s = Math.max(1, Math.min(this.modelValue - 2, this.pages - 4))
      return Array.from({ length: Math.min(5, this.pages) }, (_, i) => s + i)
    }
  },
  methods: { go (p) { if (p >= 1 && p <= this.pages) this.$emit('update:modelValue', p) } }
}
</script>
