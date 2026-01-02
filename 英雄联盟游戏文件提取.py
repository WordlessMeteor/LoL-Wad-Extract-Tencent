import cssbeautifier, jsbeautifier, json, os, time, re, shutil, traceback, _io
from humanize import naturalsize
from cdtb.hashes import default_hashfile, HashFile
from cdtb.wad import Wad
from cdtb.binfile import BinFile
from cdtb.rstfile import RstFile, get_hashfile, key_to_hash
from cdtb.export import AtlasInfoConverter
from typing import Any, Literal
from bs4 import BeautifulSoup

os.makedirs("Update Logs", exist_ok = True)
currentTime = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
log = open(f"Update Logs/{currentTime}.log", "w", encoding = "utf-8")

def logInput(prompt: str = "", log: _io.TextIOWrapper = log, write_time: bool = True) -> str:
    s = input(prompt)
    if isinstance(log, _io.TextIOWrapper):
        if write_time:
            currentTime = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
            log.write("[%s]%s\n" %(currentTime, prompt + s))
        else:
            log.write(prompt + s + "\n")
    return s

def logPrint(s: object = "", log: _io.TextIOWrapper = log, end: str = "\n", print_time: bool = False, write_time: bool = True) -> None:
    currentTime = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
    if print_time:
        print("[%s]%s" %(currentTime, s), end = end, flush = end == "\r")
    else:
        print(s, end = end, flush = end == "\r")
    if isinstance(log, _io.TextIOWrapper):
        if write_time:
            log.write("[%s]%s%s" %(currentTime, str(s), "\n" if end == "\r" else end))
        else:
            log.write("%s%s" %(str(s), "\n" if end == "\r" else end))

def format_json(origin: str, indent_char: str = " ", number: int = 4) -> str: #对字符串origin进行格式化（Formalize the string `origin`）
    indent: str = indent_char * number
    bracket_level: int = 0 #bracket_level用来根据花括号的级别输出对应数量的水平制表符（`bracket_level` is used to input the corresponding number of horizontal tabs based on the hierachy of the curly brackets）
    result: str = ""
    escape: bool = False #标注是否对下一个字符应用转义（Marks whether the next character is escaped）
    for char in origin:
        if escape: #如果一个字符是被转义的，直接添加该字符，不作任何处理（If a character is escaped, add this character directly without any other operations）
            result += char
            escape = False #转义字符被添加后，关闭转义开关（After that escaped character is added, switch off `escape`）
        else:
            if char in "{[":
                bracket_level += 1
                result += char + "\n" + indent * bracket_level
            elif char in "]}":
                bracket_level -= 1
                result += "\n" + indent * bracket_level + char
            elif char == ":":
                result += ": "
            elif char == ",":
                result += ",\n" + indent * bracket_level
            elif char == "\\":
                result += "\\"
                escape = True
            else:
                result += char
    return result

def wad_extract(wad_path: str, output_dir: str, hash_path: str | None = None, patterns: list[str] = [], unknown: Literal["yes", "only", "no"] = "yes", lazy: bool = False) -> int:
    '''
    将一个wad文件中的内容提取到指定目录。代码根据cdtb库改写而来。<br>Extract content of a wad file into a specified directory. Code are adapted from cdtb library.
    
    :param wad_path: .wad.client或.wad文件路径。<br>Path to the .wad.client or .wad file.
    :type wad_path: str
    :param output_dir: 输出目录。<br>Output directory.
    :type output_dir: str
    :hash_path: hash文件路径。<br>Path to the hash file.
    :type hash_path: str | None
    :param patterns: 筛选要提取的文件的正则表达式列表。所输入的正则表达式必须能够形成完全匹配。<br>List of regex patterns to filter files to extract. The input regular expressions must fully match the target paths.
    :type patterns: list[str]
    :param unknown: 未知文件提取策略。默认为“yes”。<br>Strategy for extracting unknown files. Default value is "yes".<br>可选值：<br>Options:
    
        - "yes": 提取所有未知文件。<br>Extract all unknown files.
        - "only": 仅提取未知文件。<br>Extract only unknown files.
        - "no": 不提取未知文件。<br>Don't extract unknown files.
    :type unknown: Literal["yes", "only", "no"]
    :param lazy: 目标文件存在时跳过提取。默认为假。<br>Skip extraction if the target file already exists. Default is False.
    :type lazy: bool
    :return: 状态码。<br>Status code.
    :rtype: int
    '''
    #参数预处理（Parameter preparation）
    if hash_path == None:
        hashfile: HashFile = default_hashfile(wad_path)
    else:
        hashfile = HashFile(hash_path)
    #读取Wad文件（Read Wad file）
    wad = Wad(wad_path, hashes = hashfile.load())
    if wad.files == None:
        logPrint("在wad文件中未找到任何文件。\nNo files found in the given wad file.")
        return 1
    else:
        if unknown == "only":
            wad.files = [wf for wf in wad.files if wf.path is None]
        elif unknown == "no":
            wad.files = [wf for wf in wad.files if wf.path is not None]
    if len(patterns) > 0:
        wad.files = [wf for wf in wad.files if any(wf.path != None and re.fullmatch(p, wf.path) for p in patterns)]
    #提取文件（Extract files）
    wad.guess_extensions()
    wad.extract(output_dir, overwrite = not lazy)
    return 0

def CopyConvert(src: str, dst: str) -> None: #纯文本文件复制函数（Plain text file copy function）
    os.makedirs(os.path.dirname(dst), exist_ok = True)
    with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
        shutil.copyfileobj(fsrc, fdst)

def BinConvert(src: str, dst: str) -> None: #二进制文件转换函数。dst参数应以“.json”结尾（Binary file conversion function. `dst` should end with ".json"）
    os.makedirs(os.path.dirname(dst), exist_ok = True)
    with open(dst, "w", encoding = "utf-8") as fdst:
        binfile = BinFile(src)
        binData: dict[str, Any] = binfile.to_serializable()
        if "__linked" in binData: #确保最后两个键一定是__linked和__patches（如有）【Make sure the last two keys must be __linked and __patches (if there they are)】
            tmp: Any = binData.pop("__linked")
            binData["__linked"] = tmp
        if "__patches" in binData:
            tmp: Any = binData.pop("__patches")
            binData["__patches"] = tmp
        json.dump(binfile.to_serializable(), fdst, indent = 4, ensure_ascii = False) #这里的indent = 4实际上可以删掉，因为format_text_files函数中在读取json文件后会自动转化成缩进为4个空格的字符串，从而显著节省空间占用。下同（Here `indent = 4` can actually be deleted, because after `format_text_files` function reads the json file, the content will be transformed into a string with 4 spaces as an indentation unit, so that space cost can be saved significantly. So can the following）

def RstConvert(src: str, dst: str, game_version: int = 1502) -> None: #字符串常量池转换函数。dst参数应以“.json”结尾（Stringtable conversion function. `dst` should end with ".json"）
    rstfile: RstFile = RstFile(src)
    hashes = get_hashfile(game_version).load()
    hashes = {key_to_hash(hash, bits = rstfile.hash_bits): value for (hash, value) in hashes.items()}
    rst_json: dict[str, dict[str, str] | int] = {"entries": {}, "version": rstfile.version}
    for (key, value) in rstfile.entries.items():
        if key in hashes:
            key = hashes[key]
        else:
            key = f"{{{key:010x}}}"
        rst_json["entries"][key] = value
    os.makedirs(os.path.dirname(dst), exist_ok = True)
    with open(dst, "w", encoding = "utf-8") as fdst:
        json.dump(rst_json, fdst, indent = 4, ensure_ascii = False)

def AtlasInfoConvert(src: str, dst: str) -> None: #图册信息转换函数（Atlas info conversion function）
    with open(src, "rb") as fsrc, open(dst, "w", encoding = "utf-8") as fdst:
        json.dump(AtlasInfoConverter.parse_atlasinfo(fsrc), fdst, indent = 4, ensure_ascii = False)

def isPlainTextPath(path: str) -> bool:
    ext: str = os.path.splitext(path)[1]
    return ext in {".json", ".txt", ".js", ".xml", ".yaml", ".css", ".html", ".cfg", ".ini", ".effect", ".manifest"}

def isWadPath(path: str) -> bool:
    ext: str = os.path.splitext(path)[1]
    return ext == ".wad" or path.endswith(".wad.client")

def extract_data_resource(copy_text: bool = True, extract_wad: bool = True) -> None:
    '''
    将游戏目录中的文件提取到某个临时文件夹。<br>Extract game files into some temporary folder.
    
    :param copy_text: 指示是否复制.wad.client文件和.wad文件以外的文本文件。默认为真。<br>Represents whether to copy text files not from ".wad.client" and ".wad" files. True by default.
    :type copy_text: bool
    :param extract_wad: 指示是否提取.wad.client文件和.wad文件中的内容。默认为真。<br>Represents whether to extract content from ".wad.client" and ".wad" files. True by default.
    :type extract_wad: bool
    '''
    logPrint("请指定游戏目录：\nPlease specify the game directory:")
    while True:
        game_dir: str = logInput()
        if game_dir == "":
            continue
        elif game_dir == chr(4):
            return
        elif not os.path.exists(game_dir):
            logPrint("目录不存在。请重新输入。\nPath not found. Please try again.")
        elif not os.path.isdir(game_dir):
            logPrint("请输入一个文件夹。\nPlease enter a folder.")
        else:
            break
    logPrint("请指定要导出的文件目录：\nPlease specify the target directory:")
    while True:
        target_dir = logInput()
        if target_dir == "":
            continue
        elif target_dir == chr(4):
            return
        elif os.path.exists(target_dir):
            if os.path.isdir(target_dir):
                break
            else:
                logPrint("您输入的目录已存在，但不是文件夹。请重新输入。\nThe path you entered already exists but isn't a folder. Please try again.")
        else:
            os.makedirs(target_dir)
            logPrint("已创建文件夹。\nFolder created.")
            break
    logPrint("正在整理文件列表……\nSorting out a file list ...", print_time = True)
    patterns_to_skip: list[str] = [
        r"Cross/coach/agent/lol_ai_coach/Python311/.*", #Python3.11的标准文件无需查看其变更（Python 3.11's standard files don't need inspecting any change）
        r"Game/Config/Champions/.*",
        r"Game/Config/Global/Recommended/RIOT_ItemSet_\d*\.json",
        r"Game/Config/ItemSets.json",
        r"Game/Logs/.*"
    ]
    error_wad_client_files: list[str] = []
    files_to_extract: list[dict[str, Any]] = []
    for root, dirs, files in os.walk(game_dir):
        for file in files:
            srcpath: str = os.path.join(root, file).replace("\\", "/")
            relpath: str = os.path.relpath(srcpath, game_dir).replace("\\", "/")
            if any(map(lambda x: re.fullmatch(x, relpath), patterns_to_skip)):
                continue
            if isPlainTextPath(relpath) and copy_text or isWadPath(relpath) and extract_wad:
                body: dict[str, Any] = {}
                src_timestamp: float = os.path.getmtime(srcpath)
                src_date: str = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(src_timestamp))
                src_bytes: int = os.path.getsize(srcpath)
                src_size: str = naturalsize(src_bytes, binary = True)
                body["relpath"] = relpath
                body["src_timestamp"] = src_timestamp
                body["src_date"] = src_date
                body["src_bytes"] = src_bytes
                body["src_size"] = src_size
                files_to_extract.append(body)
    max_index_width: int = 2 * len(str(len(files_to_extract))) + 3
    for i in range(len(files_to_extract)):
        relpath = files_to_extract[i]["relpath"]
        src_date = files_to_extract[i]["src_date"]
        src_size = files_to_extract[i]["src_size"]
        srcpath = os.path.join(game_dir, relpath).replace("\\", "/")
        index_str: str = "[%d/%d]" %(i + 1, len(files_to_extract))
        if isPlainTextPath(relpath):
            logPrint("%s | 正在复制文件（Copying）：   %s\t%s\t%s" %("{0:<{1}}".format(index_str, max_index_width), "{0:<12}".format(src_size), src_date, srcpath), print_time = True)
            dstpath: str = os.path.join(target_dir, relpath).replace("\\", "/")
            os.makedirs(os.path.dirname(dstpath), exist_ok = True)
            shutil.copy2(srcpath, dstpath) #第一步暂且先复制原始文件（For the first step, temporarily copy the raw files）
        elif isWadPath(relpath):
            logPrint("%s | 正在解包文件（Unpacking）： %s\t%s\t%s" %("{0:<{1}}".format(index_str, max_index_width), "{0:<12}".format(src_size), src_date, srcpath), print_time = True)
            if relpath.startswith("Game/DATA/FINAL/"):
                wad_extract_path_header: str = "Game/DATA/FINAL/"
            elif relpath.startswith("Plugins"):
                wad_extract_path_header = ""
            elif relpath.startswith("LeagueClient/Plugins"):
                wad_extract_path_header = "LeagueClient"
            else: #当用户传入某个具体的文件夹作为试验时，直接以relpath作为文件夹抬头（When the user pass some more specific folder as test, take `relpath` as the path header）
                wad_extract_path_header = relpath
            dstpath = os.path.join(target_dir, wad_extract_path_header).replace("\\", "/") #此时dstpath是一个文件夹（Now, `dstpath` is a folder）
            status: int = wad_extract(srcpath, dstpath, patterns = []) #这里之所以没有指定正则表达式，主要是因为尚未确定wad文件中的文本文件的命名模式（The reason why patterns aren't specified is because the pattern of names of text files in wad files isn't figured out yet）
            if status != 0:
                logPrint("解包失败。请等待该步骤结束后查看。\nUnpack failed. Please check it after this step finishes.")
                error_wad_client_files.append(srcpath)
    else:
        logPrint("%s文件夹下的游戏数据已提取到%s目标文件夹中。\nGame data under %s folder have been exported into the target folder %s successfully." %(game_dir, target_dir, game_dir, target_dir))
    if len(error_wad_client_files) > 0:
        logPrint("提取以下wad文件时出错：\nErrors occurred when extracting the following wad file(s):")
        for i in error_wad_client_files:
            logPrint(i)
        logPrint("请尝试使用黑曜石应用检查以上文件是否存在对应的文件树。如果黑曜石能够正常运行，请提交一个议题。\nPlease check these files by Obsidian to see if an organized file tree will be generated. If Obsidian works well, please open an issue.")

def convert_bin_files() -> None:
    '''
    将从.wad.client文件中提取得到的bin文件转换成文本文件，往往是json文件。<br>Transform bin files extracted from .wad.client files into text files, which are always json files.
    '''
    logPrint("请输入一个通过CDTB或者Obsidian等工具提取的客户端文件存放的文件夹路径：\nPlease input the path of a folder that contains the extracted client files using tools like CDTB or Obsidian:")
    while True:
        extract_dir: str = logInput()
        if extract_dir == "":
            continue
        elif extract_dir == chr(4):
            return
        elif not os.path.exists(extract_dir):
            logPrint("目录不存在。请重新输入。\nPath not found. Please try again.")
        elif not os.path.isdir(extract_dir):
            logPrint("请输入一个文件夹。\nPlease enter a folder.")
        else:
            break
    bin_pattern = re.compile(r"Game/DATA/FINAL/.*\.bin$") #这里和cdtb库的正则表达式有区别，因为在游戏目录下，Game文件夹以及Game/DATA文件夹内含有其它内容。下同。另外需要说明，plugins文件夹中的.wad文件中不包含.bin文件。这是通过比对cdtb库的代码和CommunityDragon在线数据库的game和plugins文件夹得出的结论（Here the regular expression is different from that in cdtb library, because under the game directory, there're other content under Game/ and Game/Data/ folders. So are the following regular expressions. Besides, worth mentioning, none of the .wad files under plugins/ folder contain any .bin file. This is concluded by comparison between cdtb library code and the game/ and plugins/ folders in CommunityDragon online database）
    rst_pattern = re.compile(r"Game/DATA/FINAL/(?:.*/)?data/menu/.*\.(txt|stringtable)$")
    atlasInfo_pattern = re.compile(r"Game/DATA/FINAL/clientstates/.*\.cdtb$|Game/DATA/FINAL/assets/items/icons2d/autoatlas/.*/atlas_info\.bin$") #注意到凡是能被atlasInfo_pattern识别到的字符串一定能被bin_pattern识别。所以，识别的顺序很重要（Note that any string matched by `atlasInfo_pattern` will be matched by `bin_pattern`. Hence, the order of finding a match really matters）
    logPrint('请输入版本号：\nPlease input the game version number:\n示例：要查询25.24版本的hash，请输入“1524”。\nExample: To use hashes in v25.24, input "1524".')
    while True:
        game_version = logInput()
        if game_version == "":
            game_version = "1524"
        elif extract_dir == chr(4):
            return
        else:
            try:
                game_version = int(game_version)
            except ValueError:
                logPrint("您的输入有误！请重新输入。\nERROR input! Please try again.")
            else:
                break
    logPrint("正在整理文件列表……\nSorting out a file list ...", print_time = True)
    binfiles_to_convert: list[dict[str, Any]] = []
    error_files: list[str] = []
    for root, dirs, files in os.walk(extract_dir): #这一步转换过程一定会发生修改时间的更新，所以本脚本没有设置“按修改时间更新”的选项（Because the modification time must be updated after this conversion, this program doesn't set an option like "Update according to Modification Time"）
        for file in files:
            srcpath = os.path.join(root, file).replace("\\", "/")
            relpath = os.path.relpath(srcpath, extract_dir).replace("\\", "/")
            if bin_pattern.search(srcpath) or rst_pattern.search(srcpath) or atlasInfo_pattern.search(srcpath):
                body: dict[str, Any] = {}
                src_timestamp: float = os.path.getmtime(srcpath)
                src_date: str = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(src_timestamp))
                src_bytes: int = os.path.getsize(srcpath)
                src_size: str = naturalsize(src_bytes, binary = True)
                body["relpath"] = relpath
                body["src_timestamp"] = src_timestamp
                body["src_date"] = src_date
                body["src_bytes"] = src_bytes
                body["src_size"] = src_size
                binfiles_to_convert.append(body)
    max_index_width: int = 2 * len(str(len(binfiles_to_convert))) + 3
    for i in range(len(binfiles_to_convert)):
        relpath = binfiles_to_convert[i]["relpath"]
        src_date = binfiles_to_convert[i]["src_date"]
        src_size = binfiles_to_convert[i]["src_size"]
        srcpath = os.path.join(extract_dir, relpath).replace("\\", "/")
        dstpath: str = os.path.join(extract_dir, relpath).replace("\\", "/")
        index_str: str = "[%d/%d]" %(i + 1, len(binfiles_to_convert))
        logPrint("%s | 正在转换文件（Converting）： %s\t%s\t%s" %("{0:<{1}}".format(index_str, max_index_width), "{0:<12}".format(src_size), src_date, srcpath), print_time = True)
        if atlasInfo_pattern.search(srcpath): #图册信息文件名模式是二进制文件名模式的一个特殊形式。要先处理特殊情形，再处理一般情形（`atlasInfo_pattern` belongs to `bin_pattern`. First deal with the special case, and then the general case）
            AtlasInfoConvert(srcpath, dstpath + ".json")
        elif bin_pattern.search(srcpath):
            try:
                BinConvert(srcpath, dstpath + ".json")
            except ValueError: #UI.wad.client/ux/tftactivesets.bin
                traceback_info = traceback.format_exc()
                logPrint(traceback_info, write_time = False)
                logPrint("文件%s转换失败！\nFile %s conversion failure!" %(srcpath, srcpath), write_time = False)
                error_files.append(srcpath)
        elif rst_pattern.search(srcpath):
            RstConvert(srcpath, dstpath + ".json", game_version)
    if len(error_files) > 0:
        logPrint("以下%d个文件转换失败。\nThe following %d file(s) fail to be converted." %(len(error_files), len(error_files)), write_time = False)
        for file in error_files:
            logPrint(file)
        logPrint("", write_time = False)

def format_text_files(abortOnDecodeError: bool = False, simpleCopyFixStrategy: bool = True) -> None:
    '''
    将从游戏数据中提取得到的文本文件格式化，并保存到目标文件夹。默认情况是存储库文件夹。<br>Format text files extracted and converted from game data and save the formatted files into the target directory, which is the repository folder by default.
    
    :param abortOnDecodeError: 标记是否在发生文本解码错误时中止程序。默认为假。<br>Marks whether to abort program when a UnicodeDecodeError happens. False by default.
    :type abortOnDecodeError: bool
    :param simpleCopyFixStrategy: 标记发生文本解码错误时，是否直接复制原始文件。默认为真。<br>Marks whether to copy the raw file when a UnicodeDecodeError happens. True by default.
    :type simpleCopyFixStrategy: int
    '''
    logPrint("请指定第一步提取的文件目录。\nPlease specify the directory of files extracted in Step 1.")
    while True:
        extract_dir: str = logInput()
        if extract_dir == "":
            continue
        elif extract_dir == chr(4):
            return
        elif not os.path.exists(extract_dir):
            logPrint("目录不存在。请重新输入。\nPath not found. Please try again.")
        elif not os.path.isdir(extract_dir):
            logPrint("请输入一个文件夹。\nPlease enter a folder.")
        else:
            break
    logPrint("请指定转换后文件的存放目录。\nPlease specify the target directory for converted files.")
    while True:
        target_dir = logInput()
        if target_dir == "":
            target_dir = os.path.expanduser("~/Documents/GitHub/LoL-Wad-Extract-Tencent/Data").replace("\\", "/")
            break
        elif target_dir == chr(4):
            return
        elif os.path.exists(target_dir):
            if os.path.isdir(target_dir):
                break
            else:
                logPrint("您输入的目录已存在，但不是文件夹。请重新输入。\nThe path you entered already exists but isn't a folder. Please try again.")
        else:
            os.makedirs(target_dir)
            logPrint("已创建文件夹。\nFolder created.")
            break
    logPrint("正在整理文件列表……\nSorting out a file list ...", print_time = True)
    updated_files: list[str] = []
    added_files: list[str] = []
    error_files: list[str] = []
    copied_files: list[str] = []
    textfiles_to_convert: list[dict[str, Any]] = []
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            srcpath: str = os.path.join(root, file).replace("\\", "/")
            relpath: str = os.path.relpath(srcpath, extract_dir).replace("\\", "/")
            dstpath: str = os.path.join(target_dir, relpath).replace("\\", "/")
            if isPlainTextPath(file):
                body: dict[str, Any] = {}
                src_timestamp: float = os.path.getmtime(srcpath)
                src_date: str = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(src_timestamp))
                src_bytes: int = os.path.getsize(srcpath)
                src_size: str = naturalsize(src_bytes, binary = True)
                dst_timestamp: float = os.path.getmtime(dstpath) if os.path.exists(dstpath) else 0
                dst_date: str = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(dst_timestamp))
                dst_bytes: int = os.path.getsize(srcpath) if os.path.exists(dstpath) else 0
                dst_size: str = naturalsize(dst_bytes, binary = True)
                body["relpath"] = relpath
                body["src_timestamp"] = src_timestamp
                body["src_date"] = src_date
                body["src_bytes"] = src_bytes
                body["src_size"] = src_size
                body["dst_timestamp"] = dst_timestamp
                body["dst_date"] = dst_date
                body["dst_bytes"] = dst_bytes
                body["dst_size"] = dst_size
                textfiles_to_convert.append(body)
    max_index_width: int = 2 * len(str(len(textfiles_to_convert))) + 3
    for i in range(len(textfiles_to_convert)):
        relpath = textfiles_to_convert[i]["relpath"]
        ext: str = os.path.splitext(relpath)[1]
        src_date = textfiles_to_convert[i]["src_date"]
        src_size = textfiles_to_convert[i]["src_size"]
        srcpath = os.path.join(extract_dir, relpath).replace("\\", "/")
        dst_date = textfiles_to_convert[i]["dst_date"]
        dst_size = textfiles_to_convert[i]["dst_size"]
        dstpath: str = os.path.join(target_dir, relpath).replace("\\", "/")
        index_str: str = "[%d/%d]" %(i + 1, len(textfiles_to_convert))
        logPrint("%s | 正在校对文件（Checking）： %s\t%s\t%s" %("{0:<{1}}".format(index_str, max_index_width), "{0:<12}".format(src_size), src_date, srcpath), print_time = True)
        #第二步涉及较为复杂的格式化操作（Step 2 involves more complex formatting operations）
        encodings = ["utf-8", "ansi"]
        for i in range(len(encodings)):
            encoding = encodings[i]
            try:
                with open(srcpath, "r", encoding = encoding) as fp:
                    text = fp.read()
            except UnicodeDecodeError as e:
                # traceback_info = traceback.format_exc()
                # logPrint(traceback_info, write_time = False)
                if i == len(encodings) - 1:
                    if abortOnDecodeError:
                        raise e
            else:
                break
        else:
            if simpleCopyFixStrategy:
                logPrint("文件解码失败！程序将跳过比对，直接复制该文件。\nFile decode error! The program will skip comparing and directly copy this file instead.", write_time = False)
                os.makedirs(os.path.dirname(dstpath), exist_ok = True)
                shutil.copy2(srcpath, dstpath)
                copied_files.append(srcpath)
            else:
                logPrint("文件解码失败！请等待程序结束后手动比对。\nFile decode error! Please check manually after the program execution finishes.", write_time = False)
                error_files.append(srcpath)
            continue
        if ext == ".json":
            try:
                src_json = json.loads(text)
            except json.decoder.JSONDecodeError as e:
                if "Unexpected UTF-8 BOM (decode using utf-8-sig)" in str(e): #解决方案来自Stack Overflow（The solution comes from https://stackoverflow.com/questions/71025396/asyncio-and-get-unexpected-utf-8-bom）
                    logPrint("文件编码格式错误！正在尝试改用utf-8-sig编码……\nFile decode error! Trying decoding by utf-8-sig ...", write_time = False)
                    src_json = json.loads(text.encode().decode("utf-8-sig"))
                    src: str = json.dumps(src_json, indent = 4, ensure_ascii = False)
                else:
                    logPrint("文件内容解析失败！请等待程序结束后手动比对。\nFile content parsing failure! Please check manually after the program execution finishes.", write_time = False)
                    error_files.append(srcpath)
                    continue
            else:
                src: str = json.dumps(src_json, indent = 4, ensure_ascii = False)
        elif ext == ".js":
            src = jsbeautifier.beautify(text)
        elif ext == ".css":
            src = cssbeautifier.beautify(text)
        elif ext == ".html":
            soup = BeautifulSoup(text, "html.parser")
            src = soup.prettify()
        else:
            src = text.replace("\r", "")
        if os.path.exists(dstpath):
            with open(dstpath, "r", encoding = "utf-8") as fp: #因为下面保存文件时用的是utf-8编码，所以这里只需要用utf-8编码即可（Because in the following files are saved with "utf-8" encoding, here we only need to open with "utf-8" encoding）
                dst = fp.read()
        else:
            dst = None
        if src != dst:
            os.makedirs(os.path.dirname(dstpath), exist_ok = True)
            with open(dstpath, "w", encoding = "utf-8") as fp:
                fp.write(src)
            if dst == None:
                added_files.append(srcpath)
                # logPrint("%s | 已添加文件（Added file）：   %s → %s\t%s → %s\t%s" %("{0:<{1}}".format(index_str, max_index_width), "{0:<12}".format(dst_size), "{0:<12}".format(src_size), dst_date, src_date, srcpath), print_time = True)
            else:
                updated_files.append(srcpath)
                # logPrint("%s | 已更新文件（Updated file）： %s → %s\t%s → %s\t%s" %("{0:<{1}}".format(index_str, max_index_width), "{0:<12}".format(dst_size), "{0:<12}".format(src_size), dst_date, src_date, srcpath), print_time = True)
    if len(updated_files) > 0:
        logPrint("已更新以下%d个文件：\nUpdated the following %d file(s):" %(len(updated_files), len(updated_files)), write_time = False)
        for file in updated_files:
            logPrint(file, write_time = False)
        logPrint("", write_time = False)
    if len(added_files) > 0:
        logPrint("已添加以下%d个文件：\nAdded the following %d file(s):" %(len(added_files), len(added_files)), write_time = False)
        for file in added_files:
            logPrint(file, write_time = False)
        logPrint("", write_time = False)
    if len(copied_files) > 0:
        logPrint("以下%d个文件因解码错误而直接复制！\nThe following %d file(s) are directly copied because of decode error." %(len(copied_files), len(copied_files)), write_time = False)
        for file in copied_files:
            logPrint(file)
        logPrint("", write_time = False)
    if len(error_files) > 0:
        logPrint("以下%d个文件比对失败。请重新比对！\nThe following %d file(s) fail to be checked. Please check manually!" %(len(error_files), len(error_files)), write_time = False)
        for file in error_files:
            logPrint(file)
        logPrint("", write_time = False)
    
def main():
    logPrint("请确保您的磁盘有足够的存储空间。建议剩余空间：200 GB。\nPlease make sure you have enough disk space. Recommended free space: 200 GB.\n在每个步骤输入目录时，输入Ctrl-D以跳过此步骤。\nWhen you enter a directory, submit Ctrl-D to skip this step.\n")
    logPrint("第一步：提取游戏目录中的文件。\nStep 1: Extract files from the game directory.", print_time = True)
    logPrint("请选择要提取的文件：\n0\t退出程序（Exit the program）\n1\t所有文本文件（All text files）\n2\t仅外部文本文件（Only external text files）\n3\t仅wad内文本文件（Only within-wad text files）\n4\t跳过此步骤（Skip this step）")
    while True:
        option = logInput()
        if option == "":
            continue
        elif option[0] == "0":
            return
        elif option[0] == "1":
            copy_text = extract_wad = True
            break
        elif option[0] == "2":
            copy_text, extract_wad = True, False
            break
        elif option[0] == "3":
            copy_text, extract_wad = False, True
            break
        elif option[0] == "4":
            copy_text = extract_wad = False
            break
        else:
            logPrint("您的输入有误！请重新输入。\nERROR input! Please try again.")
    if copy_text or extract_wad:
        extract_data_resource(copy_text = copy_text, extract_wad = extract_wad)
        logPrint('按回车键以继续，或者输入任意非空字符串以退出程序。\nPress Enter to continue, or submit any non-empty string to exit the program.')
        quit_str = logInput()
        quit: bool = bool(quit_str)
        if quit:
            return
    logPrint("第二步：转换二进制文件。\nStep 2: Convert binary files.", print_time = True)
    convert_bin_files()
    logPrint('按回车键以继续，或者输入任意非空字符串以退出程序。\nPress Enter to continue, or submit any non-empty string to exit the program.')
    quit_str = logInput()
    quit: bool = bool(quit_str)
    if quit:
        return
    logPrint("第三步：转换文本文件。\nStep 3: Convert text files.", print_time = True)
    format_text_files()
    logPrint("转换完成。请手动删除第一步和第二步在您指定的目录下产生的中间文件以释放空间。按回车键退出程序。\nConvert finished. Please clear the intermediate files generated during Steps 1 and 2 under the specified directory by yourself to save space. Press Enter to exit.")
    logInput()
    
if __name__ == "__main__":
    main()
    log.write("[The program has exited!]\n")
    log.close()
