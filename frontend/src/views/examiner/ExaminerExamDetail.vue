<template>
  <div>
    <LoadingBlock v-if="!exam" cards />
    <template v-else>
      <PageHeader :title="exam.name" :subtitle="exam.course_code + ' · ' + exam.course_name + ' · ' + exam.exam_type" :crumbs="[{ label: 'Examiner', to: '/examiner' }, { label: 'Exams', to: '/examiner/exams' }, { label: exam.name }]">
        <button v-if="exam.can_create_slots" class="btn btn-gradient" @click="openForm()"><i class="bi bi-calendar-plus me-1"></i>Create slot</button>
        <button v-if="exam.status === 'closed'" class="btn btn-success" @click="complete"><i class="bi bi-check2-circle me-1"></i>Mark examination completed</button>
      </PageHeader>

      <div class="banner mb-4" :class="exam.can_create_slots ? 'ok' : 'lock'">
        <i :class="exam.can_create_slots ? 'bi bi-unlock-fill' : 'bi bi-lock-fill'"></i>
        <div>
          <b>{{ exam.can_create_slots ? 'Slot creation is open' : 'Slot creation is closed' }}</b>
          <div class="small">{{ exam.can_create_slots ? `You can add, edit or remove slots until ${$f.fmtDate(exam.slot_creation_end)}. Slots can be scheduled between ${$f.fmtDate(exam.exam_start)} and ${$f.fmtDate(exam.exam_end)}.` : exam.slot_creation_message }}</div>
        </div>
        <StatusBadge class="ms-auto" :status="exam.status" />
      </div>

      <div class="row g-3 mb-4">
        <div class="col-6 col-md-3"><StatCard label="My slots" :value="exam.my_slots.filter(s => s.status !== 'cancelled').length" icon="calendar3-week" color="#4f46e5" /></div>
        <div class="col-6 col-md-3"><StatCard label="Booked students" :value="exam.summary.booked" icon="people" color="#06b6d4" /></div>
        <div class="col-6 col-md-3"><StatCard label="Evaluated" :value="exam.summary.evaluated" icon="clipboard-check" color="#10b981" /></div>
        <div class="col-6 col-md-3"><StatCard label="Pending" :value="exam.summary.pending" icon="hourglass-split" color="#f59e0b" /></div>
      </div>

      <div class="row g-4">
        <div class="col-xl-8">
          <div class="card-emp">
            <div class="card-header d-flex justify-content-between align-items-center"><span><i class="bi bi-calendar3-week me-2 text-primary"></i>My slots</span>
              <button v-if="exam.can_create_slots" class="btn btn-sm btn-soft" @click="openForm()"><i class="bi bi-plus-lg"></i> Add</button></div>
            <div class="table-responsive">
              <table class="table table-emp">
                <thead><tr><th>Date</th><th>Time</th><th>Mode</th><th>Seats</th><th>Status</th><th class="text-end">Actions</th></tr></thead>
                <tbody>
                  <tr v-if="!exam.my_slots.length"><td colspan="6"><EmptyState icon="calendar-plus" title="No slots yet" :text="exam.can_create_slots ? 'Create your first slot so students can book.' : 'Slots can be created during the slot creation window.'" /></td></tr>
                  <tr v-for="s in exam.my_slots" :key="s.id">
                    <td class="fw-semibold">{{ $f.fmtDay(s.date) }}</td>
                    <td>{{ $f.fmtTime(s.start_time) }} – {{ $f.fmtTime(s.end_time) }}</td>
                    <td class="small"><i :class="s.mode === 'online' ? 'bi bi-camera-video' : 'bi bi-geo-alt'"></i> {{ s.mode === 'online' ? 'Online' : s.venue }}</td>
                    <td>{{ s.booked_count }}/{{ s.capacity }}</td>
                    <td><StatusBadge :status="s.status" /></td>
                    <td class="text-end text-nowrap">
                      <button class="btn btn-sm btn-icon btn-soft me-1" title="Booked students" @click="viewBookings(s)"><i class="bi bi-people"></i></button>
                      <template v-if="exam.can_create_slots && !s.booked_count">
                        <button class="btn btn-sm btn-icon btn-light me-1" title="Edit" @click="openForm(s)"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-sm btn-icon btn-soft-danger" title="Delete" @click="remove(s)"><i class="bi bi-trash"></i></button>
                      </template>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div class="col-xl-4">
          <div class="card-emp mb-4">
            <div class="card-header"><i class="bi bi-grid-3x3-gap me-2 text-primary"></i>Evaluation rubric</div>
            <div class="card-body">
              <div v-for="r in exam.rubrics" :key="r.id" class="mb-3">
                <div class="d-flex justify-content-between"><b class="small">{{ r.criterion }}</b><span class="badge-soft bs-primary">{{ r.weightage }}%</span></div>
                <div class="small text-muted">Out of {{ r.max_marks }} · {{ r.description }}</div>
              </div>
              <div class="small text-muted border-top pt-2">Total: {{ exam.max_marks }} marks · pass {{ exam.pass_marks }}</div>
            </div>
          </div>
          <div class="card-emp">
            <div class="card-header"><i class="bi bi-info-circle me-2 text-primary"></i>Timeline</div>
            <div class="card-body small">
              <div class="timeline">
                <div class="timeline-item" :class="{ done: today >= exam.slot_creation_start }"><b>Slot creation</b><div class="text-muted">{{ $f.fmtDate(exam.slot_creation_start) }} – {{ $f.fmtDate(exam.slot_creation_end) }}</div></div>
                <div class="timeline-item" :class="{ done: today >= exam.booking_start }"><b>Student booking</b><div class="text-muted">{{ $f.fmtDate(exam.booking_start) }} – {{ $f.fmtDate(exam.booking_end) }}</div></div>
                <div class="timeline-item" :class="{ done: today >= exam.exam_start }"><b>Examinations</b><div class="text-muted">{{ $f.fmtDate(exam.exam_start) }} – {{ $f.fmtDate(exam.exam_end) }}</div></div>
              </div>
              <div class="fw-semibold mt-2">Instructions</div><div class="text-muted">{{ exam.instructions || '—' }}</div>
            </div>
          </div>
        </div>
      </div>

      <BaseModal :show="form.show" :title="form.slot ? 'Edit slot' : 'Create slot'" :subtitle="exam.name + ' · ' + exam.duration_minutes + ' min per student'" icon="calendar-plus" size="lg" @close="form.show = false">
        <SlotForm v-if="form.show" :exam="exam" :slot="form.slot" @saved="form.show = false; load()" />
        <template #footer><button class="btn btn-light" @click="form.show = false">Cancel</button><button class="btn btn-gradient" form="slotForm">{{ form.slot ? 'Save changes' : 'Create' }}</button></template>
      </BaseModal>

      <BaseModal :show="bk.show" title="Booked students" :subtitle="bk.slot ? $f.fmtDay(bk.slot.date) + ' · ' + $f.fmtTime(bk.slot.start_time) : ''" icon="people" @close="bk.show = false">
        <div v-if="!bk.list.length" class="text-center text-muted small py-3">No bookings for this slot yet.</div>
        <div v-for="b in bk.list" :key="b.id" class="d-flex align-items-center gap-2 py-2 border-bottom">
          <span class="avatar avatar-sm">{{ $f.initials(b.student_name) }}</span>
          <div class="flex-grow-1"><div class="fw-semibold small">{{ b.student_name }}</div><small class="text-muted">{{ b.roll_no }}</small></div>
          <StatusBadge :status="b.status" />
          <router-link v-if="['booked','completed'].includes(b.status)" :to="'/examiner/evaluate/' + b.id" class="btn btn-sm btn-soft">Evaluate</router-link>
        </div>
      </BaseModal>
    </template>
  </div>
</template>
<script>
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import StatCard from '@/components/common/StatCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import SlotForm from '@/components/examiner/SlotForm.vue'
export default {
  name: 'ExaminerExamDetail',
  components: { PageHeader, LoadingBlock, StatCard, StatusBadge, EmptyState, BaseModal, SlotForm },
  props: { id: String },
  data: () => ({ exam: null, form: { show: false, slot: null }, bk: { show: false, slot: null, list: [] } }),
  computed: { today () { return this.$f.todayISO() } },
  mounted () { this.load() },
  methods: {
    async load () { try { this.exam = (await api.get(`/examiner/exams/${this.id}`)).data.data } catch (e) { this.$error(e); this.$router.push('/examiner/exams') } },
    openForm (s = null) { this.form = { show: true, slot: s } },
    async remove (s) {
      if (!await this.$confirm({ title: 'Remove slot?', message: `${this.$f.fmtDay(s.date)} ${this.$f.fmtTime(s.start_time)} will be deleted.`, variant: 'danger', confirmText: 'Remove', icon: 'trash' })) return
      try { const r = await api.delete(`/examiner/slots/${s.id}`); this.$toast(r.data.message); this.load() } catch (e) { this.$error(e) }
    },
    async viewBookings (s) {
      try { const r = await api.get(`/examiner/slots/${s.id}/bookings`); this.bk = { show: true, slot: s, list: r.data.data.bookings.filter(b => b.status !== 'cancelled') } } catch (e) { this.$error(e) }
    },
    async complete () {
      if (!await this.$confirm({ title: 'Mark examination completed?', message: 'All students must be evaluated or marked absent. The admin will be notified to publish results.', confirmText: 'Mark completed', variant: 'success', icon: 'check2-circle' })) return
      try { const r = await api.post(`/examiner/exams/${this.id}/complete`); this.$toast(r.data.message); this.load() } catch (e) { this.$error(e) }
    }
  }
}
</script>
<style scoped>
.banner { display: flex; gap: 1rem; align-items: center; padding: 1rem 1.25rem; border-radius: 16px; }
.banner > i { font-size: 1.5rem; }
.banner.ok { background: rgba(16,185,129,.1); color: #047857; }
.banner.lock { background: rgba(100,116,139,.1); }
[data-bs-theme="dark"] .banner.ok { color: #6ee7b7; }
</style>
