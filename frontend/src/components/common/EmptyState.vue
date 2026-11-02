<template>
  <div class="empty-state">
    <i :class="'bi bi-' + icon"></i>
    <h6 class="mt-3 mb-1 text-body">{{ title }}</h6>
    <p class="small mb-3">{{ text }}</p>
    <slot />
  </div>
</template>
<script>
export default { name: 'EmptyState', props: { icon: { type: String, default: 'inbox' }, title: { type: String, default: 'Nothing here yet' }, text: String } }
</script>
