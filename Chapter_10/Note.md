# 第10章 扩展Redis

本章从读性能和写性能两方面对Redis的性能进行优化

## 扩展读性能

首先从单机进行考虑：

+ 确保压缩列表上限不要太高以免影响性能
+ 选择合适的结构，尽量避免无意义的全表遍历
+ 存放大体积数据的时候考虑使用合适的压缩算法来减少网络带宽消耗
+ 使用流水线和连接池

对于多机而言，搭建多个从服务器并把读任务分到从服务器上。

为了降低主服务器的带宽可以构建主从树。

## 扩展写性能

首先从单机考虑：

+ 尽可能减少写过程中的读操作
+ 将无关的功能迁移至其他服务器
+ 使用分布式锁而非WATCH/MULTI/EXEC
+ 考虑持久化操作带来的性能影响

对于多机而言，可以对需要读写的数据进行分片，每一片存至不同的服务器。

简单地讲就是构建多个存储不同分片的主服务器用于写入。