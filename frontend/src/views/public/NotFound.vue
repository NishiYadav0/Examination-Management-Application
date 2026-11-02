<template>
  <div class="container text-center py-5 my-5">
    <div class="display-1 fw-800 gradient-text">404</div>
    <h3 class="fw-bold">Page not found</h3>
    <p class="text-muted">The page you are looking for doesn't exist or was moved.</p>
    <div class="d-flex justify-content-center gap-2">
      <router-link to="/" class="btn btn-gradient"><i class="bi bi-house me-1"></i>Go home</router-link>
      <router-link v-if="$store.getters['auth/isLoggedIn']" :to="$store.getters['auth/home']" class="btn btn-soft">Dashboard</router-link>
    </div>
  </div>
</template>
<script>export default { name: 'NotFound' }</script>
