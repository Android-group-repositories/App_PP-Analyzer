## 代码功能为 web -> html -> text -> paragraph 的提取

首先运行1_Web2Html.py，会在htmls文件夹中生成sdkname.html

```cmd
python 1_Web2Html.py -n sdkname -u sdkurl
```

接着运行2_Html2Text.py，会在texts文件夹中生成sdkname.txt

```cmd
python 2_Html2Text.py -n sdkname
```

然后运行3_Text2Paragraph.py，会在paragraphs文件夹中生成sdkname.json

```cmd
python 3_Text2Paragraph.py -n sdkname
```
