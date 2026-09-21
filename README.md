# 住宅空间漫游

使用 Three.js 和 Vite 的住宅三维漫游，支持电脑和手机、房间快捷导航、门窗与家具状态切换。

**在线访问：[住宅空间漫游](https://jiangbodev.github.io/home-deco/)**

**发布状态：[GitHub Actions](https://github.com/jiangbodev/home-deco/actions/workflows/pages.yml)**

## 当前版本

- 自由穿行：允许穿过墙体、家具和户型边界，眼高固定 1.5 m；点击房间名称可返回指定位置。
- 电脑使用 WASD / 方向键移动、拖动画面转向；手机使用摇杆移动、拖动画面转向。
- 通过设置切换门窗、隐私帘、家具、吊顶等状态，支持恢复初始状态。
- 桌面和手机使用同一套模型。初始加载入口及客餐厅，其他房间后台补齐；房间跳转优先加载目标资源，已加载内容保留。
- 入口加载条使用清单中的真实资源大小、模型下载字节事件及贴图完成事件计算进度，共享贴图只计一次。显示下载百分比和已加载 MB；解析、材质与显卡准备阶段显示活动指示，不用定时器编造百分比。失败时显示重试。

## 模型与资源

当前入口是 `public/assets/modules/manifest.json`，不是历史单文件 `home.glb`。

| 项目 | 当前值 |
| --- | ---: |
| GLB 模块 | 12 |
| 共享贴图 | 62 |
| Mesh 节点 | 1,493 |
| 入口模型及贴图 | 约 3.49 MB |
| 全部模块、贴图及清单 | 约 7.85 MB |
| 加上烘焙光影、表面纹理及灯具清单 | 约 9.09 MB |
| 资源预算 | 小于 20 MB |

以上是资源文件字节数，不含网页 JavaScript、Draco 解码器及 HTTP 开销，不代表实际加载时长或显存占用。CI 会核验文件大小、烘焙版本及总预算。

模块与贴图按内容哈希命名。基础模块保留原节点、变换与交互元数据，其他模块通过 `attachTo` 挂回原节点。禁止加载房间时重新初始化交互状态。

## Blender 工作流与性能

模型修改使用 **Blender**。2026-09-21 使用 Blender 4.5.14 LTS 将两间卧室六个床品对象从 299,990 减至 59,992 个三角形（约减少 80%），保留原材质和共享贴图；其他 10 个模块不变。取消行走碰撞，消除主卧附近的逐三角形碰撞查询开销。

`source/home-deco-bedding.blend` 是本地从 GLB 重建的可编辑场景，保留床品减面修改器和打包贴图，按仓库规则不提交二进制 `.blend`。它不是原作者未入库的工程，不能恢复原始建模历史。重建和导出步骤见 [Blender 源文件说明](source/README.md)。不要对已减面输出反复减面；本次原始模块可从提交 `8fcd1e1` 取得。

几何修改后必须从最终模块组装烘焙源，重跑接触阴影、照明与物体接触烘焙。不得只修改元数据中的版本列表绕过失效检查。网页光影使用项目离线脚本，不是 Blender 完整 GI 的复现。

Chrome / Apple M4 检查中，主卧同机位三角形处理量约减少 36%，绘制调用数量未减少。该比例不是 FPS 提升比例；手机及其他硬件仍需实际体验确认。参见 [性能与验证记录](review/performance-2026-09-21.md)、[光影说明](review/appearance-2026-09-19.md)。早期单文件模型、床品破洞修复和减面方案均为历史状态，详见 Git 历史。

## 开发和校验

使用 Node.js 22，通过 HTTP 预览，不要直接打开 HTML。

```sh
npm ci
npm run dev -- --host 127.0.0.1
```

```sh
node scripts/check-loading-progress.mjs
npm run build
node scripts/check-model-budget.mjs
npm run preview -- --host 127.0.0.1
```

- `src/main.js`：渲染、自由移动、交互和加载界面。
- `src/modules.js`：模块下载、去重、预取、挂载和重试。
- `src/loading-progress.js`：入口资源的真实加载进度。
- `src/appearance.js`、`surface-finishes.js`、`object-contact.js`：材质及离线烘焙数据接入。
- `scripts/assemble-modules.mjs`：从运行模块精确组装烘焙源。
- `scripts/verify-modules.mjs SOURCE.glb`：验证模块解码几何、索引、变换及 glTF 合法性。
- `scripts/blender-simplify-bedding.py`、`import-blender-bedding.mjs`：Blender 修改与模块接入。

## GitHub Pages 发布

工作流：[`.github/workflows/pages.yml`](.github/workflows/pages.yml)。

1. Pull Request 执行依赖安装、加载进度回归、生产构建和资源预算检查。
2. 合并或推送到 `main` 后，通过同样检查，再上传 `dist/` 并部署到 GitHub Pages。
3. 也可在 Actions 页面手动运行 `main` 分支的工作流。

仓库 Settings → Pages 的 Source 使用 **GitHub Actions**。站点无需登录，部署使用工作流自带 `GITHUB_TOKEN` 的 Pages/OIDC 权限，不需要额外个人令牌。检查 Actions 的 `build` 和 `deploy` 均成功后，再访问站点核对最新界面与模型；代码合并成功不等于发布已经完成。
