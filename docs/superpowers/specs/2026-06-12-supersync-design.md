# SuperSync - 跨设备开发环境迁移工具 设计文档

## 概述

**项目名称**：SuperSync
**产品定位**：面向开发者的跨设备编程环境无缝迁移引擎
**首版平台**：macOS
**技术栈**：Python
**交互形态**：CLI 优先
**架构方案**：声明式清单 + AES 加密封装

## 核心痛点

开发者在更换电脑或团队交接时，往往需要耗费数天时间手动重装各种语言环境、依赖库，并逐一排查环境变量和配置文件冲突，效率极低且极易出错。

## 解决方案

采用"探测 → 序列化/加密 → 编排执行"三阶段架构，用户运行一次扫描即可生成加密的环境快照文件，在目标设备上导入即可全自动还原。

## 整体架构

```
[源设备]                          [目标设备]

Scanner ──→ Manifest(YAML) ──→    Parser
  │              │                   │
  ├─ brew list   ├─ AES加密        ├─ 依赖拓扑排序
  ├─ pip list    ├─ gzip压缩       ├─ 按序静默安装
  ├─ npm list    └─ .supersync文件 ├─ 冲突检测
  ├─ env vars                        └─ 配置注入
  ├─ dotfiles
  └─ IDE plugins
```

### 核心数据流

1. `supersync scan` → Scanner 探测环境 → 生成声明式 Manifest (YAML)
2. 用户交互选择敏感项 → Manifest 序列化 → AES-256 加密 + gzip 压缩 → 输出 `.supersync` 文件
3. `supersync restore env.supersync` → 解密解压 → 解析 Manifest → 依赖拓扑排序 → 按序自动安装 → 冲突时提示用户

### 项目结构

```
SuperSync/
├── src/supersync/
│   ├── __init__.py
│   ├── cli.py              # CLI 入口 (Typer)
│   ├── scanner/            # 环境探针模块
│   │   ├── base.py         # Scanner 基类
│   │   ├── brew.py         # Homebrew 扫描器
│   │   ├── pip.py          # pip 扫描器
│   │   ├── npm.py          # npm 扫描器
│   │   ├── env_vars.py     # 环境变量扫描器
│   │   ├── dotfiles.py     # Dotfiles 扫描器
│   │   └── ide.py          # IDE 插件扫描器
│   ├── manifest/           # 清单序列化模块
│   │   ├── schema.py       # Manifest 数据模型 (Pydantic)
│   │   ├── serializer.py   # YAML 序列化/反序列化
│   │   └── crypto.py       # AES 加密/解密
│   ├── provisioner/        # 部署引擎模块
│   │   ├── engine.py       # 编排执行引擎
│   │   ├── dependency.py   # 依赖拓扑排序
│   │   ├── installer.py    # 包安装器
│   │   └── conflict.py     # 冲突检测与处理
│   └── utils/              # 工具函数
├── tests/
├── pyproject.toml
└── README.md
```

## 环境探针模块 (Scanner)

每个 Scanner 实现统一接口，输出结构化数据：

```python
class ScanResult:
    source: str           # "brew" / "pip" / "npm" / ...
    items: list[Item]     # 扫描到的条目
    sensitive: list[Item] # 敏感条目（供用户选择）
    errors: list[str]     # 扫描中的警告/错误
```

### 各 Scanner 扫描策略

| Scanner | 扫描内容 | 命令/方式 | 敏感项标记 |
|---------|---------|----------|-----------|
| **brew** | 已安装 formula/cask | `brew list --formula --cask` + `brew leaves` | 无 |
| **pip** | 全局已安装包 | `pip list --format=json` | 无 |
| **npm** | 全局已安装包 | `npm list -g --json` | 含 `.npmrc` 中的 token |
| **env_vars** | 自定义 PATH 及环境变量 | 解析 shell 配置文件提取 `export` 语句 | 含 key/token/secret 的变量 |
| **dotfiles** | 配置文件内容 | 读取指定 dotfiles | `~/.ssh/` 下所有文件默认标记为敏感 |
| **ide** | VS Code 扩展列表 | `code --list-extensions` + 读取 `settings.json` | settings 中含 token 的字段 |

### 敏感数据交互流程

```
扫描完成 → 列出所有敏感项（带编号）
→ 用户交互选择：
  [1] ~/.ssh/id_rsa          → 包含 / 排除 / 加密
  [2] ~/.npmrc (含 token)    → 包含 / 排除 / 加密
  [3] env: GITHUB_TOKEN      → 包含 / 排除 / 加密
  ...
→ 默认全部"排除"，用户主动选择包含
```

### 扫描的 dotfiles 路径列表（macOS）

- `~/.zshrc`, `~/.bashrc`, `~/.bash_profile`
- `~/.gitconfig`, `~/.gitignore_global`
- `~/.ssh/config`（敏感）
- `~/.ssh/known_hosts`
- `~/.vimrc`
- `~/.config/starship.toml`
- `~/.editorconfig`
- VS Code: `~/Library/Application Support/Code/User/settings.json`

## 清单模型与加密 (Manifest & Crypto)

### Manifest YAML 结构

```yaml
version: "1.0"
created_at: "2026-06-12T10:30:00+08:00"
hostname: "macbook-pro"
platform: "macos"
arch: "arm64"

packages:
  brew:
    formula:
      - name: git
        version: "2.45.0"
      - name: node
        version: "22.2.0"
    cask:
      - name: visual-studio-code
        version: "1.90.0"
  pip:
    - name: requests
      version: "2.32.0"
  npm:
    - name: typescript
      version: "5.5.0"
      global: true

env_vars:
  - key: PYTHONPATH
    value: "/usr/local/lib/python3"
  - key: JAVA_HOME
    value: "/Library/Java/JavaVirtualMachines/jdk-21"

dotfiles:
  - path: ".zshrc"
    content: "<base64-encoded>"
    sensitive: false
  - path: ".ssh/config"
    content: "<base64-encrypted>"
    sensitive: true
    encrypted: true

ide:
  vscode:
    extensions:
      - "ms-python.python"
      - "esbenp.prettier-vscode"
    settings:
      path: "Library/Application Support/Code/User/settings.json"
      content: "<base64-encoded>"
```

### 加密策略

- 整个 Manifest 先序列化为 YAML → gzip 压缩 → AES-256-GCM 加密
- 用户设置密码 → PBKDF2 派生密钥（100,000 次迭代）
- 敏感项（用户选择包含的）在 Manifest 内部额外用独立密钥加密，即使整体解密后敏感项仍需二次解密
- 输出文件格式：`.supersync`，二进制格式

### 文件格式

```
[4 bytes: magic "SSNC"]
[2 bytes: version]
[16 bytes: salt]
[12 bytes: nonce]
[4 bytes: manifest length]
[N bytes: encrypted + compressed manifest]
[16 bytes: GCM tag]
```

## 自动化部署引擎 (Provisioner)

### 还原流程

```
.supersync 文件
  → 解密解压 → Manifest
  → 依赖拓扑排序
  → 生成执行计划（预览）
  → 按序执行安装
  → 冲突处理
  → 验证报告
```

### 依赖拓扑排序规则

1. 包管理器本身（先装 brew）
2. 语言运行时（python, node, java 等）
3. 包管理器的包（pip install, npm install 等）
4. 环境变量注入
5. Dotfiles 部署
6. IDE 插件安装

### 安装器策略

| 组件 | 安装方式 | 幂等性保证 |
|------|---------|-----------|
| brew formula | `brew install <name>` | 已存在则跳过 |
| brew cask | `brew install --cask <name>` | 已存在则跳过 |
| pip 包 | `pip install <name>==<version>` | 已存在同版本则跳过 |
| npm 全局包 | `npm install -g <name>@<version>` | 已存在同版本则跳过 |
| 环境变量 | 追加到对应 shell 配置文件 | 检测已存在则跳过 |
| dotfiles | 复制到目标路径 | 已存在则提示：覆盖/跳过/备份后覆盖 |
| VS Code 扩展 | `code --install-extension <id>` | 已安装则跳过 |

### 冲突处理

- 目标已存在不同版本 → 提示用户选择：保留/覆盖/升级
- dotfiles 已存在 → 提示：覆盖/跳过/备份原文件后覆盖
- 包安装失败 → 记录到错误报告，继续执行其余项，不中断流程

### 验证报告示例

```
✅ brew: 42/44 installed (2 skipped - already present)
✅ pip: 15/15 installed
⚠️ npm: 3/4 installed (typescript failed - requires node >= 18)
✅ env_vars: 5/5 injected
⚠️ dotfiles: 3/4 deployed (.zshrc backed up to .zshrc.supersync.bak)
✅ vscode: 12/12 extensions installed

Total: 79/82 successful, 3 warnings
See full log: ~/.supersync/restore-2026-06-12.log
```

## CLI 命令设计

```bash
# 扫描当前环境
supersync scan                          # 交互式扫描
supersync scan --output env.supersync   # 指定输出文件
supersync scan --skip-sensitive         # 跳过所有敏感项
supersync scan --include-all-sensitive  # 包含所有敏感项

# 还原环境
supersync restore env.supersync         # 交互式还原
supersync restore env.supersync --dry-run # 仅预览，不执行
supersync restore env.supersync --yes     # 自动确认所有提示

# 查看清单
supersync inspect env.supersync         # 解密后查看清单内容

# 版本信息
supersync --version
supersync --help
```

## 错误处理

- 扫描阶段：某个 Scanner 失败不影响其他 Scanner，记录错误继续执行
- 加密阶段：密码强度校验（最少 8 位），两次输入确认
- 还原阶段：单步失败不中断整体流程，汇总到最终报告
- 日志记录：所有操作写入 `~/.supersync/logs/` 目录，按日期归档

## 测试策略

- 单元测试：每个 Scanner/Provisioner 的独立逻辑（mock 子进程调用）
- 集成测试：完整 scan → encrypt → decrypt → restore 流程
- 端到端测试：在 Docker 容器中模拟真实环境还原
- 测试框架：pytest + pytest-mock

## 技术依赖

- `typer` — CLI 框架
- `pydantic` — Manifest 数据模型
- `cryptography` — AES 加密
- `rich` — 终端美化输出（进度条、表格）
- `pyyaml` — YAML 序列化
- `pytest` — 测试框架

## 传输方式

本地文件导出，用户通过 U 盘/网盘/邮件等方式自行传输 `.supersync` 文件，无需后端服务。

## 仓库

https://github.com/NoWint/SuperSync
