/* AADO 短剧制作课程（右上角「课程」入口）
   面向零基础学员，目标达到专业剪辑/制作水平。
   所有标准值均可在 PRD/91 与 PRD/96 中回溯；经验值会明确标注。 */
window.ACADEMY = {
  title: "AI 短剧制作课程",
  subtitle: "从零基础到专业编辑的完整知识体系",
  chapters: [
    {
      id: "start",
      eyebrow: "00 · ORIENTATION",
      title: "课程导览：你要成为什么样的制作者",
      lede: "这不是一份「按钮说明书」。学完之后，你应该能对一条镜头、一段声音、一次配乐做出专业判断，并说清楚判断的依据。",
      html: `
        <section class="course-sec">
          <h3>三个能力层级</h3>
          <div class="course-grid">
            <div class="course-kpi"><b>操作员</b><p>知道按钮在哪，能按流程把片子跑出来。产出可用，但不知道为什么好、为什么坏。</p></div>
            <div class="course-kpi"><b>编辑</b><p>能判断一条镜头能不能用、问题出在哪、怎么修；能按叙事节奏组织镜头与声音。这是本课程的主目标。</p></div>
            <div class="course-kpi"><b>导演</b><p>在编辑能力之上，能预先设计镜头与声音，让每个技术选择服务于故事。这需要长期实践，课程给出路径。</p></div>
          </div>
        </section>

        <section class="course-sec">
          <h3>这门课怎么用</h3>
          <p>每章采用同一结构：<b>概念 → 参数 → 判断标准 → 常见误区 → 练习</b>。建议顺序阅读，不要跳章。第 3–5 章建立画面判断，第 6–7 章建立表演与口型判断，第 8–10 章建立声音判断，第 11–14 章建立交付与选型判断。</p>
          <table class="compare-table">
            <thead><tr><th>阶段</th><th>章节</th><th>学完能做到</th></tr></thead>
            <tbody>
              <tr><td>建立全局观</td><td>1–2</td><td>说清一条 AI 短剧流水线有哪些环节、每个环节的产出物与验收标准</td></tr>
              <tr><td>画面能力</td><td>3–5</td><td>写得出可执行的镜头提示词，选得出可用镜头，看得出画面问题</td></tr>
              <tr><td>声音能力</td><td>6–10</td><td>设计四层声音、组织配乐 Cue、完成混音与响度交付</td></tr>
              <tr><td>交付与选型</td><td>11–14</td><td>做母版 QC、按场景选模型、搭出自己的供应商组合</td></tr>
            </tbody>
          </table>
        </section>

        <section class="course-sec">
          <h3>两类数字，别混用</h3>
          <p><b>标准值</b>来自规范或平台硬要求，例如归档母版 −23.0 LUFS、真峰值 ≤ −1 dBTP、音画偏移 +90/−185 ms。它们不能凭感觉改。<b>经验值</b>来自实践，例如「每场 1–3 镜」「候选出 4 条」。它们可以按项目调整，课程会明确标注。</p>
          <div class="course-note">学习建议：准备一个练习项目，每读完一章就回到项目里找一个对应环节动手。看十遍不如改一条镜头。</div>
        </section>

        <section class="course-sec">
          <h3>30 天学习路径（经验值）</h3>
          <ol>
            <li><b>第 1 周</b>：第 1–5 章。目标：独立完成一场 30 秒戏的分镜与 6 条镜头候选。</li>
            <li><b>第 2 周</b>：第 6–7 章。目标：给这场戏配好对白与口型，能解释每一条为什么开/不开口型。</li>
            <li><b>第 3 周</b>：第 8–10 章。目标：做出四层 stem，混音通过响度与可懂度检查。</li>
            <li><b>第 4 周</b>：第 11–14 章。目标：导出母版与 QC 报告，写一份模型选型说明。</li>
          </ol>
        </section>
      `
    },
    {
      id: "pipeline",
      eyebrow: "01 · THE PIPELINE",
      title: "全局图：一条 AI 短剧是怎么生产出来的",
      lede: "先看整条流水线，再学每个零件。否则你会把「工具」当成「工艺」。",
      html: `
        <section class="course-sec">
          <h3>从小说到母版的十六个环节</h3>
          <p>真人影视工业的分工，在 AI 流水线里依然成立，只是执行者从人变成了模型加人。AADO 把它压缩成 19 个模块，主干顺序是：</p>
          <div class="course-flow">
            <span>小说 / 创意</span><i>→</i><span>剧本</span><i>→</i><span>选角定妆</span><i>→</i><span>分镜</span><i>→</i><span>previz</span><i>→</i><span>镜头生成</span><i>→</i><span>一致性</span><i>→</i><span>配音</span><i>→</i><span>口型</span><i>→</i><span>声音设计</span><i>→</i><span>剪辑</span><i>→</i><span>调色母版</span><i>→</i><span>QC</span><i>→</i><span>交付</span><i>→</i><span>VFX</span><i>→</i><span>合规</span>
          </div>
          <figure class="course-fig">
            <svg viewBox="0 0 800 300" role="img" aria-label="AI 短剧三泳道流水线示意图">
              <defs><marker id="f1a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#A0A0AC"/></marker></defs>
              <style>.f1b{fill:#F4F4F8;stroke:#DCDCE4}.f1k{fill:#F2F2FE;stroke:#E0E0FA}.f1t{font-size:12px;fill:#17171C;font-weight:600}.f1l{font-size:11px;fill:#A0A0AC;letter-spacing:1.4px}.f1s{font-size:10px;fill:#6E6E7A}</style>
              <text x="20" y="84" class="f1l">画面主线</text>
              <text x="20" y="174" class="f1l">声音主线</text>
              <text x="20" y="264" class="f1l">审计主线</text>
              <rect x="100" y="62" width="100" height="36" rx="7" class="f1b"/><text x="150" y="85" text-anchor="middle" class="f1t">剧本</text>
              <rect x="214" y="62" width="100" height="36" rx="7" class="f1b"/><text x="264" y="85" text-anchor="middle" class="f1t">定妆</text>
              <rect x="328" y="62" width="100" height="36" rx="7" class="f1k"/><text x="378" y="85" text-anchor="middle" class="f1t">分镜</text>
              <rect x="442" y="62" width="100" height="36" rx="7" class="f1b"/><text x="492" y="85" text-anchor="middle" class="f1t">镜头生成</text>
              <rect x="556" y="62" width="100" height="36" rx="7" class="f1b"/><text x="606" y="85" text-anchor="middle" class="f1t">一致性</text>
              <rect x="670" y="62" width="100" height="36" rx="7" class="f1b"/><text x="720" y="85" text-anchor="middle" class="f1t">剪辑</text>
              <path d="M200,80 H210" stroke="#A0A0AC" marker-end="url(#f1a)"/><path d="M314,80 H324" stroke="#A0A0AC" marker-end="url(#f1a)"/>
              <path d="M428,80 H438" stroke="#A0A0AC" marker-end="url(#f1a)"/><path d="M542,80 H552" stroke="#A0A0AC" marker-end="url(#f1a)"/>
              <path d="M656,80 H666" stroke="#A0A0AC" marker-end="url(#f1a)"/>
              <rect x="328" y="152" width="100" height="36" rx="7" class="f1b"/><text x="378" y="175" text-anchor="middle" class="f1t">配音</text>
              <rect x="442" y="152" width="100" height="36" rx="7" class="f1k"/><text x="492" y="175" text-anchor="middle" class="f1t">口型</text>
              <rect x="556" y="152" width="100" height="36" rx="7" class="f1b"/><text x="606" y="175" text-anchor="middle" class="f1t">四层声音</text>
              <rect x="670" y="152" width="100" height="36" rx="7" class="f1b"/><text x="720" y="175" text-anchor="middle" class="f1t">混音</text>
              <path d="M428,170 H438" stroke="#A0A0AC" marker-end="url(#f1a)"/><path d="M542,170 H552" stroke="#A0A0AC" marker-end="url(#f1a)"/>
              <path d="M656,170 H666" stroke="#A0A0AC" marker-end="url(#f1a)"/>
              <rect x="214" y="242" width="100" height="36" rx="7" class="f1b"/><text x="264" y="265" text-anchor="middle" class="f1t">门禁</text>
              <rect x="328" y="242" width="100" height="36" rx="7" class="f1b"/><text x="378" y="265" text-anchor="middle" class="f1t">成本</text>
              <rect x="442" y="242" width="100" height="36" rx="7" class="f1b"/><text x="492" y="265" text-anchor="middle" class="f1t">存储血缘</text>
              <rect x="670" y="242" width="100" height="36" rx="7" class="f1b"/><text x="720" y="265" text-anchor="middle" class="f1t">合规</text>
              <path d="M314,260 H324" stroke="#A0A0AC" marker-end="url(#f1a)"/><path d="M428,260 H438" stroke="#A0A0AC" marker-end="url(#f1a)"/>
              <path d="M378,98 V146" stroke="#A0A0AC" stroke-dasharray="4 4" marker-end="url(#f1a)"/>
              <path d="M720,98 V146" stroke="#A0A0AC" stroke-dasharray="4 4" marker-end="url(#f1a)"/>
              <path d="M264,98 V236" stroke="#A0A0AC" stroke-dasharray="4 4" marker-end="url(#f1a)"/>
              <text x="386" y="126" class="f1s">按镜头并行</text>
              <text x="728" y="126" class="f1s">按镜头</text>
              <text x="272" y="210" class="f1s">贯穿全程</text>
            </svg>
            <figcaption><b>图 1 · 三泳道流水线。</b>画面、声音、审计三条主线并行推进；分镜决定镜头、镜头决定配音与口型、剪辑决定混音，审计主线贯穿每一步。</figcaption>
          </figure>
          <p>注意两个容易被低估的环节：<b>previz</b>（预览片）决定你能不能低成本试错；<b>一致性</b>不是生成完再修，而是贯穿选角、分镜、生成、剪辑的连续约束。</p>
        </section>

        <section class="course-sec">
          <h3>三条主线，而不是一条</h3>
          <table class="compare-table">
            <thead><tr><th>主线</th><th>包含环节</th><th>核心问题</th><th>失败的表现</th></tr></thead>
            <tbody>
              <tr><td><b>画面主线</b></td><td>定妆 → 分镜 → 生成 → 一致性 → 剪辑</td><td>观众是否相信这是同一个人、同一个世界</td><td>脸跳、服装跳、光跳、轴线乱</td></tr>
              <tr><td><b>声音主线</b></td><td>配音 → 口型 → 音乐 / 音效 / 环境 → 混音</td><td>观众是否听得清、听得信、听得进情绪</td><td>对白糊、口型飘、切镜爆音、音乐抢戏</td></tr>
              <tr><td><b>可审计主线</b></td><td>门禁 → 成本 → 存储血缘 → 合规</td><td>这条片子能不能被平台接收、被追溯、被复用</td><td>无署名、超预算、素材找不到来源、AI 标识缺失</td></tr>
            </tbody>
          </table>
        </section>

        <section class="course-sec">
          <h3>质量优先级：先保什么</h3>
          <p>当预算和时间有限时，专业制作者的取舍顺序通常是：<b>故事可懂 &gt; 人物一致 &gt; 表演可信 &gt; 声音清楚 &gt; 画质精致</b>。这不是审美排序，而是观众流失的先后顺序：故事看不懂，三秒就划走；脸不像同一个人，十秒出戏；声音听不清，三十秒放弃；画质差，观众反而更能忍。</p>
          <div class="course-note">反直觉结论：把 1080P 降到 720P 省下的钱，投到角色一致性和配音上，成片观感通常更好。</div>
        </section>

        <section class="course-sec">
          <h3>每个环节的产出物</h3>
          <table class="compare-table">
            <thead><tr><th>环节</th><th>产出物</th><th>交给谁</th></tr></thead>
            <tbody>
              <tr><td>剧本</td><td>场次表、对白、动作描述</td><td>分镜、配音</td></tr>
              <tr><td>定妆</td><td>角色锚点图集、音色档案</td><td>生成、配音、一致性</td></tr>
              <tr><td>分镜</td><td>镜头表（景别、时长、运镜、同框角色）</td><td>生成、剪辑、成本</td></tr>
              <tr><td>镜头生成</td><td>候选视频、选中版本、生成参数</td><td>一致性、剪辑</td></tr>
              <tr><td>配音</td><td>逐句音轨、时间码、情绪标记</td><td>口型、声音设计、字幕</td></tr>
              <tr><td>声音设计</td><td>D/M/E/Amb 四路 stem</td><td>混音、交付</td></tr>
              <tr><td>剪辑</td><td>锁定时间线、EDL/XML</td><td>母版、VFX</td></tr>
              <tr><td>母版与 QC</td><td>母版文件、QC 报告、交付单</td><td>平台、归档</td></tr>
            </tbody>
          </table>
        </section>

        <section class="course-sec">
          <h3>练习</h3>
          <ol>
            <li>把一部你看过的短剧拆成 10 个镜头，写出每个镜头的景别、时长、是否对白、有没有音乐。</li>
            <li>在这条流水线上标出：哪一步最花钱、哪一步最容易返工、哪一步最影响观众留存。</li>
          </ol>
        </section>
      `
    },
    {
      id: "shot",
      eyebrow: "02 · SHOT LANGUAGE",
      title: "镜头语言：观众没意识到、但一直在被引导的东西",
      lede: "镜头不是「拍到了什么」，而是「让观众在这一秒看什么、怎么感受」。生成模型只执行参数，判断仍然在你。",
      html: `
        <section class="course-sec">
          <h3>画幅：先决定观众在哪看</h3>
          <p><b>2.39:1</b> 宽银幕，电影感强，适合大场面与双人对峙；<b>16:9</b> 平台横屏通用；<b>9:16</b> 竖屏短剧主战场，人脸占比大，构图必须重排，不能把横屏画面裁一刀了事。专业做法是生成 16:9 open gate 母版，再按画幅派生，避免为每个画幅重复生成。</p>
          <div class="course-note">竖屏的第一原则：主体放中上部，给字幕和平台 UI 留出下方安全区。</div>
        </section>

        <section class="course-sec">
          <h3>景别：信息量与情绪距离</h3>
          <table class="compare-table">
            <thead><tr><th>景别</th><th>画面范围</th><th>作用</th><th>常见误用</th></tr></thead>
            <tbody>
              <tr><td>大全景 ELS</td><td>环境为主，人很小</td><td>交代地点、规模、孤立感</td><td>连续使用导致节奏拖沓</td></tr>
              <tr><td>全景 LS</td><td>人物全身</td><td>动作、走位、空间关系</td><td>看不清表情，却用来演情绪</td></tr>
              <tr><td>中景 MS</td><td>腰部以上</td><td>对话主力景别</td><td>全片只用一个景别，像监控</td></tr>
              <tr><td>中近景 MCU</td><td>胸部以上</td><td>对话 + 表情，短剧最常用</td><td>与中景混用导致跳切</td></tr>
              <tr><td>近景 CU</td><td>头部</td><td>情绪、反应、口型</td><td>没有动机地频繁切</td></tr>
              <tr><td>特写 ECU</td><td>眼睛、手、道具</td><td>强调关键信息</td><td>滥用会削弱强调效果</td></tr>
            </tbody>
          </table>
          <p>景别变化的专业原则：<b>相邻镜头景别至少差一级</b>，否则观众会感到「跳了一下」。这就是 30 度规则的视觉版本。</p>
          <figure class="course-fig">
            <svg viewBox="0 0 800 210" role="img" aria-label="六种景别从大全景到特写的画面范围示意">
              <style>.f2f{fill:#FFFFFF;stroke:#DCDCE4}.f2h{fill:#C9C9D6}.f2b{fill:#E4E4EE}.f2t{font-size:12px;fill:#17171C;font-weight:600}.f2s{font-size:10px;fill:#A0A0AC}.f2g{stroke:#E9E9EF}</style>
              <rect x="24" y="24" width="104" height="112" rx="4" class="f2f"/><line x1="24" y1="120" x2="128" y2="120" class="f2g"/>
              <circle cx="76" cy="98" r="4" class="f2h"/><line x1="76" y1="102" x2="76" y2="112" stroke="#C9C9D6" stroke-width="3"/>
              <text x="76" y="158" text-anchor="middle" class="f2t">大全景</text><text x="76" y="174" text-anchor="middle" class="f2s">ELS</text>
              <rect x="152" y="24" width="104" height="112" rx="4" class="f2f"/><line x1="152" y1="120" x2="256" y2="120" class="f2g"/>
              <circle cx="204" cy="86" r="7" class="f2h"/><rect x="197" y="94" width="14" height="26" rx="5" class="f2b"/>
              <text x="204" y="158" text-anchor="middle" class="f2t">全景</text><text x="204" y="174" text-anchor="middle" class="f2s">LS</text>
              <rect x="280" y="24" width="104" height="112" rx="4" class="f2f"/><line x1="280" y1="120" x2="384" y2="120" class="f2g"/>
              <circle cx="332" cy="80" r="10" class="f2h"/><rect x="321" y="91" width="22" height="29" rx="7" class="f2b"/>
              <text x="332" y="158" text-anchor="middle" class="f2t">中景</text><text x="332" y="174" text-anchor="middle" class="f2s">MS</text>
              <rect x="408" y="24" width="104" height="112" rx="4" class="f2f"/><line x1="408" y1="120" x2="512" y2="120" class="f2g"/>
              <circle cx="460" cy="76" r="14" class="f2h"/><rect x="441" y="91" width="38" height="29" rx="9" class="f2b"/>
              <text x="460" y="158" text-anchor="middle" class="f2t">中近景</text><text x="460" y="174" text-anchor="middle" class="f2s">MCU</text>
              <rect x="536" y="24" width="104" height="112" rx="4" class="f2f"/>
              <circle cx="588" cy="72" r="26" class="f2h"/><path d="M552,120 Q588,96 624,120 Z" class="f2b"/>
              <text x="588" y="158" text-anchor="middle" class="f2t">近景</text><text x="588" y="174" text-anchor="middle" class="f2s">CU</text>
              <rect x="664" y="24" width="104" height="112" rx="4" class="f2f"/>
              <ellipse cx="716" cy="80" rx="30" ry="17" fill="#FFFFFF" stroke="#C9C9D6"/><circle cx="716" cy="80" r="8" class="f2h"/>
              <text x="716" y="158" text-anchor="middle" class="f2t">特写</text><text x="716" y="174" text-anchor="middle" class="f2s">ECU</text>
            </svg>
            <figcaption><b>图 2 · 六种景别。</b>从左到右，人物在画面中越来越大、环境信息越来越少、情绪距离越来越近。相邻镜头至少差一级，避免跳切感。</figcaption>
          </figure>
        </section>

        <section class="course-sec">
          <h3>机位与角度</h3>
          <ul>
            <li><b>平视</b>：中性、客观，最不容易出错。</li>
            <li><b>仰拍</b>：人物显强、显压迫；注意背景容易露出天花板。</li>
            <li><b>俯拍</b>：人物显弱、显渺小；也用于交代空间。</li>
            <li><b>荷兰角（倾斜）</b>：不安、失衡，慎用，一集一两次足够。</li>
            <li><b>过肩镜 OTS</b>：对话标准解法，同时带到对方肩膀，建立空间关系。</li>
          </ul>
        </section>

        <section class="course-sec">
          <h3>运镜：为什么要动</h3>
          <p>推（dolly in）聚焦、拉（dolly out）抽离、摇（pan）扫视、移（track）跟随、升降（crane）改变视点。生成模型里的「运镜控制」不是装饰，它决定观众注意力的移动路径。<b>没有动机的运镜，比不动更糟</b>。</p>
          <div class="course-note">生成视频的视角跨度超过 90° 时，角色一致性会显著下降；这不是模型缺陷，是训练数据里没见过的视角。跨轴镜头要靠参考图或首尾帧补。</div>
        </section>

        <section class="course-sec">
          <h3>轴线：为什么两个人的位置不能乱</h3>
          <p>两人对话时，摄影机和他们之间有一条假想连线，叫<b>轴线</b>。所有镜头都应在轴线同一侧拍摄，否则观众会觉得两人突然换了位置。这就是 180 度规则。</p>
          <ul>
            <li><b>正反打</b>：A 看画右、B 看画左，剪辑后视线相接。</li>
            <li><b>越轴</b>：不是绝对不能，但必须用中性镜头、运动镜头或人物移动来过渡。</li>
            <li><b>视线匹配</b>：看的方向与下一镜被看对象的方向要一致。</li>
          </ul>
          <figure class="course-fig">
            <svg viewBox="0 0 800 260" role="img" aria-label="180 度轴线与正反打机位示意">
              <defs><marker id="f3a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#A0A0AC"/></marker></defs>
              <style>.f3p{font-size:12px;fill:#17171C;font-weight:600}.f3s{font-size:11px;fill:#6E6E7A}.f3l{font-size:10px;fill:#A0A0AC}</style>
              <rect x="80" y="120" width="640" height="120" fill="#F2F2FE"/>
              <line x1="90" y1="110" x2="710" y2="110" stroke="#A0A0AC" stroke-dasharray="6 5"/>
              <text x="400" y="102" text-anchor="middle" class="f3s">轴线（假想连线）</text>
              <circle cx="250" cy="110" r="20" fill="#E4E4EE" stroke="#C9C9D6"/><text x="250" y="115" text-anchor="middle" class="f3p">A</text>
              <circle cx="550" cy="110" r="20" fill="#E4E4EE" stroke="#C9C9D6"/><text x="550" y="115" text-anchor="middle" class="f3p">B</text>
              <text x="250" y="152" text-anchor="middle" class="f3s">演员 A</text><text x="550" y="152" text-anchor="middle" class="f3s">演员 B</text>
              <circle cx="300" cy="205" r="7" fill="#4F46E5"/><path d="M300,198 V170" stroke="#A0A0AC" marker-end="url(#f3a)"/>
              <circle cx="500" cy="205" r="7" fill="#4F46E5"/><path d="M500,198 V170" stroke="#A0A0AC" marker-end="url(#f3a)"/>
              <text x="300" y="226" text-anchor="middle" class="f3s">机位 1</text><text x="500" y="226" text-anchor="middle" class="f3s">机位 2</text>
              <text x="400" y="232" text-anchor="middle" class="f3l">安全侧：所有机位保持在轴线同一侧</text>
              <circle cx="400" cy="48" r="7" fill="#C2410C"/><path d="M400,55 V92" stroke="#C2410C" marker-end="url(#f3a)"/>
              <path d="M392,40 L408,56 M408,40 L392,56" stroke="#C2410C" stroke-width="2"/>
              <text x="400" y="28" text-anchor="middle" class="f3s" fill="#C2410C">越轴机位（会让人物左右互换）</text>
            </svg>
            <figcaption><b>图 3 · 轴线与正反打。</b>机位 1、2 都在轴线同侧，剪出来 A 看画右、B 看画左，视线相接；跑到对侧就是越轴，观众会觉得两人突然换了位置。</figcaption>
          </figure>
        </section>

        <section class="course-sec">
          <h3>剪辑节奏：ASL 与 J/L cut</h3>
          <p><b>ASL（平均镜头长度）</b>是节奏的量化指标。短剧常用 2–4 秒；情绪段落可以拉到 6–8 秒，动作段落可以压到 1 秒以内。<b>J cut</b> 是下一镜的声音先进来，<b>L cut</b> 是上一镜的声音延续到下一镜；两者都能让剪辑更顺，避免「一段一段拼」的机械感。</p>
        </section>

        <section class="course-sec">
          <h3>练习</h3>
          <ol>
            <li>找一段 60 秒双人对话，画轴线图，标出有没有越轴。</li>
            <li>统计它的 ASL；把其中三个镜头改写成与你原稿不同的景别，比较叙事差异。</li>
            <li>用一句话说明每个运镜镜头的动机。说不出来，就删掉运镜。</li>
          </ol>
        </section>
      `
    },
    {
      id: "genvideo",
      eyebrow: "03 · GENERATIVE VIDEO",
      title: "生成视频：模型在做什么，参数在控制什么",
      lede: "把生成模型当成一位执行能力很强、但不会读心的摄影师。你给的条件越确定，它越可靠。",
      html: `
        <section class="course-sec">
          <h3>原理：从噪声到时空片段</h3>
          <p>主流视频生成模型在「潜空间」里从随机噪声逐步去噪，生成一段连续的时空表示。它同时学习三件事：<b>外观</b>（长什么样）、<b>运动</b>（怎么动）、<b>物理</b>（东西怎么相互作用）。三者的学习难度不同，所以你会看到「画质很好但走路像滑行」「手一碰杯子就变形」之类的现象。</p>
          <p>条件控制决定生成方向：文本（prompt）、首帧（image-to-video）、首尾帧、参考图/视频/音频（reference-to-video）、镜头运动参数。控制条件越强，自由度越低，但可复现性越高。</p>
        </section>

        <section class="course-sec">
          <h3>三种模式，别用错</h3>
          <table class="compare-table">
            <thead><tr><th>模式</th><th>输入</th><th>适合</th><th>风险</th></tr></thead>
            <tbody>
              <tr><td><b>T2V 文生视频</b></td><td>文本</td><td>概念镜头、空镜、氛围</td><td>人物一致性最差</td></tr>
              <tr><td><b>I2V 图生视频</b></td><td>首帧（可选尾帧）</td><td>已有定妆/关键帧的叙事镜头</td><td>首帧之外的动作不可控</td></tr>
              <tr><td><b>R2V 参考生视频</b></td><td>多张参考图 / 参考视频 / 音频</td><td>角色一致性要求高的镜头</td><td>参考素材质量决定上限</td></tr>
            </tbody>
          </table>
          <p>短剧主干应默认走 I2V 或 R2V：先用图像模型把角色、服装、场景固定下来，再让视频模型只负责「动起来」。这是把不确定性前置到可控环节。</p>
          <figure class="course-fig">
            <svg viewBox="0 0 800 230" role="img" aria-label="文生视频、图生视频、参考生视频三种模式">
              <defs><marker id="f4a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#A0A0AC"/></marker></defs>
              <style>.f4b{fill:#F4F4F8;stroke:#DCDCE4}.f4k{fill:#F2F2FE;stroke:#E0E0FA}.f4t{font-size:12px;fill:#17171C;font-weight:600}.f4s{font-size:11px;fill:#6E6E7A}.f4h{font-size:11px;fill:#4F46E5;letter-spacing:1px}</style>
              <text x="140" y="22" text-anchor="middle" class="f4h">T2V · 文生视频</text>
              <rect x="24" y="38" width="232" height="44" rx="7" class="f4b"/><text x="140" y="65" text-anchor="middle" class="f4t">文本提示词</text>
              <path d="M140,82 V108" stroke="#A0A0AC" marker-end="url(#f4a)"/>
              <rect x="24" y="112" width="232" height="40" rx="7" class="f4b"/><text x="140" y="137" text-anchor="middle" class="f4s">视频模型</text>
              <path d="M140,152 V178" stroke="#A0A0AC" marker-end="url(#f4a)"/>
              <rect x="24" y="182" width="232" height="34" rx="7" class="f4b"/><text x="140" y="204" text-anchor="middle" class="f4s">视频（一致性最弱）</text>

              <text x="400" y="22" text-anchor="middle" class="f4h">I2V · 图生视频</text>
              <rect x="284" y="38" width="232" height="44" rx="7" class="f4b"/><text x="400" y="65" text-anchor="middle" class="f4t">首帧（可选尾帧）</text>
              <path d="M400,82 V108" stroke="#A0A0AC" marker-end="url(#f4a)"/>
              <rect x="284" y="112" width="232" height="40" rx="7" class="f4b"/><text x="400" y="137" text-anchor="middle" class="f4s">视频模型</text>
              <path d="M400,152 V178" stroke="#A0A0AC" marker-end="url(#f4a)"/>
              <rect x="284" y="182" width="232" height="34" rx="7" class="f4b"/><text x="400" y="204" text-anchor="middle" class="f4s">视频（叙事主力）</text>

              <text x="660" y="22" text-anchor="middle" class="f4h">R2V · 参考生视频</text>
              <rect x="544" y="38" width="232" height="44" rx="7" class="f4k"/><text x="660" y="65" text-anchor="middle" class="f4t">参考图 / 视频 / 音频</text>
              <path d="M660,82 V108" stroke="#A0A0AC" marker-end="url(#f4a)"/>
              <rect x="544" y="112" width="232" height="40" rx="7" class="f4k"/><text x="660" y="137" text-anchor="middle" class="f4s">视频模型</text>
              <path d="M660,152 V178" stroke="#A0A0AC" marker-end="url(#f4a)"/>
              <rect x="544" y="182" width="232" height="34" rx="7" class="f4k"/><text x="660" y="204" text-anchor="middle" class="f4s">视频（一致性最强）</text>
            </svg>
            <figcaption><b>图 4 · 三种生成模式。</b>控制条件越强，自由度越低、可复现性越高。短剧主干用 I2V/R2V，把「长什么样」交给图像，把「怎么动」交给视频。</figcaption>
          </figure>
        </section>

        <section class="course-sec">
          <h3>核心参数</h3>
          <table class="compare-table">
            <thead><tr><th>参数</th><th>控制什么</th><th>调法</th></tr></thead>
            <tbody>
              <tr><td>分辨率</td><td>细节与成本</td><td>抽卡用 480P/720P，定稿再上 1080P</td></tr>
              <tr><td>时长</td><td>单镜信息量</td><td>短剧单镜 3–5 秒；30 秒长镜只在必要时用</td></tr>
              <tr><td>帧率</td><td>运动流畅度</td><td>成片统一 24fps；生成帧率与时间线对齐</td></tr>
              <tr><td>seed</td><td>随机种子</td><td>同场景复用稳定色调；跨视角不依赖 seed</td></tr>
              <tr><td>运动强度</td><td>动作幅度</td><td>过高会形变，过低像PPT；先中档再微调</td></tr>
              <tr><td>参考素材</td><td>身份与风格</td><td>锚点图越多越稳，但超过模型上限会互相干扰</td></tr>
              <tr><td>原生音频</td><td>现场声</td><td>只当氛围参考，不替代配音与音效</td></tr>
            </tbody>
          </table>
        </section>

        <section class="course-sec">
          <h3>提示词：确定性编译，而不是文学创作</h3>
          <p>专业流水线里，提示词不是手写散文，而是从镜头契约字段<b>确定性编译</b>出来的：主体、动作、环境、景别、机位、运镜、光线、风格、约束。同一组字段必须产出字节级一致的提示词，否则无法复现、无法追责。</p>
          <ol>
            <li><b>身份锁放最前面</b>：角色名 + 锚点特征。放末尾会被服装/场景描述冲掉。</li>
            <li><b>一个镜头一个动作</b>：不要在一句里塞三个动作。</li>
            <li><b>写可见的东西</b>：「她很难过」不可见，「她低头、肩膀塌下、眼眶发红」可见。</li>
            <li><b>负向约束</b>：不要出现文字、不要换脸、不要额外人物。用模型支持的负向词或参数表达。</li>
          </ol>
          <div class="course-note">判断提示词好坏的标准不是「读起来美」，而是「换一个人照着写，能否得到同一条镜头」。</div>
        </section>

        <section class="course-sec">
          <h3>失败模式与诊断</h3>
          <table class="compare-table">
            <thead><tr><th>现象</th><th>常见原因</th><th>对策</th></tr></thead>
            <tbody>
              <tr><td>人物脸漂移</td><td>参考不足、视角跨度过大、动作太复杂</td><td>加锚点图、缩短镜头、减少动作</td></tr>
              <tr><td>闪烁 / 抖动</td><td>纹理过细、运动强度过高</td><td>降运动强度、换 seed、提高分辨率</td></tr>
              <tr><td>手部 / 物体形变</td><td>遮挡、快速运动、训练数据不足</td><td>改构图避开手部特写，或换镜头设计</td></tr>
              <tr><td>物理错误</td><td>碰撞、负重、液体</td><td>拆分动作，用剪辑掩盖，或走 VFX 修复</td></tr>
              <tr><td>文字乱码</td><td>画面里出现招牌、屏幕、字幕</td><td>后期替换屏幕内容，或避免生成文字</td></tr>
              <tr><td>色彩跳变</td><td>跨镜生成参数不一致</td><td>同场景固定 seed、参考图与色彩描述</td></tr>
              <tr><td>口型不对</td><td>原生音频与台词无关</td><td>后期口型环节修复，不指望生成模型</td></tr>
            </tbody>
          </table>
        </section>

        <section class="course-sec">
          <h3>速度档：Prime 与标准版</h3>
          <p>同一代模型常有「标准版」与「高速版」。高速版保持能力集不变，用更高单价换更短等待，官方定价约高 40%–50%。它适合有人等着看结果的场景（关键镜、客户审片），不适合夜间批量渲染。判断公式：<b>每条节省的时间 × 你每分钟的时间价值 &gt; 每条溢价</b>。</p>
        </section>

        <section class="course-sec">
          <h3>练习</h3>
          <ol>
            <li>用同一组提示词生成同一镜头三次，只改 seed，观察哪些元素稳定、哪些漂移。</li>
            <li>把一个含三个动作的提示词拆成三个镜头，比较成片可看率。</li>
            <li>为一条失败镜头写出诊断：现象、原因、下一步动作。</li>
          </ol>
        </section>
      `
    },
    {
      id: "storyboard",
      eyebrow: "04 · STORYBOARD",
      title: "从剧本到镜头：分镜是成本控制的第一道闸",
      lede: "分镜不是画得好看，而是把「要拍什么」变成「能生成什么」的可执行清单。",
      html: `
        <section class="course-sec">
          <h3>场次、镜头、镜次</h3>
          <p><b>场（scene）</b>是连续时空单位；<b>镜头（shot）</b>是一次不间断的画面；<b>镜次（take）</b>是同一镜头的第几次生成。短剧一集 30 分钟，通常 150–250 个镜头（经验值）。分镜阶段每场先派生 1–3 镜，不要一次铺满，否则返工成本会失控。</p>
        </section>

        <section class="course-sec">
          <h3>镜头表的必备字段</h3>
          <table class="compare-table">
            <thead><tr><th>字段</th><th>为什么必须</th></tr></thead>
            <tbody>
              <tr><td>场次 / 镜号</td><td>全流程唯一引用，返工与审计的锚点</td></tr>
              <tr><td>景别 / 机位 / 运镜</td><td>决定构图与生成参数</td></tr>
              <tr><td>时长</td><td>对齐配音；决定成本（按秒计费）</td></tr>
              <tr><td>同框角色</td><td>硬上限 3；超过就拆镜</td></tr>
              <tr><td>动作 / 情绪</td><td>提示词与表演的依据</td></tr>
              <tr><td>是否对白</td><td>决定是否走 TTS、口型、字幕</td></tr>
              <tr><td>场景 / 时间 / 天气</td><td>连续性检查</td></tr>
              <tr><td>参考素材</td><td>一致性命门</td></tr>
            </tbody>
          </table>
        </section>

        <section class="course-sec">
          <h3>抽卡：把随机性当预算来管理</h3>
          <p>生成视频本质是采样。专业流程不是「一次生成到满意」，而是<b>固定候选数、固定评审标准、固定淘汰规则</b>。常见做法是每镜 4 条候选（经验值），先看可用性，再看表演，最后看构图。</p>
          <ol>
            <li><b>可用性</b>：有没有形变、闪烁、穿帮。不可用直接淘汰，不进入审美比较。</li>
            <li><b>一致性</b>：脸、服装、发型是否与锚点一致。</li>
            <li><b>表演</b>：动作是否可信、情绪是否到位。</li>
            <li><b>构图与光线</b>：是否符合分镜意图。</li>
            <li><b>可剪性</b>：入点出点是否留有余量，能否与前后镜衔接。</li>
          </ol>
          <div class="course-note">候选不覆盖已选定版本。选定后再生成，应另开版本，保留可回溯的记录。</div>
          <figure class="course-fig">
            <svg viewBox="0 0 800 230" role="img" aria-label="四选一候选筛选流程">
              <defs><marker id="f5a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#A0A0AC"/></marker></defs>
              <style>.f5b{fill:#F4F4F8;stroke:#DCDCE4}.f5k{fill:#F2F2FE;stroke:#E0E0FA}.f5t{font-size:12px;fill:#17171C;font-weight:600}.f5s{font-size:10px;fill:#6E6E7A}.f5l{font-size:10px;fill:#A0A0AC}</style>
              <text x="205" y="26" text-anchor="middle" class="f5l">每镜 4 条候选（经验值）</text>
              <rect x="30" y="40" width="80" height="40" rx="7" class="f5b"/><text x="70" y="65" text-anchor="middle" class="f5t">候选 1</text>
              <rect x="120" y="40" width="80" height="40" rx="7" class="f5b"/><text x="160" y="65" text-anchor="middle" class="f5t">候选 2</text>
              <rect x="210" y="40" width="80" height="40" rx="7" class="f5b"/><text x="250" y="65" text-anchor="middle" class="f5t">候选 3</text>
              <rect x="300" y="40" width="80" height="40" rx="7" class="f5b"/><text x="340" y="65" text-anchor="middle" class="f5t">候选 4</text>
              <path d="M380,60 H432" stroke="#A0A0AC" marker-end="url(#f5a)"/>
              <rect x="436" y="34" width="150" height="52" rx="7" class="f5k"/><text x="511" y="57" text-anchor="middle" class="f5t">可用性筛查</text>
              <text x="511" y="73" text-anchor="middle" class="f5s">形变 / 闪烁 / 穿帮</text>
              <path d="M511,86 V134" stroke="#A0A0AC" marker-end="url(#f5a)"/>
              <rect x="436" y="138" width="150" height="52" rx="7" class="f5k"/><text x="511" y="161" text-anchor="middle" class="f5t">一致性与表演</text>
              <text x="511" y="177" text-anchor="middle" class="f5s">脸 / 服装 / 情绪 / 构图</text>
              <path d="M586,164 H634" stroke="#A0A0AC" marker-end="url(#f5a)"/>
              <rect x="638" y="138" width="132" height="52" rx="7" class="f5b"/><text x="704" y="161" text-anchor="middle" class="f5t">选定 1 条</text>
              <text x="704" y="177" text-anchor="middle" class="f5s">其余留档</text>
              <text x="140" y="112" class="f5l">不可用直接淘汰，不进入审美比较</text>
              <path d="M30,96 H380" stroke="#E9E9EF"/>
            </svg>
            <figcaption><b>图 5 · 候选漏斗。</b>先筛「能不能用」，再比「好不好」。把审美判断放在可用性之后，能显著减少返工与无效调用。</figcaption>
          </figure>
        </section>

        <section class="course-sec">
          <h3>连续性检查清单</h3>
          <ul>
            <li>屏幕方向：上一镜左出，下一镜应右入。</li>
            <li>视线：看的方向与被看对象的位置一致。</li>
            <li>道具：杯子、手机、伤口的位置与状态连续。</li>
            <li>服装：领口、袖口、扣子、污渍连续。</li>
            <li>光线：主光方向、色温、强弱连续。</li>
            <li>时间与天气：白天/夜晚、雨/晴不能跳。</li>
          </ul>
        </section>

        <section class="course-sec">
          <h3>previz：先做便宜的版本</h3>
          <p>在正式生成前，用低分辨率、低帧率、甚至静态图加运镜做出 animatic。它的作用不是好看，而是验证三件事：<b>时长对不对、节奏顺不顺、镜头够不够</b>。previz 阶段改一个镜头几乎零成本，成片阶段改一个镜头可能要重跑配音、口型、混音。</p>
        </section>

        <section class="course-sec">
          <h3>练习</h3>
          <ol>
            <li>把一场 2 页剧本拆成镜头表，标出每个镜头的景别、时长、是否对白。</li>
            <li>用 4 条候选的规则，为其中一镜写评审记录：淘汰理由、选中理由。</li>
            <li>找出你镜头表里「说不清为什么要存在」的镜头，删掉它，看叙事是否受损。</li>
          </ol>
        </section>
      `
    },
    {
      id: "voice",
      eyebrow: "05 · VOICE & PERFORMANCE",
      title: "配音与表演：声音是角色的第二张脸",
      lede: "观众能容忍画面差一点，但很难容忍声音不像这个人。配音不是「把字读出来」，是表演。",
      html: `
        <section class="course-sec">
          <h3>声音的五个可调维度</h3>
          <table class="compare-table">
            <thead><tr><th>维度</th><th>是什么</th><th>怎么影响表演</th></tr></thead>
            <tbody>
              <tr><td>音高（pitch）</td><td>声音高低</td><td>紧张时升高，压低声线显威胁或疲惫</td></tr>
              <tr><td>音色（timbre）</td><td>声音的「质地」</td><td>决定年龄感、健康感、地域感</td></tr>
              <tr><td>语速（rate）</td><td>单位时间字数</td><td>加快显急躁，放慢显沉重或强调</td></tr>
              <tr><td>停顿（pause）</td><td>句间/句内静默</td><td>停顿位置比音量更能表达潜台词</td></tr>
              <tr><td>重音（stress）</td><td>强调哪个词</td><td>同一句台词，重音不同，意思完全不同</td></tr>
            </tbody>
          </table>
        </section>

        <section class="course-sec">
          <h3>TTS 的三种用法</h3>
          <ol>
            <li><b>预置音色</b>：开箱即用，成本低，适合配角与群杂。</li>
            <li><b>声音克隆</b>：用 8–20 秒干净参考音频复刻音色，适合主角与常驻角色。必须取得授权。</li>
            <li><b>描述式合成</b>：用自然语言描述音色与风格，适合快速探索，但一致性较弱。</li>
          </ol>
          <p>连续剧的核心不是「哪个模型更像人」，而是<b>同一个角色跨集听起来是不是同一个人</b>。因此每个常驻角色都要有一份音色档案：音高、音色、语速、口音、情绪范围、授权参考片段。</p>
        </section>

        <section class="course-sec">
          <h3>情绪控制：有默认值，也要有回退</h3>
          <p>台词只标「愤怒」「悲伤」是不够的。专业做法是给每个角色设默认情绪与语速，未知情绪统一回落到 neutral，避免模型自由发挥导致跨镜不一致。情绪强度建议分级（1–5），并与配乐强度曲线同源，方便后期对齐。</p>
          <div class="course-note">旁白是独立音轨，不是「没人要的对白」。它有自己的音色、电平与空间感，混音时单独处理。</div>
        </section>

        <section class="course-sec">
          <h3>中文 TTS 的常见坑</h3>
          <ul>
            <li><b>多音字</b>：「行」「重」「长」在上下文里可能读错，需要人工复核或改写。</li>
            <li><b>数字与单位</b>：「2026」「3.5 亿」的读法要显式指定。</li>
            <li><b>专名</b>：人名、地名、品牌名要加发音词典。</li>
            <li><b>气口</b>：长句需要手动插入停顿，否则听起来像背书。</li>
            <li><b>情绪跳变</b>：相邻两句情绪差异过大时，中间要有停顿或呼吸。</li>
          </ul>
        </section>

        <section class="course-sec">
          <h3>校验：机器报警，人来判断</h3>
          <p>用 ASR 把生成音频转回文字，核对字词、说话人、语速与情绪标记。ASR 只能告诉你「可能错了」，不能判断「像不像这个人」。后者要靠相邻片段的 A/B 盲听。</p>
          <p>技术指标上，角色间对白电平差应控制在 ≤1 dB，避免一个角色总是比另一个响。对白还要高于稳态掩蔽 ≥15 dB，这是可懂度的硬门槛。</p>
        </section>

        <section class="course-sec">
          <h3>练习</h3>
          <ol>
            <li>给同一句台词标三种重音位置，生成三条，比较意思变化。</li>
            <li>为一个角色写音色档案，包含五个维度与一段参考音频描述。</li>
            <li>用 ASR 复核一段 30 秒配音，找出至少两个需要人工修正的地方。</li>
          </ol>
        </section>
      `
    },
    {
      id: "lipsync",
      eyebrow: "06 · LIP SYNC",
      title: "口型同步：让嘴「看起来在说」",
      lede: "口型不是画面生成的一部分，而是后期的一道修复工序。它的目标只有一个：让观众不注意到嘴。",
      html: `
        <section class="course-sec">
          <h3>原理：音素到口型</h3>
          <p>语音由音素组成，音素对应可见的嘴部形态，叫<b>视素（viseme）</b>。例如 /p/、/b/、/m/ 需要闭唇，/f/、/v/ 需要上齿碰下唇，/a/ 张嘴，/i/ 嘴角拉开。口型模型要做的是：从音轨推断每个时刻的视素，再把这组口型映射到画面里人物的嘴部。</p>
          <p>难点不在「张嘴」，而在<b>协同发音</b>：连续说话时，一个音的口型会被前后音影响。好的模型会处理这种过渡，差的模型会让嘴像机械开合。</p>
        </section>

        <section class="course-sec">
          <h3>三条技术路线</h3>
          <table class="compare-table">
            <thead><tr><th>路线</th><th>输入</th><th>输出</th><th>代表</th><th>适合</th></tr></thead>
            <tbody>
              <tr><td><b>修复型</b></td><td>已有视频 + 音轨</td><td>同一画面，只改嘴部</td><td>Sync.so、可灵 Lip Sync</td><td>已有生成镜头，保画面一致性</td></tr>
              <tr><td><b>生成型</b></td><td>人物图 + 音轨</td><td>一段新的说话视频</td><td>HeyGen Avatar、Hedra、OmniHuman</td><td>数字人口播、单镜头表演</td></tr>
              <tr><td><b>表演驱动</b></td><td>视频/图 + 驱动信号</td><td>表情、头部、嘴部一起变</td><td>Runway Act-Two</td><td>需要更强表演的镜头</td></tr>
            </tbody>
          </table>
          <div class="course-note">已有镜头只能交给修复型。用生成型等于把画面重新生成一遍，跨镜一致性会断。</div>
          <figure class="course-fig">
            <svg viewBox="0 0 800 290" role="img" aria-label="口型同步的三条技术路线">
              <defs><marker id="f6a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#A0A0AC"/></marker></defs>
              <style>.f6b{fill:#F4F4F8;stroke:#DCDCE4}.f6k{fill:#F2F2FE;stroke:#E0E0FA}.f6t{font-size:12px;fill:#17171C;font-weight:600}.f6s{font-size:11px;fill:#6E6E7A}.f6h{font-size:11px;fill:#4F46E5;font-weight:600}</style>
              <text x="30" y="30" class="f6h">修复型 · 已有镜头走这条</text>
              <rect x="30" y="42" width="200" height="46" rx="7" class="f6k"/><text x="130" y="70" text-anchor="middle" class="f6t">已有视频 + 音轨</text>
              <path d="M230,65 H292" stroke="#A0A0AC" marker-end="url(#f6a)"/>
              <rect x="296" y="42" width="150" height="46" rx="7" class="f6k"/><text x="371" y="70" text-anchor="middle" class="f6t">口型修复模型</text>
              <path d="M446,65 H508" stroke="#A0A0AC" marker-end="url(#f6a)"/>
              <rect x="512" y="42" width="250" height="46" rx="7" class="f6b"/><text x="637" y="70" text-anchor="middle" class="f6s">同一画面，只改嘴部</text>

              <text x="30" y="112" class="f6h" fill="#6E6E7A">生成型</text>
              <rect x="30" y="124" width="200" height="46" rx="7" class="f6b"/><text x="130" y="152" text-anchor="middle" class="f6t">人物图 + 音轨</text>
              <path d="M230,147 H292" stroke="#A0A0AC" marker-end="url(#f6a)"/>
              <rect x="296" y="124" width="150" height="46" rx="7" class="f6b"/><text x="371" y="152" text-anchor="middle" class="f6t">生成式口型</text>
              <path d="M446,147 H508" stroke="#A0A0AC" marker-end="url(#f6a)"/>
              <rect x="512" y="124" width="250" height="46" rx="7" class="f6b"/><text x="637" y="152" text-anchor="middle" class="f6s">新生成一段说话视频</text>

              <text x="30" y="194" class="f6h" fill="#6E6E7A">表演驱动</text>
              <rect x="30" y="206" width="200" height="46" rx="7" class="f6b"/><text x="130" y="234" text-anchor="middle" class="f6t">视频/图 + 驱动信号</text>
              <path d="M230,229 H292" stroke="#A0A0AC" marker-end="url(#f6a)"/>
              <rect x="296" y="206" width="150" height="46" rx="7" class="f6b"/><text x="371" y="234" text-anchor="middle" class="f6t">表演驱动模型</text>
              <path d="M446,229 H508" stroke="#A0A0AC" marker-end="url(#f6a)"/>
              <rect x="512" y="206" width="250" height="46" rx="7" class="f6b"/><text x="637" y="234" text-anchor="middle" class="f6s">表情 + 头动 + 口型</text>
            </svg>
            <figcaption><b>图 6 · 三条口型路线。</b>输入不同，输出也不同：修复型只动嘴，生成型会重造画面，表演驱动连表情与头动一起改。已有镜头选错路线，等于放弃一致性。</figcaption>
          </figure>
        </section>

        <section class="course-sec">
          <h3>什么时候开，什么时候不开</h3>
          <p>口型单价通常是语音的 10–50 倍（经验值），因此必须按镜头条件开启：</p>
          <ul>
            <li><b>开</b>：近景/中近景、正脸或 3/4 侧脸、有对白、嘴部清晰可见。</li>
            <li><b>不开</b>：全景、背影、侧脸超过 45°、嘴被遮挡、无对白、镜头运动过快。</li>
            <li><b>降级</b>：口型失败时回退为「不做口型」，而不是重抽整条镜头。观众对「没做口型」的容忍度，高于对「口型错乱」的容忍度。</li>
          </ul>
        </section>

        <section class="course-sec">
          <h3>同步标准</h3>
          <p>行业参考是 ITU-R BT.1359-1：音频超前 +90 ms 到滞后 −185 ms 之间，观众一般不易察觉。工程目标通常更严，控制在 ≤±25 ms（约一帧）。广播与流媒体交付还要做同步检测，重点检查整体偏移与漂移。</p>
          <table class="compare-table">
            <thead><tr><th>指标</th><th>含义</th><th>怎么看</th></tr></thead>
            <tbody>
              <tr><td>整体偏移</td><td>音频整体早于或晚于画面</td><td>拍手、关门等瞬态声与画面帧对比</td></tr>
              <tr><td>漂移</td><td>偏移随时间累积变大</td><td>片头片尾各测一次，差值即漂移</td></tr>
              <tr><td>开口延迟</td><td>声音起播到嘴张开的时间差</td><td>逐镜抽检，记录异常镜头</td></tr>
            </tbody>
          </table>
        </section>

        <section class="course-sec">
          <h3>失败与回退</h3>
          <ul>
            <li><b>嘴部模糊</b>：修复强度过高或分辨率不足。降低强度、提高输入分辨率。</li>
            <li><b>牙齿/舌头异常</b>：模型对口腔内部建模不足。改构图，减少大张嘴特写。</li>
            <li><b>头部抖动</b>：驱动信号过强。限制头部运动幅度。</li>
            <li><b>表情僵死</b>：只改了嘴，没保留表演。修复型应尽量保留原始表情与眼神。</li>
          </ul>
        </section>

        <section class="course-sec">
          <h3>练习</h3>
          <ol>
            <li>取一条有对白的近景，分别做「不做口型」和「做口型」，让朋友盲看，记录他们的第一反应。</li>
            <li>测一条镜头的开口延迟，判断它是否在 ±25 ms 内。</li>
            <li>为一场戏列出哪些镜头开/不开口型，并写明理由。</li>
          </ol>
        </section>
      `
    },
    {
      id: "sound",
      eyebrow: "07 · SOUND DESIGN",
      title: "四层声音：对白、音乐、音效、环境",
      lede: "成片的声音不是一条轨，而是四层独立生产、最后混合的结构。理解这一点，你就超过了大多数 AI 短剧团队。",
      html: `
        <section class="course-sec">
          <h3>为什么必须分层</h3>
          <p>四层分别是：<b>D 对白</b>（角色说的话）、<b>M 音乐</b>（配乐，角色听不到）、<b>E 音效</b>（脚步、开门、打斗等）、<b>Amb 环境</b>（房间底噪、街道、雨声）。分层的根本原因是它们<b>服务不同的目的、遵循不同的规则、需要独立修改</b>。</p>
          <table class="compare-table">
            <thead><tr><th>层</th><th>作用</th><th>关键规则</th><th>失败表现</th></tr></thead>
            <tbody>
              <tr><td>D 对白</td><td>推进叙事、传递信息</td><td>永远优先，高于掩蔽 ≥15 dB</td><td>听不清、串音、电平跳</td></tr>
              <tr><td>M 音乐</td><td>情绪、节奏、暗示</td><td>按 Cue 写，禁止整集循环</td><td>抢戏、切镜重启、情绪错位</td></tr>
              <tr><td>E 音效</td><td>动作可信、空间真实</td><td>对齐动作帧，误差 ≤1 帧</td><td>打斗像放气、脚步对不上</td></tr>
              <tr><td>Amb 环境</td><td>空间连续、沉浸感</td><td>无缝循环，跨场景交叉淡化</td><td>切镜爆音、房间忽大忽小</td></tr>
            </tbody>
          </table>
          <figure class="course-fig">
            <svg viewBox="0 0 800 330" role="img" aria-label="对白、音乐、音效、环境四层声音总线与输出">
              <defs><marker id="f7a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#A0A0AC"/></marker></defs>
              <style>.f7t{font-size:12px;fill:#17171C;font-weight:600}.f7s{font-size:10px;fill:#6E6E7A}.f7l{font-size:10px;fill:#A0A0AC}.f7w{font-size:12px;fill:#FFFFFF;font-weight:600}</style>
              <text x="24" y="60" class="f7t">D 对白</text><text x="24" y="118" class="f7t">M 音乐</text><text x="24" y="176" class="f7t">E 音效</text><text x="24" y="234" class="f7t">Amb 环境</text>
              <line x1="110" y1="56" x2="520" y2="56" stroke="#E9E9EF"/>
              <line x1="110" y1="114" x2="520" y2="114" stroke="#E9E9EF"/>
              <line x1="110" y1="172" x2="520" y2="172" stroke="#E9E9EF"/>
              <line x1="110" y1="230" x2="520" y2="230" stroke="#E9E9EF"/>
              <rect x="130" y="42" width="90" height="28" rx="5" fill="#F2F2FE" stroke="#E0E0FA"/><rect x="260" y="42" width="70" height="28" rx="5" fill="#F2F2FE" stroke="#E0E0FA"/><rect x="360" y="42" width="120" height="28" rx="5" fill="#F2F2FE" stroke="#E0E0FA"/>
              <rect x="150" y="100" width="320" height="28" rx="5" fill="#EFE9FB" stroke="#D9CEF3"/>
              <rect x="150" y="158" width="36" height="28" rx="5" fill="#FDF0E5" stroke="#F0D3B8"/><rect x="200" y="158" width="36" height="28" rx="5" fill="#FDF0E5" stroke="#F0D3B8"/><rect x="250" y="158" width="36" height="28" rx="5" fill="#FDF0E5" stroke="#F0D3B8"/><rect x="320" y="158" width="36" height="28" rx="5" fill="#FDF0E5" stroke="#F0D3B8"/><rect x="390" y="158" width="36" height="28" rx="5" fill="#FDF0E5" stroke="#F0D3B8"/>
              <rect x="120" y="216" width="400" height="28" rx="5" fill="#E8F5F2" stroke="#C9E3DC"/>
              <path d="M520,56 H542" stroke="#A0A0AC" marker-end="url(#f7a)"/><path d="M520,114 H542" stroke="#A0A0AC" marker-end="url(#f7a)"/>
              <path d="M520,172 H542" stroke="#A0A0AC" marker-end="url(#f7a)"/><path d="M520,230 H542" stroke="#A0A0AC" marker-end="url(#f7a)"/>
              <rect x="546" y="36" width="86" height="220" rx="9" fill="#4F46E5"/>
              <text x="589" y="132" text-anchor="middle" class="f7w">混音</text><text x="589" y="152" text-anchor="middle" class="f7w">总线</text>
              <path d="M632,66 H662" stroke="#A0A0AC" marker-end="url(#f7a)"/>
              <path d="M632,140 H662" stroke="#A0A0AC" marker-end="url(#f7a)"/>
              <path d="M632,214 H662" stroke="#A0A0AC" marker-end="url(#f7a)"/>
              <rect x="666" y="42" width="110" height="50" rx="7" fill="#F4F4F8" stroke="#DCDCE4"/><text x="721" y="63" text-anchor="middle" class="f7t">四路 stem</text><text x="721" y="79" text-anchor="middle" class="f7s">逐帧等长</text>
              <rect x="666" y="112" width="110" height="56" rx="7" fill="#F2F2FE" stroke="#E0E0FA"/><text x="721" y="135" text-anchor="middle" class="f7t">立体声 / 5.1</text><text x="721" y="151" text-anchor="middle" class="f7s">−23 LUFS 母版</text>
              <rect x="666" y="188" width="110" height="50" rx="7" fill="#F4F4F8" stroke="#DCDCE4"/><text x="721" y="209" text-anchor="middle" class="f7t">M&amp;E</text><text x="721" y="225" text-anchor="middle" class="f7s">译制 / 二次配音</text>
              <path d="M300,70 C300,82 300,88 300,98" stroke="#C2410C" stroke-dasharray="4 3" marker-end="url(#f7a)"/>
              <text x="308" y="88" class="f7l" fill="#C2410C">对白闪避 −3~−6 dB</text>
            </svg>
            <figcaption><b>图 7 · 四层声音总线。</b>四层独立生产、统一混音，输出四路 stem、母版与 M&amp;E。对白出现时音乐自动让位，保证可懂度。</figcaption>
          </figure>
        </section>

        <section class="course-sec">
          <h3>Foley 与硬音效</h3>
          <p><b>Foley（拟音）</b>是人工表演出来的日常声音：脚步、衣物摩擦、开门、持物、落座。它追求的是「与动作严丝合缝」，不是「真实录音」。<b>硬音效（hard effects）</b>是预先录制的具体声音：枪声、汽车、电话铃。两者不能混为一谈：Foley 靠表演，硬音效靠素材库。</p>
          <div class="course-note">影视里的打斗声往往比真实更夸张。观众要的是「力感」，不是物理准确。</div>
        </section>

        <section class="course-sec">
          <h3>环境床与房间声</h3>
          <p>每个场景需要一条<b>环境床（ambience bed）</b>，铺满整场。它的循环点必须零爆音、零静音缝隙，跨场景切换要有交叉淡化。否则每次切镜，观众都会听到「房间换了」。</p>
          <p><b>房间声（room tone）</b>是空间本身的底噪与早期反射。室内、室外、大空间的房间声完全不同。对白如果「贴脸干声」，会显得像在录音棚，不像在故事里。</p>
        </section>

        <section class="course-sec">
          <h3>对白优先：可懂度是硬指标</h3>
          <p>AES TD1009 的实践结论：语音需要高于稳态掩蔽 <b>≥15 dB</b> 才能全线索可闻；低到 −15 dB 时可懂度接近于零。这意味着音乐和音效必须为对白让路。</p>
          <ul>
            <li><b>Ducking（闪避）</b>：对白出现时，音乐自动降低 3–6 dB，对白结束再恢复。</li>
            <li><b>EQ 让位</b>：在对白频段（大约 1–4 kHz）给音乐做轻微衰减。</li>
            <li><b>动态控制</b>：压缩器不要压掉辅音，否则「s」「t」会消失。</li>
          </ul>
        </section>

        <section class="course-sec">
          <h3>J/L cut 与音桥</h3>
          <p>声音先于画面进入（J cut）或延续到下一镜（L cut），能让剪辑更顺滑。音桥是用一段连续的声音（雨声、音乐、脚步声）跨过镜头切换，把两个空间连起来。短剧节奏快，音桥是避免「一段一段拼」的关键手法。</p>
        </section>

        <section class="course-sec">
          <h3>stem 与 5.1</h3>
          <p>四路 stem 必须<b>逐帧等长</b>：同样起点、同样时长、样本级对齐。这样混音、返工、译制才能独立进行。5.1 交付时，中置与环绕各下混 −3 dB；<b>关键内容不得只放在 LFE</b>，因为 LFE 不参与下混，立体声观众会丢失信息。</p>
          <p><b>M&amp;E（Music &amp; Effects）</b>是去掉对白的版本，用于译制与二次配音。它要求音乐与音效本身就是独立的，不能从混好的音轨里「抠」出来。</p>
        </section>

        <section class="course-sec">
          <h3>练习</h3>
          <ol>
            <li>找一段 30 秒成片，分别静音音乐、静音音效、静音环境，记录每次观感变化。</li>
            <li>为一场室内戏列 Foley 清单：哪些动作需要拟音，哪些用硬音效。</li>
            <li>做一条 10 秒环境床，检查循环点有没有咔哒声。</li>
          </ol>
        </section>
      `
    },
    {
      id: "music",
      eyebrow: "08 · SCORE",
      title: "配乐：Cue、动机与情绪曲线",
      lede: "配乐不是「找一首好听的歌垫在下面」，而是按场次写出来的叙事结构。",
      html: `
        <section class="course-sec">
          <h3>Cue：配乐的最小单位</h3>
          <p>一条 <b>Cue</b> 是一段有明确入点、出点、情绪与强度的音乐。它可能 15 秒，也可能 2 分钟。专业配乐先做 <b>spotting</b>：和导演一起看片，标记「这里需要音乐」「这里需要停」「这里要打一个点」。短剧一集通常 6–10 条 Cue（经验值），而不是一首歌循环到底。</p>
          <table class="compare-table">
            <thead><tr><th>Cue 字段</th><th>含义</th><th>示例</th></tr></thead>
            <tbody>
              <tr><td>入点 / 出点</td><td>时间码</td><td>01:02:14:08 → 01:02:48:00</td></tr>
              <tr><td>情绪</td><td>主导感受</td><td>压抑 → 爆发</td></tr>
              <tr><td>强度</td><td>1–5 级</td><td>2 → 5</td></tr>
              <tr><td>处理</td><td>淡入淡出、stinger</td><td>2 秒淡入，结尾硬切</td></tr>
              <tr><td>Hit point</td><td>必须对齐的画面点</td><td>耳光落下的那一帧</td></tr>
            </tbody>
          </table>
          <figure class="course-fig">
            <svg viewBox="0 0 800 270" role="img" aria-label="配乐 Cue 时间线与情绪强度曲线">
              <style>.f8t{font-size:11px;fill:#17171C;font-weight:600}.f8s{font-size:10px;fill:#6E6E7A}.f8l{font-size:10px;fill:#A0A0AC}</style>
              <text x="60" y="24" class="f8l">情绪强度</text>
              <line x1="60" y1="210" x2="740" y2="210" stroke="#DCDCE4"/>
              <line x1="60" y1="196" x2="60" y2="224" stroke="#DCDCE4"/><line x1="230" y1="196" x2="230" y2="224" stroke="#DCDCE4"/><line x1="400" y1="196" x2="400" y2="224" stroke="#DCDCE4"/><line x1="570" y1="196" x2="570" y2="224" stroke="#DCDCE4"/><line x1="740" y1="196" x2="740" y2="224" stroke="#DCDCE4"/>
              <text x="60" y="240" text-anchor="middle" class="f8l">0:00</text><text x="230" y="240" text-anchor="middle" class="f8l">0:30</text><text x="400" y="240" text-anchor="middle" class="f8l">1:00</text><text x="570" y="240" text-anchor="middle" class="f8l">1:30</text><text x="740" y="240" text-anchor="middle" class="f8l">2:00</text>
              <line x1="300" y1="60" x2="300" y2="210" stroke="#E9E9EF" stroke-dasharray="4 4"/><line x1="520" y1="60" x2="520" y2="210" stroke="#E9E9EF" stroke-dasharray="4 4"/>
              <text x="306" y="72" class="f8s">场次边界</text>
              <path d="M70,178 C120,150 190,120 230,120 S290,152 300,152 S380,92 460,82 S510,120 520,120 S620,108 730,148" fill="none" stroke="#4F46E5" stroke-width="2"/>
              <circle cx="230" cy="120" r="5" fill="#C2410C"/><circle cx="460" cy="82" r="5" fill="#C2410C"/><circle cx="620" cy="108" r="5" fill="#C2410C"/>
              <text x="230" y="108" text-anchor="middle" class="f8s">H1</text><text x="460" y="70" text-anchor="middle" class="f8s">H2</text><text x="620" y="96" text-anchor="middle" class="f8s">H3</text>
              <rect x="70" y="222" width="220" height="18" rx="4" fill="#F2F2FE" stroke="#E0E0FA"/><text x="180" y="235" text-anchor="middle" class="f8t">Cue 1</text>
              <rect x="300" y="222" width="210" height="18" rx="4" fill="#F2F2FE" stroke="#E0E0FA"/><text x="405" y="235" text-anchor="middle" class="f8t">Cue 2</text>
              <rect x="520" y="222" width="210" height="18" rx="4" fill="#F2F2FE" stroke="#E0E0FA"/><text x="625" y="235" text-anchor="middle" class="f8t">Cue 3</text>
              <line x1="590" y1="36" x2="614" y2="36" stroke="#4F46E5" stroke-width="2"/><text x="620" y="40" class="f8s">强度曲线</text>
              <circle cx="590" cy="56" r="5" fill="#C2410C"/><text x="620" y="60" class="f8s">hit point</text>
            </svg>
            <figcaption><b>图 8 · Cue 时间线。</b>配乐按场次切成 Cue，情绪强度曲线与表演同源；H1–H3 是必须对齐的画面点。Cue 之间可以留白，但不允许整集循环同一段。</figcaption>
          </figure>
        </section>

        <section class="course-sec">
          <h3>动机（Motif）：让音乐记得角色</h3>
          <p><b>主导动机（leitmotif）</b>是给角色、关系或地点绑定的短旋律。它可以在不同场景里变形：大调变小调、快变慢、完整变碎片。观众未必意识到，但会建立「这个人来了」的直觉。短剧不需要复杂交响，三到五个动机就够撑起一季。</p>
        </section>

        <section class="course-sec">
          <h3>情绪曲线：与表演同源</h3>
          <p>配乐强度曲线应与表演情绪曲线同源对齐：同一场戏、同一套强度标尺。否则会出现「演员在哭，音乐在欢快」的错位。判断标准不是「好不好听」，而是<b>音乐是否在观众意识到之前，先一步推动了情绪</b>。</p>
        </section>

        <section class="course-sec">
          <h3>Loop 与 Score 的区别</h3>
          <p>Loop 是循环片段，Score 是为画面写的音乐。Loop 的问题是：观众会在 30 秒内听出重复，然后开始忽略它。专业做法是把 loop 当素材，做分层（节奏层、和声层、旋律层），按情绪强度增减，而不是整段循环。</p>
          <div class="course-note">禁止整集单曲循环。这是 AI 短剧最容易被观众识破的「廉价感」来源之一。</div>
        </section>

        <section class="course-sec">
          <h3>生成式、曲库、定制：三条路线</h3>
          <table class="compare-table">
            <thead><tr><th>路线</th><th>优点</th><th>缺点</th><th>适合</th></tr></thead>
            <tbody>
              <tr><td>生成式 AI</td><td>贴合叙事、可规模化、不重复</td><td>授权条款要逐家核；质量波动</td><td>量产短剧、需要情绪贴合</td></tr>
              <tr><td>授权曲库</td><td>权利清晰、审核好过</td><td>重复、贴合度差、按项目付费</td><td>低预算、快速上线</td></tr>
              <tr><td>定制作曲</td><td>最贴合、最可控</td><td>贵、慢</td><td>重点集、品牌项目</td></tr>
            </tbody>
          </table>
          <p>商业平台常见的组合是：主干用生成式或曲库，重点段落用定制。无论哪条路线，都要记录<b>授权快照</b>：平台、档位、生成时间、条款版本、使用位置。</p>
        </section>

        <section class="course-sec">
          <h3>练习</h3>
          <ol>
            <li>为一场 60 秒戏画情绪曲线，标出 3 个 hit point。</li>
            <li>用同一段画面配两条不同情绪的 Cue，比较叙事含义变化。</li>
            <li>写一份 Cue 表，包含入出点、情绪、强度、处理方式。</li>
          </ol>
        </section>
      `
    },
    {
      id: "mix",
      eyebrow: "09 · MIX & LOUDNESS",
      title: "混音与响度：不是「调大一点」",
      lede: "响度是交付标准，不是个人喜好。观众不会调音量，平台会按标准压缩你。",
      html: `
        <section class="course-sec">
          <h3>响度、电平、峰值：三个不同的东西</h3>
          <ul>
            <li><b>电平（level）</b>：某一瞬间的信号强度，单位 dBFS。</li>
            <li><b>响度（loudness）</b>：人耳感知的整体音量，按 ITU-R BS.1770 测量，单位 LUFS（等同 LKFS）。</li>
            <li><b>真峰值（true peak）</b>：考虑数模转换后可能出现的峰值，单位 dBTP。</li>
          </ul>
          <p>把电平调高不等于响度变高：压缩动态可以短期提升响度，但会牺牲层次。专业混音追求的是「在标准响度下仍有动态」。</p>
        </section>

        <section class="course-sec">
          <h3>交付标准</h3>
          <table class="compare-table">
            <thead><tr><th>版本</th><th>目标响度</th><th>真峰值</th><th>说明</th></tr></thead>
            <tbody>
              <tr><td>归档母版</td><td>−23.0 LUFS（QC 容差 ±0.2 LU）</td><td>≤ −1 dBTP</td><td>EBU R 128，整节目测量，不按对白门控</td></tr>
              <tr><td>广播版</td><td>−24 LKFS</td><td>&lt; −2 dBTP</td><td>按广播规范派生</td></tr>
              <tr><td>流媒体版</td><td>−23 ~ −27 LKFS</td><td>按平台要求</td><td>由母版派生，不重新混音</td></tr>
            </tbody>
          </table>
          <p>注意：平台会自己做响度归一化。你交付的版本如果过响，平台压下来后动态会更差；过轻则会被整体抬高，底噪暴露。所以按标准交付，不要「偷偷调大」。</p>
          <figure class="course-fig">
            <svg viewBox="0 0 800 230" role="img" aria-label="响度与真峰值目标区间示意">
              <style>.f9t{font-size:12px;fill:#17171C;font-weight:600}.f9s{font-size:10px;fill:#6E6E7A}.f9l{font-size:10px;fill:#A0A0AC}</style>
              <text x="70" y="28" class="f9t">节目响度（LUFS）</text>
              <rect x="70" y="52" width="660" height="36" rx="5" fill="#F4F4F8" stroke="#E9E9EF"/>
              <rect x="70" y="52" width="248" height="36" fill="#EEF2FF"/>
              <rect x="351" y="52" width="17" height="36" fill="#1F8A5B"/>
              <rect x="483" y="52" width="247" height="36" fill="#FDECEC"/>
              <line x1="359" y1="44" x2="359" y2="96" stroke="#17171C" stroke-width="2"/>
              <text x="359" y="112" text-anchor="middle" class="f9t">−23.0 LUFS</text>
              <text x="359" y="128" text-anchor="middle" class="f9s">归档母版目标（±0.2 LU）</text>
              <text x="70" y="112" text-anchor="middle" class="f9l">−30</text><text x="235" y="112" text-anchor="middle" class="f9l">−26</text><text x="483" y="112" text-anchor="middle" class="f9l">−20</text><text x="730" y="112" text-anchor="middle" class="f9l">−14</text>
              <text x="150" y="75" text-anchor="middle" class="f9s">过轻：底噪暴露</text><text x="610" y="75" text-anchor="middle" class="f9s">过响：平台压缩后动态变差</text>
              <text x="70" y="164" class="f9t">真峰值（dBTP）</text>
              <rect x="70" y="180" width="660" height="22" rx="4" fill="#F4F4F8" stroke="#E9E9EF"/>
              <rect x="70" y="180" width="560" height="22" fill="#E8F5F2"/>
              <line x1="630" y1="174" x2="630" y2="208" stroke="#C2410C" stroke-width="2"/>
              <text x="630" y="222" text-anchor="middle" class="f9s" fill="#C2410C">≤ −1 dBTP</text>
            </svg>
            <figcaption><b>图 9 · 响度目标区间。</b>响度是整节目的平均值，真峰值是瞬时的上限。母版落在绿色带内、峰值不越过红线，才算可交付。</figcaption>
          </figure>
        </section>

        <section class="course-sec">
          <h3>混音顺序</h3>
          <ol>
            <li><b>对白</b>：先保证每一句都清楚、电平一致（角色间 ≤1 dB）。</li>
            <li><b>音效</b>：对齐动作，建立空间与力感。</li>
            <li><b>环境</b>：铺满场景，填补静默，建立连续性。</li>
            <li><b>音乐</b>：最后进，按对白让位，做 ducking。</li>
            <li><b>总线处理</b>：整体压缩、限幅，检查真峰值。</li>
          </ol>
          <p>顺序不能反。先把音乐混得很满，再塞对白，最后只能靠压对白来让位，结果是「听得见但听不清」。</p>
        </section>

        <section class="course-sec">
          <h3>监听环境</h3>
          <p>AES TD1009 给出的参考：混音室约 76–78 dB SPL，家庭电视中位约 58 dB SPL，影院/回音壁约 65 dB SPL。这意味着你的混音在安静环境里好听，不代表观众在手机上听得好。专业做法是<b>至少用手机外放和耳机各听一遍</b>。</p>
        </section>

        <section class="course-sec">
          <h3>练习</h3>
          <ol>
            <li>用响度表测一段成片，记录 LUFS 与真峰值，判断是否达标。</li>
            <li>把一段对白分别与「无音乐」「有音乐但无 ducking」「有 ducking」比较，记录可懂度。</li>
            <li>用手机外放听你的混音，找出第一个听不清的词。</li>
          </ol>
        </section>
      `
    },
    {
      id: "master",
      eyebrow: "10 · MASTER & QC",
      title: "母版与 QC：让片子「能被平台接收」",
      lede: "成片不是终点，合规母版才是。技术 QC 不过，内容再好也上不了线。",
      html: `
        <section class="course-sec">
          <h3>唯一母版原则</h3>
          <p>先生成一个 16:9 open gate 母版，再派生 2.39:1、9:16、平台版。不要为每个画幅重复生成：重复生成会导致人物、光线、色彩不一致，而且成本翻倍。派生关系要记录 parent_asset_id，形成血缘。</p>
          <figure class="course-fig">
            <svg viewBox="0 0 800 260" role="img" aria-label="唯一母版派生三种画幅">
              <defs><marker id="f10a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#A0A0AC"/></marker></defs>
              <style>.f10t{font-size:12px;fill:#17171C;font-weight:600}.f10s{font-size:10px;fill:#6E6E7A}.f10l{font-size:10px;fill:#A0A0AC}</style>
              <rect x="60" y="50" width="320" height="180" rx="5" fill="#F4F4F8" stroke="#DCDCE4"/>
              <rect x="60" y="73" width="320" height="134" fill="none" stroke="#4F46E5" stroke-dasharray="5 4"/>
              <rect x="170" y="50" width="100" height="180" fill="none" stroke="#C2410C" stroke-dasharray="5 4"/>
              <text x="220" y="228" text-anchor="middle" class="f10t">16:9 open gate 母版</text>
              <text x="220" y="244" text-anchor="middle" class="f10s">唯一生成 · 其余全部派生</text>
              <path d="M384,88 H492" stroke="#A0A0AC" marker-end="url(#f10a)"/>
              <path d="M384,140 H492" stroke="#A0A0AC" marker-end="url(#f10a)"/>
              <path d="M384,192 H492" stroke="#A0A0AC" marker-end="url(#f10a)"/>
              <rect x="496" y="24" width="270" height="62" rx="7" fill="#FFFFFF" stroke="#DCDCE4"/>
              <rect x="508" y="34" width="96" height="40" fill="#F2F2FE" stroke="#E0E0FA"/><text x="620" y="49" class="f10t">2.39:1 主母版</text><text x="620" y="68" class="f10s">电影画幅</text>
              <rect x="496" y="96" width="270" height="62" rx="7" fill="#FFFFFF" stroke="#DCDCE4"/>
              <rect x="508" y="104" width="64" height="44" fill="#F2F2FE" stroke="#E0E0FA"/><text x="620" y="121" class="f10t">16:9 平台版</text><text x="620" y="140" class="f10s">横屏通用</text>
              <rect x="496" y="168" width="270" height="62" rx="7" fill="#FFFFFF" stroke="#DCDCE4"/>
              <rect x="516" y="178" width="26" height="44" fill="#FDECEC" stroke="#F0C9C9"/><text x="620" y="193" class="f10t">9:16 竖屏版</text><text x="620" y="212" class="f10s">短剧主战场，构图需重排</text>
            </svg>
            <figcaption><b>图 10 · 唯一母版派生。</b>虚线标出各画幅的裁切范围。竖屏不是「竖着裁一刀」，主体要按中上部重新构图。</figcaption>
          </figure>
        </section>

        <section class="course-sec">
          <h3>技术规格</h3>
          <table class="compare-table">
            <thead><tr><th>项目</th><th>标准</th><th>为什么</th></tr></thead>
            <tbody>
              <tr><td>帧率</td><td>24fps，全片统一</td><td>电影感；混帧会导致抖动</td></tr>
              <tr><td>色彩</td><td>Rec.709 SDR</td><td>平台兼容性最好</td></tr>
              <tr><td>色彩一致性</td><td>镜头间 ΔE ≤3，肤色 ≤2</td><td>观众对肤色跳变最敏感</td></tr>
              <tr><td>音频</td><td>24-bit / 48 kHz</td><td>影视交付标准</td></tr>
              <tr><td>时间码</td><td>起点 01:00:00:00</td><td>行业惯例，便于回批</td></tr>
              <tr><td>头尾黑场</td><td>≥1 帧且 ≤1 秒</td><td>平台与广播的技术要求</td></tr>
              <tr><td>字幕</td><td>软字幕，母版禁硬字幕</td><td>便于多语言与平台处理</td></tr>
            </tbody>
          </table>
        </section>

        <section class="course-sec">
          <h3>QC 清单</h3>
          <ul>
            <li>响度与真峰值：−23.0 LUFS ±0.2，≤ −1 dBTP。</li>
            <li>四路 stem 逐帧等长，Σ 与母版差 ≤0.1 LU。</li>
            <li>音画同步：整体偏移、漂移、开口延迟。</li>
            <li>黑帧、闪帧、banding、爆音、相位问题。</li>
            <li>字幕时长、行数、每行字数、安全区。</li>
            <li>AI 标识：显式、隐式、导出文件三类齐备。</li>
            <li>权利链与授权快照可追溯。</li>
          </ul>
        </section>

        <section class="course-sec">
          <h3>AI 标识与合规</h3>
          <p>AI 生成内容需要三类标识：画面内显式标识、文件元数据隐式标识、交付文件中的说明。缺任何一类，平台都可能拒收。音乐与音效还要登记平台、档位、条款快照与使用位置，供权利链追溯。</p>
          <div class="course-note">合规不是上线前补一张表，而是从第一次生成就开始记录。</div>
        </section>

        <section class="course-sec">
          <h3>练习</h3>
          <ol>
            <li>按 QC 清单检查一条成片，写出通过项与不通过项。</li>
            <li>用同一母版派生 2.39、16:9、9:16 三个版本，比较构图是否需要重排。</li>
            <li>找一条硬字幕的片子，说明为什么母版不允许硬字幕。</li>
          </ol>
        </section>
      `
    },
    {
      id: "models",
      eyebrow: "11 · MODEL SELECTION",
      title: "模型选型：商业平台怎么做，你该怎么做",
      lede: "选型的本质不是找「最强模型」，而是找「在你的预算、授权与交付约束下，最不容易失败的那一组」。",
      html: `
        <section class="course-sec">
          <h3>六条选型准则</h3>
          <ol>
            <li><b>能力匹配</b>：先看能力矩阵（参考图、首尾帧、多镜头、运镜、原生音频、时间戳），参数缺失不得默认「支持」。</li>
            <li><b>一致性</b>：角色跨镜/跨集是否稳定，比单帧画质更重要。</li>
            <li><b>成本</b>：视频按秒、口型按条、TTS 按字符、音乐按分钟。先控视频与口型两个大头。</li>
            <li><b>授权</b>：音乐与人脸/声音克隆优先确认商用档位，别等成片再换。</li>
            <li><b>可复现</b>：同参数能否复现同结果；seed、版本、提示词是否可记录。</li>
            <li><b>可达性</b>：网络、限流、排队、地域。生产环境优先稳定可达的端点。</li>
          </ol>
        </section>

        <section class="course-sec">
          <h3>按镜头路由，而不是全片一个模型</h3>
          <table class="compare-table">
            <thead><tr><th>镜头类型</th><th>路由策略</th><th>理由</th></tr></thead>
            <tbody>
              <tr><td>关键情绪镜</td><td>高质量档 + 更多候选</td><td>决定观众记忆点</td></tr>
              <tr><td>过场 / 氛围镜</td><td>经济档 + 少量候选</td><td>可被剪辑弱化</td></tr>
              <tr><td>动作 / 物理复杂</td><td>擅长大运动或物理的模型</td><td>避免形变</td></tr>
              <tr><td>口播 / 数字人</td><td>生成型口型模型</td><td>不需要已有镜头</td></tr>
              <tr><td>已有镜头修口型</td><td>修复型口型模型</td><td>保画面一致性</td></tr>
            </tbody>
          </table>
          <p>每类至少一主一备。主用负责 80% 的稳定产出，备用负责故障切换与特殊镜头。</p>
          <figure class="course-fig">
            <svg viewBox="0 0 800 300" role="img" aria-label="按镜头类型路由模型的示意">
              <defs><marker id="f11a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#A0A0AC"/></marker></defs>
              <style>.f11b{fill:#F4F4F8;stroke:#DCDCE4}.f11k{fill:#F2F2FE;stroke:#E0E0FA}.f11t{font-size:11px;fill:#17171C;font-weight:600}.f11s{font-size:10px;fill:#6E6E7A}.f11l{font-size:10px;fill:#A0A0AC}</style>
              <text x="24" y="24" class="f11l">镜头类型</text><text x="300" y="24" class="f11l">路由策略</text><text x="580" y="24" class="f11l">模型示例</text>
              <rect x="24" y="36" width="170" height="36" rx="6" class="f11k"/><text x="109" y="59" text-anchor="middle" class="f11t">关键情绪镜</text>
              <rect x="24" y="86" width="170" height="36" rx="6" class="f11b"/><text x="109" y="109" text-anchor="middle" class="f11t">过场 / 氛围镜</text>
              <rect x="24" y="136" width="170" height="36" rx="6" class="f11b"/><text x="109" y="159" text-anchor="middle" class="f11t">动作 / 物理复杂</text>
              <rect x="24" y="186" width="170" height="36" rx="6" class="f11b"/><text x="109" y="209" text-anchor="middle" class="f11t">口播 / 数字人</text>
              <rect x="24" y="236" width="170" height="36" rx="6" class="f11k"/><text x="109" y="259" text-anchor="middle" class="f11t">已有镜头修口型</text>
              <rect x="300" y="36" width="180" height="36" rx="6" class="f11b"/><text x="390" y="59" text-anchor="middle" class="f11s">高质量档 + 更多候选</text>
              <rect x="300" y="86" width="180" height="36" rx="6" class="f11b"/><text x="390" y="109" text-anchor="middle" class="f11s">经济档 + 少量候选</text>
              <rect x="300" y="136" width="180" height="36" rx="6" class="f11b"/><text x="390" y="159" text-anchor="middle" class="f11s">擅长大运动的模型</text>
              <rect x="300" y="186" width="180" height="36" rx="6" class="f11b"/><text x="390" y="209" text-anchor="middle" class="f11s">生成型口型</text>
              <rect x="300" y="236" width="180" height="36" rx="6" class="f11b"/><text x="390" y="259" text-anchor="middle" class="f11s">修复型口型</text>
              <rect x="580" y="36" width="190" height="36" rx="6" class="f11b"/><text x="675" y="59" text-anchor="middle" class="f11s">Wan 3.0 Prime</text>
              <rect x="580" y="86" width="190" height="36" rx="6" class="f11b"/><text x="675" y="109" text-anchor="middle" class="f11s">Wan 3.0 · 480P/720P</text>
              <rect x="580" y="136" width="190" height="36" rx="6" class="f11b"/><text x="675" y="159" text-anchor="middle" class="f11s">Seedance 2.5 / Kling</text>
              <rect x="580" y="186" width="190" height="36" rx="6" class="f11b"/><text x="675" y="209" text-anchor="middle" class="f11s">HeyGen / Hedra / OmniHuman</text>
              <rect x="580" y="236" width="190" height="36" rx="6" class="f11b"/><text x="675" y="259" text-anchor="middle" class="f11s">Sync.so / 可灵 Lip Sync</text>
              <path d="M194,54 H292" stroke="#A0A0AC" marker-end="url(#f11a)"/><path d="M194,104 H292" stroke="#A0A0AC" marker-end="url(#f11a)"/><path d="M194,154 H292" stroke="#A0A0AC" marker-end="url(#f11a)"/><path d="M194,204 H292" stroke="#A0A0AC" marker-end="url(#f11a)"/><path d="M194,254 H292" stroke="#A0A0AC" marker-end="url(#f11a)"/>
              <path d="M480,54 H572" stroke="#A0A0AC" marker-end="url(#f11a)"/><path d="M480,104 H572" stroke="#A0A0AC" marker-end="url(#f11a)"/><path d="M480,154 H572" stroke="#A0A0AC" marker-end="url(#f11a)"/><path d="M480,204 H572" stroke="#A0A0AC" marker-end="url(#f11a)"/><path d="M480,254 H572" stroke="#A0A0AC" marker-end="url(#f11a)"/>
            </svg>
            <figcaption><b>图 11 · 按镜头路由。</b>不是全片一个模型，而是按镜头价值与类型分配预算。关键镜买质量，过场镜买效率，已有镜头修口型只能走修复型。</figcaption>
          </figure>
        </section>

        <section class="course-sec">
          <h3>商业平台的声音方案</h3>
          <table class="compare-table">
            <thead><tr><th>平台 / 方案</th><th>对白</th><th>音乐</th><th>音效</th><th>关键取舍</th></tr></thead>
            <tbody>
              <tr><td>Dashverse（Frameo.AI）</td><td>ElevenLabs v3</td><td>ElevenLabs Music</td><td>公开资料未单列</td><td>从曲库转向流程内生成，追求贴合与可扩展</td></tr>
              <tr><td>腾讯云 AI 短漫剧</td><td>混元语音（多方言/复刻）</td><td>未点名</td><td>「语音与音效匹配」</td><td>全栈国产化、算法备案、IP 授权</td></tr>
              <tr><td>国内通用工具链</td><td>CosyVoice、讯飞、阿里 TTS</td><td>Mureka、ACE-Step、曲库</td><td>素材库为主</td><td>成本优先，音效普遍是短板</td></tr>
              <tr><td>海外通用工具链</td><td>ElevenLabs、Murf</td><td>Suno、Lyria、ElevenLabs Music</td><td>ElevenLabs SFX</td><td>质量优先，但要逐家核商用授权</td></tr>
            </tbody>
          </table>
          <p>共同规律：<b>语音投入最大，音乐两条路线（生成或曲库），音效最容易被省略</b>。四层声音做完整的团队，在观感上会明显区别于「加 BGM」的团队。</p>
        </section>

        <section class="course-sec">
          <h3>三套可落地的组合</h3>
          <table class="compare-table">
            <thead><tr><th>组合</th><th>文本</th><th>图像</th><th>视频</th><th>语音</th><th>音乐</th><th>口型</th></tr></thead>
            <tbody>
              <tr><td>成本 / 国内合规</td><td>DeepSeek V4-Pro</td><td>Seedream 5 Flash</td><td>Wan 3.0</td><td>Qwen TTS</td><td>ACE-Step 1.5</td><td>可灵 Avatar</td></tr>
              <tr><td>质量优先（可出海）</td><td>GPT-6 Astra / Claude</td><td>Nano Banana 2.1 / GPT Image 2.5</td><td>Wan 3.0 / Seedance 2.5</td><td>Eleven v4</td><td>ElevenLabs Music / Mureka V9</td><td>Sync.so / HeyGen</td></tr>
              <tr><td>开源自托管</td><td>Kimi K3</td><td>Qwen-Image 3</td><td>MiniMax H3</td><td>CosyVoice 3</td><td>ACE-Step 1.5</td><td>开源方案</td></tr>
            </tbody>
          </table>
        </section>

        <section class="course-sec">
          <h3>订阅套餐的边界</h3>
          <p>订阅制套餐（如 Token Plan）通常只允许在编程工具、智能体工具里交互使用，<b>禁止后端、脚本、批量调用</b>。流水线属于自动化调用，必须使用按量付费的 Key。把套餐额度当渲染预算，既不符合条款，也会在高峰期被限流。</p>
        </section>

        <section class="course-sec">
          <h3>练习</h3>
          <ol>
            <li>为你的项目写一份选型说明：六类各选谁、为什么、备选是谁、切换条件是什么。</li>
            <li>列出三项「如果预算砍半，先降哪类模型」的决策与理由。</li>
            <li>核对一次音乐授权：平台、档位、是否允许影视商用、是否允许再分发。</li>
          </ol>
        </section>
      `
    },
    {
      id: "platforms",
      eyebrow: "12 · PLATFORM STRATEGY",
      title: "商业平台的关键方案：八组取舍与真实对照",
      lede: "平台不是「谁的模型强谁赢」，而是在 IP、制作、分发三层里至少握住一层，再用分发规则反向规定制作方案。",
      html: `
        <section class="course-sec">
          <h3>先看结论</h3>
          <p>把主流平台拆开看，会发现它们在八个关键位置上做选择。这些选择不是技术偏好，而是商业位置决定的：</p>
          <div class="course-grid">
            <div class="course-kpi"><b>握 IP</b><p>番茄、书旗、阅文：用已有故事供给压低原创风险，把改编权变成上游壁垒。</p></div>
            <div class="course-kpi"><b>握模型 / 工具</b><p>字节 Seedance、快手可灵、腾讯混元、阿里通义、昆仑 SkyReels：自研或深度绑定，控制成本与产能。</p></div>
            <div class="course-kpi"><b>握分发</b><p>抖音、红果、微信、ReelShort：谁掌握用户与付费入口，谁决定分账系数与内容偏好。</p></div>
          </div>
          <div class="course-note">公开报道显示，纯 AI 流水线内容的收益系数正在被压低，而「真人 + AI 融合」在部分平台可拿到更高分账。这意味着：<b>技术方案必须从分发规则倒推</b>，而不是先选模型再找平台。</div>
          <figure class="course-fig">
            <svg viewBox="0 0 800 210" role="img" aria-label="平台价值链：IP、制作、分发、变现">
              <defs><marker id="f13a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#A0A0AC"/></marker></defs>
              <style>.f13t{font-size:13px;fill:#17171C;font-weight:600}.f13s{font-size:10px;fill:#6E6E7A}.f13l{font-size:10px;fill:#A0A0AC}</style>
              <text x="30" y="36" class="f13l">平台至少握住其中一层，否则只能赚加工费</text>
              <rect x="30" y="58" width="160" height="70" rx="8" fill="#F2F2FE" stroke="#E0E0FA"/><text x="110" y="86" text-anchor="middle" class="f13t">IP</text><text x="110" y="107" text-anchor="middle" class="f13s">番茄 / 书旗 / 阅文</text>
              <path d="M194,93 H214" stroke="#A0A0AC" marker-end="url(#f13a)"/>
              <rect x="220" y="58" width="160" height="70" rx="8" fill="#F4F4F8" stroke="#DCDCE4"/><text x="300" y="86" text-anchor="middle" class="f13t">制作</text><text x="300" y="107" text-anchor="middle" class="f13s">Dramagic / 可灵 / 混元 / 纳逗</text>
              <path d="M384,93 H404" stroke="#A0A0AC" marker-end="url(#f13a)"/>
              <rect x="410" y="58" width="160" height="70" rx="8" fill="#F4F4F8" stroke="#DCDCE4"/><text x="490" y="86" text-anchor="middle" class="f13t">分发</text><text x="490" y="107" text-anchor="middle" class="f13s">抖音 / 红果 / 微信 / ReelShort</text>
              <path d="M574,93 H594" stroke="#A0A0AC" marker-end="url(#f13a)"/>
              <rect x="600" y="58" width="170" height="70" rx="8" fill="#E8F5F2" stroke="#C9E3DC"/><text x="685" y="86" text-anchor="middle" class="f13t">变现</text><text x="685" y="107" text-anchor="middle" class="f13s">分账 / 广告 / 投流 / 付费解锁</text>
              <text x="110" y="158" text-anchor="middle" class="f13l">故事供给</text>
              <text x="300" y="158" text-anchor="middle" class="f13l">产能与成本</text>
              <text x="490" y="158" text-anchor="middle" class="f13l">用户与规则</text>
              <text x="685" y="158" text-anchor="middle" class="f13l">现金流</text>
            </svg>
            <figcaption><b>图 13 · 平台价值链。</b>字节用番茄 IP + Dramagic 制作 + 抖音/红果分发；快手用可灵 + 星芒；腾讯用混元 + 微信流量；阿里用通义 + 书旗 IP。制作团队通常只占「制作」一环。</figcaption>
          </figure>
        </section>

        <section class="course-sec">
          <h3>八组关键取舍（总表）</h3>
          <div class="table-scroll"><table class="compare-table">
            <thead><tr><th>取舍</th><th>选项 A</th><th>选项 B</th><th>谁更适合 A</th><th>谁更适合 B</th></tr></thead>
            <tbody>
              <tr><td><b>生产模式</b></td><td>全自动 Agent</td><td>半自动工作台 / 自建工具链</td><td>个人试水、低端批量</td><td>上线精品、团队化产能</td></tr>
              <tr><td><b>内容形态</b></td><td>AI 仿真人</td><td>2D / 3D 漫剧、真人 + AI</td><td>平台系数高、剧情类</td><td>成本敏感、题材适配</td></tr>
              <tr><td><b>视频模型</b></td><td>单一旗舰</td><td>多模型路由 / 自研</td><td>小团队、快速起步</td><td>平台方、规模化产能</td></tr>
              <tr><td><b>一致性</b></td><td>参考图资产库</td><td>微调 LoRA / 数字人换脸</td><td>多项目复用、版权清晰</td><td>固定 IP、特定演员</td></tr>
              <tr><td><b>声音</b></td><td>云端 TTS + 生成音乐</td><td>真人配音 + 曲库 / 定制</td><td>量产、多语种</td><td>精品、强表演</td></tr>
              <tr><td><b>口型</b></td><td>模型原生口型</td><td>后期 lip sync 修复</td><td>口播、数字人</td><td>已有镜头、出海译制</td></tr>
              <tr><td><b>成本结构</b></td><td>按秒 API</td><td>订阅套餐 / 自建 GPU</td><td>波动产能、试错</td><td>稳定大批量、长期</td></tr>
              <tr><td><b>分发</b></td><td>平台分账</td><td>投流 / 自有 App</td><td>内容型团队</td><td>有资金、有海外渠道</td></tr>
            </tbody>
          </table></div>
        </section>

        <section class="course-sec">
          <h3>1. 生产模式：全自动、半自动、自建</h3>
          <p><b>全自动 Agent</b> 的代表是字节小云雀：一句话生成剧本，几分钟出人设、大纲、分镜，再线性成片。公开测评显示它连续包月约 39 元、上手最快，但成片存在站位错误、越轴、镜头不衔接等问题，更适合试玩与低端产能。</p>
          <p><b>半自动工作台</b> 的代表是万兴剧厂、爱奇艺纳逗 Pro：人负责剧本、资产与关键决策，工具负责拆镜、生成、资产复用。纳逗 Pro 的分镜提示词会包含景别、构图、运镜、音效与音乐，专业度高；万兴剧厂会自动拆镜并考虑轴线，但拆得过粗时反而增加生成失败率。</p>
          <p><b>自建工具链</b> 的代表是中文在线「次元神笔」、360「纳米漫剧流水线」、昆仑万维「天工短剧工作台 + SkyReels」。它们把流程拆成 7–11 个标准环节，用角色库与固定流程压制随机性，适合稳定产能与多项目复用。</p>
          <div class="course-note">判断标准：如果剧本还需要人改、镜头还需要人挑，就不要买「全自动」的账。全自动省的是操作时间，不是判断时间。</div>
        </section>

        <section class="course-sec">
          <h3>2. 内容形态：平台系数比模型跑分更重要</h3>
          <p>2026 年 2 月红果漫剧分账规则把品类拆成 7 类，并用「类型系数」直接调节收益。公开报道给出的数字是：仿真人剧系数维持 <b>60 倍</b>；2D 从 <b>50 倍降到 40 倍</b>；AI 仿真人解说漫从至少 10 倍降到 <b>5 倍</b>。</p>
          <p>这组系数解释了为什么平台「偏爱仿真人」：3D 与真人素材多、表演不易崩；2D 容易出现肢体崩坏。有制片人测算，精品 2D 成本约 3 万元、爆款率 10%–13%，系数降 10 个点后回本很难。</p>
          <p>同时，多家平台在 2026 年推出扶持政策，方向一致：<b>压低纯 AI 流水线，鼓励真人 + AI 融合</b>。公开报道提到抖音/红果对真人 + AI 融合内容分账最高 95%，爱奇艺独家首发 100%，B 站承担 30%–100% 制作成本、分成最高 80%。</p>
          <div class="course-note">结论：先选平台与品类，再决定用仿真人、2D 还是真人 + AI。反过来做，很可能做出「技术很好但系数很低」的内容。</div>
        </section>

        <section class="course-sec">
          <h3>3. 视频模型：平台自研，团队路由</h3>
          <p>平台方的选择很清楚：字节用 Seedance，快手用可灵，腾讯用混元，阿里用通义万相，昆仑用 SkyReels。自研的目的不是「跑分第一」，而是把单位成本、排队与迭代节奏握在自己手里。</p>
          <p>制作团队则更适合<b>多模型路由</b>。公开测评给出的能力侧写是：Seedance 2.5 支持 30 秒、4K，多镜头一致性较好；可灵 3.0 单次 15 秒，智能分镜与中文口型强，适合剧情；Vidu 支持最多 7 个参考主体、单条约 1.5–3 元，适合批量预演；海螺 H3 的微表情与动作见长；Wan 3.0 单镜 30 秒、走开源长视频路线；Veo 3.1 单条最长 148 秒、支持原生音频，按秒约 0.15–0.40 美元，适合出海精品。</p>
          <p>平台的通用做法是：关键镜用高质量档，过场镜用经济档，口播/数字人用生成型口型，已有镜头修口型用修复型。没有平台会全片押一个模型。</p>
        </section>

        <section class="course-sec">
          <h3>4. 一致性：资产库是工业化的前提</h3>
          <p>三种主流方案：<b>参考图资产库</b>（角色、场景、道具都存成可复用资产）、<b>微调 LoRA</b>（针对固定 IP 或演员训练小模型）、<b>数字人 / 换脸</b>（用真人素材驱动）。</p>
          <p>平台级产品几乎都选第一种：万兴剧厂从剧本「资产提取」角色、场景、道具并批量生成分镜；中文在线用角色库统一角色；360 用固定流水线环节保证统一。原因是资产库能跨项目复用、版权链清晰、可审计。</p>
          <p>微调适合固定 IP 的长期系列，但迭代慢、迁移成本高。换脸/数字人效果直接，却最容易踩肖像权与演员授权的红线，商业平台通常要求单独授权与 AI 标识。</p>
        </section>

        <section class="course-sec">
          <h3>5. 声音：差异化在「分层」，不在「换模型」</h3>
          <p>平台普遍把语音当基础设施：预置音色 + 声音克隆 + 情绪控制。海外标杆 Dashverse 用 ElevenLabs v3 做对白、ElevenLabs Music 做配乐，理由是控制粒度细、音色库适合连续剧；国内平台多用自研或国产 TTS，强调中文、方言与成本。</p>
          <p>音乐有两条路线：<b>生成式</b>（贴合叙事、可规模化、无重复）与<b>授权曲库</b>（权利清晰、审核稳）。商业平台常按项目分层：主干用生成或曲库，重点段落定制。音效则普遍是短板，多数仍靠素材库 + 人工挂载。</p>
          <div class="course-note">声音的竞争力不在「用了哪家 TTS」，而在四层总线是否完整：对白清楚、音乐让位、音效对帧、环境连续。只加 BGM 的团队，观众三秒就能听出来。</div>
        </section>

        <section class="course-sec">
          <h3>6. 口型与出海：本地化成本要前置</h3>
          <p>口型有两条路线：模型<b>原生口型</b>（如可灵 3.0 的中文口型）与<b>后期 lip sync 修复</b>。口播/数字人适合原生；已有镜头、需要跨语种重配的，适合修复型。</p>
          <p>出海不是「加字幕」：ReelShort 这类平台要求竖屏、强钩子、付费解锁。公开数据显示其 AI 剧占比在 9 个月内升到近 90%，用户看完全剧预计花费约 28.14 美元，免费剧集约 17%。这意味着出海方案要同时解决：多语种配音、口型重做、字幕规范、支付与盗版分流。</p>
          <p>成本上，口型重做按镜头计费，必须在前面的分镜阶段就决定「哪些镜头值得重做」，否则后期预算会失控。</p>
        </section>

        <section class="course-sec">
          <h3>7. 成本与产能：便宜不等于能赚钱</h3>
          <p>公开测评给出的单集实测成本（口径不同，仅作量级参考）：小云雀约 39 元、万兴剧厂约 100 元、纳逗 Pro 约 110 元、天工短剧工作台约 120 元。平台方则用自研模型把成本压得更低，例如昆仑万维公开称单部 AI 短剧成本约 2 万美元、降幅超 90%。</p>
          <p>但行业数据更冷静：2026 上半年全网新上 AI 短剧超过 22 万部，播放破亿的仅 1055 部，破亿率不到 0.5%；有报道称 98.7% 的 AI 微短剧上线半年内难回本。投流成本占收入 70%–90%。</p>
          <div class="course-note">成本下降只解决「做得起」，不解决「有人看」。剧本、分发与投流效率，才是盈利的分母。</div>
        </section>

        <section class="course-sec">
          <h3>8. 分发与变现：先定规则，再定规格</h3>
          <p>主流变现路径有四条：平台分账（按有效时长 × 单价 × 系数）、广告、投流买量、付费解锁/出海 App。平台的分账系数会直接奖励或惩罚某种内容形态，因此制作规格必须与分发目标对齐。</p>
          <p>典型做法：国内走红果/抖音/快手，用仿真人或真人 + AI 拿系数；出海走 ReelShort/DramaBox，用竖屏、强钩子、付费解锁；品牌项目走定制与广告，不依赖分账。</p>
        </section>

        <section class="course-sec">
          <h3>平台方案对照</h3>
          <div class="table-scroll"><table class="compare-table">
            <thead><tr><th>平台 / 体系</th><th>核心抓手</th><th>制作方案</th><th>模型</th><th>分发 / 变现</th><th>关键取舍</th></tr></thead>
            <tbody>
              <tr><td><b>字节</b></td><td>IP + 生产 + 分发闭环</td><td>Dramagic 全流程；小云雀一句话生成</td><td>Seedance 2.0/2.5</td><td>番茄 IP + 抖音 + 红果</td><td>闭环最完整，创作者议价弱</td></tr>
              <tr><td><b>快手</b></td><td>可灵模型 + 星芒计划</td><td>平台工具 + 创作者生态</td><td>可灵 3.0/4.0</td><td>星芒分账、联合运营最高 90%</td><td>模型强，分发靠合作</td></tr>
              <tr><td><b>腾讯</b></td><td>社交流量 + 混元</td><td>腾讯云全链路 AIGC</td><td>混元视频</td><td>微信「绿泡泡短剧」免费 + 广告</td><td>流量便宜，内容供给靠外部</td></tr>
              <tr><td><b>阿里</b></td><td>模型即服务 + IP</td><td>镜仔 Agent / WonderClip</td><td>通义万相 Wan 3.0</td><td>书旗 IP + B 端输出</td><td>做「卖铲子」，不做内容生意</td></tr>
              <tr><td><b>昆仑万维</b></td><td>自研模型 + 工作台</td><td>天工短剧工作台 + SkyReels</td><td>SkyReels</td><td>出海 + 自有分发</td><td>自研压成本，质量波动</td></tr>
              <tr><td><b>阅文</b></td><td>网文 IP</td><td>漫剧助手</td><td>外部模型组合</td><td>平台分账 + 衍生品</td><td>IP 最厚，制作非强项</td></tr>
              <tr><td><b>中文在线</b></td><td>全栈工具链</td><td>次元神笔：IP → 角色库 → 分镜 → 口型</td><td>外部 + 自研组合</td><td>FlareFlow 等海外渠道</td><td>链条最全，依赖 IP 供给</td></tr>
              <tr><td><b>360</b></td><td>工业化流水线</td><td>纳米漫剧 7 步标准流程</td><td>外部模型</td><td>平台合作</td><td>标准化强，创意上限低</td></tr>
              <tr><td><b>万兴科技</b></td><td>SaaS + 积分</td><td>万兴剧厂：资产提取、自动拆镜</td><td>Seedance 2.0</td><td>订阅 + 积分</td><td>上手快，深度依赖单一模型</td></tr>
              <tr><td><b>爱奇艺</b></td><td>专业分镜 + 独家分账</td><td>纳逗 Pro</td><td>外部模型</td><td>独家首发最高 100% 分账</td><td>提示词专业，流程可控性弱</td></tr>
              <tr><td><b>ReelShort</b></td><td>海外竖屏分发</td><td>AI 剧占比近 90%</td><td>多模型组合</td><td>付费解锁 + 广告</td><td>本地化与盗版是主要成本</td></tr>
            </tbody>
          </table></div>
          <p class="muted" style="font-size:var(--fs-meta)">注：以上为 2026 年 10 月前的公开报道与厂商口径，部分数字未经独立验证；平台政策与系数会变，决策前以当期官方规则为准。</p>
        </section>

        <section class="course-sec">
          <h3>决策矩阵：你在哪个象限</h3>
          <figure class="course-fig">
            <svg viewBox="0 0 800 320" role="img" aria-label="自动化程度与内容可控性的决策矩阵">
              <style>.f14t{font-size:12px;fill:#17171C;font-weight:600}.f14s{font-size:10px;fill:#6E6E7A}.f14l{font-size:10px;fill:#A0A0AC}</style>
              <line x1="70" y1="270" x2="750" y2="270" stroke="#DCDCE4"/>
              <line x1="70" y1="270" x2="70" y2="50" stroke="#DCDCE4"/>
              <text x="410" y="302" text-anchor="middle" class="f14l">自动化程度 →</text>
              <text x="34" y="160" text-anchor="middle" class="f14l" transform="rotate(-90 34 160)">内容可控性 →</text>
              <line x1="410" y1="60" x2="410" y2="266" stroke="#E9E9EF" stroke-dasharray="4 4"/>
              <line x1="74" y1="160" x2="746" y2="160" stroke="#E9E9EF" stroke-dasharray="4 4"/>
              <rect x="420" y="70" width="310" height="80" rx="8" fill="#F2F2FE" stroke="#E0E0FA"/>
              <text x="575" y="100" text-anchor="middle" class="f14t">目标区：半自动 + 资产库</text>
              <text x="575" y="122" text-anchor="middle" class="f14s">万兴剧厂 / 纳逗 Pro / 自建工具链</text>
              <text x="240" y="100" text-anchor="middle" class="f14t">精品区：真人 + AI 融合</text>
              <text x="240" y="122" text-anchor="middle" class="f14s">高系数、强表演、成本高</text>
              <text x="575" y="205" text-anchor="middle" class="f14t">批量区：全自动 Agent</text>
              <text x="575" y="227" text-anchor="middle" class="f14s">小云雀 / 解说漫：快、便宜、系数低</text>
              <text x="240" y="205" text-anchor="middle" class="f14t">作坊区：纯手工</text>
              <text x="240" y="227" text-anchor="middle" class="f14s">难规模化，适合试验与定制</text>
            </svg>
            <figcaption><b>图 14 · 决策矩阵（示意）。</b>越往右上，自动化与可控性越能兼得。全自动在右下：产能高但可控性低，平台系数也往往更低。目标是把资产库与人工判断加进流水线，而不是盲目追求「一句话成片」。</figcaption>
          </figure>
        </section>

        <section class="course-sec">
          <h3>按团队条件的选型建议</h3>
          <table class="compare-table">
            <thead><tr><th>团队</th><th>推荐方案</th><th>预算量级</th><th>不要做什么</th></tr></thead>
            <tbody>
              <tr><td>个人 / 试水</td><td>小云雀或万兴剧厂 + Seedance/Wan 经济档</td><td>几十到一百元/集</td><td>不要一开始自建工具链、不要全片 1080P 抽卡</td></tr>
              <tr><td>3–6 人小团队</td><td>半自动工作台 + 角色资产库 + 多模型路由</td><td>数百元/集 + 人力</td><td>不要把剧本完全交给 Agent</td></tr>
              <tr><td>中型 / 出海</td><td>自建工具链 + 云端模型 + 本地化配音/口型</td><td>千元级/集起</td><td>不要用平台原生口型硬扛多语种</td></tr>
              <tr><td>平台型</td><td>自研或深度绑定模型 + IP + 分发</td><td>资本级</td><td>不要只做工具、不碰分发</td></tr>
            </tbody>
          </table>
        </section>

        <section class="course-sec">
          <h3>研究结论：八条可带走的判断</h3>
          <ol>
            <li><b>平台先握一层</b>：IP、模型/工具、分发，至少一层自有，否则只能赚加工费。</li>
            <li><b>系数决定形态</b>：仿真人系数高于 2D，2D 高于 AI 解说漫；形态选择首先是商业选择。</li>
            <li><b>纯流水线被压</b>：多家平台鼓励真人 + AI 融合，纯 AI 内容收益系数被压低。</li>
            <li><b>全自动适合试水</b>：能快速验证剧本与选题，但成片仍需人工修。</li>
            <li><b>一致性靠资产库</b>：角色、场景、道具的复用能力，比单次生成质量更决定产能。</li>
            <li><b>声音要分层</b>：对白、音乐、音效、环境四层完整，才是可交付的声音；只加 BGM 会被听出来。</li>
            <li><b>出海要前置本地化</b>：配音、口型、字幕、支付与盗版分流，都要在分镜阶段预算。</li>
            <li><b>低成本不等于盈利</b>：22 万部里破亿不到 0.5%，投流占七到九成；剧本与分发才是分母。</li>
          </ol>
        </section>

        <section class="course-sec">
          <h3>练习</h3>
          <ol>
            <li>选一个平台（红果、抖音、快手、爱奇艺、ReelShort），查它当期分账规则，写出一页「它会奖励什么内容」。</li>
            <li>用八组取舍给你的项目做一次选型表，每组写明选择、理由、备选与切换条件。</li>
            <li>比较「全自动一集」与「半自动一集」的真实成本：把返工、重抽、人工时间折算进去。</li>
            <li>为一个出海项目列出本地化清单：语种、配音、口型、字幕、支付、盗版监测。</li>
          </ol>
        </section>

        <section class="course-sec">
          <h3>资料来源与时效</h3>
          <p class="muted" style="font-size:var(--fs-meta);line-height:1.9">
            本章数据来自 2026 年 9–10 月的公开报道与厂商口径，包括：字节 Dramagic / 小云雀与红果分账规则报道；快手星芒与可灵模型报道；腾讯云 AI 漫剧全栈方案与微信短剧报道；阿里云栖与通义 / 书旗 IP 报道；昆仑万维 SkyReels 与财报报道；阅文漫剧与「漫剧助手」报道；中文在线、360、万兴科技的 AI 漫剧方案报道；爱奇艺纳逗 Pro、B 站与抖音分账政策的行业盘点；ReelShort AI 剧占比与付费结构的第三方数据报道。部分数字为媒体转述或厂商自述，未经过独立复核；平台政策变化快，落地前请以官方当期条款为准。
          </p>
        </section>
      `
    },
    {
      id: "practice",
      eyebrow: "13 · PRACTICE",
      title: "从练习到专业：评审清单与常见误区",
      lede: "专业不是知道更多名词，而是有一套稳定的判断顺序，并且在压力下仍然执行。",
      html: `
        <section class="course-sec">
          <h3>四阶段练习计划</h3>
          <table class="compare-table">
            <thead><tr><th>阶段</th><th>任务</th><th>验收</th></tr></thead>
            <tbody>
              <tr><td>第 1 周 · 画面</td><td>30 秒戏，8 个镜头，含一次正反打</td><td>景别不跳、轴线不乱、人物一致</td></tr>
              <tr><td>第 2 周 · 声音</td><td>同一场戏，配 TTS + 口型 + 四层声音</td><td>对白清楚、无爆音、口型只开该开的</td></tr>
              <tr><td>第 3 周 · 混音</td><td>完成 Cue 表与混音，导出 stem</td><td>−23.0 LUFS ±0.2、≤−1 dBTP、stem 等长</td></tr>
              <tr><td>第 4 周 · 交付</td><td>母版 QC、三画幅派生、交付单</td><td>QC 全项通过、AI 标识齐备</td></tr>
            </tbody>
          </table>
          <figure class="course-fig">
            <svg viewBox="0 0 800 180" role="img" aria-label="四周练习计划时间线">
              <defs><marker id="f12a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#A0A0AC"/></marker></defs>
              <style>.f12t{font-size:11px;fill:#17171C;font-weight:600}.f12s{font-size:9px;fill:#6E6E7A}</style>
              <line x1="40" y1="90" x2="760" y2="90" stroke="#DCDCE4"/>
              <rect x="60" y="62" width="160" height="56" rx="7" fill="#F2F2FE" stroke="#E0E0FA"/><text x="140" y="84" text-anchor="middle" class="f12t">第 1 周 · 画面</text><text x="140" y="101" text-anchor="middle" class="f12s">8 镜 + 一次正反打</text>
              <rect x="230" y="62" width="160" height="56" rx="7" fill="#F2F2FE" stroke="#E0E0FA"/><text x="310" y="84" text-anchor="middle" class="f12t">第 2 周 · 声音</text><text x="310" y="101" text-anchor="middle" class="f12s">TTS + 口型 + 四层</text>
              <rect x="400" y="62" width="160" height="56" rx="7" fill="#F2F2FE" stroke="#E0E0FA"/><text x="480" y="84" text-anchor="middle" class="f12t">第 3 周 · 混音</text><text x="480" y="101" text-anchor="middle" class="f12s">Cue 表 + stem</text>
              <rect x="570" y="62" width="160" height="56" rx="7" fill="#F2F2FE" stroke="#E0E0FA"/><text x="650" y="84" text-anchor="middle" class="f12t">第 4 周 · 交付</text><text x="650" y="101" text-anchor="middle" class="f12s">QC + 三画幅</text>
              <path d="M60,140 H730" stroke="#A0A0AC" marker-end="url(#f12a)"/>
              <text x="400" y="160" text-anchor="middle" class="f12s">目标：四周后能独立交付一条通过 QC 的先导片</text>
            </svg>
            <figcaption><b>图 12 · 四周练习路径。</b>每周只增加一层能力，不追求一次做完。第 4 周结束时，你应该拥有一份可复核的 QC 报告，而不只是一段视频。</figcaption>
          </figure>
        </section>

        <section class="course-sec">
          <h3>专业评审清单（每次交付前过一遍）</h3>
          <ul>
            <li><b>叙事</b>：每场戏的目标、冲突、结果是否清楚？有没有可以删的镜头？</li>
            <li><b>画面</b>：景别是否有变化？轴线是否一致？人物脸/服装/光线是否连续？</li>
            <li><b>表演</b>：情绪是否可信？有没有「念台词」感？口型是否只在必要镜头开？</li>
            <li><b>声音</b>：每句对白是否清楚？音乐是否让位？切镜有没有爆音？环境是否连续？</li>
            <li><b>技术</b>：响度、峰值、同步、色彩、字幕、AI 标识是否达标？</li>
            <li><b>权利</b>：音乐、声音克隆、人脸、IP 的授权是否可追溯？</li>
          </ul>
        </section>

        <section class="course-sec">
          <h3>20 条常见误区</h3>
          <ol>
            <li>以为视频模型会自动生成配乐和音效。</li>
            <li>把「有声音」当成「声音设计」。 </li>
            <li>整集循环一首 BGM。</li>
            <li>所有镜头都开高分辨率，抽卡也不降档。</li>
            <li>所有镜头都开口型，预算失控。</li>
            <li>用生成型口型去修已有镜头，画面被重生成。</li>
            <li>提示词写得很文学，但不可执行、不可复现。</li>
            <li>身份锁放在提示词末尾，被场景描述冲掉。</li>
            <li>相邻镜头景别相同，产生跳切感。</li>
            <li>越轴没有过渡镜头。</li>
            <li>对白被音乐盖住，靠观众「猜」。 </li>
            <li>环境床不循环，切镜时房间忽大忽小。</li>
            <li>音效不对动作帧，打斗像放气。</li>
            <li>把关键信息只放在 LFE，立体声观众听不到。</li>
            <li>交付前把响度「偷偷调大」。</li>
            <li>母版烧硬字幕。</li>
            <li>为每个画幅重复生成，人物不一致。</li>
            <li>用订阅套餐跑批量渲染。</li>
            <li>音乐授权只看「免费下载」，不看商用档位。</li>
            <li>没有 QC 报告就交付。</li>
          </ol>
        </section>

        <section class="course-sec">
          <h3>术语表</h3>
          <table class="compare-table">
            <thead><tr><th>术语</th><th>解释</th></tr></thead>
            <tbody>
              <tr><td>ASL</td><td>平均镜头长度，衡量剪辑节奏</td></tr>
              <tr><td>J cut / L cut</td><td>声音先入 / 声音延后，用于顺滑剪辑</td></tr>
              <tr><td>OTS</td><td>过肩镜，对话常用构图</td></tr>
              <tr><td>180 度规则</td><td>摄影机保持在轴线同一侧</td></tr>
              <tr><td>T2V / I2V / R2V</td><td>文生视频 / 图生视频 / 参考生视频</td></tr>
              <tr><td>seed</td><td>随机种子，影响可复现性</td></tr>
              <tr><td>viseme</td><td>视素，可见的口型单位</td></tr>
              <tr><td>Cue</td><td>一段有入出点的配乐</td></tr>
              <tr><td>Hit point</td><td>音乐必须对齐的画面点</td></tr>
              <tr><td>Foley</td><td>拟音，人工表演的日常声音</td></tr>
              <tr><td>Ambience bed</td><td>铺满场景的环境声床</td></tr>
              <tr><td>Room tone</td><td>空间本身的底噪与反射</td></tr>
              <tr><td>Ducking</td><td>对白出现时自动降低音乐</td></tr>
              <tr><td>Stem</td><td>分轨音频，可独立混音与交付</td></tr>
              <tr><td>M&amp;E</td><td>去掉对白的音乐+音效版本，用于译制</td></tr>
              <tr><td>LUFS / LKFS</td><td>响度单位，两者等价</td></tr>
              <tr><td>dBTP</td><td>真峰值单位</td></tr>
              <tr><td>BS.1770</td><td>ITU 响度测量标准</td></tr>
              <tr><td>EBU R 128</td><td>欧洲广播响度规范，−23 LUFS</td></tr>
              <tr><td>open gate</td><td>未裁切的原始画幅，用于派生多画幅</td></tr>
              <tr><td>ΔE</td><td>色差指标，越小越一致</td></tr>
              <tr><td>AI 标识</td><td>显式、隐式、导出文件三类标识</td></tr>
            </tbody>
          </table>
        </section>

        <section class="course-sec">
          <h3>最后一句话</h3>
          <p>专业编辑与业余爱好者的区别，不在于会不会用某个模型，而在于<b>能不能在看片时说出「这里为什么不对」以及「下一步改什么」</b>。这套判断力，只能靠一条一条镜头、一段一段声音地练出来。</p>
        </section>
      `
    }
  ]
};
