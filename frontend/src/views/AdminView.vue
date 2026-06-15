<template>
  <div>
    <LoadingSpinner v-if="loading" />

    <!-- Login Form -->
    <div v-if="!authState.loggedIn" class="admin-box">
      <p class="title">LOGIN</p>
      <div class="box" id="login-box">
        <form @submit.prevent="handleLogin">
          <label class="label">Email</label>
          <input class="input" type="text" v-model="email" placeholder="Email" required />
          <label class="label">Password</label>
          <input class="input" type="password" v-model="password" placeholder="Password" required />
          <div class="form-actions">
            <button class="button" type="submit">Login</button>
            <button class="button secondary" type="button" @click="email = ''; password = ''">Reset</button>
          </div>
        </form>
        <p v-if="msg" class="msg error-msg">{{ msg }}</p>
      </div>
    </div>

    <!-- Admin Panel -->
    <div v-if="authState.loggedIn" class="admin-box">
      <div class="admin-header">
        <p class="title">ADMIN</p>
        <button class="button secondary" @click="handleLogout">Logout</button>
      </div>

      <!-- Tab switcher -->
      <div class="group-type-button" style="margin-bottom: 24px">
        <button class="button" :class="{ active: adminTab === 'main' }" @click="adminTab = 'main'">管理</button>
        <button class="button" :class="{ active: adminTab === 'maintenance' }" @click="adminTab = 'maintenance'">維護工具</button>
      </div>

      <!-- ── 管理 Tab ── -->
      <template v-if="adminTab === 'main'">

        <!-- Default Image -->
        <div class="box">
          <p class="title is-4">DEFAULT IMAGE</p>
          <p class="desc">元素尚未上傳圖片時顯示的預設圖片</p>
          <img v-if="defaultImgData" :src="defaultImgData" class="img-preview" alt="Default" />
          <p v-else class="placeholder-text">尚未設定</p>
          <form @submit.prevent="handleUpdateDefaultImg">
            <input class="input" type="file" accept=".jpg" ref="defaultImgInput" required />
            <button class="button" type="submit" :disabled="defaultImgSaving">
              {{ defaultImgSaving ? 'Uploading…' : 'Upload' }}
            </button>
          </form>
        </div>

        <!-- Update Story -->
        <div class="box">
          <p class="title is-4">UPDATE STORY</p>
          <form @submit.prevent="handleUpdateStory">
            <label class="label">Element</label>
            <select v-model="selectedSymbol" class="select" @change="onSymbolChange">
              <option v-for="el in elements" :key="el" :value="el">{{ el }}</option>
            </select>

            <div v-if="selectedSymbol" class="current-img-wrap">
              <img
                :src="currentElementImgSrc"
                class="img-preview"
                alt=""
                @error="e => e.target.style.display='none'"
              />
            </div>

            <label class="label">Story</label>
            <textarea
              class="textarea"
              v-model="storyText"
              rows="6"
              placeholder="Write the story…"
            ></textarea>

            <label class="label">Image (.jpg)</label>
            <input class="input" type="file" accept=".jpg" ref="imageInput" />

            <button class="button" type="submit" :disabled="loading">Submit</button>
          </form>
        </div>

      </template>

      <!-- ── 維護工具 Tab ── -->
      <template v-if="adminTab === 'maintenance'">

        <div class="box maintenance-box">
          <div class="maintenance-item">
            <div class="maintenance-info">
              <p class="maintenance-title">Create DB</p>
              <p class="desc">確認 Firestore 資料表是否存在（Firebase 模式下無實際作用，可忽略）</p>
            </div>
            <button class="button" @click="handleCreateDb">執行</button>
          </div>

          <div class="maintenance-item">
            <div class="maintenance-info">
              <p class="maintenance-title">Update DB</p>
              <p class="desc">將週期表基礎資料（118 個元素屬性）上傳至 Firebase Realtime DB。<br>若資料已存在則略過，初始佈署後執行一次即可。</p>
            </div>
            <button class="button" @click="handleUpdateDb">執行</button>
          </div>

          <div class="maintenance-item">
            <div class="maintenance-info">
              <p class="maintenance-title">Backfill img_data</p>
              <p class="desc">掃描所有元素，將只有 Firebase Storage URL（img）但沒有 base64（img_data）的圖片補齊。<br>用於批次補全舊資料，正常情況下上傳圖片時已自動處理。</p>
            </div>
            <button class="button" @click="handleBackfill">執行</button>
          </div>

          <p v-if="adminMsg" class="msg" :class="adminMsgType">{{ adminMsg }}</p>
        </div>

      </template>
    </div>
  </div>
</template>

<script>
import { createDb, updateDb, getStoryData, updateStory, backfillImgData, getDefaultImgInfo, updateDefaultImg } from '../api'
import { authState, login, logout } from '../store/auth'
import { showToast } from '../store/toast'
import LoadingSpinner from '../components/LoadingSpinner.vue'

export default {
  components: { LoadingSpinner },
  data() {
    return {
      authState,
      adminTab: 'main',
      loading: false,
      email: '',
      password: '',
      msg: '',
      adminMsg: '',
      adminMsgType: '',
      elements: [],
      storyDatas: {},
      imageDatas: {},
      selectedSymbol: '',
      storyText: '',
      defaultImgData: '',
      defaultImgSaving: false
    }
  },
  computed: {
    currentElementImgSrc() {
      if (!this.selectedSymbol) return ''
      return (import.meta.env.VITE_API_URL || '/api') + '/elements/' + this.selectedSymbol + '/img'
    }
  },
  async mounted() {
    if (this.authState.loggedIn) {
      await Promise.all([this.loadStoryData(), this.loadDefaultImg()])
    }
  },
  methods: {
    async handleLogin() {
      this.loading = true
      this.msg = ''
      try {
        const result = await login(this.email, this.password)
        if (result.ok) {
          await Promise.all([this.loadStoryData(), this.loadDefaultImg()])
        } else {
          this.msg = result.message || 'Login failed'
        }
      } catch (e) {
        this.msg = e.response?.data?.message || 'Login failed'
      } finally {
        this.loading = false
      }
    },
    async handleLogout() {
      this.loading = true
      try {
        await logout()
      } catch (e) {
        console.error('Logout failed:', e)
      } finally {
        this.loading = false
      }
    },
    async handleCreateDb() {
      this.loading = true
      this.adminMsg = ''
      try {
        const res = await createDb()
        this.adminMsg = res.data.message
        this.adminMsgType = 'success-msg'
      } catch (e) {
        this.adminMsg = e.response?.data?.message || 'Error!'
        this.adminMsgType = 'error-msg'
      } finally {
        this.loading = false
      }
    },
    async handleBackfill() {
      this.loading = true
      this.adminMsg = ''
      try {
        const res = await backfillImgData()
        this.adminMsg = res.data.message
        this.adminMsgType = 'success-msg'
      } catch (e) {
        this.adminMsg = e.response?.data?.message || 'Error!'
        this.adminMsgType = 'error-msg'
      } finally {
        this.loading = false
      }
    },
    async handleUpdateDb() {
      this.loading = true
      this.adminMsg = ''
      try {
        const res = await updateDb()
        this.adminMsg = res.data.message
        this.adminMsgType = 'success-msg'
      } catch (e) {
        this.adminMsg = e.response?.data?.message || 'Error!'
        this.adminMsgType = 'error-msg'
      } finally {
        this.loading = false
      }
    },
    async loadDefaultImg() {
      try {
        const res = await getDefaultImgInfo()
        this.defaultImgData = res.data.img_data || ''
      } catch (e) {
        console.error('Failed to load default image:', e)
      }
    },
    async handleUpdateDefaultImg() {
      const imageFile = this.$refs.defaultImgInput?.files[0]
      if (!imageFile) return
      const formData = new FormData()
      formData.append('image', imageFile)
      this.defaultImgSaving = true
      try {
        const res = await updateDefaultImg(formData)
        showToast(res.data.message, 'success')
        await this.loadDefaultImg()
        this.$refs.defaultImgInput.value = ''
      } catch (e) {
        showToast(e.response?.data?.message || 'Upload failed', 'error')
      } finally {
        this.defaultImgSaving = false
      }
    },
    async loadStoryData() {
      try {
        const res = await getStoryData()
        this.elements = res.data.elements
        this.storyDatas = res.data.storyDatas
        this.imageDatas = res.data.imageDatas
        if (this.elements.length > 0) {
          this.selectedSymbol = this.elements[0]
          this.storyText = this.storyDatas[this.selectedSymbol] || ''
        }
      } catch (e) {
        console.error('Failed to load story data:', e)
      }
    },
    onSymbolChange() {
      this.storyText = this.storyDatas[this.selectedSymbol] || ''
    },
    async handleUpdateStory() {
      const formData = new FormData()
      formData.append('symbol', this.selectedSymbol)
      formData.append('stroy', this.storyText)
      const imageFile = this.$refs.imageInput?.files[0]
      if (imageFile) formData.append('image', imageFile)
      this.loading = true
      try {
        const res = await updateStory(formData)
        showToast(res.data.message || 'Saved!', 'success')
        this.storyDatas[this.selectedSymbol] = this.storyText
        if (this.$refs.imageInput) this.$refs.imageInput.value = ''
      } catch (e) {
        showToast(e.response?.data?.message || 'Save failed', 'error')
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.admin-box {
  text-align: center;
  padding: 20px;
  max-width: 720px;
  margin: 0 auto;
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 4px;
}

.box {
  background: rgba(20, 5, 35, 0.5);
  border: 1px solid rgba(228, 251, 255, 0.1);
  border-radius: 8px;
  padding: 24px 28px;
  margin-bottom: 20px;
  text-align: left;
}

.form-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 12px;
}

.desc {
  font-size: 13px;
  opacity: 0.55;
  margin: 2px 0 14px;
  line-height: 1.5;
}

.placeholder-text {
  font-size: 13px;
  opacity: 0.4;
  margin: 8px 0;
}

.img-preview {
  max-width: 160px;
  max-height: 160px;
  border-radius: 6px;
  border: 1px solid rgba(228, 251, 255, 0.15);
  display: block;
  margin: 10px 0;
}

.current-img-wrap {
  margin: 8px 0;
}

.textarea {
  width: 100%;
  min-height: 120px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(228,251,255,0.15);
  border-radius: 6px;
  color: rgba(228,251,255,0.9);
  padding: 8px 10px;
  font-size: 14px;
  resize: vertical;
  box-sizing: border-box;
  display: block;
  margin: 4px 0 10px;
}

.maintenance-box {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.maintenance-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 16px 0;
  border-bottom: 1px solid rgba(228, 251, 255, 0.07);
}

.maintenance-item:last-of-type {
  border-bottom: none;
}

.maintenance-info {
  flex: 1;
  text-align: left;
}

.maintenance-title {
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 4px;
}

.msg {
  margin-top: 12px;
  font-size: 13px;
}

.success-msg { color: #6ee76e; }
.error-msg { color: #ff6b6b; }

input.input,
select.select {
  display: block;
  width: 100%;
  margin: 4px 0 10px;
  box-sizing: border-box;
}

button.button {
  margin: 4px 2px;
}

button.secondary {
  opacity: 0.6;
}

button.button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
