<template>
  <DashboardLayout :pageTitle="event ? `Attendees & Check-In: ${event.title}` : 'Event Attendee Management'">
    <template #actions>
      <button
        v-if="event"
        type="button"
        class="btn btn-outline-secondary btn-sm"
        :disabled="exportingCsv"
        @click="handleExportCsv"
      >
        {{ exportingCsv ? 'Exporting CSV...' : 'Download Attendee CSV' }}
      </button>
    </template>

    <div v-if="loading" class="ee-surface p-5 text-center text-secondary">
      Loading event roster and check-in records...
    </div>

    <div v-else-if="errorMessage" class="ee-surface p-5 text-center">
      <h2 class="h5 fw-bold mb-2">Unable to Access Event Roster</h2>
      <p class="text-secondary mb-3">{{ errorMessage }}</p>
      <router-link to="/organizer/events" class="btn btn-primary btn-sm">
        Back to Event Management
      </router-link>
    </div>

    <template v-else-if="event">
      <!-- Summary Counts -->
      <div class="row g-3 mb-4">
        <div class="col-sm-6 col-xl-3">
          <div class="ee-surface p-3 h-100">
            <div class="small text-secondary mb-1">Active Registered</div>
            <div class="h3 fw-bold font-mono-tabular mb-0">
              {{ summary.active_registered_count }} / {{ summary.capacity }}
            </div>
          </div>
        </div>
        <div class="col-sm-6 col-xl-3">
          <div class="ee-surface p-3 h-100">
            <div class="small text-secondary mb-1">Checked In at Door</div>
            <div class="h3 fw-bold font-mono-tabular text-success mb-0">
              {{ summary.checked_in_count }}
            </div>
          </div>
        </div>
        <div class="col-sm-6 col-xl-3">
          <div class="ee-surface p-3 h-100">
            <div class="small text-secondary mb-1">Remaining Capacity</div>
            <div class="h3 fw-bold font-mono-tabular mb-0">
              {{ summary.remaining_capacity }}
            </div>
          </div>
        </div>
        <div class="col-sm-6 col-xl-3">
          <div class="ee-surface p-3 h-100">
            <div class="small text-secondary mb-1">Cancelled Registrations</div>
            <div class="h3 fw-bold font-mono-tabular text-secondary mb-0">
              {{ summary.cancelled_count }}
            </div>
          </div>
        </div>
      </div>

      <!-- Rapid Reference Check-In Bar -->
      <div class="ee-surface p-3 p-md-4 mb-4">
        <div class="row g-3 align-items-end">
          <div class="col-md-6">
            <label for="checkin-ref-input" class="form-label small fw-semibold">
              Express Check-In by Registration Reference
            </label>
            <form class="d-flex gap-2" @submit.prevent="handleReferenceCheckIn">
              <input
                id="checkin-ref-input"
                v-model.trim="referenceInput"
                type="text"
                class="form-control form-control-sm font-mono-tabular"
                placeholder="Enter reference code (e.g., EVT-A101-SF99)"
                :disabled="checkingInRef"
              />
              <button
                type="submit"
                class="btn btn-primary btn-sm px-3"
                :disabled="checkingInRef || !referenceInput"
              >
                {{ checkingInRef ? 'Verifying...' : 'Check In Pass' }}
              </button>
            </form>
          </div>

          <div class="col-md-6">
            <div class="d-flex flex-wrap gap-2 justify-content-md-end align-items-center">
              <div class="ee-segmented">
                <button
                  v-for="st in ['ALL', 'CONFIRMED', 'CHECKED_IN', 'CANCELLED']"
                  :key="st"
                  type="button"
                  class="ee-segmented-btn"
                  :class="{ active: statusFilter === st }"
                  @click="statusFilter = st; fetchRoster()"
                >
                  {{ st === 'ALL' ? 'All' : st.replace('_', ' ') }}
                </button>
              </div>
              <input
                v-model.trim="searchQuery"
                type="search"
                class="form-control form-control-sm"
                placeholder="Search name, email, ref..."
                style="max-width: 210px;"
                @input="fetchRoster"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Roster Table -->
      <div class="ee-surface">
        <div v-if="registrations.length === 0" class="p-5 text-center text-secondary">
          No registrations match the current search or status filter.
        </div>

        <div v-else class="table-responsive">
          <table class="table ee-table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Attendee</th>
                <th>Organization</th>
                <th>Registered (UTC)</th>
                <th>Status</th>
                <th>Check-In Time (UTC)</th>
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
                  <div class="fw-semibold">{{ reg.attendee?.full_name }}</div>
                  <div class="small text-secondary">{{ reg.attendee?.email }}</div>
                </td>
                <td class="text-secondary small">
                  {{ reg.attendee?.organization || '—' }}
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
                </td>
                <td class="font-mono-tabular small">
                  {{ reg.checked_in_at ? formatDateTime(reg.checked_in_at) : '—' }}
                </td>
                <td class="text-end">
                  <div class="d-inline-flex gap-2">
                    <button
                      v-if="reg.status === 'CONFIRMED'"
                      type="button"
                      class="btn btn-success btn-sm py-1 px-2"
                      :disabled="rowBusyId === reg.id"
                      @click="handleRowCheckIn(reg)"
                    >
                      Check In
                    </button>
                    <button
                      v-if="reg.status === 'CONFIRMED'"
                      type="button"
                      class="btn btn-outline-danger btn-sm py-1 px-2"
                      :disabled="rowBusyId === reg.id"
                      @click="targetCancelReg = reg"
                    >
                      Cancel
                    </button>
                    <router-link
                      :to="`/registrations/${reg.id}`"
                      class="btn btn-outline-secondary btn-sm py-1 px-2"
                    >
                      Pass
                    </router-link>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <ConfirmModal
      :visible="Boolean(targetCancelReg)"
      title="Cancel Attendee Registration"
      :message="`Cancel registration ${targetCancelReg?.registration_reference} for ${targetCancelReg?.attendee?.full_name}?`"
      confirmLabel="Cancel Registration"
      :danger="true"
      :loading="cancellingReg"
      @cancel="targetCancelReg = null"
      @confirm="confirmCancelAttendee"
    />
  </DashboardLayout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import DashboardLayout from '../components/DashboardLayout.vue';
import ConfirmModal from '../components/ConfirmModal.vue';
import { apiClient, extractErrorMessage } from '../api/client';
import { showToast } from '../stores/auth';

const route = useRoute();
const event = ref<any | null>(null);
const registrations = ref<any[]>([]);
const summary = reactive({
  active_registered_count: 0,
  confirmed_count: 0,
  checked_in_count: 0,
  cancelled_count: 0,
  remaining_capacity: 0,
  capacity: 0,
});

const loading = ref(true);
const errorMessage = ref('');
const statusFilter = ref('ALL');
const searchQuery = ref('');
const referenceInput = ref('');
const checkingInRef = ref(false);
const rowBusyId = ref<number | null>(null);
const targetCancelReg = ref<any | null>(null);
const cancellingReg = ref(false);
const exportingCsv = ref(false);

async function fetchRoster() {
  try {
    const { data } = await apiClient.get(`/events/${route.params.id}/registrations`, {
      params: {
        status: statusFilter.value,
        search: searchQuery.value,
      },
    });
    event.value = data.event;
    registrations.value = data.registrations || [];
    Object.assign(summary, data.summary || {});
  } catch (err) {
    errorMessage.value = extractErrorMessage(err, 'Failed to load attendee roster.');
  } finally {
    loading.value = false;
  }
}

async function handleReferenceCheckIn() {
  if (!referenceInput.value || checkingInRef.value || !event.value) return;
  checkingInRef.value = true;
  try {
    const { data } = await apiClient.post(`/events/${event.value.id}/check-in`, {
      registration_reference: referenceInput.value,
    });
    showToast(
      `Checked in ${data.registration.attendee?.full_name} (${data.registration.registration_reference}).`,
      'success'
    );
    referenceInput.value = '';
    await fetchRoster();
  } catch (err) {
    showToast(extractErrorMessage(err, 'Check-in rejected.'), 'danger');
  } finally {
    checkingInRef.value = false;
  }
}

async function handleRowCheckIn(reg: any) {
  rowBusyId.value = reg.id;
  try {
    await apiClient.post(`/registrations/${reg.id}/check-in`);
    showToast(`Checked in ${reg.attendee?.full_name} (${reg.registration_reference}).`, 'success');
    await fetchRoster();
  } catch (err) {
    showToast(extractErrorMessage(err, 'Check-in failed.'), 'danger');
  } finally {
    rowBusyId.value = null;
  }
}

async function confirmCancelAttendee() {
  if (!targetCancelReg.value || cancellingReg.value) return;
  cancellingReg.value = true;
  try {
    await apiClient.post(`/registrations/${targetCancelReg.value.id}/cancel`);
    showToast(`Cancelled registration ${targetCancelReg.value.registration_reference}.`, 'info');
    targetCancelReg.value = null;
    await fetchRoster();
  } catch (err) {
    showToast(extractErrorMessage(err, 'Failed to cancel registration.'), 'danger');
  } finally {
    cancellingReg.value = false;
  }
}

async function handleExportCsv() {
  if (!event.value || exportingCsv.value) return;
  exportingCsv.value = true;
  try {
    const response = await apiClient.get(`/events/${event.value.id}/registrations/export`, {
      responseType: 'blob',
    });
    const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `event_${event.value.id}_attendees.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    showToast('Attendee CSV exported successfully.', 'success');
  } catch (err) {
    showToast(extractErrorMessage(err, 'CSV export failed.'), 'danger');
  } finally {
    exportingCsv.value = false;
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

onMounted(fetchRoster);
</script>
