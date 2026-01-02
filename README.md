# 数据存档功能
本存储库从WeGame安装的《英雄联盟》和《英雄联盟体验服》中提取所有不包含用户个人配置且在不同设备上共有的文本文件，通过提交的方式分析每次更新时发生的变化。

用户输入：游戏目录。注意一定是一个**文件夹**。
- 如果只想指定个别wad文件，请参阅[CDTB存储库](https://github.com/CommunityDragon/CDTB)及其Python库。

输出（完成所有步骤后）：所有文本文件，按照原始文件结构组织。

工作流：
1. “.wad.client”文件 → 原始单文件（bin等）。
2. 非“.wad.client”的文本文件 → 适当格式化后的文本文件。
    - 目前支持以下文本编码：
        - UTF-8
        - ANSI
    - 目前收录以下文本格式：
        - .json
        - .txt
        - .js
        - .xml
        - .yaml
        - .css
        - .html
        - .cfg
        - .ini
        - .effect
        - .manifest

----
(The following content is the English version of README.)
# Data Archive Functionality
This repository is designed to extract all text files that don't involve user config and are common among different devices from League of Legends Tencent and League of Legends Tencent PBE and analyze changes after an update by commit.

User input: Game directory. Must be a **folder**.
- To extract and convert single wad files, please refer to [CDTB repository](https://github.com/CommunityDragon/CDTB) and the corresponding Python library.

Output (with all steps finished): All text files, organized by the original file structure.

Workflow:
1. "wad.client" files -> Raw single files (bin, etc.).
2. Non-"wad.client" files -> Formatted text files.
    - The following encodings are supported currently:
        - UTF-8
        - ANSI
    - The following text formats are collected currently:
        - .json
        - .txt
        - .js
        - .xml
        - .yaml
        - .css
        - .html
        - .cfg
        - .ini
        - .effect
        - .manifest
