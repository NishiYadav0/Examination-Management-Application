<template>
  <div class="py-2">
    <div class="row g-3 mb-3" v-if="cards">
      <div class="col-6 col-xl-3" v-for="i in 4" :key="i"><div class="skeleton" style="height:96px"></div></div>
    </div>
    <div class="skeleton mb-2" v-for="i in rows" :key="'r' + i" :style="{ height: '46px', opacity: 1 - i * 0.12 }"></div>
  </div>
</template>
<script>
export default { name: 'LoadingBlock', props: { rows: { type: Number, default: 5 }, cards: Boolean } }
</script>
