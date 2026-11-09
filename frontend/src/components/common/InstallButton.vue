<template>
  <button v-if="available" class="btn btn-sm btn-soft d-none d-md-inline-flex align-items-center gap-1" @click="install" title="Install EMP on your desktop / home screen">
    <i class="bi bi-download"></i> Install app
  </button>
</template>
<script>
// "Add to desktop" – uses the browser's beforeinstallprompt event (PWA)
export default {
  name: 'InstallButton',
  data: () => ({ available: !!window.__empInstallPrompt }),
  mounted () { window.addEventListener('emp:installable', this.on) },
  beforeUnmount () { window.removeEventListener('emp:installable', this.on) },
  methods: {
    on () { this.available = true },
    async install () {
      const p = window.__empInstallPrompt
      if (!p) return
      p.prompt()
      await p.userChoice
      window.__empInstallPrompt = null
      this.available = false
    }
  }
}
</script>
