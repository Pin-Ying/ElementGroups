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
          <br />
          <button class="button" type="submit" style="margin-top:10px">Login</button>
          <button class="button" type="button" @click="email = ''; password = ''" style="margin-top:10px">Reset</button>
        </form>
        <p class="label" style="color: red">{{ msg }}</p>
      </div>
    </div>

    <!-- Admin Panel -->
    <div v-if="authState.loggedIn" class="admin-box">
      <p class="title">ADMIN</p>
      <div style="margin-bottom: 20px">
        <button class="button" @click="handleCreateDb">Create db</button>
        <button class="button" @click="handleUpdateDb">Update db</button>
        <button class="button" @click="handleBackfill">Backfill img_data</button>
      </div>
      <p v-if="adminMsg" class="label" :class="adminMsgType">{{ adminMsg }}</p>

      <!-- Default Image -->
      <div class="box">
        <p class="title is-4">DEFAULT IMAGE</p>
        <p class="label" style="opacity:0.6;font-size:13px">顯示在還沒有圖片的元素上</p>
        <img v-if="defaultImgData" :src="defaultImgData" class="default-img-preview" alt="Default" />
        <p v-else class="label" style="opacity:0.5">尚未設定</p>
        <form @submit.prevent="handleUpdateDefaultImg" style="margin-top:12px">
          <input class="input" type="file" accept=".jpg" ref="defaultImgInput" required />
          <button class="button" type="submit" style="margin-top:10px">{{ defaultImgSaving ? 'Uploading...' : 'Upload' }}</button>
        </form>
        <p v-if="defaultImgMsg" class="label" :class="defaultImgMsgType">{{ defaultImgMsg }}</p>
      </div>

      <!-- Update Story Form -->
      <div class="box">
        <p class="title is-4">UPDATE STORY</p>
        <form @submit.prevent="handleUpdateStory">
          <label class="label">Element Symbol</label>
          <select v-model="selectedSymbol" class="select" @change="onSymbolChange">
            <option v-for="el in elements" :key="el" :value="el">{{ el }}</option>
          </select>
          <label class="label">Story</label>
          <input class="textarea" type="text" v-model="storyText" placeholder="Write the story" />
          <label class="label">Image</label>
          <input class="input" type="file" accept=".jpg" ref="imageInput" />
          <button class="button" type="submit" style="margin-top:10px">Submit</button>
        </form>
        <p class="label" :class="storyMsgType">{{ storyMsg }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { createDb, updateDb, getStoryData, updateStory, backfillImgData, getDefaultImgInfo, updateDefaultImg } from '../api'
import { authState, login, logout } from '../store/auth'
import LoadingSpinner from '../components/LoadingSpinner.vue'

export default {
  components: { LoadingSpinner },
  data() {
    return {
      authState,
      loading: false,
      email: '',
      password: '',
      msg: '',
      adminMsg: '',
      adminMsgType: '',
      storyMsg: '',
      storyMsgType: '',
      elements: [],
      storyDatas: {},
      imageDatas: {},
      selectedSymbol: '',
      storyText: '',
      defaultImgData: '',
      defaultImgMsg: '',
      defaultImgMsgType: '',
      defaultImgSaving: false
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
      try {
        const result = await login(this.email, this.password)
        if (result.ok) {
          this.msg = ''
          await this.loadStoryData()
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
      this.defaultImgMsg = ''
      try {
        const res = await updateDefaultImg(formData)
        this.defaultImgMsg = res.data.message
        this.defaultImgMsgType = 'success-msg'
        await this.loadDefaultImg()
      } catch (e) {
        this.defaultImgMsg = e.response?.data?.message || 'Upload failed'
        this.defaultImgMsgType = 'error-msg'
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
      this.storyMsg = ''
      try {
        const res = await updateStory(formData)
        this.storyMsg = res.data.message
        this.storyMsgType = 'success-msg'
        this.storyDatas[this.selectedSymbol] = this.storyText
      } catch (e) {
        this.storyMsg = e.response?.data?.message || 'Error!'
        this.storyMsgType = 'error-msg'
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
}

.default-img-preview {
  max-width: 200px;
  max-height: 200px;
  border-radius: 6px;
  border: 1px solid rgba(228, 251, 255, 0.2);
  margin-top: 8px;
  display: block;
  margin-left: auto;
  margin-right: auto;
}

.box {
  display: inline-block;
  width: 60%;
  background: rgba(20, 5, 35, 0.5);
  border: 1px solid rgba(228, 251, 255, 0.1);
  border-radius: 8px;
  padding: 20px;
}

input,
button,
select {
  margin: 5px auto;
}

.success-msg {
  color: #6ee76e;
}

.error-msg {
  color: #ff6b6b;
}
</style>
