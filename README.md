# 2024 NUS SOC Summer workshop

Contributor

**SUSTech** `SHU YANG`

**HKUST** `ZHANG DEXIAO`

**UESTC** `YAN ZISONG`

**SCU** `WANG YU`

NUS 暑校`sws3009`DL&Robot的仓库，欢迎食用。

**先叠甲**

coding的时候没有注重可读性，~~码风看着像谢特~~

整理仓库的时候也没有关注是否是final version可以正常运行，祝后面的xdm好运啦。

## baseline

在laptop上操控机器人，根据机器人摄像头的实时画面寻找贴在教室角落的猫猫图片并识别种类，大部分代码可以用老师给的demo。group拓展了一下前端界面 ~~虽然我们没有一个人会前端~~，可以用鼠标按钮输入或监听键盘输入，"X"用于停止，WASD和IJKL是两种不同的移动方式，“P”用于机器人拍摄图片，拍摄后使用flask传给sever端进行识别，前端轮询sever获取识别结果，打印在页面最下方。

最终模型分类accuracy5/8（大悲），因此给出训练脚本和模型。~~用于祸害后人~~~

~~和别的组交流后可以直接在页面进行实时识别，等到识别结果对了在示意TA，真是卑鄙啊~~

<img src=".\imag\frontend.png" alt="image-20240718171437736" style="zoom:33%;" />

## **Advanced**

group先自己设想一个现实场景，然后利用DL和robot的相关技术满足需求。教授会与你的advanced project进行讨论，他们重点关注的是服务场景，而不是实现技术。

一开始哥几个选了个地狱难度，服务家居老人，设想了几个情境因为实现难度反复横跳毫无进展，TA给了我们的方案是用第三方摄像头，根据画面进行路径规划，在我们的不断努力~~简化~~下，最后确定的服务场景如下：

使用第三方摄像头进行监控，检测到人物跌倒后给小车发送命令抓取药品，通过模型识别人脸将药品送到倒地的人附近

实现过程中，小车（树莓派）和server端通过socket套接字进行通信。

detect_fall.py运行在第三方摄像头（PC）上，使用yolov5模型进行实时识别是否有人跌倒，检测到有人躺板板后向小车发送start命令。运行detect_fall需要在工作区准备yolov5仓库的源码，这里只给出调用模型进行识别的代码。

小车（run_pi.py）接收到start命令后按照设定好的路线抓取药品，随后与server端（run_pc.py）通信，识别人脸，将药品送到人脸附近后松开夹子。

追踪人脸的控制思路其实也很简单，如果找不到人就原地转圈，识别到人脸后，人脸在左就将小车右转，人脸在右就左转，在中间就前进，直到人脸足够大时停止，如果追求精度可以使用PID控制。

追踪人脸的部分主要参考了一位老哥的仓库，识别人脸的模型跟这个老哥的仓库用的是同一个，是一个轻量级的开源人脸识别模型Ultralight。相对于baseline的静态图片分类，advanced是对视频流逐帧进行模型推理，哥几个也不会配cuda环境只能用cpu跑模型推理，所以注重模型的轻量化，包括前面的yolov5跌倒检测模型。

 [仓库传送门](https://github.com/rossning92/rpi-robot "再生父母")

 [b站视频传送门](https://www.bilibili.com/video/BV14g4y1q7yf/?spm_id_from=333.337.search-card.all.click&vd_source=aced0fa103df46581a09368bd73bc5b5 "再生父母")

最终成品，当当当当

<img src=".\imag\car.jpg" alt="微信图片_20240718205539" style="zoom: 33%;" />



最后有一个项目展示视频，感谢成电小哥哥的出镜
[传送门](https://www.bilibili.com/video/BV1xm87efEzd/?spm_id_from=333.999.0.0&vd_source=93416ee72e7283489256aea874287725)
