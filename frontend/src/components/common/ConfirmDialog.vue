<template>
  <BaseModal :show="!!c" :title="c ? c.title || 'Are you sure?' : ''" size="" @close="answer(false)">
    <div v-if="c" class="text-center py-2">
      <span class="icon-box mb-3" :class="'bg-' + variant + ' bg-opacity-10 text-' + variant" style="width:64px;height:64px;font-size:1.8rem">
        <i :class="'bi bi-' + (c.icon || 'question-circle')"></i>
      </span>
      <p class="mb-0">{{ c.message }}</p>
      <div v-if="c.input" class="mt-3 text-start">
        <label class="form-label">{{ c.input }}</label>
        <textarea v-model="text" class="form-control" rows="2" :placeholder="c.placeholder || ''"></textarea>
      </div>
    </div>
    <template #footer>
      <button class="btn btn-light" @click="answer(false)">{{ (c && c.cancelText) || 'Cancel' }}</button>
      <button class="btn" :class="'btn-' + variant" @click="answer(true)">{{ (c && c.confirmText) || 'Confirm' }}</button>
    </template>
  </BaseModal>
</template>
<script>
import BaseModal from './BaseModal.vue'
// Promise-based confirm dialog: const ok = await this.$confirm({...})
// When `input` is set the promise resolves to the typed text (or false)
export default {
  name: 'ConfirmDialog',
  components: { BaseModal },
  data: () => ({ text: '' }),
  computed: {
    c () { return this.$store.state.ui.confirm },
    variant () { return (this.c && this.c.variant) || 'primary' }
  },
  watch: { c () { this.text = '' } },
  methods: {
    answer (v) {
      if (!this.c) return
      this.c.resolve(v ? (this.c.input ? (this.text || ' ') : true) : false)
    }
  }
}
</script>
