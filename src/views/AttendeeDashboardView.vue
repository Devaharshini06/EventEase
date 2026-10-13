<template>
  <DashboardLayout pageTitle="Attendee Dashboard">
    <div v-if="loading" class="ee-surface p-5 text-center text-secondary">
      Loading your attendee activity...
    </div>

    <div v-else-if="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>

    <template v-else>
      <!-- Metric Cards -->
      <div class="row g-3 mb-4">
        <div class="col-sm-6 col-xl-3">
          <div class="ee-surface p-3 h-100">
            <div class="small text-secondary mb-1">Upcoming Registered Events</div>
            <div class="h3 fw-bold font-mono-tabular mb-0">{{ metrics.upcoming_events_count }}</div>
          </div>
        </div>
        <div class="col-sm-6 col-xl-3">
          <div class="ee-surface p-3 h-100">
            <div class="small text-secondary mb-1">Verified Venue Check-Ins</div>
            <div class="h3 fw-bold font-mono-tabular mb-0">{{ metrics.checked_in_count }}</div>
          </div>
        </div>
        <div class="col-sm-6 col-xl-3">
          <div class="ee-surface p-3 h-100">
            <div class="small text-secondary mb-1">Past Events Attended</div>
            <div class="h3 fw-bold font-mono-tabular mb-0">{{ metrics.past_events_count }}</div>
          </div>
        </div>
        <div class="col-sm-6 col-xl-3">
          <div class="ee-surface p-3 h-100">
            <div class="small text-secondary mb-1">Cancelled Registrations</div>
            <div class="h3 fw-bold font-mono-tabular mb-0">{{ metrics.cancelled_registrations_count }}</div>
          </div>
        </div>
      </div>

      <!-- Upcoming Registered Events -->
      <div class="ee-surface mb-4">
        <div class="p-3 p-md-4 border-bottom d-flex flex-wrap align-items-center justify-content-between gap-2">
          <div>
            <h2 class="h5 fw-bold mb-0">Upcoming Registered Events</h2>
            <p class="small text-secondary mb-0">
              Active passes with check-in references for upcoming sessions.
            </p>
          </div>
          <div class="d-flex gap-2">
            <router-link to="/events" class="btn btn-primary btn-sm">
              Discover More Events
            </router-link>
            <router-link to="/attendee/registrations" class="btn btn-outline-secondary btn-sm">
              All Registrations
            </router-link>
          </div>
        </div>

        <div v-if="upcoming.length === 0" class="p-5 text-center">
          <p class="text-secondary mb-3">You have no upcoming event registrations.</p>
          <router-link to="/events" class="btn btn-primary btn-sm">
            Browse Upcoming Events
          </router-link>
        </div>

        <div v-else class="table-responsive">
          <table class="table ee-table">
            <thead>
              <tr>
                <th>Pass Reference</th>
                <th>Event</th>
                <th>Venue &amp; City</th>
                <th>Starts (UTC)</th>
                <th>Status</th>
                <th class="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="reg in upcoming" :key="reg.id">
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
                </td>
                <td class="text-secondary small">
                  {{ reg.event?.venue }} · {{ reg.event?.city }}
                </td>
                <td class="font-mono-tabular small">
                  {{ formatDateTime(reg.event?.start_datetime) }}
                </td>
                <td>
                  <span
                    class="ee-status-text"
                    :class="`ee-status-${reg.status.toLowerCase()}`"
                  >
                    {{ reg.status }}
                  </span>
                </td>
                <td class="text-end">
                  <router-link
                    :to="`/registrations/${reg.id}`"
                    class="btn btn-outline-primary btn-sm py-1 px-2"
                  >
                    View Pass
                  </router-link>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Past & Cancelled Summary Row -->
      <div class="row g-4">
        <div class="col-lg-6">
          <div class="ee-surface p-4 h-100">
            <h3 class="h6 fw-bold mb-3">Past Events ({{ past.length }})</h3>
            <div v-if="past.length === 0" class="text-secondary small">
              No past event registrations recorded.
            </div>
            <div v-else class="d-flex flex-column gap-3">
              <div
                v-for="reg in past"
                :key="reg.id"
                class="pb-3 border-bottom d-flex justify-content-between align-items-start gap-2"
              >
                <div>
                  <router-link :to="`/registrations/${reg.id}`" class="fw-semibold text-dark text-decoration-none">
                    {{ reg.event?.title }}
                  </router-link>
                  <div class="ee-meta-line">
                    <span class="font-mono-tabular">{{ reg.registration_reference }}</span>
                    <span class="ee-meta-sep">·</span>
                    <span>{{ reg.event?.city }}</span>
                  </div>
                </div>
                <span class="ee-status-text" :class="`ee-status-${reg.status.toLowerCase()}`">
                  {{ reg.status }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="col-lg-6">
          <div class="ee-surface p-4 h-100">
            <h3 class="h6 fw-bold mb-3">Cancelled Registrations ({{ cancelled.length }})</h3>
            <div v-if="cancelled.length === 0" class="text-secondary small">
              No cancelled registrations.
            </div>
            <div v-else class="d-flex flex-column gap-3">
              <div
                v-for="reg in cancelled"
                :key="reg.id"
                class="pb-3 border-bottom d-flex justify-content-between align-items-start gap-2"
              >
                <div>
                  <router-link :to="`/registrations/${reg.id}`" class="fw-semibold text-dark text-decoration-none">
                    {{ reg.event?.title }}
                  </router-link>
                  <div class="ee-meta-line">
                    <span class="font-mono-tabular">{{ reg.registration_reference }}</span>
                    <span class="ee-meta-sep">·</span>
                    <span>Cancelled {{ formatDateTime(reg.cancelled_at) }}</span>
                  </div>
                </div>
                <span class="ee-status-text ee-status-cancelled">CANCELLED</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import DashboardLayout from '../components/DashboardLayout.vue';
import { apiClient, extractErrorMessage } from '../api/client';

const loading = ref(true);
const errorMessage = ref('');
const metrics = reactive({
  total_registrations: 0,
  upcoming_events_count: 0,
  past_events_count: 0,
  cancelled_registrations_count: 0,
  checked_in_count: 0,
});
const upcoming = ref<any[]>([]);
const past = ref<any[]>([]);
const cancelled = ref<any[]>([]);

async function loadAttendeeDashboard() {
  loading.value = true;
  errorMessage.value = '';
  try {
    const { data } = await apiClient.get('/dashboard/attendee');
    Object.assign(metrics, data.metrics || {});
    upcoming.value = data.upcoming_registrations || [];
    past.value = data.past_registrations || [];
    cancelled.value = data.cancelled_registrations || [];
  } catch (err) {
    errorMessage.value = extractErrorMessage(err, 'Failed to load attendee dashboard.');
  } finally {
    loading.value = false;
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

onMounted(loadAttendeeDashboard);
</script>
