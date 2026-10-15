---
name: feisou-search
description: Search Feishu (飞书) public cloud documents for knowledge, tutorials, and resources. Use when the user needs to search for Chinese-language knowledge articles, tutorials, guides, or technical documentation hosted on Feishu cloud documents. Triggers on "飞搜", "飞书搜索", "搜索飞书", "feisou", "feishu search", "search feishu docs", "飞书文档", or when the user wants to find Chinese knowledge content.
version: 1.0.0
author: FeiSou
url: https://feisou.app
---

# 飞搜 Skill

Search public Feishu cloud documents for high-quality Chinese knowledge articles, tutorials, and resources.

## When to Use

- User asks to search for Chinese-language knowledge, tutorials, or guides
- User mentions "飞搜", "飞书搜索", "搜索飞书文档"
- User needs to find articles, resources, or documentation hosted on Feishu
- User wants curated knowledge from Feishu knowledge bases

## Setup

1. Go to [feisou.app/dashboard](https://feisou.app/dashboard)
2. Sign up / log in (email, Google, or Feishu account)
3. Create an API Key
4. Copy the key (starts with `fs_`)

Set the environment variable:

```bash
export FEISOU_API_KEY="fs_your_key_here"
```

Or add to your `.env` file:

```
FEISOU_API_KEY=fs_your_key_here
```

## Usage

### Search

```bash
curl -G "https://feisou.app/api/skill/search" \
  --data-urlencode "key=$FEISOU_API_KEY" \
  --data-urlencode "q=搜索关键词" \
  --data-urlencode "limit=20"
```

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `key`     | Yes      | API key (`fs_...`) |
| `q`       | Yes      | Search query (Chinese or English) |
| `limit`   | No       | Max results (default 20, max 50) |

### Response

```json
{
  "query": "小红书运营",
  "total": 15,
  "results": [
    {
      "title": "小红书运营全攻略",
      "url": "https://xxx.feishu.cn/docx/...",
      "snippet": "本文从小红书平台规则、内容创作、流量获取...",
      "kb_name": "新媒体运营手册",
      "relevance_score": 0.95,
      "ai_summary": ""
    }
  ],
  "keywords": ["小红书", "运营", "内容创作"],
  "elapsed": 3.2,
  "usage": { "used": 3, "limit": 6 }
}
```

### Check Usage

```bash
curl -G "https://feisou.app/api/skill/usage" \
  --data-urlencode "key=$FEISOU_API_KEY"
```

Response:

```json
{ "usage": 3, "limit": 6, "active": true }
```

## Rate Limits

- **Free tier**: 6 searches per API key per day
- Resets daily at midnight UTC
- For higher limits, contact hi@feisou.app

## Error Codes

| Code | Meaning |
|------|---------|
| 401  | Invalid or inactive API key |
| 429  | Daily limit exceeded (response body includes usage info) |
| 500  | Server error |

## Tips for AI Agents

- Queries in **Chinese** yield the best results (most Feishu docs are in Chinese)
- The `kb_name` field shows which knowledge base the document belongs to — useful for context
- `relevance_score` ranges from 0 to 1; filter by threshold if needed
- Combine multiple queries for comprehensive coverage
- Results include `url` for direct linking to the source document

## Example Agent Workflow

```
User: "帮我找一些关于 Python 爬虫的飞书教程"
Agent:
  1. Call: GET /api/skill/search?key=fs_xxx&q=Python爬虫教程
  2. Parse results, present top matches with titles and links
  3. Summarize key findings from snippets
```
