# feishu-search-skills

**免 token 搜索飞书（Feishu / Lark）公开云文档与知识库。**

A Claude/Codex **Skill** that searches public Feishu cloud docs & wiki knowledge bases
via [飞搜 feisou.app](https://feisou.app) — **without any API key, login, cookie or browser**.

为什么需要它：Google / Bing 基本不收录 `<租户>.feishu.cn/wiki/...` 这类租户知识库
（实测 `site:feishu.cn/docx` 收录数为 0），而飞搜有自建的公开云文档索引。本 skill 把
飞搜的检索能力做成一行命令。

---

## 快速开始

```bash
# 1) 装成 Skill（可选，装完 agent 可自动发现）
mkdir -p ~/.claude/skills && cp -r . ~/.claude/skills/feisou-search

# 2) 直接搜（免 token）
python3 scripts/feisou_search.py "GEO获客"
```

```text
## GEO获客
> 飞搜实际检索词：intitle:GEO获客 site:feishu.cn | "GEO获客" site:feishu.cn | GEO customer acquisition site:feishu.cn
> 命中约 53 篇 / 知识库 22 个 / 耗时 8.6s

1. [从小红书到 GEO：生成式搜索时代的“可见度战争”](https://xxx.feishu.cn/wiki/wikcn...)
   某知识库 · 在生成式搜索的时代，信息的“被看见”...
2. ...
```

### 参数

| 参数 | 说明 |
|---|---|
| `queries` (位置参数) | 一个或多个关键词；多个 = 多次独立搜索 |
| `--limit N` | 每个关键词最多打印 N 条（默认 12） |
| `--markdown` | 直接输出服务端生成的成品 Markdown（按知识库分组） |
| `--json` | 输出原始 JSON（`flat_docs` / `groups` / `markdown` / `total_elapsed`） |
| `--quiet` | 不打进度到 stderr |
| `--timeout S` | 单次请求超时（默认 120s） |
| `--key fs_xxx` | 改用**官方** API Key 通道（见下），不传则走免 token 通道 |

```bash
python3 scripts/feisou_search.py "飞书 高级搜索语法" "VK 俄罗斯 电商" --json > out.json
python3 scripts/feisou_search.py "让人搜到你时你是最佳答案" --markdown
```

无第三方依赖（有 `requests` 就用，没有自动回退 `urllib`），
兼容系统自带 Python 3.9+（实测 macOS `/usr/bin/python3` 3.9.6 与 3.11.15）。

---

## 它为什么能免 token

飞搜有**两扇门**，走的是不同的接口：

| | 官方 Skill 接口 | 网页端接口（本工具默认） |
|---|---|---|
| 端点 | `GET /api/skill/search?key=fs_xxx&q=词` | `GET /api/search?q=词`（SSE） |
| Token | **必填且强校验**（无 key→`422`，假 key→`401`） | **不校验**，无 token 也 `200` |
| 额度 | 6 次/天/账户（`/api/skill/usage` 可查） | 无可见额度，服务端按 IP 隐式限流 |
| 返回 | 干净 JSON（`results[] / kb_name / relevance_score / usage`） | SSE 事件流：`progress → queries → result` |

关键在网页端自身逻辑：`static/app.js` 里

```js
let searchUrl = `/api/search?q=${encodeURIComponent(q)}`;
if (session?.access_token) searchUrl += `&user_token=${session.access_token}`;
else console.warn('[feisou] No session found for search, user_token not sent');
```

**有 session 就带上身份，没有就照样发** —— 于是游客通道天然可用。本工具直接复用它。

服务端内部会自己把关键词改写成 3 条检索词
（`intitle:词 site:feishu.cn`、`"词" site:feishu.cn`、英文译词），
合并「网页结果 + 自有知识库索引」后做二次语义过滤 —— 这也是它
**不认引号精确短语**的原因：精确串会被语义改写冲掉，溯源请喂「短主题词 + 特征词」。

---

## 注意事项

- 单次约 **5~20 秒**，命中 30~60 篇、覆盖 10~25 个知识库。
- 匿名通道**没有额度保证、没有 SLA**，官方随时可能加限流/人机校验；
  需要可计量、可自动化时请到 [feisou.app/dashboard](https://feisou.app/dashboard) 注册建 Key，
  然后用 `--key` 走官方 6 次/天通道（`429` = 当日额度用尽）。
- 只搜**公开**云文档，搜不到企业私有空间。
- 结果是公开分享链接，未登录打开租户 wiki 时可能提示无权限，属正常。

## 文件说明

```
SKILL.md                           # Skill 定义（frontmatter + 用法）
scripts/feisou_search.py           # 免 token 搜索脚本（唯一代码文件，纯标准库）
references/official-feisou-search.md  # 官方 feisou-search.md 原文备份（v1.0.0, author: FeiSou）
```

## 参考

- 飞搜：https://feisou.app ｜ 官方 Skill 原文：https://feisou.app/skill/feisou-search.md
- 飞书官方《高级搜索语法》（客户端内检索用法）：https://www.feishu.cn/hc/zh-CN/articles/956339790002

## License

代码部分 MIT（见 `LICENSE`）。`references/official-feisou-search.md` 为飞搜官方发布的
Skill 文档原文，版权归 FeiSou 所有，此处仅为便于对照而收录。

> 本项目与飞搜（feisou.app）无隶属关系；接口为非官方的网页端接口，若上游变更可能失效。
