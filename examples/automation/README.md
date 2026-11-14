# 自动化最小示例

本目录全为合成数据。contract.json 是用于测试的局部 Schema，不是当前影刀工具导出；candidate.json 的应用、流程和节点 ID 都没有现场身份。

六节点结构复用既有小分支方法：设置变量 → IF → 真分支日志 → ELSE → 假分支日志 → ENDIF。fill 中四项对应需要字段配置的节点。合成 block_id 是夹具，不是插入后真实返回值。

从仓库根运行：

```powershell
python -B tools/offline_demo.py automation
python -B tools/offline_demo.py candidate --candidate examples/automation/candidate.json --contract examples/automation/contract.json
python -B tools/offline_demo.py feedback --feedback examples/automation/feedback-running.json --contract examples/automation/contract.json --run-id synthetic-run-1
python -B tools/offline_demo.py feedback --feedback examples/automation/feedback-completed.json --contract examples/automation/contract.json --run-id synthetic-run-1
```

第一个命令依次验证正常候选、内存构造的目标错配和布尔型索引错误，然后解析 running 与 completed；标准结果见 [expected.json](expected.json)。其余命令分别校验给定输入。

- candidate 的通过层级是 offline_request_schema_only，executable=false。它不证明变量完整依赖、运行表单或当前合同。
- pending 不等于失败；completed 需要结束后的零错误核验字段。
- app_id、flow_id、run_id 必须对应，矛盾或未知状态拒绝，不建议重新运行。
- 合成反馈来自文件，解析器没有查询真实运行状态。

更改字段、类型或目标可观察退出码 2。无需连接 Studio，也不需要原项目目录。
