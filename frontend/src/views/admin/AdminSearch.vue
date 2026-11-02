<template>
  <div>
    <PageHeader title="Global search" subtitle="Find students, examiners, examinations, courses and bookings in one place." :crumbs="[{ label: 'Admin', to: '/admin' }, { label: 'Search' }]" />
    <form class="search-hero card-emp p-3 mb-4" @submit.prevent="go">
      <div class="input-group input-group-lg">
        <span class="input-group-text bg-transparent border-0"><i class="bi bi-search"></i></span>
        <input v-model="q" class="form-control border-0 shadow-none" placeholder="Type at least 2 characters… e.g. viva, 23F1000003, Ananya" autofocus>
        <button class="btn btn-gradient px-4">Search</button>
      </div>
    </form>
    <LoadingBlock v-if="loading" />
    <template v-else-if="res">
      <EmptyState v-if="!total" icon="search" title="No matches" :text="`Nothing matched “${$route.query.q}”.`" />
      <div class="row g-4">
        <div class="col-lg-6" v-if="res.students.length">
          <div class="card-emp h-100"><div class="card-header"><i class="bi bi-mortarboard me-2 text-primary"></i>Students ({{ res.students.length }})</div>
            <div class="list-group list-group-flush">
              <router-link v-for="u in res.students" :key="u.id" :to="'/admin/users/' + u.id" class="list-group-item list-group-item-action bg-transparent d-flex gap-2 align-items-center">
                <span class="avatar avatar-sm">{{ $f.initials(u.name) }}</span><div class="flex-grow-1"><div class="fw-semibold">{{ u.name }}</div><small class="text-muted">{{ u.profile.roll_no }} · {{ u.email }}</small></div><StatusBadge :status="u.active ? 'active' : 'blocked'" />
              </router-link>
            </div></div>
        </div>
        <div class="col-lg-6" v-if="res.examiners.length">
          <div class="card-emp h-100"><div class="card-header"><i class="bi bi-person-badge me-2 text-primary"></i>Examiners ({{ res.examiners.length }})</div>
            <div class="list-group list-group-flush">
              <router-link v-for="u in res.examiners" :key="u.id" :to="'/admin/users/' + u.id" class="list-group-item list-group-item-action bg-transparent d-flex gap-2 align-items-center">
                <span class="avatar avatar-sm">{{ $f.initials(u.name) }}</span><div class="flex-grow-1"><div class="fw-semibold">{{ u.name }}</div><small class="text-muted">{{ u.profile.department }} · {{ u.email }}</small></div><StatusBadge :status="u.active ? 'active' : 'blocked'" />
              </router-link>
            </div></div>
        </div>
        <div class="col-lg-6" v-if="res.exams.length">
          <div class="card-emp h-100"><div class="card-header"><i class="bi bi-clipboard2-check me-2 text-primary"></i>Examinations ({{ res.exams.length }})</div>
            <div class="list-group list-group-flush">
              <router-link v-for="e in res.exams" :key="e.id" :to="'/admin/exams/' + e.id" class="list-group-item list-group-item-action bg-transparent d-flex justify-content-between align-items-center">
                <div><div class="fw-semibold">{{ e.name }}</div><small class="text-muted">{{ e.course_code }} · {{ e.exam_type }}</small></div><StatusBadge :status="e.status" />
              </router-link>
            </div></div>
        </div>
        <div class="col-lg-6" v-if="res.courses.length">
          <div class="card-emp h-100"><div class="card-header"><i class="bi bi-journal-bookmark me-2 text-primary"></i>Courses ({{ res.courses.length }})</div>
            <div class="list-group list-group-flush">
              <router-link v-for="c in res.courses" :key="c.id" :to="'/admin/exams?course_id=' + c.id" class="list-group-item list-group-item-action bg-transparent">
                <b class="text-primary">{{ c.code }}</b> {{ c.name }} <small class="text-muted">· {{ c.exam_count }} exams</small>
              </router-link>
            </div></div>
        </div>
        <div class="col-12" v-if="res.bookings.length">
          <div class="card-emp"><div class="card-header"><i class="bi bi-bookmark-star me-2 text-primary"></i>Bookings ({{ res.bookings.length }})</div>
            <BookingTable :bookings="res.bookings" show-exam @changed="go" /></div>
        </div>
      </div>
    </template>
    <EmptyState v-else icon="search-heart" title="Start typing to search" text="Search by name, e-mail, roll number, employee ID, course code, exam name or booking number." />
  </div>
</template>
<script>
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import BookingTable from '@/components/admin/BookingTable.vue'
export default {
  name: 'AdminSearch',
  components: { PageHeader, LoadingBlock, EmptyState, StatusBadge, BookingTable },
  data () { return { q: this.$route.query.q || '', res: null, loading: false } },
  computed: { total () { return this.res ? Object.values(this.res).reduce((a, l) => a + l.length, 0) : 0 } },
  mounted () { if (this.q) this.search() },
  methods: {
    go () { if (this.q.trim().length < 2) return this.$toast('Type at least 2 characters', 'warning'); this.$router.replace({ query: { q: this.q.trim() } }); this.search() },
    async search () {
      this.loading = true
      try { this.res = (await api.get('/admin/search', { params: { q: this.q.trim() } })).data.data } catch (e) { this.$error(e) }
      this.loading = false
    }
  }
}
</script>
