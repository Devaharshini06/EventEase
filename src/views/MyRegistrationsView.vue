<template>
  <DashboardLayout pageTitle="My Event Registrations">
    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
      <div class="ee-segmented">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          type="button"
          class="ee-segmented-btn"
          :class="{ active: statusFilter === tab.value }"
          @click="statusFilter = tab.value; fetchRegistrations()"
        >
          {{ tab.label }}
        </button>
      </div>

      <router-link to="/events" class="btn btn-outline-primary btn-sm">
        Explore More Events
      </router-link>
    </div>

    <div v-if="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>

    <div v-if="loading" class="ee-surface p-5 text-center text-secondary">
      Loading your registration history...
    </div>

    <div v-else-if="registrations.length === 0" class="ee-surface p-5 text-center">
      <h2 class="h5 fw-bold mb-2">No registrations match this filter</h2>
      <p class="text-secondary small mb-3">
        When you register for published events, your pass references and check-in timestamps appear here.
      </p>
      <router-link to="/events" class="btn btn-primary btn-sm">
        Browse Published Events
      </router-link>
    </div>

    <div v-else class="ee-surface">
      <div class="table-responsive">
        <table class="table ee-table">
          <thead>
            <tr>
              <th>Reference Code</th>
              <th>Event Title</th>
              <th>Location</th>
              <th>Event Date (UTC)</th>
              <th>Registered On</th>
              <th>Status</th>
              <th class="text-end">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="reg in registrations" :key="reg.id">
              <td class="font-mono-tabular fw-bold">
                <router-link :to="`/registrations/${reg.id}`" class="text-decoration-none">
                  {{ reg.registration_reference }}
                </router-link>
              </td>
              <td>
                <router-link
                  v-if="reg.event"
                  :to="`/events/${reg.event.id}`"
                  class="fw-semibold text-dark text-decoration-none"
                >
                  {{ reg.event.title }}
                </router-link>
                <div class="small text-secondary">{{ reg.event?.category_name }}</div>
              </td>
              <td class="small text-secondary">
                {{ reg.event?.venue }}<br />{{ reg.event?.city }}
              </td>
              <td class="font-mono-tabular small">
                {{ formatDateTime(reg.event?.start_datetime) }}
              </td>
              <td class="font-mono-tabular small text-secondary">
                {{ formatDateTime(reg.registered_at) }}
              </td>
              <td>
                <span
                  class="ee-status-text"
                  :class="`ee-status-${reg.status.toLowerCase()}`"
                >
                  {{ reg.status }}
                </span>
                <div v-if="reg.checked_in_at" class="font-mono-tabular text-muted" style="font-size: 0.72rem;">
                  Checked in {{ formatDateTime(reg.checked_in_at) }}
                </div>
              </td>
              <td class="text-end">
                <div class="d-inline-flex gap-2">
                  <router-link
                    :to="`/registrations/${reg.id}`"
                    class="btn btn-outline-primary btn-sm py-1 px-2"
                  >
                    Pass Details
                  </router-link>
                  <button
                    v-if="reg.status === 'CONFIRMED' && !reg.event?.is_past"
                    type="button"
                    class="btn btn-outline-danger btn-sm py-1 px-2"
                    @click="targetCancelReg = reg"
                  >
                    Cancel
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <ConfirmModal
      :visible="Boolean(targetCancelReg)"
      title="Cancel Registration"
      :message="`Cancel your registration (${targetCancelReg?.registration_reference}) for '${targetCancelReg?.event?.title}'?`"
      confirmLabel="Confirm Cancellation"
      :danger="true"
      :loading="cancelling"
      @cancel="targetCancelReg = null"
      @confirm="confirmCancel"
    />
  </DashboardLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import DashboardLayout from '../components/DashboardLayout.vue';
import ConfirmModal from '../components/ConfirmModal.vue';
import { apiClient, extractErrorMessage } from '../api/client';
import { showToast } from '../stores/auth';

const tabs = [
  { label: 'All Registrations', value: 'ALL' },
  { label: 'Confirmed', value: 'CONFIRMED' },
  { label: 'Checked In', value: 'CHECKED_IN' },
  { label: 'Cancelled', value: 'CANCELLED' },
];

const statusFilter = ref('ALL');
const registrations = ref<any[]>([]);
const loading = ref(true);
const errorMessage = ref('');
const targetCancelReg = ref<any | null>(null);
const cancelling = ref(false);

async function fetchRegistrations() {
  loading.value = true;
  errorMessage.value = '';
  try {
    const { data } = await apiClient.get('/registrations/me', {
      params: { status: statusFilter.value },
    });
    registrations.value = data.registrations || [];
  } catch (err) {
    errorMessage.value = extractErrorMessage(err, 'Failed to load registrations.');
  } finally {
    loading.value = false;
  }
}

async function confirmCancel() {
  if (!targetCancelReg.value || cancelling.value) return;
  cancelling.value = true;
  try {
    await apiClient.post(`/registrations/${targetCancelReg.value.id}/cancel`);
    showToast('Registration cancelled and seat released.', 'info');
    targetCancelReg.value = null;
    await fetchRegistrations();
  } catch (err) {
    showToast(extractErrorMessage(err, 'Could not cancel registration.'), 'danger');
  } finally {
    cancelling.value = false;
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

onMounted(fetchRegistrations);
</script>
