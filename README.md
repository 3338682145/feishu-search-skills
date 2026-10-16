# feishu-search-skills

**零配置搜索飞书（Feishu / Lark）公开云文档与知识库。**

An Agent Skill + CLI that searches public Feishu cloud docs and wiki knowledge
bases via [飞搜 feisou.app](https://feisou.app) — **无需注册、无需登录、无需任何密钥、无需浏览器**。

为什么需要它：Google / Bing 基本不收录 `<租户>.feishu.cn/wiki/...` 这类租户知识库
（实测 `site:feishu.cn/docx` 收录数为 0），而飞搜有自建的公开云文档索引。本 skill 把
飞搜的检索能力做成一行命令 —— 打开终端就能用，没有任何前置配置。

---

## 快速开始

### 方式 1：直接当命令行用

```bash
git clone https://github.com/3338682145/feishu-search-skills.git
cd feishu-search-skills
python3 scripts/feisou_search.py "GEO获客"
```

### 方式 2：装成 Agent Skill（Claude Code / Codex 等）

```bash
mkdir -p ~/.claude/skills
cp -r . ~/.claude/skills/feisou-search     # SKILL.md 会被 agent 自动读取
```

之后直接对 agent 说「搜飞书文档：xxx」即可。

## 用法

```bash
python3 scripts/feisou_search.py "飞书 高级搜索语法"
python3 scripts/feisou_search.py "词A" "词B" --json        # 多词批量，输出原始 JSON
python3 scripts/feisou_search.py "词" --markdown           # 输出服务端生成的 Markdown
python3 scripts/feisou_search.py "词" --limit 30 --quiet   # 限条数、静默
```

| 参数 | 说明 |
| --- | --- |
| `--limit N` | 每个关键词最多打印条数（默认 12） |
| `--json` | 输出原始 JSON（含 `flat_docs` / `groups` / `markdown` / `total_elapsed`） |
| `--markdown` | 直接输出飞搜服务端生成的 Markdown 结果 |
| `--quiet` | 不打印进度到 stderr |
| `--timeout N` | 单次请求超时秒数（默认 90） |

多个关键词 = 多次独立搜索（顺序执行）。

## 输出示例

```
## 飞书 高级搜索语法
> 飞搜实际检索词：intitle:飞书 高级搜索语法 site:feishu.cn | "飞书 高级搜索语法" site:feishu.cn | Feishu site:feishu.cn
> 命中约 49 篇 / 知识库 20 个 / 耗时 7.1s

1. [玩转高级搜索](https://7337552821032026115.feishu.cn/wiki/FeAFw1KCwiZyxXkdu5lcIAkQnTf)
   工具 & AI 避坑参考库 · Docs 玩转高级搜索 输入"/"快速插入内容 玩…
```

实测：`GEO获客` 53 篇 / 22 个知识库（8.6s）；`VK 俄罗斯 电商` 50 篇 / 27 个知识库（12.4s）。

## 工作原理

脚本调用的是飞搜网页端搜索所用的公开接口：

```
GET https://feisou.app/api/search?q=<urlencode 词>     # SSE, text/event-stream
```

未登录访问时网页前端照常发起该请求，服务端不做身份校验，因此命令行可以直接复用，**无需注册、登录或任何凭据**。

事件流：`progress`（进度）→ `queries`（AI 改写的约 3 条检索词）→ `result`（`groups` 按知识库聚合 / `flat_docs` 扁平列表 / `markdown` 成品 / `total_elapsed`）。

## 边界与注意事项

- **不是精确匹配引擎**：查询会先被 AI 改写（`词 → "词" site:feishu.cn`、`intitle:词 site:feishu.cn`，甚至英文译词），再做语义过滤，所以**引号精确短语不保证严格命中**；溯源请用"短主题词 + 特征词"。
- 结果是公开云文档链接（多为 `<租户>.feishu.cn/wiki/...`），未登录打开时可能提示申请权限，属正常。
- **请勿当日志级爬虫使用**：批量场景请合并关键词、加 `--limit`、必要时放慢节奏 —— 这是第三方公开服务，高频访问可能被限流。
- 非官方接口，上游变更可能导致失效；无 SLA 保证。
- Python 3.9+；有 `requests` 就用，没有自动回退标准库 `urllib`。

## 目录结构

```
SKILL.md                     # Skill 定义（agent 读取的入口）
scripts/feisou_search.py     # 搜索脚本（纯标准库实现，唯一代码文件）
README.md
LICENSE
```

## License

MIT，见 [LICENSE](LICENSE)。

> 本项目与飞搜（feisou.app）无隶属关系，仅调用其公开接口。
