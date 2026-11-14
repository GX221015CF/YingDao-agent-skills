# 能力表

当前验证时点为本地候选检查，历史数据单列。具体次数和本轮检查结果见本地 work/validation-result-final.json（不纳入公开文件集）。

|能力|类型与实现位置|验证方式|限制|
|---|---|---|---|
|需求拆解、开发等级及流程分工|方法；skills/yingdao-rpa-copilot|与历史协作方法及示例交叉审阅|不自动产生现场元素|
|六节点分支候选|纯函数；tools/branch_candidate.py|构造、顺序、ID 和依赖引用测试|不是流程解释器；合成 ID 不是实际回读|
|候选局部 Schema 校验|tools/portable_validation.py、schema_subset.py、automation.py|目标错配、未知字段、缺字段、类型、支持子集测试|不证明完整语义依赖或当前官方合同|
|反馈解析|tools/automation.py、portable_validation.py|pending、completed、failed、paused、目标与 run_id、矛盾状态测试|读取合成文件，不查询真实运行|
|组成清单和字段映射|tools/migration.py|共享资源、未解析绑定、重复项、组成缺失测试|complete 为声明；不是完整应用采集|
|资源字节核验|tools/migration.py、migration_paths.py|正确、缺件、改字节、错摘要、过大资源测试|不解码、不下载、不做来源认证|
|路径限制|tools/migration_paths.py、migration.py|越界、设备名、大小写冲突及链接测试|本地材料检查；不是操作系统沙箱|
|图像交付方法和分层模板|skills/yingdao-image-migration|Skill 基础结构及链接检查；历史图像案例对照|不是完整应用分享工具|
|原生连接、写入、保存、运行|本版不提供|本批不执行|需要新的现场适配及授权|
|应用存档、恢复和重建工具|来源项目已有，未纳入本版|本版仅核对所需纯函数来源|不能将清单工具称为导入器|
|106 节点订单实例|历史现场；docs/case-studies/order-rebuild.md|历史配置回读及一次无发货预演|不是本轮运行，不是任意指令通用构建器|
|真实图像与材料交付|历史现场；docs/case-studies/image-delivery.md|历史 SDK、摘要及映射记录|不含本轮真实材料；不证明跨设备完整运行|
|RPA Challenge 新源端使用|当前仓库Skill方法＋外部正常客户端＋任务内适配；docs/case-studies/rpa-challenge-source.md|23节点配置回读及第二轮站点100%、70/70、207689ms|有人工准备应用/捕获元素；任务适配未纳入通用工具，不是目标端迁移验收|

## 当前可复现与未验证

本版命令在本机新项目中验证，同时检查不依赖来源目录、用户名和当前工作目录。Python 3.10 是语法与标准库最低要求，本轮只实际运行 Python 3.12.10；其他 Python 小版本、Linux/macOS 没有在本批实机测试。

不包含任意流程生成、现场执行层、任意元素绑定、目标账号权益验证、完整应用原生导入或无人值守生产运行。不能因离线测试通过宣称这些能力已完成。
