---
name: feisou-search
description: 搜索飞书（Feishu/Lark）公开云文档与知识库，免 token、免登录、免浏览器，直接走飞搜 feisou.app 的匿名 SSE 接口；输出标题+链接+知识库+摘要。当用户要求"搜飞书文档 / 飞搜 / 找飞书教程 / 溯源某篇飞书 wiki / search feishu docs"时使用。也可选用官方 API Key 模式（6 次/账户/天）。
---

# 飞搜（feisou.app）飞书文档搜索 Skill

覆盖 Google/Bing **搜不到**的租户知识库（`<租户>.feishu.cn/wiki/...`）：飞搜有自建索引 + 网页结果（`site:feishu.cn`）二次语义过滤。

## 1. 推荐用法：免 token（默认）

```bash
# 仓库内直接跑；装成 skill 后路径为 ~/.claude/skills/feisou-search/scripts/feisou_search.py
python3 scripts/feisou_search.py "GEO获客"
python3 scripts/feisou_search.py "GEO获客" --limit 20
python3 scripts/feisou_search.py "词A" "词B" --json   # 多词批量
python3 scripts/feisou_search.py "词" --markdown      # 服务端 Markdown
```

原理：网页端搜索走 `GET https://feisou.app/api/search?q=<urlencode 词>`（SSE，`text/event-stream`）。
前端 `app.js`：**有 supabase session 就带 `user_token`，没有就照样发** → 所以匿名可直接调用，无需 Key/登录/Cookie。
事件流：`progress`（进度）→ `queries`（AI 改写出的 3 条检索词）→ `result`（`groups` 按知识库聚合 / `flat_docs` 扁平列表 / `markdown` 成品 / `total_elapsed`）。

- 单次约 **5~20 秒**，命中 30~60 篇，覆盖 10~25 个知识库。
- 每次调用会消耗一次**服务端搜索**；匿名无限流头、无 cookie、响应无 quota 字段，额度对匿名用户在服务端按 IP 隐式计算，**不可见**。别拿它当无限爬虫，批量场景请合并关键词。

## 2. 可选：官方 API Key 模式（额度可见）

```bash
FEISOU_API_KEY=fs_xxx python3 scripts/feisou_search.py "关键词"
# 或 --key fs_xxx
```
`GET /api/skill/search?key=fs_xxx&q=词&limit=20`；免费 **6 次/账户/天（所有 Key 合计），0 点重置**（官方文档写 UTC 零点）；超限 429，Key 无效 401，缺 Key 422。Key 在 `https://feisou.app/dashboard` 登录后创建。官方原文见 `references/official-feisou-search.md`。

## 3. 已知坑（实测）

1. **不支持严格精确句**：即使你加引号，服务端也会先用 AI 改写检索词（如 `intitle:词 site:feishu.cn`、`"词" site:feishu.cn`、英文译词），再语义过滤/重排 → 整句溯源会返回大量语义噪声。**用短主题词 + 特征词**，效果最好。
2. 只搜**公开分享**的文档；作者取消公开/改权限后链接打不开（飞搜也无法授权），**不搜企业私有空间**。
3. `/search/<关键词>` 网页地址是 SSR SEO 落地页（无 JS、不计额度），**不等于真搜索**；真搜索只在上面的 SSE 接口。
4. 返回链接多为 `docs.feishu.cn/v/wiki/...` 或 `<租户>.feishu.cn/wiki/...`，**未登录时可能要求权限**，属正常。
5. Python 环境：有 `requests` 就用，没有自动回退 `urllib`；兼容 3.9+。注意**不要在函数内 `import urllib.request`**（会把 `urllib` 变成局部变量，遮蔽模块级 `urllib.parse` → 函数开头的 `urlencode/quote` 抛 UnboundLocalError）。

## 4. 相关

- 搜索侧补充：Google/Bing 基本不收录 `<租户>.feishu.cn/docx|doc|base`（`site:feishu.cn/docx` 实测 0 条），可用 `site:feishu.cn` / `site:feishu.cn/wiki` 兜底；客户端内检索语法见飞书官方《高级搜索语法》。
- 两个同名站点别混：`feisou.app`（本 skill，覆盖租户 wiki）vs `feisous.com`（偏 Google 结果壳，`/search?q=`）。
