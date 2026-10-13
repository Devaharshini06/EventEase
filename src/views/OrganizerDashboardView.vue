<template>
  <DashboardLayout pageTitle="Organizer Analytics &amp; Operations">
    <div v-if="loading" class="ee-surface p-5">
      <div class="placeholder-glow">
        <span class="placeholder col-4 mb-3"></span>
        <span class="placeholder col-12 mb-2" style="height: 80px;"></span>
      </div>
    </div>

    <div v-else-if="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>

    <template v-else>
      <!-- Metric Strip -->
      <div class="row g-3 mb-4">
        <div class="col-sm-6 col-xl-3">
          <div class="ee-surface p-3 h-100">
            <div class="small text-secondary mb-1">Total Events Created</div>
            <div class="h3 fw-bold font-mono-tabular mb-1">{{ metrics.total_events }}</div>
            <div class="ee-meta-line">
              <span>{{ metrics.published_events }} published</span>
              <span class="ee-meta-sep">·</span>
              <span>{{ metrics.draft_events }} draft</span>
            </div>
          </div>
        </div>

        <div class="col-sm-6 col-xl-3">
          <div class="ee-surface p-3 h-100">
            <div class="small text-secondary mb-1">Active Registrations</div>
            <div class="h3 fw-bold font-mono-tabular mb-1">{{ metrics.total_active_registrations }}</div>
            <div class="ee-meta-line">
              <span>{{ metrics.total_checked_in }} checked in at venue</span>
            </div>
          </div>
        </div>

        <div class="col-sm-6 col-xl-3">
          <div class="ee-surface p-3 h-100">
            <div class="small text-secondary mb-1">Remaining Published Capacity</div>
            <div class="h3 fw-bold font-mono-tabular mb-1">{{ metrics.remaining_published_capacity }}</div>
            <div class="ee-meta-line">
              <span>of {{ metrics.total_published_capacity }} total published seats</span>
            </div>
          </div>
        </div>

        <div class="col-sm-6 col-xl-3">
          <div class="ee-surface p-3 h-100">
            <div class="small text-secondary mb-1">Upcoming vs Past Events</div>
            <div class="h3 fw-bold font-mono-tabular mb-1">{{ upcomingEvents.length }} / {{ pastEvents.length }}</div>
            <div class="ee-meta-line">
              <span>{{ metrics.cancelled_events }} cancelled/archived</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Registration Counts & Occupancy per Event -->
      <div class="ee-surface mb-4">
        <div class="p-3 p-md-4 border-bottom d-flex flex-wrap align-items-center justify-content-between gap-2">
          <div>
            <h2 class="h5 fw-bold mb-0">Registration &amp; Capacity Breakdown by Event</h2>
            <p class="small text-secondary mb-0">
              Live SQLAlchemy aggregation across all events you manage.
            </p>
          </div>
          <router-link to="/organizer/events" class="btn btn-outline-secondary btn-sm">
            Manage All Events
          </router-link>
        </div>

        <div v-if="eventBreakdown.length === 0" class="p-5 text-center">
          <p class="text-secondary mb-3">You have not created any events yet.</p>
          <router-link to="/organizer/events/new" class="btn btn-primary btn-sm">
            Create Your First Event
          </router-link>
        </div>

        <div v-else class="table-responsive">
          <table class="table ee-table">
            <thead>
              <tr>
                <th>Event Title</th>
                <th>Category</th>
                <th>Start Date</th>
                <th>Status</th>
                <th class="text-end">Registered</th>
                <th class="text-end">Remaining</th>
                <th class="text-end">Occupancy</th>
                <th class="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in eventBreakdown" :key="item.event_id">
                <td class="fw-semibold">
                  <router-link :to="`/events/${item.event_id}`" class="text-decoration-none text-dark">
                    {{ item.title }}
                  </router-link>
                </td>
                <td class="text-secondary">{{ item.category_name }}</td>
                <td class="font-mono-tabular text-secondary">{{ formatDateShort(item.start_datetime) }}</td>
                <td>
                  <span
                    class="ee-status-text"
                    :class="`ee-status-${item.status.toLowerCase()}`"
                  >
                    {{ item.status }}
                  </span>
                </td>
                <td class="text-end font-mono-tabular">{{ item.registered_count }} / {{ item.capacity }}</td>
                <td class="text-end font-mono-tabular">{{ item.remaining_capacity }}</td>
                <td class="text-end font-mono-tabular">{{ item.occupancy_percent }}%</td>
                <td class="text-end">
                  <div class="d-inline-flex gap-2">
                    <router-link
                      :to="`/organizer/events/${item.event_id}/attendees`"
                      class="btn btn-outline-primary btn-sm py-1 px-2"
                    >
                      Attendees &amp; Check-In
                    </router-link>
                    <router-link
                      :to="`/organizer/events/${item.event_id}/edit`"
                      class="btn btn-outline-secondary btn-sm py-1 px-2"
                    >
                      Edit
                    </router-link>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Upcoming & Past Split -->
      <div class="row g-4">
        <div class="col-lg-6">
          <div class="ee-surface p-4 h-100">
            <h3 class="h6 fw-bold mb-3">Upcoming Active Events ({{ upcomingEvents.length }})</h3>
            <div v-if="upcomingEvents.length === 0" class="text-secondary small">
              No upcoming events scheduled.
            </div>
            <div v-else class="d-flex flex-column gap-3">
              <div
                v-for="ev in upcomingEvents.slice(0, 5)"
                :key="ev.id"
                class="pb-3 border-bottom last-border-0 d-flex justify-content-between align-items-start gap-2"
              >
                <div>
                  <router-link :to="`/events/${ev.id}`" class="fw-semibold text-dark text-decoration-none">
                    {{ ev.title }}
                  </router-link>
                  <div class="ee-meta-line">
                    <span>{{ ev.city }}</span>
                    <span class="ee-meta-sep">·</span>
                    <span class="font-mono-tabular">{{ formatDateShort(ev.start_datetime) }}</span>
                  </div>
                </div>
                <span class="font-mono-tabular small text-secondary shrink-0">
                  {{ ev.registered_count }} / {{ ev.capacity }} seats
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="col-lg-6">
          <div class="ee-surface p-4 h-100">
            <h3 class="h6 fw-bold mb-3">Completed Past Events ({{ pastEvents.length }})</h3>
            <div v-if="pastEvents.length === 0" class="text-secondary small">
              No completed past events yet.
            </div>
            <div v-else class="d-flex flex-column gap-3">
              <div
                v-for="ev in pastEvents.slice(0, 5)"
                :key="ev.id"
                class="pb-3 border-bottom d-flex justify-content-between align-items-start gap-2"
              >
                <div>
                  <router-link :to="`/events/${ev.id}`" class="fw-semibold text-dark text-decoration-none">
                    {{ ev.title }}
                  </router-link>
                  <div class="ee-meta-line">
                    <span>{{ ev.city }}</span>
                    <span class="ee-meta-sep">·</span>
                    <span class="font-mono-tabular">{{ formatDateShort(ev.start_datetime) }}</span>
                  </div>
                </div>
                <span class="font-mono-tabular small text-secondary shrink-0">
                  {{ ev.registered_count }} attended
                </span>
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
  total_events: 0,
  published_events: 0,
  draft_events: 0,
  cancelled_events: 0,
  total_active_registrations: 0,
  total_checked_in: 0,
  total_published_capacity: 0,
  remaining_published_capacity: 0,
});
const eventBreakdown = ref<any[]>([]);
const upcomingEvents = ref<any[]>([]);
const pastEvents = ref<any[]>([]);

async function fetchDashboard() {
  loading.value = true;
  errorMessage.value = '';
  try {
    const { data } = await apiClient.get('/dashboard/organizer', { params: { scope: 'own' } });
    Object.assign(metrics, data.metrics || {});
    eventBreakdown.value = data.event_breakdown || [];
    upcomingEvents.value = data.upcoming_events || [];
    pastEvents.value = data.past_events || [];
  } catch (err) {
    errorMessage.value = extractErrorMessage(err, 'Failed to load organizer dashboard.');
  } finally {
    loading.value = false;
  }
}

function formatDateShort(iso: string): string {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

onMounted(fetchDashboard);
</script>
