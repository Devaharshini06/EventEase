<template>
  <DashboardLayout pageTitle="Organizer Event Management">
    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
      <div class="ee-segmented">
        <button
          v-for="tab in statusTabs"
          :key="tab.value"
          type="button"
          class="ee-segmented-btn"
          :class="{ active: statusFilter === tab.value }"
          @click="statusFilter = tab.value; fetchMyEvents()"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="d-flex gap-2">
        <input
          v-model.trim="searchQuery"
          type="search"
          class="form-control form-control-sm"
          placeholder="Search my events..."
          style="min-width: 220px;"
          @keyup.enter="fetchMyEvents"
        />
        <button type="button" class="btn btn-outline-secondary btn-sm" @click="fetchMyEvents">
          Filter
        </button>
      </div>
    </div>

    <div v-if="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>

    <div v-if="loading" class="ee-surface p-5 text-center text-secondary">
      Loading your events...
    </div>

    <div v-else-if="events.length === 0" class="ee-surface p-5 text-center">
      <h2 class="h5 fw-bold mb-2">No events found in this view</h2>
      <p class="text-secondary small mb-3">
        Create a new event in Draft or Published mode to start accepting registrations.
      </p>
      <router-link to="/organizer/events/new" class="btn btn-primary btn-sm">
        Create New Event
      </router-link>
    </div>

    <div v-else class="ee-surface">
      <div class="table-responsive">
        <table class="table ee-table">
          <thead>
            <tr>
              <th>Event Title</th>
              <th>Category &amp; City</th>
              <th>Start (UTC)</th>
              <th>Deadline (UTC)</th>
              <th>Status</th>
              <th class="text-end">Registrations</th>
              <th class="text-end">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ev in events" :key="ev.id">
              <td>
                <router-link :to="`/events/${ev.id}`" class="fw-semibold text-dark text-decoration-none">
                  {{ ev.title }}
                </router-link>
                <div class="small text-muted text-truncate" style="max-width: 280px;">
                  {{ ev.venue }}
                </div>
              </td>
              <td>
                <div>{{ ev.category_name }}</div>
                <div class="small text-secondary">{{ ev.city }}</div>
              </td>
              <td class="font-mono-tabular small">{{ formatDateTime(ev.start_datetime) }}</td>
              <td class="font-mono-tabular small">{{ formatDateTime(ev.registration_deadline) }}</td>
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
                <div class="d-inline-flex flex-wrap justify-content-end gap-1">
                  <router-link
                    :to="`/organizer/events/${ev.id}/attendees`"
                    class="btn btn-outline-primary btn-sm py-1 px-2"
                  >
                    Attendees ({{ ev.registered_count }})
                  </router-link>
                  <button
                    v-if="ev.status === 'DRAFT'"
                    type="button"
                    class="btn btn-outline-success btn-sm py-1 px-2"
                    :disabled="actionBusyId === ev.id"
                    @click="quickToggleStatus(ev, 'PUBLISHED')"
                  >
                    Publish
                  </button>
                  <router-link
                    :to="`/organizer/events/${ev.id}/edit`"
                    class="btn btn-outline-secondary btn-sm py-1 px-2"
                  >
                    Edit
                  </router-link>
                  <button
                    v-if="ev.status !== 'CANCELLED'"
                    type="button"
                    class="btn btn-outline-danger btn-sm py-1 px-2"
                    :disabled="actionBusyId === ev.id"
                    @click="promptDeleteOrCancel(ev)"
                  >
                    {{ ev.status === 'DRAFT' && ev.registered_count === 0 ? 'Delete' : 'Cancel Event' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <ConfirmModal
      :visible=" Boolean(targetEvent) "
      :title="targetEvent?.status === 'DRAFT' && targetEvent?.registered_count === 0 ? 'Delete Draft Event' : 'Cancel Published Event'"
      :message="
        targetEvent?.status === 'DRAFT' && targetEvent?.registered_count === 0
          ? `Permanently delete the draft event '${targetEvent?.title}'?`
          : `Cancel '${targetEvent?.title}'? Existing attendee registration records will be preserved for audit history.`
      "
      :confirmLabel="targetEvent?.status === 'DRAFT' && targetEvent?.registered_count === 0 ? 'Delete Draft' : 'Confirm Cancellation'"
      :danger="true"
      :loading="modalSubmitting"
      @cancel="targetEvent = null"
      @confirm="confirmDeleteOrCancel"
    />
  </DashboardLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import DashboardLayout from '../components/DashboardLayout.vue';
import ConfirmModal from '../components/ConfirmModal.vue';
import { apiClient, extractErrorMessage } from '../api/client';
import { showToast } from '../stores/auth';

const statusTabs = [
  { label: 'All Events', value: 'ALL' },
  { label: 'Published', value: 'PUBLISHED' },
  { label: 'Drafts', value: 'DRAFT' },
  { label: 'Cancelled', value: 'CANCELLED' },
];

const statusFilter = ref('ALL');
const searchQuery = ref('');
const events = ref<any[]>([]);
const loading = ref(true);
const errorMessage = ref('');
const actionBusyId = ref<number | null>(null);
const targetEvent = ref<any | null>(null);
const modalSubmitting = ref(false);

async function fetchMyEvents() {
  loading.value = true;
  errorMessage.value = '';
  try {
    const { data } = await apiClient.get('/events', {
      params: {
        mine: true,
        scope: 'own',
        status: statusFilter.value,
        search: searchQuery.value,
        page_size: 50,
      },
    });
    events.value = data.events || [];
  } catch (err) {
    errorMessage.value = extractErrorMessage(err, 'Failed to load organizer events.');
  } finally {
    loading.value = false;
  }
}

async function quickToggleStatus(ev: any, nextStatus: string) {
  actionBusyId.value = ev.id;
  try {
    await apiClient.put(`/events/${ev.id}`, { status: nextStatus });
    showToast(`Event '${ev.title}' is now ${nextStatus}.`, 'success');
    await fetchMyEvents();
  } catch (err) {
    showToast(extractErrorMessage(err, 'Could not update status.'), 'danger');
  } finally {
    actionBusyId.value = null;
  }
}

function promptDeleteOrCancel(ev: any) {
  targetEvent.value = ev;
}

async function confirmDeleteOrCancel() {
  if (!targetEvent.value || modalSubmitting.value) return;
  modalSubmitting.value = true;
  try {
    const { data } = await apiClient.delete(`/events/${targetEvent.value.id}`);
    showToast(data.message || 'Event updated.', 'info');
    targetEvent.value = null;
    await fetchMyEvents();
  } catch (err) {
    showToast(extractErrorMessage(err, 'Operation failed.'), 'danger');
  } finally {
    modalSubmitting.value = false;
  }
}

function formatDateTime(iso: string): string {
  if (!iso) return '';
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

onMounted(fetchMyEvents);
</script>
