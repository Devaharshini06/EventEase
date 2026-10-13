<template>
  <header class="ee-topbar sticky-top">
    <div class="container h-100 d-flex align-items-center justify-content-between gap-4">
      <router-link to="/" class="ee-brand">
        EventEase
      </router-link>

      <nav class="d-none d-md-flex align-items-center gap-4">
        <router-link to="/events" class="ee-nav-link">Explore Events</router-link>
        <router-link to="/events?price_type=free" class="ee-nav-link">Free Sessions</router-link>
        <router-link v-if="isOrganizer" to="/organizer/events" class="ee-nav-link">Manage Events</router-link>
        <router-link v-else to="/register?role=organizer" class="ee-nav-link">Host Events</router-link>
        <router-link v-if="isAuthenticated" to="/attendee/registrations" class="ee-nav-link">My Registrations</router-link>
        <router-link v-if="isAdmin" to="/admin/dashboard" class="ee-nav-link">Administration</router-link>
      </nav>

      <div class="d-flex align-items-center shrink-0">
        <router-link
          v-if="isAuthenticated"
          :to="getDefaultDashboardRoute()"
          class="btn btn-primary"
        >
          Open Workspace
        </router-link>
        <router-link
          v-else
          to="/login"
          class="btn btn-primary"
        >
          Sign In
        </router-link>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useAuthStore } from '../stores/auth';

const { isAuthenticated, isOrganizer, isAdmin, getDefaultDashboardRoute } = useAuthStore();
</script>
