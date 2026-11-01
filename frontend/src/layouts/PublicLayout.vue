<template>
  <div class="d-flex flex-column min-vh-100">
    <PublicNavbar />
    <main class="flex-grow-1"><slot /></main>
    <PublicFooter />
  </div>
</template>
<script>
import PublicNavbar from '@/components/layout/PublicNavbar.vue'
import PublicFooter from '@/components/layout/PublicFooter.vue'
export default { name: 'PublicLayout', components: { PublicNavbar, PublicFooter } }
</script>
