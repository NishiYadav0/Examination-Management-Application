<template>
  <component :is="layout">
    <router-view v-slot="{ Component }">
      <transition name="page" mode="out-in">
        <component :is="Component" :key="$route.fullPath" />
      </transition>
    </router-view>
  </component>
  <ToastContainer />
  <ConfirmDialog />
</template>

<script>
import PublicLayout from '@/layouts/PublicLayout.vue'
import DashboardLayout from '@/layouts/DashboardLayout.vue'
import BlankLayout from '@/layouts/BlankLayout.vue'
import ToastContainer from '@/components/common/ToastContainer.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

export default {
  name: 'App',
  components: { PublicLayout, DashboardLayout, BlankLayout, ToastContainer, ConfirmDialog },
  computed: {
    layout () {
      const l = this.$route.meta.layout
      return l === 'dashboard' ? 'DashboardLayout' : l === 'blank' ? 'BlankLayout' : 'PublicLayout'
    }
  },
  created () {
    // refresh the logged-in user (also detects blocked accounts)
    if (this.$store.getters['auth/isLoggedIn']) {
      this.$store.dispatch('auth/fetchMe').catch(() => {})
      this.$store.dispatch('notif/load')
    }
  }
}
</script>

<style>
.page-enter-active, .page-leave-active { transition: opacity .18s ease, transform .18s ease; }
.page-enter-from { opacity: 0; transform: translateY(6px); }
.page-leave-to { opacity: 0; }
</style>
