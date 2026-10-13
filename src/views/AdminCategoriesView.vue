<template>
  <DashboardLayout pageTitle="Category Registry Management">
    <div class="row g-4">
      <!-- Create / Edit Category Form -->
      <div class="col-lg-4">
        <div class="ee-surface p-4">
          <h2 class="h5 fw-bold mb-1">
            {{ editingCategory ? 'Update Category' : 'Create New Category' }}
          </h2>
          <p class="small text-secondary mb-3">
            Categories classify events across discovery filters and analytics.
          </p>

          <div v-if="formError" class="alert alert-danger py-2 small">
            {{ formError }}
          </div>

          <form @submit.prevent="handleSaveCategory" novalidate>
            <div class="mb-3">
              <label for="cat-name" class="form-label small fw-semibold">Category Name *</label>
              <input
                id="cat-name"
                v-model.trim="form.name"
                type="text"
                class="form-control"
                placeholder="e.g., Cloud & DevOps"
                required
                :disabled="saving"
              />
            </div>

            <div class="mb-3">
              <label for="cat-desc" class="form-label small fw-semibold">Description</label>
              <textarea
                id="cat-desc"
                v-model.trim="form.description"
                rows="3"
                class="form-control"
                placeholder="Concise description of events in this category..."
                :disabled="saving"
              ></textarea>
            </div>

            <div class="form-check mb-4">
              <input
                id="cat-active"
                v-model="form.is_active"
                type="checkbox"
                class="form-check-input"
                :disabled="saving"
              />
              <label for="cat-active" class="form-check-label small fw-semibold">
                Active in public discovery filters
              </label>
            </div>

            <div class="d-flex gap-2">
              <button type="submit" class="btn btn-primary flex-grow-1" :disabled="saving">
                {{ saving ? 'Saving...' : editingCategory ? 'Save Changes' : 'Create Category' }}
              </button>
              <button
                v-if="editingCategory"
                type="button"
                class="btn btn-outline-secondary"
                :disabled="saving"
                @click="resetForm"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Categories Table -->
      <div class="col-lg-8">
        <div class="ee-surface">
          <div class="p-3 p-md-4 border-bottom d-flex align-items-center justify-content-between">
            <div>
              <h2 class="h5 fw-bold mb-0">Platform Event Categories ({{ categories.length }})</h2>
              <p class="small text-secondary mb-0">
                Categories with associated events are protected from accidental deletion.
              </p>
            </div>
          </div>

          <div v-if="loading" class="p-5 text-center text-secondary">
            Loading category registry...
          </div>

          <div v-else class="table-responsive">
            <table class="table ee-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Description</th>
                  <th>Status</th>
                  <th class="text-end">Events</th>
                  <th class="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="cat in categories" :key="cat.id">
                  <td class="fw-semibold">{{ cat.name }}</td>
                  <td class="small text-secondary">{{ cat.description || '—' }}</td>
                  <td>
                    <span
                      class="ee-status-text"
                      :class="cat.is_active ? 'ee-status-active' : 'ee-status-inactive'"
                    >
                      {{ cat.is_active ? 'ACTIVE' : 'INACTIVE' }}
                    </span>
                  </td>
                  <td class="text-end font-mono-tabular">
                    {{ cat.event_count || 0 }}
                  </td>
                  <td class="text-end">
                    <div class="d-inline-flex gap-2">
                      <button
                        type="button"
                        class="btn btn-outline-secondary btn-sm py-1 px-2"
                        @click="startEdit(cat)"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        class="btn btn-outline-danger btn-sm py-1 px-2"
                        :disabled="(cat.event_count || 0) > 0"
                        :title="(cat.event_count || 0) > 0 ? 'Cannot delete category with existing events' : 'Delete category'"
                        @click="targetDeleteCat = cat"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <ConfirmModal
      :visible="Boolean(targetDeleteCat)"
      title="Delete Event Category"
      :message="`Permanently delete the category '${targetDeleteCat?.name}'?`"
      confirmLabel="Delete Category"
      :danger="true"
      :loading="deleting"
      @cancel="targetDeleteCat = null"
      @confirm="confirmDeleteCategory"
    />
  </DashboardLayout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import DashboardLayout from '../components/DashboardLayout.vue';
import ConfirmModal from '../components/ConfirmModal.vue';
import { apiClient, extractErrorMessage } from '../api/client';
import { showToast } from '../stores/auth';

const categories = ref<any[]>([]);
const loading = ref(true);
const saving = ref(false);
const deleting = ref(false);
const formError = ref('');
const editingCategory = ref<any | null>(null);
const targetDeleteCat = ref<any | null>(null);

const form = reactive({
  name: '',
  description: '',
  is_active: true,
});

async function fetchCategories() {
  loading.value = true;
  try {
    const { data } = await apiClient.get('/categories', {
      params: { include_counts: true },
    });
    categories.value = data.categories || [];
  } catch (err) {
    showToast(extractErrorMessage(err, 'Failed to load categories.'), 'danger');
  } finally {
    loading.value = false;
  }
}

function startEdit(cat: any) {
  editingCategory.value = cat;
  form.name = cat.name;
  form.description = cat.description || '';
  form.is_active = Boolean(cat.is_active);
  formError.value = '';
}

function resetForm() {
  editingCategory.value = null;
  form.name = '';
  form.description = '';
  form.is_active = true;
  formError.value = '';
}

async function handleSaveCategory() {
  if (saving.value) return;
  formError.value = '';
  if (!form.name || form.name.length < 2) {
    formError.value = 'Category name must be at least 2 characters.';
    return;
  }

  saving.value = true;
  try {
    if (editingCategory.value) {
      await apiClient.put(`/categories/${editingCategory.value.id}`, {
        name: form.name,
        description: form.description,
        is_active: form.is_active,
      });
      showToast(`Category '${form.name}' updated.`, 'success');
    } else {
      await apiClient.post('/categories', {
        name: form.name,
        description: form.description,
        is_active: form.is_active,
      });
      showToast(`Category '${form.name}' created.`, 'success');
    }
    resetForm();
    await fetchCategories();
  } catch (err) {
    formError.value = extractErrorMessage(err, 'Could not save category.');
  } finally {
    saving.value = false;
  }
}

async function confirmDeleteCategory() {
  if (!targetDeleteCat.value || deleting.value) return;
  deleting.value = true;
  try {
    await apiClient.delete(`/categories/${targetDeleteCat.value.id}`);
    showToast(`Category '${targetDeleteCat.value.name}' deleted.`, 'info');
    targetDeleteCat.value = null;
    await fetchCategories();
  } catch (err) {
    showToast(extractErrorMessage(err, 'Failed to delete category.'), 'danger');
    targetDeleteCat.value = null;
  } finally {
    deleting.value = false;
  }
}

onMounted(fetchCategories);
</script>
