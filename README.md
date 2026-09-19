# 住宅空间漫游 · 分模块加载

## 当前加载方式（2026-09-19）

全屋分为 12 个 GLB 模块，共用 62 张按内容哈希命名的贴图。初始下载基础结构、玄关/餐客厅家具及所需贴图，模型资源约 3.49 MB；其余房间按邻接优先级后台补齐，点击房间立即优先加载，加载后保留。全部模块、贴图及清单约 9.10 MB。此数字不含网页 JS、解码器和 HTTP 开销，不是实测加载时间。

基础结构保留所有原节点、局部变换、可见性、交互元数据和碰撞几何；延迟模块把原始网格附着回对应节点。主卧、次卧床品独立，整套分拆没有减面或重新编码。资源文件名按内容变化，修改一个模块不会使其它模块缓存失效。模型下载失败时可点击页面状态重试。

- `public/assets/modules/manifest.json`：资源入口与模块依赖。
- `src/modules.js`：房间优先加载、相邻房间预取、下载去重和重试。
- `scripts/classify-modules.mjs`：结构保护规则与按世界坐标分区；输出分组映射，拆分前可人工修正。
- `scripts/split-modules.py`：无损拆分已审阅的 GLB；输出共享贴图和模块。
- `scripts/verify-modules.mjs`：逐一比较全部 1,493 个网格的解码属性、索引、节点变换和元数据，并验证 GLB。

复现（源文件可从修复提交 fd26d8c 提取）：

```sh
node scripts/classify-modules.mjs /path/to/source.glb /tmp/module-map.json
python scripts/split-modules.py /path/to/source.glb /tmp/module-map.json public/assets/modules
node scripts/verify-modules.mjs /path/to/source.glb
npm run build
```

后续局部造型修改仍应在 Blender 中完成。单独更新模块时保持挂载节点的 `attachTo`、局部坐标和交互父级关系，更新对应哈希文件及清单；若改动父级结构，应重新拆分核验。不要把已减面的模块再次减面。

以下保留历史修复记录，历史单文件体积不代表当前加载方式。

## 床品修复（2026-09-19）

恢复主卧、次卧实际可见的两组床品，共 6 个网格。此前按枕头名称保护的规则漏掉了以材质命名的导入对象，导致床品被减至约 18% 面数并出现黑色破洞。现在按床品父组保护整个层级。

当前模型 9,123,564 字节；其余模型二进制数据、场景节点、材质和贴图保持不变。解码校验 0 errors、235 条原有 warnings；两间卧室相同视角的 Three.js 对照渲染已确认明显破洞消失。检查使用无头 Chromium 软件渲染，截图时调整俯角、停止动画并跳过异步预编译，不代表移动设备性能验收。

复现：`python scripts/restore-bedding.py BASELINE.glb CURRENT.glb OUTPUT.glb`。BASELINE 必须是减面前的 19.58 MB 模型。

以下为此前轻量化记录。

本分支 `trial/unified-geometry` 使用同一份模型服务桌面与手机，不存在设备专用模型版本。

| 指标 | 上一版 | 本次候选 |
| --- | ---: | ---: |
| GLB 字节数 | 19,575,192 | 7,381,464 |
| 三角形（导出后解码） | 2,254,232 | 870,161 |
| 场景节点 | 1,618 | 1,618 |
| 材质 | 211 | 211 |

当前运行文件为 `public/assets/home.glb`。原版保留于原始本地 commit 22ec192 及此前保存的模型文件中。此优化版正在导入 GitHub main；是否上线以 GitHub Actions 的部署结果为准。

## 实际完成

- 根据软装破图反馈，恢复枕头、沙发、坐垫和地毯包边的源几何精度，其它构件保持原压缩策略。停用缺失透明贴图、被错误导出为不透明黑面的沙发接触阴影片，待正确重烘焙后恢复。节点、变换和全部纹理保持不变；实际画面仍需设备验收。

- 对窗外树木、布艺、藤编和高面数家具执行带法线/UV属性约束的离线减面。
- 建筑地面、墙、门窗等受保护构件不参与减面；节点局部变换完全一致，源元数据与交互状态保留。
- 62 张纹理的内容哈希与上一版完全相同，211 个材质保留，透明阴影修复沿用。
- 全模型重新 Draco 编码；清除减面产生的孤立顶点数据，未清除场景节点。
- 新模型接入原有响应式漫游前端，生产构建成功。

## 验证及限制

GLB 解码后结构校验：0 errors、235 warnings（原有切线空间和非 2 次幂纹理提示）。九个导航落点均有地面，且不在墙体 22 cm 范围内。

四个重点部件做了几何正交投影对比，见 `review/unified/silhouettes.png`：藤编投影差异约 1.45%，两类布艺约 0.23%，树叶约 3.68%。这些是特定投影下的二值几何轮廓差异，不是完整材质渲染、所有角度证明或网页截图。

本轮没有可用 Blender，官方下载被当前网络拒绝。实际减面使用离线 meshoptimizer，并未在网页运行时生成几何；没有进行 Blender 烘焙。贴图分辨率和材质数量未进一步降低，绘制调用也未专门合并，不能把三角形减幅当成 FPS 提升幅度。

网页材质、透明效果、近距离纹理、交互和手机/桌面性能仍需浏览器验收。GitHub 写入现已恢复；发布状态请查看 Actions。

## 本地预览

```sh
npm ci
npm run dev
npm run build
```

使用 Node 22，通过 HTTP 打开，不要直接双击 HTML。GitHub Pages 工作流仅在 main 分支推送或手动触发时运行。首次部署需在仓库 Settings → Pages 中将 Source 设置为 GitHub Actions。

## 重现候选

必须使用上一版 19.58 MB 模型作为输入，避免对已减面的候选重复减面：

```sh
node scripts/trial-unified.mjs /path/to/home-baseline-19.58MB.glb qa/unified-trial
node scripts/verify-unified.mjs /path/to/home-baseline-19.58MB.glb qa/unified-trial/home-unified-candidate.glb qa/unified-trial
node scripts/check-navigation.mjs qa/unified-trial/home-unified-candidate.glb
```

历史压缩、轮廓验证及装修资料对照记录保留在原工作区；公开仓库只收录运行所需资源、源码和优化脚本，不包含施工 PDF、Blender 源文件或设计资料。

尚未进行形体/运行时人工验收。本候选只用于审阅，不表示施工尺寸或视觉效果已最终确认。

## 漫游光影更新（2026-09-19）

当前版本加入地面、墙角和固定柜体的离线接触阴影，校准白色漆面、木纹与床品表面细节。原有模型网格未变化，保留分房间加载。模型、共享纹理和新增光影资源合计约 9.76 MB。实现、重烘焙方式和已知限制见 [本轮记录](review/appearance-2026-09-19.md)。

后续针对“柜子、墙面仍显白且缺少材质感”的反馈，加入分开的哑光墙面和缎光漆面参数，以及共用微表面纹理；总资源现约 9.94 MB。

照明进一步改为外窗方向光的离线烘焙、轨道灯局部暖光和两盏实际餐桌柔光灯；[同机位网页对比](review/lighting-comparison.png)记录实际修改前后。当前效果是实时漫游的视觉近似，不代表实测室内照度。
