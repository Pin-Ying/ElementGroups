<template>
  <div class="guide">
    <p class="title">元素說明書</p>
    <p class="guide-intro">
      這個網站把每個元素當成圖鑑裡的一張卡片。這頁說明卡片上的各項數值代表什麼、
      不同的分組方式各自依據什麼標準，以及週期表要怎麼讀。
    </p>

    <section class="guide-section">
      <h2 class="section-title">能力值</h2>
      <p class="section-desc">
        元素頁的 <strong>Stats</strong> 分頁會列出七項物理與化學性質。
        長條的長度是該項目在 118 個元素中的相對比例——長條越長，表示這個元素在這個項目上的數值越接近所有元素中的最大值，
        而不是「越好」。
      </p>
      <div class="cards">
        <div v-for="item in abilities" :key="item.name" class="card">
          <div class="card-head">
            <span class="card-name">{{ item.name }}</span>
            <span class="card-unit">{{ item.unit }}</span>
          </div>
          <p class="card-body">{{ item.desc }}</p>
          <p class="card-extreme">{{ item.extreme }}</p>
        </div>
      </div>
    </section>

    <section class="guide-section">
      <h2 class="section-title">分組方式</h2>
      <p class="section-desc">首頁的「分組」下拉可以切換元素的排列依據。</p>
      <div class="cards">
        <div v-for="item in groupings" :key="item.name" class="card">
          <div class="card-head">
            <span class="card-name">{{ item.name }}</span>
          </div>
          <p class="card-body">{{ item.desc }}</p>
        </div>
      </div>
    </section>

    <section class="guide-section">
      <h2 class="section-title">週期表怎麼讀</h2>
      <div class="prose">
        <p>
          <strong>橫列稱為「週期」</strong>，同一列的元素最外層電子所在的殼層相同。
          由上往下，每多一列就多一層電子殼層。
        </p>
        <p>
          <strong>直行稱為「族」</strong>，同一行的元素最外層電子數相同，
          因此化學性質相近——例如最右邊那一行都是幾乎不與其他元素反應的惰性氣體。
        </p>
        <p>
          <strong>下方獨立的兩列</strong>是鑭系（原子序 57–71）與錒系（89–103）。
          它們原本應該插在第 6、7 週期的第 3 行位置，但那樣會讓表格變得非常寬，
          所以習慣上抽出來放在下方，原位置以虛線框標示。
        </p>
      </div>
    </section>

    <section class="guide-section">
      <h2 class="section-title">卡片顏色</h2>
      <div class="prose">
        <p>
          每個元素的外框顏色來自 <strong>CPK 配色</strong>，這是分子模型與化學繪圖長期沿用的一套慣例，
          源自 Corey、Pauling 與 Koltun 三人的分子模型著色方式。
        </p>
        <p>
          常見的對應如：氧為紅色、氮為藍色、碳為深灰或黑色、氫為白色、硫為黃色、
          鹵素多為綠色系。用同一套顏色，是為了讓同一個元素在不同的圖表或模型裡都能一眼認出來。
        </p>
      </div>
    </section>

    <section class="guide-section">
      <h2 class="section-title">完成度標記</h2>
      <div class="prose">
        <p>
          首頁元素格子右上角的小圓點，表示這個元素的內容整理進度：
        </p>
        <p class="legend-line">
          <i class="dot dot--image"></i> 青色：已上傳代表圖片
          <i class="dot dot--story"></i> 綠色：已寫好介紹故事
        </p>
        <p>
          沒有圓點的元素表示還在整理中，點進去會看到預設圖片與「Still Creating…」。
          可以用控制列的「隱藏完成度」把這些標記關掉。
        </p>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  data() {
    return {
      abilities: [
        {
          name: '熔點',
          unit: 'K（凱氏溫標）',
          desc: '固體變成液體的溫度。數值越高代表原子之間的鍵結越強，需要更多能量才能拆開。',
          extreme: '最高的是鎢（3695 K），最低的是氦。'
        },
        {
          name: '沸點',
          unit: 'K（凱氏溫標）',
          desc: '液體變成氣體的溫度。與熔點一樣反映鍵結強度，但看的是完全脫離液態所需的能量。',
          extreme: '常溫下是氣體的元素，沸點都遠低於室溫（約 293 K）。'
        },
        {
          name: '電子親和力',
          unit: 'eV（電子伏特）',
          desc: '中性原子抓進一個電子時釋放的能量。數值越大表示這個元素越「想要」多一個電子。',
          extreme: '鹵素（氟、氯、溴、碘）特別高，惰性氣體幾乎為零。'
        },
        {
          name: '電負度',
          unit: '無單位（鮑林標度）',
          desc: '在化學鍵中把共用電子拉向自己的能力。兩個元素的電負度差距越大，鍵結越偏向離子鍵。',
          extreme: '氟最高（3.98），也是這套標度的基準。'
        },
        {
          name: '原子半徑',
          unit: 'pm（皮米）',
          desc: '原子的大小。同一週期由左往右變小（核電荷增加把電子拉得更緊），同一族由上往下變大。',
          extreme: '這裡採用凡得瓦半徑。'
        },
        {
          name: '游離能',
          unit: 'eV（電子伏特）',
          desc: '從原子上拔走一個電子所需的能量。數值越高表示電子被抓得越牢。',
          extreme: '惰性氣體最高，鹼金屬最低——後者容易失去電子形成正離子。'
        },
        {
          name: '密度',
          unit: 'g/cm³',
          desc: '單位體積的質量。受原子量與原子堆疊方式共同影響，不是單純看原子重不重。',
          extreme: '鋨與銥最高，約為水的 22 倍。'
        }
      ],
      groupings: [
        {
          name: 'Periodic Table',
          desc: '標準的週期表排版，依照原子序與電子組態擺在固定的行列位置。想看元素之間的週期性規律時用這個。'
        },
        {
          name: 'Atomic Number',
          desc: '單純依原子序 1 到 118 依序排列。想快速找到某個特定原子序的元素時最直覺。'
        },
        {
          name: 'Chemical Properties',
          desc: '依化學性質分類，例如鹼金屬、鹼土金屬、過渡金屬、鹵素、惰性氣體、鑭系、錒系等。同一組的元素反應行為相似。'
        },
        {
          name: 'Valence Shell',
          desc: '依最外層電子所在的軌域類型（s、p、d、f）分組。這決定了元素在週期表上屬於哪一個區塊，也是化學性質的根源。'
        }
      ]
    }
  }
}
</script>

<style scoped>
.guide {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px 18px 40px;
  text-align: left;
}

.guide .title {
  text-align: center;
}

.guide-intro {
  font-size: 14px;
  line-height: 1.85;
  color: rgba(228, 251, 255, 0.62);
  margin: 0 0 30px;
  text-align: center;
}

.guide-section {
  margin-bottom: 34px;
}

.section-title {
  font-size: 17px;
  font-weight: 600;
  color: #e4fbff;
  margin: 0 0 8px;
  padding-bottom: 7px;
  border-bottom: 1px solid rgba(228, 251, 255, 0.15);
}

.section-desc {
  font-size: 13px;
  line-height: 1.8;
  color: rgba(228, 251, 255, 0.6);
  margin: 0 0 14px;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 10px;
}

.card {
  padding: 14px 16px;
  border: 1px solid rgba(228, 251, 255, 0.12);
  border-radius: 8px;
  background: rgba(20, 5, 35, 0.45);
}

.card-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}

.card-name {
  font-size: 15px;
  font-weight: 600;
  color: #e4fbff;
}

.card-unit {
  font-size: 11px;
  color: rgba(228, 251, 255, 0.4);
}

.card-body {
  font-size: 13px;
  line-height: 1.75;
  color: rgba(228, 251, 255, 0.78);
  margin: 0;
}

.card-extreme {
  font-size: 12px;
  line-height: 1.7;
  color: rgba(228, 251, 255, 0.45);
  margin: 8px 0 0;
  padding-top: 8px;
  border-top: 1px dashed rgba(228, 251, 255, 0.1);
}

.prose p {
  font-size: 14px;
  line-height: 1.9;
  color: rgba(228, 251, 255, 0.78);
  margin: 0 0 12px;
}

.prose strong {
  color: #e4fbff;
}

.legend-line {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 2px;
}

.dot--image {
  background: #45d0e0;
  box-shadow: 0 0 5px rgba(69, 208, 224, 0.9);
}

.dot--story {
  background: #6ee76e;
  box-shadow: 0 0 5px rgba(110, 231, 110, 0.9);
}
</style>
