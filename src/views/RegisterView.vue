<template>
  <div class="min-vh-100 d-flex flex-column">
    <PublicNavbar />

    <main class="flex-grow-1 d-flex align-items-center py-5">
      <div class="container">
        <div class="row justify-content-center">
          <div class="col-md-9 col-lg-6">
            <div class="ee-surface p-4 p-md-5">
              <div class="mb-4">
                <h1 class="h3 fw-bold mb-1">Create Your EventEase Account</h1>
                <p class="text-secondary small mb-0">
                  Register as an event attendee or event organizer. Administrator roles are restricted to internal assignment.
                </p>
              </div>

              <div v-if="errorMessage" class="alert alert-danger py-2 small" role="alert">
                {{ errorMessage }}
              </div>

              <form @submit.prevent="handleSubmit" novalidate>
                <div class="mb-3">
                  <label class="form-label small fw-semibold d-block">Account Type</label>
                  <div class="ee-segmented w-100">
                    <button
                      type="button"
                      class="ee-segmented-btn flex-grow-1"
                      :class="{ active: form.role === 'attendee' }"
                      @click="form.role = 'attendee'"
                    >
                      Attendee (Discover &amp; Register)
                    </button>
                    <button
                      type="button"
                      class="ee-segmented-btn flex-grow-1"
                      :class="{ active: form.role === 'organizer' }"
                      @click="form.role = 'organizer'"
                    >
                      Event Organizer (Host &amp; Manage)
                    </button>
                  </div>
                </div>

                <div class="row g-3 mb-3">
                  <div class="col-md-6">
                    <label for="reg-fullname" class="form-label small fw-semibold">Full Name *</label>
                    <input
                      id="reg-fullname"
                      v-model.trim="form.full_name"
                      type="text"
                      class="form-control"
                      placeholder="Alex Rivera"
                      required
                      :disabled="submitting"
                    />
                  </div>
                  <div class="col-md-6">
                    <label for="reg-email" class="form-label small fw-semibold">Email Address *</label>
                    <input
                      id="reg-email"
                      v-model.trim="form.email"
                      type="email"
                      class="form-control"
                      placeholder="alex@company.org"
                      required
                      :disabled="submitting"
                    />
                  </div>
                </div>

                <div class="row g-3 mb-3">
                  <div class="col-md-6">
                    <label for="reg-org" class="form-label small fw-semibold">Organization / Affiliation</label>
                    <input
                      id="reg-org"
                      v-model.trim="form.organization"
                      type="text"
                      class="form-control"
                      placeholder="Meridian Engineering"
                      :disabled="submitting"
                    />
                  </div>
                  <div class="col-md-6">
                    <label for="reg-phone" class="form-label small fw-semibold">Phone Number</label>
                    <input
                      id="reg-phone"
                      v-model.trim="form.phone"
                      type="tel"
                      class="form-control"
                      placeholder="+1 (555) 234-5678"
                      :disabled="submitting"
                    />
                  </div>
                </div>

                <div class="row g-3 mb-4">
                  <div class="col-md-6">
                    <label for="reg-password" class="form-label small fw-semibold">Password (min. 8 chars) *</label>
                    <input
                      id="reg-password"
                      v-model="form.password"
                      type="password"
                      class="form-control"
                      placeholder="At least 8 characters"
                      required
                      :disabled="submitting"
                    />
                  </div>
                  <div class="col-md-6">
                    <label for="reg-confirm" class="form-label small fw-semibold">Confirm Password *</label>
                    <input
                      id="reg-confirm"
                      v-model="form.confirmPassword"
                      type="password"
                      class="form-control"
                      placeholder="Repeat password"
                      required
                      :disabled="submitting"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  class="btn btn-primary w-100 py-2"
                  :disabled="submitting"
                >
                  {{ submitting ? 'Creating Account...' : 'Create Account' }}
                </button>
              </form>

              <div class="mt-4 text-center small text-secondary">
                Already registered?
                <router-link to="/login" class="fw-semibold text-decoration-none">
                  Sign In Here
                </router-link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import PublicNavbar from '../components/PublicNavbar.vue';
import { useAuthStore, showToast } from '../stores/auth';
import { extractErrorMessage } from '../api/client';

const router = useRouter();
const route = useRoute();
const { register, getDefaultDashboardRoute } = useAuthStore();

const form = reactive({
  full_name: '',
  email: '',
  organization: '',
  phone: '',
  password: '',
  confirmPassword: '',
  role: 'attendee' as 'attendee' | 'organizer',
});

const errorMessage = ref('');
const submitting = ref(false);

onMounted(() => {
  if (route.query.role === 'organizer') {
    form.role = 'organizer';
  }
});

async function handleSubmit() {
  if (submitting.value) return;
  errorMessage.value = '';

  if (!form.full_name || form.full_name.length < 2) {
    errorMessage.value = 'Please enter your full name (at least 2 characters).';
    return;
  }
  if (!form.email || !form.email.includes('@')) {
    errorMessage.value = 'Please provide a valid email address.';
    return;
  }
  if (form.password.length < 8) {
    errorMessage.value = 'Password must be at least 8 characters long.';
    return;
  }
  if (form.password !== form.confirmPassword) {
    errorMessage.value = 'Passwords do not match.';
    return;
  }

  submitting.value = true;
  try {
    await register({
      email: form.email,
      password: form.password,
      full_name: form.full_name,
      organization: form.organization,
      phone: form.phone,
      role: form.role,
    });
    showToast('Account created and authenticated.', 'success');
    router.push(getDefaultDashboardRoute());
  } catch (err) {
    errorMessage.value = extractErrorMessage(err, 'Registration failed.');
  } finally {
    submitting.value = false;
  }
}
</script>
