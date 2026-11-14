# 迁移材料最小示例

本目录是自定义离线清单及合成材料，不是影刀原生工程。manifest.json 列出五类组成声明、一个小型 SVG、两个 selector 的 semantic.image 字段到同一资源 U01 的映射；状态均为 disabled。

reference.svg 由本项目生成，没有业务内容。modified.svg 是颜色已变的合成副本，清单仍使用原参考内容摘要，用于证明变化能够被发现。工具不渲染或解码 SVG。

从仓库根运行：

```powershell
python -B tools/offline_demo.py migration
python -B tools/offline_demo.py migration --manifest examples/migration/manifest-missing.json
python -B tools/offline_demo.py migration --manifest examples/migration/manifest-changed.json
```

预期：

|命令|资源状态|退出码|
|---|---|---|
|默认|verified；2 处绑定共享 U01|0|
|manifest-missing|missing；绑定仍保留|2|
|manifest-changed|changed；拒绝将内容变化记为完整|2|

完整 JSON 预期分别见 [expected.json](expected.json)、[expected-missing.json](expected-missing.json)、[expected-changed.json](expected-changed.json)。

检查只读取清单指定对象，不扫描寻找替代品。每个资源最多 1 MiB；清单最多 100 个资源和 1000 处绑定。拒绝越界路径、链接、重复 ID、冲突路径和无法解析的绑定。缺少组成声明会报错；complete=false 会保留，不能把未知组成改成空清单。

“资源 verified”只表示本地文件与清单字节数和 SHA-256 一致；不证明历史原图身份、图片解码、目标工程保存、账号访问、加载或运行。组成 complete 是输入声明，不是采集认证。

本例不创建迁移容器、不恢复应用目录、不生成可执行重建请求、更不调用原生导入。不同产物的边界见[架构说明](../../docs/architecture.md)。
