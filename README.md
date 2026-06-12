# SuperSync

跨设备开发环境一键迁移工具。扫描当前电脑的完整编程环境，生成加密快照文件，在另一台电脑上导入即可自动还原。

## 解决什么问题

换电脑或团队交接时，重装开发环境通常需要数天：手动安装语言运行时、包管理器依赖、IDE 插件，逐一排查环境变量和配置文件冲突。SuperSync 将这个过程压缩为两条命令。

## 工作原理

```
源设备                              目标设备

supersync scan                      supersync restore env.supersync
   │                                    │
   ├─ 扫描 Homebrew/pip/npm 包          ├─ 解密并解析清单
   ├─ 提取环境变量                      ├─ 按依赖拓扑排序
   ├─ 读取 Dotfiles 配置               ├─ 静默安装所有包
   ├─ 检测 VS Code 扩展                 ├─ 注入环境变量
   │                                    ├─ 部署 Dotfiles
   └─ AES-256 加密 → .supersync        └─ 安装 IDE 扩展
```

## 扫描范围

| 类别 | 扫描内容 | 敏感项检测 |
|------|---------|-----------|
| Homebrew | formula + cask 及版本号 | - |
| pip | 全局安装包及版本号 | - |
| npm | 全局安装包及版本号 | .npmrc 中的 token |
| 环境变量 | shell 配置中的 export 语句 | 含 token/key/secret 的变量 |
| Dotfiles | .zshrc, .bashrc, .gitconfig, .vimrc 等 | .ssh/ 目录下所有文件 |
| VS Code | 扩展列表 + settings.json | settings 中的 token 字段 |

## 安装

```bash
git clone https://github.com/NoWint/SuperSync.git
cd SuperSync
pip install -e .
```

需要 Python 3.11+。

## 使用

### 扫描环境

```bash
supersync scan
```

交互式扫描当前环境，提示处理敏感项，设置加密密码后生成 `env.supersync` 文件。

```bash
# 指定输出路径
supersync scan --output my-env.supersync

# 跳过所有敏感项（不包含 SSH Keys、API Tokens 等）
supersync scan --skip-sensitive

# 包含所有敏感项并加密
supersync scan --include-all-sensitive
```

### 还原环境

```bash
supersync restore env.supersync
```

输入密码解密后，自动按依赖顺序安装所有组件。

```bash
# 仅预览，不实际执行安装
supersync restore env.supersync --dry-run

# 自动确认所有提示
supersync restore env.supersync --yes
```

### 查看快照内容

```bash
supersync inspect env.supersync
```

解密后显示快照中的环境摘要，不执行任何安装操作。

### 检查更新

```bash
# Check for updates
supersync update --check

# Update to latest version
supersync update
```

## 安全设计

- **AES-256-GCM 加密**：快照文件使用 PBKDF2 密钥派生（100,000 次迭代）+ AES-256-GCM 认证加密
- **敏感数据二次加密**：选择"加密"的敏感项在清单内部额外加密，即使整体解密后仍需单独解密
- **敏感项默认排除**：SSH Keys、API Tokens 等默认不包含，需用户主动选择
- **密码强度校验**：最少 8 位，两次输入确认
- **本地传输**：快照文件通过本地文件传输，不经过任何服务器

## 文件格式

`.supersync` 文件为二进制格式：

```
[4B: magic "SSNC"] [2B: version] [16B: salt] [12B: nonce]
[4B: data length] [NB: encrypted gzip'd YAML] [16B: GCM tag]
```

## 项目结构

```
src/supersync/
├── cli.py                 # CLI 入口 (Typer + Rich)
├── scanner/               # 环境探针
│   ├── base.py            # Scanner 基类、Item、ScanResult
│   ├── brew.py            # Homebrew 扫描器
│   ├── pip_scanner.py     # pip 扫描器
│   ├── npm.py             # npm 扫描器
│   ├── env_vars.py        # 环境变量扫描器
│   ├── dotfiles.py        # Dotfiles 扫描器
│   └── ide.py             # VS Code 扫描器
├── manifest/              # 清单与加密
│   ├── schema.py          # Pydantic 数据模型
│   ├── serializer.py      # YAML 序列化
│   └── crypto.py          # AES-256-GCM 加解密
├── provisioner/           # 部署引擎
│   ├── dependency.py      # 依赖拓扑排序
│   ├── installer.py       # 包安装器
│   ├── conflict.py        # 冲突检测
│   └── engine.py          # 编排执行引擎
└── utils/
    └── run.py             # 子进程运行工具
```

## 技术栈

- **CLI**：[Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/)
- **数据模型**：[Pydantic](https://docs.pydantic.dev/) v2
- **加密**：[cryptography](https://cryptography.io/) (AES-256-GCM + PBKDF2)
- **序列化**：[PyYAML](https://pyyaml.org/)
- **测试**：[pytest](https://docs.pytest.org/)

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 运行单个模块测试
pytest tests/test_scanner/ -v
```

## 当前限制

- 仅支持 macOS
- 还原时要求目标设备已安装 Homebrew（brew 命令可用）
- 敏感项的"二次加密"使用与整体相同的密码派生机制

## License

MIT
