import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { installImageGuard } from './utils/imageGuard'
import './assets/style.css'
import './assets/forms.css'

const app = createApp(App)
app.use(router)
installImageGuard(router)
app.mount('#app')
