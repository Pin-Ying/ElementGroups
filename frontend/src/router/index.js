import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import StoryView from '../views/StoryView.vue'
import AdminView from '../views/AdminView.vue'
import LinksView from '../views/LinksView.vue'
import GuideView from '../views/GuideView.vue'
import PageView from '../views/PageView.vue'

const routes = [
  { path: '/', name: 'Home', component: HomeView },
  { path: '/stroy/:symbol', name: 'Story', component: StoryView, props: true },
  { path: '/admin', name: 'Admin', component: AdminView },
  { path: '/links', name: 'Links', component: LinksView },
  { path: '/guide', name: 'Guide', component: GuideView },
  { path: '/p/:slug', name: 'Page', component: PageView, props: true }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  // 切換頁面時回到頂端，否則從長頁面點連結會停在中間
  scrollBehavior() {
    return { top: 0 }
  }
})

export default router
