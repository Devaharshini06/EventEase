<template>
  <DashboardLayout pageTitle="Platform Administration Overview">
    <div v-if="loading" class="ee-surface p-5 text-center text-secondary">
      Loading platform-wide analytics...
    </div>

    <div v-else-if="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>

    <template v-else>
      <!-- Top Metrics Row -->
      <div class="row g-3 mb-4">
        <div class="col-sm-6 col-xl-3">
          <div class="ee-surface p-3 h-100">
            <div class="small text-secondary mb-1">Registered Platform Users</div>
            <div class="h3 fw-bold font-mono-tabular mb-1">{{ metrics.total_users }}</div>
            <div class="ee-meta-line">
              <span>{{ metrics.active_users }} active</span>
              <span class="ee-meta-sep">·</span>
              <span>{{ metrics.inactive_users }} deactivated</span>
            </div>
          </div>
        </div>

        <div class="col-sm-6 col-xl-3">
          <div class="ee-surface p-3 h-100">
            <div class="small text-secondary mb-1">Published Events</div>
            <div class="h3 fw-bold font-mono-tabular mb-1">{{ metrics.published_events }}</div>
            <div class="ee-meta-line">
              <span>{{ metrics.total_events }} total</span>
              <span class="ee-meta-sep">·</span>
              <span>{{ metrics.draft_events }} draft</span>
            </div>
          </div>
        </div>

        <div class="col-sm-6 col-xl-3">
          <div class="ee-surface p-3 h-100">
            <div class="small text-secondary mb-1">Active Registrations</div>
            <div class="h3 fw-bold font-mono-tabular mb-1">{{ metrics.active_registrations }}</div>
            <div class="ee-meta-line">
              <span>{{ metrics.checked_in_registrations }} checked in</span>
              <span class="ee-meta-sep">·</span>
              <span>{{ metrics.cancelled_registrations }} cancelled</span>
            </div>
          </div>
        </div>

        <div class="col-sm-6 col-xl-3">
          <div class="ee-surface p-3 h-100">
            <div class="small text-secondary mb-1">Active Categories</div>
            <div class="h3 fw-bold font-mono-tabular mb-1">{{ eventsByCategory.length }}</div>
            <div class="ee-meta-line">
              <router-link to="/admin/categories" class="text-decoration-none">
                Manage Category Registry &rarr;
              </router-link>
            </div>
          </div>
        </div>
      </div>

      <!-- Category Distribution & Recent Activity Split -->
      <div class="row g-4 mb-4">
        <div class="col-lg-6">
          <div class="ee-surface h-100">
            <div class="p-3 p-md-4 border-bottom d-flex align-items-center justify-content-between">
              <div>
                <h2 class="h6 fw-bold mb-0">Events Grouped by Category</h2>
                <p class="small text-secondary mb-0">
                  Real-time SQLAlchemy group-by aggregation across all categories.
                </p>
              </div>
              <router-link to="/admin/categories" class="btn btn-outline-secondary btn-sm">
                Edit Categories
              </router-link>
            </div>

            <div class="table-responsive">
              <table class="table ee-table">
                <thead>
                  <tr>
                    <th>Category Name</th>
                    <th class="text-end">Events</th>
                    <th class="text-end">Active Regs</th>
                    <th class="text-end">Total Capacity</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="cat in eventsByCategory" :key="cat.category_id">
                    <td class="fw-semibold">{{ cat.category_name }}</td>
                    <td class="text-end font-mono-tabular">{{ cat.event_count }}</td>
                    <td class="text-end font-mono-tabular">{{ cat.active_registrations }}</td>
                    <td class="text-end font-mono-tabular">{{ cat.total_capacity }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="col-lg-6">
          <div class="ee-surface h-100">
            <div class="p-3 p-md-4 border-bottom d-flex align-items-center justify-content-between">
              <div>
                <h2 class="h6 fw-bold mb-0">Recent Registration Activity</h2>
                <p class="small text-secondary mb-0">
                  Latest attendee registrations and check-ins across the platform.
                </p>
              </div>
              <router-link to="/admin/users" class="btn btn-outline-secondary btn-sm">
                User Directory
              </router-link>
            </div>

            <div v-if="recentActivity.length === 0" class="p-4 text-center text-secondary small">
              No registration activity recorded yet.
            </div>

            <div v-else class="table-responsive">
              <table class="table ee-table">
                <thead>
                  <tr>
                    <th>Reference</th>
                    <th>Attendee</th>
                    <th>Event</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="act in recentActivity" :key="act.id">
                    <td class="font-mono-tabular fw-semibold">
                      <router-link :to="`/registrations/${act.id}`" class="text-decoration-none">
                        {{ act.registration_reference }}
                      </router-link>
                    </td>
                    <td>
                      <div class="fw-semibold">{{ act.attendee_name }}</div>
                      <div class="small text-secondary">{{ act.attendee_email }}</div>
                    </td>
                    <td class="small">
                      <router-link :to="`/events/${act.event_id}`" class="text-decoration-none text-dark">
                        {{ act.event_title }}
                      </router-link>
                    </td>
                    <td>
                      <span
                        class="ee-status-text"
                        :class="`ee-status-${act.status.toLowerCase()}`"
                      >
                        {{ act.status }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Platform-Wide Event Moderation Table -->
      <div class="ee-surface">
        <div class="p-3 p-md-4 border-bottom d-flex flex-wrap align-items-center justify-content-between gap-2">
          <div>
            <h2 class="h6 fw-bold mb-0">All Platform Events &amp; Moderation Status</h2>
            <p class="small text-secondary mb-0">
              Administrators can inspect, edit, or cancel any event on the platform.
            </p>
          </div>
        </div>

        <div class="table-responsive">
          <table class="table ee-table">
            <thead>
              <tr>
                <th>Event Title</th>
                <th>Organizer</th>
                <th>Category &amp; City</th>
                <th>Starts (UTC)</th>
                <th>Status</th>
                <th class="text-end">Occupancy</th>
                <th class="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ev in recentEvents" :key="ev.id">
                <td class="fw-semibold">
                  <router-link :to="`/events/${ev.id}`" class="text-decoration-none text-dark">
                    {{ ev.title }}
                  </router-link>
                </td>
                <td class="small text-secondary">{{ ev.organizer_name }}</td>
                <td class="small text-secondary">{{ ev.category_name }} · {{ ev.city }}</td>
                <td class="font-mono-tabular small">{{ formatDateShort(ev.start_datetime) }}</td>
                <td>
                  <span
                    class="ee-status-text"
                    :class="`ee-status-${ev.status.toLowerCase()}`"
                  >
                    {{ ev.status }}
                  </span>
                </td>
                <td class="text-end font-mono-tabular">
                  {{ ev.registered_count }} / {{ ev.capacity }}
                </td>
                <td class="text-end">
                  <div class="d-inline-flex gap-2">
                    <router-link
                      :to="`/organizer/events/${ev.id}/attendees`"
                      class="btn btn-outline-primary btn-sm py-1 px-2"
                    >
                      Roster
                    </router-link>
                    <router-link
                      :to="`/organizer/events/${ev.id}/edit`"
                      class="btn btn-outline-secondary btn-sm py-1 px-2"
                    >
                      Moderate / Edit
                    </router-link>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
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
  total_users: 0,
  active_users: 0,
  inactive_users: 0,
  total_events: 0,
  published_events: 0,
  draft_events: 0,
  cancelled_events: 0,
  total_registrations: 0,
  active_registrations: 0,
  checked_in_registrations: 0,
  cancelled_registrations: 0,
});
const eventsByCategory = ref<any[]>([]);
const recentActivity = ref<any[]>([]);
const recentEvents = ref<any[]>([]);

async function loadAdminDashboard() {
  loading.value = true;
  errorMessage.value = '';
  try {
    const { data } = await apiClient.get('/dashboard/admin');
    Object.assign(metrics, data.metrics || {});
    eventsByCategory.value = data.events_by_category || [];
    recentActivity.value = data.recent_activity || [];
    recentEvents.value = data.recent_events || [];
  } catch (err) {
    errorMessage.value = extractErrorMessage(err, 'Failed to load administrator dashboard.');
  } finally {
    loading.value = false;
  }
}

function formatDateShort(iso?: string): string {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

onMounted(loadAdminDashboard);
</script>
