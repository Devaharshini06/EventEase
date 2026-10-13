<template>
  <div class="ee-workspace">
    <aside class="ee-sidebar">
      <div class="d-flex align-items-center justify-content-between pe-3">
        <router-link to="/" class="ee-sidebar-brand flex-grow-1">
          EventEase
        </router-link>
      </div>

      <div class="px-3 py-3 border-bottom border-secondary border-opacity-25">
        <div class="text-white fw-semibold text-truncate" style="font-size: 0.9rem;">
          {{ state.user?.full_name || 'Authenticated User' }}
        </div>
        <div class="ee-meta-line text-secondary" style="font-size: 0.76rem;">
          <span>{{ roleLabel }}</span>
          <span class="ee-meta-sep">·</span>
          <span class="text-truncate">{{ state.user?.email }}</span>
        </div>
      </div>

      <nav class="py-3 flex-grow-1 d-flex flex-column gap-1">
        <div class="px-4 py-1 text-secondary" style="font-size: 0.72rem; font-weight: 600;">
          Discovery
        </div>
        <router-link to="/events" class="ee-sidebar-link">
          <span>Browse All Events</span>
        </router-link>

        <div class="px-4 pt-3 pb-1 text-secondary" style="font-size: 0.72rem; font-weight: 600;">
          Attendee Portal
        </div>
        <router-link to="/attendee/dashboard" class="ee-sidebar-link">
          <span>Attendee Dashboard</span>
        </router-link>
        <router-link to="/attendee/registrations" class="ee-sidebar-link">
          <span>My Registrations</span>
        </router-link>

        <template v-if="isOrganizer">
          <div class="px-4 pt-3 pb-1 text-secondary" style="font-size: 0.72rem; font-weight: 600;">
            Organizer Console
          </div>
          <router-link to="/organizer/dashboard" class="ee-sidebar-link">
            <span>Organizer Analytics</span>
          </router-link>
          <router-link to="/organizer/events" class="ee-sidebar-link">
            <span>Event Management</span>
          </router-link>
          <router-link to="/organizer/events/new" class="ee-sidebar-link">
            <span>Create New Event</span>
          </router-link>
        </template>

        <template v-if="isAdmin">
          <div class="px-4 pt-3 pb-1 text-secondary" style="font-size: 0.72rem; font-weight: 600;">
            Platform Administration
          </div>
          <router-link to="/admin/dashboard" class="ee-sidebar-link">
            <span>Admin Overview</span>
          </router-link>
          <router-link to="/admin/users" class="ee-sidebar-link">
            <span>User Directory</span>
          </router-link>
          <router-link to="/admin/categories" class="ee-sidebar-link">
            <span>Category Registry</span>
          </router-link>
        </template>

        <div class="px-4 pt-3 pb-1 text-secondary" style="font-size: 0.72rem; font-weight: 600;">
          Account
        </div>
        <router-link to="/profile" class="ee-sidebar-link">
          <span>Profile &amp; Security</span>
          <span v-if="state.unreadCount > 0" class="font-mono-tabular text-warning">
            {{ state.unreadCount }}
          </span>
        </router-link>
      </nav>

      <div class="p-3 border-top border-secondary border-opacity-25">
        <button
          type="button"
          class="btn btn-outline-light btn-sm w-100"
          :disabled="loggingOut"
          @click="handleLogout"
        >
          {{ loggingOut ? 'Signing Out...' : 'Sign Out' }}
        </button>
      </div>
    </aside>

    <div class="ee-workspace-main">
      <header class="ee-workspace-header">
        <div class="d-flex align-items-center gap-2 text-secondary" style="font-size: 0.875rem;">
          <router-link to="/" class="text-decoration-none text-secondary">EventEase</router-link>
          <span>/</span>
          <span class="text-dark fw-semibold">{{ pageTitle }}</span>
        </div>

        <div class="d-flex align-items-center gap-3">
          <slot name="actions"></slot>
          <router-link
            v-if="isOrganizer && $route.path !== '/organizer/events/new'"
            to="/organizer/events/new"
            class="btn btn-primary btn-sm"
          >
            Create Event
          </router-link>
        </div>
      </header>

      <main class="ee-workspace-content">
        <slot></slot>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore, showToast } from '../stores/auth';

defineProps<{
  pageTitle: string;
}>();

const router = useRouter();
const { state, isOrganizer, isAdmin, logout } = useAuthStore();
const loggingOut = ref(false);

const roleLabel = computed(() => {
  const role = state.user?.primary_role;
  if (role === 'admin') return 'Administrator';
  if (role === 'organizer') return 'Organizer';
  return 'Attendee';
});

async function handleLogout() {
  loggingOut.value = true;
  try {
    await logout();
    showToast('Signed out of your EventEase session.', 'info');
    router.push('/login');
  } finally {
    loggingOut.value = false;
  }
}
</script>
