<template>
  <div>
    <LoadingSpinner v-if="loading" />

    <!-- 圖片裁切：上傳任何圖片後先進這裡 -->
    <ImageCropper
      v-if="cropFile"
      :file="cropFile"
      @done="onCropDone"
      @skip="onCropSkip"
      @cancel="onCropCancel"
    />

    <!-- Login Form -->
    <div v-if="!authState.loggedIn" class="admin-box">
      <p class="title">LOGIN</p>
      <div class="box" id="login-box">
        <p v-if="!loginMethodsLoaded" class="field-hint">載入中…</p>

        <template v-else>
          <!-- Google 是主要方式，放最上面。登入成功後 authState.loggedIn 會變
               true，watch 會接手跑 bootstrap()，這裡不需要自己處理後續 -->
          <div v-if="googleLoginEnabled" class="login-google-row">
            <GoogleLoginButton />
          </div>

          <!-- 帳密登入。兩種方式都能用時收在「使用其他方式登入」後面——這頁是
               站長自己的登入頁，Google 出狀況時要有後路，但平常不該跟主要方式
               並排。只剩帳密可用時直接展開，不必多按一次。

               後端關掉帳密登入時整塊都不畫：真正擋下來的是 auth.login()，這裡
               只是不要留一組送出去必定被拒的輸入框。 -->
          <template v-if="passwordLoginEnabled">
            <button
              v-if="googleLoginEnabled && !showPasswordForm"
              class="alt-login-toggle"
              type="button"
              @click="showPasswordForm = true"
            >使用其他方式登入</button>

            <form v-if="!googleLoginEnabled || showPasswordForm" @submit.prevent="handleLogin">
              <label class="label">Email</label>
              <input class="input" type="text" v-model="email" required />
              <label class="label">Password</label>
              <input class="input" type="password" v-model="password" required />
              <div class="form-actions">
                <button class="button" type="submit">Login</button>
                <button class="button secondary" type="button" @click="email = ''; password = ''">Reset</button>
              </div>
            </form>
          </template>

          <p v-if="!passwordLoginEnabled && !googleLoginEnabled" class="field-hint">
            目前沒有可用的登入方式。請確認後端的 GOOGLE_LOGIN_ENABLED
            與 PASSWORD_LOGIN_ENABLED 設定。
          </p>
        </template>

        <p v-if="msg" class="msg error-msg">{{ msg }}</p>
      </div>
    </div>

    <!-- Admin Panel -->
    <div v-if="authState.loggedIn" class="admin-layout">
      <!-- 側邊導覽：功能區塊變多後改為一次只顯示一項，不必一路往下滑 -->
      <aside class="admin-nav">
        <p class="nav-title">ADMIN</p>
        <nav class="nav-list">
          <button
            v-for="s in SECTIONS"
            :key="s.key"
            class="nav-item"
            type="button"
            :class="{ active: section === s.key }"
            @click="setSection(s.key)"
          >
            <span class="nav-icon">{{ s.icon }}</span>
            <span class="nav-label">{{ s.label }}</span>
          </button>
        </nav>
        <button class="nav-item nav-logout" type="button" @click="handleLogout">
          <span class="nav-icon">→</span>
          <span class="nav-label">登出</span>
        </button>
      </aside>

      <div class="admin-content">
        <p class="content-title">{{ currentSection.label }}</p>

        <!-- Pages -->
        <!-- 頁面管理（issue #20）：系統頁面與自訂頁面併成同一份清單，
             點「編輯」才進表單。原本是三塊不同的東西疊在同一個捲動頁上，
             要改哪裡得先捲到對的位置，才會覺得零散 -->
        <div v-if="section === 'pages'" class="box">
          <!-- ── 清單 ── -->
          <template v-if="pageMode === 'list'">
            <div class="section-head">
              <p class="title is-4">PAGES</p>
              <button class="button" type="button" @click="newPage">＋ 建立新頁面</button>
            </div>
            <p class="desc">
              系統頁面有固定網址，可以改文案但不能刪除；自訂頁面可自由新增、排序與刪除。<br>
              未發布的頁面只有登入後看得到。
            </p>

            <div class="page-table">
              <div class="page-row page-row--head">
                <span>排序</span>
                <span>標題</span>
                <span>路徑</span>
                <span>狀態</span>
                <span>導覽列</span>
                <span>操作</span>
              </div>

              <div v-for="row in pageRows" :key="row.kind + ':' + row.key" class="page-row">
                <span class="page-order">
                  <template v-if="row.kind === 'custom'">
                    <button
                      class="icon-button"
                      type="button"
                      title="上移"
                      :disabled="!row.canUp || pageSaving"
                      @click="movePage(row, -1)"
                    >▲</button>
                    <button
                      class="icon-button"
                      type="button"
                      title="下移"
                      :disabled="!row.canDown || pageSaving"
                      @click="movePage(row, 1)"
                    >▼</button>
                  </template>
                </span>

                <span class="page-title-cell">
                  {{ row.title }}
                  <span v-if="row.system" class="system-tag">系統</span>
                </span>

                <span class="page-path">{{ row.path }}</span>

                <span>
                  <span class="status-tag" :class="row.published ? 'is-live' : 'is-draft'">
                    {{ row.published ? '已發布' : '草稿' }}
                  </span>
                </span>

                <span class="page-nav-cell">{{ row.nav }}</span>

                <span class="page-ops">
                  <button class="button secondary small" type="button" @click="editRow(row)">編輯</button>
                  <button
                    v-if="row.kind === 'custom'"
                    class="icon-button danger"
                    type="button"
                    :title="pendingDeletePage === row.key ? '再按一次確認刪除' : '刪除'"
                    :class="{ confirming: pendingDeletePage === row.key }"
                    @click="deleteRow(row)"
                  >{{ pendingDeletePage === row.key ? '確認' : '✕' }}</button>
                </span>
              </div>
            </div>
          </template>

          <!-- ── 編輯：內建文案 ── -->
          <template v-else-if="editKind === 'meta'">
            <div class="section-head">
              <button class="button secondary" type="button" @click="backToList">← 返回列表</button>
              <p class="title is-4">{{ metaDef ? metaDef.label : '' }}</p>
              <button class="button" type="button" :disabled="metaSaving" @click="handleSaveMeta">
                {{ metaSaving ? 'Saving…' : '儲存文案' }}
              </button>
            </div>
            <p class="desc">
              這頁的版面是固定的，可編輯的是上面的各段文字。<br>
              欄位留空表示使用內建預設值（顯示在灰字提示裡）；部署更新預設文案不會蓋掉你改過的欄位。
            </p>

            <form v-if="metaDef" @submit.prevent="handleSaveMeta">
              <div v-for="f in metaDef.fields" :key="f.name" class="meta-field">
                <label class="label">{{ f.label }}</label>
                <select
                  v-if="f.type === 'select'"
                  class="select"
                  v-model="metaForm[f.name]"
                  :aria-label="f.label"
                >
                  <option v-for="o in f.options" :key="o.key" :value="o.key">{{ o.label }}</option>
                </select>
                <textarea
                  v-else-if="f.multiline"
                  class="textarea"
                  rows="3"
                  v-model="metaForm[f.name]"
                  :placeholder="f.default || '（預設為空）'"
                  :aria-label="f.label"
                ></textarea>
                <input
                  v-else
                  class="input"
                  :type="f.type === 'number' ? 'number' : 'text'"
                  v-model="metaForm[f.name]"
                  :placeholder="f.default || '（預設為空）'"
                  :aria-label="f.label"
                />
              </div>
            </form>
          </template>

          <!-- ── 編輯：Markdown 頁面（自訂頁與內建頁共用） ── -->
          <template v-else>
            <AdminBar :title="pageForm.original_slug || pageForm.slug ? `編輯頁面：${pageForm.title || pageForm.slug}` : '建立新頁面'">
              <template #lead>
                <button class="button secondary" type="button" @click="backToList">← 返回列表</button>
              </template>
              <button class="button secondary" type="button" :disabled="pageSaving" @click="saveAsDraft">存成草稿</button>
              <button class="button" type="button" :disabled="pageSaving" @click="publishPage">
                {{ pageSaving ? 'Saving…' : '發布' }}
              </button>
            </AdminBar>

            <p v-if="editingBuiltinPage" class="desc">
              這是內建頁面，網址固定為 {{ '/' + pageForm.slug }}，也不會出現在導覽列。<br>
              儲存後該頁就改用你編輯的版本；之後部署更新內建模板也不會蓋掉它。
            </p>

            <form class="page-form" @submit.prevent="publishPage">
            <div class="page-form-row">
              <div>
                <label class="label">頁面標題</label>
                <input class="input" type="text" v-model="pageForm.title" />
              </div>
              <div>
                <label class="label">副標題</label>
                <input class="input" type="text" v-model="pageForm.subtitle" aria-label="副標題" />
                <p class="field-hint">顯示在標題底下，留空就不顯示</p>
              </div>
            </div>

            <div class="page-form-row">
              <div v-if="!editingBuiltinPage">
                <label class="label">網址代稱</label>
                <input class="input" type="text" v-model="pageForm.slug" aria-label="網址代稱" />
                <p class="field-hint">網址為 /p/{{ pageForm.slug || '…' }}，只能用小寫英數字與連字號</p>
              </div>
              <div>
                <AiField
                  label="SEO 描述"
                  kind="page-seo"
                  v-model="pageForm.seo_description"
                  :extra="pageSeoAiContext"
                  hint="搜尋結果顯示的那段字，留空會自動取內文開頭"
                />
              </div>
            </div>

            <!-- 導覽位置對內建頁面一樣有意義（/guide、/links 也要能決定
                 放在側欄還是頁尾），不要因為它是內建頁就藏起來 -->
            <div class="page-form-row">
              <div>
                <label class="label">導覽位置</label>
                <select class="select" v-model="pageForm.nav_position">
                  <option v-for="n in NAV_POSITIONS" :key="n.key" :value="n.key">{{ n.label }}</option>
                </select>
              </div>
              <div>
                <label class="label">排序</label>
                <input class="input" type="number" v-model.number="pageForm.nav_order" aria-label="排序" />
              </div>
            </div>

            <div class="label-row">
              <label class="label">頁面內容</label>
              <span class="label-row-actions">
                <button
                  v-if="hasBuiltinTemplate"
                  class="ai-toggle"
                  type="button"
                  @click="reloadBuiltinTemplate"
                >載入最新內建模板</button>
                <button class="ai-toggle" type="button" @click="showMarkdownHelp = !showMarkdownHelp">
                  {{ showMarkdownHelp ? '收起語法說明' : '語法說明' }}
                </button>
              </span>
            </div>

            <!-- 頁面內容的 AI 協助（issue #19），與元素故事共用每日額度 -->
            <div v-if="showMarkdownHelp" class="md-help">
              <p><code># 標題</code>　<code>**粗體**</code>　<code>*斜體*</code>　<code>[文字](網址)</code>　<code>- 清單</code>　<code>---</code> 分隔線</p>
              <p>另外有三種區塊，用來排出一般 Markdown 做不到的版面：</p>
              <pre>:::cards
### 熔點 | K（凱氏溫標）
固體變成液體的溫度。

### 沸點 | K
液體變成氣體的溫度。
:::</pre>
              <p><code>:::cards</code> 卡片格線（每個 <code>###</code> 一張，標題可用 <code>|</code> 分隔附註）、<code>:::note</code> 提示區塊、<code>:::links</code> 自動插入目前設定的社群連結。</p>
            </div>

            <!-- 區塊編輯器（issue #20）。舊頁面第一次打開時，原本的 Markdown
                 會自動變成一個「自訂 Markdown」區塊，內容不會消失 -->
            <div class="blocks-head">
              <p class="label">頁面區塊（{{ pageForm.blocks.length }}）</p>
              <button class="button secondary small" type="button" @click="blockPickerOpen = !blockPickerOpen">
                {{ blockPickerOpen ? '取消' : '＋ 新增區塊' }}
              </button>
            </div>

            <div v-if="blockPickerOpen" class="block-picker">
              <button
                v-for="def in PAGE_BLOCKS"
                :key="def.key"
                class="block-type"
                type="button"
                @click="addBlock(def.key)"
              >
                <span class="block-type-icon">{{ def.icon }}</span>
                <span class="block-type-name">{{ def.label }}</span>
                <span class="block-type-desc">{{ def.desc }}</span>
              </button>
            </div>

            <div v-if="!pageForm.blocks.length" class="placeholder-text">
              還沒有任何區塊，按「新增區塊」開始。
            </div>

            <div
              v-for="(block, bi) in pageForm.blocks"
              :key="bi"
              class="block-card"
            >
              <div class="block-card-head">
                <span class="block-index">{{ bi + 1 }}</span>
                <span class="block-name">{{ blockLabel(block.type) }}</span>
                <span class="block-actions">
                  <button class="icon-button" type="button" title="上移" :disabled="bi === 0" @click="moveBlock(bi, -1)">▲</button>
                  <button class="icon-button" type="button" title="下移" :disabled="bi === pageForm.blocks.length - 1" @click="moveBlock(bi, 1)">▼</button>
                  <button class="icon-button danger" type="button" title="刪除" @click="pageForm.blocks.splice(bi, 1)">✕</button>
                </span>
              </div>

              <div v-for="f in blockFields(block.type)" :key="f.name" class="block-field">
                <!-- Markdown 欄位用 AiField：標籤、輸入框與 AI 協助是一組的 -->
                <AiField
                  v-if="f.type === 'markdown'"
                  :label="f.label"
                  kind="page-content"
                  v-model="block.data[f.name]"
                  :rows="8"
                  multiline
                />

                <template v-else>
                <label class="label">{{ f.label }}</label>

                <select v-if="f.type === 'select'" class="select" v-model="block.data[f.name]" :aria-label="f.label">
                  <option v-for="o in f.options" :key="o.value" :value="o.value">{{ o.label }}</option>
                </select>

                <textarea
                  v-else-if="f.type === 'textarea'"
                  class="textarea"
                  rows="3"
                  v-model="block.data[f.name]"
                  :aria-label="f.label"
                ></textarea>

                <div v-else-if="f.type === 'image'" class="block-image">
                  <img v-if="blockImgSrc(block.data)" :src="blockImgSrc(block.data)" alt="" />
                  <span v-else class="layer-empty">未設定</span>
                  <input class="input" type="file" accept="image/*" :aria-label="f.label" @change="onBlockImage($event, block.data, f.name)" />
                  <button class="button secondary small" type="button" @click="openImagePicker(block.data)">從圖庫挑</button>
                  <button v-if="blockImgSrc(block.data)" class="draft-link" type="button" @click="clearBlockImage(block.data)">移除</button>
                  <span v-if="block.data.image_ref" class="hint-inline">來自圖庫，之後在圖庫換圖這裡會跟著變</span>
                </div>

                <!-- list：重複的子項目，欄位一樣由定義長出來 -->
                <div v-else-if="f.type === 'list'" class="block-list">
                  <div v-for="(item, ii) in block.data[f.name]" :key="ii" class="block-list-item">
                    <div class="block-list-head">
                      <span class="block-index">{{ ii + 1 }}</span>
                      <span class="block-actions">
                        <button class="icon-button" type="button" title="上移" :disabled="ii === 0" @click="moveItem(block.data[f.name], ii, -1)">▲</button>
                        <button class="icon-button" type="button" title="下移" :disabled="ii === block.data[f.name].length - 1" @click="moveItem(block.data[f.name], ii, 1)">▼</button>
                        <button class="icon-button danger" type="button" title="刪除" @click="block.data[f.name].splice(ii, 1)">✕</button>
                      </span>
                    </div>
                    <div v-for="sub in f.itemFields" :key="sub.name" class="block-field">
                      <label class="label">{{ sub.label }}</label>
                      <textarea v-if="sub.type === 'textarea'" class="textarea" rows="3" v-model="item[sub.name]" :aria-label="sub.label"></textarea>
                      <div v-else-if="sub.type === 'image'" class="block-image">
                        <img v-if="blockImgSrc(item)" :src="blockImgSrc(item)" alt="" />
                        <span v-else class="layer-empty">未設定</span>
                        <input class="input" type="file" accept="image/*" :aria-label="sub.label" @change="onBlockImage($event, item, sub.name)" />
                        <button class="button secondary small" type="button" @click="openImagePicker(item)">從圖庫挑</button>
                        <button v-if="blockImgSrc(item)" class="draft-link" type="button" @click="clearBlockImage(item)">移除</button>
                      </div>
                      <input v-else class="input" type="text" v-model="item[sub.name]" :aria-label="sub.label" />
                    </div>
                  </div>
                  <button class="button secondary small" type="button" @click="addItem(block.data[f.name], f)">＋ 新增一項</button>
                </div>

                <input v-else class="input" type="text" v-model="block.data[f.name]" :aria-label="f.label" />
                </template>
              </div>

              <p v-if="!blockFields(block.type).length" class="field-hint">
                這個區塊沒有可設定的欄位，直接放進頁面即可。
              </p>
            </div>

            <!-- 從圖庫挑圖：列出所有圖庫的圖，選了存的是參照而不是圖片本身 -->
            <div v-if="imagePickerTarget" class="block-picker">
              <p class="label">從圖庫挑一張圖</p>
              <p v-if="!libraryList.length" class="field-hint">還沒有任何圖庫，請先到「圖庫管理」建立。</p>
              <div v-for="lib in libraryList" :key="lib.id" class="picker-group">
                <p class="field-hint">{{ lib.name }}（{{ bindLabel(lib) }}）</p>
                <div class="style-grid library-grid">
                  <button
                    v-for="img in lib.images"
                    :key="img.id"
                    class="block-type picker-image"
                    type="button"
                    @click="pickImage(lib, img)"
                  >
                    <img :src="img.img_data" alt="" />
                    <span class="block-type-name">{{ img.name }}</span>
                  </button>
                </div>
              </div>
              <button class="button secondary small" type="button" @click="imagePickerTarget = null">取消</button>
            </div>

            <div class="page-preview">
              <p class="preview-label">即時預覽</p>
              <PageBlocks :blocks="pageForm.blocks" :libraries="libraryList" />
            </div>

          </form>
          </template>
        </div>

        <!-- Molecules -->
        <div v-if="section === 'molecules'" class="box">
          <AdminBar title="MOLECULES">
            <button class="button secondary" type="button" :disabled="moleculeSaving" @click="saveMoleculeDraft">存成草稿</button>
            <button class="button" type="button" :disabled="moleculeSaving" @click="publishMolecule">
              {{ moleculeSaving ? 'Saving…' : '發布' }}
            </button>
          </AdminBar>
          <p class="desc">
            用下面的建構器點選元素拼出分子式，再向 PubChem 查詢自動帶入分子量與 IUPAC 名稱。<br>
            網址代稱取自 IUPAC 名稱；查不到的分子也可以手動填寫後儲存。
          </p>

          <div v-if="moleculesMigratable" class="migrate-hint">
            <span>分子圖片可以搬進通用圖庫，之後每個分子都能有多張圖。</span>
            <button
              class="button secondary small"
              type="button"
              :disabled="migratingInto === 'molecule'"
              @click="handleMigrateInto('molecule', loadMolecules)"
            >{{ migratingInto === 'molecule' ? '搬移中…' : '全部搬進圖庫' }}</button>
          </div>

          <!-- 清單工具列：仿化學資料庫的「搜尋＋分類＋組成元素」三種切入點 -->
          <div class="mol-toolbar">
            <input
              class="input mol-filter-input"
              type="text"
              v-model="moleculeFilter"
              placeholder="搜尋名稱、分子式或網址代稱"
              aria-label="搜尋分子"
            />
            <select class="select mol-filter-select" v-model="moleculeCategoryFilter" aria-label="分類篩選">
              <option value="">全部分類</option>
              <option v-for="c in moleculeCategories" :key="c" :value="c">{{ c }}</option>
              <option value="__none__">未分類</option>
            </select>
            <select class="select mol-filter-select" v-model="moleculeElementFilter" aria-label="元素篩選">
              <option value="">全部元素</option>
              <option v-for="sym in moleculeElements" :key="sym" :value="sym">{{ sym }}</option>
            </select>
          </div>
          <p v-if="moleculeList.length" class="field-hint mol-count">
            {{ filteredMolecules.length }} / {{ moleculeList.length }} 個分子
          </p>

          <div class="page-list">
            <button
              v-for="m in filteredMolecules"
              :key="m.slug"
              class="page-item"
              type="button"
              :class="{ active: moleculeForm.original_slug === m.slug }"
              @click="selectMolecule(m)"
            >
              <span class="page-item-title" v-html="subscript(m.formula)"></span>
              <span class="page-item-meta">
                {{ m.name }}
                <span
                  v-if="moleculeCategory(m)"
                  class="mol-category-tag"
                  :class="{ 'mol-category-tag--auto': !m.category }"
                  :title="m.category ? '手動指定的分類' : '依組成元素自動判斷'"
                >{{ moleculeCategory(m) }}</span>
                <span v-if="!m.published" class="draft-tag">草稿</span>
              </span>
            </button>
            <button class="page-item page-item--new" type="button" @click="newMolecule">＋ 新增分子</button>
          </div>

          <form class="page-form" @submit.prevent="handleSaveMolecule">
            <label class="label">分子式建構器</label>
            <FormulaBuilder v-model="moleculeForm.nodes" @change="onFormulaChange" />

            <div class="mol-lookup">
              <input
                class="input"
                type="text"
                v-model="moleculeQuery"
                placeholder="也可以直接輸入名稱查詢，例如 water、caffeine"
                aria-label="分子名稱"
                @keydown.enter.prevent="lookupByName"
              />
              <button class="button secondary" type="button" :disabled="moleculeLooking" @click="lookupByName">
                依名稱查詢
              </button>
              <button
                class="button secondary"
                type="button"
                :disabled="moleculeLooking || !moleculeForm.formula"
                @click="lookupByFormula"
              >依分子式查詢</button>
            </div>

            <div v-if="lookupResults.length" class="mol-results">
              <p class="field-hint">PubChem 查到 {{ lookupResults.length }} 筆，點選要套用的：</p>
              <button
                v-for="r in lookupResults"
                :key="r.cid"
                class="mol-result"
                type="button"
                @click="applyLookup(r)"
              >
                <span class="mol-result-formula" v-html="subscript(r.formula)"></span>
                <span class="mol-result-name">{{ r.iupac_name || '（無 IUPAC 名稱）' }}</span>
                <span class="mol-result-cid">CID {{ r.cid }}</span>
              </button>
            </div>

            <div class="page-form-row">
              <div>
                <label class="label">顯示名稱</label>
                <input class="input" type="text" v-model="moleculeForm.name" aria-label="顯示名稱" />
                <p class="field-hint">可以填中文或俗名，例如「水」</p>
              </div>
              <div>
                <label class="label">IUPAC 名稱</label>
                <input class="input" type="text" v-model="moleculeForm.iupac_name" aria-label="IUPAC 名稱" />
                <p class="field-hint">網址為 /molecule/{{ moleculeSlug || '…' }}</p>
              </div>
            </div>

            <div class="page-form-row">
              <div>
                <label class="label">分子式</label>
                <input class="input" type="text" v-model="moleculeForm.formula" aria-label="分子式" />
              </div>
              <div>
                <label class="label">分子量</label>
                <input class="input" type="text" v-model="moleculeForm.weight" aria-label="分子量" />
              </div>
            </div>

            <label class="label">分類</label>
            <input class="input" type="text" v-model="moleculeForm.category" list="mol-category-presets" aria-label="分類" />
            <datalist id="mol-category-presets">
              <option v-for="c in CATEGORY_PRESETS" :key="c" :value="c" />
            </datalist>
            <p class="field-hint">
              <template v-if="moleculeForm.category">
                手動指定的分類。清空這欄會改用自動判斷{{ moleculeAutoCategory ? `：${moleculeAutoCategory}` : '' }}
              </template>
              <template v-else-if="moleculeAutoCategory">
                留空就好，會依組成元素自動歸為「{{ moleculeAutoCategory }}」。要覆寫才需要填
              </template>
              <template v-else>
                填好分子式後會依組成元素自動判斷分類，也可以在這裡自行指定
              </template>
            </p>

            <label class="label">SMILES</label>
            <input class="input" type="text" v-model="moleculeForm.smiles" aria-label="SMILES" />

            <AiField
              label="介紹"
              kind="molecule"
              v-model="moleculeForm.description"
              :extra="moleculeAiContext"
              :rows="5"
              multiline
            />

            <label class="label">代表圖片</label>
            <div class="mol-image-row">
              <div class="mol-image-preview">
                <img v-if="moleculeImageSrc" :src="moleculeImageSrc" alt="分子圖片" />
                <span v-else class="layer-empty">沒有自訂圖片時會用 PubChem 的 2D 結構圖</span>
              </div>
              <div class="mol-image-actions">
                <input type="file" accept="image/*" ref="moleculeImgInput" @change="onMoleculeImgChange" />
                <button
                  v-if="moleculeForm.img_data"
                  class="button secondary"
                  type="button"
                  @click="moleculeForm.img_data = ''"
                >移除自訂圖片</button>
              </div>
            </div>

            <div class="link-actions">
              <button
                v-if="moleculeForm.original_slug"
                class="button secondary"
                type="button"
                :disabled="moleculeSaving"
                @click="handleDeleteMolecule"
              >刪除此分子</button>
            </div>
          </form>
        </div>

        <!-- Element Groups（主族形象） -->
        <div v-if="section === 'groups'" class="box">
          <AdminBar title="ELEMENT GROUPS">
            <button v-if="groupForm.key" class="button" type="button" :disabled="groupSaving" @click="handleSaveGroup">
              {{ groupSaving ? 'Saving…' : '儲存形象' }}
            </button>
          </AdminBar>
          <p class="desc">
            同族元素性質相近，可以共用一套設計形象（例如 7A 鹵素是型態不穩定的獵食鳥類、
            8A 惰性氣體是圓胖胖的穩定物種）。<br>
            設定後會顯示在該族每個元素的介紹頁。
          </p>

          <div v-if="groupsMigratable" class="migrate-hint">
            <span>主族形象圖可以搬進通用圖庫，之後每一族都能有多個形象。</span>
            <button
              class="button secondary small"
              type="button"
              :disabled="migratingInto === 'group'"
              @click="handleMigrateInto('group', loadGroups)"
            >{{ migratingInto === 'group' ? '搬移中…' : '全部搬進圖庫' }}</button>
          </div>

          <div v-for="sec in GROUP_SECTIONS" :key="sec.title" class="group-section">
            <p class="group-section-title">{{ sec.title }}</p>
            <div class="group-key-list">
              <button
                v-for="g in sec.groups"
                :key="g.key"
                class="group-key"
                type="button"
                :class="{ active: groupForm.key === g.key, filled: groupHasContent(g.key) }"
                @click="selectGroup(g.key)"
              >
                <span class="group-key-label">{{ g.label }}</span>
                <span class="group-key-name">{{ g.name }}</span>
              </button>
            </div>
          </div>

          <form v-if="groupForm.key" @submit.prevent="handleSaveGroup">
            <label class="label">形象名稱</label>
            <input class="input" type="text" v-model="groupForm.name" aria-label="形象名稱" />
            <p class="field-hint">這一族的形象稱呼，例如「獵食鳥系」；留空表示尚未定名</p>

            <AiField
              label="共同特色"
              kind="group-archetype"
              v-model="groupForm.description"
              :extra="groupAiContext"
              :rows="5"
              multiline
              hint="同族設計時共用的特色，會顯示在元素頁的主族形象區塊"
            />

            <label class="label">形象代表圖</label>
            <div class="mol-image-row">
              <div class="mol-image-preview">
                <img v-if="groupForm.img_data" :src="groupForm.img_data" alt="主族形象圖" />
                <span v-else class="layer-empty">未設定</span>
              </div>
              <div class="mol-image-actions">
                <input type="file" accept="image/*" @change="onGroupImgChange" />
                <button
                  v-if="groupForm.img_data"
                  class="button secondary"
                  type="button"
                  @click="groupForm.img_data = ''"
                >移除圖片</button>
              </div>
            </div>

            <div class="link-actions">
              <span class="hint-inline">{{ groupElements(groupForm.key) }}</span>
            </div>
          </form>
        </div>

        <!-- Particles（基本粒子形象） -->
        <div v-if="section === 'particles'" class="box">
          <AdminBar title="PARTICLES">
            <button class="button secondary" type="button" :disabled="particleSaving" @click="saveParticleDraft">存成草稿</button>
            <button class="button" type="button" :disabled="particleSaving" @click="publishParticle">
              {{ particleSaving ? 'Saving…' : '發布' }}
            </button>
          </AdminBar>
          <p class="desc">
            電子、質子、中子這些基本粒子的形象設定，會呈現在前台的「基本粒子」頁。<br>
            可自由新增其他粒子（光子、夸克⋯），用排序控制先後。
          </p>

          <div class="page-list">
            <button
              v-for="pt in particleList"
              :key="pt.slug"
              class="page-item"
              type="button"
              :class="{ active: particleForm.original_slug === pt.slug }"
              @click="selectParticle(pt)"
            >
              <span class="page-item-title">{{ pt.name }}</span>
              <span class="page-item-meta">
                {{ pt.title || pt.slug }}
                <span v-if="!pt.published" class="draft-tag">草稿</span>
              </span>
            </button>
            <button class="page-item page-item--new" type="button" @click="newParticle">＋ 新增粒子</button>
          </div>

          <form class="page-form" @submit.prevent="handleSaveParticle">
            <div class="page-form-row">
              <div>
                <label class="label">粒子名稱</label>
                <input class="input" type="text" v-model="particleForm.name" aria-label="粒子名稱" />
                <p class="field-hint">例如「電子」</p>
              </div>
              <div>
                <label class="label">網址代稱</label>
                <input class="input" type="text" v-model="particleForm.slug" aria-label="粒子網址代稱" />
                <p class="field-hint">留空會從名稱產生；只能用小寫英數字與連字號</p>
              </div>
            </div>

            <div class="page-form-row">
              <div>
                <AiField
                  label="形象稱呼"
                  kind="particle-title"
                  v-model="particleForm.title"
                  :extra="particleAiContext"
                  hint="例如「黑白相間、變化無常又長翅膀的小圓球」"
                />
              </div>
              <div>
                <label class="label">排序</label>
                <input class="input" type="number" v-model.number="particleForm.order" aria-label="粒子排序" />
                <p class="field-hint">數字小的排前面</p>
              </div>
            </div>

            <AiField
              label="介紹"
              kind="particle-intro"
              v-model="particleForm.description"
              :extra="particleAiContext"
              :rows="5"
              multiline
            />

            <div v-if="particlesMigratable" class="migrate-hint">
              <span>粒子形象圖可以搬進通用圖庫，之後每顆粒子都能有多個樣貌。</span>
              <button class="button secondary small" type="button" :disabled="migratingInto === 'particle'" @click="handleMigrateInto('particle', loadParticles)">
                {{ migratingInto === 'particle' ? '搬移中…' : '全部搬進圖庫' }}
              </button>
              <p class="field-hint">已經有圖庫的粒子（例如電子）會把形象圖併進去，不會另外開一個庫。</p>
            </div>

            <label class="label">形象圖</label>
            <div v-if="particleLibrary" class="migrated-notice">
              這顆粒子的形象圖來自通用圖庫「{{ particleLibrary.name }}」（{{ particleLibrary.images.length }} 張），顯示的是預設那張。
              <button class="draft-link" type="button" @click="section = 'libraries'; selectLibrary(particleLibrary)">
                到「圖庫管理」編輯
              </button>
            </div>
            <div class="mol-image-row">
              <div class="mol-image-preview">
                <img v-if="particleForm.img_data" :src="particleForm.img_data" alt="粒子形象圖" />
                <span v-else class="layer-empty">未設定</span>
              </div>
              <div v-if="!particleLibrary" class="mol-image-actions">
                <input type="file" accept="image/*" @change="onParticleImgChange" />
                <button
                  v-if="electronChoices.length"
                  class="button secondary"
                  type="button"
                  @click="useDefaultElectronImg"
                >帶入預設電子圖</button>
                <button
                  v-if="particleForm.img_data"
                  class="button secondary"
                  type="button"
                  @click="particleForm.img_data = ''"
                >移除圖片</button>
              </div>
            </div>

            <div class="link-actions">
              <button
                v-if="particleForm.original_slug"
                class="button secondary"
                type="button"
                :disabled="particleSaving"
                @click="handleDeleteParticle"
              >刪除此粒子</button>
            </div>
          </form>
        </div>

        <!-- Site Settings -->
        <div v-if="section === 'site'" class="box">
          <AdminBar title="SITE SETTINGS">
            <button class="button" type="button" :disabled="siteSaving" @click="handleUpdateSiteSettings">
              {{ siteSaving ? 'Saving…' : '儲存' }}
            </button>
          </AdminBar>
          <p class="desc">
            網站層級的基本資料。標題與副標題會顯示在每一頁的左上角，
            描述用於搜尋引擎與分享連結時的摘要；留空則沿用系統預設文案。
          </p>
          <form @submit.prevent="handleUpdateSiteSettings">
            <label class="label">網站標題</label>
            <input class="input" type="text" v-model="siteForm.title" />

            <label class="label">副標題</label>
            <input class="input" type="text" v-model="siteForm.subtitle" />

            <AiField
              label="網站描述（SEO）"
              kind="site-description"
              v-model="siteForm.description"
              :extra="siteAiContext"
              :rows="2"
              multiline
            />

            <label class="label">首頁背景圖</label>
            <p class="field-hint">{{ uploadHint }}</p>
            <img v-if="siteBgCurrent && !siteBgPreviewUrl" :src="siteBgCurrent" class="img-preview bg-preview" alt="目前背景圖" />
            <p v-else-if="!siteBgCurrent && !siteBgPreviewUrl" class="placeholder-text">尚未設定，維持原本的漸層底色</p>
            <input class="input" type="file" accept="image/*" ref="siteBgInput" @change="onSiteBgFileChange" />
            <div v-if="siteBgPreviewUrl" class="preview-new">
              <p class="preview-label">新背景圖預覽（尚未儲存）</p>
              <img :src="siteBgPreviewUrl" class="img-preview bg-preview" alt="New background preview" />
              <p class="compress-info">{{ compressionSummary(siteBgInfo) }}</p>
            </div>

            <label class="label">元素圖鑑外框</label>
            <p class="field-hint">套用在元素頁代表圖外圍的框線樣式，會依該元素的顏色變化。</p>
            <div class="frame-picker">
              <button
                v-for="f in FRAME_STYLES"
                :key="f.key"
                class="frame-option"
                type="button"
                :class="{ active: siteForm.frame_style === f.key }"
                @click="siteForm.frame_style = f.key"
              >
                <PokedexFrame :style="f.key" color="E06633">
                  <span class="frame-sample">Fe</span>
                </PokedexFrame>
                <span class="frame-option-label">{{ f.label }}</span>
              </button>
            </div>

            <label class="label">分層圖底色</label>
            <p class="field-hint">
              原子核、電子、手寫元素名都是去背 PNG，需要一個底色才看得清楚。
              預設白色，與原本的靜態圖一致。
            </p>
            <div class="bg-picker">
              <input type="color" v-model="siteForm.layer_bg" aria-label="分層圖底色" />
              <input class="input bg-hex" type="text" v-model="siteForm.layer_bg" aria-label="色碼" />
              <button class="draft-link" type="button" @click="siteForm.layer_bg = '#ffffff'">還原白色</button>
              <span class="bg-sample" :style="{ background: siteForm.layer_bg }"></span>
            </div>

            <label class="label">電子大小</label>
            <p class="field-hint">
              電子在元素圖上的直徑，佔圖片寬度的百分比。電子數多的元素會自動再縮小一些避免重疊。
            </p>
            <div class="size-picker">
              <input type="range" min="10" max="40" step="1" v-model.number="siteForm.electron_size" aria-label="電子大小" />
              <span class="size-value">{{ siteForm.electron_size }}%</span>
              <span class="size-demo">
                <span class="size-demo-nucleus"></span>
                <span class="size-demo-electron" :style="{ width: siteForm.electron_size + '%', height: siteForm.electron_size + '%' }"></span>
              </span>
              <button class="draft-link" type="button" @click="siteForm.electron_size = 24">還原 24%</button>
            </div>

            <label class="label">自訂外框圖（PNG，需透明背景）</label>
            <p class="field-hint">上傳後會覆蓋上面選的內建款式，圖片會等比拉伸鋪滿代表圖範圍。</p>
            <img v-if="siteFrameCurrent && !siteFramePreviewUrl" :src="siteFrameCurrent" class="img-preview bg-preview" alt="目前外框圖" />
            <p v-else-if="!siteFrameCurrent && !siteFramePreviewUrl" class="placeholder-text">未使用自訂外框</p>
            <input class="input" type="file" accept="image/png" ref="siteFrameInput" @change="onSiteFrameFileChange" />
            <div v-if="siteFramePreviewUrl" class="preview-new">
              <p class="preview-label">新外框圖預覽（尚未儲存）</p>
              <img :src="siteFramePreviewUrl" class="img-preview bg-preview" alt="New frame preview" />
            </div>

            <div class="link-actions">
              <button
                v-if="siteBgCurrent"
                class="button secondary"
                type="button"
                :disabled="siteSaving"
                @click="handleClearSiteBg"
              >移除背景圖</button>
              <button
                v-if="siteFrameCurrent"
                class="button secondary"
                type="button"
                :disabled="siteSaving"
                @click="handleClearSiteFrame"
              >移除自訂外框</button>
            </div>
          </form>
        </div>

        <!-- Default Image -->

        <!-- 圖層素材：全站共用的素材與設定。原本電子樣式另外養一套圖，
             但「基本粒子」本來就是可自由新增的粒子形象庫，改成直接引用它 -->
        <div v-if="section === 'electrons'" class="box">
          <AdminBar title="LAYER ASSETS" />
          <p class="desc">
            全站共用的素材與設定。電子的畫法可以套用到任何元素，所以集中管理在這裡；<br>
            設一個<strong>預設</strong>之後，沒有另外指定的元素都會自動使用它。<br>
            每個元素放幾顆由電子組態自動決定。原子核與手寫名是每個元素各自的，在「元素故事」的圖層區設定。
          </p>

          <!-- 已經搬進通用圖庫的話，這裡就不再是編輯處，避免兩邊各改各的 -->
          <div v-if="electronLibrary" class="migrated-notice">
            電子樣式已搬進通用圖庫「{{ electronLibrary.name }}」（{{ electronLibrary.images.length }} 張）。
            <button class="draft-link" type="button" @click="section = 'libraries'; selectLibrary(electronLibrary)">
              到「圖庫管理」編輯
            </button>
          </div>

          <template v-else>
            <div v-if="electronStyles.length" class="migrate-hint">
              <span>這組樣式可以搬進通用圖庫，之後統一在「圖庫管理」維護。</span>
              <button class="button secondary small" type="button" :disabled="migrating" @click="handleMigrateElectrons">
                {{ migrating ? '搬移中…' : '搬進圖庫' }}
              </button>
              <p class="field-hint">舊資料會保留當退路，每個元素原本指定的樣式也會照樣指得到。</p>
            </div>

          <div v-if="!electronStyles.length" class="placeholder-text">尚未新增任何電子樣式。</div>

          <div v-else class="style-grid">
            <div
              v-for="st in electronStyles"
              :key="st.id"
              class="style-item"
              :class="{ broken: brokenStyles.includes(st.id), 'is-default': st.id === defaultStyleId }"
            >
              <img :src="st.img_data" alt="" @error="markBrokenStyle(st.id)" />
              <span class="style-name">
                {{ st.name }}
                <span v-if="brokenStyles.includes(st.id)" class="broken-tag">圖片損毀</span>
              </span>
              <div class="style-actions">
                <button
                  class="style-default-btn"
                  type="button"
                  :class="{ active: st.id === defaultStyleId }"
                  @click="toggleDefaultStyle(st)"
                >{{ st.id === defaultStyleId ? '★ 預設' : '設為預設' }}</button>
                <button
                  class="icon-button danger"
                  type="button"
                  :title="pendingDeleteStyle === st.id ? '再按一次確認刪除' : '刪除'"
                  :class="{ confirming: pendingDeleteStyle === st.id }"
                  @click="handleDeleteStyle(st)"
                >{{ pendingDeleteStyle === st.id ? '確認' : '✕' }}</button>
              </div>
            </div>
          </div>

          <label class="label">新增樣式</label>
          <p class="field-hint">請使用<strong>去背的 PNG</strong>，正方形構圖。上傳後會縮至 240px 並保留透明背景。</p>
          <div class="style-upload">
            <input class="input" type="text" v-model="newStyleName" aria-label="樣式名稱" />
            <input class="input" type="file" accept="image/*" ref="styleInput" aria-label="樣式圖片" @change="onStyleFile" />
          </div>
          <div v-if="newStyleImg" class="preview-new">
            <p class="preview-label">預覽（尚未儲存）</p>
            <img :src="newStyleImg" class="img-preview sprite-preview" alt="" />
            <p v-if="newStyleInfo" class="compress-info">
              {{ newStyleInfo.sourceSize }}
              <template v-if="newStyleInfo.trimmed"> → 裁掉透明邊距後 {{ newStyleInfo.contentSize }}</template>
              → 置中輸出 240×240
            </p>
          </div>
          <div class="link-actions">
            <button class="button" type="button" :disabled="styleSaving || !newStyleImg" @click="handleSaveStyle">
              {{ styleSaving ? 'Saving…' : '新增樣式' }}
            </button>
          </div>
          </template>

          <label class="label">運動方式（全站）</label>
          <p class="field-hint">
            這是整體的視覺風格，全站元素共用一種，不需要逐個元素設定。儲存後前台立即反映。
          </p>
          <div class="motion-picker">
            <button
              v-for="opt in motionOptions"
              :key="opt.value"
              class="motion-option"
              type="button"
              :class="{ active: motion === opt.value }"
              :disabled="motionSaving"
              @click="handleSaveMotion(opt.value)"
            >
              <span class="motion-name">{{ opt.label }}</span>
              <span class="motion-desc">{{ opt.desc }}</span>
            </button>
          </div>

          <!-- 原本自成一個側欄項目。它也是「全站共用的一張圖」，
               和這裡的性質一樣，沒有理由分成兩個地方 -->
          <label class="label">預設元素圖片（全站）</label>
          <p class="field-hint">元素還沒上傳自己的圖片時顯示這張。{{ uploadHint }}</p>
          <img v-if="defaultImgData" :src="defaultImgData" class="img-preview" alt="預設元素圖片" />
          <p v-else class="placeholder-text">尚未設定</p>
          <form @submit.prevent="handleUpdateDefaultImg">
            <input class="input" type="file" accept="image/*" ref="defaultImgInput" @change="onDefaultImgFileChange" />
            <div v-if="defaultImgPreviewUrl" class="preview-new">
              <p class="preview-label">新圖片預覽（尚未儲存）</p>
              <img :src="defaultImgPreviewUrl" class="img-preview" alt="新的預設元素圖片" />
              <p class="compress-info">{{ compressionSummary(defaultImgInfo) }}</p>
            </div>
            <div class="link-actions">
              <button class="button" type="submit" :disabled="defaultImgSaving || !defaultImgBlob">
                {{ defaultImgSaving ? 'Uploading…' : '上傳預設圖片' }}
              </button>
            </div>
          </form>
        </div>

        <!-- 圖庫管理：通用的一組圖，透過 bind_type 決定能用在哪一類東西上。
             要讓新的東西也能有圖庫，只在後端 BINDABLE_TYPES 加一筆即可 -->
        <div v-if="section === 'libraries'" class="box">
          <AdminBar title="IMAGE LIBRARIES">
            <template v-if="libraryForm">
              <button class="button secondary" type="button" @click="libraryForm = null">取消</button>
              <button class="button" type="button" :disabled="librarySaving" @click="handleSaveLibrary">
                {{ librarySaving ? 'Saving…' : '儲存圖庫' }}
              </button>
            </template>
            <button v-else class="button" type="button" @click="newLibrary">＋ 建立圖庫</button>
          </AdminBar>
          <p class="desc">
            一個圖庫是一組圖，綁在某個對象上（基本粒子、元素、主族、分子，或不綁對象的全站圖庫）。<br>
            綁定類型決定這個圖庫將來能用在哪裡，之後要開放新的對象類型不必再做一套介面。
          </p>

          <div v-if="!libraryList.length" class="placeholder-text">尚未建立任何圖庫。</div>

          <div v-else class="page-table">
            <div class="page-row page-row--head">
              <span>名稱</span><span>綁定</span><span>圖片數</span><span>操作</span>
            </div>
            <div v-for="lib in libraryList" :key="lib.id" class="page-row library-row">
              <span class="page-title-cell">{{ lib.name }}</span>
              <span class="page-path">{{ bindLabel(lib) }}</span>
              <span class="page-nav-cell">{{ lib.images.length }} 張</span>
              <span class="page-ops">
                <button class="button secondary small" type="button" @click="selectLibrary(lib)">編輯</button>
                <button
                  class="icon-button danger"
                  type="button"
                  :title="pendingDeleteLibrary === lib.id ? '再按一次確認刪除' : '刪除'"
                  :class="{ confirming: pendingDeleteLibrary === lib.id }"
                  @click="handleDeleteLibrary(lib)"
                >{{ pendingDeleteLibrary === lib.id ? '確認' : '✕' }}</button>
              </span>
            </div>
          </div>

          <form v-if="libraryForm" class="page-form" @submit.prevent="handleSaveLibrary">
            <p class="label">{{ libraryForm.id ? '編輯圖庫' : '建立圖庫' }}</p>

            <div class="page-form-row">
              <div>
                <label class="label">圖庫名稱</label>
                <input class="input" type="text" v-model="libraryForm.name" aria-label="圖庫名稱" />
              </div>
              <div>
                <label class="label">綁定類型</label>
                <select class="select" v-model="libraryForm.bind_type" @change="onBindTypeChange" aria-label="綁定類型">
                  <option v-for="b in bindable" :key="b.key" :value="b.key">{{ b.label }}</option>
                </select>
                <p class="field-hint">決定這個圖庫能用在哪一類東西上</p>
              </div>
            </div>

            <div v-if="currentBindable && currentBindable.needs_target">
              <label class="label">綁定對象</label>
              <select class="select" v-model="libraryForm.bind_id" aria-label="綁定對象">
                <option value="">請選擇…</option>
                <option v-for="t in bindTargets" :key="t.id" :value="t.id">{{ t.name }}</option>
              </select>
              <p v-if="!bindTargets.length" class="field-hint">這個類型底下還沒有可綁的對象。</p>
            </div>

            <label class="label">圖片（{{ libraryForm.images.length }} / {{ libraryMax }}）</label>
            <p class="field-hint">請使用<strong>去背的 PNG</strong>，正方形構圖。上傳後會縮至 240px 並保留透明背景。</p>

            <div v-if="libraryForm.images.length" class="style-grid library-grid">
              <div
                v-for="(img, i) in libraryForm.images"
                :key="img.id"
                class="style-item"
                :class="{ 'is-default': img.id === libraryForm.default_image }"
              >
                <img :src="img.img_data" alt="" />
                <input class="input" type="text" v-model="img.name" :aria-label="'圖片名稱 ' + (i + 1)" />
                <div class="style-actions">
                  <button
                    class="style-default-btn"
                    type="button"
                    :class="{ active: img.id === libraryForm.default_image }"
                    @click="libraryForm.default_image = libraryForm.default_image === img.id ? '' : img.id"
                  >{{ img.id === libraryForm.default_image ? '★ 預設' : '設為預設' }}</button>
                  <button class="icon-button danger" type="button" title="移除" @click="libraryForm.images.splice(i, 1)">✕</button>
                </div>
              </div>
            </div>

            <input
              class="input"
              type="file"
              accept="image/*"
              multiple
              ref="libraryImgInput"
              :disabled="libraryForm.images.length >= libraryMax"
              aria-label="新增圖片"
              @change="onLibraryImages"
            />

          </form>
        </div>

        <!-- Creator Links -->
        <div v-if="section === 'links'" class="box">
          <AdminBar title="CREATOR LINKS">
            <button class="button" type="button" :disabled="creatorLinksSaving" @click="handleUpdateCreatorLinks">
              {{ creatorLinksSaving ? 'Saving…' : '儲存' }}
            </button>
          </AdminBar>
          <p class="desc">
            設定要對外顯示的社群連結，數量不限。<br>
            儲存後會出現在每一頁最下方的頁尾，以及 /links 頁面；網址留空的項目會被忽略。<br>
            /links 頁面的說明文字請到「頁面管理」編輯。
          </p>

          <form @submit.prevent="handleUpdateCreatorLinks">
            <label class="label">頭像形狀</label>
            <div class="shape-picker">
              <button
                v-for="sh in AVATAR_SHAPES"
                :key="sh.key"
                class="shape-option"
                type="button"
                :class="{ active: creatorMeta.avatar_shape === sh.key }"
                @click="creatorMeta.avatar_shape = sh.key"
              >
                <i class="shape-demo" :class="'shape-demo--' + sh.key"></i>
                {{ sh.label }}
              </button>
            </div>

            <div v-if="!creatorLinks.length" class="placeholder-text">
              尚未新增任何連結，點下方「＋ 新增連結」開始。
            </div>

            <div v-if="creatorLinks.length" class="link-head">
              <span>平台</span>
              <span>顯示名稱</span>
              <span>網址</span>
            </div>

            <div v-for="(link, i) in creatorLinks" :key="i" class="link-row">
              <div class="link-row-fields">
                <select class="select link-platform" v-model="link.platform" @change="onPlatformChange(link)" aria-label="平台">
                  <option v-for="p in platforms" :key="p.key" :value="p.key">{{ p.label }}</option>
                </select>
                <input
                  class="input link-label"
                  type="text"
                  v-model="link.label"
                  aria-label="顯示名稱"
                />
                <input
                  class="input link-url"
                  type="url"
                  v-model="link.url"
                  aria-label="網址"
                />
              </div>
              <div class="link-row-actions">
                <button class="icon-button" type="button" title="上移" :disabled="i === 0" @click="moveLink(i, -1)">↑</button>
                <button class="icon-button" type="button" title="下移" :disabled="i === creatorLinks.length - 1" @click="moveLink(i, 1)">↓</button>
                <button class="icon-button danger" type="button" title="刪除" @click="removeLink(i)">✕</button>
              </div>

              <div class="link-extras">
                <div class="link-avatar">
                  <span
                    v-if="link.avatar"
                    class="avatar-preview"
                    :class="'avatar-preview--' + creatorMeta.avatar_shape"
                  >
                    <img :src="link.avatar" alt="" />
                  </span>
                  <span v-else class="avatar-empty">無頭像</span>
                  <input
                    class="input avatar-input"
                    type="file"
                    accept="image/*"
                    :aria-label="link.label + ' 頭像'"
                    @change="onAvatarChange($event, link)"
                  />
                  <button v-if="link.avatar" class="icon-button danger" type="button" title="移除頭像" @click="link.avatar = ''">✕</button>
                </div>

                <label class="link-color">
                  顏色
                  <input type="color" :value="link.color || platformInfo(link.platform).color" @input="link.color = $event.target.value" />
                  <button v-if="link.color" class="reset-color" type="button" @click="link.color = ''">用平台預設</button>
                </label>
              </div>
            </div>

            <div class="link-actions">
              <button class="button secondary" type="button" @click="addLink">＋ 新增連結</button>
            </div>
          </form>
        </div>

        <!-- Update Story -->
        <div v-if="section === 'story'" class="box">
          <AdminBar title="UPDATE STORY">
            <button class="button secondary" type="button" :disabled="loading" @click="handleSaveStoryDraft">存成草稿</button>
            <button class="button" type="button" :disabled="loading" @click="handleUpdateStory">發布</button>
          </AdminBar>
          <p class="desc">
            編輯單一元素的故事內容與代表圖片。<br>
            選擇元素後，Story 的文字會顯示在前台該元素的介紹頁（/stroy/{{ selectedSymbol || 'Symbol' }}），
            上傳圖片則會<strong>直接覆蓋</strong>該元素目前的圖片。<br>
            下拉選單的 ✓ 表示已寫故事、▣ 表示已上傳圖片。
          </p>

          <div class="progress-summary">
            <span>已寫故事 <strong>{{ storyProgress }}</strong> / {{ elements.length }}</span>
            <span class="progress-divider">·</span>
            <span>已上圖 <strong>{{ imageProgress }}</strong> / {{ elements.length }}</span>
          </div>

          <form @submit.prevent="handleUpdateStory">
            <label class="label">Element</label>
            <select v-model="selectedSymbol" class="select" @change="onSymbolChange">
              <option v-for="opt in elementOptions" :key="opt.symbol" :value="opt.symbol">{{ opt.label }}</option>
            </select>

            <AiField
              label="Story"
              kind="element-story"
              v-model="storyText"
              :extra="{ symbol: selectedSymbol }"
              :rows="6"
              multiline
            />

            <label class="label">Image</label>
            <p class="field-hint">{{ uploadHint }}</p>
            <input class="input" type="file" accept="image/*" ref="imageInput" @change="onImageFileChange" />

            <!-- 目前圖片與待上傳的新圖並排，方便直接對照 -->
            <div class="img-compare">
              <div v-if="selectedSymbol" class="img-slot">
                <p class="preview-label">目前圖片</p>
                <img
                  :src="currentElementImgSrc"
                  class="img-preview"
                  alt=""
                  @error="e => e.target.style.display='none'"
                />
              </div>
              <div v-if="newImagePreviewUrl" class="img-slot img-slot--new">
                <p class="preview-label">新圖片（尚未儲存）</p>
                <img :src="newImagePreviewUrl" class="img-preview" alt="New image preview" />
                <p class="compress-info">{{ compressionSummary(newImageInfo) }}</p>
              </div>
            </div>

            <div v-if="hasDraft" class="draft-notice">
              這個元素有未發布的草稿。
              <button class="draft-link" type="button" @click="loadDraft">載入草稿</button>
              <button class="draft-link" type="button" @click="loadPublished">改看已發布內容</button>
            </div>

          </form>

          <!-- 圖片分層 -->
          <div class="gallery-admin" :class="{ 'is-loading': elementLoading }">
            <p class="label">
              圖片分層
              <span v-if="elementLoading" class="loading-tag">載入中…</span>
            </p>
            <p class="field-hint">
              把代表圖拆成原子核、電子、手寫元素名三層。<br>
              <strong>設定原子核之後才會啟用分層呈現</strong>，在那之前一律沿用上面的代表圖。<br>
              三層都請使用<strong>去背的 PNG</strong>，上傳後會保留透明背景（縮至 900px）。
            </p>

            <div class="layer-grid">
              <div class="layer-slot">
                <p class="preview-label">原子核</p>
                <img v-if="layerForm.nucleus" :src="layerForm.nucleus" alt="" @error="onLayerImgError('nucleus')" />
                <p v-else class="layer-empty">{{ layerErrors.nucleus || '未設定' }}</p>
                <input class="input" type="file" accept="image/*" aria-label="原子核圖層" @change="onLayerFile($event, 'nucleus')" />
                <button v-if="layerForm.nucleus" class="draft-link" type="button" @click="layerForm.nucleus = ''">移除</button>
              </div>

              <div class="layer-slot">
                <p class="preview-label">手寫元素名</p>
                <img v-if="layerForm.name_img" :src="layerForm.name_img" alt="" @error="onLayerImgError('name_img')" />
                <p v-else class="layer-empty">{{ layerErrors.name_img || '未設定' }}</p>
                <input class="input" type="file" accept="image/*" aria-label="手寫元素名圖層" @change="onLayerFile($event, 'name_img')" />
                <button v-if="layerForm.name_img" class="draft-link" type="button" @click="layerForm.name_img = ''">移除</button>
              </div>

              <div class="layer-slot">
                <p class="preview-label">電子（{{ outerElectrons }} 顆）</p>
                <div v-if="electronChoices.length" class="electron-picker">
                  <button
                    v-for="st in electronChoices"
                    :key="st.id"
                    class="electron-option"
                    type="button"
                    :class="{ active: layerForm.electron_style === st.id }"
                    :title="st.name + (st.id === electronDefaultId ? '（預設）' : '')"
                    @click="layerForm.electron_style = layerForm.electron_style === st.id ? '' : st.id"
                  >
                    <img :src="st.img_data" alt="" />
                    <span v-if="st.id === electronDefaultId" class="electron-default-mark">★</span>
                  </button>
                </div>
                <p v-else class="layer-empty">尚無樣式，請先到「圖庫管理」新增</p>
                <p v-if="electronChoices.length && !layerForm.electron_style" class="layer-empty">
                  {{ electronDefaultId ? '未指定，將使用預設電子' : '未指定，且尚未設定預設電子' }}
                </p>

                <p class="layer-empty">
                  運動方式是全站統一的，到「圖層素材」設定。目前為<strong>{{ motionLabel }}</strong>。
                </p>
              </div>
            </div>

            <div class="link-actions">
              <button class="button" type="button" :disabled="layerSaving || elementLoading || !selectedSymbol" @click="handleSaveLayers">
                {{ layerSaving ? 'Saving…' : '儲存圖層' }}
              </button>
              <span class="hint-inline">
                最外層 {{ outerElectrons }} 個電子（由電子組態 {{ selectedConfig }} 推算）
              </span>
            </div>
          </div>

          <!-- 其他樣貌（gallery） -->
          <div class="gallery-admin" :class="{ 'is-loading': elementLoading }">
            <p class="label">
              其他樣貌
              <span v-if="elementLoading" class="loading-tag">載入中…</span>
            </p>
            <p class="field-hint">
              代表圖以外的照片，會顯示在元素頁故事下方的獨立區塊，最多 {{ GALLERY_MAX }} 張。<br>
              比照昆蟲、鳥類圖鑑：同一個元素的不同型態或狀態（例如純金屬、氧化物、礦石）。
            </p>

            <div v-if="galleryLibrary" class="migrated-notice">
              這個元素的其他樣貌已存在通用圖庫「{{ galleryLibrary.name }}」，在這裡編輯會直接寫回圖庫。
            </div>
            <div v-else-if="galleryItems.length" class="migrate-hint">
              <span>其他樣貌可以搬進通用圖庫，之後在「圖庫管理」也看得到、也能編輯。</span>
              <button class="button secondary small" type="button" :disabled="migratingGallery" @click="handleMigrateGalleries">
                {{ migratingGallery ? '搬移中…' : '全部搬進圖庫' }}
              </button>
              <p class="field-hint">會一次搬移所有元素的其他樣貌。舊資料保留當退路，這個編輯區照常可用。</p>
            </div>

            <div v-if="!galleryItems.length" class="placeholder-text">
              尚未加入其他樣貌。
            </div>

            <div v-else class="gallery-admin-grid">
              <div v-for="(item, i) in galleryItems" :key="i" class="gallery-admin-item">
                <img :src="item.img_data" alt="" />
                <input
                  class="input gallery-caption"
                  type="text"
                  v-model="item.caption"
                  aria-label="說明文字"
                />
                <div class="gallery-admin-actions">
                  <button class="icon-button" type="button" title="左移" :disabled="i === 0" @click="moveGalleryItem(i, -1)">←</button>
                  <button class="icon-button" type="button" title="右移" :disabled="i === galleryItems.length - 1" @click="moveGalleryItem(i, 1)">→</button>
                  <button class="icon-button danger" type="button" title="刪除" @click="removeGalleryItem(i)">✕</button>
                </div>
              </div>
            </div>

            <input
              class="input"
              type="file"
              accept="image/*"
              multiple
              ref="galleryInput"
              :disabled="galleryItems.length >= GALLERY_MAX"
              @change="onGalleryFileChange"
            />

            <div class="link-actions">
              <button class="button" type="button" :disabled="gallerySaving || elementLoading || !selectedSymbol" @click="handleSaveGallery">
                {{ gallerySaving ? 'Saving…' : '儲存其他樣貌' }}
              </button>
              <span class="hint-inline">{{ galleryItems.length }} / {{ GALLERY_MAX }} 張</span>
            </div>
          </div>
        </div>

        <!-- 浮水印 -->
        <WatermarkPanel v-if="section === 'watermark'" />

        <!-- 維護工具 -->
        <div v-if="section === 'maintenance'" class="box maintenance-box">
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

          <div class="maintenance-item">
            <div class="maintenance-info">
              <p class="maintenance-title">Rebuild Completion</p>
              <p class="desc">重新掃描所有元素，更新首頁用來標示「已上傳圖片／已寫故事」的摘要資料。<br>正常情況下儲存故事時已自動同步，只有直接從 Firebase 後台改過資料才需要執行。</p>
            </div>
            <button class="button" @click="handleRebuildCompletion">執行</button>
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

          <p v-if="adminMsg" class="msg" :class="adminMsgType">{{ adminMsg }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getAdminParticles, saveParticle, deleteParticle, getAdminGroups, saveGroup, getAdminMolecules, saveMolecule, deleteMolecule, lookupMolecule, createDb, updateDb, getStoryData, updateStory, backfillImgData, getDefaultImgInfo, updateDefaultImg, getAdminCreatorLinks, updateCreatorLinks, rebuildCompletion, getAiStatus, getPageMeta, savePageMeta, getAdminSiteSettings, updateSiteSettings, getAdminGallery, updateGallery, getAdminPages, savePage, deletePage, getAdminLayers, updateLayers, getElectronStyles, saveElectronStyle, deleteElectronStyle, setDefaultElectronStyle, getLibraries, saveLibrary, deleteLibrary, getBindableTargets, migrateElectronStyles, migrateGalleries, migrateIntoLibraries, getElectronMotion, setElectronMotion, apiBase } from '../api'
import { authState, login, logout } from '../store/auth'
import { showToast } from '../store/toast'
import { setCreatorLinks } from '../store/creatorLinks'
import { setSiteSettings, SITE_DEFAULTS, siteSettingsState } from '../store/siteSettings'
import { setPageSeo } from '../utils/seo'
import { refreshPages } from '../store/pages'
import { PLATFORMS, platformInfo } from '../utils/socialPlatforms'
import { compressImage, normalizeSprite, formatBytes, MAX_UPLOAD_BYTES, MAX_EDGE } from '../utils/imageCompress'
import PokedexFrame, { FRAME_STYLES } from '../components/PokedexFrame.vue'
import ImageCropper from '../components/ImageCropper.vue'
import MarkdownContent from '../components/MarkdownContent.vue'
import FormulaBuilder from '../components/FormulaBuilder.vue'
import { BUILTIN_PAGES } from '../utils/builtinPages'
import { outerElectronCount } from '../utils/valence'
import { parseFormula, usedElements } from '../utils/formula'
import { GROUP_SECTIONS } from '../utils/elementGroups'
import { MOLECULE_CATEGORIES, autoCategory, moleculeCategory } from '../utils/moleculeCategory'
import { metaDef as pageMetaDef, fieldDefault as pageMetaDefault, NAV_POSITIONS } from '../utils/pageMeta'
import { PAGE_BLOCKS, blockType, emptyBlock, emptyItem, blocksFrom, blocksToText } from '../utils/blockTypes'
import PageBlocks from '../components/PageBlocks.vue'
import AdminBar from '../components/AdminBar.vue'
import AiField from '../components/AiField.vue'
import GoogleLoginButton from '../components/GoogleLoginButton.vue'
import { fetchGoogleLoginConfig } from '../utils/googleAuth'
import { refreshPageMeta } from '../store/pageMeta'
import { buildTableGroups } from '../utils/periodicTableGroups'
import { elementsState, ensureElements } from '../store/elements'
import { runWatermarkJob } from '../utils/watermarkJobs'

// 與後端 GALLERY_MAX 一致
const GALLERY_MAX = 6

// 網址固定、由程式提供版面的頁面。可以改文案，但不能刪也不能改路徑。
// 三種編輯方式：
//   site     首頁文案在「網站設定」，這裡只做入口
//   markdown /guide 與 /links，整頁內容就是 Markdown
//   meta     版面固定，只有零碎文字可覆寫（PAGE_META_DEFS）
const SYSTEM_PAGES = [
  { kind: 'site', key: 'home', label: '首頁', path: '/' },
  { kind: 'markdown', key: 'guide', path: '/guide' },
  { kind: 'markdown', key: 'links', path: '/links' },
  // 這裡自己給名稱，不用 PAGE_META_DEFS 的 label：那份 label 帶著網址
  // 是為了舊版的單一清單，現在路徑已經是獨立欄位，再帶一次只是重複
  { kind: 'meta', key: 'molecules', label: '分子圖鑑', path: '/molecules' },
  { kind: 'meta', key: 'molecule', label: '分子頁', path: '/molecule/…' },
  { kind: 'meta', key: 'particles', label: '基本粒子', path: '/particles' },
  { kind: 'meta', key: 'watermark', label: '浮水印檢視', path: '/watermark' },
  { kind: 'meta', key: 'story', label: '元素頁區塊標題', path: '/stroy/…' },
  { kind: 'meta', key: 'footer', label: '頁尾', path: '（全站頁尾）' }
]

// 常用化合物分類，datalist 建議用；可自由輸入其他分類
// 分類留空時前台會自己從組成元素判斷（utils/moleculeCategory.js），
// 所以這份清單的角色是「覆寫」而不是「必填」。四個主分類排在前面，
// 是為了讓手動指定時仍然落在同一套語彙裡；後面幾個是正交的性質標籤，
// 需要按用途歸類時才用得上。
const CATEGORY_PRESETS = [
  ...MOLECULE_CATEGORIES,
  '生物分子', '溶劑', '高分子', '氣體'
]

const EMPTY_PARTICLE = () => ({
  original_slug: '', slug: '', name: '', title: '', description: '',
  img_data: '', order: 0, published: true
})

const EMPTY_MOLECULE = () => ({
  original_slug: '', name: '', iupac_name: '', formula: '', weight: '',
  smiles: '', cid: null, description: '', category: '', img_data: '', nodes: [],
  source: 'manual', published: true
})

const EMPTY_PAGE = () => ({
  original_slug: '', slug: '', title: '', subtitle: '', seo_description: '',
  content: '', blocks: [], nav_position: 'sidebar', nav_order: 0, published: false
})

const AVATAR_SHAPES = [
  { key: 'circle', label: '圓形' },
  { key: 'square', label: '方形' }
]

// 後台功能區塊。一次只顯示一項，避免所有表單疊在同一頁要一路往下滑。
const SECTIONS = [
  { key: 'story', label: '元素故事', icon: '✎' },
  { key: 'pages', label: '頁面管理', icon: '▤' },
  { key: 'molecules', label: '分子管理', icon: '⬡' },
  { key: 'site', label: '網站設定', icon: '⚙' },
  { key: 'electrons', label: '圖層素材', icon: '◌' },
  { key: 'libraries', label: '圖庫管理', icon: '▤' },
  { key: 'groups', label: '主族形象', icon: '❖' },
  { key: 'particles', label: '基本粒子', icon: '◉' },
  { key: 'links', label: '社群連結', icon: '⚯' },
  { key: 'watermark', label: '浮水印', icon: '◈' },
  { key: 'maintenance', label: '維護工具', icon: '⚒' }
]
import LoadingSpinner from '../components/LoadingSpinner.vue'
import WatermarkPanel from '../components/WatermarkPanel.vue'

export default {
  components: { LoadingSpinner, PokedexFrame, ImageCropper, MarkdownContent, PageBlocks, AdminBar, AiField, FormulaBuilder, WatermarkPanel, GoogleLoginButton },
  data() {
    return {
      authState,
      // 可用的登入方式，查到之前兩個都不畫（避免表單閃一下又消失）
      loginMethodsLoaded: false, googleLoginEnabled: false, passwordLoginEnabled: true,
      // 「使用其他方式登入」按下去之後才展開帳密表單
      showPasswordForm: false,
      SECTIONS,
      section: SECTIONS.some(s => s.key === localStorage.getItem('adminSection'))
        ? localStorage.getItem('adminSection')
        : 'story',
      loading: false,
      bootstrapped: false,
      email: '',
      password: '',
      msg: '',
      adminMsg: '',
      watermarkJob: null,
      watermarkFailures: [],
      adminMsgType: '',
      elements: [],
      storyDatas: {},
      draftDatas: {},
      elementConfigs: {},
      imageDatas: {},
      hasImageMap: {},
      selectedSymbol: '',
      elementLoading: false,
      storyText: '',
      defaultImgData: '',
      defaultImgSaving: false,
      newImagePreviewUrl: '',
      newImageBlob: null,
      newImageInfo: null,
      defaultImgPreviewUrl: '',
      defaultImgBlob: null,
      defaultImgInfo: null,
      creatorLinks: [],
      creatorMeta: { description: '', avatar_shape: 'circle' },
      AVATAR_SHAPES,
      creatorLinksSaving: false,
      platforms: PLATFORMS,
      FRAME_STYLES,
      GALLERY_MAX,
      GROUP_SECTIONS,
      CATEGORY_PRESETS,
      PAGE_BLOCKS,
      blockPickerOpen: false,
      imagePickerTarget: null,
      NAV_POSITIONS,
      layerForm: { nucleus: '', name_img: '', electron_style: '' },
      layerSaving: false,
      layerErrors: { nucleus: '', name_img: '' },
      libraryList: [],
      migrating: false,
      migratingGallery: false,
      migratingInto: '',
      bindable: [],
      bindTargets: [],
      libraryMax: 12,
      libraryForm: null,
      librarySaving: false,
      pendingDeleteLibrary: '',
      brokenStyles: [],
      pendingDeleteStyle: '',
      electronStyles: [],
      defaultStyleId: '',
      newStyleName: '',
      newStyleImg: '',
      newStyleInfo: null,
      styleSaving: false,
      motion: 'orbit',
      motionSaving: false,
      motionOptions: [
        { value: 'orbit', label: '繞著原子核', desc: '分層繞行，會轉到原子核前後，有遠近景深' },
        { value: 'free', label: '自由飄動', desc: '電子脫離圖框，在整個網頁裡漫遊' },
        { value: 'follow', label: '跟隨鼠標', desc: '電子跟著滑鼠跑，前後快慢不同會拖出尾巴' }
      ],
      pageList: [],
      SYSTEM_PAGES,
      // 清單／編輯兩段式，避免所有東西擠在同一個捲動頁
      pageMode: 'list',
      editKind: 'page',
      pendingDeletePage: '',
      pageMetaAll: {},
      metaKey: '',
      metaForm: {},
      metaSaving: false,

      pageForm: EMPTY_PAGE(),
      pageSaving: false,
      particleList: [],
      particleForm: EMPTY_PARTICLE(),
      particleSaving: false,
      groupList: [],
      groupForm: { key: '', name: '', description: '', img_data: '' },
      groupSaving: false,
      moleculeList: [],
      moleculeFilter: '',
      moleculeCategoryFilter: '',
      moleculeElementFilter: '',
      moleculeForm: EMPTY_MOLECULE(),
      moleculeSaving: false,
      moleculeQuery: '',
      moleculeLooking: false,
      lookupResults: [],
      showMarkdownHelp: false,
      cropFile: null,
      cropTarget: null,
      cropQueue: [],
      galleryItems: [],
      gallerySaving: false,
      siteForm: { title: '', subtitle: '', description: '', frame_style: 'classic', layer_bg: '#ffffff', electron_size: 24 },
      siteDefaults: SITE_DEFAULTS,
      siteBgCurrent: '',
      siteBgPreviewUrl: '',
      siteFrameCurrent: '',
      siteFramePreviewUrl: '',
      siteFrameBlob: null,
      siteBgBlob: null,
      siteBgInfo: null,
      siteSaving: false,
      aiPlaceholder: null
    }
  },
  computed: {
    metaDef() {
      return pageMetaDef(this.metaKey)
    },
    // 用實際會顯示的分類（含自動判斷的），後台的篩選才會跟前台看到的一致。
    // 只收手動填的話，這個下拉在沒人填 category 的情況下永遠是空的
    moleculeCategories() {
      return [...new Set(this.moleculeList.map(m => moleculeCategory(m)).filter(Boolean))].sort()
    },
    moleculeElements() {
      return [...new Set(this.moleculeList.flatMap(m => m.elements || []))].sort()
    },
    filteredMolecules() {
      const q = this.moleculeFilter.trim().toLowerCase()
      return this.moleculeList.filter(m => {
        if (q && !(m.name?.toLowerCase().includes(q) || m.formula?.toLowerCase().includes(q) || m.slug?.includes(q))) return false
        // 這裡比對的是顯示用的分類，所以「未分類」現在的意思是
        // 「手動沒填，而且組成元素也認不出來」——通常是分子式還沒填
        const category = moleculeCategory(m)
        if (this.moleculeCategoryFilter === '__none__') { if (category) return false }
        else if (this.moleculeCategoryFilter && category !== this.moleculeCategoryFilter) return false
        if (this.moleculeElementFilter && !(m.elements || []).includes(this.moleculeElementFilter)) return false
        return true
      })
    },
    moleculeSlug() {
      const raw = this.moleculeForm.iupac_name || this.moleculeForm.name
      return raw.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
    },
    moleculeImageSrc() {
      if (this.moleculeForm.img_data) return this.moleculeForm.img_data
      return this.moleculeForm.cid
        ? `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/${this.moleculeForm.cid}/PNG`
        : ''
    },
    currentSection() {
      return SECTIONS.find(s => s.key === this.section) || SECTIONS[0]
    },
    uploadHint() {
      return `上傳前會自動等比縮至長邊 ${MAX_EDGE}px 並轉為 JPEG，減少資料庫用量；超過 ${formatBytes(MAX_UPLOAD_BYTES)} 的檔案不接受。`
    },
    currentElementImgSrc() {
      if (!this.selectedSymbol) return ''
      return apiBase + '/elements/' + this.selectedSymbol + '/img'
    },
    // #5：每個元素標示故事/圖片完成度，讓 admin 一眼看出還有哪些沒補
    elementOptions() {
      return this.elements.map(sym => {
        const hasStory = !!(this.storyDatas[sym] || '').trim()
        const hasImage = !!this.hasImageMap[sym]
        // 用幾何符號而非 emoji：介面字型沒有 emoji 字符，會渲染成方框
        const marks = (hasStory ? ' ✓' : '') + (hasImage ? ' ▣' : '')
        return { symbol: sym, hasStory, hasImage, label: sym + marks }
      })
    },
    editingBuiltinPage() {
      return !!BUILTIN_PAGES[this.pageForm.slug]
    },
    // 內建模板是空的時候不顯示「載入最新內建模板」——按下去只會清空
    // 編輯框，看起來像誤觸
    hasBuiltinTemplate() {
      return !!BUILTIN_PAGES[this.pageForm.slug]?.content?.trim()
    },
    // 主族形象要讓 AI 知道對象是哪一族、有哪些元素。族與元素的對照後端也有，
    // 但元素符號只在 periodic_table 節點裡，為了一個提示整包讀那個節點正是
    // 拖垮 /elements/seo 的那件事，所以由這裡帶過去
    groupAiContext() {
      return {
        key: this.groupForm.key,
        name: this.groupForm.name,
        elements: this.groupElements(this.groupForm.key)
      }
    },
    // 形象稱呼與介紹互為對方的 context：先寫好其中一個，另一個就有東西可扣
    particleAiContext() {
      return {
        name: this.particleForm.name,
        title: this.particleForm.title,
        description: this.particleForm.description
      }
    },
    // 分類欄位留空時前台會判成什麼。優先用建構器的節點，還沒動過建構器
    // 就從分子式字串解析——手動貼上分子式的情況下 nodes 是空的
    moleculeAutoCategory() {
      const f = this.moleculeForm
      const nodes = f.nodes?.length ? f.nodes : parseFormula(f.formula)
      return autoCategory(usedElements(nodes))
    },
    // 表單上填了什麼就帶什麼，空欄位由後端濾掉
    moleculeAiContext() {
      const f = this.moleculeForm
      return {
        name: f.name,
        iupac_name: f.iupac_name,
        formula: f.formula,
        weight: f.weight,
        category: f.category,
        smiles: f.smiles
      }
    },
    siteAiContext() {
      return { title: this.siteForm.title, subtitle: this.siteForm.subtitle }
    },
    // SEO 描述是摘要型：要摘的就是這頁目前的標題與區塊內容
    pageSeoAiContext() {
      return {
        title: this.pageForm.title,
        // 描述只有一句話，內容再長也沒有意義；後端另有一道同樣的上限
        content: blocksToText(this.pageForm.blocks).slice(0, 4000)
      }
    },
    // 系統頁面與自訂頁面合成同一份清單。系統頁排在前面（網址固定、順序
    // 也固定），自訂頁接在後面，依導覽位置分組後才照 nav_order 排
    pageRows() {
      const rows = SYSTEM_PAGES.map(s => {
        if (s.kind === 'markdown') {
          // 資料庫有同名頁面表示已經改過，標題與發布狀態要看資料庫的版本
          const saved = this.pageList.find(p => p.slug === s.key)
          return {
            kind: 'markdown',
            key: s.key,
            title: saved?.title || BUILTIN_PAGES[s.key].title,
            path: s.path,
            published: saved ? saved.published : true,
            nav: '固定',
            system: true,
            saved
          }
        }
        if (s.kind === 'site') {
          return {
            kind: 'site',
            key: s.key,
            title: this.siteForm.title || s.label,
            path: s.path,
            published: true,
            nav: '固定',
            system: true
          }
        }
        // 純文案頁的導覽位置存在 _page_meta，不是「固定」。沒存過就顯示該頁自己
        // 的預設值——寫死 footer 的話，預設在別處的頁面（浮水印檢視是 sidebar）
        // 會在這份清單上顯示錯的位置
        const navKey = pageMetaDef(s.key)?.fields.some(f => f.name === 'nav_position')
          ? (this.pageMetaAll[s.key]?.nav_position || pageMetaDefault(s.key, 'nav_position'))
          : ''
        return {
          kind: 'meta',
          key: s.key,
          title: s.label || pageMetaDef(s.key)?.label || s.key,
          path: s.path,
          published: true,
          nav: navKey ? (NAV_POSITIONS.find(n => n.key === navKey)?.label || navKey) : '固定',
          system: true
        }
      })

      const builtinSlugs = new Set(Object.keys(BUILTIN_PAGES))
      const navRank = Object.fromEntries(NAV_POSITIONS.map((n, i) => [n.key, i]))
      const custom = this.pageList
        .filter(p => !builtinSlugs.has(p.slug))
        .sort((a, b) =>
          (navRank[a.nav_position] ?? 99) - (navRank[b.nav_position] ?? 99) ||
          (a.nav_order || 0) - (b.nav_order || 0) ||
          a.title.localeCompare(b.title)
        )

      custom.forEach((p, i) => {
        const sameGroup = j => custom[j] && custom[j].nav_position === p.nav_position
        rows.push({
          kind: 'custom',
          key: p.slug,
          title: p.title,
          path: `/p/${p.slug}`,
          published: p.published,
          nav: NAV_POSITIONS.find(n => n.key === p.nav_position)?.label || p.nav_position,
          page: p,
          // 排序只在同一個導覽位置內有意義，跨組交換不會改變畫面
          canUp: sameGroup(i - 1),
          canDown: sameGroup(i + 1),
          neighbours: { up: custom[i - 1], down: custom[i + 1] }
        })
      })

      return rows
    },
    selectedConfig() {
      return this.elementConfigs[this.selectedSymbol] || ''
    },
    outerElectrons() {
      return outerElectronCount(this.selectedConfig)
    },
    // 電子是否已經搬進圖庫。搬了就以圖庫為準，這裡只留入口
    electronLibrary() {
      return this.libraryList.find(l => l.bind_type === 'particle' && l.bind_id === 'electron') || null
    },
    // 電子目前可選的樣式與預設。搬進圖庫後以圖庫為準，否則沿用舊節點。
    // 所有消費端只讀這兩個，不要各自判斷該讀哪一邊——搬遷時漏改一處就會
    // 出現「圖庫改了但別的地方沒跟著改」
    // 目前選中的元素是否已經有「其他樣貌」圖庫
    // 目前編輯中的粒子是否已經有圖庫
    particleLibrary() {
      const slug = this.particleForm.original_slug || this.particleForm.slug
      if (!slug) return null
      return this.libraryList.find(l => l.bind_type === 'particle' && l.bind_id === slug) || null
    },
    // 還有粒子的形象圖沒進圖庫時才顯示搬遷入口
    particlesMigratable() {
      return this.particleList.some(p => p.img_data && !p.has_library)
    },
    groupsMigratable() {
      return this.groupList.some(g => g.img_data && !g.has_library)
    },
    moleculesMigratable() {
      // 分子清單沒有 has_library 欄位，改用圖庫清單反查
      const bound = new Set(this.libraryList.filter(l => l.bind_type === 'molecule').map(l => l.bind_id))
      return this.moleculeList.some(m => m.img_data && !bound.has(m.slug))
    },
    galleryLibrary() {
      if (!this.selectedSymbol) return null
      return this.libraryList.find(
        l => l.bind_type === 'element' && l.bind_id === this.selectedSymbol) || null
    },
    electronChoices() {
      const lib = this.electronLibrary
      if (lib) return lib.images.map(i => ({ id: i.id, name: i.name, img_data: i.img_data }))
      return this.electronStyles
    },
    electronDefaultId() {
      return this.electronLibrary ? this.electronLibrary.default_image : this.defaultStyleId
    },
    currentBindable() {
      return this.bindable.find(b => b.key === this.libraryForm?.bind_type) || null
    },
    motionLabel() {
      return (this.motionOptions.find(o => o.value === this.motion) || {}).label || this.motion
    },
    hasDraft() {
      return !!(this.draftDatas[this.selectedSymbol] || '').trim()
    },
    storyProgress() {
      return this.elementOptions.filter(o => o.hasStory).length
    },
    imageProgress() {
      return this.elementOptions.filter(o => o.hasImage).length
    }
  },
  watch: {
    // initAuth 是非同步的：硬重整 /admin 時 mounted 執行當下可能還沒完成登入檢查，
    // 等狀態翻成已登入再補載，否則後台會顯示一片空資料（issue #13/#16 的元凶）
    'authState.loggedIn'(loggedIn) {
      if (loggedIn) this.bootstrap()
    }
  },
  async mounted() {
    // 後台不該被收錄。robots.txt 已經擋掉，這裡再補一層：已經被收錄的
    // 網址只有 noindex 能讓它從索引移除
    setPageSeo({ title: `管理後台｜${siteSettingsState.title}`, noindex: true })
    // 不管登入與否都先問一次可用的登入方式：這頁的用途就是登入，跟頁尾那個
    // 低調入口不一樣，沒有「不要打擾一般訪客」的顧慮。結果在 utils/googleAuth
    // 有快取，兩處共用同一次請求
    this.loadLoginMethods()
    if (this.authState.loggedIn) {
      await this.bootstrap()
    }
  },
  beforeUnmount() {
    this.revokeImagePreview()
    this.revokeDefaultImgPreview()
  },
  methods: {
    // 清單與篩選都要用，掛上來讓 template 直接呼叫
    moleculeCategory,
    async loadLoginMethods() {
      const cfg = await fetchGoogleLoginConfig()
      this.googleLoginEnabled = !!cfg.enabled
      // 舊版後端不會回這個欄位，那時候帳密登入本來就是開的，
      // 只有明確收到 false 才關掉
      this.passwordLoginEnabled = cfg.passwordLogin !== false
      this.loginMethodsLoaded = true
    },
    async bootstrap() {
      if (this.bootstrapped) return
      this.bootstrapped = true
      this.loading = true
      try {
        await this.loadAll()
      } finally {
        this.loading = false
      }
    },
    loadAll() {
      return Promise.all([
        this.loadStoryData(), this.loadDefaultImg(), this.loadCreatorLinks(),
        this.loadSiteSettings(), this.loadPages(),
        this.loadElectronStyles(), this.loadLibraries(), this.loadMolecules(), this.loadGroups(), this.loadParticles(), this.loadPageMeta()
      ])
    },
    // ── 圖片裁切流程 ──
    // 三個 1:1 顯示的圖片（元素代表圖、預設圖、其他樣貌）上傳後先進裁切；
    // 首頁背景圖是全螢幕 cover，固定比例沒有意義，維持原本的壓縮流程
    openCropper(e, target) {
      const file = e.target.files[0]
      e.target.value = ''
      if (!file) return
      if (!file.type.startsWith('image/')) {
        showToast('請選擇圖片檔', 'error')
        return
      }
      this.cropTarget = target
      this.cropQueue = []
      this.cropFile = file
    },
    async onCropDone({ blob }) {
      // 裁切輸出已是 JPEG，再走一次壓縮確保尺寸與檔案大小一致
      const file = new File([blob], 'cropped.jpg', { type: 'image/jpeg' })
      await this.acceptCropped(file)
    },
    async onCropSkip() {
      await this.acceptCropped(this.cropFile)
    },
    onCropCancel() {
      this.nextCropOrClose()
    },
    async acceptCropped(file) {
      const target = this.cropTarget
      try {
        const result = await compressImage(file)
        if (target === 'story') {
          this.newImageBlob = result.blob
          this.newImageInfo = result
          this.newImagePreviewUrl = URL.createObjectURL(result.blob)
        } else if (target === 'default') {
          this.defaultImgBlob = result.blob
          this.defaultImgInfo = result
          this.defaultImgPreviewUrl = URL.createObjectURL(result.blob)
        } else if (target === 'gallery') {
          const img_data = await new Promise((resolve, reject) => {
            const reader = new FileReader()
            reader.onload = () => resolve(reader.result)
            reader.onerror = reject
            reader.readAsDataURL(result.blob)
          })
          this.galleryItems.push({ img_data, caption: '' })
        }
      } catch (err) {
        showToast(err.message || '圖片處理失敗', 'error')
      } finally {
        this.nextCropOrClose()
      }
    },
    nextCropOrClose() {
      // gallery 多檔時逐張處理
      this.cropFile = this.cropQueue.length ? this.cropQueue.shift() : null
      if (!this.cropFile) this.cropTarget = null
    },
    onImageFileChange(e) {
      this.revokeImagePreview()
      this.openCropper(e, 'story')
    },
    revokeImagePreview() {
      if (this.newImagePreviewUrl) {
        URL.revokeObjectURL(this.newImagePreviewUrl)
        this.newImagePreviewUrl = ''
      }
      this.newImageBlob = null
      this.newImageInfo = null
    },
    onDefaultImgFileChange(e) {
      this.revokeDefaultImgPreview()
      this.openCropper(e, 'default')
    },
    revokeDefaultImgPreview() {
      if (this.defaultImgPreviewUrl) {
        URL.revokeObjectURL(this.defaultImgPreviewUrl)
        this.defaultImgPreviewUrl = ''
      }
      this.defaultImgBlob = null
      this.defaultImgInfo = null
    },
    compressionSummary(info) {
      if (!info) return ''
      const saved = info.originalSize - info.compressedSize
      const pct = info.originalSize ? Math.round((saved / info.originalSize) * 100) : 0
      const size = `${formatBytes(info.originalSize)} → ${formatBytes(info.compressedSize)}`
      const dims = info.resized ? `，已縮至 ${info.width}×${info.height}` : ''
      return saved > 0 ? `${size}（省下 ${pct}%）${dims}` : `${size}${dims}`
    },
    async handleLogin() {
      this.loading = true
      this.msg = ''
      try {
        const result = await login(this.email, this.password)
        if (result.ok) {
          await this.bootstrap()
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
    async loadGallery() {
      if (!this.selectedSymbol) { this.galleryItems = []; return }
      try {
        const res = await getAdminGallery(this.selectedSymbol)
        this.galleryItems = res.data.images || []
      } catch (e) {
        console.error('Failed to load gallery:', e)
        this.galleryItems = []
      }
    },
    onGalleryFileChange(e) {
      const files = [...e.target.files]
      e.target.value = ''
      if (!files.length) return

      const room = GALLERY_MAX - this.galleryItems.length
      if (files.length > room) {
        showToast(`最多再加 ${room} 張，只會處理前 ${room} 張`, 'warning')
      }
      // 多檔時逐張進裁切，處理完一張才換下一張
      this.cropQueue = files.slice(0, room)
      this.cropTarget = 'gallery'
      this.cropFile = this.cropQueue.shift() || null
    },
    moveGalleryItem(i, delta) {
      const target = i + delta
      if (target < 0 || target >= this.galleryItems.length) return
      const [item] = this.galleryItems.splice(i, 1)
      this.galleryItems.splice(target, 0, item)
    },
    removeGalleryItem(i) {
      this.galleryItems.splice(i, 1)
    },
    async handleSaveGallery() {
      this.gallerySaving = true
      try {
        const res = await updateGallery(this.selectedSymbol, this.galleryItems.map(it => ({
          img_data: it.img_data,
          caption: (it.caption || '').trim()
        })))
        showToast(res.data.message || 'Saved!', 'success')
      } catch (e) {
        showToast(e.response?.data?.message || 'Save failed', 'error')
      } finally {
        this.gallerySaving = false
      }
    },
    async loadParticles() {
      try {
        const res = await getAdminParticles()
        this.particleList = res.data.particles || []
      } catch (e) {
        console.error('Failed to load particles:', e)
      }
    },
    selectParticle(pt) {
      this.particleForm = {
        original_slug: pt.slug, slug: pt.slug, name: pt.name,
        title: pt.title || '', description: pt.description || '',
        img_data: pt.img_data || '', order: pt.order || 0,
        published: pt.published !== false
      }
    },
    newParticle() {
      this.particleForm = EMPTY_PARTICLE()
    },
    useDefaultElectronImg() {
      // 電子的形象圖直接沿用圖層素材的預設電子，不必重新上傳
      const choices = this.electronChoices
      const style = choices.find(st => st.id === this.electronDefaultId) || choices[0]
      if (style?.img_data) this.particleForm.img_data = style.img_data
    },
    async onParticleImgChange(e) {
      const file = e.target.files[0]
      e.target.value = ''
      if (!file) return
      try {
        const result = await compressImage(file, { keepTransparency: true })
        this.particleForm.img_data = await new Promise((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = () => resolve(reader.result)
          reader.onerror = reject
          reader.readAsDataURL(result.blob)
        })
      } catch (err) {
        showToast(err.message || '圖片處理失敗', 'error')
      }
    },
    async publishParticle() {
      this.particleForm.published = true
      await this.handleSaveParticle()
    },
    async saveParticleDraft() {
      this.particleForm.published = false
      await this.handleSaveParticle()
    },
    async handleSaveParticle() {
      this.particleSaving = true
      try {
        const res = await saveParticle(this.particleForm)
        showToast(res.data.message || '已儲存', 'success')
        this.particleForm.original_slug = res.data.slug
        this.particleForm.slug = res.data.slug
        await this.loadParticles()
      } catch (e) {
        showToast(e.response?.data?.message || '儲存失敗', 'error')
      } finally {
        this.particleSaving = false
      }
    },
    async handleDeleteParticle() {
      const slug = this.particleForm.original_slug
      if (!slug) return
      this.particleSaving = true
      try {
        const res = await deleteParticle(slug)
        showToast(res.data.message || '已刪除', 'success')
        this.newParticle()
        await this.loadParticles()
      } catch (e) {
        showToast(e.response?.data?.message || '刪除失敗', 'error')
      } finally {
        this.particleSaving = false
      }
    },
    async loadGroups() {
      try {
        const res = await getAdminGroups()
        this.groupList = res.data.groups || []
      } catch (e) {
        console.error('Failed to load groups:', e)
      }
    },
    groupHasContent(key) {
      const g = this.groupList.find(x => x.key === key)
      return !!(g && (g.name || g.description || g.img_data))
    },
    groupElements(key) {
      // 顯示這一族有哪些元素，幫助確認設定對象
      const map = buildTableGroups(elementsState.elements)
      const syms = Object.keys(map).filter(s => map[s] === key)
      if (!syms.length) return ''
      const head = syms.slice(0, 12).join('、')
      return syms.length > 12 ? `${head}⋯ 共 ${syms.length} 個元素` : `${head}`
    },
    selectGroup(key) {
      ensureElements()
      const g = this.groupList.find(x => x.key === key)
      this.groupForm = {
        key,
        name: g?.name || '',
        description: g?.description || '',
        img_data: g?.img_data || ''
      }
    },
    async onGroupImgChange(e) {
      const file = e.target.files[0]
      e.target.value = ''
      if (!file) return
      try {
        // 形象圖與電子一樣多為去背 PNG，保留透明
        const result = await compressImage(file, { keepTransparency: true })
        this.groupForm.img_data = await new Promise((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = () => resolve(reader.result)
          reader.onerror = reject
          reader.readAsDataURL(result.blob)
        })
      } catch (err) {
        showToast(err.message || '圖片處理失敗', 'error')
      }
    },
    async handleSaveGroup() {
      this.groupSaving = true
      try {
        const res = await saveGroup(this.groupForm.key, {
          name: this.groupForm.name,
          description: this.groupForm.description,
          img_data: this.groupForm.img_data
        })
        showToast(res.data.message || '已儲存', 'success')
        await this.loadGroups()
      } catch (e) {
        showToast(e.response?.data?.message || '儲存失敗', 'error')
      } finally {
        this.groupSaving = false
      }
    },
    async loadMolecules() {
      try {
        const res = await getAdminMolecules()
        this.moleculeList = res.data.molecules || []
      } catch (e) {
        console.error('Failed to load molecules:', e)
      }
    },
    selectMolecule(m) {
      this.lookupResults = []
      this.moleculeQuery = ''
      this.moleculeForm = {
        original_slug: m.slug, name: m.name, iupac_name: m.iupac_name || '',
        formula: m.formula || '', weight: m.weight || '', smiles: m.smiles || '',
        cid: m.cid || null, description: m.description || '',
        category: m.category || '', img_data: m.img_data || '',
        // 舊資料沒存建構器節點時，從分子式反推一份，仍然可以繼續編輯
        nodes: m.nodes?.length ? m.nodes : parseFormula(m.formula),
        source: m.source || 'manual', published: m.published !== false
      }
    },
    newMolecule() {
      this.moleculeForm = EMPTY_MOLECULE()
      this.lookupResults = []
      this.moleculeQuery = ''
    },
    onFormulaChange({ formula }) {
      this.moleculeForm.formula = formula
    },
    async runLookup(params) {
      this.moleculeLooking = true
      this.lookupResults = []
      try {
        const res = await lookupMolecule(params)
        const results = res.data.results || []
        if (!results.length) {
          showToast('PubChem 查不到這個分子，可以手動填寫', 'error')
        } else if (results.length === 1) {
          this.applyLookup(results[0])
        } else {
          this.lookupResults = results
        }
      } catch (e) {
        showToast(e.response?.data?.message || '查詢失敗', 'error')
      } finally {
        this.moleculeLooking = false
      }
    },
    lookupByName() {
      const name = this.moleculeQuery.trim()
      if (!name) return showToast('請先輸入分子名稱', 'error')
      this.runLookup({ name })
    },
    lookupByFormula() {
      const formula = this.moleculeForm.formula
      if (!formula) return showToast('請先用建構器拼出分子式', 'error')
      this.runLookup({ formula })
    },
    applyLookup(r) {
      const f = this.moleculeForm
      f.formula = r.formula || f.formula
      f.weight = r.weight || ''
      f.iupac_name = r.iupac_name || ''
      f.smiles = r.smiles || ''
      f.cid = r.cid || null
      f.source = 'pubchem'
      if (!f.name) f.name = r.iupac_name || r.formula || ''
      // 查詢結果的分子式回填建構器，讓拼出來的內容與 PubChem 一致
      if (r.formula) f.nodes = parseFormula(r.formula)
      this.lookupResults = []
      showToast(`已套用 PubChem CID ${r.cid}`, 'success')
    },
    async onMoleculeImgChange(e) {
      const file = e.target.files[0]
      e.target.value = ''
      if (!file) return
      try {
        // 結構圖多半是去背 PNG，保留透明才不會變成黑塊
        const result = await compressImage(file, { keepTransparency: true })
        this.moleculeForm.img_data = await new Promise((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = () => resolve(reader.result)
          reader.onerror = reject
          reader.readAsDataURL(result.blob)
        })
      } catch (err) {
        showToast(err.message || '圖片處理失敗', 'error')
      }
    },
    async publishMolecule() {
      this.moleculeForm.published = true
      await this.handleSaveMolecule()
    },
    async saveMoleculeDraft() {
      this.moleculeForm.published = false
      await this.handleSaveMolecule()
    },
    async handleSaveMolecule() {
      this.moleculeSaving = true
      try {
        const res = await saveMolecule({ ...this.moleculeForm, slug: this.moleculeForm.original_slug || '' })
        showToast(res.data.message || '已儲存', 'success')
        this.moleculeForm.original_slug = res.data.slug
        await this.loadMolecules()
      } catch (e) {
        showToast(e.response?.data?.message || '儲存失敗', 'error')
      } finally {
        this.moleculeSaving = false
      }
    },
    async handleDeleteMolecule() {
      const slug = this.moleculeForm.original_slug
      if (!slug) return
      this.moleculeSaving = true
      try {
        const res = await deleteMolecule(slug)
        showToast(res.data.message || '已刪除', 'success')
        this.newMolecule()
        await this.loadMolecules()
      } catch (e) {
        showToast(e.response?.data?.message || '刪除失敗', 'error')
      } finally {
        this.moleculeSaving = false
      }
    },
    subscript(formula) {
      return String(formula || '').replace(/\d/g, d => `<sub>${d}</sub>`)
    },
    async loadPageMeta() {
      try {
        const res = await getPageMeta()
        this.pageMetaAll = res.data.meta || {}
      } catch (e) {
        console.error('Failed to load page meta:', e)
      }
    },
    selectMetaKey(key) {
      this.metaKey = key
      const overrides = this.pageMetaAll[key] || {}
      const form = {}
      for (const f of pageMetaDef(key).fields) {
        // 下拉與數字沒有「留空＝用預設」的表現方式，直接帶入預設值
        form[f.name] = overrides[f.name] || (f.type ? f.default : '')
      }
      this.metaForm = form
    },
    async handleSaveMeta() {
      this.metaSaving = true
      try {
        const res = await savePageMeta(this.metaKey, this.metaForm)
        showToast(res.data.message || '已儲存', 'success')
        await this.loadPageMeta()
        // 讓前台立即反映
        await refreshPageMeta()
      } catch (e) {
        showToast(e.response?.data?.message || '儲存失敗', 'error')
      } finally {
        this.metaSaving = false
      }
    },
    async loadPages() {
      try {
        const res = await getAdminPages()
        this.pageList = res.data.pages || []
      } catch (e) {
        console.error('Failed to load pages:', e)
      }
    },
    reloadBuiltinTemplate() {
      // 模板更新是選擇性的：只換編輯框的內容，按發布前不影響線上頁面。
      // 這樣部署更新內建模板時，已編輯的版本不會被悄悄蓋掉（issue #16）
      const b = BUILTIN_PAGES[this.pageForm.slug]
      if (!b) return
      this.pageForm.content = b.content
      this.pageForm.blocks = blocksFrom(b)
      showToast('已載入最新內建模板到編輯框，按發布才會套用；不想要可以重新選取頁面還原', 'success')
    },
    importBuiltin(slug) {
      const b = BUILTIN_PAGES[slug]
      if (!b) return
      this.pageForm = {
        original_slug: '', slug, title: b.title, content: b.content,
        blocks: blocksFrom(b), subtitle: '', seo_description: '',
        // 這兩頁本來就有自己的路由，不需要再出現在導覽列
        nav_position: 'none', nav_order: 0, published: true
      }
      showToast(`已載入「${b.title}」的內建內容，編輯後按發布即可套用`, 'success')
    },
    selectPage(p) {
      this.pageForm = {
        original_slug: p.slug, slug: p.slug, title: p.title,
        subtitle: p.subtitle || '', seo_description: p.seo_description || '',
        // 舊頁面沒有 blocks，用 blocksFrom 把 Markdown 轉成一個區塊帶進來
        blocks: blocksFrom(p),
        content: p.content || '', nav_position: p.nav_position,
        nav_order: p.nav_order, published: p.published
      }
    },
    newPage() {
      this.pageForm = EMPTY_PAGE()
      this.editKind = 'page'
      this.pageMode = 'edit'
    },
    // 清單上按「編輯」：依這一列是哪種頁面決定要開哪個表單
    editRow(row) {
      this.pendingDeletePage = ''
      if (row.kind === 'site') {
        // 首頁文案本來就住在網站設定，這裡只是把入口收進清單
        this.section = 'site'
        return
      }
      if (row.kind === 'meta') {
        this.selectMetaKey(row.key)
        this.editKind = 'meta'
        this.pageMode = 'edit'
        return
      }
      if (row.kind === 'markdown' && !row.saved) {
        // 還沒改過的內建頁，先把內建模板帶進編輯框；按發布才會真的覆寫
        this.importBuiltin(row.key)
      } else {
        this.selectPage(row.saved || row.page)
      }
      this.editKind = 'page'
      this.pageMode = 'edit'
    },
    // 圖庫參照優先；沒有就是自己上傳的圖
    blockImgSrc(data) {
      const ref = data?.image_ref
      if (ref?.library && ref.image) {
        const lib = this.libraryList.find(l => l.id === ref.library)
        const img = lib?.images.find(i => i.id === ref.image)
        if (img) return img.img_data
      }
      return data?.image || ''
    },
    openImagePicker(target) {
      this.imagePickerTarget = target
    },
    pickImage(library, image) {
      // 存參照而不是圖片：圖庫換圖時用到的頁面會跟著更新
      this.imagePickerTarget.image_ref = { library: library.id, image: image.id }
      this.imagePickerTarget.image = ''
      this.imagePickerTarget = null
    },
    clearBlockImage(target) {
      target.image = ''
      delete target.image_ref
    },
    blockLabel(type) {
      return blockType(type)?.label || type
    },
    blockFields(type) {
      return blockType(type)?.fields || []
    },
    addBlock(key) {
      const block = emptyBlock(key)
      if (block) this.pageForm.blocks.push(block)
      this.blockPickerOpen = false
    },
    moveBlock(i, delta) {
      const to = i + delta
      if (to < 0 || to >= this.pageForm.blocks.length) return
      const [b] = this.pageForm.blocks.splice(i, 1)
      this.pageForm.blocks.splice(to, 0, b)
    },
    addItem(list, field) {
      list.push(emptyItem(field))
    },
    moveItem(list, i, delta) {
      const to = i + delta
      if (to < 0 || to >= list.length) return
      const [it] = list.splice(i, 1)
      list.splice(to, 0, it)
    },
    async onBlockImage(e, target, key) {
      const file = e.target.files[0]
      e.target.value = ''
      if (!file) return
      try {
        // 頁面裡的圖不像圖層要去背置中，沿用一般的壓縮就好
        const result = await compressImage(file)
        target[key] = await this.blobToDataUrl(result.blob)
        // 自己上傳就不再跟著圖庫走，否則參照會蓋掉剛上傳的圖
        delete target.image_ref
      } catch (err) {
        showToast(err.message || '圖片處理失敗', 'error')
      }
    },
    backToList() {
      this.pageMode = 'list'
      this.pendingDeletePage = ''
    },
    // 同一個導覽位置內和上／下一頁交換 nav_order
    async movePage(row, delta) {
      const other = delta < 0 ? row.neighbours.up : row.neighbours.down
      if (!other) return

      this.pageSaving = true
      try {
        // nav_order 可能兩頁都是 0（沒排過），直接交換會沒有效果，
        // 所以改成依目前的順序重新編號
        const a = { ...row.page, nav_order: other.nav_order }
        const b = { ...other, nav_order: row.page.nav_order }
        if (a.nav_order === b.nav_order) {
          a.nav_order = delta < 0 ? b.nav_order - 1 : b.nav_order + 1
        }
        await savePage({ ...a, original_slug: a.slug })
        await savePage({ ...b, original_slug: b.slug })
        await this.loadPages()
        await refreshPages()
      } catch (e) {
        showToast(e.response?.data?.message || '排序失敗', 'error')
      } finally {
        this.pageSaving = false
      }
    },
    // 清單上直接刪除，按兩次確認（與電子樣式庫同一套互動）
    async deleteRow(row) {
      if (this.pendingDeletePage !== row.key) {
        this.pendingDeletePage = row.key
        return
      }
      this.pendingDeletePage = ''
      this.pageSaving = true
      try {
        const res = await deletePage(row.key)
        showToast(res.data.message || '已刪除', 'success')
        await this.loadPages()
        await refreshPages()
      } catch (e) {
        showToast(e.response?.data?.message || '刪除失敗', 'error')
      } finally {
        this.pageSaving = false
      }
    },
    async publishPage() {
      this.pageForm.published = true
      await this.handleSavePage()
    },
    async saveAsDraft() {
      this.pageForm.published = false
      await this.handleSavePage()
    },
    async handleSavePage() {
      this.pageSaving = true
      try {
        const res = await savePage(this.pageForm)
        showToast(res.data.message || '已儲存', 'success')
        this.pageForm.original_slug = res.data.slug
        this.pageForm.slug = res.data.slug
        await this.loadPages()
        // 讓前台導覽立即反映
        await refreshPages()
      } catch (e) {
        showToast(e.response?.data?.message || '儲存失敗', 'error')
      } finally {
        this.pageSaving = false
      }
    },
    async loadSiteSettings() {
      try {
        const res = await getAdminSiteSettings()
        this.siteForm = {
          title: res.data.title || '',
          subtitle: res.data.subtitle || '',
          description: res.data.description || '',
          frame_style: res.data.frame_style || 'classic',
          layer_bg: res.data.layer_bg || '#ffffff',
          electron_size: Number(res.data.electron_size) || 24
        }
        this.siteBgCurrent = res.data.bg_image || ''
        this.siteFrameCurrent = res.data.frame_image || ''
      } catch (e) {
        console.error('Failed to load site settings:', e)
      }
    },
    async onSiteBgFileChange(e) {
      this.revokeSiteBgPreview()
      const file = e.target.files[0]
      if (!file) return
      try {
        const result = await compressImage(file)
        this.siteBgBlob = result.blob
        this.siteBgInfo = result
        this.siteBgPreviewUrl = URL.createObjectURL(result.blob)
      } catch (err) {
        showToast(err.message || '圖片處理失敗', 'error')
        e.target.value = ''
      }
    },
    revokeSiteBgPreview() {
      if (this.siteBgPreviewUrl) {
        URL.revokeObjectURL(this.siteBgPreviewUrl)
        this.siteBgPreviewUrl = ''
      }
      this.siteBgBlob = null
      this.siteBgInfo = null
    },
    onSiteFrameFileChange(e) {
      this.revokeSiteFramePreview()
      const file = e.target.files[0]
      if (!file) return
      // 外框圖要保留透明背景，不能走 JPEG 壓縮，只擋過大的檔案
      if (file.size > MAX_UPLOAD_BYTES) {
        showToast(`外框圖 ${formatBytes(file.size)} 超過 ${formatBytes(MAX_UPLOAD_BYTES)} 上限`, 'error')
        e.target.value = ''
        return
      }
      this.siteFrameBlob = file
      this.siteFramePreviewUrl = URL.createObjectURL(file)
    },
    revokeSiteFramePreview() {
      if (this.siteFramePreviewUrl) {
        URL.revokeObjectURL(this.siteFramePreviewUrl)
        this.siteFramePreviewUrl = ''
      }
      this.siteFrameBlob = null
    },
    buildSiteFormData() {
      const formData = new FormData()
      formData.append('title', this.siteForm.title)
      formData.append('subtitle', this.siteForm.subtitle)
      formData.append('description', this.siteForm.description)
      formData.append('frame_style', this.siteForm.frame_style || 'classic')
      formData.append('layer_bg', this.siteForm.layer_bg || '#ffffff')
      formData.append('electron_size', this.siteForm.electron_size || 24)
      return formData
    },
    async handleClearSiteFrame() {
      const formData = this.buildSiteFormData()
      formData.append('clear_frame_image', '1')
      await this.saveSiteSettings(formData)
    },
    async saveSiteSettings(formData) {
      this.siteSaving = true
      try {
        const res = await updateSiteSettings(formData)
        showToast(res.data.message || 'Saved!', 'success')
        await this.loadSiteSettings()
        // 讓 header 與頁面標題立刻反映
        setSiteSettings({ ...this.siteForm, bg_image: this.siteBgCurrent, frame_image: this.siteFrameCurrent })
        if (this.$refs.siteBgInput) this.$refs.siteBgInput.value = ''
        if (this.$refs.siteFrameInput) this.$refs.siteFrameInput.value = ''
        this.revokeSiteBgPreview()
        this.revokeSiteFramePreview()
      } catch (e) {
        showToast(e.response?.data?.message || 'Save failed', 'error')
      } finally {
        this.siteSaving = false
      }
    },
    async handleUpdateSiteSettings() {
      const formData = this.buildSiteFormData()
      if (this.siteBgBlob) formData.append('bg_image', this.siteBgBlob, 'bg.jpg')
      if (this.siteFrameBlob) formData.append('frame_image', this.siteFrameBlob, 'frame.png')
      await this.saveSiteSettings(formData)
    },
    async handleClearSiteBg() {
      const formData = this.buildSiteFormData()
      formData.append('clear_bg_image', '1')
      await this.saveSiteSettings(formData)
    },
    /**
     * 把既有的圖片全部套上浮水印。實際的分批邏輯在 utils/watermarkJobs.js，
     * 與「浮水印」分頁那顆按鈕同一份——這裡只負責顯示進度。
     */
    async handleApplyWatermark() {
      this.adminMsg = ''
      this.watermarkFailures = []
      try {
        const result = await runWatermarkJob('backfill', progress => {
          this.watermarkJob = { ...progress }
        })
        this.adminMsg = result.text
        this.adminMsgType = result.failed ? 'error-msg' : 'success-msg'
        this.watermarkFailures = result.failures
        showToast(result.text, result.failed ? 'error' : 'success')
      } catch (e) {
        this.adminMsg = e.response?.data?.message || 'Error!'
        this.adminMsgType = 'error-msg'
      } finally {
        this.watermarkJob = null
      }
    },
    async handleRebuildCompletion() {
      this.loading = true
      this.adminMsg = ''
      try {
        const res = await rebuildCompletion()
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
        await this.loadStoryData()
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
      if (!this.defaultImgBlob) return
      const formData = new FormData()
      formData.append('image', this.defaultImgBlob, '_default.jpg')
      this.defaultImgSaving = true
      try {
        const res = await updateDefaultImg(formData)
        showToast(res.data.message, 'success')
        await this.loadDefaultImg()
        this.$refs.defaultImgInput.value = ''
        this.revokeDefaultImgPreview()
      } catch (e) {
        showToast(e.response?.data?.message || 'Upload failed', 'error')
      } finally {
        this.defaultImgSaving = false
      }
    },
    platformInfo,
    setSection(key) {
      this.section = key
      localStorage.setItem('adminSection', key)
      this.adminMsg = ''
    },
    addLink() {
      const used = new Set(this.creatorLinks.map(l => l.platform))
      const next = PLATFORMS.find(p => !used.has(p.key)) || PLATFORMS[0]
      this.creatorLinks.push({ platform: next.key, label: next.label, url: '', color: '', avatar: '' })
    },
    removeLink(i) {
      this.creatorLinks.splice(i, 1)
    },
    moveLink(i, delta) {
      const target = i + delta
      if (target < 0 || target >= this.creatorLinks.length) return
      const [item] = this.creatorLinks.splice(i, 1)
      this.creatorLinks.splice(target, 0, item)
    },
    onPlatformChange(link) {
      // 顯示名稱還是預設值時，跟著平台一起換；使用者自訂過就不動它
      const isDefaultLabel = PLATFORMS.some(p => p.label === link.label)
      if (!link.label || isDefaultLabel) link.label = platformInfo(link.platform).label
    },
    async onAvatarChange(e, link) {
      const file = e.target.files[0]
      e.target.value = ''
      if (!file) return
      try {
        // 頭像顯示尺寸很小，壓縮流程已足夠，不需要另外裁切
        const result = await compressImage(file)
        link.avatar = await new Promise((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = () => resolve(reader.result)
          reader.onerror = reject
          reader.readAsDataURL(result.blob)
        })
      } catch (err) {
        showToast(err.message || '頭像處理失敗', 'error')
      }
    },
    async loadCreatorLinks() {
      try {
        const res = await getAdminCreatorLinks()
        this.creatorLinks = (res.data.links || []).map(l => ({
          platform: l.platform || 'website',
          label: l.label || '',
          url: l.url || '',
          color: l.color || '',
          avatar: l.avatar || ''
        }))
        this.creatorMeta = {
          description: res.data.description || '',
          avatar_shape: res.data.avatar_shape || 'circle'
        }
      } catch (e) {
        console.error('Failed to load creator links:', e)
      }
    },
    async handleUpdateCreatorLinks() {
      const links = this.creatorLinks
        .filter(l => (l.url || '').trim())
        .map(l => ({
          platform: l.platform,
          label: (l.label || '').trim() || platformInfo(l.platform).label,
          url: l.url.trim(),
          color: l.color || '',
          avatar: l.avatar || ''
        }))
      const payload = { ...this.creatorMeta, links }
      this.creatorLinksSaving = true
      try {
        const res = await updateCreatorLinks(payload)
        showToast(res.data.message || 'Saved!', 'success')
        // 讓頁尾與 /links 立刻反映這次儲存的結果
        setCreatorLinks(payload)
      } catch (e) {
        showToast(e.response?.data?.message || 'Save failed', 'error')
      } finally {
        this.creatorLinksSaving = false
      }
    },
    async loadStoryData() {
      try {
        const res = await getStoryData()
        this.elements = res.data.elements || []
        this.storyDatas = res.data.storyDatas || {}
        this.draftDatas = res.data.draftDatas || {}
        this.elementConfigs = res.data.configurations || {}
        this.imageDatas = res.data.imageDatas || {}
        this.hasImageMap = res.data.hasImage || {}
        if (this.elements.length > 0) {
          this.selectedSymbol = this.elements[0]
          this.storyText = this.storyDatas[this.selectedSymbol] || ''
          this.loadGallery()
          this.loadLayers()
        } else {
          showToast('元素清單為空，請先執行 Update DB', 'warning')
        }
      } catch (e) {
        console.error('Failed to load story data:', e)
        showToast('無法載入元素清單：' + (e.message || 'Network error'), 'error')
      }
    },
    onSymbolChange() {
      // 有未發布的草稿就優先帶出來，避免使用者以為之前寫的東西不見了
      this.storyText = this.draftDatas[this.selectedSymbol]
        || this.storyDatas[this.selectedSymbol] || ''
      this.elementLoading = true
      Promise.all([this.loadGallery(), this.loadLayers()])
        .finally(() => { this.elementLoading = false })
      // AI 的方向、參考資料與建議都是針對前一個元素寫的，換元素時一併清掉，
      // 否則會把上一個元素的設定帶到下一個
      this.revokeImagePreview()
      if (this.$refs.imageInput) this.$refs.imageInput.value = ''
    },
    // ── 圖片分層 ──
    async loadLayers() {
      if (!this.selectedSymbol) return
      try {
        const res = await getAdminLayers(this.selectedSymbol)
        this.layerForm = {
          nucleus: res.data.nucleus || '',
          name_img: res.data.name_img || '',
          electron_style: res.data.electron_style || ''
        }
      } catch (e) {
        console.error('Failed to load layers:', e)
      }
    },
    async onLayerFile(e, field) {
      const file = e.target.files[0]
      e.target.value = ''
      if (!file) return
      try {
        // 圖層要疊在彼此之上，必須保留透明；PNG 壓不掉多少，尺寸給小一點
        const result = await compressImage(file, { keepTransparency: true, maxEdge: 900 })
        this.layerForm[field] = await this.blobToDataUrl(result.blob)
        this.layerErrors[field] = ''
      } catch (err) {
        showToast(err.message || '圖片處理失敗', 'error')
      }
    },
    blobToDataUrl(blob) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result)
        reader.onerror = reject
        reader.readAsDataURL(blob)
      })
    },
    onLayerImgError(field) {
      // 顯示不出來多半是資料在儲存時被截斷，直接清掉並提示重傳
      this.layerErrors[field] = '圖片損毀，請重新上傳'
      this.layerForm[field] = ''
      showToast('圖層圖片載入失敗，請重新上傳', 'error')
    },
    async handleSaveLayers() {
      this.layerSaving = true
      try {
        const res = await updateLayers(this.selectedSymbol, this.layerForm)
        showToast(res.data.message || '已儲存', 'success')
      } catch (e) {
        showToast(e.response?.data?.message || '儲存失敗', 'error')
      } finally {
        this.layerSaving = false
      }
    },
    // ── 通用圖庫 ──
    async loadLibraries() {
      try {
        const res = await getLibraries()
        this.libraryList = res.data.libraries || []
        this.bindable = res.data.bindable || []
        this.libraryMax = res.data.max_images || 12
      } catch (e) {
        console.error('Failed to load libraries:', e)
      }
    },
    bindLabel(lib) {
      const def = this.bindable.find(b => b.key === lib.bind_type)
      const label = def?.label || lib.bind_type
      return lib.bind_id ? `${label}：${lib.bind_id}` : label
    },
    newLibrary() {
      const first = this.bindable[0]?.key || 'particle'
      this.libraryForm = { id: '', name: '', bind_type: first, bind_id: '', default_image: '', images: [] }
      this.pendingDeleteLibrary = ''
      this.loadBindTargets(first)
    },
    selectLibrary(lib) {
      // 深拷貝：編輯中途取消不該影響清單上的資料
      this.libraryForm = JSON.parse(JSON.stringify(lib))
      this.pendingDeleteLibrary = ''
      this.loadBindTargets(lib.bind_type)
    },
    onBindTypeChange() {
      // 換了類型，原本綁的對象一定不適用
      this.libraryForm.bind_id = ''
      this.loadBindTargets(this.libraryForm.bind_type)
    },
    async loadBindTargets(bindType) {
      const def = this.bindable.find(b => b.key === bindType)
      if (!def?.needs_target) {
        this.bindTargets = []
        return
      }
      try {
        const res = await getBindableTargets(bindType)
        this.bindTargets = res.data.targets || []
      } catch (e) {
        console.error('Failed to load bindable targets:', e)
        this.bindTargets = []
      }
    },
    async onLibraryImages(e) {
      const files = [...e.target.files]
      e.target.value = ''
      const room = this.libraryMax - this.libraryForm.images.length
      if (files.length > room) showToast(`最多再加 ${room} 張，多的已略過`, 'error')

      for (const file of files.slice(0, room)) {
        try {
          // 與電子樣式同一套處理：裁掉透明邊距並置中，不同來源的圖疊起來才一致
          const result = await normalizeSprite(file, { size: 240 })
          this.libraryForm.images.push({
            id: '',
            name: file.name.replace(/\.[^.]+$/, ''),
            img_data: await this.blobToDataUrl(result.blob)
          })
        } catch (err) {
          showToast(err.message || '圖片處理失敗', 'error')
        }
      }
    },
    async handleSaveLibrary() {
      this.librarySaving = true
      try {
        const res = await saveLibrary(this.libraryForm)
        showToast(res.data.message || '已儲存', 'success')
        this.libraryForm = null
        await this.loadLibraries()
      } catch (e) {
        showToast(e.response?.data?.message || '儲存失敗', 'error')
      } finally {
        this.librarySaving = false
      }
    },
    async handleDeleteLibrary(lib) {
      if (this.pendingDeleteLibrary !== lib.id) {
        this.pendingDeleteLibrary = lib.id
        setTimeout(() => {
          if (this.pendingDeleteLibrary === lib.id) this.pendingDeleteLibrary = ''
        }, 4000)
        return
      }
      this.pendingDeleteLibrary = ''
      try {
        const res = await deleteLibrary(lib.id)
        showToast(res.data.message || '已刪除', 'success')
        if (this.libraryForm?.id === lib.id) this.libraryForm = null
        await this.loadLibraries()
      } catch (e) {
        showToast(e.response?.data?.message || '刪除失敗', 'error')
      }
    },
    // bindType 決定搬哪一類；reload 是搬完要重抓的清單
    async handleMigrateInto(bindType, reload) {
      this.migratingInto = bindType
      try {
        const res = await migrateIntoLibraries(bindType)
        showToast(res.data.message || '已搬移', 'success')
        await this.loadLibraries()
        await reload()
      } catch (e) {
        showToast(e.response?.data?.message || '搬移失敗', 'error')
      } finally {
        this.migratingInto = ''
      }
    },
    async handleMigrateGalleries() {
      this.migratingGallery = true
      try {
        const res = await migrateGalleries()
        showToast(res.data.message || '已搬移', 'success')
        await this.loadLibraries()
        await this.loadGallery()
      } catch (e) {
        showToast(e.response?.data?.message || '搬移失敗', 'error')
      } finally {
        this.migratingGallery = false
      }
    },
    async handleMigrateElectrons() {
      this.migrating = true
      try {
        const res = await migrateElectronStyles()
        showToast(res.data.message || '已搬移', 'success')
        await this.loadLibraries()
      } catch (e) {
        showToast(e.response?.data?.message || '搬移失敗', 'error')
      } finally {
        this.migrating = false
      }
    },
    // ── 電子樣式庫 ──
    async loadElectronStyles() {
      try {
        const res = await getElectronStyles()
        this.electronStyles = res.data.styles || []
        this.defaultStyleId = res.data.default_id || ''
      } catch (e) {
        console.error('Failed to load electron styles:', e)
      }

      try {
        const res = await getElectronMotion()
        this.motion = res.data.motion || 'orbit'
      } catch (e) {
        console.error('Failed to load electron motion:', e)
      }
    },
    async onStyleFile(e) {
      const file = e.target.files[0]
      if (!file) return
      try {
        // 自動裁掉透明邊距並置中到正方形，否則不同來源的 PNG 疊上去
        // 大小會差很多
        const result = await normalizeSprite(file, { size: 240 })
        this.newStyleImg = await this.blobToDataUrl(result.blob)
        this.newStyleInfo = result
        if (!this.newStyleName) this.newStyleName = file.name.replace(/\.[^.]+$/, '')
      } catch (err) {
        showToast(err.message || '圖片處理失敗', 'error')
      }
    },
    async handleSaveStyle() {
      this.styleSaving = true
      try {
        const res = await saveElectronStyle({ name: this.newStyleName, img_data: this.newStyleImg })
        showToast(res.data.message || '已新增', 'success')
        this.newStyleName = ''
        this.newStyleImg = ''
        this.newStyleInfo = null
        if (this.$refs.styleInput) this.$refs.styleInput.value = ''
        await this.loadElectronStyles()
      } catch (e) {
        showToast(e.response?.data?.message || '新增失敗', 'error')
      } finally {
        this.styleSaving = false
      }
    },
    async toggleDefaultStyle(style) {
      const next = this.defaultStyleId === style.id ? '' : style.id
      try {
        const res = await setDefaultElectronStyle(next)
        showToast(res.data.message || '已更新', 'success')
        this.defaultStyleId = next
      } catch (e) {
        showToast(e.response?.data?.message || '設定失敗', 'error')
      }
    },
    async handleDeleteStyle(style) {
      // 第一次點只是進入確認狀態，避免手滑刪掉畫好的素材
      if (this.pendingDeleteStyle !== style.id) {
        this.pendingDeleteStyle = style.id
        setTimeout(() => {
          if (this.pendingDeleteStyle === style.id) this.pendingDeleteStyle = ''
        }, 4000)
        return
      }
      this.pendingDeleteStyle = ''
      try {
        const res = await deleteElectronStyle(style.id)
        showToast(res.data.message || '已刪除', 'success')
        // 有元素正在用這個樣式的話，選取狀態一併清掉
        if (this.layerForm.electron_style === style.id) this.layerForm.electron_style = ''
        if (this.defaultStyleId === style.id) this.defaultStyleId = ''
        await this.loadElectronStyles()
      } catch (e) {
        showToast(e.response?.data?.message || '刪除失敗', 'error')
      }
    },
    async handleSaveMotion(value) {
      if (value === this.motion || this.motionSaving) return
      const previous = this.motion
      this.motion = value
      this.motionSaving = true
      try {
        const res = await setElectronMotion(value)
        if (res.data.result === 'success') {
          showToast(res.data.message, 'success')
        } else {
          this.motion = previous
          showToast(res.data.message || '儲存失敗', 'error')
        }
      } catch (e) {
        this.motion = previous
        showToast(e.response?.data?.message || '儲存失敗', 'error')
      } finally {
        this.motionSaving = false
      }
    },
    loadDraft() {
      this.storyText = this.draftDatas[this.selectedSymbol] || ''
      showToast('已載入草稿，按「發布」才會對外顯示', 'success')
    },
    loadPublished() {
      this.storyText = this.storyDatas[this.selectedSymbol] || ''
    },
    async handleSaveStoryDraft() {
      const formData = new FormData()
      formData.append('symbol', this.selectedSymbol)
      formData.append('stroy', this.storyText)
      formData.append('draft', '1')
      this.loading = true
      try {
        const res = await updateStory(formData)
        showToast(res.data.message || '草稿已儲存', 'success')
        this.draftDatas[this.selectedSymbol] = this.storyText
      } catch (e) {
        showToast(e.response?.data?.message || '儲存失敗', 'error')
      } finally {
        this.loading = false
      }
    },
    async handleUpdateStory() {
      const formData = new FormData()
      formData.append('symbol', this.selectedSymbol)
      formData.append('stroy', this.storyText)
      const imageBlob = this.newImageBlob
      if (imageBlob) formData.append('image', imageBlob, `${this.selectedSymbol}.jpg`)
      this.loading = true
      try {
        const res = await updateStory(formData)
        showToast(res.data.message || 'Saved!', 'success')
        this.storyDatas[this.selectedSymbol] = this.storyText
        // 已正式發布，草稿不再需要
        delete this.draftDatas[this.selectedSymbol]
        // 讓下拉選單的完成度標記立即反映這次儲存的結果
        if (imageBlob) this.hasImageMap[this.selectedSymbol] = true
        if (this.$refs.imageInput) this.$refs.imageInput.value = ''
        this.revokeImagePreview()
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

.login-google-row {
  display: flex;
  justify-content: center;
}

/* Google 按鈕在上、帳密在下，兩者之間留白 */
.login-google-row + .alt-login-toggle,
.login-google-row + form {
  margin-top: 14px;
}

/* 次要入口做成文字連結的樣子，不要跟主要的 Google 按鈕搶視覺重量 */
.alt-login-toggle {
  display: inline-block;
  border: none;
  background: none;
  padding: 4px 8px;
  font-size: 13px;
  font-family: 'Space Grotesk', sans-serif;
  color: rgba(228, 251, 255, 0.5);
  text-decoration: underline;
  text-underline-offset: 3px;
  cursor: pointer;
  transition: color 0.2s;
}

.alt-login-toggle:hover {
  color: rgba(228, 251, 255, 0.85);
}

/* ── 後台版面：側邊導覽 + 內容區 ── */
.admin-layout {
  display: grid;
  grid-template-columns: 190px 1fr;
  gap: 20px;
  max-width: 1080px;
  margin: 0 auto;
  padding: 20px 18px 40px;
  align-items: start;
}

.admin-nav {
  position: sticky;
  top: 88px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 14px 10px;
  border: 1px solid rgba(228, 251, 255, 0.1);
  border-radius: 10px;
  background: rgba(20, 5, 35, 0.5);
}

.nav-title {
  font-size: 12px;
  letter-spacing: 0.2em;
  color: rgba(228, 251, 255, 0.35);
  margin: 0 0 10px;
  padding: 0 10px;
  text-align: left;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 9px 11px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: rgba(228, 251, 255, 0.62);
  font-family: inherit;
  font-size: 14px;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.nav-item:hover {
  background: rgba(228, 251, 255, 0.07);
  color: rgba(228, 251, 255, 0.92);
}

.nav-item.active {
  background: rgba(228, 251, 255, 0.15);
  color: #e4fbff;
  font-weight: 600;
}

.nav-icon {
  width: 16px;
  text-align: center;
  opacity: 0.8;
  flex-shrink: 0;
}

.nav-logout {
  margin-top: 10px;
  padding-top: 13px;
  border-top: 1px solid rgba(228, 251, 255, 0.1);
  border-radius: 0 0 7px 7px;
  color: rgba(228, 251, 255, 0.4);
}

.nav-logout:hover {
  color: #ff6b6b;
  background: rgba(255, 107, 107, 0.1);
}

.admin-content {
  min-width: 0;
}

.content-title {
  font-size: 13px;
  letter-spacing: 0.16em;
  color: rgba(228, 251, 255, 0.4);
  margin: 0 0 10px;
  text-align: left;
}

.admin-content .box {
  margin-bottom: 0;
}

@media (max-width: 760px) {
  .admin-layout {
    grid-template-columns: 1fr;
    gap: 14px;
    padding: 14px 10px 32px;
  }

  .admin-nav {
    position: static;
    flex-direction: row;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
    padding: 8px;
  }

  .nav-title { display: none; }

  /* 改為換行而不是橫向捲動：七個功能全部一次看得到，
     不必左右滑才知道後面還有什麼 */
  .nav-list {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 4px;
    flex: 1;
  }

  .nav-item {
    width: auto;
    white-space: nowrap;
    padding: 7px 12px;
    font-size: 13px;
  }

  .nav-logout {
    margin-top: 0;
    padding-top: 7px;
    border-top: none;
    border-left: 1px solid rgba(228, 251, 255, 0.1);
    border-radius: 7px;
    margin-left: 4px;
    padding-left: 12px;
  }

  /* 編輯區與即時預覽並排在手機上各剩不到半欄，改為上下排列 */
  .page-editor {
    grid-template-columns: 1fr;
  }

  .page-form-row {
    grid-template-columns: 1fr;
    gap: 0;
  }
}

/* 更窄的螢幕：選單再縮一級，圖示與文字都收小 */
@media (max-width: 480px) {
  .admin-layout { padding: 10px 8px 28px; }
  .admin-nav { padding: 6px; gap: 3px; }
  .nav-item { padding: 6px 9px; font-size: 12px; gap: 6px; }
  .nav-icon { width: 13px; }
  .admin-content .box { padding: 16px 14px; }
  .content-title { font-size: 12px; }
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

/* Bulma 是淺色主題，.title 與 .label 的預設字色是深灰（rgb(46,51,61)），
   套在這個深色後台上對比只有 1.54，幾乎看不見。整個後台一起覆寫。 */
.title {
  color: #e4fbff;
}

.label {
  color: rgba(228, 251, 255, 0.82);
}

.desc {
  font-size: 13px;
  opacity: 0.62;
  margin: 2px 0 14px;
  line-height: 1.5;
}

/* ── Creator links 動態列 ── */
.link-head {
  display: grid;
  grid-template-columns: 130px 150px 1fr;
  gap: 8px;
  padding: 0 0 6px;
  margin-right: 100px;
  font-size: 11px;
  letter-spacing: 0.08em;
  color: rgba(228, 251, 255, 0.4);
  border-bottom: 1px solid rgba(228, 251, 255, 0.1);
}

.link-row {
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(228, 251, 255, 0.07);
}

/* 頭像與自訂色：放在該連結底下的第二行 */
.link-extras {
  flex-basis: 100%;
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
  padding-left: 2px;
}

.link-avatar {
  display: flex;
  align-items: center;
  gap: 7px;
}

.avatar-preview {
  display: block;
  width: 32px;
  height: 32px;
  overflow: hidden;
  flex-shrink: 0;
  border: 1px solid rgba(228, 251, 255, 0.25);
}

.avatar-preview--circle { border-radius: 50%; }
.avatar-preview--square { border-radius: 6px; }

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border: none;
  border-radius: 0;
  display: block;
}

.avatar-empty {
  font-size: 11px;
  color: rgba(228, 251, 255, 0.3);
  width: 32px;
  text-align: center;
}

.avatar-input {
  margin: 0;
  font-size: 11px;
  max-width: 190px;
}

.link-color {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(228, 251, 255, 0.55);
}

.link-color input[type="color"] {
  width: 30px;
  height: 24px;
  padding: 0;
  border: 1px solid rgba(228, 251, 255, 0.25);
  border-radius: 5px;
  background: transparent;
  cursor: pointer;
}

.reset-color {
  font-size: 11px;
  padding: 2px 8px;
  border: 1px solid rgba(228, 251, 255, 0.2);
  border-radius: 999px;
  background: transparent;
  color: rgba(228, 251, 255, 0.5);
  font-family: inherit;
  cursor: pointer;
}

.reset-color:hover {
  color: #e4fbff;
  border-color: rgba(228, 251, 255, 0.5);
}

/* 頭像形狀選擇 */
.shape-picker {
  display: flex;
  gap: 8px;
  margin: 4px 0 14px;
}

.shape-option {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 14px;
  border: 1px solid rgba(228, 251, 255, 0.18);
  border-radius: 8px;
  background: transparent;
  color: rgba(228, 251, 255, 0.6);
  font-family: inherit;
  font-size: 13px;
  cursor: pointer;
}

.shape-option.active {
  border-color: #6ee76e;
  background: rgba(110, 231, 110, 0.1);
  color: #e4fbff;
}

.shape-demo {
  width: 16px;
  height: 16px;
  background: rgba(228, 251, 255, 0.45);
  display: inline-block;
}

.shape-demo--circle { border-radius: 50%; }
.shape-demo--square { border-radius: 4px; }

.link-row:last-of-type {
  border-bottom: none;
}

.link-row-fields {
  flex: 1;
  display: grid;
  grid-template-columns: 130px 150px 1fr;
  gap: 8px;
  min-width: 0;
}

.link-row-fields .input,
.link-row-fields .select {
  margin: 0;
}

.link-row-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
  padding-top: 2px;
}

.icon-button {
  width: 28px;
  height: 30px;
  border: 1px solid rgba(228, 251, 255, 0.2);
  border-radius: 5px;
  background: rgba(228, 251, 255, 0.05);
  color: rgba(228, 251, 255, 0.7);
  cursor: pointer;
  font-size: 13px;
  line-height: 1;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.icon-button:hover:not(:disabled) {
  background: rgba(228, 251, 255, 0.15);
  border-color: rgba(228, 251, 255, 0.45);
  color: #e4fbff;
}

.icon-button:disabled {
  opacity: 0.25;
  cursor: not-allowed;
}

.icon-button.confirming {
  width: auto;
  padding: 0 8px;
  font-size: 11px;
  background: rgba(255, 107, 107, 0.25);
  border-color: rgba(255, 107, 107, 0.7);
  color: #ff6b6b;
}

.icon-button.danger:hover:not(:disabled) {
  background: rgba(255, 107, 107, 0.18);
  border-color: rgba(255, 107, 107, 0.6);
  color: #ff6b6b;
}

.link-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 14px;
}

@media (max-width: 700px) {
  .link-row-fields {
    grid-template-columns: 1fr;
  }
  /* 單欄排列時欄位標題對不上，改在列內用 aria-label 辨識 */
  .link-head {
    display: none;
  }
}

.progress-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  opacity: 0.75;
  margin: 0 0 14px;
  padding: 8px 12px;
  border: 1px solid rgba(228, 251, 255, 0.12);
  border-radius: 6px;
  background: rgba(228, 251, 255, 0.04);
}

.progress-summary strong {
  color: #6ee76e;
  font-weight: 600;
}

.progress-divider {
  opacity: 0.35;
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

.img-compare {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
  margin: 10px 0 4px;
}

.img-slot {
  min-width: 0;
}

.img-slot--new .img-preview {
  border-color: rgba(110, 231, 110, 0.55);
}

.preview-label {
  font-size: 12px;
  opacity: 0.5;
  margin: 4px 0 2px;
}

.preview-new {
  margin: 4px 0 10px;
}

/* ── AI 故事協助 ── */
.site-desc {
  min-height: 60px;
}

/* ── 圖片分層 ── */
.layer-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin: 10px 0 14px;
}

.layer-slot {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px;
  border: 1px solid rgba(228, 251, 255, 0.12);
  border-radius: 8px;
  background: rgba(3, 1, 12, 0.4);
}

.layer-slot > img {
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: contain;
  border: none;
  border-radius: 5px;
  background: rgba(60, 40, 75, 0.35);
}

.layer-slot .input { margin: 0; font-size: 11px; }

/* 圖層的空狀態要能正常斷行；.avatar-empty 是社群頭像佔位用的，寬度寫死 32px */
.layer-empty {
  font-size: 12px;
  color: rgba(228, 251, 255, 0.35);
  line-height: 1.6;
  margin: 0;
  padding: 14px 4px;
  text-align: center;
}
.layer-slot .select { margin: 0; }

.electron-picker {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  padding: 6px 0;
}

.electron-option {
  width: 42px;
  height: 42px;
  padding: 4px;
  border: 1px solid rgba(228, 251, 255, 0.18);
  border-radius: 8px;
  background: rgba(60, 40, 75, 0.35);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.electron-option:hover { border-color: rgba(228, 251, 255, 0.5); }

.electron-option.active {
  border-color: #6ee76e;
  background: rgba(110, 231, 110, 0.15);
}

.electron-option img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border: none;
  border-radius: 0;
  display: block;
}

/* ── 全站電子運動方式 ── */
.motion-picker {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 10px;
  margin: 10px 0 22px;
}

.motion-option {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 14px;
  text-align: left;
  border: 1px solid rgba(228, 251, 255, 0.12);
  border-radius: 8px;
  background: rgba(228, 251, 255, 0.03);
  color: inherit;
  cursor: pointer;
}

.motion-option:hover:not(:disabled) { border-color: rgba(228, 251, 255, 0.3); }
.motion-option:disabled { cursor: default; opacity: 0.6; }

.motion-option.active {
  border-color: #6ee76e;
  background: rgba(110, 231, 110, 0.08);
}

.motion-name { font-size: 14px; font-weight: bold; }
.motion-desc { font-size: 12px; opacity: 0.7; line-height: 1.5; }

/* ── 電子樣式庫 ── */
.style-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
  margin: 10px 0 18px;
}

.style-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 10px;
  border: 1px solid rgba(228, 251, 255, 0.12);
  border-radius: 8px;
  background: rgba(3, 1, 12, 0.4);
}

.style-item img {
  width: 56px;
  height: 56px;
  object-fit: contain;
  border: none;
  border-radius: 0;
}

.style-item.broken { border-color: rgba(255, 107, 107, 0.5); }
.style-item.is-default { border-color: #6ee76e; background: rgba(110, 231, 110, 0.08); }

.style-actions { display: flex; align-items: center; gap: 5px; }

.style-default-btn {
  padding: 2px 9px;
  font-size: 11px;
  font-family: inherit;
  border: 1px solid rgba(228, 251, 255, 0.2);
  border-radius: 999px;
  background: transparent;
  color: rgba(228, 251, 255, 0.5);
  cursor: pointer;
  white-space: nowrap;
}

.style-default-btn:hover { color: #e4fbff; border-color: rgba(228, 251, 255, 0.5); }
.style-default-btn.active { color: #6ee76e; border-color: rgba(110, 231, 110, 0.6); }

.electron-option { position: relative; }

/* 電子是去背 PNG，配個底色才看得清楚 */
.sprite-preview {
  max-width: 90px;
  background:
    linear-gradient(45deg, rgba(228,251,255,0.06) 25%, transparent 25%, transparent 75%, rgba(228,251,255,0.06) 75%),
    linear-gradient(45deg, rgba(228,251,255,0.06) 25%, transparent 25%, transparent 75%, rgba(228,251,255,0.06) 75%);
  background-size: 12px 12px;
  background-position: 0 0, 6px 6px;
}

.electron-default-mark {
  position: absolute;
  top: -5px;
  right: -3px;
  font-size: 10px;
  color: #6ee76e;
}

.broken-tag {
  display: block;
  font-size: 10px;
  color: #ff6b6b;
  margin-top: 2px;
}

.style-name {
  font-size: 12px;
  color: rgba(228, 251, 255, 0.7);
  text-align: center;
  word-break: break-word;
}

.style-upload {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 10px;
  margin: 4px 0;
}

@media (max-width: 700px) {
  .style-upload { grid-template-columns: 1fr; }
}

/* ── 全站電子運動方式 ── */
.motion-picker {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 10px;
  margin: 10px 0 22px;
}

.motion-option {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 14px;
  text-align: left;
  border: 1px solid rgba(228, 251, 255, 0.12);
  border-radius: 8px;
  background: rgba(228, 251, 255, 0.03);
  color: inherit;
  cursor: pointer;
}

.motion-option:hover:not(:disabled) { border-color: rgba(228, 251, 255, 0.3); }
.motion-option:disabled { cursor: default; opacity: 0.6; }

.motion-option.active {
  border-color: #6ee76e;
  background: rgba(110, 231, 110, 0.08);
}

.motion-name { font-size: 14px; font-weight: bold; }
.motion-desc { font-size: 12px; opacity: 0.7; line-height: 1.5; }

/* ── 頁面區塊編輯器 ── */
.blocks-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin: 18px 0 8px;
}

.blocks-head .label { margin: 0; }

.block-picker {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 10px;
  margin-bottom: 16px;
  padding: 12px;
  border: 1px solid rgba(157, 140, 255, 0.28);
  border-radius: 8px;
  background: rgba(90, 70, 160, 0.1);
}

.block-type {
  display: grid;
  grid-template-columns: 28px 1fr;
  grid-template-rows: auto auto;
  gap: 2px 8px;
  padding: 10px 12px;
  text-align: left;
  border: 1px solid rgba(228, 251, 255, 0.12);
  border-radius: 8px;
  background: rgba(228, 251, 255, 0.03);
  color: inherit;
  cursor: pointer;
}

.block-type:hover { border-color: rgba(228, 251, 255, 0.35); }

.block-type-icon {
  grid-row: 1 / 3;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: rgba(228, 251, 255, 0.6);
}

.block-type-name { font-size: 14px; font-weight: bold; }
.block-type-desc { font-size: 12px; opacity: 0.65; line-height: 1.5; }

.block-card {
  margin-bottom: 12px;
  padding: 12px 14px;
  border: 1px solid rgba(228, 251, 255, 0.12);
  border-radius: 8px;
  background: rgba(3, 1, 12, 0.35);
}

.block-card-head,
.block-list-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.block-index {
  min-width: 22px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(228, 251, 255, 0.12);
  font-size: 12px;
  text-align: center;
}

.block-name { flex: 1; font-weight: bold; color: #e4fbff; }
.block-actions { display: flex; gap: 4px; }

.block-field { margin-bottom: 10px; }
.block-field .label { font-size: 12px; }

.block-image {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.block-image img {
  width: 72px;
  height: 72px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid rgba(228, 251, 255, 0.14);
}

.block-image .input { flex: 1; min-width: 180px; }

.block-list-item {
  margin-bottom: 10px;
  padding: 10px 12px;
  border: 1px solid rgba(228, 251, 255, 0.1);
  border-radius: 6px;
  background: rgba(228, 251, 255, 0.03);
}

.picker-group { margin-bottom: 12px; }

.picker-image {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.picker-image img {
  width: 64px;
  height: 64px;
  object-fit: contain;
}

/* ── 元素故事草稿 ── */
.draft-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin: 10px 0 4px;
  padding: 9px 13px;
  border: 1px solid rgba(255, 196, 107, 0.35);
  border-radius: 7px;
  background: rgba(255, 196, 107, 0.08);
  font-size: 13px;
  color: rgba(255, 196, 107, 0.9);
}

.draft-link {
  border: none;
  background: none;
  padding: 0;
  font-family: inherit;
  font-size: 13px;
  color: #ffc46b;
  text-decoration: underline;
  text-underline-offset: 2px;
  cursor: pointer;
}

.draft-link:hover { color: #fff; }

/* ── 頁面管理 ── */
.page-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin: 4px 0 18px;
}

.page-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 3px;
  padding: 9px 14px;
  border: 1px solid rgba(228, 251, 255, 0.14);
  border-radius: 8px;
  background: transparent;
  font-family: inherit;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.page-item:hover {
  border-color: rgba(228, 251, 255, 0.4);
  background: rgba(228, 251, 255, 0.05);
}

.page-item.active {
  border-color: #6ee76e;
  background: rgba(110, 231, 110, 0.1);
}

.page-item-title {
  font-size: 14px;
  color: rgba(228, 251, 255, 0.9);
}

.page-item-meta {
  font-size: 11px;
  color: rgba(228, 251, 255, 0.4);
  display: flex;
  align-items: center;
  gap: 6px;
}

.draft-tag {
  color: #ffc46b;
  border: 1px solid rgba(255, 196, 107, 0.4);
  border-radius: 999px;
  padding: 0 6px;
}

.page-item--new {
  justify-content: center;
  color: rgba(228, 251, 255, 0.6);
  font-size: 13px;
  border-style: dashed;
}

.page-form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.page-editor {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin: 4px 0 6px;
}

.page-content {
  min-height: 340px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 13px;
  line-height: 1.7;
  margin: 0;
}

.page-preview {
  padding: 12px 14px;
  border: 1px solid rgba(228, 251, 255, 0.12);
  border-radius: 6px;
  background: rgba(3, 1, 12, 0.35);
  max-height: 420px;
  overflow-y: auto;
}

.md-help {
  padding: 12px 14px;
  margin: 0 0 10px;
  border: 1px solid rgba(157, 140, 255, 0.25);
  border-radius: 8px;
  background: rgba(90, 70, 160, 0.12);
  font-size: 12px;
  line-height: 1.8;
  color: rgba(228, 251, 255, 0.72);
}

.md-help p { margin: 0 0 8px; }
.md-help p:last-child { margin-bottom: 0; }

.md-help code {
  font-size: 12px;
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(3, 1, 12, 0.6);
}

.md-help pre {
  margin: 0 0 8px;
  padding: 10px 12px;
  border-radius: 6px;
  background: rgba(3, 1, 12, 0.6);
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
}

@media (max-width: 860px) {
  .page-form-row,
  .page-editor {
    grid-template-columns: 1fr;
  }
  .page-preview { max-height: 300px; }
}

/* ── 其他樣貌管理 ── */
.gallery-admin {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid rgba(228, 251, 255, 0.1);
}

.gallery-admin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
  margin: 10px 0 14px;
}

.gallery-admin-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px;
  border: 1px solid rgba(228, 251, 255, 0.12);
  border-radius: 8px;
  background: rgba(3, 1, 12, 0.4);
}

.gallery-admin-item img {
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border-radius: 5px;
  border: none;
}

.gallery-caption {
  margin: 0;
  font-size: 12px;
  padding: 4px 7px;
}

.gallery-admin-actions {
  display: flex;
  gap: 4px;
  justify-content: center;
}

/* ── 電子大小 ── */
.size-picker {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin: 4px 0 14px;
}

.size-picker input[type="range"] { flex: 1; min-width: 140px; max-width: 220px; }

.size-value {
  font-size: 13px;
  color: rgba(228, 251, 255, 0.8);
  font-variant-numeric: tabular-nums;
  min-width: 38px;
}

/* 即時預覽：白底方塊上一顆原子核與一顆電子 */
.size-demo {
  position: relative;
  width: 74px;
  height: 74px;
  border-radius: 6px;
  background: #fff;
  flex-shrink: 0;
}

.size-demo-nucleus {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 46%;
  height: 46%;
  margin: -23% 0 0 -23%;
  border-radius: 50%;
  background: #e06633;
}

.size-demo-electron {
  position: absolute;
  top: 14%;
  left: 68%;
  border-radius: 50%;
  background: #2b6cb0;
  transform: translate(-50%, -50%);
}

/* ── 分層圖底色 ── */
.bg-picker {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin: 4px 0 14px;
}

.bg-picker input[type="color"] {
  width: 40px;
  height: 30px;
  padding: 0;
  border: 1px solid rgba(228, 251, 255, 0.25);
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
}

.bg-hex {
  width: 110px;
  margin: 0;
  font-size: 13px;
}

.bg-sample {
  width: 30px;
  height: 30px;
  border-radius: 6px;
  border: 1px solid rgba(228, 251, 255, 0.2);
}

/* ── 圖鑑外框選擇 ── */
.frame-picker {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(92px, 1fr));
  gap: 10px;
  margin: 4px 0 14px;
  max-width: 460px;
}

.frame-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 7px;
  padding: 9px;
  border: 1px solid rgba(228, 251, 255, 0.14);
  border-radius: 8px;
  background: transparent;
  font-family: inherit;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.frame-option:hover {
  border-color: rgba(228, 251, 255, 0.4);
  background: rgba(228, 251, 255, 0.05);
}

.frame-option.active {
  border-color: #6ee76e;
  background: rgba(110, 231, 110, 0.1);
}

.frame-sample {
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 1 / 1;
  font-size: 20px;
  font-weight: 700;
  color: #E06633;
  background: rgba(60, 40, 75, 0.6);
}

.frame-option-label {
  font-size: 12px;
  color: rgba(228, 251, 255, 0.7);
}

.frame-option.active .frame-option-label {
  color: #e4fbff;
}

.bg-preview {
  max-width: 260px;
  max-height: 140px;
  object-fit: cover;
}

.compress-info {
  font-size: 12px;
  color: #6ee76e;
  opacity: 0.85;
  margin: 4px 0 0;
}
.preview-new .img-preview {
  border-color: rgba(110, 231, 110, 0.5);
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

.mol-toolbar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}

.mol-toolbar .mol-filter-input {
  flex: 2 1 200px;
  margin: 0;
}

.mol-toolbar .mol-filter-select {
  flex: 1 1 120px;
  margin: 0;
}

.mol-count {
  text-align: left;
  margin: 4px 0 8px;
}

.mol-category-tag {
  font-size: 10px;
  padding: 1px 7px;
  border-radius: 999px;
  border: 1px solid rgba(157, 140, 255, 0.4);
  color: rgba(200, 190, 255, 0.85);
}

/* 自動判斷的分類用虛線框，一眼看出哪些是手動指定過的 */
.mol-category-tag--auto {
  border-style: dashed;
  border-color: rgba(157, 140, 255, 0.28);
  color: rgba(200, 190, 255, 0.55);
}

.mol-lookup {
  display: flex;
  gap: 8px;
  margin: 12px 0 4px;
  flex-wrap: wrap;
}

.mol-lookup .input { flex: 1 1 240px; }

.mol-results {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 10px;
}

.mol-result {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding: 8px 12px;
  border: 1px solid rgba(228, 251, 255, 0.18);
  border-radius: 8px;
  background: rgba(20, 5, 35, 0.5);
  color: #e4fbff;
  cursor: pointer;
  text-align: left;
}

.mol-result:hover { border-color: rgba(228, 251, 255, 0.5); }

.mol-result-formula { font-weight: 700; }

.mol-result-name {
  flex: 1;
  font-size: 13px;
  color: rgba(228, 251, 255, 0.7);
  word-break: break-all;
}

.mol-result-cid {
  font-size: 12px;
  color: rgba(228, 251, 255, 0.45);
}

.mol-image-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.mol-image-preview {
  width: 140px;
  aspect-ratio: 1 / 1;
  border: 1px dashed rgba(228, 251, 255, 0.25);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
}

.mol-image-preview img {
  max-width: 100%;
  max-height: 100%;
  background: #fff;
  border-radius: 4px;
}

.mol-image-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-item-title :deep(sub),
.mol-result-formula :deep(sub) {
  font-size: 0.6em;
  vertical-align: baseline;
  position: relative;
  bottom: -0.2em;
}

.loading-tag {
  margin-left: 10px;
  font-size: 12px;
  font-weight: 400;
  color: rgba(228, 251, 255, 0.5);
}

.gallery-admin.is-loading {
  opacity: 0.55;
  pointer-events: none;
}

/* iOS Safari 聚焦到字級小於 16px 的表單元件時會自動放大整頁，
   而且常常卡在放大狀態，看起來就是「後台版面變太大」(issue #10)。
   手機上把表單字級固定在 16px 從根源避免縮放。
   放在樣式表末端，才不會被前面的基礎字級規則蓋掉 */
@media (max-width: 760px) {
  .input,
  .select,
  select.select,
  .layer-slot .input {
    font-size: 16px;
  }
}

/* ── 主族形象選擇器 ── */
.group-section {
  margin-bottom: 16px;
}

.group-section-title {
  font-size: 12px;
  letter-spacing: 0.12em;
  color: rgba(228, 251, 255, 0.45);
  text-align: left;
  margin: 0 0 8px;
  padding-bottom: 5px;
  border-bottom: 1px solid rgba(228, 251, 255, 0.1);
}

.group-key-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(118px, 1fr));
  gap: 8px;
}

.group-key {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px;
  border: 1px solid rgba(228, 251, 255, 0.15);
  border-radius: 8px;
  background: transparent;
  color: rgba(228, 251, 255, 0.65);
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, background 0.15s;
}

.group-key:hover { border-color: rgba(228, 251, 255, 0.4); }

.group-key.filled {
  border-color: rgba(110, 231, 110, 0.45);
}

.group-key.active {
  background: rgba(228, 251, 255, 0.1);
  border-color: #e4fbff;
  color: #e4fbff;
}

.group-key-label {
  font-size: 15px;
  font-weight: 700;
}

.group-key-name {
  font-size: 11px;
  opacity: 0.7;
}

.meta-field { margin-bottom: 4px; }

/* ── 頁面管理：清單／編輯 ── */
.section-head {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}

/* 頁面編輯有區塊編輯器之後會很長，動作列黏在頁首底下，捲到哪裡都按得到。
   頁首是 sticky、底緣固定在 63px，所以這裡貼齊 63 而不是留空隙。
   上方多給 12px 內距並用 -12px 抵銷，讓背景往上多蓋一段——只要 top 和
   頁首底緣差一點點，捲動的內容就會從那條縫透出來。
   負的左右外距＋補回內距則是讓背景蓋滿整個 box 寬度。 */
.section-head--sticky {
  position: sticky;
  top: 63px;
  z-index: 20;
  margin: -36px -28px 6px;
  padding: 26px 28px 14px;
  background: rgba(14, 5, 26, 0.97);
  border-bottom: 1px solid rgba(228, 251, 255, 0.1);
  backdrop-filter: blur(4px);
}

/* 標題吃掉中間的空間，把動作按鈕推到兩端 */
.section-head .title { margin: 0; flex: 1; }

.page-table {
  display: flex;
  flex-direction: column;
  margin-top: 14px;
  border: 1px solid rgba(228, 251, 255, 0.12);
  border-radius: 8px;
  overflow: hidden;
}

.page-row {
  display: grid;
  grid-template-columns: 68px minmax(120px, 1.6fr) minmax(100px, 1.2fr) 84px 96px auto;
  gap: 10px;
  align-items: center;
  padding: 9px 14px;
  border-top: 1px solid rgba(228, 251, 255, 0.08);
  font-size: 13px;
}

.page-row:first-child { border-top: none; }

/* 清單的顏色分三階：標題最亮、路徑與導覽位置次之、表頭最淡，
   讓一眼能先掃到標題 */
.page-row--head {
  background: rgba(228, 251, 255, 0.06);
  font-size: 12px;
  letter-spacing: 0.04em;
  color: rgba(228, 251, 255, 0.6);
}

.page-order { display: flex; gap: 2px; }
.page-order .icon-button { padding: 0 4px; font-size: 11px; }

.page-title-cell {
  display: flex;
  align-items: center;
  gap: 7px;
  font-weight: bold;
  color: #e4fbff;
}

.page-path {
  font-family: monospace;
  font-size: 12px;
  color: rgba(228, 251, 255, 0.72);
  overflow-wrap: anywhere;
}

.system-tag {
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(228, 251, 255, 0.12);
  color: rgba(228, 251, 255, 0.8);
  font-size: 11px;
  font-weight: normal;
}

.status-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  white-space: nowrap;
}

.status-tag.is-live { background: rgba(110, 231, 110, 0.14); color: #6ee76e; }
.status-tag.is-draft { background: rgba(255, 196, 107, 0.14); color: #ffc46b; }

.page-nav-cell { font-size: 12px; color: rgba(228, 251, 255, 0.72); }

.page-ops {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
  align-items: center;
}

.button.small { padding: 4px 12px; font-size: 12px; }

.migrate-hint,
.migrated-notice {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin: 10px 0 18px;
  padding: 10px 14px;
  border: 1px solid rgba(157, 140, 255, 0.28);
  border-radius: 8px;
  background: rgba(90, 70, 160, 0.12);
  font-size: 13px;
  color: rgba(228, 251, 255, 0.75);
}

.migrate-hint .field-hint { flex-basis: 100%; margin: 0; }

/* 圖庫清單比頁面清單少兩欄，沿用同一套列樣式但改欄寬 */
.library-row {
  grid-template-columns: minmax(140px, 1.6fr) minmax(120px, 1.2fr) 80px auto;
}

/* 圖庫的每張圖多了一個可編輯的名稱欄位，格子要比純展示的電子樣式寬，
   否則名稱稍長就被裁掉（120px 的格子只剩 75px 給輸入框） */
.library-grid {
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
}

.library-grid .style-item .input {
  width: 100%;
  /* grid 子項預設 min-width:auto，不設 0 仍會被內容撐開 */
  min-width: 0;
}

/* 窄螢幕排不下六欄，改成兩欄的卡片，欄位前面補上名稱 */
@media (max-width: 700px) {
  .page-row--head { display: none; }

  .page-row {
    grid-template-columns: 1fr auto;
    gap: 6px 10px;
    padding: 12px 14px;
  }

  .page-order { grid-row: 1; grid-column: 2; justify-content: flex-end; }
  .page-title-cell { grid-row: 1; grid-column: 1; }
  .page-path { grid-column: 1 / -1; }
  .page-nav-cell::before { content: '導覽列：'; }
  .page-ops { grid-column: 1 / -1; justify-content: flex-start; }
}
</style>
