# 🌱 PlanTree - 计划树游戏（？）

> **用你的专注，培育一片数字森林**

PlanTree 是一款通过麦克风音量控制的专注力可视化工具。根据你的专注模式（安静或朗读），让小树苗成长为参天大树。每日进度独立，但总成就永久积累！

## ✨ 核心特性

- **🎤 双模式切换**
  - **安静模式**：声音低于阈值时树苗生长（适合学习/工作）
  - **早读模式**：声音高于阈值时树苗生长（适合朗读/背诵）

- **🌳 三重成长系统**
  - **🌱 树苗** → **🌳 大树** → **🎄 巨型树**
  - 每积累100%进度获得1棵🌱
  - 可配置合并数量（默认10棵合成下一级）

- **📊 双重进度系统**
  - **每日进度**：每天独立，可参与排行榜
  - **总进度**：永久积累，记录你的所有成就

- **🏆 智能排行榜**
  - 自动保存每日最高分
  - 保留最近7天的详细记录
  - 冒泡排序算法确保公平

## 🛠 技术特性

- **跨平台支持**：完整支持 Windows、Linux 和 macOS
- **POSIX 兼容**：遵循 XDG 规范，支持 Unix-like 系统
- **实时音频处理**：使用 RMS 计算音量强度
- **智能数据存储**：
  - 原子文件写入，防止数据损坏
  - 跨平台路径处理
  - 自动清理旧数据
- **自适应布局**：流式布局自动排列树木
- **暗色主题**：护眼界面设计

## 📦 安装与运行

### 环境要求
- Python 3.7+
- Windows 10+/Linux/macOS（需支持音频输入）

### 安装依赖
```bash
pip install PySide6 sounddevice numpy
```

### 运行
```bash
python main.py
```

### 打包（可选）
```bash
pyinstaller main.spec
```

## ⚙️ 配置说明

### 跨平台数据存储位置

#### Windows
```
%APPDATA%\PlanTree\
├── progress.json        # 主进度（永久）
├── daily_progress.json  # 每日进度（7天）
└── leaderboard.json    # 排行榜数据
```

#### Linux (遵循 XDG 规范)
```
~/.local/share/plantree/
├── progress.json        # 主进度（永久）
├── daily_progress.json  # 每日进度（7天）
└── leaderboard.json    # 排行榜数据
```

#### macOS
```
~/Library/Application Support/PlanTree/
├── progress.json        # 主进度（永久）
├── daily_progress.json  # 每日进度（7天）
└── leaderboard.json    # 排行榜数据
```

### 设置参数
| 参数 | 范围 | 说明 |
|------|------|------|
| 安静阈值 | 0-600 | 安静模式下声音需低于此值 |
| 朗读阈值 | 0-600 | 早读模式下声音需高于此值 |
| 增长速度 | 1.0-100.0 | 每秒增长百分比 |
| 合并数量 | 1-1000 | 合成下一级所需数量 |

## 🎮 使用指南

1. **启动应用**：程序自动开始监听麦克风
2. **选择模式**：
   - 安静模式：保持环境安静
   - 早读模式：大声朗读/说话
3. **观察生长**：根据模式要求，树苗会逐渐生长
4. **查看成果**：
   - 上方显示当日进度条
   - 中间显示培育的树木
   - 下方显示当日和总计分数
5. **提交分数**：每天自动提交最高分到排行榜

## 📊 分数计算

```
每日分数 = 树苗数 × 1 + 大树数 × 合并数 + 巨型树数 × (合并数²)
总分数 = 总树苗数 × 1 + 总大树数 × 合并数 + 总巨型树数 × (合并数²)
```

## 🎯 使用技巧

1. **调整阈值**：根据环境噪音调整阈值，获得最佳体验
2. **每日挑战**：每天都是新的开始，努力创造更高分数
3. **长期积累**：总进度会永久记录你的所有成就
4. **排行榜竞争**：与自己的历史成绩竞争

## 🔧 平台特定说明

### Linux 用户
- **音频支持**：确保安装 PulseAudio 或 ALSA
- **依赖安装**：
  ```bash
  # Ubuntu/Debian
  sudo apt install python3-pip python3-dev portaudio19-dev
  
  # Fedora
  sudo dnf install python3-pip python3-devel portaudio-devel
  
  # Arch Linux
  sudo pacman -S python-pip python-portaudio
  ```
- **Wayland 支持**：自动配置为使用 XCB 后端以确保兼容性

### macOS 用户
```bash
brew install portaudio
pip install PySide6 sounddevice numpy
```

### Windows 用户
- 确保有可用的麦克风
- 无需额外配置

## 📝 代码结构

```
main.py
├── 音频回调函数 (audio_callback)
├── 跨平台路径处理 (get_app_data_path)
├── 数据管理函数 (load/save - 原子写入)
├── TreeManager 类（核心逻辑）
├── FlowLayout 类（自定义布局）
├── SettingsDialog 类（设置界面）
└── LoudnessMonitor 类（主界面）
```

## 🔧 开发说明

### 主要类说明
- **TreeManager**：管理所有游戏逻辑和进度
- **FlowLayout**：实现流式布局，自动排列树木
- **SettingsDialog**：提供用户自定义设置

### 数据流
1. 音频输入 → RMS计算 → 音量值
2. 音量值 → 生长判断 → 进度更新
3. 进度更新 → 树木生成 → 界面刷新
4. 定时保存 → 数据持久化

### 跨平台特性
- **原子文件操作**：使用临时文件+重命名，防止数据损坏
- **权限管理**：Unix 系统自动设置适当权限
- **错误处理**：全面的异常处理，避免程序崩溃
- **向后兼容**：自动处理旧版本数据格式

## 📄 许可证

Apache License 2.0 - 详见 LICENSE 文件

## 👨‍💻 作者

**侯皓铭**（GitHub：[@imjumping](https://github.com/imjumping))  
河北省邢台市第十二中学

**GitHub 仓库**: [https://github.com/imjumping/TreePlanGame](https://github.com/imjumping/TreePlanGame)

## 📋 更新日志

懒得写了

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 🐛 故障排除

### 常见问题

1. **没有声音检测**
   - 检查麦克风权限
   - 确保音频设备正常工作
   - Linux: 检查 PulseAudio 服务状态

2. **数据不保存**
   - 检查数据目录权限
   - 确保有足够的磁盘空间
   - 查看控制台错误输出

3. **界面显示异常**
   - 更新显卡驱动
   - 确保安装了正确的 PySide6 库

### 日志查看
程序启动时会显示数据目录位置和音频设备信息：
```
Starting PlanTree...
Running on Linux, data directory: /home/user/.local/share/plantree
Using audio device: Built-in Audio Analog Stereo
```

## 🌟 设计理念

> "让专注可见，让成长有形"  
> 通过简单的音频交互，将抽象的专注力转化为直观的视觉成果，激励用户保持高效状态。

---

**开始你的专注之旅，培育属于你的数字森林吧！** 🌲

## 📱 未来计划

没

---

*版本：v2.0 | 更新日期：2026年1月*

## 🌐 相关链接

- [GitHub 仓库](https://github.com/imjumping/TreePlanGame)
- [问题反馈](https://github.com/imjumping/TreePlanGame/issues)
- 更新日志（懒得写了）
