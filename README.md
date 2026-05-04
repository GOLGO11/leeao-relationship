# 李敖交互式人物关系表

这个项目现在按“逐本、多轮”的方式推进：用户指定一本书，我先做该书的一轮抽取与网页/纯文本导出；用户再指示增删、分类、合并别名或继续深挖。每一轮完成时，我都会给出下一轮建议。

## 当前工作规则

1. 不一次性处理 163 本。
2. 每轮只处理用户指定的一本书，必要时只处理其中若干章。
3. 人物关系分为：直接接触/往来、司法/诉讼/审判、家人/情感、出版/学术/媒体、政治/公共论战、神交/思想引用、间接提及/待复核。
4. “神交”单独列出，例如爱因斯坦、孔子、拿破仑等只在思想、阅读、引用层面相关的人物。
5. 每轮同步更新网页数据和纯文本导出。

## 常用命令

列出书目录：

```powershell
Get-ChildItem -Directory '《大李敖全集5.0》（wjm_tcy版）分章节\*\*' | Select-Object FullName
```

抽取指定一本书：

```powershell
C:\Users\zzy87\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\extract_relationships.py --book-path "《大李敖全集5.0》（wjm_tcy版）分章节\001.自传回忆类\001.李敖自传与回忆"
```

打开网页：

```text
index.html
```

## 输出

- `index.html`：交互式网页。
- `data/relationship-data.js`：网页读取的数据。
- `data/people.json`：结构化数据。
- `exports/li-ao-relationships.txt`：纯文本人物总表。
- `exports/by-book-index.txt`：逐本索引。
- `exports/li-ao-relationships.csv`：表格导出。
