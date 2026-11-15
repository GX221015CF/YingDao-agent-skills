# 演示媒体、来源与权利边界

## 文件

|文件|用途与规格|来源|
|---|---|---|
|[yingdao-rpa-copilot-intro.mp4](yingdao-rpa-copilot-intro.mp4)|已审阅成片的原字节副本；112秒、1920×1080、30fps、H.264/yuv420p、静音，2,828,643字节|MEDIA-01|
|[yingdao-rpa-copilot-cover.png](yingdao-rpa-copilot-cover.png)|README封面；1600×900，官方Logo加文字，个人项目·非官方|MEDIA-02、MEDIA-03|
|[yingdao-rpa-copilot-cover.svg](yingdao-rpa-copilot-cover.svg)|可编辑封面；文本使用Microsoft YaHei/Noto Sans CJK SC等系统字体，不附带字体文件|MEDIA-02、MEDIA-03|
|[yingdao-official-mark.svg](yingdao-official-mark.svg)|影刀官网引用的App标识原件，30×30 viewBox，可等比缩放|MEDIA-02|
|[media-manifest.json](media-manifest.json)|上述四个媒体的长度、SHA-256、类型和权利分类|本次核对|

成片SHA-256：`5ae2a51adcb3113fcd7c63a97db4df2c2014629b6b4b3e051486d62638a7279c`。仓库副本与维护者认可的成片一致，没有重剪、转码或再次渲染视频。源文件名包含first-cut-v1，这是制作阶段名称；维护者已观看并明确认可本版作为仓库展示成片。

## 官方Logo的准确来源

- **MEDIA-02 来源页面：** [影刀官网首页](https://www.yingdao.com/)。
- **官方页面引用：** 首页HTML的`link rel="shortcut icon"`明确指向下列SVG；不是从安装包或第三方图片站提取。
- **资源地址：** [官网引用的App标识SVG](https://winrobot-pub-a-dev-1302949341.cos.ap-shanghai.myqcloud.com/image/20260901134651/5401fcb49f712bdcf1784a2c0da52685.svg)。
- **取得日期：** 2026-11-15；原件1,553字节，SHA-256为`a762f487a14dd34de5eea96b37c6af64eaf2f18befaf2c72860ff31bbc355dc8`。
- 封面嵌入原标识并等比放大，保留原颜色和图形；没有仿制、重绘或制作官方认证标识。官网完整字标未纳入仓库。

官网公开可访问不等于MIT或全面再分发许可。本次读取的首页及SVG未提供该Logo的开放许可，也未发现针对此次标识使用的明确限制；本项目仅以产品识别和个人项目说明为目的引用。Logo及影刀商标归各自权利人，**不属于本项目MIT范围**，也不表示官方合作或认可。进一步使用仍须遵循权利人的适用要求，本说明不授予任何第三方商标权利。

## 视频与封面中的权利分类

- **MEDIA-01**：用户认可的个人项目演示成片。剪辑、字幕与示意为项目制作内容；实际影刀、浏览器及表格界面和所涉标识属于各自权利人。整段MP4不作为纯自编代码适用MIT，不授予外部软件、界面或商标的再许可。
- **MEDIA-03**：本项目自编封面排版和文字可按项目MIT使用；嵌入其中的MEDIA-02标识除外，合成PNG同样保留该例外，不作为无权利限制图片。
- 视频原始三段录屏、制作工程、全部抽帧、工作簿、完整日志与内部来源记录未纳入文件集。详细私人路径只留维护者本地。

## 隐私与事实核对范围

制作验证记录包含全片3360帧解码、385张去重来源画面的本地OCR/裁切遮挡审查、870次成片遮挡区域检查及18张导出代表帧敏感模式核对。本批复核这些记录、成片摘要及必要的已脱敏镜头总览，维护者的观感认可另行记录，不替代隐私检查。有限检查不保证发现所有敏感信息。

首次正式运行的127项配置和229项内容核验，与重复运行补丁的本地检查、后续手工运行画面分别归属，见[视频案例](../case-studies/order-recording-demo.md)。后续录屏显示运行结束和三张报表，没有新增同级独立业务验收。

## GitHub访问

[仓库视频文件页](https://github.com/GX221015CF/YingDao-agent-skills/blob/main/docs/media/yingdao-rpa-copilot-intro.mp4)提供文件信息；[原文件查看/下载入口](https://github.com/GX221015CF/YingDao-agent-skills/raw/refs/heads/main/docs/media/yingdao-rpa-copilot-intro.mp4)指向同一受仓库权限控制的内容。私有仓库需要相应权限，访问者可能先登录。README只使用可点击封面和链接，不保证各端都内嵌播放。

本批只同步到现有私有main，不使用Git LFS、外部托管、Release或Pages；以后是否公开由维护者另行决定。
