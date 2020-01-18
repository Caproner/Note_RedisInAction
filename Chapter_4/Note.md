# 第4章 数据安全与性能保障

本章主要讨论Redis的数据安全与性能问题，主要包括如下内容：

+ Redis持久化
+ Redis系统故障处理
+ Redis事务、非事务型流水线
+ Redis性能问题

## 持久化

Redis的持久化策略包括两种：

+ 快照
+ 只追加文件（AOF）

其可以通过修改配置文件`redis.conf`来开启/关闭这些持久化策略，或者修改这些策略的细则。

### 快照

快照任务会将当前Redis的所有数据以配置项`dbfilename`为文件名，写入配置项`dir`指向的目录。

触发快照任务的方法有：

+ 客户端发送`BGSAVE`命令
  + 此时Redis会fork一个子进程执行快照任务
+ 客户端发送`SAVE`命令
  + 此时Redis会直接执行快照任务，在任务结束之前不再响应任何其他命令
+ 配置文件中设置`save`选项以配置触发任务
  + `save`选项的格式为`save s n`，表示当`s`秒内有`n`次写入的时候就会自动执行`BGSAVE`
  + 支持设置多个`save`，只要有一个满足就会执行
+ Redis正常关闭时
  + 通过`SHUTDOWN`命令关闭或者接收到标准`TERM`信号时为正常关闭
  + 此时Redis会先执行`SAVE`再关闭
+ 复制之前，具体参考后面讲到的Redis复制

当Redis服务器重启的时候便会自动载入快照以恢复数据

### AOF

Redis会将每个写命令都放入AOF文件中。当Redis重启的时候，只需要从头到尾执行一遍AOF文件的命令即可还原数据。

其对应的配置选项`appendfsync`有三种不同的取值：

+ `always`：每个Redis写命令实时同步进文件中
+ `everysec`：每秒执行一次同步
+ `no`：让操作系统来决定何时进行同步

一般比较常用的是`everysec`。

#### 重写AOF文件

随着时间的增长，AOF文件会越来越大（甚至比Redis本身存的数据都大），其中冗余的命令会越来越多。

此时就需要对AOF文件进行重写以压缩其体积。

在Redis中使用`BGREWRITEAOF`即可重写`AOF`文件，它会fork一个进程来做这件事情

### 持久化的优劣

持久化可以让Redis数据更加安全，减少数据丢失的风险和量级。

同时执行持久化策略本身需要消耗大量的时间和资源，这会拖慢Redis的运行速度。

## 多机部署

Redis可以通过部署多机并配置好主从关系来提升读性能。

### 建立主从关系

两台Redis服务器可以确定主从关系，此时从服务器的数据来源会被绑定在主服务器上，当主服务器执行写命令的时候，其会将命令同步给从服务器一并执行。

在预定成为从服务器的机子上使用`SLAVEOF host post`命令使其成为主服务器`host:port`的从服务器。

其过程如下：

+ 从服务器执行命令，向主服务器发送`SYNC`命令请求同步
+ 主服务器收到命令，开始执行`BGSAVE`，并开启一个缓存区记录接下来收到的所有写命令
+ `BGSAVE`执行完毕之后，将快照文件传给从服务器
+ 从服务器丢弃自己的所有数据并接收主服务器的快照文件并载入
+ 快照文件传送完毕，主服务器会先将缓存区的写命令推送给从服务器，之后便每收到一个写命令就推送给从服务器
+ 从服务器载入完成之后开始接收主服务器的写命令

有两点需要注意的是：

+ 机子可以通过设置`SLAVEOF no one`来停止接收主服务器的数据，以解除主从关系
+ 在配置主从服务器之后，还需要额外配置一个外部的负载均衡来实现分布式读

### 主从链

Redis可以通过主从关系建立类似树的主从链关系

### 检验硬盘写入

当确立主从关系之后，用户需要通过检验写入来确定主从服务器是否同步完成。

方法很简单，往主服务器上写个东西，然后去从服务器上读，读的到则说明同步完成。

## 处理系统故障

Redis服务器可能会出现系统故障，其分如下两种：

+ 可恢复运行的故障
+ 不可恢复运行的故障

针对第一种，只需要通过之前的持久化数据还原即可

针对第二种，则需要重新梳理主从链，即为在主从链中去掉当前服务器节点，并让其所有从服务器接入新的主服务器（或者让其中一台成为新的主服务器）

## Redis事务

Redis处理事务的命令有：`WATCH`，`UNWATCH`，`MULTI`，`EXEC`，`DISCARD`。

其中`WATCH`，`MULTI`，`EXEC`之前已经介绍过了，而`UNWATCH`则为取消`WATCH`，`DISCARD`则为取消事务。

其与关系型数据库的事务的不同点在于其需要手动维护数据一致性。对于关系型数据库而言。其能够保证在执行事务的过程中相关数据不会被修改，而Redis的事务仅仅是一连串指令执行。

这个差异在二阶提交事件中尤为突出。二阶提交是指【数据库进行读操作，并根据读操作结果来执行写操作】。关系型数据库的事务可以通过给数据上锁来避免脏读的情况，而Redis事务需要通过`WATCH`来停止可能出现脏读的事务。

Redis处理二阶提交事务的大致框架为：

+ WATCH需要读和写的数据
+ 执行读操作，如果读操作的结果使得写操作无需进行则执行`UNWATCH`，并结束事务
+ 否则执行`MULTI`+写操作+`EXEC`来执行事务
+ 当`EXEC`执行失败的时候重试事务（回到步骤1）

简单的讲，关系型数据库通过给数据加锁的操作来保证数据一致性（悲观锁），而Redis通过重试可能会出现数据不一致性的事务来保证数据一致性（乐观锁）。

## 非事务型流水线

之前的Python代码中会使用`pipeline`来创建流水线并执行事务，但有时候我们并不需要其事务功能，而是单纯需要一次性执行多个指令。这个时候就就可以使用非事务型流水线。

在Python中，只需要在创建流水线的时候传入`False`即可创建非事务型的流水线：

```
pipe = conn.pipeline(False)
```

非事务型流水线快于事务性流水线。

## 性能注意事项

redis自带压测工具`redis-benchmark`可以用于测试redis服务器性能。一般而言服务器使用Redis的真实性能为测试数据的50%~60%。当低于这个数值的时候就需要考虑Redis连接复用的问题了（也就是减少创建新连接的情况）。