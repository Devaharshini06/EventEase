<template>
  <article class="ee-surface-interactive p-4 h-100 d-flex flex-column justify-content-between">
    <div>
      <div class="ee-meta-line mb-2">
        <span class="fw-semibold text-dark">{{ event.category_name }}</span>
        <span class="ee-meta-sep" aria-hidden="true">·</span>
        <span>{{ event.city }}</span>
        <span class="ee-meta-sep" aria-hidden="true">·</span>
        <span class="font-mono-tabular">{{ formatDateShort(event.start_datetime) }}</span>
      </div>

      <h3 class="h5 mb-2">
        <router-link
          :to="`/events/${event.id}`"
          class="text-decoration-none text-dark stretched-link"
        >
          {{ event.title }}
        </router-link>
      </h3>

      <p class="text-secondary small mb-3" style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
        {{ event.description }}
      </p>
    </div>

    <div class="pt-3 border-top">
      <div class="d-flex align-items-center justify-content-between small text-secondary mb-2">
        <span class="text-truncate" style="max-width: 65%;" :title="event.venue">
          {{ event.venue }}
        </span>
        <span class="font-mono-tabular fw-semibold text-dark">
          {{ event.is_free ? 'Free Entry' : `$${Number(event.price).toFixed(2)} (Info)` }}
        </span>
      </div>

      <div class="d-flex align-items-center justify-content-between small">
        <span class="text-muted text-truncate" style="max-width: 55%;">
          Host: {{ event.organizer_name }}
        </span>
        <span
          class="ee-status-text tabular-nums"
          :class="availabilityClass"
        >
          {{ availabilityLabel }}
        </span>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  event: {
    id: number;
    title: string;
    description: string;
    category_name: string;
    organizer_name: string;
    venue: string;
    city: string;
    start_datetime: string;
    remaining_capacity: number;
    capacity: number;
    price: number;
    is_free: boolean;
    status: string;
    is_registration_open: boolean;
    deadline_passed?: boolean;
    is_past?: boolean;
  };
}>();

const availabilityLabel = computed(() => {
  if (props.event.status !== 'PUBLISHED') {
    return props.event.status;
  }
  if (props.event.is_past) {
    return 'Event Ended';
  }
  if (props.event.remaining_capacity <= 0) {
    return 'Capacity Full (0 left)';
  }
  if (props.event.deadline_passed) {
    return 'Registration Closed';
  }
  return `${props.event.remaining_capacity} / ${props.event.capacity} seats left`;
});

const availabilityClass = computed(() => {
  if (props.event.status !== 'PUBLISHED' || props.event.is_past || props.event.deadline_passed) {
    return 'ee-status-draft';
  }
  if (props.event.remaining_capacity <= 0) {
    return 'ee-status-cancelled';
  }
  return 'ee-status-published';
});

function formatDateShort(iso: string): string {
  if (!iso) return '';
  const dt = new Date(iso);
  return dt.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}
</script>
