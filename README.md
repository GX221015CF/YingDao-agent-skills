# YingDao-agent-skills

面向影刀 RPA 的 Agent 协作方法、最小离线工具和脱敏案例。当前为 **v0.1.0 候选**：清楚文档、可运行离线示例和历史案例摘要已整理，纳入 MIT 许可与私有版本管理范围。仓库保持私有，尚未公开；未安装或替换全局 Skill。

这里有两条路径：

1. **从业务需求到自动化搭建**：使用 yingdao-rpa-copilot 整理输入输出、流程、变量和验收；本版用六节点小分支演示候选校验和反馈解析。
2. **从已有应用到迁移复用**：先明确流程、元素、资源和依赖组成；本版用合成清单演示材料、字段映射、摘要和缺件核验。yingdao-image-migration 负责图像迁移方法与模板，不是完整应用分享或原生导入器。

## 快速开始

环境：Python 3.10+，仅标准库；本轮实测 Python 3.12.10 / Windows。无需登录影刀、安装依赖或联网。

在仓库根目录运行：

```powershell
python -B tools/offline_demo.py automation
python -B tools/offline_demo.py migration
python -B -m unittest discover -s tests -v
python -B tools/check_repository.py
```

自动化示例应输出六个节点、两个候选请求、目标错配和无效输入的拒绝结果，以及 pending、completed 两种反馈状态。它不发送这两个请求，也不运行影刀。

迁移示例应输出一个资源、两个字段绑定、共享资源 U01 和 verified。图像解码、来源认证、目标保存、账号访问和原生导入仍标记 false。这里的完整组成是输入的声明，不是工具独立采集了完整应用。

示例只打印 JSON。测试使用 work 下独立临时目录并正常清理，不修改示例原件。命令退出码 0 表示本命令的离线检查通过；2 表示输入或材料检查未通过。反馈解析中的 failed 是一个已识别状态，解析通过不等于流程成功。

如果工作目录不同，可以用入口的绝对路径；默认示例按入口位置定位，不依赖用户名或来源项目。

## 继续尝试

- [自动化示例：候选和反馈命令](examples/automation/README.md)
- [迁移示例：共享资源、缺件和内容变化](examples/migration/README.md)
- [自动化搭建 Skill](skills/yingdao-rpa-copilot/SKILL.md)
- [图像迁移 Skill](skills/yingdao-image-migration/SKILL.md)
- [本次离线验证结果](docs/validation.md)

Skill 是给 Agent 的方法与判断指导。离线工具是本仓库的独立 Python 代码；只复制一个 Skill 文件不会自动获得工具、现场连接或执行权限。本候选不执行安装。

## 目录

|位置|内容|
|---|---|
|skills/|两个 Skill 的公开候选及必要参考|
|tools/|纯函数提取和最小离线适配，无现场客户端|
|examples/|合成 Schema、候选、反馈、资源和预期结果|
|tests/|候选、反馈、迁移及 CLI 离线测试|
|docs/|架构、能力表、来源说明和脱敏案例|
|public-files.json|经审阅的精确版本管理文件集；沿用原文件名，不代表获准公开|
|LICENSE|标准 MIT 许可证；适用范围见许可说明|
|work/、.local/|本地任务上下文、验证回执和内部出处，不纳入公开范围|

## 已有能力与边界

[能力表](docs/capabilities.md)列出实现位置、验证方式和限制；[架构说明](docs/architecture.md)解释五类资产的区别。

- 当前可直接复现：合成分支候选的局部 Schema 校验；运行状态解析；组成声明、共享映射和资源字节检查。
- 历史实测：106 节点实例重建及无发货预演；4 项真实本地图像独立 SDK 匹配；21 份图像补充材料交付。参见[订单案例](docs/case-studies/order-rebuild.md)和[图像交付案例](docs/case-studies/image-delivery.md)。
- 新源端验证：[RPA Challenge Input Forms](docs/case-studies/rpa-challenge-source.md) 使用当前 Skill 方法、外部已存在正常客户端及本任务局部适配，经过一次失败修正后取得站点 100%（70/70）。该案例不表示本仓库已包含通用现场执行器或跨设备迁移能力；本批新增记录仅本地保存，未推送。
- 进阶源端验证：[Excel 订单核查与对账](docs/case-studies/order-reconciliation-source.md) 使用原生网页查询与 CodeFlow 计算，16 行正常及异常结果与事先冻结的独立预期全部一致。新增解析与报表代码、原始材料及现场适配留在本地工作目录，仓库仅纳入脱敏复盘；本批未推送。
- 当前未包含：现场进程发现、MCP 传输、写入执行器、自动保存或运行、完整应用采集、原生导入、账号权益迁移、图片下载和解码工具。
- 手动使用影刀不等于通过 Skill 自动搭建；图像材料核验不等于完整应用分享；历史案例成功不证明当前用户环境或任意版本兼容。

## 来源、公开范围与后续

本版只整理自编方法、纯函数和合成材料，没有商业程序集、提取代码、真实业务图像、名单、完整订单日志或原始配置。公开文件通过来源编号追溯改编关系，私人出处留本地。详见[来源与适配](docs/provenance.md)及[公开范围审阅](docs/publication-review.md)。

个人分工：项目发起人承担需求定义、方案取舍、现场反馈和使用验收；Codex 协助代码、配置、工具执行和证据整理。

有权许可的自编内容采用 [MIT](LICENSE)，来源和商标边界见[许可说明](docs/licensing.md)。MIT 许可与仓库可见性分别管理；当前仅进行私有版本保存与同步，不能称为公开发布，也没有获得以后转公开的授权。

“演示操作＋讲解＋规则补充”暂缓，仅在[路线图](docs/roadmap.md)记录，不是第一版阻塞。
