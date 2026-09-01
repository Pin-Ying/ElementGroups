<template>
  <div class="box maintenance-box">
    <div class="maintenance-item">
      <div class="maintenance-info">
        <p class="maintenance-title">登入帳號</p>
        <p class="desc">
          列出這個 Firebase 專案裡所有能登入的帳號。看得到每個帳號有哪些登入方式
          （providers）與 email 是否已驗證。<br>
          <strong>沒有 password 就代表那個帳號不能用帳密登入</strong>——Firebase 會在
          同一個 email 的 Google 帳號登入時，移除未驗證的密碼憑證。把 email 標記為
          已驗證之後就不會再發生。
        </p>
      </div>
      <button class="button" :disabled="authUsersLoading" @click="loadAuthUsers">
        {{ authUsersLoading ? '載入中…' : '載入' }}
      </button>
    </div>

    <div v-if="authUsers.length" class="auth-users">
      <p v-if="!authAllowlistConfigured" class="msg error-msg">
        尚未設定 ADMIN_ACCOUNTS，目前每一個帳號都能進後台。
      </p>
      <div v-for="u in authUsers" :key="u.uid" class="auth-user">
        <div class="auth-user-main">
          <span class="auth-user-email">{{ u.email || '（無 email）' }}</span>
          <span class="auth-user-tags">
            <i v-for="p in u.providers" :key="p" class="auth-tag">{{ providerLabel(p) }}</i>
            <i v-if="!u.emailVerified" class="auth-tag auth-tag--warn">email 未驗證</i>
            <i v-if="u.disabled" class="auth-tag auth-tag--warn">已停用</i>
            <i v-if="!u.allowed" class="auth-tag auth-tag--warn">不可進後台</i>
          </span>
          <span class="auth-user-uid">{{ u.uid }}</span>
        </div>
        <button
          v-if="!u.emailVerified && u.allowed"
          class="button secondary btn-sm"
          :disabled="verifyingUid === u.uid"
          @click="handleVerifyEmail(u)"
        >{{ verifyingUid === u.uid ? '處理中…' : '標記 email 已驗證' }}</button>
      </div>
    </div>

    <div class="maintenance-item">
      <div class="maintenance-info">
        <p class="maintenance-title">Create DB</p>
        <p class="desc">確認 Firestore 資料表是否存在（Firebase 模式下無實際作用，可忽略）</p>
      </div>
      <button class="button" @click="run(createDb)">執行</button>
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
      <button class="button" @click="run(backfillImgData)">執行</button>
    </div>

    <div class="maintenance-item">
      <div class="maintenance-info">
        <p class="maintenance-title">Rebuild Completion</p>
        <p class="desc">重新掃描所有元素，更新首頁用來標示「已上傳圖片／已寫故事」的摘要資料。<br>正常情況下儲存故事時已自動同步，只有直接從 Firebase 後台改過資料才需要執行。</p>
      </div>
      <button class="button" @click="run(rebuildCompletion)">執行</button>
    </div>

    <div class="maintenance-item">
      <div class="maintenance-info">
        <p class="maintenance-title">Apply Watermark</p>
        <p class="desc">
          把資料庫裡既有的圖片全部套上浮水印，同時備份原圖。<br>
          開啟浮水印只影響之後上傳的圖片，原本就在的要靠這個補；同一張不會被套第二次。
          補過之後，往後在「浮水印」分頁改簽名或強度，儲存時就會自動用原圖重印。
          <br>簽名與強度在「◈ 浮水印」分頁設定。
        </p>
      </div>
      <button class="button" :disabled="!!watermarkJob" @click="handleApplyWatermark">
        {{ watermarkJob ? '執行中…' : '執行' }}
      </button>
    </div>

    <p v-if="watermarkJob" class="desc">
      {{ watermarkJob.done }} / {{ watermarkJob.total }} 個位置，已處理 {{ watermarkJob.images }} 張
    </p>
    <ul v-if="watermarkFailures.length" class="desc">
      <li v-for="f in watermarkFailures" :key="f.path">失敗：{{ f.path }}－{{ f.reason }}</li>
    </ul>

    <p v-if="msg" class="msg" :class="msgType">{{ msg }}</p>
  </div>
</template>

<script>
// 後台的「維護工具」分頁（issue #29 的第二個拆分對象）。
//
// 這裡的東西共同點是「按一下、跑一個批次作業、回報結果」，所以四個 DB
// 相關的按鈕收斂成同一個 run()——原本 handleCreateDb／handleBackfill／
// handleRebuildCompletion 三個 method 的內容一模一樣，只差呼叫哪支 API。
// handleUpdateDb 多一個「完成後要通知殼重載故事資料」的步驟，所以獨立。
//
// ## 與殼的介面
//
// loading  全域的 LoadingSpinner 由 AdminView 管，這裡用事件請求它開關。
//          維護作業會改動資料，蓋住整頁避免使用者在跑到一半時亂點是刻意的。
// db-updated  Update DB 完成後要讓「元素故事」分頁重新載入，否則它的元素
//          清單還是舊的。等 story 分頁也拆出去、自己負責載入之後，這個
//          事件就可以拿掉。
//
// 訊息狀態（msg／msgType）留在這裡而不是提升到殼：原本 AdminView 的
// setSection() 會在切換分頁時清掉 adminMsg，現在分頁用 v-if 渲染，切走
// 就 unmount，狀態自然消失，那行手動清除也跟著不需要了。
import {
  createDb, updateDb, backfillImgData, rebuildCompletion,
  getAuthUsers, verifyAuthUserEmail
} from '../../api'
import { showToast } from '../../store/toast'
import { runWatermarkJob } from '../../utils/watermarkJobs'

export default {
  emits: ['loading', 'db-updated'],
  data() {
    return {
      msg: '',
      msgType: '',
      authUsers: [],
      authUsersLoading: false,
      authAllowlistConfigured: true,
      verifyingUid: '',
      watermarkJob: null,
      watermarkFailures: []
    }
  },
  methods: {
    // template 直接把 api 函式傳進 run()，所以要讓它們拿得到
    createDb,
    backfillImgData,
    rebuildCompletion,

    /** 跑一個沒有後續動作的維護作業，統一處理 loading 與結果訊息。 */
    async run(apiCall) {
      this.$emit('loading', true)
      this.msg = ''
      try {
        const res = await apiCall()
        this.msg = res.data.message
        this.msgType = 'success-msg'
      } catch (e) {
        this.msg = e.response?.data?.message || 'Error!'
        this.msgType = 'error-msg'
      } finally {
        this.$emit('loading', false)
      }
    },

    async handleUpdateDb() {
      this.$emit('loading', true)
      this.msg = ''
      try {
        const res = await updateDb()
        this.msg = res.data.message
        this.msgType = 'success-msg'
        // 週期表換了一批資料，元素故事分頁的清單要跟著更新
        this.$emit('db-updated')
      } catch (e) {
        this.msg = e.response?.data?.message || 'Error!'
        this.msgType = 'error-msg'
      } finally {
        this.$emit('loading', false)
      }
    },

    /**
     * 把既有的圖片全部套上浮水印。實際的分批邏輯在 utils/watermarkJobs.js，
     * 與「浮水印」分頁那顆按鈕同一份——這裡只負責顯示進度。
     */
    async handleApplyWatermark() {
      this.msg = ''
      this.watermarkFailures = []
      try {
        const result = await runWatermarkJob('backfill', progress => {
          this.watermarkJob = { ...progress }
        })
        this.msg = result.text
        this.msgType = result.failed ? 'error-msg' : 'success-msg'
        this.watermarkFailures = result.failures
        showToast(result.text, result.failed ? 'error' : 'success')
      } catch (e) {
        this.msg = e.response?.data?.message || 'Error!'
        this.msgType = 'error-msg'
      } finally {
        this.watermarkJob = null
      }
    },

    providerLabel(id) {
      return { 'password': '密碼', 'google.com': 'Google' }[id] || id
    },

    async loadAuthUsers() {
      this.authUsersLoading = true
      try {
        const res = await getAuthUsers()
        this.authUsers = res.data.users || []
        this.authAllowlistConfigured = res.data.allowlistConfigured !== false
      } catch (e) {
        showToast(e.response?.data?.message || '載入帳號失敗', 'error')
      } finally {
        this.authUsersLoading = false
      }
    },

    async handleVerifyEmail(user) {
      this.verifyingUid = user.uid
      try {
        const res = await verifyAuthUserEmail(user.uid)
        showToast(res.data.message || '已標記', res.data.result === 'success' ? 'success' : 'error')
        // 重新載入而不是就地改狀態：providers 也可能一起變了
        await this.loadAuthUsers()
      } catch (e) {
        showToast(e.response?.data?.message || '操作失敗', 'error')
      } finally {
        this.verifyingUid = ''
      }
    }
  }
}
</script>

<style scoped>
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

/* 登入帳號清單 */
.auth-users {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 4px 0 18px;
  padding: 12px;
  border: 1px solid rgba(228, 251, 255, 0.14);
  border-radius: 8px;
  background: rgba(20, 5, 35, 0.4);
}

.auth-user {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.auth-user-main {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  min-width: 0;
}

.auth-user-email {
  font-size: 13px;
  color: rgba(228, 251, 255, 0.9);
}

.auth-user-uid {
  font-size: 11px;
  color: rgba(228, 251, 255, 0.35);
  word-break: break-all;
}

.auth-user-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.auth-tag {
  font-size: 10px;
  font-style: normal;
  padding: 1px 7px;
  border-radius: 999px;
  border: 1px solid rgba(228, 251, 255, 0.25);
  color: rgba(228, 251, 255, 0.6);
}

.auth-tag--warn {
  border-color: rgba(255, 196, 107, 0.45);
  color: #ffc46b;
}
</style>
