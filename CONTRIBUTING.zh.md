# 为 huaweicloud 做贡献

> **语言切换：** [English](./CONTRIBUTING.md) | 中文

首先，感谢您考虑为 huaweicloud 做出贡献！🎉

## 行为准则

本项目及所有参与者受[行为准则](CODE_OF_CONDUCT.md)约束。参与即表示您认同并遵守该准则。

## 如何贡献？

### 报告 Bug

- **先检查是否已有人报告** — 搜索现有 Issues
- **新建 Issue** — 使用 Bug Report 模板，填写所有部分
- **尽量提供最小可复现示例**

### 建议新功能

- **先检查是否已有人建议** — 搜索现有 Issues
- **新建 Issue** — 使用 Feature Request 模板

### 提交 Pull Request

1. Fork 本仓库
2. 创建功能分支（`git checkout -b feat/my-feature`）
3. 进行修改
4. 确保所有测试通过（`npm test`）
5. 使用[约定式提交](https://www.conventionalcommits.org/zh-hans/)规范的描述提交：
   - `feat: add new feature`
   - `fix: resolve bug in module`
   - `docs: update README`
6. 推送到您的 Fork，并向 `main` 分支发起 Pull Request
7. 等待 Review — 至少 2 人批准

## 开发环境搭建

```bash
git clone https://github.com/huaweicloud/huaweicloud.git
cd huaweicloud
npm install
npm run dev
```

## 代码风格

- 遵循项目现有代码风格
- 提交前运行 `npm run lint` — 所有 lint 检查必须通过
- 为新功能编写测试

## 许可证

通过贡献，您同意您的贡献将按照 Apache License 2.0 许可。
