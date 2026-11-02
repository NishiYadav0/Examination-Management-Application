<template>
  <span class="badge-soft d-inline-flex align-items-center gap-1" :class="'bs-' + meta.color">
    <i v-if="!noIcon" :class="'bi bi-' + meta.icon" style="font-size:.7rem"></i>{{ label || meta.label }}
  </span>
</template>
<script>
import { statusMeta } from '@/utils/format'
export default {
  name: 'StatusBadge',
  props: { status: String, label: String, noIcon: Boolean },
  computed: { meta () { return statusMeta(this.status) } }
}
</script>
