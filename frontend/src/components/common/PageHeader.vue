<template>
  <div class="page-header d-flex flex-wrap align-items-center justify-content-between gap-3 fade-in">
    <div>
      <nav v-if="crumbs && crumbs.length" aria-label="breadcrumb">
        <ol class="breadcrumb small mb-1">
          <li v-for="(c, i) in crumbs" :key="i" class="breadcrumb-item" :class="{ active: !c.to }">
            <router-link v-if="c.to" :to="c.to">{{ c.label }}</router-link><span v-else>{{ c.label }}</span>
          </li>
        </ol>
      </nav>
      <h1>{{ title }}</h1>
      <p v-if="subtitle" class="text-muted mb-0 mt-1">{{ subtitle }}</p>
    </div>
    <div class="d-flex flex-wrap gap-2"><slot /></div>
  </div>
</template>
<script>
export default { name: 'PageHeader', props: { title: String, subtitle: String, crumbs: Array } }
</script>
