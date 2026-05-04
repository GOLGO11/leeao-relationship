from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


SOURCE_DIR = "《大李敖全集5.0》（wjm_tcy版）分章节"


SINGLE_SURNAMES = (
    "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜"
    "戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳鲍史唐费"
    "廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄"
    "和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴宋庞熊纪舒屈项祝董梁杜"
    "阮蓝闵席季麻强贾路娄危江童佟颜郭梅盛林刁钟徐邱骆高夏蔡田胡凌霍虞"
    "万支柯昝管卢莫经房裘缪干解应宗丁宣邓郁单杭洪包诸左石崔吉龚程邢"
    "裴陆荣翁荀羊於惠甄曲家封芮羿储靳汲邴糜松井段富巫乌焦巴弓牧隗山"
    "谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘斜厉戎祖武符刘景詹束龙叶幸"
    "司韶郜黎蓟薄印宿白怀蒲台从鄂索咸籍赖卓蔺屠蒙池乔阴胥能苍闻莘党"
    "翟谭贡劳逄姬申扶堵冉宰郦雍却璩桑桂濮牛寿通边扈燕冀郏浦尚农温别"
    "庄晏柴瞿阎充慕连茹习宦艾鱼容向古易慎戈廖庾终暨居衡步都耿满弘匡"
    "国文寇广禄阙东欧殳沃利蔚越夔隆师巩厍聂晁勾敖融冷訾辛阚那简饶空"
    "曾毋沙乜养鞠须丰巢关蒯相查後荆红游竺权逯盖益桓公"
)

COMPOUND_SURNAMES = (
    "欧阳", "太史", "端木", "上官", "司马", "东方", "独孤", "南宫", "万俟", "闻人",
    "夏侯", "诸葛", "尉迟", "公羊", "赫连", "澹台", "皇甫", "宗政", "濮阳", "公冶",
    "太叔", "申屠", "公孙", "慕容", "仲孙", "钟离", "长孙", "宇文", "司徒", "鲜于",
    "司空", "闾丘", "子车", "亓官", "司寇", "巫马", "公西", "颛孙", "壤驷", "公良",
    "漆雕", "乐正", "宰父", "谷梁", "拓跋", "夹谷", "轩辕", "令狐", "段干", "百里",
    "呼延", "东郭", "南门", "羊舌", "微生", "公户", "公玉", "公仪", "梁丘", "公仲",
    "公上", "公门", "公山", "公坚", "左丘", "公伯", "西门", "公祖", "第五", "公乘",
    "贯丘", "公皙", "南荣", "东里", "东宫", "仲长", "子书", "子桑", "即墨", "达奚",
    "褚师",
)

FOREIGN_AND_HISTORICAL = {
    "爱因斯坦", "苏格拉底", "柏拉图", "亚里士多德", "拿破仑", "马克思", "恩格斯", "列宁",
    "斯大林", "希特勒", "达尔文", "罗素", "伏尔泰", "卢梭", "康德", "黑格尔", "尼采",
    "莎士比亚", "歌德", "托尔斯泰", "陀思妥耶夫斯基", "林肯", "华盛顿", "罗斯福", "丘吉尔",
    "凯撒", "哥伦布", "伽利略", "牛顿", "释迦牟尼", "耶稣", "穆罕默德", "孔子", "孟子",
    "老子", "庄子", "墨子", "荀子", "韩非", "司马迁", "班固", "陶渊明", "李白", "杜甫",
    "白居易", "苏东坡", "王安石", "朱熹", "王阳明", "曹操", "诸葛亮", "岳飞", "文天祥",
    "鲁迅", "胡适", "孙中山", "蒋介石", "毛泽东", "周恩来",
}

SPIRITUAL_ONLY = {
    "爱因斯坦", "苏格拉底", "柏拉图", "亚里士多德", "拿破仑", "马克思", "恩格斯", "列宁",
    "斯大林", "希特勒", "达尔文", "罗素", "伏尔泰", "卢梭", "康德", "黑格尔", "尼采",
    "莎士比亚", "歌德", "托尔斯泰", "陀思妥耶夫斯基", "林肯", "华盛顿", "罗斯福", "丘吉尔",
    "凯撒", "哥伦布", "伽利略", "牛顿", "释迦牟尼", "耶稣", "穆罕默德", "孔子", "孟子",
    "老子", "庄子", "墨子", "荀子", "韩非", "司马迁", "班固", "陶渊明", "李白", "杜甫",
    "白居易", "苏东坡", "王安石", "朱熹", "王阳明", "曹操", "诸葛亮", "岳飞", "文天祥",
    "鲁迅",
}

ALIASES = {
    "胡适之": "胡适",
    "王世傑": "王世杰",
    "相湘": "吴相湘",
    "姚老头": "姚从吾",
    "周树人": "鲁迅",
    "东方望": "汪梦湘",
    "马戈": "马宏祥",
    "施启杨": "施启扬",
    "詹永傑": "詹永杰",
    "景生二": "李景生",
    "严师母": "林蒨",
    "素馨": "李文钧",
    "项廼光": "项迺光",
    "阉鸡": "李盛渊",
}

ALWAYS_NAMES = {
    "姚从吾", "蔡元培", "周作人", "钱玄同", "沈尹默", "陶晋生", "严以侨",
    "李政一", "黄中国", "高时运", "李国龙", "崔积泽",
    "周弘", "景新汉", "马宏祥", "白绍康", "华昌平", "李华俊", "陈又亮",
    "祝庭生", "张克斌", "袁祝泰", "朱广诚", "黄锡昌", "施启扬", "佟耀勋",
    "阙至正", "孙英善", "林淑美", "杨祖燕", "杨世彭", "袁天中", "王尚义",
    "陈良榘", "王曾才", "李耀祖", "王文振", "陈士宽", "施敏雄", "毛树清", "林钟雄",
    "陈立峰", "李方桂", "余光中", "札奇斯钦", "史为鉴", "庄申", "李其泰",
    "陈正澄", "钱穆", "顾翊群", "郑学稼", "胡传厚", "聂华苓", "潘琦君",
    "徐钟珮", "张明", "张兰熙", "曾虚白",
    "陶涤亚", "项迺光", "项廼光", "周道济", "王洸", "屠炳春", "任卓宣",
    "柴松林", "魏萼", "邬昆如", "魏以之", "史与为", "胡汝森", "陈启天",
    "于长城", "于长庚", "林蒨", "李盛渊", "俞中兴",
}

NONSTANDARD_NAMES = {
    "小屯", "小蕾", "勘勘", "谌谌", "素馨", "小八", "阉鸡", "札奇斯钦", "李其泰",
}

CURATED_IDENTITIES = {
    "胡适": ["correspondence", "meeting", "academic"],
    "姚从吾": ["teacher_student", "academic"],
    "陶希圣": ["meeting", "politician", "public_debate", "academic"],
    "胡秋原": ["public_debate", "publishing", "academic", "indoctrination"],
    "殷海光": ["teacher_student", "publishing", "academic", "public_debate"],
    "徐高阮": ["public_debate", "academic"],
    "吴相湘": ["teacher_student", "academic", "meeting"],
    "林蒨": ["in_law"],
    "马占山": ["military_figure", "politician"],
    "蒋介石": ["politician", "public_debate"],
    "严侨": ["teacher_student"],
    "萧启庆": ["academic", "meeting"],
    "高荫祖": ["meeting", "politician"],
    "叶明勋": ["media"],
    "敖弟": ["family", "correspondence"],
    "王世杰": ["politician", "meeting"],
    "王克敏": ["politician"],
    "魏廷朝": ["case_prison", "political_dissident"],
    "黄宝实": ["public_debate"],
    "龚德柏": ["political_dissident", "media"],
    "赵铁寒": ["academic", "publishing"],
    "罗家伦": ["academic", "politician"],
    "沈刚伯": ["academic"],
    "张伯伯": ["nickname", "meeting"],
    "张伯敏": ["academic"],
    "钱思亮": ["academic", "meeting"],
    "庄严": ["academic", "correspondence"],
    "蒋君章": ["academic"],
    "王民信": ["academic", "classmate_colleague"],
    "蒋复璁": ["academic"],
    "陈鼓应": ["classmate_colleague"],
    "马宏祥": ["correspondence", "classmate_colleague", "publishing"],
    "林海音": ["correspondence", "publishing"],
    "王文俊": ["in_law"],
    "王正廷": ["politician"],
    "王洪钧": ["publishing"],
    "梁实秋": ["academic", "publishing"],
    "萧孟能": ["publishing"],
    "蒋经国": ["politician", "public_debate"],
    "周恩来": ["politician", "spiritual"],
    "毛泽东": ["politician", "spiritual"],
    "张学良": ["politician", "public_debate"],
    "彭明敏": ["political_dissident", "politician"],
    "谢聪敏": ["case_prison", "political_dissident"],
    "李政一": ["case_prison"],
    "黄中国": ["case_prison", "litigation"],
    "高时运": ["case_prison", "politician"],
    "李国龙": ["case_prison"],
    "古永城": ["underworld"],
    "李盛渊": ["underworld"],
    "俞中兴": ["underworld", "case_prison"],
    "吴彰炯": ["intelligence_police", "military_figure"],
    "汪梦湘": ["intelligence_police", "military_figure", "publishing", "friendship"],
    "胡炎汉": ["case_prison"],
    "陈独秀": ["academic", "politician", "spiritual"],
    "鲁迅": ["academic", "spiritual"],
    "李伋": ["spiritual"],
    "李玄伯": ["teacher_student", "academic"],
    "钱宾四": ["academic", "spiritual"],
    "罗志希": ["publishing", "politician"],
    "赵元任": ["academic"],
    "李德林": ["in_law"],
    "尹女士": ["in_law", "nickname"],
    "王家桢": ["politician"],
    "王墨林": ["meeting"],
    "李鼎彝": ["family", "academic"],
    "吴焕章": ["friendship"],
    "温茂林": ["meeting", "household_staff"],
    "李纯仁": ["family"],
    "丁锡庆": ["in_law"],
    "周翔举": ["friendship", "meeting"],
    "詹永杰": ["friendship", "classmate_colleague"],
    "严停云": ["publishing"],
    "李子卓": ["in_law", "politician"],
    "关颂韬": ["meeting"],
    "李景生": ["family", "nickname"],
    "徐伟森": ["friendship", "meeting"],
    "周桐雨": ["meeting"],
    "徐国材": ["in_law"],
    "张桂贞": ["family"],
    "顾维钧": ["politician", "spiritual"],
    "张莘夫": ["friendship"],
    "李锡恩": ["academic", "politician"],
    "陈纳德": ["military_figure", "spiritual"],
    "周克敏": ["in_law"],
    "孙念台": ["teacher_student"],
    "张作相": ["politician"],
    "王靖雯": ["media"],
    "西门庆": ["spiritual"],
    "刘半农": ["academic", "spiritual"],
    "黄毅辛": ["case_prison", "media"],
    "崔积泽": ["case_prison", "friendship"],
    "王云五": ["publishing", "politician"],
    "林正杰": ["publishing", "public_debate", "politician"],
    "黄信介": ["politician", "political_dissident", "media", "public_debate"],
    "骆学良": ["publishing", "media", "correspondence"],
    "侯立朝": ["intelligence_police", "publishing", "public_debate"],
    "陈果夫": ["politician", "spiritual"],
    "葛县长": ["politician", "litigation"],
    "冀元铎": ["intelligence_police", "litigation"],
    "陶百川": ["legal_official", "politician"],
    "钱思亮": ["academic"],
    "刘子健": ["academic"],
    "李翰祥": ["media"],
    "芮逸夫": ["academic"],
    "李宏基": ["academic"],
    "孙英善": ["classmate_colleague"],
    "周弘": ["classmate_colleague", "meeting"],
    "景新汉": ["classmate_colleague", "meeting"],
    "白绍康": ["classmate_colleague", "meeting"],
    "华昌平": ["classmate_colleague", "meeting"],
    "李华俊": ["classmate_colleague", "meeting"],
    "陈又亮": ["classmate_colleague", "meeting"],
    "祝庭生": ["classmate_colleague", "meeting"],
    "张克斌": ["classmate_colleague", "meeting"],
    "袁祝泰": ["classmate_colleague", "meeting"],
    "朱广诚": ["classmate_colleague", "meeting"],
    "黄锡昌": ["classmate_colleague", "meeting"],
    "施启扬": ["classmate_colleague", "public_debate", "meeting"],
    "佟耀勋": ["classmate_colleague", "meeting"],
    "阙至正": ["classmate_colleague", "meeting"],
    "林淑美": ["classmate_colleague", "meeting"],
    "杨祖燕": ["classmate_colleague", "meeting"],
    "杨世彭": ["classmate_colleague", "meeting"],
    "袁天中": ["classmate_colleague", "meeting"],
    "王尚义": ["classmate_colleague", "meeting"],
    "陈良榘": ["classmate_colleague", "meeting"],
    "王曾才": ["classmate_colleague", "meeting"],
    "李耀祖": ["classmate_colleague", "meeting"],
    "王文振": ["classmate_colleague"],
    "陈士宽": ["classmate_colleague"],
    "施敏雄": ["classmate_colleague", "indoctrination"],
    "毛树清": ["classmate_colleague", "friendship", "indoctrination"],
    "林钟雄": ["classmate_colleague", "meeting", "public_debate", "indoctrination"],
    "徐公起": ["academic"],
    "李济": ["academic"],
    "姚渔湘": ["academic", "meeting"],
    "李朝宗": ["intelligence_police", "litigation"],
    "姜穆": ["litigation"],
    "王惺三": ["legal_official"],
    "端木恺": ["legal_official"],
    "李孟谦": ["family"],
    "李文钧": ["family"],
    "李景生": ["family"],
    "小屯": ["in_law", "romance", "nickname"],
    "小蕾": ["romance", "nickname", "meeting"],
    "勘勘": ["family", "nickname"],
    "谌谌": ["family", "nickname"],
    "小八": ["family", "nickname"],
    "陈立峰": ["publishing"],
    "李方桂": ["academic", "meeting"],
    "余光中": ["academic", "publishing", "meeting"],
    "札奇斯钦": ["academic", "classmate_colleague", "meeting"],
    "史为鉴": ["academic", "publishing", "meeting"],
    "庄申": ["correspondence", "academic"],
    "李其泰": ["academic"],
    "陈正澄": ["classmate_colleague", "academic", "publishing"],
    "钱穆": ["academic", "correspondence", "public_debate", "indoctrination"],
    "顾翊群": ["academic", "public_debate"],
    "郑学稼": ["academic", "publishing", "public_debate"],
    "胡传厚": ["media"],
    "聂华苓": ["publishing", "media", "meeting"],
    "潘琦君": ["publishing", "meeting"],
    "徐钟珮": ["publishing", "meeting"],
    "张明": ["publishing", "meeting"],
    "张兰熙": ["publishing", "meeting"],
    "曾虚白": ["media", "public_debate", "indoctrination"],
    "陶涤亚": ["indoctrination"],
    "项迺光": ["indoctrination"],
    "周道济": ["indoctrination"],
    "王洸": ["indoctrination"],
    "屠炳春": ["indoctrination"],
    "任卓宣": ["indoctrination", "public_debate"],
    "柴松林": ["indoctrination"],
    "魏萼": ["indoctrination"],
    "邬昆如": ["indoctrination"],
    "魏以之": ["intelligence_police", "public_debate"],
    "史与为": ["intelligence_police", "political_dissident"],
    "胡汝森": ["publishing", "public_debate"],
    "陈启天": ["public_debate", "politician"],
    "于长城": ["political_dissident"],
    "于长庚": ["political_dissident"],
}

NONSTANDARD_NAME_RE = re.compile("|".join(map(re.escape, sorted(NONSTANDARD_NAMES, key=len, reverse=True))))

MEETING_CUES = (
    "见", "见到", "见面", "会面", "晤", "拜访", "访问", "认识", "遇见", "碰到", "来我家",
    "到我家", "去我家", "我家来", "请我", "请他", "找我", "找他", "陪我", "陪他", "一起",
)

CORRESPONDENCE_CUES = (
    "写信", "来信", "回信", "寄给", "致函", "致电", "打电话", "电报", "电话", "回电",
)

TEACHER_STUDENT_CUES = (
    "老师", "学生", "教授", "助理", "授课", "教书", "师母", "师生",
)

CLASSMATE_COLLEAGUE_CUES = (
    "同学", "同班", "同事", "同僚", "同房", "同案", "同排", "同住", "一起给", "同在",
)

FRIENDSHIP_CUES = (
    "朋友", "好友", "旧友", "交情", "交往", "关怀", "送我", "告诉我", "问我", "对我说", "跟我说",
)

FAMILY_CUES = (
    "父亲", "母亲", "爸爸", "妈妈", "哥哥", "弟弟", "姐姐", "妹妹", "儿子", "女儿", "家中", "家里",
)

IN_LAW_CUES = (
    "太太", "妻", "夫人", "岳父", "岳母", "大舅子", "姻亲", "嫁给", "娶", "结婚", "离婚",
)

ROMANCE_CUES = (
    "情人", "女友", "男友", "恋爱", "小情人", "爱上", "分手", "情书",
)

PUBLISHING_CUES = (
    "编辑", "主编", "出版", "出版社", "杂志", "报纸", "写稿", "投稿", "序", "书店", "文星",
)

ACADEMIC_CUES = (
    "研究", "学者", "博士", "学术", "史学", "传记", "论文", "大学", "台大", "北大",
)

MEDIA_CUES = (
    "记者", "访谈", "采访", "受访", "演讲", "节目", "电视", "广播", "导演",
)

LEGAL_OFFICIAL_CUES = (
    "法官", "审判长", "审判官", "检察官", "检察长", "书记官", "律师", "庭长",
)

LITIGATION_CUES = (
    "法院", "法庭", "判决", "上诉", "起诉", "公诉", "控告", "诬告", "告发", "诉状", "复判",
)

CASE_PRISON_CUES = (
    "同案", "狱友", "牢房", "同房", "监狱", "看守所", "探监", "保释", "军法",
)

POLITICIAN_CUES = (
    "总统", "主席", "委员", "部长", "院长", "市长", "县长", "立委", "选举", "政府", "党部",
)

INTELLIGENCE_POLICE_CUES = (
    "情治", "特务", "调查局", "警备总部", "警总", "警察", "保防", "政战", "保安处",
)

MILITARY_FIGURE_CUES = (
    "将军", "上校", "少将", "中将", "军法", "军衔", "司令", "军长", "师长", "旅长", "参谋",
)

PUBLIC_DEBATE_CUES = (
    "国民党", "民进党", "共产党", "台独", "政治", "公共", "论战", "批评", "攻击", "封杀", "军购",
)

SPIRITUAL_CUES = (
    "读", "思想", "著作", "作品", "名言", "引用", "书中", "书里", "历史上", "古代",
    "古人", "哲学", "主义", "诗", "文学", "说过", "所谓", "比喻", "像", "想象力",
)

ROLE_SUFFIXES = (
    "先生", "女士", "小姐", "太太", "夫人", "教授", "博士", "法官", "律师", "检察官", "审判长",
    "审判官", "书记官", "院长", "庭长", "校长", "主席", "总统", "部长", "将军", "上校", "少将",
    "中将", "作家", "编辑", "记者", "导演", "委员", "同学", "老师",
)

BAD_NAME_CHARS = set("的一是在不了和与及或而也就都被把让给对从向于以为着过吗呢啊呀吧里中上下前后内外时日年月个些其此那这我你他她它们")
BAD_ENDINGS = (
    "先生", "小姐", "太太", "教授", "博士", "法官", "律师", "研究", "真面", "全集", "文集",
    "目录", "自序", "序言", "附录", "一文", "一书", "主义", "政府", "法院", "法庭", "国民",
    "民进", "共产党", "自由", "中国", "台湾", "美国", "日本", "香港", "北京", "台北",
)
BAD_ENDING_CHARS = set("部党会社院局处署队军报刊界学史论节集号法罪案书文稿语话事影研省市县馆系志敌间物")
STOP_NAMES = {
    "李敖", "李先", "李大师", "李先生", "李语", "李文", "李书", "李政", "王法", "王国", "王军",
    "中国人", "台湾人", "美国人", "日本人", "英国人", "国民党", "民进党", "共产党", "新闻界",
    "文化界", "政治犯", "外省人", "台湾话", "负责人", "发行人", "总编辑", "编者略", "不自由",
    "文星", "台独", "利益", "文学", "宣传", "支持", "成立", "毕业", "党员", "司令", "权力",
    "国防部", "华民国", "国总统", "国共产", "党主席", "蒋总统", "白色恐", "宫博物",
    "公敌", "时间", "国家长", "陆杂志", "史系", "马褂", "吉林省", "龙江省", "国史馆",
    "卢沟桥", "丰富", "全家最", "祝寿", "关切", "任委员", "别文坛", "文星讼", "利用胡",
    "别学问", "包涵", "宣传自", "家琼瑶", "文星发", "时还可", "江苏钱", "严侨老",
    "周旋冠", "孙文有", "时找出", "东皋", "任院长", "江陵将", "管理", "段洗脑",
    "经验", "万岁", "国家带", "司法行", "华北政", "卓绝", "游击战", "连空头", "任常务",
    "任主任", "安东省", "江反省", "全国振", "山东反", "时发表", "武誓彭", "任命",
    "相终始", "谷旅团", "别人", "李同志", "计程车", "麻烦", "管区警", "姚谈", "姚老谈",
    "和蔼", "时用手", "明言当", "明言地", "姚老", "松曰", "时警总", "文化古", "经济问", "水槽",
    "东林怀", "怀严侨", "家失散", "古稀之", "平地人", "严侨带", "时全照", "时间已",
    "陆丢掉", "那位老", "胡适谈", "冷场", "时又有", "华严通", "车修好", "东北义",
    "公室", "时代老", "谢饭", "和济之", "于吴廷", "支持胡", "于引导", "房客庄",
    "通知李", "都本仁", "向教务", "花枝", "雷震曾", "别人裁", "姚二次", "敖弟之",
    "时考入", "那身体", "任性", "经理", "于京房", "元配离", "华严做", "华严结",
    "台记者", "周讲座", "家严茶", "寿衣替", "居住合", "师范", "师资", "房难友",
    "敖弟偶", "敖弟细", "文星写", "时可增", "时痛骂", "时磕头", "时餬口", "明处境",
    "明情况", "欧美变", "武人", "程度受", "胡诗", "胡适信", "胡适提", "胡适车",
    "苏共接", "荣同辱", "解仍旧", "路人来", "辛酸", "边站", "连助教", "通知五",
    "那次人", "严侨建", "台者", "和希望", "安徽反", "时谢绝", "曾经有", "江西反",
    "班长倒", "相印证", "管理财", "须请李",
    "明天再", "时买房", "班陆侃", "时还有", "通话人",
    "纪念周", "吉林女",
    "封长信", "高明得",
}
SIGNAL_BEFORE = set(" \t\r\n　,，.。:：;；、!！?？([（《〈“‘'\"和与及给向问访见找由同为把对从跟请替将是叫姓名骂告")
SIGNAL_AFTER = set(" \t\r\n　,，.。:：;；、!！?？)]）《》〉”’'\"")
DIRECT_PREFIXES = (
    "和", "与", "跟", "同", "给", "向", "问", "访", "见", "找", "请", "陪", "替", "骂", "告",
    "控告", "认识", "拜访", "告诉", "介绍", "约", "送", "接", "晤", "遇见", "碰到", "写信给",
    "打电话给",
)
POST_VERBS = (
    "说", "问", "来信", "回信", "告诉我", "告诉", "到我家", "来我家", "陪我", "判", "审理",
    "主审", "写信", "致函", "致电", "访问", "受访", "帮我", "请我",
)
ROLE_PREFIX_RE = re.compile(
    r"(审判长|审判官|法官|律师|检察官|书记官|院长|处长|主任|校长|教授|主席|总统|部长|"
    r"将军|上校|少将|中将|主编|编辑|记者|发行人|总编辑|所长|庭长|委员)[^。！？；：:]{0,10}$"
)

CATEGORY_LABELS = {
    "meeting": "见面",
    "correspondence": "通信",
    "teacher_student": "师生",
    "classmate_colleague": "同学同事",
    "friendship": "朋友",
    "family": "亲属",
    "in_law": "姻亲",
    "romance": "情感",
    "publishing": "出版",
    "academic": "学术",
    "media": "媒体",
    "household_staff": "家中雇员",
    "indoctrination": "感化人员",
    "legal_official": "司法人员",
    "litigation": "诉讼",
    "case_prison": "同案狱友",
    "politician": "政治人物",
    "political_dissident": "政治异议者",
    "intelligence_police": "情治警务",
    "military_figure": "军事人物",
    "underworld": "江湖人物",
    "public_debate": "公共论战",
    "spiritual": "神交引用",
    "nickname": "称谓待考",
    "mentioned": "待复核",
}


def build_name_regex() -> re.Pattern[str]:
    compounds = "|".join(map(re.escape, sorted(COMPOUND_SURNAMES, key=len, reverse=True)))
    singles = re.escape("".join(sorted(set(SINGLE_SURNAMES))))
    # Chinese personal names in this corpus are mostly 2-3 chars. Compound surnames add one or two chars.
    return re.compile(rf"(?:{compounds})[\u4e00-\u9fff]{{1,2}}|[{singles}][\u4e00-\u9fff]{{1,2}}")


NAME_RE = build_name_regex()
FOREIGN_RE = re.compile("|".join(map(re.escape, sorted(FOREIGN_AND_HISTORICAL, key=len, reverse=True))))


def read_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "big5", "utf-16"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def clean_title(raw: str) -> str:
    name = re.sub(r"^\d+[.．、]\s*", "", raw)
    name = re.sub(r"\.txt$", "", name, flags=re.I)
    return name.strip(" 《》\t\r\n")


def is_likely_person_name(name: str) -> bool:
    if name in ALWAYS_NAMES or name in ALIASES or name in NONSTANDARD_NAMES:
        return True
    if name in STOP_NAMES:
        return False
    if name.startswith("李敖"):
        return False
    if len(name) < 2 or len(name) > 6:
        return False
    if any(ch in BAD_NAME_CHARS for ch in name[1:]):
        return False
    if any(name.endswith(x) or name.startswith(x) for x in BAD_ENDINGS):
        return False
    if name[-1] in BAD_ENDING_CHARS:
        return False
    if re.search(r"[第年月日号集类篇册卷上下前后续新大小多少]", name[1:]):
        return False
    if name in FOREIGN_AND_HISTORICAL:
        return True
    if name[:2] in COMPOUND_SURNAMES:
        return len(name) in (3, 4)
    return name[0] in SINGLE_SURNAMES and len(name) in (2, 3)


def context_window(text: str, start: int, end: int, width: int = 48) -> str:
    snippet = text[max(0, start - width): min(len(text), end + width)]
    snippet = re.sub(r"\s+", " ", snippet).strip()
    return snippet


def score_context(name: str, ctx: str, after: str) -> tuple[str, int, list[str]]:
    scores = Counter()
    hits: list[str] = []
    cue_sets = (
        ("meeting", MEETING_CUES, 4),
        ("correspondence", CORRESPONDENCE_CUES, 5),
        ("teacher_student", TEACHER_STUDENT_CUES, 5),
        ("classmate_colleague", CLASSMATE_COLLEAGUE_CUES, 4),
        ("friendship", FRIENDSHIP_CUES, 3),
        ("family", FAMILY_CUES, 5),
        ("in_law", IN_LAW_CUES, 5),
        ("romance", ROMANCE_CUES, 5),
        ("publishing", PUBLISHING_CUES, 4),
        ("academic", ACADEMIC_CUES, 4),
        ("media", MEDIA_CUES, 4),
        ("legal_official", LEGAL_OFFICIAL_CUES, 5),
        ("litigation", LITIGATION_CUES, 4),
        ("case_prison", CASE_PRISON_CUES, 5),
        ("politician", POLITICIAN_CUES, 4),
        ("intelligence_police", INTELLIGENCE_POLICE_CUES, 4),
        ("military_figure", MILITARY_FIGURE_CUES, 4),
        ("public_debate", PUBLIC_DEBATE_CUES, 3),
        ("spiritual", SPIRITUAL_CUES, 1),
    )
    for category, cues, weight in cue_sets:
        local_hits = [cue for cue in cues if cue in ctx]
        if local_hits:
            scores[category] += weight + min(len(local_hits), 4)
            hits.extend(local_hits[:4])
    for suffix in ROLE_SUFFIXES:
        if after.startswith(suffix):
            if suffix in ("先生", "女士", "小姐"):
                hits.append(suffix)
                continue
            if suffix in LEGAL_OFFICIAL_CUES or suffix in ("法官", "律师", "检察官", "审判长", "审判官", "书记官"):
                scores["legal_official"] += 6
            elif suffix in FAMILY_CUES:
                scores["family"] += 4
            elif suffix in TEACHER_STUDENT_CUES or suffix in ("教授", "博士"):
                scores["teacher_student"] += 5
                scores["academic"] += 2
            elif suffix in PUBLISHING_CUES or suffix in ("作家", "编辑"):
                scores["publishing"] += 4
            elif suffix in MEDIA_CUES or suffix in ("记者", "导演"):
                scores["media"] += 4
            elif suffix in POLITICIAN_CUES or suffix in ("主席", "总统", "部长", "委员"):
                scores["politician"] += 4
            elif suffix in INTELLIGENCE_POLICE_CUES:
                scores["intelligence_police"] += 4
            elif suffix in MILITARY_FIGURE_CUES or suffix in ("将军", "上校", "少将", "中将"):
                scores["military_figure"] += 4
            else:
                scores["meeting"] += 3
            hits.append(suffix)
    if name in FOREIGN_AND_HISTORICAL:
        scores["spiritual"] += 4
    if not scores:
        return "mentioned", 0, []
    category, score = scores.most_common(1)[0]
    stronger_than_spiritual = [
        "meeting", "correspondence", "teacher_student", "family", "in_law", "romance",
        "legal_official", "litigation", "case_prison",
    ]
    if category == "spiritual" and any(scores[item] >= 4 for item in stronger_than_spiritual):
        category, score = max(((item, scores[item]) for item in stronger_than_spiritual), key=lambda x: x[1])
    return category, int(score), sorted(set(hits), key=hits.index)


@dataclass
class PersonHit:
    name: str
    occurrences: int = 0
    relevant_occurrences: int = 0
    title_hits: int = 0
    score: int = 0
    name_signals: int = 0
    strong_signals: int = 0
    categories: Counter = field(default_factory=Counter)
    cue_hits: Counter = field(default_factory=Counter)
    books: Counter = field(default_factory=Counter)
    chapters: Counter = field(default_factory=Counter)
    collections: Counter = field(default_factory=Counter)
    evidence: list[dict] = field(default_factory=list)


def add_evidence(hit: PersonHit, item: dict) -> None:
    if len(hit.evidence) < 10:
        hit.evidence.append(item)
        return
    # Keep high-score examples and a spread across books.
    existing_books = {x["book"] for x in hit.evidence}
    if item["score"] >= 4 and item["book"] not in existing_books:
        hit.evidence[-1] = item


def iter_text_files(source_root: Path) -> list[Path]:
    return sorted(
        (p for p in source_root.rglob("*.txt") if len(p.relative_to(source_root).parts) >= 3),
        key=lambda p: str(p),
    )


def meta_for_path(source_root: Path, path: Path) -> tuple[str, str, str]:
    rel = path.relative_to(source_root)
    parts = rel.parts
    collection = clean_title(parts[0]) if len(parts) > 1 else "全集简介"
    book = clean_title(parts[1]) if len(parts) > 2 else clean_title(path.stem)
    chapter = clean_title(path.name)
    return collection, book, chapter


def is_contextual_false_positive(name: str, text: str, start: int, end: int) -> bool:
    ctx = context_window(text, start, end)
    if name == "老子":
        real_markers = ("《老子》", "老子曰", "老子说", "道德经", "老庄")
        if any(marker in ctx for marker in real_markers):
            return False
        false_markers = (
            "我老子", "老子们", "死了老子", "老子不管儿子", "老子感化",
            "受老子感化", "土匪爷爷", "有钱的老子", "老子的余荫",
            "你老子", "他老子", "儿子", "父亲意像",
        )
        return any(marker in ctx for marker in false_markers)
    return False


def extract_from_text(
    text: str,
    path: Path,
    source_root: Path,
    people: dict[str, PersonHit],
    title_names: set[str],
) -> None:
    collection, book, chapter = meta_for_path(source_root, path)
    for regex in (NAME_RE, FOREIGN_RE, NONSTANDARD_NAME_RE):
        for match in regex.finditer(text):
            name = match.group(0)
            if not is_likely_person_name(name):
                continue
            if is_contextual_false_positive(name, text, match.start(), match.end()):
                continue
            name = ALIASES.get(name, name)
            ctx = context_window(text, match.start(), match.end())
            after = text[match.end(): match.end() + 6]
            before = text[match.start() - 1: match.start()] if match.start() else ""
            pre12 = text[max(0, match.start() - 12): match.start()]
            has_name_signal = (
                name in title_names
                or name in FOREIGN_AND_HISTORICAL
                or before in SIGNAL_BEFORE
                or (after[:1] in SIGNAL_AFTER)
                or any(after.startswith(suffix) for suffix in ROLE_SUFFIXES)
            )
            has_strong_signal = (
                name in title_names
                or name in FOREIGN_AND_HISTORICAL
                or any(after.startswith(suffix) for suffix in ROLE_SUFFIXES)
                or any(pre12.endswith(prefix) for prefix in DIRECT_PREFIXES)
                or any(after.startswith(verb) for verb in POST_VERBS)
                or bool(ROLE_PREFIX_RE.search(pre12))
            )
            category, score, cues = score_context(name, ctx, after)
            hit = people.setdefault(name, PersonHit(name=name))
            hit.occurrences += 1
            if has_name_signal:
                hit.name_signals += 1
            if has_strong_signal:
                hit.strong_signals += 1
            hit.score += score
            hit.categories[category] += 1
            hit.books[book] += 1
            hit.collections[collection] += 1
            hit.chapters[f"{book} / {chapter}"] += 1
            if name in title_names:
                hit.title_hits += 1
                score += 2
            if score > 0 or name in title_names or name in CURATED_IDENTITIES:
                hit.relevant_occurrences += 1
                for cue in cues:
                    hit.cue_hits[cue] += 1
                add_evidence(
                    hit,
                    {
                        "book": book,
                        "collection": collection,
                        "chapter": chapter,
                        "category": category,
                        "score": score,
                        "cues": cues[:6],
                        "snippet": ctx,
                    },
                )


def extract_title_names(source_root: Path, files: list[Path] | None = None) -> set[str]:
    names: set[str] = set()
    for path in files or iter_text_files(source_root):
        collection, book, chapter = meta_for_path(source_root, path)
        for raw in (book, chapter):
            for match in NAME_RE.finditer(raw):
                name = match.group(0)
                if is_likely_person_name(name):
                    names.add(ALIASES.get(name, name))
            for match in FOREIGN_RE.finditer(raw):
                names.add(ALIASES.get(match.group(0), match.group(0)))
            for match in NONSTANDARD_NAME_RE.finditer(raw):
                names.add(ALIASES.get(match.group(0), match.group(0)))
            for marker in ("研究", "评传", "真面目", "臭史", "论"):
                if marker in raw:
                    prefix = raw.split(marker, 1)[0]
                    for match in NAME_RE.finditer(prefix):
                        name = match.group(0)
                        if is_likely_person_name(name):
                            names.add(ALIASES.get(name, name))
    return names


def keep_person(hit: PersonHit) -> bool:
    if hit.name in STOP_NAMES:
        return False
    if hit.name in CURATED_IDENTITIES and hit.occurrences > 0:
        return True
    if hit.title_hits > 0:
        return True
    if hit.name_signals == 0:
        return False
    if hit.strong_signals >= 1 and hit.relevant_occurrences >= 1:
        return True
    if hit.name in FOREIGN_AND_HISTORICAL and hit.occurrences >= 1:
        return True
    if hit.strong_signals >= 2 and hit.occurrences >= 2:
        return True
    return False


def categories_for_hit(hit: PersonHit) -> list[str]:
    if hit.name in CURATED_IDENTITIES:
        return CURATED_IDENTITIES[hit.name]
    if hit.name in SPIRITUAL_ONLY:
        return ["spiritual"]
    categories = []
    minimum = max(2, math.ceil(hit.occurrences * 0.08))
    for category, count in hit.categories.most_common():
        if category == "mentioned" and len(hit.categories) > 1:
            continue
        if count >= minimum or category == primary_category(hit):
            categories.append(category)
    if hit.name in FOREIGN_AND_HISTORICAL and "spiritual" not in categories:
        categories.append("spiritual")
    if not categories:
        categories.append("mentioned")
    return categories


def primary_category(hit: PersonHit) -> str:
    if hit.name in CURATED_IDENTITIES:
        return CURATED_IDENTITIES[hit.name][0]
    weighted = Counter(hit.categories)
    if hit.name in FOREIGN_AND_HISTORICAL:
        weighted["spiritual"] += 4
    if hit.relevant_occurrences == 0:
        return "mentioned"
    return weighted.most_common(1)[0][0]


def confidence(hit: PersonHit) -> int:
    points = 30
    points += min(hit.relevant_occurrences * 8, 30)
    points += min(len(hit.books) * 4, 20)
    points += min(hit.title_hits * 10, 20)
    points += min(hit.strong_signals * 6, 18)
    points += min(hit.score, 25)
    return max(1, min(points, 99))


def build_outputs(people: dict[str, PersonHit], source_root: Path, files: list[Path]) -> dict:
    kept = [hit for hit in people.values() if keep_person(hit)]
    person_rows = []
    identity_links = []
    by_book: dict[str, dict] = {}
    for path in files:
        collection, book, _chapter = meta_for_path(source_root, path)
        by_book.setdefault(book, {"book": book, "collection": collection, "people": Counter(), "chapters": 0})
        by_book[book]["chapters"] += 1

    for hit in kept:
        cats = categories_for_hit(hit)
        primary = primary_category(hit)
        row = {
            "name": hit.name,
            "category": primary,
            "categoryLabel": CATEGORY_LABELS[primary],
            "primaryCategory": primary,
            "primaryCategoryLabel": CATEGORY_LABELS[primary],
            "categories": cats,
            "categoryLabels": [CATEGORY_LABELS[cat] for cat in cats],
        "categoryStats": [
                {
                    "category": cat,
                    "label": CATEGORY_LABELS[cat],
                    "count": hit.categories[cat] or max(1, min(hit.occurrences, 3)),
                    "curated": hit.name in CURATED_IDENTITIES,
                }
                for cat in cats
            ],
            "confidence": confidence(hit),
            "occurrences": hit.occurrences,
            "relevantOccurrences": hit.relevant_occurrences,
            "bookCount": len(hit.books),
            "chapterCount": len(hit.chapters),
            "titleHits": hit.title_hits,
            "topBooks": [{"book": b, "count": c} for b, c in hit.books.most_common(12)],
            "topChapters": [{"chapter": ch, "count": c} for ch, c in hit.chapters.most_common(10)],
            "collections": [{"collection": c, "count": n} for c, n in hit.collections.most_common()],
            "cues": [{"cue": cue, "count": n} for cue, n in hit.cue_hits.most_common(10)],
            "evidence": sorted(hit.evidence, key=lambda x: (-x["score"], x["book"], x["chapter"]))[:8],
        }
        person_rows.append(row)
        for stat in row["categoryStats"]:
            identity_links.append(
                {
                    "person": hit.name,
                    "category": stat["category"],
                    "categoryLabel": stat["label"],
                    "count": stat["count"],
                    "personOccurrences": hit.occurrences,
                    "confidence": row["confidence"],
                }
            )
        for book, count in hit.books.items():
            if book in by_book:
                by_book[book]["people"][hit.name] += count

    person_rows.sort(key=lambda x: ("mentioned" in x["categories"], -x["confidence"], -x["occurrences"], x["name"]))
    book_rows = []
    for item in by_book.values():
        people_for_book = item["people"].most_common(80)
        book_rows.append(
            {
                "book": item["book"],
                "collection": item["collection"],
                "chapters": item["chapters"],
                "personCount": len(item["people"]),
                "people": [{"name": name, "count": count} for name, count in people_for_book],
            }
        )
    book_rows.sort(key=lambda x: (x["collection"], x["book"]))

    category_counts = {
        key: sum(1 for x in person_rows if key in x["categories"])
        for key in CATEGORY_LABELS
    }
    totals = {
        "people": len(person_rows),
        "books": len(book_rows),
        "chapters": sum(x["chapters"] for x in book_rows),
        "identityLinks": len(identity_links),
        "categoryCounts": category_counts,
        "spiritual": category_counts.get("spiritual", 0),
        "legal": category_counts.get("legal_official", 0) + category_counts.get("litigation", 0),
        "direct": category_counts.get("meeting", 0),
        "mentioned": sum(1 for x in person_rows if "mentioned" in x["categories"]),
    }
    return {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "sourceRoot": str(source_root),
        "method": "本地规则抽取：中文姓名候选 + 关系语境线索 + 逐书聚合；结果保留证据片段，适合继续人工校订。",
        "categoryLabels": CATEGORY_LABELS,
        "totals": totals,
        "people": person_rows,
        "identityLinks": sorted(
            identity_links,
            key=lambda x: (-x["personOccurrences"], x["person"], x["category"]),
        ),
        "books": book_rows,
    }


def write_json_js(data: dict, data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "people.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    js = "window.LEEAO_RELATIONSHIP_DATA = "
    js += json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    js += ";\n"
    (data_dir / "relationship-data.js").write_text(js, encoding="utf-8")


def write_text_exports(data: dict, export_dir: Path) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("李敖交互式人物关系图：纯文本导出")
    lines.append(f"生成时间：{data['generatedAt']}")
    lines.append(f"来源：{data['sourceRoot']}")
    lines.append(f"说明：{data['method']}")
    lines.append("")
    totals = data["totals"]
    category_summary = "；".join(
        f"{data['categoryLabels'][key]} {count}"
        for key, count in totals.get("categoryCounts", {}).items()
        if count
    )
    lines.append(
        f"总计：{totals['people']} 人；{totals['identityLinks']} 条身份边；"
        f"{totals['books']} 本书；{totals['chapters']} 个章节。"
    )
    lines.append(f"身份节点：{category_summary}")
    lines.append("")
    for label_key, label in data["categoryLabels"].items():
        group = [p for p in data["people"] if label_key in p["categories"]]
        if not group:
            continue
        lines.append(f"==== {label}（{len(group)}人）====")
        for p in group:
            books = "；".join(f"{b['book']}({b['count']})" for b in p["topBooks"][:6])
            cues = "、".join(c["cue"] for c in p["cues"][:6]) or "无明显线索"
            labels = " / ".join(p["categoryLabels"])
            lines.append(
                f"- {p['name']}｜分类：{labels}｜可信度 {p['confidence']}｜出现 {p['occurrences']} 次｜"
                f"涉及 {p['bookCount']} 本｜线索：{cues}｜主要书目：{books}"
            )
            for ev in p["evidence"][:2]:
                lines.append(f"  证据：《{ev['book']}》/{ev['chapter']}：{ev['snippet']}")
        lines.append("")
    (export_dir / "li-ao-relationships.txt").write_text("\n".join(lines), encoding="utf-8")

    by_book_lines = []
    by_book_lines.append("李敖人物关系逐本索引")
    by_book_lines.append(f"生成时间：{data['generatedAt']}")
    by_book_lines.append("")
    for book in data["books"]:
        people = "、".join(f"{p['name']}({p['count']})" for p in book["people"][:60])
        by_book_lines.append(
            f"《{book['book']}》｜{book['collection']}｜章节 {book['chapters']}｜人物 {book['personCount']}"
        )
        by_book_lines.append(people if people else "（未抽到候选人物）")
        by_book_lines.append("")
    (export_dir / "by-book-index.txt").write_text("\n".join(by_book_lines), encoding="utf-8")

    with (export_dir / "li-ao-relationships.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["姓名", "分类", "主分类", "可信度", "出现次数", "相关出现", "涉及书数", "涉及章节数", "主要书目", "线索"])
        for p in data["people"]:
            writer.writerow(
                [
                    p["name"],
                    " / ".join(p["categoryLabels"]),
                    p["primaryCategoryLabel"],
                    p["confidence"],
                    p["occurrences"],
                    p["relevantOccurrences"],
                    p["bookCount"],
                    p["chapterCount"],
                    "；".join(f"{b['book']}({b['count']})" for b in p["topBooks"][:8]),
                    "、".join(c["cue"] for c in p["cues"][:8]),
                ]
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Li Ao relationship candidates book by book.")
    parser.add_argument("--source", default=SOURCE_DIR, help="source corpus directory")
    parser.add_argument("--book-path", help="one book directory under the source corpus")
    parser.add_argument("--all", action="store_true", help="scan the whole corpus explicitly")
    parser.add_argument("--data-dir", default="data", help="output data directory")
    parser.add_argument("--export-dir", default="exports", help="plain-text export directory")
    args = parser.parse_args()

    source_root = Path(args.source).resolve()
    if not source_root.exists():
        raise SystemExit(f"Source directory not found: {source_root}")

    if args.book_path:
        target = Path(args.book_path)
        if not target.is_absolute():
            target = Path.cwd() / target
        if not target.exists():
            raise SystemExit(f"Book directory not found: {target}")
        files = sorted(target.rglob("*.txt"), key=lambda p: str(p))
    elif args.all:
        files = iter_text_files(source_root)
    else:
        sample_books = sorted(
            p for p in source_root.glob("*/*") if p.is_dir()
        )[:12]
        print("请指定一本书，例如：")
        for book in sample_books:
            print(f"  --book-path \"{book}\"")
        print("如确需全库抽取，请显式加 --all。")
        raise SystemExit(2)

    title_names = extract_title_names(source_root, files)
    people: dict[str, PersonHit] = {}
    for idx, path in enumerate(files, 1):
        text = read_text(path)
        extract_from_text(text, path, source_root, people, title_names)
        if idx % 500 == 0:
            print(f"processed {idx}/{len(files)} files; candidates={len(people)}")
    data = build_outputs(people, source_root, files)
    write_json_js(data, Path(args.data_dir))
    write_text_exports(data, Path(args.export_dir))
    print(
        f"done: {data['totals']['people']} people, {data['totals']['books']} books, "
        f"{data['totals']['chapters']} chapters"
    )


if __name__ == "__main__":
    main()
