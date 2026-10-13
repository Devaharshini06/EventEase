<template>
  <DashboardLayout pageTitle="User Administration &amp; Access Control">
    <div class="ee-surface p-3 p-md-4 mb-4">
      <div class="row g-3 align-items-end">
        <div class="col-md-5">
          <label for="user-search" class="form-label small fw-semibold">Search Users</label>
          <input
            id="user-search"
            v-model.trim="searchQuery"
            type="search"
            class="form-control form-control-sm"
            placeholder="Name, email, or organization..."
            @input="fetchUsers"
          />
        </div>

        <div class="col-sm-6 col-md-4">
          <label class="form-label small fw-semibold d-block">Filter by Role</label>
          <div class="ee-segmented w-100">
            <button
              v-for="r in ['all', 'admin', 'organizer', 'attendee']"
              :key="r"
              type="button"
              class="ee-segmented-btn flex-grow-1"
              :class="{ active: roleFilter === r }"
              @click="roleFilter = r; fetchUsers()"
            >
              {{ r === 'all' ? 'All' : r.charAt(0).toUpperCase() + r.slice(1) }}
            </button>
          </div>
        </div>

        <div class="col-sm-6 col-md-3">
          <label for="user-active-filter" class="form-label small fw-semibold">Account Status</label>
          <select
            id="user-active-filter"
            v-model="activeFilter"
            class="form-select form-select-sm"
            @change="fetchUsers"
          >
            <option value="">All Accounts</option>
            <option value="true">Active Only</option>
            <option value="false">Deactivated Only</option>
          </select>
        </div>
      </div>
    </div>

    <div v-if="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>

    <div v-if="loading" class="ee-surface p-5 text-center text-secondary">
      Loading registered users...
    </div>

    <div v-else class="ee-surface">
      <div class="table-responsive">
        <table class="table ee-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Full Name &amp; Email</th>
              <th>Organization</th>
              <th>Role Assignment</th>
              <th>Account Status</th>
              <th>Joined</th>
              <th class="text-end">Account Governance</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td class="font-mono-tabular text-secondary">#{{ u.id }}</td>
              <td>
                <div class="fw-semibold">{{ u.full_name }}</div>
                <div class="small text-secondary">{{ u.email }}</div>
              </td>
              <td class="small text-secondary">{{ u.organization || '—' }}</td>
              <td>
                <select
                  class="form-select form-select-sm"
                  style="max-width: 150px;"
                  :value="u.primary_role"
                  :disabled="u.id === state.user?.id || busyUserId === u.id"
                  @change="handleRoleChange(u, ($event.target as HTMLSelectElement).value)"
                >
                  <option value="attendee">attendee</option>
                  <option value="organizer">organizer</option>
                  <option value="admin">admin</option>
                </select>
              </td>
              <td>
                <span
                  class="ee-status-text"
                  :class="u.active ? 'ee-status-active' : 'ee-status-inactive'"
                >
                  {{ u.active ? 'ACTIVE' : 'DEACTIVATED' }}
                </span>
              </td>
              <td class="font-mono-tabular small text-secondary">
                {{ formatDateShort(u.created_at) }}
              </td>
              <td class="text-end">
                <button
                  v-if="u.id !== state.user?.id"
                  type="button"
                  class="btn btn-sm py-1 px-2"
                  :class="u.active ? 'btn-outline-danger' : 'btn-outline-success'"
                  :disabled="busyUserId === u.id"
                  @click="promptToggleStatus(u)"
                >
                  {{ u.active ? 'Deactivate Account' : 'Activate Account' }}
                </button>
                <span v-else class="small text-muted">Current Admin</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <ConfirmModal
      :visible="Boolean(targetStatusUser)"
      :title="targetStatusUser?.active ? 'Deactivate User Account' : 'Reactivate User Account'"
      :message="
        targetStatusUser?.active
          ? `Deactivate ${targetStatusUser?.full_name} (${targetStatusUser?.email})? Any active authentication tokens for this user will be immediately revoked.`
          : `Reactivate ${targetStatusUser?.full_name} (${targetStatusUser?.email}) so they can sign in again?`
      "
      :confirmLabel="targetStatusUser?.active ? 'Deactivate User' : 'Activate User'"
      :danger="Boolean(targetStatusUser?.active)"
      :loading="busyUserId !== null"
      @cancel="targetStatusUser = null"
      @confirm="confirmToggleStatus"
    />
  </DashboardLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import DashboardLayout from '../components/DashboardLayout.vue';
import ConfirmModal from '../components/ConfirmModal.vue';
import { apiClient, extractErrorMessage } from '../api/client';
import { useAuthStore, showToast } from '../stores/auth';

const { state } = useAuthStore();

const users = ref<any[]>([]);
const loading = ref(true);
const errorMessage = ref('');
const searchQuery = ref('');
const roleFilter = ref('all');
const activeFilter = ref('');
const busyUserId = ref<number | null>(null);
const targetStatusUser = ref<any | null>(null);

async function fetchUsers() {
  loading.value = true;
  errorMessage.value = '';
  try {
    const { data } = await apiClient.get('/users', {
      params: {
        search: searchQuery.value,
        role: roleFilter.value,
        active: activeFilter.value,
      },
    });
    users.value = data.users || [];
  } catch (err) {
    errorMessage.value = extractErrorMessage(err, 'Failed to load users.');
  } finally {
    loading.value = false;
  }
}

async function handleRoleChange(user: any, newRole: string) {
  if (newRole === user.primary_role) return;
  busyUserId.value = user.id;
  try {
    const { data } = await apiClient.put(`/users/${user.id}/role`, { role: newRole });
    user.primary_role = data.user.primary_role;
    user.roles = data.user.roles;
    showToast(`Updated role for ${user.full_name} to '${newRole}'.`, 'success');
  } catch (err) {
    showToast(extractErrorMessage(err, 'Failed to update role.'), 'danger');
    await fetchUsers();
  } finally {
    busyUserId.value = null;
  }
}

function promptToggleStatus(user: any) {
  targetStatusUser.value = user;
}

async function confirmToggleStatus() {
  if (!targetStatusUser.value || busyUserId.value !== null) return;
  const u = targetStatusUser.value;
  busyUserId.value = u.id;
  try {
    const { data } = await apiClient.put(`/users/${u.id}/status`, {
      active: !u.active,
    });
    showToast(data.message, 'info');
    targetStatusUser.value = null;
    await fetchUsers();
  } catch (err) {
    showToast(extractErrorMessage(err, 'Could not change user status.'), 'danger');
  } finally {
    busyUserId.value = null;
  }
}

function formatDateShort(iso?: string): string {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

onMounted(fetchUsers);
</script>
