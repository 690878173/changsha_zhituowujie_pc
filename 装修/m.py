import os
import hashlib
from pathlib import Path
from typing import List


def get_file_md5(file_path: str, chunk_size=4096) -> str:
    md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                md5.update(chunk)
        return md5.hexdigest()
    except Exception as e:
        return f"ERROR:{str(e)}"


def scan_folder(root_dir: str) -> dict:
    root = Path(root_dir).resolve()
    file_map = {}
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            full_path = Path(dirpath) / filename
            rel_path = str(full_path.relative_to(root))
            file_map[rel_path] = get_file_md5(str(full_path))
    return file_map


def compare_multi_folders(dir_list: List[str]):
    """
    支持传入2个或3个目录列表自动对比
    """
    dir_count = len(dir_list)
    assert dir_count in (2, 3), "仅支持传入2个或3个目录进行对比"

    # 扫描所有目录
    map_list = [scan_folder(d) for d in dir_list]
    key_sets = [set(m.keys()) for m in map_list]
    all_keys = set().union(*key_sets)

    print("=" * 75)
    for idx, path in enumerate(dir_list, 1):
        print(f"目录{idx}: {path}")
    print("=" * 75)

    if dir_count == 2:
        m1, m2 = map_list
        k1, k2 = key_sets
        only_1 = sorted(k1 - k2)
        only_2 = sorted(k2 - k1)
        common = sorted(k1 & k2)

        diff_content = []
        same_all = []
        for k in common:
            h1 = m1[k]
            h2 = m2[k]
            if h1 != h2:
                diff_content.append((k, h1, h2))
            else:
                same_all.append(k)

        print(f"\n【只存在于目录1】({len(only_1)})")
        for f in only_1:
            print(f"  {f}")

        print(f"\n【只存在于目录2】({len(only_2)})")
        for f in only_2:
            print(f"  {f}")

        print(f"\n【同名但内容不一致】({len(diff_content)})")
        for name, h1, h2 in diff_content:
            print(f"  {name}")
            print(f"    md5_1:{h1}")
            print(f"    md5_2:{h2}")

        print(f"\n【同名且内容完全一致】({len(same_all)})")

        print("\n===== 汇总 =====")
        print(f"仅目录1:{len(only_1)} | 仅目录2:{len(only_2)}")
        print(f"同名不同内容:{len(diff_content)} | 完全相同:{len(same_all)}")

    elif dir_count == 3:
        m1, m2, m3 = map_list
        k1, k2, k3 = key_sets

        only_1 = sorted(k1 - k2 - k3)
        only_2 = sorted(k2 - k1 - k3)
        only_3 = sorted(k3 - k1 - k2)

        exist_12_not3 = sorted((k1 & k2) - k3)
        exist_13_not2 = sorted((k1 & k3) - k2)
        exist_23_not1 = sorted((k2 & k3) - k1)

        all_exist = sorted(k1 & k2 & k3)
        diff_content = []
        same_all = []

        for k in all_exist:
            h1 = m1[k]
            h2 = m2[k]
            h3 = m3[k]
            if h1 == h2 == h3:
                same_all.append(k)
            else:
                diff_content.append((k, h1, h2, h3))

        print(f"\n【只在目录1存在】({len(only_1)})")
        for f in only_1:
            print(f"  {f}")

        print(f"\n【只在目录2存在】({len(only_2)})")
        for f in only_2:
            print(f"  {f}")

        print(f"\n【只在目录3存在】({len(only_3)})")
        for f in only_3:
            print(f"  {f}")

        print(f"\n【目录1、2存在，目录3无】({len(exist_12_not3)})")
        for f in exist_12_not3:
            print(f"  {f}")

        print(f"\n【目录1、3存在，目录2无】({len(exist_13_not2)})")
        for f in exist_13_not2:
            print(f"  {f}")

        print(f"\n【目录2、3存在，目录1无】({len(exist_23_not1)})")
        for f in exist_23_not1:
            print(f"  {f}")

        print(f"\n【三者都存在，但内容不一致】({len(diff_content)})")
        for name, h1, h2, h3 in diff_content:
            print(f"  {name}")
            print(f"    md51:{h1}")
            print(f"    md52:{h2}")
            print(f"    md53:{h3}")

        print(f"\n【三者路径存在且内容完全一致】({len(same_all)})")

        print("\n===== 汇总 =====")
        print(f"仅1:{len(only_1)} | 仅2:{len(only_2)} | 仅3:{len(only_3)}")
        print(f"1&2无3:{len(exist_12_not3)} | 1&3无2:{len(exist_13_not2)} | 2&3无1:{len(exist_23_not1)}")
        print(f"同名内容不同:{len(diff_content)} | 全部相同:{len(same_all)}")


if __name__ == "__main__":
    # =========== 配置区域，二选一 ===========
    # 方式1：对比两个文件夹
    # folders = [
    #     r"./data/原始模板/",
    #     r"./data/导出模板/"
    # ]

    # 方式2：对比三个文件夹
    folders = [
        r"./data/原始模板/",
        r"./data/导入模板2/",
        # r"./data/导入模板1/"
    ]
    # =======================================

    compare_multi_folders(folders)