# 第3章 Redis命令

本章主要了解Redis的常用命令

## 字符串

字符串本身是一个key-value组。其值可以是字符串、整数、浮点数三种之一。

其中由数字组成的字符串会自动转化为整数或浮点数。

其整数取值范围跟随机器的long类型取值范围（32位机器上为32位，64位机器上为64位），浮点数为IEEE 754标准的双精度浮点数。

### 自增/自减

字符串可以对其值进行自增/自减操作：

| 命令        | 用例                   | 描述                                | 时间复杂度 |
| ----------- | ---------------------- | ----------------------------------- | ---------- |
| INCR        | INCR key               | 令键key对应的值自增1                | O(1)       |
| DECR        | DECR key               | 令键key对应的值自减1                | O(1)       |
| INCRBY      | INCRBY key amount      | 令键key对应的值自增amount           | O(1)       |
| DECRBY      | DECRBY key amount      | 令键key对应的值自减amount           | O(1)       |
| INCRBYFLOAT | INCRBYFLOAT key amount | 令键key对应的值自增amount（浮点数） | O(1)       |

这五个自增/自减命令的返回值均为自增/自减后的值，若目标值无法解释为数字则会报错

### 字符串整体读写操作

字符串支持简单的读取（GET）和写入（SET）操作，以及基于其的扩展操作：

| 命令   | 用例                      | 描述                                                         | 时间复杂度 |
| ------ | ------------------------- | ------------------------------------------------------------ | ---------- |
| SET    | SET key value             | 设置key的值为value<br/>当key已经存在时覆盖其原来的值<br/>可以追加的参数有：<br/>EX sec：设置key过期时间，单位为秒<br/>PX millisec：设置key过期时间，单位为毫秒<br/>NX：只在键不存在时才对键进行操作<br/>XX：只在键存在时才对键进行操作 | O(1)       |
| GET    | GET key                   | 返回key对应的值<br/>若key不存在则返回nil                     | O(1)       |
| GETSET | GETSET key value          | 相当于SET key value<br/>区别在于GETSET会返回其被修改之前的值 | O(1)       |
| SETNX  | SETNX key value           | 相当于SET key value NX                                       | O(1)       |
| SETEX  | SETEX key sec value       | 相当于SET key value EX sec                                   | O(1)       |
| PSETEX | PSETEX key millisec value | 相当于SET key value PX millisec                              | O(1)       |

### 字符串批量读写操作

Redis提供了用于批量SET和GET的操作，这些操作都是原子的：

| 命令   | 用例                             | 描述                                                         | 时间复杂度           |
| ------ | -------------------------------- | ------------------------------------------------------------ | -------------------- |
| MSET   | MSET key value [key value ...]   | 设置多个key的值<br/>相当于多次SET                            | O(N)<br/>N为键的数量 |
| MSETNX | MSETNX key value [key value ...] | 相当于多次SETNX<br/>当其中某个键已经存在时会全部失败<br/>也就是要么全部成功返回1<br/>要么全部失败返回0 | O(N)<br/>N为键的数量 |
| MGET   | MGET key [key ...]               | 获取多个key的值<br/>相当于多次GET<br/>其会返回一个列表       | O(N)<br/>N为键的数量 |

### 针对字符串特性的读写操作

字符串同样支持针对值的字符串特性的读写操作，其中包括：

+ 取字符串长度
+ 字符串尾部添加
+ 字符串区间读写

| 命令     | 用例                      | 描述                                                         | 时间复杂度                                                   |
| -------- | ------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| STRLEN   | STRLEN key                | 返回key对应的值的长度<br/>key不存在时返回0                   | O(1)                                                         |
| APPEND   | APPEND key value          | 将value尾部添加到key对应的值中                               | O(1)                                                         |
| GETRANGE | GETRANGE key start end    | 返回key对应的值的[start, end]部分<br/>其中start和end相当于数组下标<br/>支持负的下标-x，此时表示倒数第x位 | O(N)<br/>其中N为返回部分的长度                               |
| SETRANGE | SETRANGE key offset value | 从偏移量offset开始，用value覆盖key对应的值<br/>此举不会减少key对应的值的长度 | 如果value较短则为均摊O(1)<br/>如果value较长则为O(M)<br/>其中M为value的长度 |

### 位图操作

不同于字符串，位图操作将key-value组的value看作是二进制位数组。

其对应的位图命令可以操作这些二进制位：

| 命令     | 用例                           | 描述                                                         | 时间复杂度 |
| -------- | ------------------------------ | ------------------------------------------------------------ | ---------- |
| SETBIT   | SETBIT key offset value        | 设置key对应的值的偏移量为offset的位为value<br/>value的取值只可以是0或1 | O(1)       |
| GETBIT   | GETBIT key offset              | 获取key对应的值的偏移量为offset的位                          | O(1)       |
| BITCOUNT | BITCOUNT key [start] [end]     | 获取key对应的值的1的个数<br/>可以使用start和end来指定区间    | O(N)       |
| BITPOS   | BITPOS key bit [start] [end]   | 获取key对应的值的第一个为bit的位的位置<br/>可以使用start和end来指定区间 | O(N)       |
| BITOP    | BITOP op destkey key [key ...] | 对一到多个key对应的值执行op操作<br/>并将结果存到destkey中<br/>可选的op有：AND OR NOT XOR | O(N)       |

## 列表

列表即为一个key-value**s**组，其用一个key关联一个线性表

### 常用操作

| 命令      | 用例                        | 描述                                                         | 时间复杂度 |
| --------- | --------------------------- | ------------------------------------------------------------ | ---------- |
| RPUSH     | RPUSH key value [value ...] | 将value从列表右端PUSH进去                                    | O(1)       |
| LPUSH     | LPUSH key value [value ...] | 将value从列表左端PUSH进去<br/>注意当value有多个的时候，<br/>由于是依次PUSH，<br/>故PUSH后的列表的左端顺序<br/>跟命令列出来的顺序是相反的 | O(1)       |
| RPOP      | RPOP key                    | 从列表右端POP出一个value                                     | O(1)       |
| LPOP      | LPOP key                    | 从列表左端POP出一个value                                     | O(1)       |
| LINDEX    | LINDEX key index            | 返回下标为index的元素<br/>同样支持负下标                     | O(N)       |
| LRANGE    | LRANGE key start end        | 返回子列表[start, stop]                                      | O(N)       |
| LTRIM     | LTRIM key start stop        | 将列表修建为只剩[start, end]                                 | O(N)       |
| RPOPLPUSH | RPOPLPUSH src dest          | 将src的右端元素POP出来<br/>并PUSH到dest的左端<br/>返回POP出来的元素 | O(1)       |

### 阻塞式操作

列表支持阻塞式操作，也就是在操作时如果列表为空则会阻塞一段时间直到列表不为空或超时

| 命令       | 用例                        | 描述                                                         | 时间复杂度 |
| ---------- | --------------------------- | ------------------------------------------------------------ | ---------- |
| BLPOP      | BLPOP key [key ...] timeout | 对第一个非空列表LPOP<br/>返回被LPOP的列表名和元素<br/>如果所有列表都是空则阻塞最多timeout秒 | O(1)       |
| BRPOP      | BRPOP key [key ...] timeout | 对第一个非空列表RPOP<br/>返回被RPOP的列表名和元素<br/>如果所有列表都是空则阻塞最多timeout秒 | O(1)       |
| BRPOPLPUSH | BRPOPLPUSH src dest timeout | RPOPLPUSH的阻塞版本                                          | O(1)       |

## 集合

其与列表一样是一个key-values组，不同的是其对应的values不是一个线性表而是一个不可重复的集合

### 常用操作

| 命令        | 用例                     | 描述                                                         | 时间复杂度                       |
| ----------- | ------------------------ | ------------------------------------------------------------ | -------------------------------- |
| SADD        | SADD key item [item ...] | 将item添加进集合中                                           | O(N)<br/>N为添加的item数量       |
| SREM        | SREM key item [item ...] | 将item从集合中移除<br/>不存在的item会被忽视                  | O(N)<br/>N为需要移除的item数量   |
| SISMEMBER   | SISMEMBER key item       | 返回item在集合中是否存在                                     | O(1)                             |
| SCARD       | SCARD key                | 返回集合的基数（即元素个数）                                 | O(1)                             |
| SMEMBERS    | SMEMBERS key             | 返回集合的所有元素                                           | O(N)<br/>N为集合的基数           |
| SRANDMEMBER | SRANDMEMBER key [count]  | 随机返回一个元素<br/>若有count且大于0，则返回count个互不重复的元素<br/>若count小于0，则返回-count个可能重复的元素 | O(count)<br/>当没有count时为O(1) |
| SPOP        | SPOP key                 | 随机返回并移除一个元素                                       | O(1)                             |
| SMOVE       | SMOVE src dest item      | 如果src中有item，将item从src移到dest                         | O(1)                             |

### 集合间运算操作

集合同样支持数学概念里的集合的运算操作：

| 命令        | 用例                          | 描述                           | 时间复杂度                                       |
| ----------- | ----------------------------- | ------------------------------ | ------------------------------------------------ |
| SDIFF       | SDIFF key [key ...]           | 返回第一个集合减其他集合的差集 | O(N)<br/>N为所有集合的元素个数之和               |
| SDIFFSTORE  | SDIFFSTORE dst key [key ...]  | SDIFF的存储版本，结果存到dst   | O(N)<br/>N为所有集合的元素个数之和               |
| SINTER      | SINTER key [key ...]          | 返回集合的交集                 | O(N*M)<br/>N为最小的集合的基数<br/>M为集合的个数 |
| SINTERSTORE | SINTERSTORE dst key [key ...] | SINTER的存储版本，结果存到dst  | O(NM)<br/>N为最小的集合的基数<br/>M为集合的个数  |
| SUNION      | SUNION key [key ...]          | 返回集合的并集                 | O(N)<br/>N为所有集合的元素个数之和               |
| SUNIONSTORE | SUNIONSTORE dst key [key ...] | SUNION的存储版本，结果存到dst  | O(N)<br/>N为所有集合的元素个数之和               |

## 散列

散列相当于集合中每个value都变成一个key-value（也就是Redis的字符串结构）

故其具备像字符串一样的处理方式：

+ HSET
+ HGET
+ HSETNX
+ HDEL
+ HLEN
+ HSTRLEN
+ HINCRBY
+ HINCRBYFLOAT
+ HMSET
+ HMGET

其去掉H字母和第一个表示散列key的参数之外就跟字符串的命令没有区别了，故不再赘述

## 有序集合

有序集合相当于集合中每个value变成一个key-value，

其实更准确的说是key-score，其值必须是一个浮点数。

有序集合内的key按score升序排序，当score一样时按key字典序升序排序

### 常用操作

| 命令    | 用例                                       | 描述                                                         | 时间复杂度                                             |
| ------- | ------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------ |
| ZADD    | ZADD key score member [[score member] ...] | 添加元素                                                     | O(M*log(N))<br/>M为添加的元素个数<br/>N为集合的基数    |
| ZREM    | ZREM key member [member ...]               | 移除元素                                                     | O(Mlog(N))<br/>M为成功移除的元素个数<br/>N为集合的基数 |
| ZCARD   | ZCARD key                                  | 返回集合的基数                                               | O(1)                                                   |
| ZINCRBY | ZINCRBY key inc member                     | 给member的score加上inc                                       | O(log(N))                                              |
| ZCOUNT  | ZCOUNT key min max                         | 返回score在[min, max]的成员数量                              | O(log(N))                                              |
| ZRANK   | ZRANK key member                           | 返回member的排名<br/>排名以0为底                             | O(log(N))                                              |
| ZSCORE  | ZSCORE key member                          | 返回member的分值                                             | O(1)                                                   |
| ZRANGE  | ZRANGE key start stop [WITHSCORE]          | 返回分值排名在[start, stop]内的成员的member<br/>带WITHSCORE选项可以连带返回score | O(log(N)+M)<br/>N为集合的基数<br/>M为结果的数量        |

### 批量操作

| 命令             | 用例                                                         | 描述                                                         | 时间复杂度                                                   |
| ---------------- | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| ZREVRANK         | ZREVRANK key member                                          | ZRANK的逆序版                                                | O(log(N))                                                    |
| ZREVRANGE        | ZREVRANGE key start stop [WITHSCORE]                         | ZRANGE的逆序版                                               | O(log(N)+M)<br/>N为集合的基数<br/>M为结果的数量              |
| ZRANGEBYSCORE    | ZRANGEBYSCORE key min max [WITHSCORE] [LIMIT offset count]   | 返回分值在[min, max]之间的member<br/>带WITHSCORE选项可以连带返回score<br/>带LIMIT选项可以做出像SQL里面的limit操作 | O(log(N)+M)<br/>N为集合的基数<br/>M为结果的数量<br/>如果带LIMIT的话还要加上offset的复杂度 |
| ZREVRANGEBYSCORE | ZREVRANGEBYSCORE key min max [WITHSCORE] [LIMIT offset count] | ZRANGEBYSCORE的逆序版                                        | O(log(N)+M)<br/>N为集合的基数<br/>M为结果的数量<br/>如果带LIMIT的话还要加上offset的复杂度 |
| ZREMRANGEBYRANK  | ZREMRANGEBYRANK key start stop                               | 将所有排名在[start, stop]的元素删掉                          | O(log(N)+M)<br/>N为集合的基数<br/>M为结果的数量              |
| ZREMRANGEBYSCORE | ZREMRANGEBYSCORE key min max                                 | 将所有分值在[min, max]的元素删掉                             | O(log(N)+M)<br/>N为集合的基数<br/>M为结果的数量              |
| ZINTERSTORE      | ZINTERSTORE dst keynum key [key ...] [WEIGHT weight [weight ...]] [AGGREGATE SUM\|MIN\|MAX] | 计算多个集合的交集，结果存储到dst<br/>AGGREGATE选项可以指定其分值的计算方式，默认是SUM<br/>WEIGHT可以指定每个集合的权重，相当于在计算之前将分值乘上一个数 | O(NK)+O(Mlog(M))<br/>N为给定集合的最小基数<br/>K为集合个数<br/>M为结果集合的基数 |
| ZUNIONSTORE      | ZUNIONSTORE dst keynum key [key ...] [WEIGHT weight [weight ...]] [AGGEREGATE SUM\|MIN\|MAX] | 计算多个集合的并集，结果存储到dst<br/>AGGREGATE选项可以指定其分值的计算方式，默认是SUM<br/>WEIGHT可以指定每个集合的权重，相当于在计算之前将分值乘上一个数 | O(NK)+O(Mlog(M))<br/>N为给定集合的最小基数<br/>K为集合个数<br/>M为结果集合的基数 |

## 发布与订阅

Redis可以实现发布订阅模式：

| 命令         | 用例                               | 描述                           | 时间复杂度                                                 |
| ------------ | ---------------------------------- | ------------------------------ | ---------------------------------------------------------- |
| SUBSCRIBE    | SUBSCRIBE channel [channel ...]    | 订阅频道                       | O(N)<br/>N为频道数量                                       |
| UNSUBSCRIBE  | UNSUBSCRIBE channel [channel ...]  | 取消订阅频道                   | O(N)<br/>N为频道数量                                       |
| PUBLISH      | PUBLISH channel message            | 将消息发送给频道               | O(N+M)<br/>N为订阅该频道的数量<br/>M为使用模式订阅的用户数 |
| PSUBSCRIBE   | PSUBSCRIBE pattern [pattern ...]   | 模式订阅，订阅符合模式的频道。 | O(N)<br/>N为模式数量                                       |
| PUNSUBSCRIBE | PUNSUBSCRIBE pattern [pattern ...] | 取消订阅符合模式的频道。       | O(N)<br/>N为模式数量                                       |

不过很少会用到Redis的发布订阅功能来传输消息，原因为：

+ Redis并不能保证系统的稳定性，当接收方消费消息的速度小于发送方发送消息的速度，则会造成消息积压最终挤爆内存导致程序崩溃。
+ Redis无法保证消息传输的可靠性，当遇到断线等阻断消息传输的情况时Redis的发布订阅并不会进行消息重传

## 其他命令

### 排序

SORT命令可以实现数据排序输出。

其参数较多，这里不进行赘述，需要的时候查使用手册即可。

### Redis事务

Redis可以实现简单的事务模式：

| 命令  | 用例                | 描述                                                         | 时间复杂度           |
| ----- | ------------------- | ------------------------------------------------------------ | -------------------- |
| MULTI | MULTI               | 标记一个事务块的开始<br/>接下去的命令除非遇到EXEC，否则全部挂起 | O(1)                 |
| EXEC  | EXEC                | 执行事务块内所有指令<br/>当事务块中有命令的键被WATCH，<br/>且这个键在WATCH之后被改动的话，<br/>事务就会被打断，返回nil。 | 事务的时间复杂度总和 |
| WATCH | WATCH key [key ...] | 监视key，当事务开始执行时会先检查监视的key是否被修改。       | O(1)                 |

### 过期时间

Redis可以通过另外的命令给键增加过期时间：

| 命令      | 用例                       | 描述                            | 时间复杂度 |
| --------- | -------------------------- | ------------------------------- | ---------- |
| PERSIST   | PERSIST key                | 移除key的过期时间               | O(1)       |
| TTL       | TTL key                    | 查看key的剩余过期时间，单位为秒 | O(1)       |
| EXPIRE    | EXPIRE key sec             | 设置key的过期时间为sec秒        | O(1)       |
| EXPIREAT  | EXPIRE key timestamp       | 设置key在timestamp时间戳后过期  | O(1)       |
| TTL       | PTTL key                   | TTL的毫秒版本                   | O(1)       |
| PEXPIRE   | PEXPIRE key millisec       | EXPIRE的毫秒版本                | O(1)       |
| PEXPIREAT | PEXPIRE key millitimestamp | EXIPREAT的毫秒版本              | O(1)       |

