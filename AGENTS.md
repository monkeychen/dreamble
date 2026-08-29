# dreamble 项目规范

本仓库集中维护「聊哉梦呓」相关产品、个人站、Agent Skills 和提示词资料。

## 项目专用skills位置

**物理存放**：`skills/`（本站原创技能）与 `.workbuddy/skills/`（外部技能软链，已 gitignore）。

**加载入口**：内核只扫描 `{workspace}/.codebuddy/skills/` 与 `~/.workbuddy/skills/`（用户级）。
`skills/` 和 `.workbuddy/skills/` 本身**不会被扫描**。

约定：
- **物理唯一存放** `.workbuddy/skills/`（软链集合，已被 gitignore）。
- 项目根 `.codebuddy -> .workbuddy`（与平台自建的 `.claude -> .workbuddy` 同一套别名机制），
  使 `.codebuddy/skills` 解析到 `.workbuddy/skills`，从而被内核加载。
- 本站原创技能源码放 `skills/`（进版本库），另在 `.workbuddy/skills/` 建相对软链 `../../skills/<name>` 挂载。

新增或接入任何技能，除放进物理目录外，必须确认 `.workbuddy/skills/<name>/SKILL.md` 可解析，否则不生效。
`.codebuddy`、`.workbuddy` 均已加入 .gitignore，不进版本库。

## 规则范围

- 本文件适用于仓库根目录及未设置独立规则的子目录。
- 子目录存在 `AGENTS.md`、`CLAUDE.md` 或其他协作规范时，优先遵守离目标文件最近的规则。
- 新增目录前先明确用途、结构、命名和清理规则；不要在仓库根目录堆放临时产物。
- 各子项目独立运行和验证，仓库根目录不设置虚假的统一构建命令。

## 修改与验证

- 只修改当前任务涉及的文件，不夹带工作区内的无关改动。
- 修改后运行对应子项目的 test、lint、check 或 build；不能用跳过检查、注释错误等方式换取通过。
- 技术决策说明“为什么”和“对用户的影响”，优先保证实际使用体验。
- 密钥、Token、密码、部署账号和本地环境文件不得提交。

## Git 交付规则

- 这是站主个人维护的项目。完成任务并通过验证后，默认直接在 `main` 分支 commit，并执行 `git push origin main`。
- 默认不创建功能分支、不创建 Pull Request；只有站主当次明确要求时才使用分支或 PR。
- 提交前确认暂存范围，只提交本次任务文件。
- commit message 使用简洁英文，准确描述变更意图。
