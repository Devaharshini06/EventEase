<template>
  <div
    v-if="visible"
    class="modal d-block"
    tabindex="-1"
    role="dialog"
    aria-modal="true"
    style="background-color: rgba(15, 23, 42, 0.55);"
  >
    <div class="modal-dialog modal-dialog-centered" role="document">
      <div class="modal-content ee-surface border-0 shadow">
        <div class="modal-header border-bottom px-4 py-3">
          <h5 class="modal-title fw-bold mb-0">{{ title }}</h5>
          <button
            type="button"
            class="btn-close"
            aria-label="Close"
            :disabled="loading"
            @click="$emit('cancel')"
          ></button>
        </div>
        <div class="modal-body px-4 py-4">
          <p class="mb-0 text-secondary">{{ message }}</p>
        </div>
        <div class="modal-footer border-top px-4 py-3">
          <button
            type="button"
            class="btn btn-outline-secondary"
            :disabled="loading"
            @click="$emit('cancel')"
          >
            {{ cancelLabel || 'Keep Current State' }}
          </button>
          <button
            type="button"
            class="btn"
            :class="danger ? 'btn-danger' : 'btn-primary'"
            :disabled="loading"
            @click="$emit('confirm')"
          >
            {{ loading ? 'Processing...' : confirmLabel }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  visible: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  cancelLabel?: string;
  danger?: boolean;
  loading?: boolean;
}>();

defineEmits<{
  (e: 'confirm'): void;
  (e: 'cancel'): void;
}>();
</script>
