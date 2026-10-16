#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
feisou_search.py — 搜索飞书公开云文档与知识库

原理：网页端搜索走的是 SSE 接口 `GET https://feisou.app/api/search?q=<词>`；
     本脚本按同样方式直接复用该接口。

用法：
    python3 feisou_search.py "GEO获客"
    python3 feisou_search.py "GEO获客" --json            # 原始 JSON
    python3 feisou_search.py "GEO获客" --limit 10        # 每词最多列几条
    python3 feisou_search.py "词A" "词B"                 # 多词批量
    python3 feisou_search.py "词" --timeout 60 --quiet

注意：该接口会先用 AI 把查询改写成约 3 条检索词（含 `"词" site:feishu.cn`、`intitle:词 site:feishu.cn`），
     再做语义过滤，所以**引号精确短语并不保证严格命中**；按主题词搜索效果最好。
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request

ANON_ENDPOINT = "https://feisou.app/api/search"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"


def _requests():
    try:
        import requests  # noqa
        return requests
    except Exception:
        return None


def search_anon(q, timeout=90, verbose=True):
    """走公开的 SSE 搜索接口，返回 {queries, groups, doc_count, elapsed}"""
    req = _requests()
    url = ANON_ENDPOINT + "?q=" + urllib.parse.quote(q)
    headers = {"User-Agent": UA, "Accept": "text/event-stream"}
    state = {"queries": [], "keywords": [], "groups": [], "flat_docs": [], "markdown": "",
             "elapsed": None, "doc_count": None, "answer": ""}

    if req is not None:
        r = req.get(url, headers=headers, stream=True, timeout=timeout)
        r.raise_for_status()
        lines = r.iter_lines(decode_unicode=True)
    else:
        resp = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout)

        def gen():
            for raw in resp:
                yield raw.decode("utf-8", "replace").rstrip("\r\n")
        lines = gen()

    for line in lines:
        if not line or not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if not payload:
            continue
        try:
            ev = json.loads(payload)
        except Exception:
            continue
        t = ev.get("type")
        if t == "progress":
            if verbose:
                sys.stderr.write("  · %s (%ss)\n" % (ev.get("message", ""), ev.get("elapsed")))
                sys.stderr.flush()
        elif t == "queries":
            state["queries"] = ev.get("queries") or state["queries"]
            state["keywords"] = ev.get("keywords") or state["keywords"]
            if verbose and state["queries"]:
                sys.stderr.write("  检索词: %s\n" % "; ".join(state["queries"]))
                sys.stderr.flush()
        elif t in ("result", "complete", "done"):
            if ev.get("groups") is not None:
                state["groups"] = ev.get("groups") or []
            if ev.get("queries"):
                state["queries"] = ev["queries"]
            if ev.get("keywords"):
                state["keywords"] = ev["keywords"]
            if ev.get("flat_docs"):
                state["flat_docs"] = ev["flat_docs"]
            if ev.get("markdown"):
                state["markdown"] = ev["markdown"]
            if ev.get("answer"):
                state["answer"] = ev["answer"]
            if ev.get("total_elapsed") is not None:
                state["elapsed"] = ev["total_elapsed"]
            if ev.get("doc_count") is not None:
                state["doc_count"] = ev["doc_count"]
            if state["flat_docs"]:
                state["doc_count"] = state["doc_count"] or len(state["flat_docs"])
    return state


def _doc(d, space=None):
    return {
        "title": d.get("title"),
        "url": d.get("url"),
        "snippet": (d.get("snippet") or "").replace("\n", " ").strip(),
        "space": d.get("subtitle") or d.get("kb_name") or d.get("space") or space,
    }


def flatten(state):
    if state.get("flat_docs"):          # 服务端已给扁平列表
        return [_doc(d) for d in state["flat_docs"]]
    docs = []
    for g in state.get("groups") or []:
        for d in g.get("docs") or []:
            docs.append(_doc(d, g.get("name")))
    return docs


def print_md(q, state, limit):
    docs = flatten(state)
    print("## %s" % q)
    if state.get("queries"):
        print("> 实际检索词：%s" % " | ".join(state["queries"]))
    n = state.get("doc_count") or state.get("total") or len(docs)
    el = state.get("elapsed")
    print("> 命中约 %s 篇 / 知识库 %d 个 / 耗时 %s\n" % (n, len(state.get("groups") or []), ("%.1fs" % el) if isinstance(el, (int, float)) else "n/a"))
    if not docs:
        print("（无结果）\n")
        return
    for i, d in enumerate(docs[:limit], 1):
        print("%d. [%s](%s)" % (i, d["title"] or "(无标题)", d["url"]))
        meta = " · ".join([x for x in [d["space"], d["snippet"][:120]] if x])
        if meta:
            print("   %s" % meta)
    if len(docs) > limit:
        print("   …（共 %d 篇，用 --limit 调整）" % len(docs))
    print()


def main():
    ap = argparse.ArgumentParser(description="搜索飞书公开云文档与知识库")
    ap.add_argument("queries", nargs="+", help="搜索关键词（中文效果最好）")
    ap.add_argument("--json", action="store_true", help="输出原始 JSON")
    ap.add_argument("--limit", type=int, default=12, help="每词最多打印条数（默认 12）")
    ap.add_argument("--timeout", type=int, default=90)
    ap.add_argument("--quiet", action="store_true", help="不打进度到 stderr")
    ap.add_argument("--markdown", action="store_true", help="直接输出服务端生成的 Markdown 结果")
    args = ap.parse_args()

    all_out = []
    for q in args.queries:
        if not args.quiet:
            sys.stderr.write("[feishu-search] 搜索: %s\n" % q)
        try:
            state = search_anon(q, timeout=args.timeout, verbose=not args.quiet)
        except Exception as e:
            sys.stderr.write("  失败: %r\n" % (e,))
            all_out.append({"query": q, "error": repr(e)})
            continue
        all_out.append({"query": q, "state": state})

    if args.json:
        print(json.dumps(all_out, ensure_ascii=False, indent=2))
    else:
        for item in all_out:
            if "error" in item:
                print("## %s\n> 失败：%s\n" % (item["query"], item["error"]))
            elif args.markdown and item["state"].get("markdown"):
                print(item["state"]["markdown"])
            else:
                print_md(item["query"], item["state"], args.limit)


if __name__ == "__main__":
    main()
