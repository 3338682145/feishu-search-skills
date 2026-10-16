---
name: feisou-search
description: 搜索飞书（Feishu/Lark）公开云文档与知识库，零配置开箱即用：直接调用 feisou.app 的公开 SSE 搜索接口，无需注册、无需登录、无需任何密钥、无需浏览器，输出标题+链接+所属知识库+摘要。当用户要求"搜飞书文档 / 飞搜 / 找飞书教程 / 溯源某篇飞书 wiki / search feishu docs"时使用。
---

# 飞搜（feisou.app）飞书文档搜索 Skill

覆盖 Google/Bing **搜不到**的租户知识库（`<租户>.feishu.cn/wiki/...`）：飞搜有自建的公开文档索引 + 网页结果（`site:feishu.cn`）二次语义过滤。

## 1. 用法（开箱即用，无任何前置配置）

```bash
# 仓库内直接跑；装成 skill 后路径为 ~/.claude/skills/feisou-search/scripts/feisou_search.py
python3 scripts/feisou_search.py "GEO获客"
python3 scripts/feisou_search.py "GEO获客" --limit 20
python3 scripts/feisou_search.py "词A" "词B" --json       # 多词批量，原始 JSON
python3 scripts/feisou_search.py "词" --markdown          # 服务端 Markdown
python3 scripts/feisou_search.py "词" --timeout 60 --quiet
```

- **不需要任何账号、密钥、Cookie、浏览器，也不依赖任何环境变量。**
- 输出：AI 改写的 3 条检索词 → 命中篇数 / 知识库数 / 耗时 → `标题 + 链接 + 所属知识库 + 摘要`。
- 多个关键词 = 多次独立搜索（顺序执行）。

## 2. 工作原理

`GET https://feisou.app/api/search?q=<urlencode 词>`（SSE，`text/event-stream`）——飞搜网页端搜索用的就是这个公开接口，未登录访问时前端照常发起请求，服务端不做身份校验。

事件流：`progress`（进度）→ `queries`（AI 改写的检索词）→ `result`（`groups` 按知识库聚合 / `flat_docs` 扁平列表 / `markdown` 成品 / `total_elapsed`）。

- 单次约 3~20 秒，命中 30~60 篇，覆盖 10~27 个知识库。
- 请勿当日志级爬虫用：批量场景请合并关键词、配 `--limit`、必要时放慢节奏；上游对高频匿名访问可能限流。

## 3. 注意事项

1. **它不是精确匹配引擎**：长句会被 AI 改写（如 `词 → "词" site:feishu.cn`、`intitle:词 site:feishu.cn`、甚至英文译词），再做语义过滤，因此**引号精确短语不保证严格命中**；溯源建议用"短主题词 + 特征词"。
2. 返回的多为 `<租户>.feishu.cn/wiki/...`，未登录打开时可能提示申请权限，属正常现象。
3. Python 3.9+ 可跑；有 `requests` 就用，没有自动回退 `urllib`。**不要在函数内 `import urllib.request`**（会把 `urllib` 变成局部变量，遮蔽模块级 `urllib.parse` → 函数开头的 urlencode 抛 `UnboundLocalError`）。
4. `/search/<关键词>` 这类网页地址是 SSR 落地页，**不等于真实搜索**；真实搜索就是上面的 SSE 接口。

## 4. 相关

- Google/Bing 基本不收录 `<租户>.feishu.cn/docx|doc|base`（`site:feishu.cn/docx` 实测 0 条），可用 `site:feishu.cn` / `site:feishu.cn/wiki` 兜底；客户端内检索语法见飞书官方《高级搜索语法》。
- 两个同名站点别混：`feisou.app`（本 skill，覆盖租户 wiki）vs `feisous.com`（偏 Google 结果壳，`/search?q=`）。
