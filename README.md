# 雨澜轩 · 统一轻量模型试验

本分支 `trial/unified-geometry` 使用同一份模型服务桌面与手机，不存在设备专用模型版本。

| 指标 | 上一版 | 本次候选 |
| --- | ---: | ---: |
| GLB 字节数 | 19,575,192 | 7,254,028 |
| 三角形 | 2,254,232 | 788,837 |
| 场景节点 | 1,618 | 1,618 |
| 材质 | 211 | 211 |

当前运行文件为 `public/assets/home.glb`。原版保留于原始本地 commit 22ec192 及此前保存的模型文件中。此优化版正在导入 GitHub main；是否上线以 GitHub Actions 的部署结果为准。

## 实际完成

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
node scripts/trial-unified.mjs /path/to/yulanxuan-home-19.58MB.glb qa/unified-trial
node scripts/verify-unified.mjs /path/to/yulanxuan-home-19.58MB.glb qa/unified-trial/home-unified-candidate.glb qa/unified-trial
node scripts/check-navigation.mjs qa/unified-trial/home-unified-candidate.glb
```

历史压缩、轮廓验证及装修资料对照记录保留在原工作区；公开仓库只收录运行所需资源、源码和优化脚本，不包含施工 PDF、Blender 源文件或设计资料。

尚未进行形体/运行时人工验收。本候选只用于审阅，不表示施工尺寸或视觉效果已最终确认。
