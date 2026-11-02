<template>
  <div>
    <PageHeader title="Students" subtitle="View, edit, block or unblock any registered student." :crumbs="[{ label: 'Admin', to: '/admin' }, { label: 'Students' }]" />
    <UserList role="student" />
  </div>
</template>
<script>
import PageHeader from '@/components/common/PageHeader.vue'
import UserList from '@/components/admin/UserList.vue'
export default { name: 'AdminStudents', components: { PageHeader, UserList } }
</script>
