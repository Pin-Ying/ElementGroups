<template>
  <div class="admin-bar">
    <slot name="lead" />
    <p class="title is-4">{{ title }}</p>
    <div class="admin-bar-actions">
      <slot />
    </div>
  </div>
</template>

<script>
// 後台各區塊共用的標題＋動作列。
//
// 黏在頁首下方，捲到哪裡主要動作都按得到——後台很多區塊（元素故事、頁面
// 區塊、分子、圖庫）內容都很長，動作放在底部要一路捲下去才按得到。
//
// 抽成元件而不是在每個區塊各貼一份樣式：sticky 的 top 必須和頁首底緣
// 完全吻合，差一兩像素就會看到背後的內容從縫裡滑過去。集中一處才不會
// 有的區塊對、有的區塊留縫。
export default {
  props: {
    title: { type: String, default: '' }
  }
}
</script>

<style scoped>
.admin-bar {
  position: sticky;
  /* 頁首是 sticky、底緣固定在 63px，這裡貼齊它 */
  top: 63px;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  /* 上方多給內距並用外距抵銷，讓背景往上多蓋一段；左右負外距則是讓
     背景蓋滿整個 box 寬度，捲動的內容才不會從側邊透出來 */
  margin: -36px -28px 14px;
  padding: 26px 28px 14px;
  background: rgba(14, 5, 26, 0.97);
  border-bottom: 1px solid rgba(228, 251, 255, 0.1);
  backdrop-filter: blur(4px);
}

.admin-bar .title {
  margin: 0;
  flex: 1;
  /* 標題不該把按鈕擠出去 */
  min-width: 0;
}

.admin-bar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

@media (max-width: 700px) {
  .admin-bar {
    margin: -20px -18px 12px;
    padding: 18px 18px 12px;
  }
}
</style>
