import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import StoryView from '../views/StoryView.vue'
import AdminView from '../views/AdminView.vue'
import LinksView from '../views/LinksView.vue'

const routes = [
  { path: '/', name: 'Home', component: HomeView },
  { path: '/stroy/:symbol', name: 'Story', component: StoryView, props: true },
  { path: '/admin', name: 'Admin', component: AdminView },
  { path: '/links', name: 'Links', component: LinksView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
