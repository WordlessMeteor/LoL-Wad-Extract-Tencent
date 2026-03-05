import cssbeautifier, jsbeautifier, json, os, time, re, shutil, traceback, _io
from humanize import naturalsize
from cdtb.hashes import default_hashfile, HashFile
from cdtb.wad import Wad
from cdtb.binfile import BinFile
from cdtb.rstfile import RstFile, get_hashfile, key_to_hash
from cdtb.export import AtlasInfoConverter
from typing import Any, Literal, Optional
from bs4 import BeautifulSoup

os.makedirs("Data/Update Logs", exist_ok = True)
currentTime = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
log = open(f"Data/Update Logs/{currentTime}.log", "w", encoding = "utf-8")

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

def wad_extract(wad_path: str, output_dir: str, hash_path: Optional[str] = None, patterns: list[str] = [], unknown: Literal["yes", "only", "no"] = "yes", lazy: bool = False) -> int:
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

def extract_data_resource(game_dir: Optional[str] = None, target_dir: Optional[str] = None, copy_text: bool = True, extract_wad: bool = True) -> None:
    '''
    将游戏目录中的文件提取到某个临时文件夹。<br>Extract game files into some temporary folder.
    
    :param copy_text: 指示是否复制.wad.client文件和.wad文件以外的文本文件。默认为真。<br>Represents whether to copy text files not from ".wad.client" and ".wad" files. True by default.
    :type copy_text: bool
    :param extract_wad: 指示是否提取.wad.client文件和.wad文件中的内容。默认为真。<br>Represents whether to extract content from ".wad.client" and ".wad" files. True by default.
    :type extract_wad: bool
    '''
    #参数预处理（Parameter preprocess）
    if not bool(game_dir):
        logPrint("请指定游戏目录：\nPlease specify the game directory:")
        while True:
            game_dir = logInput()
            if game_dir == chr(4):
                return
            elif not os.path.exists(game_dir):
                logPrint("目录不存在。请重新输入。\nPath not found. Please try again.")
            elif not os.path.isdir(game_dir):
                logPrint("请输入一个文件夹。\nPlease enter a folder.")
            else:
                break
    if not bool(target_dir):
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
    #提取文件（Extract files）
    logPrint("正在整理文件列表……\nSorting out a file list ...", print_time = True)
    patterns_to_skip: list[str] = [
        r"Cross/coach/agent/lol_ai_coach/Python311/.*", #Python3.11的标准文件无需查看其变更（Python 3.11's standard files don't need inspecting any change）
        r"Game/Config/Champions/.*",
        r"Game/Config/Global/Recommended/RIOT_ItemSet_\d*\.json",
        r"Game/Config/ItemSets.json",
        r"Game/Logs/.*",
        r"tiny_cache/.*"
    ]
    error_wad_client_files: list[str] = []
    files_to_extract: list[dict[str, Any]] = []
    for root, dirs, files in os.walk(game_dir):
        for file in files:
            srcpath: str = os.path.join(root, file).replace("\\", "/")
            relpath: str = os.path.relpath(srcpath, game_dir).replace("\\", "/")
            if any(map(lambda x: re.search(x, srcpath), patterns_to_skip)):
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
    locale_re = re.compile(r"[a-z]{2}_[A-Z]{2}")
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
            shutil.copy2(srcpath, dstpath) #第一阶段暂且先复制原始文件（For the first phase, temporarily copy the raw files）
        elif isWadPath(relpath):
            logPrint("%s | 正在解包文件（Unpacking）： %s\t%s\t%s" %("{0:<{1}}".format(index_str, max_index_width), "{0:<12}".format(src_size), src_date, srcpath), print_time = True)
            if relpath.startswith("Game/DATA/FINAL/"): #需要特别小心带有语言文化代码后缀的wad文件（Watch out for the wad files with locale suffix）
                wad_extract_path_header: str = "Game/DATA/FINAL/" #通过这个处理，即使Game/DATA/FINAL文件夹下的wad文件分布于不同目录，其内的文件也会按照wad文件组织树来进行组织，并都位于Game/DATA/FINAL文件夹下（By this operation, even if those wad files under Game/DATA/FINAL folder are distributed into different directories, the internal files will follow the organization inside the wad files, and of course, will be exported into the Game/DATA/FINAL after all）
                if matchObj := locale_re.search(os.path.basename(relpath)):
                    locale: str = matchObj.group()
                    wad_extract_path_header = os.path.join(wad_extract_path_header, locale.lower()) #语言文化代码参照CommunityDragon数据库的组织形式，一律小写（Locales are all set lower, following the manner of CommunityDragon database）
            elif relpath.startswith("Plugins"): #适用于国际服（Applies in Riot server）
                wad_extract_path_header = ""
            elif relpath.startswith("LeagueClient/Plugins"): #适用于国服（Applies in Tencent server）
                wad_extract_path_header = "LeagueClient"
            else: #当用户传入某个具体的文件夹作为试验时，直接以relpath作为文件夹抬头（When the user pass some more specific folder as test, take `relpath` as the path header）
                wad_extract_path_header = relpath
            dstpath = os.path.join(target_dir, wad_extract_path_header).replace("\\", "/") #此时dstpath是一个文件夹（Now, `dstpath` is a folder）
            status: int = wad_extract(srcpath, dstpath, patterns = []) #这里之所以没有指定正则表达式，主要是因为尚未确定wad文件中的文本文件的命名模式（The reason why patterns aren't specified is because the pattern of names of text files in wad files isn't figured out yet）
            if status != 0:
                logPrint("解包失败。请等待该阶段结束后查看。\nUnpack failed. Please check it after this phase finishes.")
                error_wad_client_files.append(srcpath)
    else:
        logPrint("%s文件夹下的游戏数据已提取到%s目标文件夹中。\nGame data under %s folder have been exported into the target folder %s successfully." %(game_dir, target_dir, game_dir, target_dir))
    if len(error_wad_client_files) > 0:
        logPrint("提取以下wad文件时出错：\nErrors occurred when extracting the following wad file(s):")
        for i in error_wad_client_files:
            logPrint(i)
        logPrint("请尝试使用黑曜石应用检查以上文件是否存在对应的文件树。如果黑曜石能够正常运行，请提交一个议题。\nPlease check these files by Obsidian to see if an organized file tree will be generated. If Obsidian works well, please open an issue.")

def convert_bin_files(extract_dir: Optional[str] = None, target_dir: Optional[str] = None, game_version: Optional[int] = None) -> None:
    '''
    将从.wad.client文件中提取得到的bin文件转换成文本文件，往往是json文件。与此同时，再复制一份所有文本文件。<br>Transform bin files extracted from .wad.client files into text files, which are always json files. Meanwhile, make another copy of all text files.
    '''
    #参数预处理（Parameter preprocess）
    if not bool(extract_dir):
        logPrint("请输入一个通过CDTB或者Obsidian等工具提取的客户端文件存放的文件夹路径：\nPlease input the path of a folder that contains the extracted client files using tools like CDTB or Obsidian:")
        while True:
            extract_dir = logInput()
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
    if not bool(target_dir):
        logPrint("请输入一个转换后文件的存放文件夹路径：\nPlease input the path of a folder to store the converted files:")
        while True:
            target_dir = logInput()
            if target_dir == "":
                continue
            elif target_dir == chr(4):
                return
            elif not os.path.exists(target_dir):
                logPrint("目录不存在。请重新输入。\nPath not found. Please try again.")
            elif not os.path.isdir(target_dir):
                logPrint("请输入一个文件夹。\nPlease enter a folder.")
            else:
                break
    if not bool(game_version):
        logPrint('请输入版本号：\nPlease input the game version number:\n示例：要查询26.05版本的hash，请输入“1605”。\nExample: To use hashes in v26.05, input "1605".')
        while True:
            game_version_str = logInput()
            if game_version_str == "":
                game_version = 1605
            elif game_version_str == chr(4):
                return
            else:
                try:
                    game_version = int(game_version_str)
                except ValueError:
                    logPrint("您的输入有误！请重新输入。\nERROR input! Please try again.")
                else:
                    break
    #复制文本文件和转换bin文件（Copy text files and convert bin files）
    logPrint("正在整理文件列表……\nSorting out a file list ...", print_time = True)
    bin_pattern = re.compile(r"Game/DATA/FINAL/.*\.bin$") #这里和cdtb库的正则表达式有区别，因为在游戏目录下，Game文件夹以及Game/DATA文件夹内含有其它内容。下同。另外需要说明，plugins文件夹中的.wad文件中不包含.bin文件。这是通过比对cdtb库的代码和CommunityDragon在线数据库的game和plugins文件夹得出的结论（Here the regular expression is different from that in cdtb library, because under the game directory, there're other content under Game/ and Game/DATA/ folders. So are the following regular expressions. Besides, worth mentioning, none of the .wad files under plugins/ folder contain any .bin file. This is concluded by comparison between cdtb library code and the game/ and plugins/ folders in CommunityDragon online database）
    rst_pattern = re.compile(r"Game/DATA/FINAL/(?:.*/)?data/menu/.*\.(txt|stringtable)$")
    atlasInfo_pattern = re.compile(r"Game/DATA/FINAL/clientstates/.*\.cdtb$|Game/DATA/FINAL/assets/items/icons2d/autoatlas/.*/atlas_info\.bin$") #注意到凡是能被atlasInfo_pattern识别到的字符串一定能被bin_pattern识别。所以，识别的顺序很重要（Note that any string matched by `atlasInfo_pattern` will be matched by `bin_pattern`. Hence, the order of finding a match really matters）
    binfiles_to_convert: list[dict[str, Any]] = []
    textfiles_to_copy: list[dict[str, Any]] = []
    error_files: list[str] = []
    for root, dirs, files in os.walk(extract_dir): #这一步转换过程一定会发生修改时间的更新，所以本脚本没有设置“按修改时间更新”的选项（Because the modification time must be updated after this conversion, this program doesn't set an option like "Update according to Modification Time"）
        for file in files:
            srcpath = os.path.join(root, file).replace("\\", "/")
            relpath = os.path.relpath(srcpath, extract_dir).replace("\\", "/")
            if isPlainTextPath(relpath) or bin_pattern.search(srcpath) or rst_pattern.search(srcpath) or atlasInfo_pattern.search(srcpath):
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
                if isPlainTextPath(relpath):
                    textfiles_to_copy.append(body)
                else:
                    binfiles_to_convert.append(body)
    count: int = len(binfiles_to_convert) + len(textfiles_to_copy)
    max_index_width: int = 2 * len(str(len(binfiles_to_convert))) + 3
    for i in range(len(textfiles_to_copy)):
        relpath = textfiles_to_copy[i]["relpath"]
        src_date = textfiles_to_copy[i]["src_date"]
        src_size = textfiles_to_copy[i]["src_size"]
        srcpath = os.path.join(extract_dir, relpath).replace("\\", "/")
        dstpath: str = os.path.join(target_dir, relpath).replace("\\", "/")
        index_str: str = "[%d/%d]" %(i + 1, count)
        logPrint("%s | 正在复制文件（Copying）：   %s\t%s\t%s" %("{0:<{1}}".format(index_str, max_index_width), "{0:<12}".format(src_size), src_date, srcpath), print_time = True)
        os.makedirs(os.path.dirname(dstpath), exist_ok = True)
        shutil.copy2(srcpath, dstpath) #第二阶段也暂且先复制原始文件（For the second phase, temporarily copy the raw files, too）
    for i in range(len(binfiles_to_convert)):
        relpath = binfiles_to_convert[i]["relpath"]
        src_date = binfiles_to_convert[i]["src_date"]
        src_size = binfiles_to_convert[i]["src_size"]
        srcpath = os.path.join(extract_dir, relpath).replace("\\", "/")
        dstpath: str = os.path.join(target_dir, relpath).replace("\\", "/")
        index_str: str = "[%d/%d]" %(len(textfiles_to_copy) + i + 1, count)
        logPrint("%s | 正在转换文件（Converting）： %s\t%s\t%s" %("{0:<{1}}".format(index_str, max_index_width), "{0:<12}".format(src_size), src_date, srcpath), print_time = True)
        os.makedirs(os.path.dirname(dstpath), exist_ok = True)
        if atlasInfo_pattern.search(srcpath): #图册信息文件名模式是二进制文件名模式的一个特殊形式。要先处理特殊情形，再处理一般情形（`atlasInfo_pattern` belongs to `bin_pattern`. First deal with the special case, and then the general case）
            AtlasInfoConvert(srcpath, dstpath + ".json")
        elif bin_pattern.search(srcpath):
            try:
                BinConvert(srcpath, dstpath + ".json")
            except ValueError: #UI.wad.client/ux/tftactivesets.bin
                traceback_info = traceback.format_exc()
                logPrint(traceback_info, write_time = False)
                logPrint("文件%s转换失败！\nFile %s conversion failure!" %(srcpath, srcpath), write_time = False)
                if os.path.exists(dstpath + ".json"):
                    os.remove(dstpath + ".json") #转换失败的文件为空，因此应当删除（Files fail to converted will be empty and thus should be removed）
                error_files.append(srcpath)
        elif rst_pattern.search(srcpath):
            RstConvert(srcpath, dstpath + ".json", game_version)
    if len(error_files) > 0:
        logPrint("以下%d个文件转换失败。\nThe following %d file(s) fail to be converted." %(len(error_files), len(error_files)), write_time = False)
        for file in error_files:
            logPrint(file)
        logPrint("", write_time = False)

def format_text_files(convert_dir: Optional[str] = None, target_dir: Optional[str] = None, abortOnDecodeError: bool = False, simpleCopyFixStrategy: bool = True, delete_old_files: Optional[bool] = None, delete_old_folders: Optional[bool] = None) -> None:
    '''
    将从游戏数据中提取得到的文本文件格式化，并保存到目标文件夹。默认情况是存储库文件夹。<br>Format text files extracted and converted from game data and save the formatted files into the target directory, which is the repository folder by default.
    
    :param abortOnDecodeError: 标记是否在发生文本解码错误时中止程序。默认为假。<br>Marks whether to abort program when a UnicodeDecodeError happens. False by default.
    :type abortOnDecodeError: bool
    :param simpleCopyFixStrategy: 标记发生文本解码错误时，是否直接复制原始文件。默认为真。<br>Marks whether to copy the raw file when a UnicodeDecodeError happens. True by default.
    :type simpleCopyFixStrategy: int
    '''
    #参数预处理（Parameter preprocess）
    if not bool(convert_dir):
        logPrint("请指定第一阶段提取的文件目录。\nPlease specify the directory of files extracted in Phase 1.")
        while True:
            convert_dir = logInput()
            if convert_dir == "":
                continue
            elif convert_dir == chr(4):
                return
            elif not os.path.exists(convert_dir):
                logPrint("目录不存在。请重新输入。\nPath not found. Please try again.")
            elif not os.path.isdir(convert_dir):
                logPrint("请输入一个文件夹。\nPlease enter a folder.")
            else:
                break
    if not bool(target_dir):
        logPrint("请指定格式化后文件的存放目录。\nPlease specify the target directory for formalized files.")
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
    #格式化文件（Format files）
    logPrint("正在整理文件列表……\nSorting out a file list ...", print_time = True)
    updated_files: list[str] = []
    added_files: list[str] = []
    error_files: list[str] = []
    copied_files_OnDecodeError: list[str] = [] #存储因为解码失败而直接复制的文件（Stores files that fail to be decoded and thus directly copied）
    copied_files_OnParsingFailure: list[str] = [] #存储因为内容解析失败而直接复制的文件（Stores files that fail to be parsed content and thus directly copied）
    folders_to_delete: list[str] = [] #统计旧版本存在而新版本不存在的文件夹（Summarize the folders that exist in the old patch but not in the new patch）
    files_to_delete: list[str] = [] #统计旧版本存在而新版本不存在的文件（Summarize the files that exist in the old patch but not in the new patch）
    for root, dirs, files in os.walk(target_dir): #要统计旧版本不存在的文件和文件夹，一定要先把旧版本有的文件和文件夹全部列出来，然后跟新版本比对，新版本有的则逐个从待删除列表中移除（To summarize the files and folders that don't exist in the old patch, the program should first list all the local files and folders in the old patch, then compare them with the new patch and remove each file or folder that exists in the new patch）
        root = os.path.realpath(root).replace("\\", "/")
        if not root in folders_to_delete:
            folders_to_delete.append(root.replace("\\", "/"))
        files_to_delete += list(map(lambda x: os.path.realpath(os.path.join(root, x)).replace("\\", "/"), files))
    textfiles_to_convert: list[dict[str, Any]] = []
    for root, dirs, files in os.walk(convert_dir):
        src_folder: str = root.replace("\\", "/")
        rel_folder: str = os.path.relpath(src_folder, convert_dir).replace("\\", "/")
        dst_folder: str = os.path.realpath(os.path.join(target_dir, rel_folder)).replace("\\", "/")
        for file in files:
            srcpath: str = os.path.join(root, file).replace("\\", "/")
            relpath: str = os.path.relpath(srcpath, convert_dir).replace("\\", "/") #在获取文件的相对路径时，不可能出现“.”作为目录引用（While getting the relative path of a file, the path can't have a "." as the current directory）
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
                if dstpath in files_to_delete:
                    files_to_delete.remove(dstpath)
        if dst_folder in folders_to_delete:
            folders_to_delete.remove(dst_folder)
    max_index_width: int = 2 * len(str(len(textfiles_to_convert))) + 3
    for i in range(len(textfiles_to_convert)):
        relpath = textfiles_to_convert[i]["relpath"]
        ext: str = os.path.splitext(relpath)[1]
        src_date = textfiles_to_convert[i]["src_date"]
        src_size = textfiles_to_convert[i]["src_size"]
        srcpath = os.path.join(convert_dir, relpath).replace("\\", "/")
        dst_date = textfiles_to_convert[i]["dst_date"]
        dst_size = textfiles_to_convert[i]["dst_size"]
        dstpath: str = os.path.join(target_dir, relpath).replace("\\", "/")
        index_str: str = "[%d/%d]" %(i + 1, len(textfiles_to_convert))
        logPrint("%s | 正在校对文件（Checking）： %s\t%s\t%s" %("{0:<{1}}".format(index_str, max_index_width), "{0:<12}".format(src_size), src_date, srcpath), print_time = True)
        #第二阶段涉及较为复杂的格式化操作（Phase 2 involves more complex formatting operations）
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
                copied_files_OnDecodeError.append(srcpath)
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
                    if simpleCopyFixStrategy:
                        logPrint("文件内容解析失败！程序将跳过比对，直接复制该文件。\nFile content parsing failure! The program will skip comparing and directly copy this file instead.", write_time = False)
                        os.makedirs(os.path.dirname(dstpath), exist_ok = True)
                        shutil.copy2(srcpath, dstpath)
                        copied_files_OnParsingFailure.append(srcpath)
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
    if len(copied_files_OnDecodeError) > 0:
        logPrint("以下%d个文件因解码错误而直接复制！\nThe following %d file(s) are directly copied because of decode error." %(len(copied_files_OnDecodeError), len(copied_files_OnDecodeError)), write_time = False)
        for file in copied_files_OnDecodeError:
            logPrint(file)
        logPrint("", write_time = False)
    if len(copied_files_OnParsingFailure) > 0:
        logPrint("以下%d个文件因文件内容解析错误而直接复制！\nThe following %d file(s) are directly copied because of content parsing error." %(len(copied_files_OnParsingFailure), len(copied_files_OnParsingFailure)), write_time = False)
        for file in copied_files_OnParsingFailure:
            logPrint(file)
        logPrint("", write_time = False)
    if len(error_files) > 0:
        logPrint("以下%d个文件比对失败。请重新比对！\nThe following %d file(s) fail to be checked. Please check manually!" %(len(error_files), len(error_files)), write_time = False)
        for file in error_files:
            logPrint(file)
        logPrint("", write_time = False)
    if len(files_to_delete) > 0:
        if delete_old_files == None:
            logPrint("以下%d个文件不存在于新版本中。是否永久删除这些文件？（输入任意非空字符串删除，否则不删除。）\nThe following %d file(s) don't exist in the new patch. Do you want to delete them? (Submit any non-empty string to delete, or null to refuse deleting the files.)\n" %(len(files_to_delete), len(files_to_delete)) + "\n".join(files_to_delete), write_time = False)
            delete_file_str: str = logInput()
            delete_file: bool = bool(delete_file_str)
        else:
            logPrint("正在删除以下%d个文件……\nDeleting the following %d file(s) ...\n" %(len(files_to_delete), len(files_to_delete)) + "\n".join(files_to_delete), write_time = False)
            delete_file = delete_old_files
        if delete_file:
            for file in files_to_delete:
                try:
                    os.remove(file)
                except FileNotFoundError:
                    pass
        logPrint("", write_time = False)
    if len(folders_to_delete) > 0:
        if delete_old_folders == None:
            logPrint("以下%d个文件夹不存在于新版本中。是否永久删除这些文件夹？（输入任意非空字符串删除，否则不删除。）\nThe following %d folder(s) don't exist in the new patch. Do you want to delete them? (Submit any non-empty string to delete, or null to refuse deleting the folders.)\n" %(len(folders_to_delete), len(folders_to_delete)) + "\n".join(folders_to_delete), write_time = False)
            delete_folder_str: str = logInput()
            delete_folder: bool = bool(delete_folder_str)
        else:
            logPrint("正在删除以下%d个文件夹……\nDeleting the following %d folder(s) ...\n" %(len(folders_to_delete), len(folders_to_delete)) + "\n".join(folders_to_delete), write_time = False)
            delete_folder = delete_old_folders
        if delete_folder:
            for folder in folders_to_delete:
                try:
                    shutil.rmtree(folder)
                except FileNotFoundError:
                    pass
        logPrint("", write_time = False)

def delete_intermediate_files(extract_dir: Optional[str] = None, convert_dir: Optional[str] = None) -> None:
    #参数预处理（Parameter preprocess）
    if not bool(extract_dir):
        logPrint("请指定第一阶段提取的文件目录。\nPlease specify the directory of files extracted into in Phase 1.")
        while True:
            extract_dir = logInput()
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
    extract_dir = extract_dir.replace("\\", "/")
    if not bool(convert_dir):
        logPrint("请指定第二阶段转换的文件目录。\nPlease specify the directory of files converted into in Phase 2.")
        while True:
            convert_dir = logInput()
            if convert_dir == "":
                continue
            elif convert_dir == chr(4):
                return
            elif not os.path.exists(convert_dir):
                logPrint("目录不存在。请重新输入。\nPath not found. Please try again.")
            elif not os.path.isdir(convert_dir):
                logPrint("请输入一个文件夹。\nPlease enter a folder.")
            else:
                break
    convert_dir = convert_dir.replace("\\", "/")
    #删除临时文件（Delete intermediate files）
    logPrint(f"正在删除文件夹（Deleting folder）： {extract_dir}\n请耐心等待。此过程将花费至少5分钟。\nPlease wait in patience. This process will take at least 5 minutes.")
    while os.path.exists(extract_dir) and os.path.isdir(extract_dir):
        try:
            shutil.rmtree(extract_dir)
        except PermissionError:
            logPrint("拒绝访问：另一个程序正在使用此文件，进程无法访问。请检查文件占用情况后按回车键重试，或者输入任意非空字符串以取消删除。\nPermission Error: The process cannot access the file, because it's being used by another process. Please check the file occupation and press Enter to try again, or submit any non-empty string to cancel deletion.")
            cancel_str: str = logInput()
            cancel: bool = bool(cancel_str)
            if cancel:
                break
    logPrint(f"正在删除文件夹（Deleting folder）： {convert_dir}\n请耐心等待。此过程将花费少于1分钟。\nPlease wait in patience. This process will take less than 1 minute.")
    while os.path.exists(convert_dir) and os.path.isdir(convert_dir):
        try:
            shutil.rmtree(convert_dir)
        except PermissionError:
            logPrint("拒绝访问：另一个程序正在使用此文件，进程无法访问。请检查文件占用情况后按回车键重试，或者输入任意非空字符串以取消删除。\nPermission Error: The process cannot access the file, because it's being used by another process. Please check the file occupation and press Enter to try again, or submit any non-empty string to cancel deletion.")
            cancel_str: str = logInput()
            cancel: bool = bool(cancel_str)
            if cancel:
                break

def main():
    logPrint("请确保您的磁盘有足够的存储空间。建议剩余空间：200 GB。\nPlease make sure you have enough disk space. Recommended free space: 200 GB.\n在自动化流程设置参数时，输入多个Ctrl-D字符以回退多步。\nWhen you're setting parameters for the automatic procedures, submit multiple Ctrl-D characters to recall multiple steps.\n在分步执行流程中，输入Ctrl-D字符以返回上一层。\nWhen you select stepwise execution, submit Ctrl-D character to return to the last step.\n")
    game_version_default: int = 1605
    game_dir_latest_default: str = "C:/WeGameApps/英雄联盟"
    extract_dir_latest_default: str = "D:/Workspace/LoL-Wad-Extract-Tencent/latest"
    convert_dir_latest_default: str = "D:/Workspace/LoL-Wad-Extract-Tencent/latest-text"
    target_dir_latest_default: str = os.path.expanduser("~/Documents/GitHub/LoL-Wad-Extract-Tencent/Data/latest").replace("\\", "/")
    game_dir_pbe_default: str = "C:/WeGameApps/英雄联盟体验服"
    extract_dir_pbe_default: str = "D:/Workspace/LoL-Wad-Extract-Tencent/pbe"
    convert_dir_pbe_default: str = "D:/Workspace/LoL-Wad-Extract-Tencent/pbe-text"
    target_dir_pbe_default: str = os.path.expanduser("~/Documents/GitHub/LoL-Wad-Extract-Tencent/Data/pbe").replace("\\", "/")
    behavior_str: str = "请选择行为：\nPlease select a behavior:\n0\t退出程序（Exit the program）\n1\t提取和转换正式服的所有文本文件（Extract and convert text files from latest game data）\n2\t提取和转换测试服的所有文本文件（Extract and convert text files from pbe game data）\n3\t分步执行（Execute stepwise）"
    logPrint(behavior_str)
    while True:
        mode = logInput()
        if mode == "":
            continue
        elif mode[0] == "0":
            break
        elif mode[0] == "1" or mode[0] == "2":
            #参数初始化（Parameter initialization）
            useLatest: bool = mode[0] == "1" #代表是否使用正式服版本线的游戏文件（Represents whether to use game files of live patchline）
            productName_zh: str = "正式服" if useLatest else "体验服" #用于中文步骤提示（Used in step hints in Chinese）
            productName_en: str = "latest" if useLatest else "pbe" #用于英文步骤提示（Used in step hints in English）
            game_dir_default: str = game_dir_latest_default if useLatest else game_dir_pbe_default #指定默认游戏目录（Specifies the default game directory to copy text files and read wad files from）
            extract_dir_default: str = extract_dir_latest_default if useLatest else extract_dir_pbe_default #指定默认提取目录，用于存放从游戏目录中复制的文本文件和从wad文件中提取的所有文件（Specifies the default extraction directory to store text files copied from game directory and all files extracted from wad files）
            convert_dir_default: str = convert_dir_latest_default if useLatest else convert_dir_pbe_default #指定默认转换目录，用于存放从提取目录中转换的标准化文本文件（Specifies the default convert directory to store formalized text files converted from extraction directiory）
            target_dir_default: str = target_dir_latest_default if useLatest else target_dir_pbe_default #指定默认生成目录，用于存放所有格式化后的文本文件（Specifies the default generation directory to store all formatted text files）
            game_dir: str = "" #代表程序实际使用的游戏目录（Represents the game directory to be used actually）
            extract_dir: str = "" #代表程序实际使用的提取目录（Represents the extraction directory to be used actually）
            convert_dir: str = "" #代表程序实际使用的转换目录（Represents the convert directory to be used actually）
            game_version: int = 0 #代表游戏版本正整数（Represents the game version integer）
            target_dir: str = "" #代表程序实际使用的生成目录（Represents the generation directory to be used actually）
            step: int = 1 #标记步骤序号（Denotes the step number）
            allTextExtract: bool = False #代表是否提取所有文本文件，包括wad外和wad内的。当该变量的值为真时，copy_text和extract_wad置为真（Represents whether to extract all text files, including both beyond-wad and within-wad. When this variable's value is True, the values of `copy_text` and `extract_wad` are set as True）
            copy_text: bool = False #代表是否提取wad外的所有文本文件（Represents whether to extract all text files outside the wad files）
            extract_wad: bool = False #代表是否提取wad内的所有文件（Represents whether to extract all files within the wad files）
            delete_old_files_and_folders: bool = False #代表是否删除旧版本中存在但新版本中不存在的文件和文件夹（Represents whether to delete the files and folders that exist in the old patch but not in the new patch）
            back: bool = False #代表是否返回上一层（Represents whether to return to the last step）
            #参数设置（Parameter configuration）
            while step <= 9:
                if step <= 0:
                    back = True
                    break
                elif step == 1:
                    logPrint(f"第一步：请指定英雄联盟国服{productName_zh}游戏目录：\nStep 1: Please specify the game directory of League of Legends Tencent {productName_en} patchline:\n当前默认目录（Current default directory）： {game_dir_default}")
                    while True:
                        game_dir: str = logInput()
                        if game_dir == "":
                            game_dir = game_dir_default
                        if chr(4) in game_dir:
                            step -= 1 + game_dir.count(chr(4))
                            break
                        elif not os.path.exists(game_dir):
                            logPrint("目录不存在。请重新输入。\nPath not found. Please try again.")
                        elif not os.path.isdir(game_dir):
                            logPrint("请输入一个文件夹。\nPlease enter a folder.")
                        else:
                            break
                elif step == 2:
                    logPrint(f"第二步：请指定从英雄联盟国服{productName_zh}的游戏文件中提取的文件的存放目录：\nStep 2: Please specify the extraction directory to store files extracted from League of Legends Tencent game files of {productName_en} patchline:\n当前默认目录（Current default directory）： {extract_dir_default}")
                    while True:
                        extract_dir: str = logInput()
                        if extract_dir == "":
                            extract_dir = extract_dir_default
                        if chr(4) in extract_dir:
                            step -= 1 + extract_dir.count(chr(4))
                            break
                        elif os.path.exists(extract_dir):
                            if os.path.isdir(extract_dir):
                                break
                            else:
                                logPrint("您输入的目录已存在，但不是文件夹。请重新输入。\nThe path you entered already exists but isn't a folder. Please try again.")
                        else:
                            os.makedirs(extract_dir)
                            logPrint("已创建文件夹。\nFolder created.")
                            break
                elif step == 3:
                    logPrint(f"第三步：请指定从英雄联盟国服{productName_zh}的游戏文件中提取的文件转换后的目录：\nStep 3: Please specify the convert directory to store files converted from those extracted from League of Legends Tencent game files of {productName_en} patchline:\n当前默认目录（Current default directory）： {convert_dir_default}")
                    while True:
                        convert_dir: str = logInput()
                        if convert_dir == "":
                            convert_dir = convert_dir_default
                        if chr(4) in convert_dir:
                            step -= 1 + convert_dir.count(chr(4))
                            break
                        elif os.path.exists(convert_dir):
                            if os.path.isdir(convert_dir):
                                break
                            else:
                                logPrint("您输入的目录已存在，但不是文件夹。请重新输入。\nThe path you entered already exists but isn't a folder. Please try again.")
                        else:
                            os.makedirs(convert_dir)
                            logPrint("已创建文件夹。\nFolder created.")
                            break
                elif step == 4:
                    logPrint(f'第四步：请输入英雄联盟国服{productName_zh}的游戏版本号：\nStep 4: Please input the game version number of League of Legends Tencent {productName_en} patchline:\n示例：要查询26.05版本的hash，请输入“1605”。\nExample: To use hashes in v26.05, input "1605".')
                    while True:
                        game_version_str = logInput()
                        if game_version_str == "":
                            game_version = game_version_default
                            break
                        if chr(4) in game_version_str:
                            step -= 1 + game_version_str.count(chr(4))
                            break
                        else:
                            try:
                                game_version = int(game_version_str)
                            except ValueError:
                                logPrint("您的输入有误！请重新输入。\nERROR input! Please try again.")
                            else:
                                break
                elif step == 5:
                    logPrint(f"第五步：请指定从英雄联盟国服{productName_zh}的游戏文件转换后文件的存放目录。\nStep 5: Please specify the target directory for files converted from League of Legends Tencent game files of {productName_en} patchline.\n当前默认目录（Current default directory）： {target_dir_default}")
                    while True:
                        target_dir = logInput()
                        if target_dir == "":
                            target_dir = target_dir_default
                        if chr(4) in target_dir:
                            step -= 1 + target_dir.count(chr(4))
                            break
                        elif os.path.exists(target_dir):
                            if os.path.isdir(target_dir):
                                break
                            else:
                                logPrint("您输入的目录已存在，但不是文件夹。请重新输入。\nThe path you entered already exists but isn't a folder. Please try again.")
                        else:
                            os.makedirs(target_dir)
                            logPrint("已创建文件夹。\nFolder created.")
                            break
                elif step == 6:
                    logPrint(f"第六步：是否提取和转换所有文本文件？\nStep 6: Do you want to extract and convert all text files?\n☆1\t是（Yes）\n2\t否（No）")
                    while True:
                        allTextExtract_str: str = logInput()
                        if allTextExtract_str == "":
                            allTextExtract_str = "1"
                        if chr(4) in allTextExtract_str:
                            step -= 1 + allTextExtract_str.count(chr(4))
                            break
                        elif allTextExtract_str[0] == "1" or allTextExtract_str[0] == "2":
                            allTextExtract: bool = allTextExtract_str[0] == "1"
                            break
                        else:
                            logPrint("您的输入有误！请重新输入。\nERROR input! Please try again.")
                elif step == 7:
                    if not allTextExtract:
                        logPrint("第七步：是否提取外部文本文件？\nStep 7: Do you want to extract non-wad text files?\n☆1\t是（Yes）\n2\t否（No）")
                        while True:
                            copy_text_str: str = logInput()
                            if copy_text_str == "":
                                copy_text_str = "1"
                            if chr(4) in copy_text_str:
                                step -= 1 + copy_text_str.count(chr(4))
                                break
                            elif copy_text_str[0] == "1" or copy_text_str[0] == "2":
                                copy_text: bool = copy_text_str[0] == "1"
                                break
                            else:
                                logPrint("您的输入有误！请重新输入。\nERROR input! Please try again.")
                elif step == 8:
                    if not allTextExtract:
                        logPrint("第八步：是否提取wad内文本文件？\nStep 8: Do you want to extract within-wad text files?\n☆1\t是（Yes）\n2\t否（No）")
                        while True:
                            copy_text_str: str = logInput()
                            if copy_text_str == "":
                                copy_text_str = "1"
                            if chr(4) in copy_text_str:
                                step -= 1 + copy_text_str.count(chr(4))
                                break
                            elif copy_text_str[0] == "1" or copy_text_str[0] == "2":
                                copy_text: bool = copy_text_str[0] == "1"
                                break
                            else:
                                logPrint("您的输入有误！请重新输入。\nERROR input! Please try again.")
                elif step == 9:
                    logPrint("第九步：是否自动删除新版本不存在的文件和文件夹？\nStep 9: Do you want the program to automatically delete the files and folders that don't exist in the new patch?\n☆1\t是（Yes）\n2\t否（No）")
                    while True:
                        delete_old_files_and_folders_str: str = logInput()
                        if delete_old_files_and_folders_str == "":
                            delete_old_files_and_folders = True
                            break
                        if chr(4) in delete_old_files_and_folders_str:
                            step -= (3 if allTextExtract else 1) + delete_old_files_and_folders_str.count(chr(4))
                            break
                        elif delete_old_files_and_folders_str[0] == "1" or delete_old_files_and_folders_str[0] == "2":
                            delete_old_files_and_folders = delete_old_files_and_folders_str[0] == "1"
                            break
                        else:
                            logPrint("您的输入有误！请重新输入。\nERROR input! Please try again.")
                else:
                    logPrint("发现异常步骤！请联系开发人员检查和调试代码。\nAn unexpected step is found! Please contact the developer to check and debug the code.")
                    back = True
                    break
                step += 1
            if back:
                logPrint(behavior_str)
                continue
            #参数后处理（Parameter post-operation）
            if allTextExtract:
                copy_text = extract_wad = True
            #运行主要流程（Run main procedures）
            logPrint("第一阶段：提取游戏目录中的文件。\nPhase 1: Extract files from the game directory.", print_time = True)
            extract_data_resource(game_dir = game_dir, target_dir = extract_dir, copy_text = copy_text, extract_wad = extract_wad)
            logPrint("第二阶段：转换二进制文件。\nPhase 2: Convert binary files.", print_time = True)
            convert_bin_files(extract_dir = extract_dir, target_dir = convert_dir, game_version = game_version)
            logPrint("第三阶段：转换文本文件。\nPhase 3: Convert text files.", print_time = True)
            format_text_files(convert_dir = convert_dir, target_dir = target_dir, delete_old_files = delete_old_files_and_folders, delete_old_folders = delete_old_files_and_folders)
            logPrint("第四阶段：删除中间文件。\nPhase 4: Delete intermediate files.", print_time = True)
            delete_intermediate_files(extract_dir = extract_dir, convert_dir = convert_dir)
        elif mode[0] == "3":
            #参数初始化（Parameter initialization）
            copy_text = extract_wad = False
            #参数设置（Parameter configuration）
            #运行主要流程（Run main procedures）
            logPrint("第一阶段：提取游戏目录中的文件。\nPhase 1: Extract files from the game directory.", print_time = True)
            logPrint("请选择要提取的文件：\n0\t返回上一层（Return to the last step）\n1\t所有文本文件（All text files）\n2\t仅外部文本文件（Only external text files）\n3\t仅wad内文本文件（Only within-wad text files）\n4\t跳过此步骤（Skip this step）")
            while True:
                back: bool = False
                option = logInput()
                if option == "":
                    continue
                elif option[0] == "0":
                    back = True
                    break
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
            if back:
                logPrint(behavior_str)
                continue
            if copy_text or extract_wad:
                extract_data_resource(copy_text = copy_text, extract_wad = extract_wad)
                logPrint('按回车键以继续，或者输入任意非空字符串以返回上一层。\nPress Enter to continue, or submit any non-empty string to return to the last step.')
                back_str = logInput()
                back: bool = bool(back_str)
                if back:
                    logPrint(behavior_str)
                    continue
            logPrint("第二阶段：转换二进制文件。\nPhase 2: Convert binary files.", print_time = True)
            convert_bin_files()
            logPrint('按回车键以继续，或者输入任意非空字符串以返回上一层。\nPress Enter to continue, or submit any non-empty string to return to the last step.')
            back_str = logInput()
            back: bool = bool(back_str)
            if back:
                logPrint(behavior_str)
                continue
            logPrint("第三阶段：转换文本文件。\nStep 3: Convert text files.", print_time = True)
            format_text_files()
            logPrint("转换完成。请手动删除第一阶段和第二阶段在您指定的目录下产生的中间文件以释放空间。按回车键继续。\nConvert finished. Please clear the intermediate files generated during Phases 1 and 2 under the specified directory by yourself to save space. Press Enter to continue.")
            logInput()
        else:
            logPrint("您的输入有误！请重新输入。\nERROR input! Please try again.")
            continue
        logPrint(behavior_str)
    
if __name__ == "__main__":
    main()
    log.write("[The program has exited!]\n")
    log.close()
