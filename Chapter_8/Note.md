# 第8章 构件简单社交网络

本章1将尝试构建一个类似Twitter的社交网络平台，以及用于第三方的流API

这个社交平台的功能有：

+ 用户可以发送推文，也就是消息
+ 用户可以关注其他用户获取其他用户发送的消息
+ 第三方可以连接流API来获取社交网络上的事件

## 用户和状态

首先需要做的就是存储用户和消息的状态。

这里只需要使用哈希表存储即可。注意每个用户和每条消息都需要有一个唯一ID，并用做哈希表的表名的组成部分。

## 主页时间线

每个用户都会有一个主页时间线，这个时间线存储着其关注的用户所发的消息。

因为消息需要按时间顺序存储（毕竟叫做时间线），故需要使用有序集合来存储时间线。

每个用户的主页时间线为一个有序集合，键为消息ID，值为消息发布的时间戳。

用户除了主页时间线之外还会有个人时间线，用户存储用户自己发的消息。

## 关注者列表和正在关注列表

这个也只需要一个有序集合来存储即可。键为关注或粉丝的ID，值为关注或被关注的时间。

这里会涉及到两个动作：关注和取消关注。

### 关注

当用户A关注用户B时，除了修改用户哈希表和关注者/正在关注列表之外，还需要将用户B的个人时间线并入用户A的主页时间线。

### 取消关注

同样的，当用户A取消关注用户B时，除了修改上述表之外，还需要将用户B的个人时间线上的信息从用户A的主页时间线中去掉（求差集或直接`ZREM`即可）

> 看起来这些方法都十分低效，但其这么做的目的是为了保证用户获取主页信息的高效。当对每个用户维护一个主页时间线的时候，用户获取主页信息就只需要读取主页时间线即可。而由于用户关注/取关的时间频率远小于用户获取主页信息的频率，故用关注/取关事件的性能牺牲换取用户获取主页信息的性能提升是值得的。

## 状态消息的发布与删除

当消息发布的时候，需要做的动作显然有三个：

+ 新建消息，修改消息发布者的个人信息（消息数+1）
+ 将消息ID放入发布者的个人时间线
+ 将消息ID放入所有发布者的粉丝的主页时间线

前两个十分简单，略。

问题在于最后一个。当发布者的粉丝量足够大的时候这个动作显然会十分缓慢，故需要：

+ 将消息发布到前1000个粉丝的主页时间线
  + 这里的1000是基于统计数据得出的，Twitter上粉丝数超过1000的用户占比补到0.1%，为了照顾99.9%的其他用户故需要这么做。
+ 开启一个延迟任务，将消息推送至剩余的粉丝的主页时间线

这样就可以保证请求可以快速返回

删除同理

## 流API

流API用于提供给第三方接入获取事件数据。

这里的事件数据仅包括发布消息和删除消息。

为了达成此目的需要构建一个**HTTP流服务器**，这个服务器提供的接口接收请求之后会保持连接并换为HTTP的分块传输模式，不断地将事件数据返回给客户端。类似于订阅发布模式。
