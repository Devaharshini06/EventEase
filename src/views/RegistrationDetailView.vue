<template>
  <DashboardLayout pageTitle="Registration Pass &amp; Check-In Verification">
    <div v-if="loading" class="ee-surface p-5 text-center text-secondary">
      Loading registration pass...
    </div>

    <div v-else-if="errorMessage" class="ee-surface p-5 text-center">
      <h2 class="h5 fw-bold mb-2">Registration Record Unavailable</h2>
      <p class="text-secondary mb-3">{{ errorMessage }}</p>
      <router-link to="/attendee/registrations" class="btn btn-primary btn-sm">
        Back to My Registrations
      </router-link>
    </div>

    <div v-else-if="registration" class="row justify-content-center">
      <div class="col-lg-8">
        <div class="ee-surface p-4 p-md-5">
          <div class="d-flex flex-wrap align-items-start justify-content-between gap-3 pb-4 border-bottom mb-4">
            <div>
              <div class="ee-meta-line mb-1">
                <span>EventEase Official Attendee Pass</span>
                <span class="ee-meta-sep">·</span>
                <span
                  class="ee-status-text"
                  :class="`ee-status-${registration.status.toLowerCase()}`"
                >
                  {{ registration.status }}
                </span>
              </div>
              <h1 class="h3 fw-bold mb-1">{{ registration.event?.title }}</h1>
              <div class="text-secondary small">
                {{ registration.event?.venue }} · {{ registration.event?.city }}
              </div>
            </div>

            <div class="text-md-end">
              <div class="small text-muted">Registration Reference</div>
              <div class="h4 font-mono-tabular fw-bold mb-0 text-primary">
                {{ registration.registration_reference }}
              </div>
            </div>
          </div>

          <!-- Pass Details Grid -->
          <div class="row g-4 mb-4">
            <div class="col-md-7">
              <div class="row g-3">
                <div class="col-sm-6">
                  <div class="small text-muted">Attendee Name</div>
                  <div class="fw-semibold">{{ registration.attendee?.full_name }}</div>
                </div>
                <div class="col-sm-6">
                  <div class="small text-muted">Attendee Email</div>
                  <div class="fw-semibold">{{ registration.attendee?.email }}</div>
                </div>
                <div class="col-sm-6">
                  <div class="small text-muted">Event Starts (UTC)</div>
                  <div class="font-mono-tabular fw-semibold">
                    {{ formatDateTime(registration.event?.start_datetime) }}
                  </div>
                </div>
                <div class="col-sm-6">
                  <div class="small text-muted">Event Ends (UTC)</div>
                  <div class="font-mono-tabular fw-semibold">
                    {{ formatDateTime(registration.event?.end_datetime) }}
                  </div>
                </div>
                <div class="col-sm-6">
                  <div class="small text-muted">Registered At (UTC)</div>
                  <div class="font-mono-tabular small">
                    {{ formatDateTime(registration.registered_at) }}
                  </div>
                </div>
                <div class="col-sm-6">
                  <div class="small text-muted">Check-In Verification</div>
                  <div class="font-mono-tabular small fw-semibold">
                    {{
                      registration.checked_in_at
                        ? `Checked in at ${formatDateTime(registration.checked_in_at)}`
                        : registration.status === 'CANCELLED'
                        ? 'Registration Cancelled'
                        : 'Awaiting Door Check-In'
                    }}
                  </div>
                </div>
                <div v-if="registration.notes" class="col-12">
                  <div class="small text-muted">Attendee Notes</div>
                  <div class="small text-secondary">{{ registration.notes }}</div>
                </div>
              </div>
            </div>

            <!-- Deterministic Reference Matrix Visual (Encodes only registration_reference) -->
            <div class="col-md-5 d-flex flex-column align-items-center justify-content-center border-start-md">
              <div class="p-3 bg-light border rounded text-center">
                <svg
                  width="136"
                  height="136"
                  viewBox="0 0 17 17"
                  role="img"
                  :aria-label="`Check-in code for ${registration.registration_reference}`"
                >
                  <rect width="17" height="17" fill="#ffffff" />
                  <rect
                    v-for="(cell, idx) in referenceMatrixCells"
                    :key="idx"
                    :x="cell.x"
                    :y="cell.y"
                    width="1"
                    height="1"
                    fill="#0f172a"
                  />
                </svg>
                <div class="font-mono-tabular fw-bold small mt-2">
                  {{ registration.registration_reference }}
                </div>
                <div class="text-muted" style="font-size: 0.7rem;">
                  Encodes reference code only
                </div>
              </div>
            </div>
          </div>

          <div class="d-flex flex-wrap align-items-center justify-content-between gap-2 pt-3 border-top">
            <div class="d-flex gap-2">
              <router-link to="/attendee/registrations" class="btn btn-outline-secondary btn-sm">
                &larr; My Registrations
              </router-link>
              <router-link
                v-if="registration.event"
                :to="`/events/${registration.event.id}`"
                class="btn btn-outline-secondary btn-sm"
              >
                View Event Page
              </router-link>
            </div>

            <div class="d-flex gap-2">
              <button
                v-if="canOrganizerCheckIn && registration.status === 'CONFIRMED'"
                type="button"
                class="btn btn-success btn-sm"
                :disabled="actionLoading"
                @click="handleCheckIn"
              >
                {{ actionLoading ? 'Checking In...' : 'Check In Attendee Now' }}
              </button>
              <button
                v-if="registration.status === 'CONFIRMED' && !registration.event?.is_past"
                type="button"
                class="btn btn-outline-danger btn-sm"
                :disabled="actionLoading"
                @click="showCancelModal = true"
              >
                Cancel Registration
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <ConfirmModal
      :visible="showCancelModal"
      title="Cancel Registration Pass"
      :message="`Are you sure you want to cancel pass ${registration?.registration_reference}?`"
      confirmLabel="Confirm Cancellation"
      :danger="true"
      :loading="actionLoading"
      @cancel="showCancelModal = false"
      @confirm="handleCancel"
    />
  </DashboardLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import DashboardLayout from '../components/DashboardLayout.vue';
import ConfirmModal from '../components/ConfirmModal.vue';
import { apiClient, extractErrorMessage } from '../api/client';
import { useAuthStore, showToast } from '../stores/auth';

const route = useRoute();
const { state, isAdmin } = useAuthStore();

const registration = ref<any | null>(null);
const loading = ref(true);
const errorMessage = ref('');
const actionLoading = ref(false);
const showCancelModal = ref(false);

const canOrganizerCheckIn = computed(() => {
  if (!registration.value || !state.user) return false;
  if (isAdmin.value) return true;
  return (
    state.user.roles.includes('organizer') &&
    registration.value.event?.organizer_id === state.user.id
  );
});

const referenceMatrixCells = computed(() => {
  const refStr = registration.value?.registration_reference || 'EVT-0000-0000';
  const cells: Array<{ x: number; y: number }> = [];

  // Finder corners
  const drawFinder = (ox: number, oy: number) => {
    for (let y = 0; y < 5; y++) {
      for (let x = 0; x < 5; x++) {
        if (x === 0 || x === 4 || y === 0 || y === 4 || (x === 2 && y === 2)) {
          cells.push({ x: ox + x, y: oy + y });
        }
      }
    }
  };
  drawFinder(1, 1);
  drawFinder(11, 1);
  drawFinder(1, 11);

  // Deterministic bit pattern from registration_reference characters
  let hash = 2166136261;
  for (let i = 0; i < refStr.length; i++) {
    hash ^= refStr.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }

  for (let y = 1; y < 16; y++) {
    for (let x = 1; x < 16; x++) {
      const inFinder =
        (x < 7 && y < 7) || (x > 9 && y < 7) || (x < 7 && y > 9);
      if (!inFinder) {
        const bit = ((hash >>> ((x * 7 + y * 13) % 28)) ^ refStr.charCodeAt((x + y) % refStr.length)) & 1;
        if (bit === 1) {
          cells.push({ x, y });
        }
      }
    }
  }
  return cells;
});

async function loadRegistration() {
  loading.value = true;
  errorMessage.value = '';
  try {
    const { data } = await apiClient.get(`/registrations/${route.params.id}`);
    registration.value = data.registration;
  } catch (err) {
    errorMessage.value = extractErrorMessage(err, 'Could not load registration details.');
  } finally {
    loading.value = false;
  }
}

async function handleCheckIn() {
  if (!registration.value || actionLoading.value) return;
  actionLoading.value = true;
  try {
    const { data } = await apiClient.post(`/registrations/${registration.value.id}/check-in`);
    registration.value = data.registration;
    showToast('Attendee checked in successfully.', 'success');
  } catch (err) {
    showToast(extractErrorMessage(err, 'Check-in failed.'), 'danger');
  } finally {
    actionLoading.value = false;
  }
}

async function handleCancel() {
  if (!registration.value || actionLoading.value) return;
  actionLoading.value = true;
  try {
    const { data } = await apiClient.post(`/registrations/${registration.value.id}/cancel`);
    registration.value = data.registration;
    showCancelModal.value = false;
    showToast('Registration cancelled.', 'info');
  } catch (err) {
    showToast(extractErrorMessage(err, 'Could not cancel registration.'), 'danger');
    showCancelModal.value = false;
  } finally {
    actionLoading.value = false;
  }
}

function formatDateTime(iso?: string): string {
  if (!iso) return '';
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

onMounted(loadRegistration);
</script>
