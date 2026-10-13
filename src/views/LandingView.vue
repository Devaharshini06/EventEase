<template>
  <div class="min-vh-100 d-flex flex-column">
    <PublicNavbar />

    <main class="flex-grow-1">
      <!-- Hero Section -->
      <section class="py-5 border-bottom bg-white">
        <div class="container py-lg-3">
          <div class="row g-4 align-items-stretch">
            <div class="col-lg-6 d-flex flex-column justify-content-center">
              <div class="ee-meta-line mb-3">
                <span class="fw-semibold text-dark">Event Discovery &amp; Registration Platform</span>
                <span class="ee-meta-sep">·</span>
                <span>Role-Based Operations</span>
              </div>

              <h1 class="display-5 fw-bold mb-3" style="font-size: clamp(2.25rem, 3.8vw, 3.35rem);">
                Publish conferences, manage capacity, and verify attendee check-ins.
              </h1>

              <p class="lead text-secondary mb-4" style="font-size: 1.05rem;">
                EventEase connects technical organizers, community hosts, and attendees on a unified scheduling and registration platform backed by transactional seat allocation.
              </p>

              <div class="d-flex flex-wrap align-items-center gap-3">
                <router-link to="/events" class="btn btn-primary px-4 py-2">
                  Browse Upcoming Events
                </router-link>
                <router-link
                  v-if="!isAuthenticated"
                  to="/register?role=organizer"
                  class="btn btn-outline-secondary px-4 py-2"
                >
                  Become an Organizer
                </router-link>
                <router-link
                  v-else
                  :to="getDefaultDashboardRoute()"
                  class="btn btn-outline-secondary px-4 py-2"
                >
                  Go to My Dashboard
                </router-link>
              </div>
            </div>

            <div class="col-lg-6">
              <div class="ee-hero-media h-100 position-relative">
                <img
                  v-if="!heroImageFailed"
                  :src="heroBannerUrl"
                  alt="Keynote presentation inside a modern timber and glass conference auditorium"
                  referrerpolicy="no-referrer"
                  class="w-100 h-100"
                  style="object-fit: cover; min-height: 360px;"
                  @error="heroImageFailed = true"
                />
                <div
                  class="position-absolute bottom-0 start-0 end-0 p-4 text-white ee-hero-scrim"
                >
                  <div class="ee-meta-line text-white-50 mb-1">
                    <span class="text-white fw-semibold">Featured Platform Capability</span>
                    <span>·</span>
                    <span class="font-mono-tabular">Real-Time Seat Ledger</span>
                  </div>
                  <p class="mb-0 small text-light">
                    Every registration generates a verifiable pass reference and updates venue capacity atomically.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Full-width KPI Strip below Hero Split -->
          <div class="row g-3 mt-4 pt-3 border-top">
            <div class="col-6 col-md-3">
              <div class="text-secondary small">Published Events</div>
              <div class="h4 fw-bold font-mono-tabular mb-0">{{ totalPublishedEvents }}</div>
            </div>
            <div class="col-6 col-md-3">
              <div class="text-secondary small">Active Categories</div>
              <div class="h4 fw-bold font-mono-tabular mb-0">{{ categories.length }}</div>
            </div>
            <div class="col-6 col-md-3">
              <div class="text-secondary small">Host Cities</div>
              <div class="h4 fw-bold font-mono-tabular mb-0">{{ citiesCount }}</div>
            </div>
            <div class="col-6 col-md-3">
              <div class="text-secondary small">Pass Verification</div>
              <div class="h4 fw-bold font-mono-tabular mb-0">Instant Reference</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Featured Upcoming Events -->
      <section class="py-5">
        <div class="container">
          <div class="d-flex flex-wrap align-items-end justify-content-between mb-4 gap-3">
            <div>
              <h2 class="h3 mb-1">Upcoming Published Events</h2>
              <p class="text-secondary mb-0">
                Live conferences, workshops, and community sessions open for registration.
              </p>
            </div>
            <router-link to="/events" class="btn btn-outline-secondary">
              View All Events
            </router-link>
          </div>

          <div v-if="loading" class="row g-4">
            <div v-for="n in 3" :key="n" class="col-md-6 col-lg-4">
              <div class="ee-surface p-4" style="height: 240px;">
                <div class="placeholder-glow">
                  <span class="placeholder col-5 mb-3"></span>
                  <span class="placeholder col-10 mb-2"></span>
                  <span class="placeholder col-8 mb-4"></span>
                  <span class="placeholder col-6"></span>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="featuredEvents.length === 0" class="ee-surface p-5 text-center">
            <h3 class="h5 mb-2">No published events available right now</h3>
            <p class="text-secondary mb-3">
              Check back soon or sign in as an organizer to publish a new event.
            </p>
            <router-link to="/login" class="btn btn-primary">Sign In to Publish</router-link>
          </div>

          <div v-else class="row g-4">
            <div
              v-for="ev in featuredEvents"
              :key="ev.id"
              class="col-md-6 col-lg-4"
            >
              <EventCard :event="ev" />
            </div>
          </div>
        </div>
      </section>

      <!-- Categories Directory -->
      <section class="py-5 bg-white border-top border-bottom">
        <div class="container">
          <div class="mb-4">
            <h2 class="h3 mb-1">Browse by Event Category</h2>
            <p class="text-secondary mb-0">
              Filter sessions by subject domain and technical focus.
            </p>
          </div>

          <div class="row g-3">
            <div
              v-for="cat in categories"
              :key="cat.id"
              class="col-sm-6 col-lg-3"
            >
              <router-link
                :to="`/events?category_id=${cat.id}`"
                class="ee-surface-interactive p-3 d-block text-decoration-none h-100"
              >
                <div class="d-flex align-items-center justify-content-between mb-1">
                  <span class="fw-bold text-dark">{{ cat.name }}</span>
                  <span class="font-mono-tabular small text-secondary">
                    {{ cat.published_event_count || 0 }} events
                  </span>
                </div>
                <p class="small text-secondary mb-0">
                  {{ cat.description }}
                </p>
              </router-link>
            </div>
          </div>
        </div>
      </section>

      <!-- Role Workflows Section -->
      <section class="py-5">
        <div class="container">
          <div class="mb-4">
            <h2 class="h3 mb-1">Built for Every Event Role</h2>
            <p class="text-secondary mb-0">
              Dedicated workspaces enforced with server-side Flask-Security-Too authorization.
            </p>
          </div>

          <div class="row g-4">
            <div class="col-md-4">
              <div class="ee-surface p-4 h-100">
                <div class="ee-meta-line mb-2">
                  <span class="fw-bold text-dark">01. Event Attendees</span>
                </div>
                <h3 class="h5 mb-2">Discover &amp; Register</h3>
                <p class="text-secondary small mb-0">
                  Filter live events by city, date, category, and availability. Reserve seats with instant registration references and manage cancellations before deadlines.
                </p>
              </div>
            </div>
            <div class="col-md-4">
              <div class="ee-surface p-4 h-100">
                <div class="ee-meta-line mb-2">
                  <span class="fw-bold text-dark">02. Event Organizers</span>
                </div>
                <h3 class="h5 mb-2">Publish &amp; Check In</h3>
                <p class="text-secondary small mb-0">
                  Create draft or published events, track real-time occupancy, export attendee rosters to CSV, and check in guests at the venue door.
                </p>
              </div>
            </div>
            <div class="col-md-4">
              <div class="ee-surface p-4 h-100">
                <div class="ee-meta-line mb-2">
                  <span class="fw-bold text-dark">03. Administrators</span>
                </div>
                <h3 class="h5 mb-2">Govern &amp; Audit</h3>
                <p class="text-secondary small mb-0">
                  Oversee platform-wide metrics, manage the category registry, assign user roles, and activate or deactivate user accounts immediately.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <footer class="bg-white border-top py-4 mt-auto">
      <div class="container d-flex flex-wrap align-items-center justify-content-between gap-3 small text-secondary">
        <div>
          <span class="fw-bold text-dark">EventEase</span> · Event Management and Registration Platform
        </div>
        <div class="d-flex gap-4">
          <router-link to="/events" class="text-decoration-none text-secondary">Explore Events</router-link>
          <router-link to="/login" class="text-decoration-none text-secondary">Sign In</router-link>
          <router-link to="/register" class="text-decoration-none text-secondary">Create Account</router-link>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import PublicNavbar from '../components/PublicNavbar.vue';
import EventCard from '../components/EventCard.vue';
import { apiClient } from '../api/client';
import { useAuthStore } from '../stores/auth';
import heroBannerUrl from '../assets/images/hero_eventease_summit_1791904231050.jpg';

const { isAuthenticated, getDefaultDashboardRoute } = useAuthStore();

const featuredEvents = ref<any[]>([]);
const categories = ref<any[]>([]);
const totalPublishedEvents = ref(0);
const citiesCount = ref(0);
const loading = ref(true);
const heroImageFailed = ref(false);

onMounted(async () => {
  loading.value = true;
  try {
    const [eventsRes, catsRes] = await Promise.all([
      apiClient.get('/events', { params: { page: 1, page_size: 6, sort_by: 'date_asc' } }),
      apiClient.get('/categories', { params: { include_counts: true, active_only: true } }),
    ]);
    featuredEvents.value = eventsRes.data.events || [];
    totalPublishedEvents.value = eventsRes.data.pagination?.total || 0;
    citiesCount.value = (eventsRes.data.available_cities || []).length;
    categories.value = catsRes.data.categories || [];
  } catch {
    // Handled gracefully by empty state
  } finally {
    loading.value = false;
  }
});
</script>
