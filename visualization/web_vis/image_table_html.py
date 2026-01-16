import os
from typing import List
from IPython.display import display, HTML
from collections import OrderedDict
import json
from collections import defaultdict


html_table_tmplate = {
    0: """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Comparison Table</title>
    <style>
        table {
            width: auto;
            border-collapse: collapse;
            margin: 0 auto;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
            max-width: 20vw;
            width: auto;
        }
        th {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    ${image_table}
</body>
</html>
""",
    1: """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Image Gallery</title>
    <style>
        table {
            width: auto;
            border-collapse: collapse;
            margin: 0 auto;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
            max-width: 20vw; /* 不超过当前页面的20% */
            width: auto;
        }
        img {
            width: 90%;  /* 图片占满90%的单元格 */
            height: auto;
        }
        img.multi_image {
            max-width: 30% !important;
            width: auto !important;
            height: auto !important;
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
            max-width: 100%;
            max-height: 100%;
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
            width: auto;
            height: auto;
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

        ${script}
    </script>
</head>
<body>
    <div id="preview" onclick="hidePreview()">
        <img src="" alt="Preview">
    </div>
    ${image_table}
</body>
</html>
"""
}


class Filter:
    # script = """
    #     function filterTable() {
    #         const rows = document.querySelectorAll("#imageTable tbody tr");
    #         const filters = {};
            
    #         // 获取所有选中的复选框值
    #         document.querySelectorAll("input[type='checkbox']").forEach(checkbox => {
    #             if (checkbox.checked) {
    #                 const key = checkbox.name;
    #                 const value = checkbox.value;
    #                 if (!filters[key]) {
    #                     filters[key] = new Set();
    #                 }
    #                 // 如果选择了[all]，则忽略该key的其他选项
    #                 if (value === '[all]') {
    #                     filters[key] = new Set(['[all]']);
    #                     return;
    #                 }
    #                 // 如果当前key已经有[all]选项，则跳过
    #                 if (!filters[key].has('[all]')) {
    #                     filters[key].add(value);
    #                 }
    #             }
    #         });
            
    #         var count = 0;
    #         rows.forEach(row => {
    #             const attrData = row.getAttribute("attr-data");
    #             let match = true;
                
    #             for (const [key, values] of Object.entries(filters)) {
    #                 // 如果该key选择了[all]，则跳过筛选
    #                 if (values.has('[all]')) continue;
                    
    #                 // 检查是否匹配任意一个选中的值
    #                 let keyMatch = false;
    #                 for (const value of values) {
    #                     if (attrData.includes(`${key}=${value}`)) {
    #                         keyMatch = true;
    #                         break;
    #                     }
    #                 }
    #                 if (!keyMatch) {
    #                     match = false;
    #                     break;
    #                 }
    #             }
    #             count +=1;
    #             row.style.display = match ? "" : "none";
    #         });
    #         console.log("filterTable() count:", count, filters, rows.length);
    #     }"""

    script = """
    function filterTable() {
        const rows = document.querySelectorAll("#imageTable tbody tr");
        const filters = {};
        
        // 获取所有选中的复选框值
        document.querySelectorAll("input[ui_type='filter']").forEach(checkbox => {
            if (checkbox.checked) {
                const key = checkbox.name;
                const value = checkbox.value;
                if (!filters[key]) {
                    filters[key] = new Set();
                }
                // 如果选择了[all]，则忽略该key的其他选项
                if (value === '[all]') {
                    filters[key] = new Set(['[all]']);
                    return;
                }
                // 如果当前key已经有[all]选项，则跳过
                if (!filters[key].has('[all]')) {
                    filters[key].add(value);
                }
            }
        });
        
        var count = 0;
        rows.forEach(row => {
            const attrData = row.getAttribute("attr-data");
            let match = true;
            
            for (const [key, values] of Object.entries(filters)) {
                // 如果该key选择了[all]，则跳过筛选
                if (values.has('[all]')) continue;
                
                // 检查是否匹配任意一个选中的值
                let keyMatch = false;
                for (const value of values) {
                    if (attrData.includes(`${key}=${value}`)) {
                        keyMatch = true;
                        break;
                    }
                }
                if (!keyMatch) {
                    match = false;
                    break;
                }
            }
            // 设置select属性而不是直接修改display
            row.setAttribute('selected', match ? 'true' : 'false');
            count += 1;
        });
        console.log("filterTable() count:", count, filters, rows.length);
        // 筛选后更新分页
        currentPage = 1;
        updatePagination();
    }"""

    @staticmethod
    def html_code(attrs):
        def get_filter_keys_and_values(attrs):
                """获取所有filter keys及其对应的所有取值"""
                filter_keys = OrderedDict()
                value_dict = {}
                
                if attrs:
                    for attr in attrs:
                        for key, value in attr.items():
                            filter_keys[key] = None
                            if key not in value_dict:
                                value_dict[key] = set()
                            value_dict[key].add(str(value))
                
                return filter_keys.keys(), value_dict
        
        filter_keys, value_dict = get_filter_keys_and_values(attrs)
        # 为每个filter key生成一个复选框组
        filter_html = "<div style='margin-bottom: 20px;'>"
        for key in filter_keys:
            filter_html += f"""
            <div style='margin-bottom: 10px;'>
                <label>{key}:</label>
                <div style='display: flex; flex-wrap: wrap;'>
                    <label style='margin-right: 10px;'>
                        <input type='checkbox' ui_type='filter' name='{key}' value='[all]' onchange='filterTable()'> [all]
                    </label>
            """
            # 添加其他选项
            for value in sorted(value_dict[key]):
                filter_html += f"""
                    <label style='margin-right: 10px;'>
                        <input type='checkbox' ui_type='filter' name='{key}' value='{value}' onchange='filterTable()'> {value}
                    </label>
                """
            filter_html += """
                </div>
            </div>
            """
        filter_html += "</div>"
        return filter_html


class Page:
    html_code = """
    <div style="margin-bottom: 20px;">
        <label>每页显示行数:</label>
        <select id="rowsPerPage" onchange="changePageSize()">
            <option value="100">100</option>
            <option value="50">50</option>
            <option value="20">20</option>
            <option value="10">10</option>
        </select>
    </div>
    <div id="pagination" style="margin-top: 20px; text-align: center;">
        <button onclick="previousPage()">上一页</button>
        <span id="pageInfo" style="margin: 0 10px;"></span>
        <button onclick="nextPage()">下一页</button>
    </div>"""

    scirpt = """
        let currentPage = 1;
        let rowsPerPage = 100;
        let totalRows = 0;
        let totalPages = 0;

        function updatePagination() {
            // 获取所有selected为true的行
            const selectedRows = Array.from(document.querySelectorAll("#imageTable tbody tr[selected='true']"));
            totalRows = selectedRows.length;
            totalPages = Math.ceil(totalRows / rowsPerPage);
            
            // 确保当前页不超过总页数
            if (currentPage > totalPages && totalPages > 0) {
                currentPage = totalPages;
            }
            
            // 显示当前页码信息
            document.getElementById("pageInfo").innerText = `第 ${currentPage} 页，共 ${totalPages} 页 (总行数: ${totalRows})`;
            
            // 显示当前页的行
            const start = (currentPage - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            
            // 先隐藏所有行
            document.querySelectorAll("#imageTable tbody tr").forEach(row => {
                row.style.display = "none";
            });
            
            // 显示当前页的选中行
            selectedRows.forEach((row, index) => {
                if (index >= start && index < end) {
                    row.style.display = "";
                }
            });
            console.log("updatePagination() currentPage:", currentPage, "rowsPerPage:", rowsPerPage, "totalRows:", totalRows, "totalPages:", totalPages);
        }

        function changePageSize() {
            rowsPerPage = parseInt(document.getElementById("rowsPerPage").value);
            currentPage = 1;
            updatePagination();
        }

        function previousPage() {
            if (currentPage > 1) {
                currentPage--;
                updatePagination();
            }
        }

        function nextPage() {
            // 重新计算总页数，确保数据是最新的
            const visibleRows = Array.from(document.querySelectorAll("#imageTable tbody tr[selected='true']"));
            totalPages = Math.ceil(visibleRows.length / rowsPerPage);
            
            // 如果当前页已经是最后一页，则不做任何操作
            if (currentPage >= totalPages) {
                return;
            }
            
            currentPage++;
            updatePagination();
        }

        // 初始化分页
        document.addEventListener("DOMContentLoaded", function() {
            updatePagination();
        });
    """


class CheckBox:
    # data_id 用来标识当前结果是针对那个图的；column_name记录当前checkbox在哪一列的列名
    checkbox_html_code = """<input type="checkbox" class="itemCheckbox" data_id="{data_id}" column_name="{column_name}" {checked}>"""
    save_button_html_code = """<button id="saveCheckbox" onclick="save_checkbox_result(0)">保存选择结果</button>"""
    load_button_html_code = """<button id="loadCheckbox" onclick="load_checkbox_result(0)">加载选择结果</button>"""
    script = """
    function save_checkbox_result(idx) {
        const checkedCheckboxes = Array.from(document.querySelectorAll(".itemCheckbox:checked"));
        const selectedIds = checkedCheckboxes.map(checkbox => [checkbox.getAttribute("column_name"), checkbox.getAttribute("data_id")]);
        console.log("save_checkbox_result() idx:", idx, selectedIds);

        const result = {
            selectedIds: selectedIds,
            timestamp: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(result, null, 2)], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = 'selection_result.json';
        document.body.appendChild(a);
        a.click();
        
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    function load_checkbox_result(idx) {
        console.log("load_checkbox_result() idx:", idx);
        
        // 创建文件输入元素
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.json';
        fileInput.style.display = 'none';
        
        fileInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    const result = JSON.parse(e.target.result);
                    console.log("Loaded checkbox result:", result);
                    
                    // 先取消所有checkbox的选中状态
                    document.querySelectorAll('.itemCheckbox').forEach(checkbox => {
                        checkbox.checked = false;
                    });
                    
                    // 根据保存的结果设置checkbox状态
                    if (result.selectedIds && Array.isArray(result.selectedIds)) {
                        result.selectedIds.forEach(([columnName, dataId]) => {
                            const checkbox = document.querySelector(`.itemCheckbox[column_name="${columnName}"][data_id="${dataId}"]`);
                            if (checkbox) {
                                checkbox.checked = true;
                            }
                        });
                    }
                    
                    alert(`成功加载选择结果！共加载了 ${result.selectedIds ? result.selectedIds.length : 0} 个选择项`);
                    
                } catch (error) {
                    console.error("Error parsing JSON file:", error);
                    alert("文件格式错误，请选择正确的JSON文件");
                }
            };
            
            reader.readAsText(file);
        });
        
        // 触发文件选择
        document.body.appendChild(fileInput);
        fileInput.click();
        document.body.removeChild(fileInput);
    }
"""

def assert_no_suffix_str(keys: List[str]):
    """
    断言keys列表中不存在某个key是另一个key的后缀
    Args:
        keys: 字符串列表
    Raises:
        AssertionError: 如果存在后缀关系
    """
    if not keys or len(keys) < 2:
        return
    # 检查是否存在后缀关系
    for i in range(len(keys)):
        for j in range(len(keys)):
            if i != j:  # 不比较自己
                key1 = keys[i]
                key2 = keys[j]
                # 检查key1是否是key2的后缀
                if key2.endswith(key1) and key1 != key2:
                    raise AssertionError(f"Key '{key1}' is a suffix of key '{key2}'. This may cause conflicts in string matching.")
    return True
        

def build_image_table_html(image_urls, column_names, attrs=None, template_id=0):
    """
        image_urls: (M, K), M rows and K columns
            [
                [url_1, url_2, ..., url_k],
                [url_1, url_2, ..., url_k],
            ]
        attrs: [  # attribution of each row
            {},
            {}
        ]
    Example:
        html_code = build_image_table_html(image_urls, column_names)
        display(HTML(html_code))
    """
    table_template = '''
    {}
    <table id="imageTable">
        <thead>
            {}
        </thead>
        <tbody>
            {}
        </tbody>
    </table>
    {}
    '''
    if attrs is not None:
        keys = set()
        for attr in attrs: keys |= set(attr.keys())
        assert_no_suffix_str(list(keys))

    ths = "<tr>" + "".join(['<th>{}</th>'.format(k) for k in column_names]) + "</tr>"   # title
    tr_template = '<tr attr-data="{}" selected="true">\n{}\n</tr>'
    td_template = '<td><img src="{}" alt="{}" onclick="showPreview(\'{}\')"></td>'
    multi_img_td_template = lambda urls: '<td>{}</td>'.format('\n'.join([
        f'<img class="multi_image" src="{url}" alt="{os.path.split(url)[-1]}" onclick="showPreview(\'{url}\')">' for url in urls
        ]))
    txt_td_template = '<td style="overflow-wrap: break-word; word-break: break-all; width: 300px; border: 1px solid black; {}">{}</td>'

    trs = []
    for idx, row_image_urls in enumerate(image_urls):
        tds = [] # [td_template.format(image_url, os.path.split(image_url)[-1], image_url) for image_url in row_image_urls]
        for col_idx, image_url in enumerate(row_image_urls):
            if isinstance(image_url, str):
                tds.append(td_template.format(image_url, os.path.split(image_url)[-1], image_url))
            elif isinstance(image_url, list):
                tds.append(multi_img_td_template(image_url))
            elif isinstance(image_url, tuple):
                dtype, content = image_url[:2]
                if dtype == 'str':
                    style = image_url[2] if len(image_url) >= 3 else ""
                    tds.append(txt_td_template.format(style, content))
                elif dtype == 'checkbox':
                    column_name = image_url[2] if len(image_url) >= 3 else col_idx
                    checked = image_url[3] if len(image_url) >= 4 else False
                    check_box_code = CheckBox.checkbox_html_code.format(
                        data_id=idx if content is None else content,
                        column_name=column_name,
                        checked="checked" if checked else "")
                    tds.append(f'<td>{check_box_code}</td>')
                else: raise NotImplementedError(image_url)
            else: raise NotImplementedError(image_url)
        
        attr_data = ""
        if attrs and idx < len(attrs):
            attr_data = " ".join(f"{k}={v}" for k, v in attrs[idx].items())
        tr = tr_template.format(attr_data, "\n".join(tds))
        trs.append(tr)

    filter_html = "\n".join([Filter.html_code(attrs), CheckBox.load_button_html_code])
    botome_html = "\n".join([Page.html_code, CheckBox.save_button_html_code]) 
    table_html = table_template.format(filter_html, ths, "\n".join(trs), botome_html)  # <table> ... </table>
    html_code = html_table_tmplate[template_id].replace("${image_table}", table_html)  # 

    script_code = "\n".join([Filter.script, Page.scirpt, CheckBox.script])  #  
    html_code = html_code.replace("${script}", script_code)  # 
    return html_code


def display_image_table_html(image_urls, column_names):
    html_code = build_image_table_html(image_urls, column_names)
    return display(HTML(html_code))


def get_image_urls(image_dir_dict, base_url=".", image_root="./", image_names=None, show_range=(0, 10), 
                   reference_column=0, priority_dict=None, return_image_names=False):
    """Given a dict that map column name to a image dir, collect all image_urls that statistified input 
    condition to format a 2-D list , for build_image_table_html.

    Args:
        image_dir_dict: 
            {
                "column1 name": image_dir1,
                "column2 name": image_dir2,
                ....
            }
        base_url: url prefix need to append before image_path
        image_names: which name of image need to collect
        show_range: which range of image need to collect, if image_names given, will not work
        priority_dict: dict that map image_name to priority, if priority < 0, meaning not show
            {
                "image_name1": -1, # not show
                "image_name2": 2, # show at second
                "image_name3": 1, # show at first
            }
    
    Example:
        base_url = "http://30.72.66.176:8081/files/apdcephfs_cq9/share_1447896/xuehuiyu/Workspace/work/detection_and_segmentation/DINO/"
        image_urls, column_names = web_vis.get_image_urls(
            {
                'Detected Image': 'logs/vis_results/advertisment_parsing_4gpu/advertisment/v2_8class_5/DINO/R50-MS4/eval/checkpoint0011/val/',
                'GT Image':'logs/vis_results/advertisment_parsing_4gpu/advertisment/v2_8class_5/gt/val/',
                'Original Image': 'datasets/data/advertisment/v2_8class_5/images/val'
            },
            base_url, show_range=(10, 20))
    """
    column_keys = list(image_dir_dict.keys())
    main_column_key = column_keys[reference_column]

    if image_names is None:
        image_dir = os.path.join(image_root, image_dir_dict[main_column_key])
        image_names = sorted(os.listdir(image_dir))
        image_names = image_names[show_range[0]:show_range[1]]

    image_urls = []
    if priority_dict is not None:
        image_names_priorty = [(priority_dict[img_name], img_name) for img_name in image_names]
        image_names_priorty = sorted(image_names_priorty, key=lambda x: x[0])
        image_names = [img_name for p, img_name in image_names_priorty if p >= 0]  # sort by priority, if priority < 0, meaning not show
    for image_name in image_names:
        row_image_urls = []
        for k in column_keys:
            image_dir = image_dir_dict[k]
            if isinstance(image_dir, str):
                img_path = os.path.join(image_dir, image_name)
                img_url = base_url + "/" + img_path
                row_image_urls.append(img_url)
            elif isinstance(image_dir, dict):
                info_dict = image_dir
                row_image_urls.append(info_dict[image_name])
            else:
                raise NotImplementedError(f"{image_dir}: {type(image_dir)}")
        image_urls.append(row_image_urls)
    if return_image_names:
        return image_urls, column_keys, image_names
    else:
        return image_urls, column_keys
    
def get_selected_checkbox_as_attrs_of_rows(rows_tag, json_datas, column_map=None, attrs=None):
    """Read result JSON and convert to attributes for each row

    Args:
        rows_tag (list): row tags for each row, such as image_name/image_id/row_id
        json_datas (dict, str): record setted column_name and row_tag of each selected checkbox
            {
                "selectedIds": [
                    [column_name, row_tag],
                    ...., 
                ]
            } 
        column_map (dict): _description_

    Returns: length of return equal to input_row_tag_list
        list: [
            {"column_name": True/False, ...}, 
            ...
        ]
        
    Example:
        > image_names = [os.path.split(jd['image_path'])[-1] for jd in jds]
        > images_list = [
                [
                    os.path.abspath(f"{images_root}/{sub_dir}/{image_name}"),
                    ('checkbox', image_name, "文字乱码：大图明显"),    # ("checkbox", row_tag, column_name)
                    ('checkbox', image_name, "文字乱码：底分辨率模糊"),
                    ('checkbox', image_name, "文字乱码：原图模糊")
                ] for image_name in image_names]
        > column_names = ["image", "文字乱码：大图明显", "文字乱码：底分辨率模糊", "文字乱码：原图模糊"]
        > vis_utils.save_to_web_and_get_url3(images_list, save_html_web_path, column_names, attrs=attrs)
        >
        > # saved checkbox json and load as attrs selected items
        > checkbox_data = json.load(open('../dataset2/json/lableled/small_text_on_product.json'))
        > column_map = {"小字畸形：明显": "1. 小字畸形：明显", "小字畸形：模糊": "2. 小字畸形：模糊", "小字畸形：底分辨率": "3. 小字畸形：底分辨率"} # colmun_name: showed attr name
        > attrs = get_selected_checkbox_as_attrs_of_rows(image_names, checkbox_data, column_map)
        > vis_utils.save_to_web_and_get_url3(images_list, save_html_web_path, column_names, attrs=attrs)
    """
    if isinstance(json_datas, str):
        json_datas = json.load(open(json_datas))
        
    row_attrs = defaultdict(dict)
    collected_column_names = set()
    for column_name, row_tag in json_datas['selectedIds']:
        column_name = column_map[column_name] if column_map is not None else column_name
        row_attrs[row_tag][column_name] = True
        collected_column_names.add(column_name)
    
    attrs = [{} for _ in range(len(rows_tag))] if attrs is None else attrs
    for row_tag, attr in zip(rows_tag, attrs):
        _attr = {c: False for c in collected_column_names}
        _attr.update(row_attrs.get(row_tag, {}))
        attr.update(_attr)
    return attrs
