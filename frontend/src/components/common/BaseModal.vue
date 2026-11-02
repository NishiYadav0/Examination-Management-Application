<template>
  <teleport to="body">
    <div class="modal fade" tabindex="-1" ref="el" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable" :class="size ? 'modal-' + size : ''">
        <div class="modal-content">
          <div class="modal-header">
            <div class="d-flex align-items-center gap-2">
              <span v-if="icon" class="icon-box bg-primary bg-opacity-10 text-primary" style="width:38px;height:38px;font-size:1.05rem"><i :class="'bi bi-' + icon"></i></span>
              <div>
                <h5 class="modal-title mb-0">{{ title }}</h5>
                <small v-if="subtitle" class="text-muted">{{ subtitle }}</small>
              </div>
            </div>
            <button type="button" class="btn-close" @click="$emit('close')" aria-label="Close"></button>
          </div>
          <div class="modal-body"><slot /></div>
          <div v-if="$slots.footer" class="modal-footer"><slot name="footer" /></div>
        </div>
      </div>
    </div>
  </teleport>
</template>
<script>
import { Modal } from 'bootstrap'
// Bootstrap modal controlled by the `show` prop. Handles fast show/hide sequences
// (e.g. two confirm dialogs in a row) by waiting for each transition to finish.
export default {
  name: 'BaseModal',
  props: { show: Boolean, title: String, subtitle: String, icon: String, size: String },
  emits: ['close'],
  data: () => ({ state: 'hidden', requestedHide: false }),
  mounted () {
    this.modal = new Modal(this.$refs.el, { backdrop: 'static' })
    this.$refs.el.addEventListener('shown.bs.modal', () => { this.state = 'shown'; if (!this.unmounted) this.sync() })
    this.$refs.el.addEventListener('hidden.bs.modal', () => {
      this.state = 'hidden'
      const userClosed = !this.requestedHide && this.show
      this.requestedHide = false
      if (this.unmounted) return
      if (userClosed) this.$emit('close')
      this.$nextTick(() => this.sync())
    })
    this.sync()
  },
  beforeUnmount () {
    // The page may change (e.g. router.push after "Create") while the modal is still
    // animating. Disposing Bootstrap's Modal mid-animation makes its transition callback
    // crash ("Cannot read properties of null (reading 'style')"), so we close instantly
    // and dispose only after any running transition has finished.
    const modal = this.modal
    const el = this.$refs.el
    this.unmounted = true
    const cleanup = () => {
      try { modal && modal.dispose() } catch (e) { /* ignore */ }
      document.querySelectorAll('.modal-backdrop').forEach(b => b.remove())
      document.body.classList.remove('modal-open')
      document.body.style.removeProperty('overflow')
      document.body.style.removeProperty('padding-right')
    }
    if (!modal) return cleanup()
    if (el) el.classList.remove('show')
    if (this.state === 'shown') {
      try { modal._isShown = true; modal.hide() } catch (e) { /* ignore */ }
    }
    if (this.state === 'hidden') cleanup()
    else setTimeout(cleanup, 500) // longer than Bootstrap's 300 ms fade
  },
  watch: { show () { this.sync() } },
  methods: {
    sync () {
      if (this.show && this.state === 'hidden') { this.state = 'showing'; this.modal.show() } else if (!this.show && this.state === 'shown') { this.state = 'hiding'; this.requestedHide = true; this.modal.hide() }
    }
  }
}
</script>
