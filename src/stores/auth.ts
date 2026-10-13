import { reactive, computed } from 'vue';
import {
  apiClient,
  getStoredToken,
  getStoredUser,
  setStoredAuth,
  clearStoredAuth,
  registerUnauthorizedHandler,
} from '../api/client';

export interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  organization: string;
  phone: string;
  bio: string;
  active: boolean;
  roles: string[];
  primary_role: 'admin' | 'organizer' | 'attendee';
  created_at: string;
  unread_notifications_count?: number;
}

export interface NotificationItem {
  id: number;
  recipient_id: number;
  title: string;
  content: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
}

export interface ToastMessage {
  id: number;
  type: 'success' | 'danger' | 'warning' | 'info';
  text: string;
}

const state = reactive<{
  token: string | null;
  user: UserProfile | null;
  notifications: NotificationItem[];
  unreadCount: number;
  loadingAuth: boolean;
  toasts: ToastMessage[];
}>({
  token: getStoredToken(),
  user: getStoredUser(),
  notifications: [],
  unreadCount: 0,
  loadingAuth: false,
  toasts: [],
});

let toastCounter = 1;

export function showToast(text: string, type: 'success' | 'danger' | 'warning' | 'info' = 'info') {
  const id = toastCounter++;
  state.toasts.push({ id, type, text });
  setTimeout(() => {
    dismissToast(id);
  }, 4500);
}

export function dismissToast(id: number) {
  const idx = state.toasts.findIndex((t) => t.id === id);
  if (idx !== -1) {
    state.toasts.splice(idx, 1);
  }
}

registerUnauthorizedHandler(() => {
  state.token = null;
  state.user = null;
  state.notifications = [];
  state.unreadCount = 0;
});

export function useAuthStore() {
  const isAuthenticated = computed(() => Boolean(state.token && state.user));
  const isAdmin = computed(() => Boolean(state.user?.roles?.includes('admin')));
  const isOrganizer = computed(
    () => Boolean(state.user?.roles?.includes('organizer') || state.user?.roles?.includes('admin'))
  );
  const isAttendee = computed(() => Boolean(state.user));

  async function login(email: string, password: string) {
    state.loadingAuth = true;
    try {
      const { data } = await apiClient.post('/auth/login', { email, password });
      state.token = data.token;
      state.user = data.user;
      setStoredAuth(data.token, data.user);
      await fetchNotifications();
      return data.user as UserProfile;
    } finally {
      state.loadingAuth = false;
    }
  }

  async function register(payload: {
    email: string;
    password: string;
    full_name: string;
    organization?: string;
    phone?: string;
    role: 'attendee' | 'organizer';
  }) {
    state.loadingAuth = true;
    try {
      const { data } = await apiClient.post('/auth/register', payload);
      state.token = data.token;
      state.user = data.user;
      setStoredAuth(data.token, data.user);
      await fetchNotifications();
      return data.user as UserProfile;
    } finally {
      state.loadingAuth = false;
    }
  }

  async function fetchMe() {
    if (!state.token) return null;
    try {
      const { data } = await apiClient.get('/auth/me');
      state.user = data.user;
      state.unreadCount = data.user.unread_notifications_count || 0;
      setStoredAuth(state.token, data.user);
      return data.user as UserProfile;
    } catch {
      state.token = null;
      state.user = null;
      clearStoredAuth();
      return null;
    }
  }

  async function updateProfile(payload: {
    full_name?: string;
    organization?: string;
    phone?: string;
    bio?: string;
    current_password?: string;
    new_password?: string;
  }) {
    const { data } = await apiClient.put('/auth/profile', payload);
    state.user = data.user;
    if (state.token) {
      setStoredAuth(state.token, data.user);
    }
    return data.user as UserProfile;
  }

  async function logout() {
    try {
      if (state.token) {
        await apiClient.post('/auth/logout');
      }
    } catch {
      // Ignore logout network error if token already expired
    } finally {
      state.token = null;
      state.user = null;
      state.notifications = [];
      state.unreadCount = 0;
      clearStoredAuth();
    }
  }

  async function fetchNotifications() {
    if (!state.token) return;
    try {
      const { data } = await apiClient.get('/auth/notifications');
      state.notifications = data.notifications || [];
      state.unreadCount = data.unread_count || 0;
    } catch {
      // Ignore silent notification polling error
    }
  }

  async function markNotificationRead(id: number) {
    try {
      await apiClient.put(`/auth/notifications/${id}/read`);
      const target = state.notifications.find((n) => n.id === id);
      if (target && !target.is_read) {
        target.is_read = true;
        state.unreadCount = Math.max(0, state.unreadCount - 1);
      }
    } catch {
      // Ignore error
    }
  }

  function getDefaultDashboardRoute(): string {
    if (!state.user) return '/login';
    if (state.user.roles.includes('admin')) return '/admin/dashboard';
    if (state.user.roles.includes('organizer')) return '/organizer/dashboard';
    return '/attendee/dashboard';
  }

  return {
    state,
    isAuthenticated,
    isAdmin,
    isOrganizer,
    isAttendee,
    login,
    register,
    fetchMe,
    updateProfile,
    logout,
    fetchNotifications,
    markNotificationRead,
    getDefaultDashboardRoute,
    showToast,
    dismissToast,
  };
}
