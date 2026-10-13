<template>
  <div class="min-vh-100 d-flex flex-column">
    <PublicNavbar />

    <main class="flex-grow-1 py-4 py-lg-5">
      <div class="container">
        <div class="mb-3">
          <router-link to="/events" class="text-decoration-none small text-secondary">
            &larr; Back to Event Discovery
          </router-link>
        </div>

        <div v-if="loading" class="ee-surface p-5">
          <div class="placeholder-glow">
            <span class="placeholder col-3 mb-3"></span>
            <span class="placeholder col-8 mb-3" style="height: 32px;"></span>
            <span class="placeholder col-12 mb-2"></span>
            <span class="placeholder col-10"></span>
          </div>
        </div>

        <div v-else-if="errorMessage" class="ee-surface p-5 text-center">
          <h2 class="h4 fw-bold mb-2">Unable to Load Event</h2>
          <p class="text-secondary mb-3">{{ errorMessage }}</p>
          <router-link to="/events" class="btn btn-primary">Return to Events</router-link>
        </div>

        <div v-else-if="event" class="row g-4">
          <!-- Main Event Information Column -->
          <div class="col-lg-8">
            <div class="ee-surface p-4 p-md-5 h-100">
              <div class="ee-meta-line mb-3">
                <span class="fw-semibold text-dark">{{ event.category_name }}</span>
                <span class="ee-meta-sep">·</span>
                <span>{{ event.city }}</span>
                <span class="ee-meta-sep">·</span>
                <span
                  class="ee-status-text"
                  :class="`ee-status-${event.status.toLowerCase()}`"
                >
                  Status: {{ event.status }}
                </span>
              </div>

              <h1 class="h2 fw-bold mb-3">{{ event.title }}</h1>

              <div class="ee-meta-line mb-4 pb-3 border-bottom">
                <span>Hosted by <strong class="text-dark">{{ event.organizer_name }}</strong></span>
                <template v-if="event.organizer_organization">
                  <span class="ee-meta-sep">·</span>
                  <span>{{ event.organizer_organization }}</span>
                </template>
              </div>

              <h2 class="h5 fw-bold mb-2">About This Event</h2>
              <p class="text-secondary mb-4" style="white-space: pre-line;">
                {{ event.description }}
              </p>

              <div class="row g-3 pt-3 border-top">
                <div class="col-sm-6">
                  <div class="small text-muted">Venue &amp; City</div>
                  <div class="fw-semibold">{{ event.venue }}</div>
                  <div class="small text-secondary">{{ event.city }}</div>
                </div>
                <div class="col-sm-6">
                  <div class="small text-muted">Ticket Pricing</div>
                  <div class="fw-semibold font-mono-tabular">
                    {{ event.is_free ? 'Free Registration ($0.00)' : `$${Number(event.price).toFixed(2)} USD (Informational — No Online Payment)` }}
                  </div>
                  <div v-if="!event.is_free" class="small text-secondary">
                    Displayed price is informational only; no payment is collected online.
                  </div>
                </div>
                <div class="col-sm-6">
                  <div class="small text-muted">Starts (UTC)</div>
                  <div class="fw-semibold font-mono-tabular">{{ formatDateTime(event.start_datetime) }}</div>
                </div>
                <div class="col-sm-6">
                  <div class="small text-muted">Ends (UTC)</div>
                  <div class="fw-semibold font-mono-tabular">{{ formatDateTime(event.end_datetime) }}</div>
                </div>
                <div class="col-sm-6">
                  <div class="small text-muted">Registration Deadline (UTC)</div>
                  <div class="fw-semibold font-mono-tabular">{{ formatDateTime(event.registration_deadline) }}</div>
                </div>
                <div class="col-sm-6">
                  <div class="small text-muted">Seat Availability</div>
                  <div class="fw-semibold font-mono-tabular">
                    {{ event.remaining_capacity }} of {{ event.capacity }} seats remaining
                  </div>
                </div>
              </div>

              <!-- Organizer / Admin Controls -->
              <div v-if="canManage" class="mt-4 pt-4 border-top d-flex flex-wrap gap-2">
                <router-link :to="`/organizer/events/${event.id}/edit`" class="btn btn-outline-primary btn-sm">
                  Edit Event Details
                </router-link>
                <router-link :to="`/organizer/events/${event.id}/attendees`" class="btn btn-outline-secondary btn-sm">
                  Manage Attendees &amp; Check-In ({{ event.registered_count }})
                </router-link>
              </div>
            </div>
          </div>

          <!-- Registration Action Sidebar -->
          <div class="col-lg-4">
            <div class="ee-surface p-4">
              <h2 class="h5 fw-bold mb-3">Registration Status</h2>

              <div class="mb-3">
                <div class="d-flex justify-content-between small mb-1">
                  <span class="text-secondary">Confirmed Attendees</span>
                  <span class="font-mono-tabular fw-semibold">
                    {{ event.registered_count }} / {{ event.capacity }}
                  </span>
                </div>
                <div class="progress" style="height: 8px;">
                  <div
                    class="progress-bar"
                    role="progressbar"
                    :style="{ width: `${Math.min(100, (event.registered_count / event.capacity) * 100)}%` }"
                  ></div>
                </div>
              </div>

              <!-- Active Registration Card -->
              <div
                v-if="myRegistration && myRegistration.status !== 'CANCELLED'"
                class="p-3 bg-light rounded border mb-3"
              >
                <div class="small text-secondary mb-1">Your Pass Reference</div>
                <div class="h5 font-mono-tabular fw-bold mb-1">
                  {{ myRegistration.registration_reference }}
                </div>
                <div class="ee-meta-line mb-3">
                  <span class="ee-status-text ee-status-confirmed">
                    {{ myRegistration.status }}
                  </span>
                  <span class="ee-meta-sep">·</span>
                  <span class="font-mono-tabular">
                    Registered {{ formatDateShort(myRegistration.registered_at) }}
                  </span>
                </div>

                <div class="d-grid gap-2">
                  <router-link
                    :to="`/registrations/${myRegistration.id}`"
                    class="btn btn-primary btn-sm"
                  >
                    View Check-In Pass
                  </router-link>
                  <button
                    v-if="myRegistration.status === 'CONFIRMED' && !event.is_past"
                    type="button"
                    class="btn btn-outline-danger btn-sm"
                    :disabled="actionLoading"
                    @click="showCancelModal = true"
                  >
                    Cancel Registration
                  </button>
                </div>
              </div>

              <!-- Eligible to Register -->
              <template v-else>
                <div v-if="actionError" class="alert alert-danger py-2 small">
                  {{ actionError }}
                </div>

                <div v-if="!isAuthenticated" class="d-grid gap-2">
                  <p class="small text-secondary mb-2">
                    Sign in or create an account to reserve your seat and receive a check-in reference.
                  </p>
                  <router-link :to="`/login?redirect=/events/${event.id}`" class="btn btn-primary">
                    Sign In to Register
                  </router-link>
                </div>

                <div v-else-if="event.is_registration_open">
                  <div class="mb-3">
                    <label for="reg-notes" class="form-label small fw-semibold">
                      Accessibility or Dietary Notes (Optional)
                    </label>
                    <textarea
                      id="reg-notes"
                      v-model.trim="registrationNotes"
                      rows="2"
                      class="form-control form-control-sm"
                      placeholder="Optional note for the event organizer..."
                      :disabled="actionLoading"
                    ></textarea>
                  </div>
                  <button
                    type="button"
                    class="btn btn-primary w-100 py-2"
                    :disabled="actionLoading"
                    @click="handleRegister"
                  >
                    {{ actionLoading ? 'Confirming Seat...' : 'Register for This Event' }}
                  </button>
                </div>

                <div v-else class="p-3 bg-light rounded border text-secondary small">
                  <strong class="d-block text-dark mb-1">Registration Unavailable</strong>
                  <span v-if="event.status !== 'PUBLISHED'">This event is currently {{ event.status }} and not open to public registration.</span>
                  <span v-else-if="event.is_past">This event has already ended.</span>
                  <span v-else-if="event.deadline_passed">The registration deadline for this event has passed.</span>
                  <span v-else-if="event.remaining_capacity <= 0">All {{ event.capacity }} seats for this event have been reserved.</span>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </main>

    <ConfirmModal
      :visible="showCancelModal"
      title="Cancel Event Registration"
      :message="`Are you sure you want to cancel your registration (${myRegistration?.registration_reference}) for '${event?.title}'? Your seat will be released immediately.`"
      confirmLabel="Cancel My Registration"
      :danger="true"
      :loading="actionLoading"
      @cancel="showCancelModal = false"
      @confirm="handleCancelRegistration"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import PublicNavbar from '../components/PublicNavbar.vue';
import ConfirmModal from '../components/ConfirmModal.vue';
import { apiClient, extractErrorMessage } from '../api/client';
import { useAuthStore, showToast } from '../stores/auth';

const route = useRoute();
const router = useRouter();
const { isAuthenticated } = useAuthStore();

const event = ref<any | null>(null);
const myRegistration = ref<any | null>(null);
const canManage = ref(false);
const loading = ref(true);
const errorMessage = ref('');
const actionLoading = ref(false);
const actionError = ref('');
const registrationNotes = ref('');
const showCancelModal = ref(false);

async function loadEventDetail() {
  loading.value = true;
  errorMessage.value = '';
  try {
    const { data } = await apiClient.get(`/events/${route.params.id}`);
    event.value = data.event;
    myRegistration.value = data.my_registration;
    canManage.value = Boolean(data.can_manage);
  } catch (err) {
    errorMessage.value = extractErrorMessage(err, 'Event could not be found.');
  } finally {
    loading.value = false;
  }
}

async function handleRegister() {
  if (actionLoading.value || !event.value) return;
  actionLoading.value = true;
  actionError.value = '';
  try {
    const { data } = await apiClient.post(`/events/${event.value.id}/registrations`, {
      notes: registrationNotes.value,
    });
    myRegistration.value = data.registration;
    showToast(`Registration confirmed! Reference: ${data.registration.registration_reference}`, 'success');
    router.push(`/registrations/${data.registration.id}`);
  } catch (err) {
    actionError.value = extractErrorMessage(err, 'Could not complete registration.');
    await loadEventDetail();
  } finally {
    actionLoading.value = false;
  }
}

async function handleCancelRegistration() {
  if (actionLoading.value || !myRegistration.value) return;
  actionLoading.value = true;
  actionError.value = '';
  try {
    await apiClient.post(`/registrations/${myRegistration.value.id}/cancel`);
    showCancelModal.value = false;
    showToast('Your registration has been cancelled and seat capacity restored.', 'info');
    await loadEventDetail();
  } catch (err) {
    actionError.value = extractErrorMessage(err, 'Failed to cancel registration.');
    showCancelModal.value = false;
  } finally {
    actionLoading.value = false;
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

function formatDateShort(iso: string): string {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

onMounted(loadEventDetail);
</script>
