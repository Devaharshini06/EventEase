import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';
import { useAuthStore, showToast } from '../stores/auth';

import LandingView from '../views/LandingView.vue';
import LoginView from '../views/LoginView.vue';
import RegisterView from '../views/RegisterView.vue';
import EventDiscoveryView from '../views/EventDiscoveryView.vue';
import EventDetailView from '../views/EventDetailView.vue';
import OrganizerDashboardView from '../views/OrganizerDashboardView.vue';
import EventFormView from '../views/EventFormView.vue';
import OrganizerEventsView from '../views/OrganizerEventsView.vue';
import AttendeeDashboardView from '../views/AttendeeDashboardView.vue';
import MyRegistrationsView from '../views/MyRegistrationsView.vue';
import RegistrationDetailView from '../views/RegistrationDetailView.vue';
import OrganizerAttendeesView from '../views/OrganizerAttendeesView.vue';
import AdminDashboardView from '../views/AdminDashboardView.vue';
import AdminUsersView from '../views/AdminUsersView.vue';
import AdminCategoriesView from '../views/AdminCategoriesView.vue';
import ProfileView from '../views/ProfileView.vue';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'landing',
    component: LandingView,
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { guestOnly: true },
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterView,
    meta: { guestOnly: true },
  },
  {
    path: '/events',
    name: 'event-discovery',
    component: EventDiscoveryView,
  },
  {
    path: '/events/:id',
    name: 'event-detail',
    component: EventDetailView,
  },
  {
    path: '/organizer/dashboard',
    name: 'organizer-dashboard',
    component: OrganizerDashboardView,
    meta: { requiresAuth: true, roles: ['organizer', 'admin'] },
  },
  {
    path: '/organizer/events',
    name: 'organizer-events',
    component: OrganizerEventsView,
    meta: { requiresAuth: true, roles: ['organizer', 'admin'] },
  },
  {
    path: '/organizer/events/new',
    name: 'event-create',
    component: EventFormView,
    meta: { requiresAuth: true, roles: ['organizer', 'admin'] },
  },
  {
    path: '/organizer/events/:id/edit',
    name: 'event-edit',
    component: EventFormView,
    meta: { requiresAuth: true, roles: ['organizer', 'admin'] },
  },
  {
    path: '/organizer/events/:id/attendees',
    name: 'organizer-attendees',
    component: OrganizerAttendeesView,
    meta: { requiresAuth: true, roles: ['organizer', 'admin'] },
  },
  {
    path: '/attendee/dashboard',
    name: 'attendee-dashboard',
    component: AttendeeDashboardView,
    meta: { requiresAuth: true },
  },
  {
    path: '/attendee/registrations',
    name: 'my-registrations',
    component: MyRegistrationsView,
    meta: { requiresAuth: true },
  },
  {
    path: '/registrations/:id',
    name: 'registration-detail',
    component: RegistrationDetailView,
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/dashboard',
    name: 'admin-dashboard',
    component: AdminDashboardView,
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/users',
    name: 'admin-users',
    component: AdminUsersView,
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/categories',
    name: 'admin-categories',
    component: AdminCategoriesView,
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/profile',
    name: 'profile',
    component: ProfileView,
    meta: { requiresAuth: true },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

router.beforeEach(async (to, _from, next) => {
  const { state, isAuthenticated, fetchMe, getDefaultDashboardRoute } = useAuthStore();

  if (state.token && !state.user) {
    await fetchMe();
  }

  if (to.meta.requiresAuth && !isAuthenticated.value) {
    showToast('Please sign in to access that workspace.', 'warning');
    return next({ path: '/login', query: { redirect: to.fullPath } });
  }

  if (to.meta.guestOnly && isAuthenticated.value) {
    return next(getDefaultDashboardRoute());
  }

  const requiredRoles = to.meta.roles as string[] | undefined;
  if (requiredRoles && state.user) {
    const hasRole = requiredRoles.some((r) => state.user?.roles?.includes(r));
    if (!hasRole) {
      showToast('Your account role does not have access to that section.', 'danger');
      return next(getDefaultDashboardRoute());
    }
  }

  next();
});
