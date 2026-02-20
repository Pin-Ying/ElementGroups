import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import StoryView from '../views/StoryView.vue'
import AdminView from '../views/AdminView.vue'

const routes = [
  { path: '/', name: 'Home', component: HomeView },
  { path: '/stroy/:symbol', name: 'Story', component: StoryView, props: true },
  { path: '/admin', name: 'Admin', component: AdminView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
