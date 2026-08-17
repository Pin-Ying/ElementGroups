import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import StoryView from '../views/StoryView.vue'
import AdminView from '../views/AdminView.vue'
import LinksView from '../views/LinksView.vue'
import GuideView from '../views/GuideView.vue'
import PageView from '../views/PageView.vue'
import MoleculesView from '../views/MoleculesView.vue'
import ParticlesView from '../views/ParticlesView.vue'
import MoleculeView from '../views/MoleculeView.vue'
import WatermarkView from '../views/WatermarkView.vue'

const routes = [
  { path: '/', name: 'Home', component: HomeView },
  { path: '/stroy/:symbol', name: 'Story', component: StoryView, props: true },
  { path: '/admin', name: 'Admin', component: AdminView },
  { path: '/links', name: 'Links', component: LinksView },
  { path: '/guide', name: 'Guide', component: GuideView },
  { path: '/p/:slug', name: 'Page', component: PageView, props: true },
  {
    path: '/molecules',
    name: 'Molecules',
    component: MoleculesView,
    // 元素頁的「查看更多」會帶 ?element=Fe 篩選
    props: route => ({ element: route.query.element || '' })
  },
  { path: '/molecule/:slug', name: 'Molecule', component: MoleculeView, props: true },
  { path: '/particles', name: 'Particles', component: ParticlesView },
  { path: '/watermark', name: 'Watermark', component: WatermarkView }
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
