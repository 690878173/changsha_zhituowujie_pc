"""分析产品详情页的HTML结构 - 描述、功效、成分"""
import sys, json, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Tool
from lxml import etree

url = "https://lumedeodorant.com/products/vanilla-bliss-solid-stick-deodorant"
print(f"正在抓取: {url}")
res = Tool.get(url)
Tool.HTML.save(res.text, "pdp_analysis.html")
print("已保存到 pdp_analysis.html")

html = etree.HTML(res.text)

# 1. 找描述区域 - accordion 中的内容
print("\n" + "="*60)
print("=== ACCORDION 区块 ===")
accordions = html.xpath('//div[contains(@class,"accordion")]')
for i, acc in enumerate(accordions):
    cls = acc.get('class', '')
    # 找标题
    titles = acc.xpath('.//h3//text() | .//button//text()')
    title = ' '.join(t.strip() for t in titles if t.strip())
    print(f"\n[{i}] class={cls[:80]}")
    print(f"    标题: {title[:100]}")
    # 打印内部HTML前500字
    inner = etree.tostring(acc, encoding='unicode')[:600]
    print(f"    HTML片段: {inner[:500]}...")

# 2. 找包含 "ingredient" / "benefit" / "功效" / "成分" 的区域
print("\n" + "="*60)
print("=== 功效/成分 相关区块 ===")
for node in html.xpath('//*[contains(text(),"Ingredient") or contains(text(),"ingredient") or contains(text(),"Benefit") or contains(text(),"What")]'):
    tag = node.tag
    text = ''.join(node.xpath('.//text()')).strip()[:120]
    parent_tag = node.getparent().tag if node.getparent() is not None else 'none'
    parent_cls = node.getparent().get('class', '')[:60] if node.getparent() is not None else ''
    print(f"  <{tag}> [{parent_tag}.{parent_cls}] {text}")

# 3. 找 "benefits-bar" / "features" 等区块
print("\n" + "="*60)
print("=== 功效 FEATURES/BENEFITS 区块 ===")
for container in html.xpath('//div[contains(@class,"benefit") or contains(@class,"feature") or contains(@class,"icon-")]'):
    if container.xpath('.//img'):
        imgs = container.xpath('.//img/@alt')
        texts = container.xpath('.//p//text() | .//span//text()')
        print(f"  class={container.get('class','')[:80]}")
        print(f"    alts: {[a.strip() for a in imgs if a.strip()][:5]}")
        print(f"    texts: {[t.strip() for t in texts if t.strip()][:5]}")
        print()

print("\n完成!")
