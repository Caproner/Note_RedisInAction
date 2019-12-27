import sys
import redis
import time

REDIS_KEY_PREFIX = "chapter1_training1:"
ONE_WEEK_IN_SECONDS = 60 * 60 * 24 * 7
VOTE_SCORE = 432
ARTICLE_PER_PAGE = 25


# 输出使用说明
def printUsage():
    print("Usage: python3 ArticleVoter.py [method] [opts..]")
    print("-----------------------------------------")
    print("Current method(s) supported:")
    print("\t vote:\t给文章投赞成票")
    print("\t\tUsage: python3 ArticleVoter.py vote [读者名字] [文章ID]")
    print("\t nega_vote:\t给文章投反对票")
    print("\t\tUsage: python3 ArticleVoter.py nega_vote [读者名字] [文章ID]")
    print("\t reverse:\t反转文章的投票")
    print("\t\tUsage: python3 ArticleVoter.py reverse [文章ID]")
    print("\t post:\t发表文章")
    print("\t\tUsage: python3 ArticleVoter.py post [作者名字] [文章标题] [文章链接]")
    print("\t get:\t获取文章排名")
    print("\t\tUsage: python3 ArticleVoter.py get [页码] [排名方式，可不填或填写'time'或'score'，默认为'score']")
    print("")


# 返回某个组别下的文章排名，按order降序排序
def get_group_articles(group, page, order = "score"):
    r = redis.Redis()
    key = REDIS_KEY_PREFIX + order + ":" + group + ":"
    if not r.exists(key):
        r.zinterstore(key,
            [REDIS_KEY_PREFIX + "group:" + group, REDIS_KEY_PREFIX + order + ":"],
            aggregate='max',
        )
        r.expire(key, 60)
    return get_articles(page, order + ":" + group)


# 给一篇文章添加/移除若干个分组
def add_remove_groups(articleID, toAdd = [], toRemove = []):
    r = redis.Redis()
    article = "article:" + articleID
    for group in toAdd:
        r.sadd(REDIS_KEY_PREFIX + "group:" + group, article)
    for group in toRemove:
        r.srem(REDIS_KEY_PREFIX + "group:" + group, article)


# 返回文章排名，按order降序排序
def get_articles(page, order = "score"):
    r = redis.Redis()
    order += ":"
    start = (page - 1) * ARTICLE_PER_PAGE
    end = page * ARTICLE_PER_PAGE - 1

    ids = r.zrevrange(REDIS_KEY_PREFIX + order, start, end)
    articles = []
    for articleID in ids:
        article_data =  r.hgetall(REDIS_KEY_PREFIX + str(articleID, encoding="utf-8"))
        article_data[bytes('id', encoding="utf-8")] = articleID
        articles.append(article_data)
    
    return articles


# 反转文章的投票
def reverse_article_vote(articleID):
    r = redis.Redis()
    articleTime = r.zscore(REDIS_KEY_PREFIX + "time:", "article:" + articleID)
    if articleTime == None:
        print("Error: 文章不存在")
        return False
    articleScore = r.zscore(REDIS_KEY_PREFIX + "score:", "article:" + articleID)
    articleScore = articleTime - (articleScore - articleTime)
    r.zadd(REDIS_KEY_PREFIX + "score:", {"article:" + articleID: articleScore})
    vote = r.hget(REDIS_KEY_PREFIX + "article:" + articleID, 'votes')
    r.hset(REDIS_KEY_PREFIX + "article:" + articleID, 'votes', str(-1 * int(vote)))
    return True


# 给文章投反对票
def article_nega_vote(user, articleID):
    r = redis.Redis()
    articleTime = r.zscore(REDIS_KEY_PREFIX + "time:", "article:" + articleID)
    if articleTime == None:
        print("Error: 文章不存在")
        return False

    cutoff = time.time() - ONE_WEEK_IN_SECONDS
    if articleTime < cutoff:
        print("Error: 文章已过期，不能再投票给该文章")
        return False
    
    if r.sadd(REDIS_KEY_PREFIX + "voted:" + articleID, user):
        r.zincrby(REDIS_KEY_PREFIX + "score:", -1 * VOTE_SCORE, "article:" + articleID)
        r.hincrby(REDIS_KEY_PREFIX + "article:" + articleID, 'votes', -1)
    else:
        print("Error: 同一个用户不能多次投票给同一篇文章")
        return False
    return True


# 给文章投赞成票
def article_vote(user, articleID):
    r = redis.Redis()
    articleTime = r.zscore(REDIS_KEY_PREFIX + "time:", "article:" + articleID)
    if articleTime == None:
        print("Error: 文章不存在")
        return False

    cutoff = time.time() - ONE_WEEK_IN_SECONDS
    if articleTime < cutoff:
        print("Error: 文章已过期，不能再投票给该文章")
        return False
    
    if r.sadd(REDIS_KEY_PREFIX + "voted:" + articleID, user):
        r.zincrby(REDIS_KEY_PREFIX + "score:", VOTE_SCORE, "article:" + articleID)
        r.hincrby(REDIS_KEY_PREFIX + "article:" + articleID, 'votes')
    else:
        print("Error: 同一个用户不能多次投票给同一篇文章")
        return False
    return True


# 发布文章
def post_article(user, title, link):
    r = redis.Redis()
    articleID = str(r.incr(REDIS_KEY_PREFIX + "article:"))

    voted = REDIS_KEY_PREFIX + "voted:" + articleID
    r.sadd(voted, user)
    r.expire(voted, ONE_WEEK_IN_SECONDS)

    now = time.time()
    article = REDIS_KEY_PREFIX + "article:" + articleID
    r.hmset(article, {
        "title": title,
        "link": link,
        "poster": user,
        "time": now,
        "votes": 1,
    })

    r.zadd(REDIS_KEY_PREFIX + "score:", {"article:" + articleID: now + VOTE_SCORE})
    r.zadd(REDIS_KEY_PREFIX + "time:", {"article:" + articleID: now})

    return articleID


def main():

    # 给文章投赞成票
    if (len(sys.argv) == 4 and sys.argv[1] == "vote"):
        user = sys.argv[2]
        articleID = sys.argv[3]
        if article_vote(user, articleID):
            print("投票成功！")
    # 给文章投反对票
    elif (len(sys.argv) == 4 and sys.argv[1] == "nega_vote"):
        user = sys.argv[2]
        articleID = sys.argv[3]
        if article_nega_vote(user, articleID):
            print("投票成功！")
    # 发布文章
    elif (len(sys.argv) == 5 and sys.argv[1] == 'post'):
        user = sys.argv[2]
        title = sys.argv[3]
        link = sys.argv[4]
        articleID = post_article(user, title, link)
        print("文章ID: " + articleID)
    # 返回文章排名
    elif (len(sys.argv) > 2 and len(sys.argv) < 5 and sys.argv[1] == 'get'):
        page = int(sys.argv[2])
        if len(sys.argv) == 4:
            articles = get_articles(page, sys.argv[3])
        else:
            articles = get_articles(page)
        print(articles)
    # 反转文章的投票
    elif (len(sys.argv) == 3 and sys.argv[1] == "reverse"):
        articleID = sys.argv[2]
        if reverse_article_vote(articleID):
            print("反转投票成功！")
    else:
        printUsage()


if __name__ == '__main__':
    main()