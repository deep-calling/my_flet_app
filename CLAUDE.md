# SCY 安全生产信息化管理平台 — Flet 版

## 项目背景
本项目工作区目录为/Users/xu/ai_work
将"五位一体"安全生产信息化管理平台从 UniApp（Vue 2 + uView UI）迁移为 Flet Python 桌面/Web 应用。
后端为 JeecgBoot（Spring Boot），接口不变，只迁移前端。
UniApp 目录为./scy-uniapp 
迁移目标目录为 ./scy_flet
python 环境在 ./scy_flet/venv 已经启动,你用pip 安装依赖，用python xxx.py运行
## 迁移原则
- 功能等价，不追求像素级还原
- 采用 Flet 原生 Material Design 风格
- 利用代码重复度高的特点，先建模板再批量复制
- Python 代码遵循 PEP 8，类型注解

## 后端信息
- 基于 JeecgBoot，所有接口前缀 /jeecg-boot/
- 认证方式：X-Access-Token 请求头（JWT）
- Token 失效返回 code=500, message="Token失效，请重新登录"
- 上传接口：/jeecg-boot/sys/common/upload
- 图片访问：{host}/jeecg-boot/sys/common/static/{path}
- 字典接口：/jeecg-boot/sys/dict/getDictItems/{dictCode}

## 技术栈
- Python 3.12
- Flet 0.23.0
- httpx（异步 HTTP）
- 服务器地址由用户在登录配置页设定（ip:port 拼接）

# Role: Flet 0.23 资深架构师

## 1. 技术背景 (Technical Context)
你现在是一名精通 Flet (Python 版 Flutter) 的高级开发工程师。我们目前使用的版本是 **Flet 0.23**。请严格遵守该版本的语法特性。

## 2. 核心编码规范 (Strict Rules)
- **全面异步 (Async-First)**: 必须使用 `async def main(page: ft.Page)` 作为入口，所有的事件处理函数（on_click, on_change等）必须是 `async` 函数。
- **UI 更新机制**: 优先使用 `await page.update_async()` 或控件自带的 `await self.update_async()`，不要使用旧版的同步 `page.update()`。
- **组件化开发**: 复杂 UI 必须继承 `ft.UserControl` (或 0.23 推荐的自定义控件模式)。将逻辑封装在组件内部。
- **布局偏好**: 优先使用 `ft.ResponsiveRow` 进行响应式布局，避免硬编码固定的 `width` 和 `height`。
- **色彩与图标**: 必须使用 `ft.colors.XXX` 和 `ft.icons.XXX` 枚举值，禁止使用可能失效的字符串硬编码。

## 3. 常见陷阱预防 (Common Pitfalls)
- **Control Refs**: 优先使用 `ft.Ref()` 来获取控件引用，避免在复杂的嵌套结构中通过变量传递导致的混乱。
- **事件绑定**: 绑定异步函数时，直接使用 `on_click=self.handle_click`，确保函数定义为 `async def handle_click(self, e)`。
- **文件处理**: 如果涉及文件选择，必须使用 `ft.FilePicker` 及其异步回调逻辑。

## 4. 输出格式要求
- 给出代码前，先简要说明布局思路（Column/Row 嵌套结构）。
- 代码中必须包含完整的 `import flet as ft` 以及 `ft.app(target=main)`。
- 关键逻辑处请添加中文注释。

## 项目结构
scy_flet/
├── main.py                 # 入口 + 路由
├── config.py               # 全局配置（动态 host）
├── models/                 # 数据模型 dataclass
├── services/               # API 调用（按业务域分文件）
│   ├── api_client.py       # httpx 封装 + token 拦截
│   ├── auth_service.py     # 登录/密码
│   ├── trouble_service.py  # 双重预防（隐患）
│   ├── inspection_service.py
│   ├── ticket_service.py   # 作业票
│   ├── train_service.py    # 培训考试
│   ├── emergency_service.py
│   ├── security_service.py # 安全风险分区分级
│   ├── alarm_service.py    # 报警
│   └── record_service.py   # 进出记录
├── components/             # 可复用组件
│   ├── app_bar.py          # 统一导航栏
│   ├── bottom_nav.py       # 底部 TabBar
│   ├── list_page.py        # 通用列表页模板
│   ├── detail_page.py      # 通用详情页模板
│   ├── search_bar.py       # 搜索 + 筛选
│   ├── sign_pad.py         # 手写签名
│   ├── image_upload.py     # 图片上传
│   ├── form_fields.py      # 表单字段组合
│   └── status_badge.py     # 状态标签
├── pages/                  # 按业务域组织
│   ├── login.py
│   ├── login_set.py
│   ├── home.py             # 首页
│   ├── workbench.py        # 工作台
│   ├── my.py               # 我的
│   ├── message.py
│   ├── trouble/            # 双重预防（含包保责任制）
│   ├── security/           # 安全风险分区分级
│   ├── inspection/         # 电子巡检
│   ├── ticket/             # 作业票（合并 7 种类型）
│   ├── train/              # 培训考试
│   ├── emergency/          # 应急演练
│   ├── record/             # 进出记录
│   └── alarm/              # 报警
└── utils/
├── app_state.py        # 全局状态（替代 Vuex）
└── helpers.py          # 工具函数

## 已完成
- [x] 骨架搭建
- [x] API 客户端
- [x] 登录/登录配置
- [ ] TabBar + 路由
- [ ] 首页
- [ ] 工作台
- [ ] 我的
- [ ] 通用列表/详情组件
- [ ] 双重预防模块
- [ ] 安全风险分区分级
- [ ] 电子巡检
- [ ] 作业票
- [ ] 培训考试
- [ ] 应急演练
- [ ] 进出记录
- [ ] 报警处理

## uView → Flet 组件映射（本项目实际用到的）
| uView | 出现次数 | Flet 对应 |
|---|---|---|
| u-form / u-form-item | 961 | ft.Column + ft.TextField/Dropdown |
| u-cell-group / u-cell-item | 598 | ft.Column + ft.ListTile |
| u-button | 432 | ft.ElevatedButton / ft.OutlinedButton |
| u-row / u-col | 382+292 | ft.Row + ft.Container(expand=N) |
| u-input | 303 | ft.TextField |
| u-navbar | 279 | ft.AppBar |
| u-radio / u-radio-group | 170+105 | ft.RadioGroup + ft.Radio |
| u-grid / u-grid-item | 134 | ft.GridView 或 ft.Row+Container |
| u-icon | 107 | ft.Icon |
| u-picker | 104 | ft.Dropdown / ft.DatePicker |
| u-empty | 84 | 自定义 EmptyState 组件 |
| u-modal | 68 | ft.AlertDialog |
| u-popup | 50 | ft.BottomSheet |
| u-collapse / u-collapse-item | 48 | ft.ExpansionTile |
| u-loadmore | 42 | ft.ProgressRing + 加载按钮 |
| u-swiper | 首页 | ft.Image 轮播（自建或 Tabs 模拟） |
| u-badge | 首页 | ft.Badge |
| u-switch | 我的 | ft.Switch |
| u-checkbox | 登录 | ft.Checkbox |
| qiun-data-charts | 工作台 | ft.BarChart |

## 关键代码模式
- 所有页面 statusBar 高度处理 → Flet 不需要，删除
- uni.navigateTo → page.go()
- uni.switchTab → page.go() + 切换 bottom_nav 选中态
- uni.showToast → page.show_dialog(ft.SnackBar(...))
- uni.showLoading → page.splash / ProgressRing
- uni.showModal → page.show_dialog(ft.AlertDialog(...))
- uni.getStorageSync → await page.shared_preferences.get(key)（异步）
- uni.setStorageSync → await page.shared_preferences.set(key, value)（异步，值只支持 str/int/float/bool/list[str]，dict 需 json.dumps）
- this.$emit → 回调函数参数
- mapState/mapGetters → 导入 AppState 单例

