# 立體幾何題目自動生成器

Solid Geometry Auto-Generator for K-12 Math Education

## 功能說明

以 **斜二測畫法**（oblique axonometric projection）產生黑白線稿風格的立體幾何示意圖，適用於國小 / 國中數學教材與題目製作。

### 目前支援形狀

| 形狀 | 函數 | 狀態 |
|------|------|------|
| 長方體 | `draw_cuboid()` | ✅ 完成 |
| 圓柱體 | `draw_cylinder()` | ✅ 完成 |
| 三角柱 | `draw_triangular_prism()` | 🔜 預留 |
| 圓錐 | `draw_cone()` | 🔜 預留 |
| 四角錐 | `draw_pyramid()` | 🔜 預留 |

## 快速開始

```bash
pip install numpy matplotlib
python geometry_generator.py
```

執行後產生 `geometry_figure.png`。

## 參數調整

```python
generate_figure(
    box_length = 20,   # 長方體：長
    box_width  = 12,   # 長方體：寬
    box_height =  6,   # 長方體：高
    cyl_radius =  5,   # 圓柱體：半徑
    cyl_height =  8,   # 圓柱體：高
    filename   = "my_figure.png",
)
```

## 模組架構

```
geometry_generator.py
├── project()              # 斜二測投影核心
├── fill_face_2d()         # 平面面填色（可複用）
├── draw_cuboid()          # 長方體線框
├── draw_cylinder()        # 圓柱體線框
├── draw_dimension_line()  # 雙箭頭尺寸標線
├── draw_radius_line()     # 半徑線 + 圓心 O
└── generate_figure()      # 場景組合器（主入口）
```

## 視覺特色

- 黑白線稿，可見邊實線、隱藏邊虛線
- 長方體頂面淡灰填色，清楚標示承接面
- 接觸橢圓加粗，強調兩形體連接關係
- 全自動尺寸標線：長、寬、高、半徑
- 中文標籤支援（macOS / Windows / Linux）
