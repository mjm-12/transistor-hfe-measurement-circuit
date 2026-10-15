
# KiCad PCB テキスト一括更新スクリプト
# =====================================
# スクリプティングコンソールで以下を実行:
# import os, pcbnew; exec(open(os.path.join(os.path.dirname(pcbnew.GetBoard().GetFileName()), "script/batch_update_text.py")).read())         

import pcbnew

board = pcbnew.GetBoard()

# ============================================================
#  設定エリア (ここだけ編集する)
# ============================================================

# --- 新しいフォントサイズ / 線幅 (単位: mm) ---
NEW_WIDTH_MM  = 0.8   # 文字幅
NEW_HEIGHT_MM = 0.8    # 文字高さ
NEW_THICK_MM  = 0.125   # 線幅 (Stroke Width)

# --- 更新するテキスト種別 ---
UPDATE_REFERENCE = True   # Reference (REF**) を対象にするか
UPDATE_VALUE     = True   # Value を対象にするか
UPDATE_USER_TEXT = True    # fp_text user を対象にするか

# --- レイヤーフィルタ (空リスト [] で全レイヤーが対象) ---
TARGET_LAYERS = [
    pcbnew.F_SilkS,
    pcbnew.B_SilkS,
    # pcbnew.F_Fab,
    # pcbnew.B_Fab,
    # pcbnew.F_Cu,
]

# --- フットプリントフィルタ (空文字列 "" で全フットプリントが対象) ---
TARGET_LIBRARY = ""    # 例: "0_Global_OriginalFootPrint"  (部分一致)
TARGET_FP_NAME = ""    # 例: "TestPoint_Pad_1.5x1.5mm_Label" (部分一致)

# --- ドライランモード ---
# True  : 変更内容を確認するだけ (PCBは書き換えない)
# False : 実際に適用する
DRY_RUN = False

# ============================================================
#  ここから下は編集不要
# ============================================================

def layer_ok(item):
    if not TARGET_LAYERS:
        return True
    return item.GetLayer() in TARGET_LAYERS

def fp_ok(fp):
    fp_id = fp.GetFPIDAsString()
    parts = fp_id.split(":", 1)
    lib  = parts[0] if len(parts) > 0 else ""
    name = parts[1] if len(parts) > 1 else ""
    if TARGET_LIBRARY and TARGET_LIBRARY not in lib:
        return False
    if TARGET_FP_NAME and TARGET_FP_NAME not in name:
        return False
    return True

def get_text_items(fp):
    items = []
    if UPDATE_REFERENCE and layer_ok(fp.Reference()):
        items.append(("Ref", fp.Reference()))
    if UPDATE_VALUE and layer_ok(fp.Value()):
        items.append(("Val", fp.Value()))
    if UPDATE_USER_TEXT:
        for g in fp.GraphicalItems():
            try:
                g.GetText()          # テキスト項目か確認
                if layer_ok(g):
                    items.append(("User", g))
            except AttributeError:
                pass
    return items

new_w = pcbnew.FromMM(NEW_WIDTH_MM)
new_h = pcbnew.FromMM(NEW_HEIGHT_MM)
new_t = pcbnew.FromMM(NEW_THICK_MM)

log = []
for fp in board.GetFootprints():
    if not fp_ok(fp):
        continue
    for kind, item in get_text_items(fp):
        old_w = pcbnew.ToMM(item.GetTextWidth())
        old_h = pcbnew.ToMM(item.GetTextHeight())
        old_t = pcbnew.ToMM(item.GetTextThickness())
        layer = board.GetLayerName(item.GetLayer())
        log.append({
            "ref"  : fp.GetReference(),
            "fpid" : fp.GetFPIDAsString(),
            "kind" : kind,
            "text" : item.GetText()[:20],
            "layer": layer,
            "old_w": old_w, "old_h": old_h, "old_t": old_t,
        })
        if not DRY_RUN:
            item.SetTextSize(pcbnew.VECTOR2I(new_w, new_h))
            item.SetTextThickness(new_t)

if not DRY_RUN:
    board.SetModified()
    pcbnew.Refresh()

# --- 結果表示 ---
mode = "【DRY RUN - 変更なし】" if DRY_RUN else "【適用済み】"
print("=" * 90)
print(f"  {mode}  対象件数: {len(log)}")
print(f"  新しい設定: サイズ {NEW_WIDTH_MM} x {NEW_HEIGHT_MM} mm  /  線幅 {NEW_THICK_MM} mm")
print("=" * 90)
print(f"{'Ref':<8} {'種別':<5} {'レイヤー':<12} {'テキスト':<22} {'旧W':>6} {'旧H':>6} {'旧T':>6}")
print("-" * 90)

# 変更がある行のみ強調表示
changed = 0
for r in log:
    marker = ""
    if (abs(r["old_w"] - NEW_WIDTH_MM)  > 0.001 or
        abs(r["old_h"] - NEW_HEIGHT_MM) > 0.001 or
        abs(r["old_t"] - NEW_THICK_MM)  > 0.001):
        marker = " <=="
        changed += 1
    print(f"{r['ref']:<8} {r['kind']:<5} {r['layer']:<12} {r['text']:<22} "
          f"{r['old_w']:>5.2f}  {r['old_h']:>5.2f}  {r['old_t']:>5.3f}{marker}")

print("-" * 90)
print(f"  値が変わるもの: {changed} 件 / 全体: {len(log)} 件")
if DRY_RUN and log:
    print("\n  → DRY_RUN = False に変えて再実行すると適用されます")
print("=" * 90)
