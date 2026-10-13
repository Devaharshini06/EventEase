<template>
  <DashboardLayout :pageTitle="isEditing ? 'Edit Event' : 'Create New Event'">
    <div class="row justify-content-center">
      <div class="col-xl-9">
        <div class="ee-surface p-4 p-md-5">
          <div class="d-flex align-items-center justify-content-between mb-4 pb-3 border-bottom">
            <div>
              <h1 class="h4 fw-bold mb-1">
                {{ isEditing ? 'Update Event Configuration' : 'Publish or Draft a New Event' }}
              </h1>
              <p class="small text-secondary mb-0">
                Configure venue details, UTC schedule bounds, registration deadline, and attendee capacity.
              </p>
            </div>
            <router-link to="/organizer/events" class="btn btn-outline-secondary btn-sm">
              Back to My Events
            </router-link>
          </div>

          <div v-if="loadingInitial" class="py-4 text-center text-secondary">
            Loading event configuration...
          </div>

          <form v-else @submit.prevent="handleSubmit" novalidate>
            <div v-if="errorMessage" class="alert alert-danger py-2 small" role="alert">
              {{ errorMessage }}
            </div>

            <div class="row g-3 mb-3">
              <div class="col-md-8">
                <label for="ev-title" class="form-label small fw-semibold">Event Title *</label>
                <input
                  id="ev-title"
                  v-model.trim="form.title"
                  type="text"
                  class="form-control"
                  placeholder="e.g., Distributed Systems & Storage Architecture Summit"
                  required
                  :disabled="submitting"
                />
              </div>

              <div class="col-md-4">
                <label for="ev-category" class="form-label small fw-semibold">Category *</label>
                <select
                  id="ev-category"
                  v-model="form.category_id"
                  class="form-select"
                  required
                  :disabled="submitting"
                >
                  <option value="" disabled>Select a Category</option>
                  <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                    {{ cat.name }}
                  </option>
                </select>
              </div>
            </div>

            <div class="mb-3">
              <label for="ev-desc" class="form-label small fw-semibold">Event Description *</label>
              <textarea
                id="ev-desc"
                v-model.trim="form.description"
                rows="4"
                class="form-control"
                placeholder="Provide a comprehensive overview of the agenda, speakers, and target audience (minimum 10 characters)..."
                required
                :disabled="submitting"
              ></textarea>
            </div>

            <div class="row g-3 mb-3">
              <div class="col-md-7">
                <label for="ev-venue" class="form-label small fw-semibold">Venue Name &amp; Address *</label>
                <input
                  id="ev-venue"
                  v-model.trim="form.venue"
                  type="text"
                  class="form-control"
                  placeholder="e.g., Yerba Buena Center for the Arts, Forum Hall"
                  required
                  :disabled="submitting"
                />
              </div>

              <div class="col-md-5">
                <label for="ev-city" class="form-label small fw-semibold">City *</label>
                <input
                  id="ev-city"
                  v-model.trim="form.city"
                  type="text"
                  class="form-control"
                  placeholder="e.g., San Francisco"
                  required
                  :disabled="submitting"
                />
              </div>
            </div>

            <div class="row g-3 mb-3">
              <div class="col-md-4">
                <label for="ev-start" class="form-label small fw-semibold">Start Date &amp; Time *</label>
                <input
                  id="ev-start"
                  v-model="form.start_datetime"
                  type="datetime-local"
                  class="form-control font-mono-tabular"
                  required
                  :disabled="submitting"
                />
              </div>

              <div class="col-md-4">
                <label for="ev-end" class="form-label small fw-semibold">End Date &amp; Time *</label>
                <input
                  id="ev-end"
                  v-model="form.end_datetime"
                  type="datetime-local"
                  class="form-control font-mono-tabular"
                  required
                  :disabled="submitting"
                />
              </div>

              <div class="col-md-4">
                <label for="ev-deadline" class="form-label small fw-semibold">Registration Deadline *</label>
                <input
                  id="ev-deadline"
                  v-model="form.registration_deadline"
                  type="datetime-local"
                  class="form-control font-mono-tabular"
                  required
                  :disabled="submitting"
                />
              </div>
            </div>

            <div class="row g-3 mb-4">
              <div class="col-md-4">
                <label for="ev-capacity" class="form-label small fw-semibold">
                  Attendee Capacity *
                  <span v-if="isEditing && currentRegistered > 0" class="text-muted">
                    (min {{ currentRegistered }})
                  </span>
                </label>
                <input
                  id="ev-capacity"
                  v-model.number="form.capacity"
                  type="number"
                  min="1"
                  max="100000"
                  class="form-control font-mono-tabular"
                  required
                  :disabled="submitting"
                />
              </div>

              <div class="col-md-4">
                <label for="ev-price" class="form-label small fw-semibold">
                  Informational Price (USD)
                </label>
                <input
                  id="ev-price"
                  v-model.number="form.price"
                  type="number"
                  min="0"
                  step="0.01"
                  class="form-control font-mono-tabular"
                  :disabled="submitting"
                />
                <div class="form-text small">0.00 for Free events. Informational only.</div>
              </div>

              <div class="col-md-4">
                <label for="ev-status" class="form-label small fw-semibold">Publication Status *</label>
                <select
                  id="ev-status"
                  v-model="form.status"
                  class="form-select"
                  :disabled="submitting"
                >
                  <option value="DRAFT">DRAFT (Private to Organizer)</option>
                  <option value="PUBLISHED">PUBLISHED (Open for Discovery)</option>
                  <option v-if="isEditing" value="CANCELLED">CANCELLED</option>
                  <option v-if="isEditing" value="ARCHIVED">ARCHIVED</option>
                </select>
              </div>
            </div>

            <div class="d-flex justify-content-end gap-2 pt-3 border-top">
              <router-link to="/organizer/events" class="btn btn-outline-secondary">
                Cancel
              </router-link>
              <button
                type="submit"
                class="btn btn-primary px-4"
                :disabled="submitting"
              >
                {{ submitting ? 'Saving Event...' : isEditing ? 'Save Changes' : 'Create Event' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import DashboardLayout from '../components/DashboardLayout.vue';
import { apiClient, extractErrorMessage } from '../api/client';
import { showToast } from '../stores/auth';

const route = useRoute();
const router = useRouter();

const isEditing = computed(() => Boolean(route.params.id));
const categories = ref<any[]>([]);
const loadingInitial = ref(false);
const submitting = ref(false);
const errorMessage = ref('');
const currentRegistered = ref(0);

function defaultFutureIso(days: number, hour: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  d.setHours(hour, 0, 0, 0);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:00`;
}

function toDatetimeLocal(iso: string): string {
  if (!iso) return '';
  return iso.slice(0, 16);
}

const form = reactive({
  title: '',
  description: '',
  category_id: '' as number | '',
  venue: '',
  city: '',
  start_datetime: defaultFutureIso(14, 9),
  end_datetime: defaultFutureIso(14, 17),
  registration_deadline: defaultFutureIso(12, 18),
  capacity: 50,
  price: 0,
  status: 'PUBLISHED',
});

onMounted(async () => {
  loadingInitial.value = true;
  try {
    const catRes = await apiClient.get('/categories');
    categories.value = catRes.data.categories || [];
    if (!isEditing.value && categories.value.length > 0) {
      form.category_id = categories.value[0].id;
    }

    if (isEditing.value) {
      const { data } = await apiClient.get(`/events/${route.params.id}`);
      const ev = data.event;
      form.title = ev.title;
      form.description = ev.description;
      form.category_id = ev.category_id;
      form.venue = ev.venue;
      form.city = ev.city;
      form.start_datetime = toDatetimeLocal(ev.start_datetime);
      form.end_datetime = toDatetimeLocal(ev.end_datetime);
      form.registration_deadline = toDatetimeLocal(ev.registration_deadline);
      form.capacity = ev.capacity;
      form.price = ev.price;
      form.status = ev.status;
      currentRegistered.value = ev.registered_count || 0;
    }
  } catch (err) {
    errorMessage.value = extractErrorMessage(err, 'Could not load event form data.');
  } finally {
    loadingInitial.value = false;
  }
});

async function handleSubmit() {
  if (submitting.value) return;
  errorMessage.value = '';

  if (!form.title || form.title.length < 3) {
    errorMessage.value = 'Event title must be at least 3 characters.';
    return;
  }
  if (!form.description || form.description.length < 10) {
    errorMessage.value = 'Event description must be at least 10 characters.';
    return;
  }
  if (!form.category_id) {
    errorMessage.value = 'Please select an event category.';
    return;
  }
  if (!form.venue || !form.city) {
    errorMessage.value = 'Both venue and city are required.';
    return;
  }

  submitting.value = true;
  try {
    const payload = {
      title: form.title,
      description: form.description,
      category_id: Number(form.category_id),
      venue: form.venue,
      city: form.city,
      start_datetime: form.start_datetime,
      end_datetime: form.end_datetime,
      registration_deadline: form.registration_deadline,
      capacity: Number(form.capacity),
      price: Number(form.price || 0),
      status: form.status,
    };

    if (isEditing.value) {
      const { data } = await apiClient.put(`/events/${route.params.id}`, payload);
      showToast('Event updated successfully.', 'success');
      router.push(`/events/${data.event.id}`);
    } else {
      const { data } = await apiClient.post('/events', payload);
      showToast('Event created successfully.', 'success');
      router.push(`/events/${data.event.id}`);
    }
  } catch (err) {
    errorMessage.value = extractErrorMessage(err, 'Failed to save event.');
  } finally {
    submitting.value = false;
  }
}
</script>
