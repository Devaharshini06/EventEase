<template>
  <DashboardLayout pageTitle="Account Profile &amp; Notifications">
    <div class="row g-4">
      <!-- Profile & Password Update -->
      <div class="col-lg-6">
        <div class="ee-surface p-4">
          <h2 class="h5 fw-bold mb-1">Personal Profile &amp; Credentials</h2>
          <p class="small text-secondary mb-4">
            Update your contact details or rotate your password.
          </p>

          <div v-if="errorMessage" class="alert alert-danger py-2 small">
            {{ errorMessage }}
          </div>

          <form @submit.prevent="handleSaveProfile" novalidate>
            <div class="mb-3">
              <label class="form-label small fw-semibold">Email Address (Verified Login ID)</label>
              <input
                type="email"
                class="form-control bg-light"
                :value="state.user?.email"
                disabled
              />
            </div>

            <div class="mb-3">
              <label class="form-label small fw-semibold">Assigned Platform Role(s)</label>
              <input
                type="text"
                class="form-control bg-light font-mono-tabular"
                :value="(state.user?.roles || []).join(', ')"
                disabled
              />
            </div>

            <div class="mb-3">
              <label for="prof-name" class="form-label small fw-semibold">Full Name *</label>
              <input
                id="prof-name"
                v-model.trim="form.full_name"
                type="text"
                class="form-control"
                required
                :disabled="saving"
              />
            </div>

            <div class="row g-3 mb-3">
              <div class="col-md-6">
                <label for="prof-org" class="form-label small fw-semibold">Organization</label>
                <input
                  id="prof-org"
                  v-model.trim="form.organization"
                  type="text"
                  class="form-control"
                  :disabled="saving"
                />
              </div>
              <div class="col-md-6">
                <label for="prof-phone" class="form-label small fw-semibold">Phone Number</label>
                <input
                  id="prof-phone"
                  v-model.trim="form.phone"
                  type="tel"
                  class="form-control"
                  :disabled="saving"
                />
              </div>
            </div>

            <div class="mb-4">
              <label for="prof-bio" class="form-label small fw-semibold">Bio / Professional Summary</label>
              <textarea
                id="prof-bio"
                v-model.trim="form.bio"
                rows="3"
                class="form-control"
                :disabled="saving"
              ></textarea>
            </div>

            <div class="pt-3 border-top mb-4">
              <h3 class="h6 fw-bold mb-2">Change Password (Optional)</h3>
              <div class="row g-3">
                <div class="col-md-6">
                  <label for="prof-cur-pw" class="form-label small fw-semibold">Current Password</label>
                  <input
                    id="prof-cur-pw"
                    v-model="form.current_password"
                    type="password"
                    class="form-control"
                    autocomplete="current-password"
                    :disabled="saving"
                  />
                </div>
                <div class="col-md-6">
                  <label for="prof-new-pw" class="form-label small fw-semibold">New Password (min 8 chars)</label>
                  <input
                    id="prof-new-pw"
                    v-model="form.new_password"
                    type="password"
                    class="form-control"
                    autocomplete="new-password"
                    :disabled="saving"
                  />
                </div>
              </div>
            </div>

            <button type="submit" class="btn btn-primary w-100" :disabled="saving">
              {{ saving ? 'Saving Changes...' : 'Save Profile Changes' }}
            </button>
          </form>
        </div>
      </div>

      <!-- In-App Notifications -->
      <div class="col-lg-6">
        <div class="ee-surface p-4 h-100">
          <div class="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom">
            <div>
              <h2 class="h5 fw-bold mb-0">In-App Notifications</h2>
              <p class="small text-secondary mb-0">
                Registration confirmations, check-in alerts, and event updates.
              </p>
            </div>
            <span class="font-mono-tabular small text-secondary">
              {{ state.unreadCount }} unread
            </span>
          </div>

          <div v-if="state.notifications.length === 0" class="py-5 text-center text-secondary small">
            No notifications yet.
          </div>

          <div v-else class="d-flex flex-column gap-3">
            <div
              v-for="note in state.notifications"
              :key="note.id"
              class="p-3 rounded border"
              :class="note.is_read ? 'bg-white' : 'bg-light border-primary border-opacity-25'"
            >
              <div class="d-flex align-items-start justify-content-between gap-2 mb-1">
                <div class="fw-semibold small">{{ note.title }}</div>
                <span class="font-mono-tabular text-muted" style="font-size: 0.72rem;">
                  {{ formatDateTime(note.created_at) }}
                </span>
              </div>
              <p class="small text-secondary mb-2">{{ note.content }}</p>
              <div v-if="!note.is_read" class="text-end">
                <button
                  type="button"
                  class="btn btn-outline-secondary btn-sm py-0 px-2"
                  style="font-size: 0.75rem;"
                  @click="markNotificationRead(note.id)"
                >
                  Mark Read
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue';
import DashboardLayout from '../components/DashboardLayout.vue';
import { useAuthStore, showToast } from '../stores/auth';
import { extractErrorMessage } from '../api/client';

const { state, fetchMe, updateProfile, fetchNotifications, markNotificationRead } = useAuthStore();

const saving = ref(false);
const errorMessage = ref('');

const form = reactive({
  full_name: state.user?.full_name || '',
  organization: state.user?.organization || '',
  phone: state.user?.phone || '',
  bio: state.user?.bio || '',
  current_password: '',
  new_password: '',
});

onMounted(async () => {
  const user = await fetchMe();
  if (user) {
    form.full_name = user.full_name;
    form.organization = user.organization || '';
    form.phone = user.phone || '';
    form.bio = user.bio || '';
  }
  await fetchNotifications();
});

async function handleSaveProfile() {
  if (saving.value) return;
  errorMessage.value = '';
  saving.value = true;
  try {
    const payload: Record<string, string> = {
      full_name: form.full_name,
      organization: form.organization,
      phone: form.phone,
      bio: form.bio,
    };
    if (form.new_password) {
      payload.current_password = form.current_password;
      payload.new_password = form.new_password;
    }
    await updateProfile(payload);
    form.current_password = '';
    form.new_password = '';
    showToast('Profile updated successfully.', 'success');
  } catch (err) {
    errorMessage.value = extractErrorMessage(err, 'Failed to update profile.');
  } finally {
    saving.value = false;
  }
}

function formatDateTime(iso?: string): string {
  if (!iso) return '';
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
</script>
