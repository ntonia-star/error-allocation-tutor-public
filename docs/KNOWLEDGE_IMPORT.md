# 导入核验知识

1. 将有权处理的资料放入本地knowledge_source/；该目录已忽略提交。PDF/PPTX扫描：`python scripts/inspect_sources.py`。需要先安装requirements-tools.txt中的解析库。
2. 扫描PDF可用scripts/ocr_sources.py，需本机Tesseract以及tools/tessdata中的chi_sim、eng识别包。OCR输出仅供人工核对，不能直接用于公式问答。旧PPT应另存为PPTX副本，原件保留。
3. 由维护者检查相关完整页面、公式、条件和图表，将有权使用的内容整理为JSON数组。每条包括id、title、category、content、formula、conditions、symbols、related、sources、verified。sources至少一项，每项保留file、kind、chapter、pdf_page、printed_page、slide、url；不能虚构缺失页码。verified必须是人工确认后的true。
4. 运行`python scripts/import_knowledge.py 本地核验文件.json`，会验证字段与来源后更新index、structured_knowledge和chunks；它不验证版权许可或公式语义，仍需维护者审核。
5. 若有权在网页展示源页，可将对应图片存入本地knowledge_base/pages/，并在sources中给出真实book/slides路由和pdf_page；未提供图像的来源不应设置假的可点击URL。目录默认忽略提交。
6. 重启服务。知识库和题目数据发生变更后，在自己的私有部署副本中测试并部署；不要将私人课程内容回传到本公开仓库。

公开版自带的corpus.json及exercises.json均为[]。题目采用id、level、question、answer、explanation、source_ids字段，level为记忆/理解/应用；source_ids必须指向已核验片段。没有任何课程原文或例题作为默认数据。
