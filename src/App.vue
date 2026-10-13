<template>
  <router-view />

  <!-- Global Toast Feedback Stack -->
  <div class="ee-toast-container" aria-live="polite" aria-atomic="true">
    <div
      v-for="t in state.toasts"
      :key="t.id"
      class="ee-surface shadow p-3 d-flex align-items-start justify-content-between gap-3"
      :class="{
        'border-success': t.type === 'success',
        'border-danger': t.type === 'danger',
        'border-warning': t.type === 'warning',
      }"
    >
      <div class="small">
        <span
          class="fw-bold me-1"
          :class="{
            'text-success': t.type === 'success',
            'text-danger': t.type === 'danger',
            'text-warning': t.type === 'warning',
            'text-primary': t.type === 'info',
          }"
        >
          {{ t.type.toUpperCase() }}:
        </span>
        <span class="text-dark">{{ t.text }}</span>
      </div>
      <button
        type="button"
        class="btn-close btn-sm"
        aria-label="Dismiss notification"
        @click="dismissToast(t.id)"
      ></button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useAuthStore, dismissToast } from './stores/auth';

const { state, fetchMe, fetchNotifications } = useAuthStore();

onMounted(async () => {
  if (state.token) {
    const user = await fetchMe();
    if (user) {
      await fetchNotifications();
    }
  }
});
</script>
