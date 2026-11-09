<template>
  <button class="btn btn-icon btn-soft" @click="toggle" :title="dark ? 'Switch to light mode' : 'Switch to dark mode'" aria-label="Toggle theme">
    <i :class="dark ? 'bi bi-sun' : 'bi bi-moon-stars'"></i>
  </button>
</template>
<script>
export default {
  name: 'ThemeToggle',
  computed: { dark () { return this.$store.state.ui.theme === 'dark' } },
  methods: { toggle () { this.$store.commit('ui/setTheme', this.dark ? 'light' : 'dark') } }
}
</script>
