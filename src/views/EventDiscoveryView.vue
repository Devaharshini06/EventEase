<template>
  <div class="min-vh-100 d-flex flex-column">
    <PublicNavbar />

    <main class="flex-grow-1 py-4 py-lg-5">
      <div class="container">
        <div class="d-flex flex-wrap align-items-end justify-content-between gap-3 mb-4">
          <div>
            <h1 class="h2 fw-bold mb-1">Discover Published Events</h1>
            <p class="text-secondary mb-0">
              Search and filter conferences, workshops, and community gatherings with real-time seat availability.
            </p>
          </div>
          <div class="ee-meta-line">
            <span class="font-mono-tabular fw-semibold text-dark">{{ pagination.total }}</span>
            <span>matching event(s)</span>
          </div>
        </div>

        <!-- Filter Bar -->
        <div class="ee-surface p-3 p-md-4 mb-4">
          <form @submit.prevent="applyFilters">
            <div class="row g-3">
              <div class="col-md-4">
                <label for="filter-search" class="form-label small fw-semibold">Search Keyword</label>
                <input
                  id="filter-search"
                  v-model.trim="filters.search"
                  type="search"
                  class="form-control form-control-sm"
                  placeholder="Title, description, venue, or city..."
                />
              </div>

              <div class="col-sm-6 col-md-2">
                <label for="filter-category" class="form-label small fw-semibold">Category</label>
                <select id="filter-category" v-model="filters.category_id" class="form-select form-select-sm">
                  <option value="">All Categories</option>
                  <option v-for="cat in categories" :key="cat.id" :value="String(cat.id)">
                    {{ cat.name }}
                  </option>
                </select>
              </div>

              <div class="col-sm-6 col-md-2">
                <label for="filter-city" class="form-label small fw-semibold">Location (City)</label>
                <select id="filter-city" v-model="filters.city" class="form-select form-select-sm">
                  <option value="">All Cities</option>
                  <option v-for="c in availableCities" :key="c" :value="c">
                    {{ c }}
                  </option>
                </select>
              </div>

              <div class="col-sm-6 col-md-2">
                <label for="filter-price" class="form-label small fw-semibold">Pricing Type</label>
                <select id="filter-price" v-model="filters.price_type" class="form-select form-select-sm">
                  <option value="">All Pricing</option>
                  <option value="free">Free Only</option>
                  <option value="paid">Paid (Informational)</option>
                </select>
              </div>

              <div class="col-sm-6 col-md-2">
                <label for="filter-sort" class="form-label small fw-semibold">Sort By</label>
                <select id="filter-sort" v-model="filters.sort_by" class="form-select form-select-sm">
                  <option value="date_asc">Soonest First</option>
                  <option value="date_desc">Latest First</option>
                  <option value="capacity_desc">Most Seats Remaining</option>
                  <option value="price_asc">Price: Low to High</option>
                  <option value="title_asc">Title: A to Z</option>
                </select>
              </div>

              <div class="col-sm-6 col-md-3">
                <label for="filter-start-date" class="form-label small fw-semibold">From Date</label>
                <input
                  id="filter-start-date"
                  v-model="filters.start_date"
                  type="date"
                  class="form-control form-control-sm"
                />
              </div>

              <div class="col-sm-6 col-md-3">
                <label for="filter-end-date" class="form-label small fw-semibold">To Date</label>
                <input
                  id="filter-end-date"
                  v-model="filters.end_date"
                  type="date"
                  class="form-control form-control-sm"
                />
              </div>

              <div class="col-sm-6 col-md-3 d-flex align-items-end">
                <div class="ee-segmented w-100">
                  <button
                    type="button"
                    class="ee-segmented-btn flex-grow-1"
                    :class="{ active: filters.availability === '' }"
                    @click="filters.availability = ''; applyFilters()"
                  >
                    All Published
                  </button>
                  <button
                    type="button"
                    class="ee-segmented-btn flex-grow-1"
                    :class="{ active: filters.availability === 'open' }"
                    @click="filters.availability = 'open'; applyFilters()"
                  >
                    Open Seats Only
                  </button>
                </div>
              </div>

              <div class="col-sm-6 col-md-3 d-flex align-items-end gap-2">
                <button type="submit" class="btn btn-primary btn-sm flex-grow-1" :disabled="loading">
                  Apply Filters
                </button>
                <button
                  type="button"
                  class="btn btn-outline-secondary btn-sm"
                  :disabled="loading"
                  @click="resetFilters"
                >
                  Reset
                </button>
              </div>
            </div>
          </form>
        </div>

        <!-- Error State -->
        <div v-if="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>

        <!-- Loading State -->
        <div v-if="loading" class="row g-4">
          <div v-for="n in 6" :key="n" class="col-md-6 col-lg-4">
            <div class="ee-surface p-4" style="height: 240px;">
              <div class="placeholder-glow">
                <span class="placeholder col-6 mb-3"></span>
                <span class="placeholder col-10 mb-2"></span>
                <span class="placeholder col-8 mb-4"></span>
                <span class="placeholder col-5"></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="events.length === 0" class="ee-surface p-5 text-center">
          <h2 class="h5 fw-bold mb-2">No events match your current filters</h2>
          <p class="text-secondary small mb-3">
            Try broadening your search terms, clearing date bounds, or viewing all categories.
          </p>
          <button type="button" class="btn btn-primary btn-sm" @click="resetFilters">
            Clear All Filters
          </button>
        </div>

        <!-- Event Grid -->
        <div v-else class="row g-4">
          <div v-for="ev in events" :key="ev.id" class="col-md-6 col-lg-4">
            <EventCard :event="ev" />
          </div>
        </div>

        <!-- Pagination -->
        <div
          v-if="pagination.total_pages > 1"
          class="d-flex align-items-center justify-content-between mt-4 pt-3 border-top"
        >
          <div class="small text-secondary font-mono-tabular">
            Page {{ pagination.page }} of {{ pagination.total_pages }} ({{ pagination.total }} total)
          </div>
          <div class="d-flex gap-2">
            <button
              type="button"
              class="btn btn-outline-secondary btn-sm"
              :disabled="pagination.page <= 1 || loading"
              @click="changePage(pagination.page - 1)"
            >
              Previous
            </button>
            <button
              type="button"
              class="btn btn-outline-secondary btn-sm"
              :disabled="pagination.page >= pagination.total_pages || loading"
              @click="changePage(pagination.page + 1)"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import PublicNavbar from '../components/PublicNavbar.vue';
import EventCard from '../components/EventCard.vue';
import { apiClient, extractErrorMessage } from '../api/client';

const route = useRoute();
const router = useRouter();

const events = ref<any[]>([]);
const categories = ref<any[]>([]);
const availableCities = ref<string[]>([]);
const loading = ref(true);
const errorMessage = ref('');

const filters = reactive({
  search: (route.query.search as string) || '',
  category_id: (route.query.category_id as string) || '',
  city: (route.query.city as string) || '',
  price_type: (route.query.price_type as string) || '',
  availability: (route.query.availability as string) || '',
  start_date: (route.query.start_date as string) || '',
  end_date: (route.query.end_date as string) || '',
  sort_by: (route.query.sort_by as string) || 'date_asc',
});

const pagination = reactive({
  page: Number(route.query.page) || 1,
  page_size: 9,
  total: 0,
  total_pages: 1,
});

async function loadCategories() {
  try {
    const { data } = await apiClient.get('/categories', { params: { active_only: true } });
    categories.value = data.categories || [];
  } catch {
    // Non-fatal
  }
}

async function fetchEvents() {
  loading.value = true;
  errorMessage.value = '';
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.page_size,
      sort_by: filters.sort_by,
    };
    if (filters.search) params.search = filters.search;
    if (filters.category_id) params.category_id = filters.category_id;
    if (filters.city) params.city = filters.city;
    if (filters.price_type) params.price_type = filters.price_type;
    if (filters.availability) params.availability = filters.availability;
    if (filters.start_date) params.start_date = `${filters.start_date}T00:00:00`;
    if (filters.end_date) params.end_date = `${filters.end_date}T23:59:59`;

    const { data } = await apiClient.get('/events', { params });
    events.value = data.events || [];
    availableCities.value = data.available_cities || [];
    if (data.pagination) {
      pagination.total = data.pagination.total;
      pagination.page = data.pagination.page;
      pagination.total_pages = data.pagination.total_pages;
    }
  } catch (err) {
    errorMessage.value = extractErrorMessage(err, 'Failed to load events.');
  } finally {
    loading.value = false;
  }
}

function applyFilters() {
  pagination.page = 1;
  syncQueryAndFetch();
}

function resetFilters() {
  filters.search = '';
  filters.category_id = '';
  filters.city = '';
  filters.price_type = '';
  filters.availability = '';
  filters.start_date = '';
  filters.end_date = '';
  filters.sort_by = 'date_asc';
  pagination.page = 1;
  syncQueryAndFetch();
}

function changePage(newPage: number) {
  pagination.page = newPage;
  syncQueryAndFetch();
}

function syncQueryAndFetch() {
  const query: Record<string, string> = {};
  if (filters.search) query.search = filters.search;
  if (filters.category_id) query.category_id = filters.category_id;
  if (filters.city) query.city = filters.city;
  if (filters.price_type) query.price_type = filters.price_type;
  if (filters.availability) query.availability = filters.availability;
  if (filters.start_date) query.start_date = filters.start_date;
  if (filters.end_date) query.end_date = filters.end_date;
  if (filters.sort_by !== 'date_asc') query.sort_by = filters.sort_by;
  if (pagination.page > 1) query.page = String(pagination.page);

  router.replace({ path: '/events', query });
  fetchEvents();
}

watch(
  () => route.query,
  (newQuery) => {
    if (newQuery.price_type !== undefined && newQuery.price_type !== filters.price_type) {
      filters.price_type = String(newQuery.price_type || '');
      fetchEvents();
    }
    if (newQuery.category_id !== undefined && newQuery.category_id !== filters.category_id) {
      filters.category_id = String(newQuery.category_id || '');
      fetchEvents();
    }
  }
);

onMounted(async () => {
  await Promise.all([loadCategories(), fetchEvents()]);
});
</script>
