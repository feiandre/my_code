import io
import os
import logging
import json

# 代码语句分类
CODE = 'code'
BLANK = 'blank'
INLINE = 'inline'
BLOCK = 'block'

# 语言类型 语言类型和备注字符可以自定义
languages = [
    {
    'lang': 'python',
    'for_short': 'python',
    'suffix': 'py',
    'inline_mark': '#',
    'block_mark': [("'''", "'''"),('"""','"""'),("r'''", "'''"),('r"""','"""')]
    },
    {
    'lang': 'sql',
    'for_short': 'sql',
    'suffix': 'sql',
    'inline_mark': '--',
    'block_mark': [('/*', '*/')]
    },
    {
    'lang': 'javascript',
    'for_short': 'js',
    'suffix': 'js',
    'inline_mark': r"//",
    'block_mark': [('/*', '*/')]
    }
]

class CodeCounter:

    def __init__(self, lang='python', is_cum=False, res_type='dict'):
        """初始化代码计数实例
            :param version: 版本号 可空
            :param lang: 默认python语言
                language字典里定义的语言类型 python, sql, javascript, ...
            :param cum: 代码行数是否累计计数
            :param res_type:统计结果返回形式: 默认返回字典形式
                dict: {'language': 'python', 'code': 6, 'blank': 1, 'inline': 1, 'block': 8, 'remark': 9}
                list: [['language', 'code', 'blank', 'inline', 'block', 'remark'], ['python', 6, 1, 1, 8, 9]]
                tuple: (('language', 'code', 'blank', 'inline', 'block', 'remark'), ('python', 6, 1, 1, 8, 9))
                json: {"language": "python", "code": 6, "blank": 1, "inline": 1, "block": 8, "remark": 9}
        """
        self.code_count = 0 # 代码
        self.blank_count = 0 # 空行
        self.inline_remark_count = 0
        self.block_remark_count = 0
        self.total_remark_count = 0 # 注释
        self.is_cum = is_cum
        self.language = [l for l in languages if l['lang'] == lang or l['for_short'] == lang][0]
        self.type = res_type
            


    def count_code(self, content, language=None, depends_on_file=False):
        """统计script文件中代码行数
            :param content: 代码内容或者代码文本文件或者为文件描述符
            :param language: 传入的代码的语言类型 默认为实例初始化时的语言
            :param depends_on_file: 是否以文件后缀判断语言类型, 默认 否,此项为真时,优先级比languange参数级别高
        """
        if self.is_cum == False:
            self.code_count = 0 # 代码
            self.blank_count = 0 # 空行
            self.inline_remark_count = 0
            self.block_remark_count = 0
            self.total_remark_count = 0 # 注释

        if isinstance(content, io.TextIOWrapper):
            lines = content.read()
        elif os.path.isfile(content):
            with open(content, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = io.StringIO(content)
        
        if depends_on_file == False:
            if language is None:
                lang = self.language
            else:
                lang = [l for l in languages if l['lang'] == language or l['for_short'] == language][0]
        else:
            ext = os.path.splitext(content)[-1][1:]
            lang = [l for l in languages if l['suffix'] == ext][0]

        def is_code(line):
            """先判断文本行是否是代码行
                            或者空白行
                            或者行内注释
                :param line: 一行文本行
            """
            if line is None:
                return BLANK
            elif line.strip().startswith(lang['inline_mark']):
                return INLINE
            elif len(line.strip()) == 0:
                return BLANK
            else:
                return CODE
        

        block_lines = []
        start = ''
        end = ''
        for line in lines:
            if is_code(line) == INLINE:
                self.inline_remark_count += 1
                logging.debug('inline : ' + str(self.inline_remark_count) + ' - ' + line)
            elif is_code(line) == BLANK:
                self.blank_count += 1
                logging.debug('blank  : ' + str(self.blank_count) + ' - ' + line)
            elif is_code(line) == CODE:
                if  len(block_lines) == 0:
                    for block_remark in lang['block_mark']:
                        start = block_remark[0]
                        end = block_remark[1]

                        if line.strip().startswith(start):
                            block_lines.append(line)
                            self.block_remark_count += 1
                            logging.debug('block_s: ' + str(self.block_remark_count) + ' - ' + line)
                            break
                    else:
                        self.code_count += 1
                        logging.debug('code   : ' + str(self.code_count)  + ' - ' + line)
                elif len(block_lines) > 0 and line.strip().endswith(end):
                    self.block_remark_count += 1
                    logging.debug('block_e: ' + str(self.block_remark_count) + ' - ' + line)
                    block_lines = []
                elif len(block_lines) > 0 and not line.strip().endswith(end):
                    self.block_remark_count += 1
                    logging.debug('block  : ' + str(self.block_remark_count) + ' - ' + line)
        self.remark_count = self.inline_remark_count + self.block_remark_count
        if self.type == 'dict' or self.type == 'json':
            res = {
                'language': lang['lang'], 
                'code': self.code_count, 
                'blank': self.blank_count, 
                'inline': self.inline_remark_count, 
                'block': self.block_remark_count, 
                'remark': self.remark_count
            }
        if self.type == 'list':
            res = [['language', 'code', 'blank', 'inline', 'block', 'remark'],
                [lang['lang'], 
                self.code_count,
                self.blank_count, 
                self.inline_remark_count,
                self.block_remark_count, 
                self.remark_count]
            ]
        if self.type == 'tuple':
            res =  (
                ('language', 
                'code', 
                'blank', 
                'inline', 
                'block', 
                'remark'), 
                (lang['lang'], 
                self.code_count,
                self.blank_count, 
                self.inline_remark_count,
                self.block_remark_count, 
                self.remark_count)
            )
        if self.type == 'json':
            res = json.dumps(res)

        return res

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format='%(lineno)d - %(message)s')
    counter = CodeCounter(res_type='json')
    res = counter.count_code("code_demo.py")
    print(res)
