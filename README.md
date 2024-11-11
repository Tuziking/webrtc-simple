# webrtc-simple
>简单的webrtc实践记录，Android做客户端，java和python分别作为p2p协议的两个服务器
### 文件目录
```
webrtc-simple
├── android 用于实现Android客户端的webrtc推流
├── host-java 用于实现java端的webrtc服务器，负责处理sdp的交换
└── python 用于实现python客户端的webrtc拉流，maybe可以用来做一些cv的处理
     
```
### 项目简介
- 本项目是一个简单的webrtc实践项目，主要用于学习webrtc的使用，以及webrtc的一些原理
- 项目分为三个部分，分别是Android端的webrtc推流，java端的webrtc服务器，python端的webrtc拉流
  - java实现的webrtc服务器主要用于处理sdp的交换，只作为中转使用，具体推拉流需要客户端来建立P2P连接

### 碎碎谈
- webrtc的服务器与Android端借助于Android Studio开发实战：从零基础到APP上线这本书（第三版）
- python的webrtc拉流部分是自己实现的（webrtc的相关可用资源太少了！！！！），主要使用了python的一个webrtc库，具体的实现可以参考代码