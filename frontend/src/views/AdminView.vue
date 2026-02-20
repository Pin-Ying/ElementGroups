<template>
  <div>
    <!-- Login Form -->
    <div v-if="!loggedIn" class="admin-box">
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
      <br />
      <router-link class="button" to="/">Go Back To Index</router-link>
    </div>

    <!-- Admin Panel -->
    <div v-else class="admin-box">
      <p class="title">ADMIN</p>
      <div style="margin-bottom: 20px">
        <router-link class="button" to="/">Back To Index</router-link>
        <button class="button" @click="handleCreateDb">Create db</button>
        <button class="button" @click="handleUpdateDb">Update db</button>
        <button class="button" @click="handleLogout">Log out</button>
      </div>
      <p v-if="adminMsg" class="label">{{ adminMsg }}</p>

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
        <p class="label">{{ storyMsg }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { login, logout, createDb, updateDb, getStoryData, updateStory } from '../api'

export default {
  data() {
    return {
      loggedIn: false,
      email: '',
      password: '',
      msg: '',
      adminMsg: '',
      storyMsg: '',
      elements: [],
      storyDatas: {},
      imageDatas: {},
      selectedSymbol: '',
      storyText: ''
    }
  },
  methods: {
    async handleLogin() {
      try {
        const res = await login(this.email, this.password)
        if (res.data.result === 'success') {
          this.loggedIn = true
          this.msg = ''
          await this.loadStoryData()
        }
      } catch (e) {
        this.msg = e.response?.data?.message || 'Login failed'
      }
    },
    async handleLogout() {
      try {
        await logout()
        this.loggedIn = false
      } catch (e) {
        console.error('Logout failed:', e)
      }
    },
    async handleCreateDb() {
      try {
        const res = await createDb()
        this.adminMsg = res.data.message
      } catch (e) {
        this.adminMsg = e.response?.data?.message || 'Error!'
      }
    },
    async handleUpdateDb() {
      try {
        const res = await updateDb()
        this.adminMsg = res.data.message
      } catch (e) {
        this.adminMsg = e.response?.data?.message || 'Error!'
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

      try {
        const res = await updateStory(formData)
        this.storyMsg = res.data.message
        this.storyDatas[this.selectedSymbol] = this.storyText
      } catch (e) {
        this.storyMsg = e.response?.data?.message || 'Error!'
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

.box {
  display: inline-block;
  width: 60%;
}

input,
button,
select {
  margin: 5px auto;
}
</style>
