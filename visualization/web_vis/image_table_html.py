import os
from IPython.display import display, HTML


html_table_tmplate = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Comparison Table</title>
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
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
"""


def build_image_table_html(image_urls, column_names):
    """
        image_urls: (M, K), M rows and K columns
            [
                [url_1, url_2, ..., url_k],
                [url_1, url_2, ..., url_k],
            ]
    Example:
        html_code = build_image_table_html(image_urls, column_names)
        display(HTML(html_code))
    """
    table_template = '''
    <table>
        <tr>
            {}
        </tr>
            {}
    </table>
    '''

    ths = "<tr>" + "".join(['<th>{}</th>'.format(k) for k in column_names]) + "</tr>"   # title
    tr_template = '<tr>\n{}\n</tr>'
    td_template = '<td><img src="{}"></td>'

    trs = []
    for row_image_urls in image_urls:
        tds = [td_template.format(image_url) for image_url in row_image_urls]
        tr = tr_template.format("\n".join(tds))
        trs.append(tr)
    table_html = table_template.format(ths, "\n".join(trs))  # <table> ... </table>
    html_code = html_table_tmplate.replace("${image_table}", table_html)  # 
    return html_code


def display_image_table_html(image_urls, column_names):
    html_code = build_image_table_html(image_urls, column_names)
    return display(HTML(html_code))


def get_image_urls(image_dir_dict, base_url, image_names=None, show_range=(0, 10)):
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
    main_column_key = column_keys[0]

    if image_names is None:
        image_names = os.listdir(image_dir_dict[main_column_key])[show_range[0]:show_range[1]]

    image_urls = []
    for image_name in image_names:
        row_image_urls = []
        for k in column_keys:
            img_path = os.path.join(image_dir_dict[k], image_name)
            img_url = base_url + "/" + img_path
            row_image_urls.append(img_url)
        image_urls.append(row_image_urls)
    return image_urls, column_keys
    
