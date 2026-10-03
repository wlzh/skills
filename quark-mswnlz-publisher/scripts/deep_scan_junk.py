"""递归扫描批次文件夹（最多4层），找出并删除所有'更多资源收藏不迷路'"""
import asyncio, json, sys
sys.path.insert(0, "/Users/m/document/QNSZ/project/QuarkPanTool")
from quark import QuarkPanFileManager

async def deep_scan(mgr, fid, path="", depth=0, hits=None):
    if hits is None: hits = []
    try:
        children = await mgr.get_file_list(fid)
    except Exception as e:
        return hits
    for c in children:
        name = c.get("file_name", "")
        is_dir = c.get("dir", False)
        cfid = c.get("fid", "")
        full = f"{path}/{name}"
        if "更多资源收藏不迷路" in name:
            hits.append({"path": full, "fid": cfid, "is_dir": is_dir, "parent_fid": fid})
        if is_dir and depth < 4:
            await deep_scan(mgr, cfid, full, depth + 1, hits)
    return hits

async def main():
    batch = json.load(open("/Users/m/document/QNSZ/project/skills/quark-mswnlz-publisher/scripts/batch_share_results.json"))
    batch_fid = batch["batch_folder_fid"]
    mgr = QuarkPanFileManager()
    
    print(f"批次: {batch.get('batch_folder_name', '?')}")
    print(f"FID: {batch_fid}")
    print("递归扫描中（4层深度）...\n")
    
    hits = await deep_scan(mgr, batch_fid)
    
    if not hits:
        print("✅ 未发现'更多资源收藏不迷路'")
        return
    
    print(f"🎯 找到 {len(hits)} 个:\n")
    for h in hits:
        t = "📁" if h["is_dir"] else "📄"
        print(f"  {t} {h['path']}")
    
    print(f"\n开始删除...\n")
    ok = 0
    for h in hits:
        try:
            await mgr.delete_files([h["fid"]], pdir_fid=h["parent_fid"])
            print(f"  ✅ {h['path']}")
            ok += 1
        except Exception as e:
            print(f"  ❌ {h['path']} → {e}")
    
    print(f"\n完成: {ok}/{len(hits)}")

asyncio.run(main())
