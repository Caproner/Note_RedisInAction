# 第3章练习题

### 练习：通过列表来降低内存占用

原先的`update_token`使用了有序集合来保证其可以存储用户最近浏览的25件商品。

但是其需要多余的空间存储时间戳，并按时间戳进行排序。

事实上只需要维护一个最大长度为25的队列就可以了：

```python
def update_token(conn, token, user, item=None):
  timestamp = time.time()
  conn.hset('login:', token, user)
  conn.zadd('recent:', token, timestamp)
  if item:
    conn.lpush('viewed:' + token, item)
    conn.ltrim('viewed:' + token, 0, 24)
```

### 练习：移除竞争条件

可能会造成内存泄漏的地方是存储投票记录的集合`voted:${article_id}`。

这个集合在创建的时候被设置了过期时间，而投票的过程是先判断是否超出时间，然后再对这个集合进行`SADD`。

那么就存在一种情况：在判断是否超时之后和`SADD`之前，这个集合因为到期而被删除，这个时候`SADD`就会因为集合不存在而产生一个新的集合，并且这个集合在这之后就不会用到，更没有程序会去销毁它，这就造成了内存泄漏。

一个解决方法就是在检查过期时间之前WATCH这个集合，并将投票的改动归入事务。如果在检查过期时间之后和`SADD`之前这个集合被删除，那么WATCH会观测到这个变动，使得事务被打断，进而防止`SADD`的不正确执行。

```python
def article_vote(conn, user, article):
  cutoff = time.time() - ONE_WEEK_IN_SECONDS
  article_id = article.partition(':')[-1]
  voted = 'voted:' + article_id
  
  pipeline = conn.pipeline()
  pipeline.watch(voted)
  if conn.zscore('time:', article) < cutoff:
    pipeline.unwatch()
    return
  
  if conn.exists(voted) == 1:
    pipeline.multi()
    pipeline.sadd(voted, user)
    pipeline.zincrby('score:', article, VOTE_SCORE)
    pipeline.hincrby(article, 'votes', 1)
    pipeline.execute()
    
  pipeline.unwatch()
```

### 练习：提高性能

只需要将所有没有前后关系的查询聚集起来一次发送即可。

`get_articles()`一共26次查询，其中第一次查询决定余下25次查询的参数，剩下的25次查询相互独立，故只需要将这25次查询聚合起来即可。

```python
def get_articles(conn, page, order='score:'):
  start = (page-1) * ARTICLES_PER_PAGE
  end = start + ARTICLES_PER_PAGE - 1
  
  ids = conn.zrevrange(order, start, end)
  pipeline = conn.pipeline()
  for id in ids:
    pipeline.hgetall(id)
  articles_datas = pipeline.execute()
  
  articles = []
  for i in range(ids):
    articles_data = articles_datas[i]
    articles_data['id'] = ids[i]
    articles.append(article_data)
    
  return articles
```

### 练习：使用EXPIRE命令代替时间戳有序集合

`update_token()`使用了一个有序集合记录了其最近登录时间，用于清理会话，如果改为设置过期时间的话就可以直接设置token的有效期，而不多使用一个有序集合：

```python
def update_token(conn, token, user, item=None):
  conn.set('login:' + token, user)
  conn.expire('login:' + token, EXPIRE_SEC)
  if item:
    conn.lpush('viewed:' + token, item)
    conn.ltrim('viewed:' + token, 0, 24)
```

同样的，`add_to_cart`也只需要加个过期时间即可：

```python
def add_to_cart(conn, session, item, count):
  if count <= 0:
    conn.hrem('cart:' + session, item)
  else:
    conn.hset('cart:' + session, item, count)
  conn.expire('cart:' + session, EXPIRE_SEC)
```

