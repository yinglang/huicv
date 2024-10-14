import os
import sys
import pandas as pd
import json

html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Image Gallery</title>
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        img {
            max-width: 100%;
            height: auto;
        }
        td.image{
            width: 20%;
        }
        td.prompt {
            width: 1%; /* 指定宽度，可以根据需要调整 */
            white-space: pre-wrap; /* 保留换行符并自动换行 */
            word-wrap: break-word; /* 如果单词太长，强制换行 */
        }
        .fixed-column-width {
            width: 200px; /* 设置列宽为200px */
            word-wrap: break-word; /* 自动换行 */
            white-space: pre-wrap; /* 保留空白字符，如换行符和空格 */
        }
        #preview {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.8);
            z-index: 100;
        }
        
        /* 预览图片样式 */
        #preview img {
            display: block;
            position: absolute;
            top: 50%;
            left: 50%;
            max-width: 90%;
            max-height: 90%;
            transform: translate(-50%, -50%);
            cursor: pointer;
        }
    </style>
    <script>
        function showPreview(src) {
            var preview = document.getElementById("preview");
            var previewImg = preview.getElementsByTagName("img")[0];
            previewImg.src = src;
            preview.style.display = "block";
        }
    
        function hidePreview() {
            var preview = document.getElementById("preview");
            preview.style.display = "none";
        }
    </script>
</head>
<body>
    <div id="preview" onclick="hidePreview()">
        <img src="" alt="Preview">
    </div>
    <table>
        <thead>
            <tr>
                <th>文件名</th>
                <th>raw</th>
                <th>线上优化版</th>
            </tr>
        </thead>
        <tbody>
        </tbody>
    </table>
</body>
</html>
"""

classify = sys.argv[1]
folder1 = f"/deloresding/temp/{classify}"

if not os.path.isdir("/apdcephfs_cq9/share_1447896"+folder1):
    print(0)
    sys.exit(0)
    
data = []
for filename in sorted(os.listdir("/apdcephfs_cq9/share_1447896"+folder1)):
    #print(filename)
    if not filename.endswith(("jpg", "png")):
        continue
    
    img1_path = os.path.join(folder1, filename)

    html += f"""
        <tr>
            <td>{filename}</td>
            <td class="image"><img src="{img1_path}" alt="{filename}_1" onclick="showPreview('{img1_path}')"></td>
        </tr>
    """ 


with open(f"/apdcephfs_cq9/share_1447896/lucienymliu/html/deloresding/横转竖/{classify}.html", "w") as file:
    file.write(html)
