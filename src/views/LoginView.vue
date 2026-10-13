<template>
  <div class="min-vh-100 d-flex flex-column">
    <PublicNavbar />

    <main class="flex-grow-1 d-flex align-items-center py-5">
      <div class="container">
        <div class="row justify-content-center g-4">
          <div class="col-md-8 col-lg-5">
            <div class="ee-surface p-4 p-md-5">
              <div class="mb-4">
                <h1 class="h3 fw-bold mb-1">Sign In to EventEase</h1>
                <p class="text-secondary small mb-0">
                  Authenticate with your account credentials to access your dashboard.
                </p>
              </div>

              <div v-if="errorMessage" class="alert alert-danger py-2 small" role="alert">
                {{ errorMessage }}
              </div>

              <form @submit.prevent="handleSubmit" novalidate>
                <div class="mb-3">
                  <label for="login-email" class="form-label small fw-semibold">Email Address</label>
                  <input
                    id="login-email"
                    v-model.trim="email"
                    type="email"
                    class="form-control"
                    placeholder="you@organization.com"
                    required
                    autocomplete="email"
                    :disabled="submitting"
                  />
                </div>

                <div class="mb-4">
                  <label for="login-password" class="form-label small fw-semibold">Password</label>
                  <input
                    id="login-password"
                    v-model="password"
                    type="password"
                    class="form-control"
                    placeholder="Enter your password"
                    required
                    autocomplete="current-password"
                    :disabled="submitting"
                  />
                </div>

                <button
                  type="submit"
                  class="btn btn-primary w-100 py-2"
                  :disabled="submitting"
                >
                  {{ submitting ? 'Signing In...' : 'Sign In' }}
                </button>
              </form>

              <div class="mt-4 pt-3 border-top">
                <div class="small fw-semibold text-secondary mb-2">
                  Quick Demo Accounts (One-Click Sign In)
                </div>
                <div class="d-flex flex-wrap gap-2">
                  <button
                    type="button"
                    class="btn btn-outline-secondary btn-sm flex-grow-1"
                    :disabled="submitting"
                    @click="fillAndLogin('attendee@eventease.io', 'AttendeePassword123!')"
                  >
                    Attendee Demo
                  </button>
                  <button
                    type="button"
                    class="btn btn-outline-secondary btn-sm flex-grow-1"
                    :disabled="submitting"
                    @click="fillAndLogin('organizer@eventease.io', 'OrganizerPassword123!')"
                  >
                    Organizer Demo
                  </button>
                  <button
                    type="button"
                    class="btn btn-outline-secondary btn-sm flex-grow-1"
                    :disabled="submitting"
                    @click="fillAndLogin('admin@eventease.io', 'AdminPassword123!')"
                  >
                    Admin Demo
                  </button>
                </div>
              </div>

              <div class="mt-4 text-center small text-secondary">
                Don't have an account yet?
                <router-link to="/register" class="fw-semibold text-decoration-none">
                  Create an Account
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
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import PublicNavbar from '../components/PublicNavbar.vue';
import { useAuthStore, showToast } from '../stores/auth';
import { extractErrorMessage } from '../api/client';

const router = useRouter();
const route = useRoute();
const { login, getDefaultDashboardRoute } = useAuthStore();

const email = ref('');
const password = ref('');
const errorMessage = ref('');
const submitting = ref(false);

async function handleSubmit() {
  if (submitting.value) return;
  errorMessage.value = '';

  if (!email.value || !password.value) {
    errorMessage.value = 'Please enter both your email address and password.';
    return;
  }

  submitting.value = true;
  try {
    const user = await login(email.value, password.value);
    showToast(`Welcome back, ${user.full_name}.`, 'success');
    const redirectTarget = (route.query.redirect as string) || getDefaultDashboardRoute();
    router.push(redirectTarget);
  } catch (err) {
    errorMessage.value = extractErrorMessage(err, 'Invalid email or password.');
  } finally {
    submitting.value = false;
  }
}

async function fillAndLogin(demoEmail: string, demoPassword: string) {
  email.value = demoEmail;
  password.value = demoPassword;
  await handleSubmit();
}
</script>
