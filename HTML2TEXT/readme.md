## 代码功能为 Web -> Html -> Text -> Paragraph -> Sentence -> Tuple 的提取

首先运行 1_Web2Html.py，会在 htmls 文件夹中生成 sdkname.html

```cmd
python 1_Web2Html.py -n sdkname -u sdkurl
```

接着运行 2_Html2Text.py，会在 texts 文件夹中生成 sdkname.txt

```cmd
python 2_Html2Text.py -n sdkname
```

然后运行 3_Text2Paragraph_PP.py，会在 paragraphs 文件夹中生成 sdkname.json

```cmd
python 3_Text2Paragraph_PP.py -n sdkname
```

然后使用模式 1 运行 4_Paragraph2Tuple_PP_Data.py，会在 Sentences 文件夹中生成 sdkname.txt

```cmd
python 4_Paragraph2Tuple_PP_Data.py -n sdkname -m 1
```

最后使用模式 2 运行 4_Paragraph2Tuple_PP_Data.py，会在 Tuples 文件夹中生成 sdkname.csv

```cmd
python 4_Paragraph2Tuple_PP_Data.py -n sdkname -m 2
```

（处理 Children 类似，将 4_Paragraph2Tuple_PP_Data.py 换成 4_Paragraph2Tuple_PP_Children.py 即可）
