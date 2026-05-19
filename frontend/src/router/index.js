import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/calendar'
      },
      {
        path: 'calendar',
        name: 'Calendar',
        component: () => import('@/views/Calendar.vue'),
        meta: { title: '会议室日历' }
      },
      {
        path: 'my-bookings',
        name: 'MyBookings',
        component: () => import('@/views/MyBookings.vue'),
        meta: { title: '我的预约' }
      },
      {
        path: 'admin/rooms',
        name: 'AdminRooms',
        component: () => import('@/views/admin/Rooms.vue'),
        meta: { title: '会议室管理', requiresAdmin: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else if (to.meta.requiresAdmin && !userStore.user?.is_admin) {
    next('/')
  } else {
    next()
  }
})

export default router
