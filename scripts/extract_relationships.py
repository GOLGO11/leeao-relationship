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
    "莎士比亚", "萧伯纳", "歌德", "托尔斯泰", "陀思妥耶夫斯基", "林肯", "华盛顿", "罗斯福", "丘吉尔",
    "马歇尔", "詹姆斯·法兰克", "詹姆斯杜渥", "詹姆斯·杜渥",
    "马歇尔", "詹姆斯·法兰克", "詹姆斯杜渥", "詹姆斯·杜渥",
    "凯撒", "哥伦布", "伽利略", "牛顿", "释迦牟尼", "耶稣", "穆罕默德", "孔子", "孟子",
    "老子", "庄子", "墨子", "荀子", "韩非", "司马迁", "班固", "陶渊明", "李白", "杜甫",
    "白居易", "苏东坡", "王安石", "朱熹", "王阳明", "曹操", "诸葛亮", "岳飞", "文天祥",
    "鲁迅", "胡适", "孙中山", "蒋介石", "毛泽东", "周恩来",
}

SPIRITUAL_ONLY = {
    "爱因斯坦", "苏格拉底", "柏拉图", "亚里士多德", "拿破仑", "马克思", "恩格斯", "列宁",
    "斯大林", "希特勒", "达尔文", "罗素", "伏尔泰", "卢梭", "康德", "黑格尔", "尼采",
    "莎士比亚", "萧伯纳", "歌德", "托尔斯泰", "陀思妥耶夫斯基", "林肯", "华盛顿", "罗斯福", "丘吉尔",
    "凯撒", "哥伦布", "伽利略", "牛顿", "释迦牟尼", "耶稣", "穆罕默德", "孔子", "孟子",
    "老子", "庄子", "墨子", "荀子", "韩非", "司马迁", "班固", "陶渊明", "李白", "杜甫",
    "白居易", "苏东坡", "王安石", "朱熹", "王阳明", "曹操", "诸葛亮", "岳飞", "文天祥",
    "鲁迅",
}

FICTIONAL_CHARACTERS = {
    "西门庆", "潘金莲", "武松", "孙悟空", "猪八戒", "唐僧", "沙僧",
    "贾宝玉", "林黛玉", "薛宝钗", "鲁智深", "林冲", "宋江", "李逵",
    "哈姆雷特", "堂吉诃德", "浮士德", "罗密欧", "朱丽叶", "夏洛克",
    "福尔摩斯", "阿Q", "孔乙己", "祥林嫂",
}

ALIASES = {
    "胡适之": "胡适",
    "钱宾四": "钱穆",
    "王世傑": "王世杰",
    "相湘": "吴相湘",
    "姚老头": "姚从吾",
    "周树人": "鲁迅",
    "东方望": "汪梦湘",
    "于大江": "汪梦湘",
    "沈局长": "沈之岳",
    "马戈": "马宏祥",
    "施启杨": "施启扬",
    "詹永傑": "詹永杰",
    "景生二": "李景生",
    "严师母": "林蒨",
    "严以侨": "严侨",
    "素馨": "李文钧",
    "塞克": "陈凝秋",
    "鲁掖": "王贵民",
    "项廼光": "项迺光",
    "阉鸡": "李盛渊",
    "蒋总裁": "蒋介石",
    "何王剑": "王剑芬",
    "华严": "严停云",
    "孟绝子": "孟祥柯",
    "李老太": "张桂贞",
    "李季恒": "李鼎彝",
    "玑衡": "李鼎彝",
    "李大下巴": "李鼎彝",
    "马小个子": "马占山",
    "鲁肇岚": "小蕾",
    "尚勤": "王尚勤",
    "小屯": "王小屯",
    "吴黑子": "吴申叔",
    "吴处长": "吴彰炯",
    "毛主席": "毛泽东",
    "蔡校长": "蔡元培",
    "孔冬梅": "孔东梅",
    "马萨利": "马萨利克",
    "刘福増": "刘福增",
    "汪师长": "汪敬煦",
    "孙猴子": "孙悟空",
    "蒋夫人": "宋美龄",
    "萧朱婉": "朱婉坚",
    "萧太太": "朱婉坚",
    "朱太太": "朱婉坚",
    "萧先生": "萧孟能",
    "康白联": "康白",
    "居人王": "王黄双",
    "居人黄": "黄彩琴",
    "胡因梦": "胡茵梦",
    "胡因子": "胡茵梦",
    "王女士": "王剑芬",
    "何秀惶": "何秀煌",
    "柏杨太": "艾玫",
    "莫院长": "莫德惠",
    "魏胖": "魏廷朝",
    "老谢": "谢聪敏",
    "王洁": "王洁中",
    "马丁·恩纳尔斯": "马丁·恩纳尔斯",
    "马丁·恩纳": "马丁·恩纳尔斯",
    "马丁埃纳": "马丁·恩纳尔斯",
    "詹姆斯杜渥": "詹姆斯·杜渥",
    "白脸": "黄永寿",
    "欧阳坤判": "欧阳坤",
    "何剑芬": "王剑芬",
    "何王剑芬": "王剑芬",
    "胡因": "胡茵梦",
    "马克斯": "马克思",
    "高金": "高金素梅",
    "南榕": "郑南榕",
    "毛局长": "毛人凤",
    "裴老爷子": "裴存藩",
    "裴老爷": "裴存藩",
    "裴将军": "裴存藩",
    "裴主任": "裴存藩",
    "裴书记长": "裴存藩",
    "裴厅长": "裴存藩",
    "裴市长": "裴存藩",
    "裴干事长": "裴存藩",
    "裴监察人": "裴存藩",
    "裴委员": "裴存藩",
    "裴老太": "裴老太太",
    "傅总司": "傅作义",
    "傅总司令": "傅作义",
    "何市长": "何思源",
    "陈司令": "陈长捷",
    "戴雨农": "戴笠",
    "阎百川": "阎锡山",
    "马司令": "马法五",
    "曲成军": "曲军成",
    "雷德福": "罗伯特雷德福",
    "傅宜生": "傅作义",
    "黄三": "黄胜常",
    "彭老师": "彭明敏",
    "路易斯": "乔·路易斯",
    "孔夫子": "孔子",
    "王雪艇": "王世杰",
    "经国": "蒋经国",
    "经国哥": "蒋经国",
    "蒋校长": "蒋介石",
    "郑矮子": "郑彦棻",
    "李济之": "李济",
    "吴稚老": "吴稚晖",
    "祖光": "罗祖光",
    "慎之": "曹慎之",
    "刘科长": "刘昭祥",
    "钱复同": "钱复",
    "柏杨师": "柏杨",
    "李焕先": "李焕",
    "周玉寇": "周玉蔻",
    "徐佛观": "徐复观",
    "张炎元": "张炳华",
    "华塘先生": "乔家才",
    "华塘兄": "乔家才",
    "乔老": "乔家才",
    "仲琳兄": "李仲琳",
    "永铭兄": "张永铭",
    "培初兄": "刘培初",
    "庆斌兄": "齐庆斌",
    "汉三兄": "马汉三",
    "炳华先生": "张炳华",
    "张局长": "张炳华",
    "马兴峻": "马兴骏",
    "项乃光": "项迺光",
    "姜绍谟": "姜诏谟",
    "党丕琇": "党丕修",
    "蒋公": "蒋介石",
    "扬正民": "施启扬",
    "新娘子钟桂": "李钟桂",
    "钟桂": "李钟桂",
    "俊才老师": "吴俊才",
    "章铨": "吴章铨",
    "雷德福邱": "邱铭笙",
    "罗伯特雷德福邱": "邱铭笙",
    "赵红粉": "赵培鑫",
    "杜甫诗": "杜甫",
    "左丘": "左丘明",
    "林世煌": "林世煜",
    "孟肯": "门肯",
    "宋将军": "宋希濂",
    "希濂先生": "宋希濂",
    "宋希濂将军": "宋希濂",
    "张少帅": "张学良",
    "经国先生": "蒋经国",
    "蒋主任": "蒋经国",
    "登辉先生": "李登辉",
    "邓公小平": "邓小平",
    "李蓝女士": "李蓝",
    "李蓝小姐": "李蓝",
    "大风兄": "大风",
    "江南": "刘宜良",
    "苏子": "苏轼",
    "桓君山": "桓谭",
    "杜元凯": "杜预",
    "巴顿将": "巴顿",
    "巴顿将军": "巴顿",
    "阿周": "周忠明",
    "朱子": "朱熹",
    "鲁迅先生": "鲁迅",
    "太史公": "司马迁",
    "孙子膑": "孙膑",
    "邱公子": "邱铭笙",
    "赵准医师": "赵培鑫",
    "赵娘子": "赵培鑫",
    "苏院长": "苏贞昌",
    "苏院长贞昌": "苏贞昌",
    "谢院长": "谢长廷",
    "谢院长长廷": "谢长廷",
    "杜部长": "杜正胜",
    "杜部长正胜": "杜正胜",
    "薛局长": "薛石民",
    "薛局长石民": "薛石民",
    "张主任委员政雄": "张政雄",
    "陈总统": "陈水扁",
    "陈总统水扁": "陈水扁",
    "苏光头": "苏贞昌",
    "林委员郁方": "林郁方",
    "郁方": "林郁方",
    "小马哥": "马英九",
    "小亨利": "柯承亨",
    "罗委员志明": "罗志明",
    "丁委员守中": "丁守中",
    "苏委员起": "苏起",
    "费委员鸿泰": "费鸿泰",
    "李部长杰": "李杰",
    "李部长天羽": "李天羽",
    "蔡副部长明宪": "蔡明宪",
    "蔡清游": "蔡清遊",
    "华柱": "高华柱",
    "施次长颜祥": "施颜祥",
    "Vicky": "李姿仪",
    "用和": "汪用和",
    "苏亚孙": "翁苏亚孙",
    "小常": "常修治",
    "小蔡": "蔡志煌",
    "许老爹": "许历农",
    "颜胖子": "颜清标",
    "沈二爷": "沈铭三",
    "殷师母": "夏君璐",
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
    "于长城", "于长庚", "林蒨", "李盛渊", "俞中兴", "雷震", "康白",
    "王黄双", "黄彩琴", "何秀煌", "孟祥柯", "段宏俊", "叶肇模",
    "萧近仁", "高仲元", "陈子和", "张任飞", "章尊良", "林紫耀", "艾玫",
    "郭荣文", "刘刑警", "尤元基", "王剑吟", "尹俊", "王洁中", "吴荣元",
    "陈鸿渐", "蔡俊军", "沈之岳", "蔡金铿", "吴松枝", "赵清泉",
    "杨英龙", "刘伟民", "徐开喜", "黄祥华", "谭坤泉",
    "朱光军", "汪本流", "毛世馨", "陈晏庭", "王建福", "李聪明", "林荣宗",
    "欧阳坤", "陈廷柳", "陈金凤", "汪宾彬", "黄道舜", "雷志云", "陈庆堂",
    "林浩兴", "苏振崧", "卞昭荃", "刘台生", "熊钰铮", "林堂正", "孟昭熙",
    "蔡火炮", "蔡国扬", "徐鹏举", "林宗科", "杨次长", "洪炳麟", "蔡甘清",
    "陈清华", "程台生", "李新冰", "黄永寿", "黄铭强", "张树忠", "温锦丰",
    "赖锡志", "丘国利", "李焕升", "张国杰",
    "吴尚纬", "许文志", "魏文龙", "屠寄",
    "金亚平", "黄仁温", "晁煜", "张顺良", "庄建国", "童聪明", "谢骏扬",
    "董嘉诚", "林丰翔", "林河南", "赵天仪", "张齐斌", "王护士",
    "璩诗方", "刘维斌", "刘望苏", "蒋家语", "吴祥辉", "郑南榕",
    "陈凝秋", "王贵民",
    "毛人凤", "乔家才", "裴存藩", "裴老爷子", "裴老太太", "张太太", "李登辉", "龙云", "卢汉", "傅作义", "何思源", "陈长捷",
    "戴笠", "阎锡山", "马法五", "李广和", "王霭芬", "吴铸人", "姚蓉轩",
    "沈醉", "杜聿明", "杜致勇", "张永亭", "邱铭笙", "郑介民", "马汉三",
    "李希成", "曲军成", "宋希濂", "叶翔之", "刘秋芳", "张炎元", "廖耀湘",
    "徐复观", "张炳华", "李宗仁",
    "潘其武", "吉章简", "周伟龙", "刘培初", "刘人奎", "张家铨", "楼兆元",
    "侯镜如", "张毅夫", "李肖白", "徐业道", "徐人骥", "吴茂先", "于斌",
    "戴颂仪", "王荫泰", "吴景中", "齐庆斌", "李汉元", "王鲁翘", "傅有权",
    "白世维", "孙耕南", "王蒲臣", "史泓", "曾毓隽", "严家诰", "吴健吾",
    "王崇五", "李叶超", "谷正文", "张宣泽", "文强", "雷鸣远", "李德和",
    "史择言", "康淑媛", "岳梓宇", "孔觉民", "马兴骏", "吴石", "李玉堂",
    "钟浩东", "陈太初", "桂永清", "何震", "姜盛三", "阮清源", "赵耀斌",
    "乔凤藻", "张镇邦", "梁化之", "汤局长", "孔嘉", "吴安之", "尚渭父",
    "包烈", "侯祯祥", "箫信如", "阎致远", "李仲琳", "俞泽生", "郭外川",
    "谷凤翔", "彭孟缉", "王有为", "吴利君", "刘镇芳", "聂琮", "周关锠",
    "毛万里", "黄加持", "张志智", "梁上栋", "苗告宝", "胡伯岳", "韩希圣",
    "谢冰莹", "黄振华", "何福祥", "舒适存", "刘仲康",
    "王调勋", "荆向荣", "许先登", "唐新", "姜诏谟", "王立生", "魏毅生",
    "林尧民", "王德荫", "郭寿华", "白莲丞", "吕仕伦", "郭宗泰", "王孔安",
    "贺元", "杨遇春", "尚望", "严灵峰", "柯建安", "程克祥", "萧勃",
    "舒翔", "赵斌成", "何芝园", "于书绅", "杨济华", "李叶", "王新衡",
    "杨隆祜", "杨蔚", "唐棣", "何龙庆", "汪祖华", "郭巩疆", "钟贡勋",
    "王荣国", "杨清植", "李曾逊", "周正", "毛惕园", "谭明诚", "梁若节",
    "李希纯", "吴思俭", "霍立人", "孙华", "王兆槐", "乐干", "党丕修",
    "刘钦礼", "郭履洲", "杨震裔", "刘戈青", "郑修元", "陶一珊", "何峨芳",
    "张辅邦", "李培楠", "刘光朝", "贾秀升", "王志超",
    "范炳文", "高向果", "左思元", "武成祖", "李友平", "苏桐凤", "田荣祖",
    "张庆恩", "谢文津", "韦宪文", "杨作芝", "冯大轰", "房秉符", "张彝鼎",
    "杨治泰", "牛焕辰", "李思聪", "郝家驹", "刘士烈", "温松康", "张岫岚",
    "陈汝淦", "潘秀仁",
    "袁寄滨", "陈谦", "丁继曾", "叶霞翟", "谢贵诚", "马敬华", "赵龙文",
    "姬梅轩", "杨觉民", "武树华", "李友芝", "申有枝", "赵富瑞",
    "韩克温", "于华庭", "李海涵", "杨庭芳", "朱耀武", "王利秋", "尚厚庵",
    "霍来庭", "童秀明", "王玉宾", "胡鸿章",
    "李钟桂", "吴俊才", "王新德", "孟大中", "孟大强", "查良钊", "彭立云",
    "孔昭庆", "仁井田陞", "丘宏达", "陈继盛", "陈隆志", "陈少廷", "关中",
    "许信良", "张俊宏", "史静波", "王芳华", "连家立", "汪中磊", "王昇",
    "王济中", "孙运璿", "游荣茂", "李志鹏", "温士源", "程国强", "周清玉",
    "赖文良", "朱石炎", "赵培鑫", "连培如", "柯贤忠", "狄德罗", "史华格",
    "梭维斯特", "左丘明", "邱义仁", "林世煜", "余陈月瑛", "曾心仪",
    "邓维桢", "刘福增", "门肯", "基辛格", "傅朝枢", "刘宜良", "大风",
    "李蓝", "汪东林", "俞济时", "孙元良", "张达钧", "邓小平", "庾信",
    "桓谭", "杜预", "苏轼", "潘毓刚", "刘焕荣", "游国麟", "徐菊生",
    "周忠明", "施大哥", "巴顿", "约伯", "徐武军", "孙武", "孙膑",
    "吕思勉", "龚鹏程", "张玉法", "裴普贤", "钱太太", "曾子", "朱熹",
    "李霁野", "张宗昌", "亚丹", "宇野精一", "王瑞武", "李显斌",
    "张金龙", "陈光耀", "小甜甜", "张斌", "周蔚英",
    "何飞鹏", "章孝慈", "高信疆", "沈登恩", "顾锦才", "黄剑青", "林晃", "魏锦水",
    "田耕莘", "刘家昌", "李济", "王尚勤", "胡星妈", "黄宏成", "陈维昭",
    "吴锦江", "胡炎汉", "黄毅辛",
    "王恒庆", "吴焕章", "张灏", "张瑞珂", "罗香林", "王兆民", "张乐平",
    "叶圣康", "张立豫", "叶成有", "王自义", "汤克勤", "石锦",
    "杨锦钟", "杨锦铨", "许文葵", "王孟仁", "余又健", "杨肇南",
    "杨肖震", "程东白", "翁硕柏",
    "张群", "黄少谷", "黄杰", "曹建中", "李晋芳", "钱翊平", "侯立朝",
    "阮继光", "袁英华", "卢华栋", "屠申虹", "汤炎光", "郑彦棻",
    "伍一心", "李国瑾", "李善培", "施珂", "郑锡华", "段春理",
    "毛子水", "陈顾远", "柏杨", "于右任",
    "伍伯英", "王德云", "蔡秀雄", "陈联欢", "吴谦仁", "张济团", "王瑶",
    "谢家鹤", "钟曜唐", "陈健民", "张玉芳", "王云涛", "傅国光", "徐文开",
    "成鼎", "李桓", "王宗", "萧凯", "聂开国", "许登源", "李彬如",
    "袁耀权", "杨西崑", "王淦开", "包德甫", "林佛儿", "陈中雄", "黄华成",
    "辜振甫", "蔡维屏", "陈培基", "叶迫", "范子文", "满素玉", "丁慰慈",
    "沈铭三", "黄德贤", "蒋光超", "司马文武", "陈水扁", "甘地",
    "平鑫涛", "骆明道", "周之鸣", "李鸿禧", "蔡墩铭", "于申德",
    "林慧峰", "阎愈政", "魏廷昱",
    "苏贞昌", "王金平", "林郁方", "李杰", "李天羽", "薛石民", "杜正胜",
    "赖英照", "张政雄", "高金素梅", "李纪珠", "曾永权", "周守训", "洪秀柱",
    "雷倩", "刘忆如", "张显耀", "李文忠", "王世坚", "张俊雄", "王幸男",
    "罗志明", "丁守中", "苏起", "费鸿泰", "蔡明宪", "帅化民", "柯俊雄",
    "卢秀燕", "赵良燕", "汤曜明", "许世楷", "吴钊燮",
}

NONSTANDARD_NAMES = {
    "小屯", "小蕾", "咪咪", "勘勘", "谌谌", "素馨", "小八", "阉鸡", "札奇斯钦", "李其泰",
    "王洁中", "尹俊", "毛世馨", "丘国利", "欧阳坤", "屠寄", "晁煜", "南榕",
    "塞克", "玑衡", "华严", "裴存藩", "裴老爷子", "裴将军", "裴主任", "裴书记长",
    "裴厅长", "裴市长", "裴干事长", "裴监察人", "裴委员", "裴老太太", "张太太",
    "傅总司令", "罗伯特雷德福",
    "华塘先生", "华塘兄", "乔老", "仲琳兄", "永铭兄", "培初兄", "庆斌兄",
    "汉三兄", "炳华先生", "张局长",
    "新娘子钟桂", "俊才老师", "雷德福邱", "罗伯特雷德福邱", "宋将军",
    "希濂先生", "宋希濂将军", "张少帅", "经国先生", "登辉先生", "邓公小平",
    "李蓝女士", "李蓝小姐", "大风兄", "苏子", "桓君山", "杜元凯",
    "巴顿将军", "阿周", "施大哥", "钱太太", "朱子", "鲁迅先生",
    "太史公", "孙子膑", "邱公子", "小甜甜", "赵准医师", "赵娘子",
    "苏院长贞昌", "谢院长长廷", "杜部长正胜", "薛局长石民", "张主任委员政雄",
    "陈总统水扁", "林委员郁方", "罗委员志明", "丁委员守中", "苏委员起",
    "费委员鸿泰", "李部长杰", "李部长天羽", "蔡副部长明宪", "高金素梅",
}

CURATED_IDENTITIES = {
    "胡适": ["correspondence", "meeting", "academic"],
    "马克思": ["spiritual"],
    "马丁·路德·金": ["spiritual"],
    "老子": ["spiritual"],
    "孙中山": ["politician", "spiritual"],
    "李凤亭": ["family"],
    "武则天": ["spiritual"],
    "章太炎": ["academic", "spiritual"],
    "姚从吾": ["teacher_student", "academic"],
    "陶希圣": ["politician", "academic", "public_debate", "meeting"],
    "胡秋原": ["public_debate", "publishing", "academic"],
    "殷海光": ["teacher_student", "publishing", "academic", "public_debate"],
    "徐高阮": ["public_debate", "academic"],
    "吴相湘": ["teacher_student", "academic", "meeting"],
    "林蒨": ["in_law"],
    "马占山": ["military_figure", "politician"],
    "蒋介石": ["politician", "public_debate"],
    "严侨": ["teacher_student", "academic", "friendship", "meeting"],
    "萧启庆": ["academic", "meeting"],
    "高荫祖": ["meeting", "politician"],
    "何飞鹏": ["publishing", "media", "meeting"],
    "章孝慈": ["academic", "politician", "meeting", "public_debate"],
    "高信疆": ["media", "publishing", "correspondence", "friendship", "witness", "meeting"],
    "田耕莘": ["religion", "politician", "public_debate"],
    "沈登恩": ["publishing", "meeting"],
    "于右任": ["politician", "meeting"],
    "叶翔之": ["politician", "military_figure"],
    "张群": ["politician", "meeting"],
    "黄少谷": ["politician", "meeting"],
    "黄杰": ["politician", "military_figure", "meeting"],
    "曹建中": ["military_figure", "intelligence_police", "publishing", "public_debate"],
    "李晋芳": ["politician", "publishing"],
    "钱翊平": ["publishing", "classmate_colleague", "meeting"],
    "郑锡华": ["publishing", "case_prison", "meeting"],
    "阮继光": ["classmate_colleague", "meeting"],
    "袁英华": ["classmate_colleague", "meeting"],
    "卢华栋": ["classmate_colleague", "case_prison", "political_dissident", "meeting"],
    "屠申虹": ["publishing", "meeting"],
    "汤炎光": ["publishing", "politician", "meeting"],
    "郑彦棻": ["legal_official", "politician", "prison_admin"],
    "伍一心": ["intelligence_police", "military_figure", "meeting"],
    "李国瑾": ["intelligence_police", "military_figure", "meeting"],
    "段春理": ["intelligence_police", "military_figure", "meeting"],
    "李善培": ["friendship", "meeting"],
    "施珂": ["military_figure", "friendship", "meeting"],
    "毛子水": ["academic", "meeting"],
    "陈顾远": ["academic", "lawyer_counsel", "public_debate"],
    "柏杨": ["publishing", "political_dissident", "human_rights", "public_debate"],
    "伍伯英": ["legal_official", "litigation"],
    "王德云": ["legal_official", "litigation"],
    "蔡秀雄": ["legal_official", "litigation"],
    "陈联欢": ["legal_official", "litigation"],
    "吴谦仁": ["legal_official", "litigation"],
    "张济团": ["legal_official", "litigation"],
    "王瑶": ["legal_official", "litigation"],
    "谢家鹤": ["legal_official", "litigation"],
    "钟曜唐": ["legal_official", "litigation"],
    "陈健民": ["legal_official", "litigation"],
    "张玉芳": ["legal_official"],
    "王云涛": ["legal_official"],
    "傅国光": ["legal_official"],
    "徐文开": ["legal_official"],
    "成鼎": ["legal_official"],
    "李桓": ["legal_official"],
    "王宗": ["legal_official"],
    "萧凯": ["legal_official"],
    "聂开国": ["lawyer_counsel"],
    "许登源": ["case_prison"],
    "李彬如": ["military_figure"],
    "杨西崑": ["correspondence"],
    "王淦开": ["correspondence", "intelligence_police"],
    "包德甫": ["media"],
    "林佛儿": ["publishing"],
    "陈中雄": ["publishing", "meeting"],
    "黄华成": ["publishing", "meeting"],
    "辜振甫": ["politician", "meeting"],
    "蔡维屏": ["teacher_student"],
    "陈培基": ["legal_official", "litigation"],
    "叶迫": ["case_prison"],
    "范子文": ["case_prison", "intelligence_police", "political_dissident"],
    "满素玉": ["case_prison"],
    "丁慰慈": ["torture_victim"],
    "胡星妈": ["nickname", "family", "in_law"],
    "沈铭三": ["family", "friendship", "meeting"],
    "黄德贤": ["legal_official", "litigation"],
    "蒋光超": ["media", "witness", "litigation", "meeting"],
    "司马文武": ["litigation", "public_debate"],
    "莫德惠": ["politician"],
    "孙文燕": ["academic", "correspondence"],
    "杨洁篪": ["politician", "publishing", "public_debate"],
    "王企祥": ["academic", "spiritual"],
    "桂裕": ["teacher_student", "academic"],
    "杜重远": ["media", "political_dissident", "litigation"],
    "唐培礼": ["religion", "case_prison"],
    "陈逸松": ["lawyer_counsel", "case_prison"],
    "陈水扁": ["politician", "public_debate"],
    "甘地": ["spiritual"],
    "平鑫涛": ["publishing", "meeting"],
    "骆明道": ["friendship", "meeting"],
    "周之鸣": ["friendship", "meeting"],
    "李鸿禧": ["academic", "legal_official"],
    "蔡墩铭": ["academic", "legal_official"],
    "于申德": ["in_law", "family"],
    "林慧峰": ["in_law"],
    "阎愈政": ["friendship"],
    "魏廷昱": ["public_debate"],
    "苏贞昌": ["politician", "meeting", "public_debate"],
    "谢长廷": ["politician", "meeting", "public_debate"],
    "王金平": ["politician", "friendship", "meeting", "correspondence", "property_finance"],
    "林郁方": ["politician", "public_debate", "meeting"],
    "李杰": ["military_figure", "politician", "meeting"],
    "李天羽": ["military_figure", "politician", "meeting"],
    "薛石民": ["intelligence_police", "politician", "meeting"],
    "杜正胜": ["politician", "academic", "meeting"],
    "赖英照": ["legal_official", "politician"],
    "张政雄": ["politician", "meeting"],
    "高金素梅": ["politician", "media", "meeting"],
    "李纪珠": ["politician", "academic", "meeting"],
    "曾永权": ["politician", "meeting"],
    "周守训": ["politician", "media", "meeting"],
    "洪秀柱": ["politician", "meeting"],
    "雷倩": ["politician", "litigation", "public_debate"],
    "刘忆如": ["politician", "academic", "meeting"],
    "张显耀": ["politician", "meeting"],
    "李文忠": ["politician", "public_debate", "meeting"],
    "王世坚": ["politician", "media"],
    "张俊雄": ["politician", "meeting"],
    "王幸男": ["politician", "litigation", "public_debate"],
    "罗志明": ["politician", "meeting"],
    "丁守中": ["politician", "public_debate", "meeting"],
    "苏起": ["politician", "academic", "public_debate", "meeting"],
    "费鸿泰": ["politician", "meeting"],
    "蔡明宪": ["military_figure", "politician", "meeting"],
    "帅化民": ["military_figure", "politician", "friendship"],
    "柯俊雄": ["politician", "media"],
    "卢秀燕": ["politician", "meeting"],
    "赵良燕": ["politician", "litigation"],
    "汤曜明": ["politician", "military_figure"],
    "许世楷": ["politician", "meeting"],
    "吴钊燮": ["politician", "meeting"],
    "蔡同荣": ["politician", "public_debate", "litigation"],
    "陈文茜": ["media", "politician", "correspondence", "friendship"],
    "李庆华": ["politician", "family"],
    "顾崇廉": ["military_figure", "politician", "friendship", "meeting"],
    "游锡堃": ["politician", "family"],
    "吕秀莲": ["politician", "public_debate"],
    "林浊水": ["politician", "public_debate", "meeting"],
    "许志雄": ["politician", "academic", "litigation"],
    "林义雄": ["politician", "public_debate"],
    "王闿运": ["spiritual"],
    "李文仪": ["friendship", "public_debate"],
    "李庆安": ["politician", "family"],
    "胡锦涛": ["politician"],
    "谢文政": ["politician"],
    "张庆惠": ["politician", "friendship"],
    "尤清": ["politician", "public_debate"],
    "康宁祥": ["politician", "public_debate"],
    "柯承亨": ["military_figure", "politician", "meeting"],
    "陈国祥": ["military_figure", "party_propaganda", "public_debate"],
    "黄义交": ["politician", "friendship", "meeting"],
    "刘文雄": ["politician", "friendship", "meeting"],
    "白添枝": ["politician", "friendship", "meeting"],
    "汤火圣": ["politician"],
    "黄适卓": ["politician", "correspondence"],
    "冯沪祥": ["politician", "friendship", "meeting"],
    "吴德美": ["politician"],
    "黄志芳": ["politician"],
    "姚文智": ["politician", "media"],
    "陈明真": ["politician", "scientist", "public_debate"],
    "蔡锦隆": ["politician"],
    "叶芳雄": ["politician"],
    "郝柏村": ["military_figure", "politician"],
    "林国庆": ["politician"],
    "郑金玲": ["politician"],
    "尹伶瑛": ["politician"],
    "黄石城": ["politician", "public_debate"],
    "施明德": ["political_dissident", "politician", "public_debate"],
    "沈剑虹": ["politician", "academic", "public_debate"],
    "杨宪村": ["politician", "public_debate", "publishing"],
    "刘峰松": ["case_prison", "correspondence", "meeting"],
    "陈彦增": ["meeting", "correspondence", "family"],
    "张光锦": ["friendship"],
    "韩世忠": ["spiritual", "military_figure"],
    "杨振宁": ["spiritual", "scientist"],
    "丁尼生": ["spiritual"],
    "李逸洋": ["politician"],
    "吴伯雄": ["politician", "public_debate"],
    "林镇驹": ["friendship", "meeting"],
    "高华柱": ["military_figure", "politician"],
    "高华德": ["spiritual", "politician"],
    "池启明": ["legal_official", "meeting"],
    "陈学圣": ["politician"],
    "雷学明": ["military_figure", "litigation", "family"],
    "倪文亚": ["politician", "family"],
    "黄光彩": ["academic", "public_debate"],
    "许惠祐": ["intelligence_police", "politician", "meeting"],
    "黄天福": ["politician", "family"],
    "孙道存": ["property_finance", "neighbor"],
    "周阳山": ["academic", "politician", "meeting"],
    "谢冠生": ["legal_official", "politician"],
    "胡祖庆": ["academic", "politician", "meeting"],
    "谢瑞智": ["academic"],
    "李念祖": ["legal_official", "academic", "meeting"],
    "杨泰顺": ["academic", "meeting"],
    "林腾鹞": ["academic", "meeting"],
    "刘庆瑞": ["academic", "family"],
    "郭婉蓉": ["academic", "family"],
    "杜鲁门": ["spiritual", "politician"],
    "徐智雄": ["legal_official", "meeting"],
    "翁钤": ["family", "meeting"],
    "翁镇": ["family", "meeting"],
    "翁廷伟": ["family", "meeting"],
    "翁廷府": ["family", "meeting"],
    "翁苏亚孙": ["family", "friendship"],
    "王爱雪": ["meeting", "friendship"],
    "蒋仲苓": ["military_figure", "politician"],
    "周公": ["spiritual"],
    "吴汉": ["spiritual", "military_figure"],
    "李广": ["spiritual", "military_figure"],
    "梅农": ["spiritual", "politician"],
    "王作荣": ["teacher_student", "academic", "politician"],
    "劳思光": ["academic", "public_debate", "meeting"],
    "陈耀昌": ["friendship", "medical_care", "academic", "politician"],
    "郝龙斌": ["politician", "public_debate", "meeting"],
    "颜胖子": ["politician", "nickname", "meeting"],
    "丁戴维": ["politician", "meeting"],
    "翁岳生": ["legal_official", "academic", "meeting"],
    "梁肃戎": ["politician", "meeting", "litigation"],
    "许历农": ["military_figure", "politician", "meeting"],
    "费正清": ["spiritual", "academic", "public_debate"],
    "李远哲": ["scientist", "politician", "academic", "public_debate"],
    "陈诚": ["politician", "military_figure", "meeting"],
    "陈履安": ["friendship", "politician", "meeting", "family"],
    "董作宾": ["academic", "meeting"],
    "施颜祥": ["politician", "meeting"],
    "叶赛莺": ["legal_official", "meeting"],
    "林庆隆": ["legal_official", "meeting"],
    "王祥基": ["media", "friendship", "meeting"],
    "林弘宣": ["political_dissident", "correspondence", "human_rights"],
    "徐炳强": ["litigation"],
    "陈境圳": ["teacher_student", "classmate_colleague", "meeting"],
    "李庆元": ["politician", "meeting"],
    "霍姆斯": ["spiritual", "legal_official"],
    "刘泰英": ["politician", "litigation", "property_finance"],
    "陈唐山": ["classmate_colleague", "politician"],
    "李震山": ["legal_official", "academic", "intelligence_police", "meeting"],
    "叶俊荣": ["legal_official", "academic", "politician", "meeting"],
    "刘幸义": ["legal_official", "meeting"],
    "穆闽珠": ["politician", "meeting"],
    "张书铭": ["publishing", "friendship", "meeting"],
    "张坤山": ["publishing", "friendship"],
    "阙聪华": ["classmate_colleague", "meeting"],
    "赖岳忠": ["media", "friendship", "meeting"],
    "李姿仪": ["classmate_colleague", "meeting"],
    "杨士仪": ["classmate_colleague", "meeting"],
    "陈静兰": ["media", "meeting"],
    "汪用和": ["media", "meeting"],
    "黄富": ["political_dissident", "human_rights", "public_debate"],
    "蔡豪": ["politician", "friendship", "meeting"],
    "颜清标": ["politician", "nickname", "meeting"],
    "冯定国": ["politician", "friendship", "meeting"],
    "李鸿钧": ["politician", "friendship", "meeting"],
    "陈荫华": ["politician", "meeting"],
    "黄主文": ["politician", "publishing", "correspondence"],
    "万春华": ["witness", "meeting"],
    "马美美": ["property_finance", "meeting"],
    "郭正亮": ["politician"],
    "王启而": ["classmate_colleague", "meeting"],
    "常修治": ["intelligence_police", "meeting"],
    "蔡志煌": ["intelligence_police", "meeting"],
    "殷琪": ["property_finance", "public_debate"],
    "秦孝仪": ["party_propaganda", "litigation", "academic"],
    "吴健雄": ["spiritual", "scientist"],
    "王恒庆": ["teacher_student", "meeting"],
    "张灏": ["academic", "classmate_colleague", "meeting"],
    "王兆民": ["politician", "family", "correspondence"],
    "张乐平": ["spiritual", "media"],
    "叶圣康": ["publishing", "meeting"],
    "张瑞珂": ["meeting"],
    "罗香林": ["academic"],
    "张立豫": ["in_law"],
    "叶成有": ["in_law"],
    "王自义": ["in_law"],
    "汤克勤": ["in_law"],
    "石锦": ["in_law"],
    "杨锦钟": ["teacher_student"],
    "杨锦铨": ["teacher_student"],
    "许文葵": ["teacher_student"],
    "王孟仁": ["teacher_student"],
    "余又健": ["teacher_student"],
    "杨肇南": ["teacher_student"],
    "杨肖震": ["teacher_student"],
    "程东白": ["teacher_student"],
    "翁硕柏": ["teacher_student"],
    "顾锦才": ["legal_official", "litigation"],
    "黄剑青": ["legal_official", "litigation"],
    "林晃": ["legal_official", "litigation"],
    "魏锦水": ["trust_property", "property_finance"],
    "王尚勤": ["romance", "friendship", "meeting"],
    "黄宏成": ["teacher_student", "academic", "meeting"],
    "陈维昭": ["academic", "correspondence", "public_debate"],
    "叶明勋": ["media", "in_law"],
    "敖弟": ["family", "correspondence"],
    "王世杰": ["politician", "meeting"],
    "王克敏": ["politician"],
    "魏廷朝": ["case_prison", "political_dissident", "human_rights", "friendship", "meeting"],
    "龚德柏": ["political_dissident", "media", "indoctrination"],
    "赵铁寒": ["academic", "publishing"],
    "罗家伦": ["academic", "politician"],
    "沈刚伯": ["academic"],
    "张伯伯": ["nickname", "meeting"],
    "张伯敏": ["academic"],
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
    "萧孟能": ["publishing", "litigation", "property_finance"],
    "蒋经国": ["politician", "public_debate"],
    "周恩来": ["politician", "spiritual"],
    "毛泽东": ["politician", "spiritual"],
    "张学良": ["politician", "public_debate"],
    "彭明敏": ["political_dissident", "politician"],
    "谢聪敏": ["case_prison", "political_dissident", "human_rights", "friendship", "meeting"],
    "李政一": ["case_prison", "political_dissident", "torture_victim", "correspondence"],
    "陆啸钊": ["classmate_colleague", "friendship", "publishing", "academic"],
    "谷正纲": ["politician", "witness"],
    "毛人凤": ["politician", "intelligence_police", "prison_admin", "military_figure"],
    "裴存藩": ["politician", "military_figure", "neighbor", "meeting"],
    "裴老太太": ["marriage_context", "neighbor", "nickname", "meeting"],
    "张太太": ["nickname", "neighbor", "meeting"],
    "李登辉": ["politician"],
    "龙云": ["military_figure", "politician"],
    "卢汉": ["military_figure", "politician"],
    "傅作义": ["military_figure", "politician"],
    "何思源": ["politician"],
    "陈长捷": ["military_figure"],
    "戴笠": ["intelligence_police", "military_figure"],
    "阎锡山": ["politician", "military_figure"],
    "马法五": ["military_figure"],
    "李广和": ["intelligence_police", "military_figure", "politician"],
    "王霭芬": ["politician"],
    "吴铸人": ["politician"],
    "沈醉": ["intelligence_police", "military_figure", "publishing"],
    "杜聿明": ["military_figure"],
    "张永亭": ["veteran", "military_figure", "friendship", "meeting"],
    "潘毓刚": ["scientist", "academic", "friendship"],
    "徐菊生": ["veteran", "military_figure", "friendship", "meeting"],
    "周忠明": ["veteran", "military_figure", "friendship", "meeting"],
    "施大哥": ["veteran", "military_figure", "nickname", "friendship", "meeting"],
    "巴顿": ["military_figure", "spiritual"],
    "约伯": ["spiritual"],
    "刘焕荣": ["social_case"],
    "游国麟": ["social_case"],
    "邱铭笙": ["disability", "publishing", "academic", "meeting"],
    "张金龙": ["medical_care", "meeting"],
    "陈光耀": ["medical_care", "meeting"],
    "小甜甜": ["medical_care", "nickname", "meeting"],
    "张斌": ["medical_care", "academic"],
    "张继高": ["media", "publishing", "correspondence", "friendship", "meeting"],
    "张翠英": ["media", "in_law", "meeting"],
    "夏道平": ["academic"],
    "熊廷武": ["classmate_colleague", "friendship", "meeting"],
    "张丕隆": ["classmate_colleague", "meeting"],
    "张忠栋": ["meeting"],
    "武忠森": ["lawyer_counsel", "meeting"],
    "刘焕宇": ["legal_official", "litigation"],
    "孙森焱": ["legal_official", "litigation"],
    "李琼荫": ["legal_official", "litigation"],
    "俞雨娣": ["in_law", "meeting"],
    "白云": ["media"],
    "李鸿章": ["spiritual", "politician"],
    "黄胜常": ["friendship", "meeting"],
    "罗警员": ["intelligence_police", "nickname", "meeting"],
    "乔·路易斯": ["spiritual"],
    "吴稚晖": ["politician", "spiritual"],
    "孙立人": ["military_figure", "politician"],
    "盛世才": ["politician", "military_figure", "public_debate"],
    "张京育": ["academic", "politician", "meeting"],
    "林荣三": ["media", "publishing", "public_debate"],
    "陈冲": ["politician"],
    "周联华": ["religion", "academic"],
    "赵耀东": ["politician", "meeting"],
    "宋明怡": ["media"],
    "吴欲君": ["legal_official", "litigation"],
    "王立杰": ["legal_official", "litigation"],
    "林振国": ["politician", "correspondence"],
    "杨襄明": ["legal_official", "litigation"],
    "查泰莱": ["fictional"],
    "祝英台": ["fictional"],
    "莫院长": ["politician", "nickname"],
    "曾桂香": ["legal_official", "litigation"],
    "罗建群": ["legal_official", "litigation"],
    "萧亨国": ["legal_official", "litigation"],
    "罗祖光": ["friendship"],
    "曹慎之": ["meeting", "public_debate"],
    "黎则奋": ["media"],
    "黄宝实": ["politician", "public_debate"],
    "袁耀权": ["case_prison", "military_figure", "meeting"],
    "刘昭祥": ["intelligence_police", "meeting"],
    "杨秉钺": ["legal_official", "litigation"],
    "苏茂秋": ["legal_official", "litigation"],
    "黄奠华": ["legal_official", "litigation"],
    "鞠金蕾": ["legal_official", "military_figure", "litigation"],
    "张权利": ["litigation"],
    "钱复": ["politician", "academic"],
    "梁松雄": ["legal_official", "litigation"],
    "陈满贤": ["legal_official", "litigation"],
    "陈瑞甫": ["legal_official", "litigation"],
    "刁德善": ["case_prison", "political_dissident"],
    "李焕": ["politician", "party_propaganda"],
    "陈绥民": ["party_propaganda", "politician", "meeting"],
    "李天培": ["academic", "classmate_colleague", "friendship", "meeting"],
    "刘必跟": ["litigation", "witness"],
    "孙智燊": ["academic", "classmate_colleague", "meeting"],
    "周玉蔻": ["media", "meeting"],
    "吴越潮": ["politician", "meeting"],
    "叶公超": ["politician", "meeting"],
    "林家祺": ["intelligence_police", "meeting", "friendship"],
    "郭国基": ["politician", "public_debate"],
    "汪家声": ["legal_official", "litigation"],
    "张烈老": ["nickname", "friendship"],
    "罗伯特雷德福": ["spiritual"],
    "郑介民": ["intelligence_police", "military_figure", "politician"],
    "马汉三": ["intelligence_police", "politician", "case_prison"],
    "李希成": ["intelligence_police", "legal_official", "prison_admin"],
    "曲军成": ["anti_communist_defector", "political_dissident", "indoctrination", "case_prison", "human_rights"],
    "王瑞武": ["politician", "human_rights"],
    "李显斌": ["anti_communist_defector"],
    "刘秋芳": ["politician", "intelligence_police"],
    "鲍文樾": ["military_figure", "case_prison", "meeting"],
    "周端甫": ["intelligence_police", "prison_admin", "meeting"],
    "唐嗣尧": ["politician", "intelligence_police"],
    "倪超凡": ["intelligence_police", "military_figure"],
    "黄天迈": ["intelligence_police", "prison_admin"],
    "姜达绪": ["prison_admin", "legal_official"],
    "张子扬": ["politician", "witness"],
    "郭紫峻": ["intelligence_police", "politician"],
    "刘启瑞": ["intelligence_police", "academic"],
    "徐复观": ["academic", "spiritual"],
    "徐武军": ["meeting", "academic"],
    "孙武": ["spiritual", "military_figure"],
    "孙膑": ["spiritual", "military_figure"],
    "吕思勉": ["academic", "spiritual"],
    "龚鹏程": ["academic", "public_debate"],
    "张玉法": ["academic", "public_debate"],
    "裴普贤": ["academic", "public_debate"],
    "钱太太": ["marriage_context", "meeting"],
    "曾子": ["spiritual"],
    "朱熹": ["spiritual", "academic"],
    "张炳华": ["intelligence_police", "politician", "prison_admin"],
    "李宗仁": ["politician", "military_figure"],
    "吴毅安": ["military_figure", "politician"],
    "潘其武": ["intelligence_police", "prison_admin", "case_prison"],
    "吉章简": ["intelligence_police", "military_figure", "politician"],
    "周伟龙": ["intelligence_police", "military_figure", "case_prison"],
    "刘培初": ["intelligence_police", "military_figure", "human_rights", "friendship"],
    "刘人奎": ["intelligence_police", "military_figure"],
    "张家铨": ["intelligence_police", "politician"],
    "楼兆元": ["intelligence_police", "case_prison", "friendship"],
    "侯镜如": ["military_figure"],
    "张毅夫": ["intelligence_police"],
    "李肖白": ["intelligence_police", "meeting"],
    "徐业道": ["intelligence_police", "meeting"],
    "徐人骥": ["intelligence_police", "meeting"],
    "吴茂先": ["intelligence_police"],
    "于斌": ["politician", "meeting"],
    "戴颂仪": ["intelligence_police", "military_figure"],
    "王荫泰": ["politician"],
    "吴景中": ["intelligence_police", "friendship", "case_prison"],
    "齐庆斌": ["intelligence_police", "friendship"],
    "李汉元": ["intelligence_police"],
    "王鲁翘": ["intelligence_police", "friendship"],
    "傅有权": ["intelligence_police", "friendship"],
    "白世维": ["intelligence_police", "friendship"],
    "孙耕南": ["intelligence_police"],
    "王蒲臣": ["intelligence_police", "friendship"],
    "史泓": ["intelligence_police"],
    "曾毓隽": ["politician"],
    "严家诰": ["case_prison"],
    "吴健吾": ["friendship", "meeting"],
    "王崇五": ["friendship", "human_rights"],
    "李叶超": ["friendship", "human_rights"],
    "谷正文": ["intelligence_police", "military_figure", "meeting"],
    "张宣泽": ["case_prison", "politician"],
    "文强": ["intelligence_police", "publishing"],
    "雷鸣远": ["religion", "politician"],
    "李德和": ["family", "politician"],
    "史择言": ["intelligence_police"],
    "岳梓宇": ["friendship", "witness"],
    "孔觉民": ["intelligence_police"],
    "马兴骏": ["intelligence_police", "case_prison"],
    "吴石": ["military_figure", "case_prison"],
    "李玉堂": ["military_figure", "case_prison"],
    "钟浩东": ["political_dissident", "case_prison"],
    "陈太初": ["case_prison"],
    "桂永清": ["military_figure"],
    "何震": ["intelligence_police", "case_prison"],
    "姜盛三": ["intelligence_police", "case_prison"],
    "阮清源": ["case_prison", "friendship"],
    "赵耀斌": ["case_prison"],
    "乔凤藻": ["case_prison"],
    "张镇邦": ["case_prison", "friendship"],
    "梁化之": ["politician"],
    "汤局长": ["intelligence_police", "nickname"],
    "孔嘉": ["friendship", "meeting"],
    "吴安之": ["friendship", "meeting"],
    "尚渭父": ["friendship", "meeting"],
    "包烈": ["intelligence_police"],
    "侯祯祥": ["intelligence_police", "friendship"],
    "箫信如": ["intelligence_police", "friendship"],
    "阎致远": ["friendship", "meeting"],
    "李仲琳": ["friendship", "meeting"],
    "俞泽生": ["politician", "friendship"],
    "郭外川": ["politician", "human_rights"],
    "谷凤翔": ["politician", "meeting"],
    "彭孟缉": ["military_figure", "politician"],
    "张志智": ["politician", "meeting"],
    "梁上栋": ["politician", "meeting"],
    "苗告宝": ["friendship", "meeting"],
    "胡伯岳": ["friendship", "meeting"],
    "韩希圣": ["friendship", "meeting"],
    "徐志道": ["intelligence_police", "prison_admin", "human_rights"],
    "张永铭": ["intelligence_police", "legal_official", "friendship", "human_rights"],
    "张公度": ["intelligence_police", "friendship", "witness"],
    "康淑媛": ["witness", "property_finance"],
    "刘瑞符": ["intelligence_police", "human_rights"],
    "陈仙洲": ["intelligence_police", "military_figure"],
    "周念行": ["publishing", "friendship"],
    "张子奇": ["politician", "meeting"],
    "陈维纶": ["military_figure", "publishing"],
    "刘建章": ["military_figure", "publishing"],
    "谢冰莹": ["publishing", "public_debate"],
    "黄振华": ["publishing", "public_debate"],
    "何福祥": ["publishing", "public_debate"],
    "舒适存": ["publishing", "public_debate"],
    "刘仲康": ["publishing", "intelligence_police"],
    "顾祝同": ["military_figure", "politician", "publishing"],
    "邢森洲": ["intelligence_police", "meeting"],
    "周蔚英": ["marriage_context", "meeting"],
    "邹志英": ["meeting", "case_prison"],
    "吴家元": ["property_finance", "politician"],
    "唐乃建": ["intelligence_police", "politician"],
    "姚蓉轩": ["classmate_colleague", "friendship", "meeting"],
    "王调勋": ["intelligence_police", "friendship", "meeting"],
    "荆向荣": ["intelligence_police", "friendship", "meeting"],
    "许先登": ["intelligence_police", "friendship", "meeting"],
    "唐新": ["intelligence_police", "friendship", "meeting"],
    "姜诏谟": ["intelligence_police", "friendship", "meeting"],
    "王立生": ["intelligence_police", "friendship", "meeting"],
    "魏毅生": ["intelligence_police", "friendship", "meeting"],
    "林尧民": ["intelligence_police", "friendship", "meeting"],
    "王德荫": ["intelligence_police", "friendship", "meeting"],
    "郭寿华": ["intelligence_police", "friendship", "meeting"],
    "白莲丞": ["intelligence_police", "friendship", "meeting"],
    "吕仕伦": ["intelligence_police", "friendship", "meeting"],
    "郭宗泰": ["intelligence_police", "friendship", "meeting"],
    "王孔安": ["intelligence_police", "friendship", "meeting"],
    "贺元": ["intelligence_police", "friendship", "meeting"],
    "杨遇春": ["intelligence_police", "friendship", "meeting"],
    "尚望": ["intelligence_police", "friendship", "meeting"],
    "严灵峰": ["intelligence_police", "friendship", "meeting"],
    "柯建安": ["intelligence_police", "friendship", "meeting"],
    "程克祥": ["intelligence_police", "friendship", "meeting"],
    "萧勃": ["intelligence_police", "friendship", "meeting"],
    "舒翔": ["intelligence_police", "friendship", "meeting"],
    "赵斌成": ["intelligence_police", "friendship", "meeting"],
    "何芝园": ["intelligence_police", "friendship", "meeting"],
    "于书绅": ["intelligence_police", "friendship", "meeting"],
    "杨济华": ["intelligence_police", "friendship", "meeting"],
    "李叶": ["intelligence_police", "friendship", "meeting"],
    "吴利君": ["intelligence_police", "friendship", "meeting"],
    "王新衡": ["intelligence_police", "friendship", "meeting"],
    "杨隆祜": ["intelligence_police", "friendship", "meeting"],
    "杨蔚": ["intelligence_police", "friendship", "meeting"],
    "唐棣": ["intelligence_police", "friendship", "meeting"],
    "何龙庆": ["intelligence_police", "friendship", "meeting"],
    "汪祖华": ["intelligence_police", "friendship", "meeting"],
    "郭巩疆": ["intelligence_police", "friendship", "meeting"],
    "钟贡勋": ["intelligence_police", "friendship", "meeting"],
    "王荣国": ["intelligence_police", "friendship", "meeting"],
    "杨清植": ["intelligence_police", "friendship", "meeting"],
    "李曾逊": ["intelligence_police", "friendship", "meeting"],
    "周正": ["intelligence_police", "friendship", "meeting"],
    "毛惕园": ["intelligence_police", "friendship", "meeting"],
    "谭明诚": ["intelligence_police", "friendship", "meeting"],
    "梁若节": ["intelligence_police", "friendship", "meeting"],
    "李希纯": ["intelligence_police", "friendship", "meeting"],
    "吴思俭": ["intelligence_police", "friendship", "meeting"],
    "霍立人": ["intelligence_police", "friendship", "meeting"],
    "刘镇芳": ["intelligence_police", "friendship", "meeting"],
    "孙华": ["intelligence_police", "friendship", "meeting"],
    "王兆槐": ["intelligence_police", "friendship", "meeting"],
    "乐干": ["intelligence_police", "friendship", "meeting"],
    "党丕修": ["intelligence_police", "friendship", "meeting"],
    "刘钦礼": ["intelligence_police", "friendship", "meeting"],
    "聂琮": ["intelligence_police", "friendship", "meeting"],
    "周关锠": ["intelligence_police", "friendship", "meeting"],
    "马志超": ["intelligence_police", "friendship", "meeting"],
    "毛万里": ["intelligence_police", "friendship", "meeting"],
    "郭履洲": ["intelligence_police", "friendship", "meeting"],
    "杨震裔": ["intelligence_police", "friendship", "meeting"],
    "刘戈青": ["intelligence_police", "friendship", "meeting"],
    "郑修元": ["intelligence_police", "friendship", "meeting"],
    "陶一珊": ["intelligence_police", "friendship", "meeting"],
    "何峨芳": ["intelligence_police", "friendship", "meeting"],
    "张辅邦": ["intelligence_police", "friendship", "meeting"],
    "黄加持": ["intelligence_police", "friendship", "meeting"],
    "李培楠": ["intelligence_police", "friendship", "meeting"],
    "刘光朝": ["intelligence_police", "friendship", "meeting"],
    "贾秀升": ["intelligence_police", "friendship", "meeting"],
    "王志超": ["intelligence_police", "friendship", "meeting"],
    "范炳文": ["classmate_colleague", "friendship", "meeting"],
    "高向果": ["classmate_colleague", "friendship", "meeting"],
    "左思元": ["classmate_colleague", "friendship", "meeting"],
    "武成祖": ["classmate_colleague", "friendship", "meeting"],
    "李友平": ["classmate_colleague", "friendship", "meeting"],
    "苏桐凤": ["classmate_colleague", "friendship", "meeting"],
    "田荣祖": ["classmate_colleague", "friendship", "meeting"],
    "张庆恩": ["classmate_colleague", "friendship", "meeting"],
    "谢文津": ["classmate_colleague", "friendship", "meeting"],
    "王有为": ["classmate_colleague", "friendship", "meeting"],
    "韦宪文": ["classmate_colleague", "friendship", "meeting"],
    "杨作芝": ["classmate_colleague", "friendship", "meeting"],
    "冯大轰": ["classmate_colleague", "friendship", "meeting"],
    "房秉符": ["classmate_colleague", "friendship", "meeting"],
    "张彝鼎": ["classmate_colleague", "friendship", "meeting"],
    "杨治泰": ["classmate_colleague", "friendship", "meeting"],
    "牛焕辰": ["classmate_colleague", "friendship", "meeting"],
    "李思聪": ["classmate_colleague", "friendship", "meeting"],
    "郝家驹": ["classmate_colleague", "friendship", "meeting"],
    "刘士烈": ["classmate_colleague", "friendship", "meeting"],
    "温松康": ["classmate_colleague", "friendship", "meeting"],
    "张岫岚": ["classmate_colleague", "friendship", "meeting"],
    "陈汝淦": ["classmate_colleague", "friendship", "meeting"],
    "潘秀仁": ["classmate_colleague", "friendship", "meeting"],
    "袁寄滨": ["classmate_colleague", "intelligence_police", "meeting"],
    "陈谦": ["classmate_colleague", "intelligence_police", "meeting"],
    "丁继曾": ["classmate_colleague", "intelligence_police", "meeting"],
    "叶霞翟": ["classmate_colleague", "intelligence_police", "meeting"],
    "谢贵诚": ["classmate_colleague", "intelligence_police", "meeting"],
    "马敬华": ["classmate_colleague", "intelligence_police", "meeting"],
    "赵龙文": ["classmate_colleague", "intelligence_police", "meeting"],
    "姬梅轩": ["friendship", "meeting"],
    "杨觉民": ["friendship", "meeting"],
    "武树华": ["friendship", "meeting"],
    "李友芝": ["friendship", "meeting"],
    "申有枝": ["friendship", "meeting"],
    "赵富瑞": ["friendship", "meeting"],
    "韩克温": ["friendship", "meeting"],
    "于华庭": ["friendship", "meeting"],
    "李海涵": ["friendship", "meeting"],
    "杨庭芳": ["friendship", "meeting"],
    "朱耀武": ["friendship", "meeting"],
    "王利秋": ["friendship", "meeting"],
    "尚厚庵": ["friendship", "meeting"],
    "胡鸿章": ["friendship", "meeting"],
    "霍来庭": ["friendship", "meeting"],
    "童秀明": ["friendship", "meeting"],
    "王玉宾": ["friendship", "meeting"],
    "李钟桂": ["marriage_context", "public_debate", "meeting"],
    "吴俊才": ["teacher_student", "academic", "meeting"],
    "王新德": ["classmate_colleague", "friendship"],
    "孟大中": ["classmate_colleague", "friendship", "witness"],
    "孟大强": ["family"],
    "查良钊": ["academic", "witness"],
    "彭立云": ["fictional"],
    "孔昭庆": ["fictional"],
    "仁井田陞": ["academic", "spiritual"],
    "丘宏达": ["academic", "public_debate"],
    "陈继盛": ["academic", "public_debate"],
    "陈隆志": ["academic", "public_debate"],
    "陈少廷": ["public_debate"],
    "关中": ["public_debate", "politician", "academic"],
    "许信良": ["public_debate", "politician"],
    "张俊宏": ["public_debate", "politician"],
    "吴章铨": ["publishing", "correspondence"],
    "史静波": ["publishing", "correspondence"],
    "王芳华": ["meeting"],
    "连家立": ["friendship", "meeting"],
    "汪中磊": ["friendship", "meeting"],
    "王昇": ["politician", "military_figure"],
    "王济中": ["prison_admin", "politician"],
    "孙运璿": ["politician"],
    "游荣茂": ["politician", "public_debate"],
    "李志鹏": ["politician", "public_debate"],
    "温士源": ["politician", "public_debate"],
    "程国强": ["classmate_colleague", "friendship"],
    "周清玉": ["media", "publishing"],
    "赖文良": ["public_debate"],
    "朱石炎": ["legal_official"],
    "赵培鑫": ["friendship", "meeting"],
    "连培如": ["friendship", "meeting"],
    "柯贤忠": ["prison_medical", "politician"],
    "狄德罗": ["spiritual"],
    "史华格": ["spiritual"],
    "梭维斯特": ["spiritual"],
    "左丘明": ["spiritual"],
    "陆象山": ["spiritual"],
    "黄中国": ["case_prison", "litigation"],
    "高时运": ["case_prison", "politician"],
    "李国龙": ["case_prison"],
    "古永城": ["underworld"],
    "李盛渊": ["underworld"],
    "俞中兴": ["underworld", "case_prison"],
    "汪梦湘": ["intelligence_police", "military_figure", "publishing", "friendship", "public_debate"],
    "胡炎汉": ["case_prison", "political_dissident"],
    "陈独秀": ["academic", "politician", "spiritual"],
    "鲁迅": ["academic", "spiritual"],
    "李伋": ["spiritual"],
    "李玄伯": ["teacher_student", "academic"],
    "罗志希": ["publishing", "politician"],
    "赵元任": ["academic"],
    "李德林": ["in_law"],
    "尹女士": ["in_law", "nickname"],
    "王家桢": ["politician"],
    "王墨林": ["meeting"],
    "李鼎彝": ["family", "academic"],
    "陈凝秋": ["teacher_student", "academic"],
    "王贵民": ["meeting", "publishing"],
    "吴焕章": ["friendship", "meeting"],
    "温茂林": ["meeting", "household_staff"],
    "李纯仁": ["family"],
    "丁锡庆": ["in_law"],
    "周翔举": ["friendship", "meeting"],
    "詹永杰": ["friendship", "classmate_colleague"],
    "严停云": ["publishing"],
    "李子卓": ["in_law", "politician"],
    "关颂韬": ["meeting"],
    "徐伟森": ["friendship", "meeting"],
    "周桐雨": ["meeting"],
    "徐国材": ["in_law"],
    "张桂贞": ["family"],
    "顾维钧": ["spiritual", "politician"],
    "张莘夫": ["friendship"],
    "李锡恩": ["academic", "politician"],
    "陈纳德": ["military_figure", "spiritual"],
    "马歇尔": ["spiritual", "military_figure", "politician", "legal_official"],
    "詹姆斯·法兰克": ["spiritual"],
    "詹姆斯·杜渥": ["spiritual"],
    "周克敏": ["in_law"],
    "孙念台": ["teacher_student", "academic", "meeting"],
    "张作相": ["politician"],
    "王靖雯": ["media"],
    "西门庆": ["fictional"],
    "刘半农": ["spiritual"],
    "黄毅辛": ["case_prison"],
    "崔积泽": ["case_prison", "friendship"],
    "王云五": ["publishing", "politician"],
    "林正杰": ["media", "public_debate", "politician"],
    "黄信介": ["politician", "political_dissident", "media", "public_debate"],
    "骆学良": ["media", "publishing", "correspondence"],
    "安瑞甫": ["media", "meeting"],
    "刘绍唐": ["publishing", "media", "meeting"],
    "谢然之": ["party_propaganda", "public_debate"],
    "吴祥辉": ["media", "public_debate"],
    "蒋家语": ["correspondence", "witness"],
    "郑南榕": ["martyr", "media", "political_dissident", "friendship", "meeting", "correspondence"],
    "邱义仁": ["media", "politician", "public_debate"],
    "林世煜": ["media", "public_debate"],
    "余陈月瑛": ["politician", "public_debate"],
    "曾心仪": ["publishing", "political_dissident"],
    "邓维桢": ["media", "political_dissident", "public_debate"],
    "刘福增": ["academic", "public_debate"],
    "黄昭堂": ["political_dissident", "politician", "public_debate"],
    "邹纾予": ["intelligence_police"],
    "门肯": ["spiritual", "academic"],
    "蔡文崧": ["litigation"],
    "余主管": ["torture_actor", "nickname"],
    "郑主管": ["torture_actor", "nickname"],
    "戴布兹": ["spiritual", "political_dissident"],
    "基辛格": ["politician", "spiritual"],
    "宋希濂": ["military_figure", "publishing", "correspondence", "public_debate", "meeting"],
    "傅朝枢": ["publishing", "meeting"],
    "刘宜良": ["media", "publishing"],
    "大风": ["publishing", "correspondence"],
    "李蓝": ["publishing", "media", "meeting"],
    "汪东林": ["publishing"],
    "俞济时": ["military_figure", "politician"],
    "孙元良": ["military_figure", "publishing"],
    "张达钧": ["publishing", "military_figure"],
    "邓小平": ["politician", "spiritual"],
    "庾信": ["spiritual"],
    "桓谭": ["spiritual"],
    "杜预": ["spiritual", "military_figure"],
    "苏轼": ["spiritual"],
    "李霁野": ["academic", "publishing"],
    "张宗昌": ["military_figure", "politician"],
    "亚丹": ["publishing", "correspondence"],
    "宇野精一": ["academic"],
    "台静农": ["academic", "publishing", "meeting", "public_debate"],
    "侯立朝": ["intelligence_police", "publishing", "public_debate"],
    "陈果夫": ["politician", "spiritual"],
    "葛县长": ["politician", "litigation"],
    "冀元铎": ["intelligence_police", "litigation"],
    "陶百川": ["legal_official", "politician"],
    "钱思亮": ["academic", "meeting"],
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
    "施启扬": ["classmate_colleague", "legal_official", "politician", "public_debate", "meeting"],
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
    "李济": ["academic", "public_debate"],
    "姚渔湘": ["academic", "meeting"],
    "李朝宗": ["intelligence_police", "litigation"],
    "姜穆": ["litigation"],
    "王惺三": ["legal_official"],
    "端木恺": ["legal_official"],
    "李孟谦": ["family"],
    "李文钧": ["family"],
    "李景生": ["family", "nickname"],
    "王小屯": ["in_law", "romance"],
    "小蕾": ["romance", "nickname", "meeting"],
    "咪咪": ["romance", "nickname", "classmate_colleague"],
    "勘勘": ["family", "nickname"],
    "谌谌": ["family", "nickname"],
    "小八": ["family", "nickname"],
    "陈立峰": ["publishing"],
    "李方桂": ["academic", "meeting"],
    "余光中": ["academic", "publishing", "meeting"],
    "周作人": ["academic", "spiritual"],
    "札奇斯钦": ["academic", "classmate_colleague", "meeting"],
    "史为鉴": ["academic", "publishing", "meeting"],
    "汪荣祖": ["academic", "publishing", "correspondence", "meeting"],
    "庄申": ["correspondence", "academic"],
    "李其泰": ["academic"],
    "陈正澄": ["classmate_colleague", "academic", "publishing"],
    "钱穆": ["academic", "correspondence", "meeting", "public_debate"],
    "雷震": ["political_dissident", "publishing", "media"],
    "康白": ["meeting", "correspondence"],
    "周康熙": ["property_finance", "litigation"],
    "萧广仁": ["property_finance", "litigation"],
    "毛四": ["legal_official"],
    "王文发": ["prison_guard", "prison_admin", "torture_actor"],
    "王黄双": ["litigation"],
    "黄彩琴": ["litigation", "witness", "property_finance"],
    "刘辰旦": ["case_prison", "meeting", "friendship", "political_dissident", "torture_victim"],
    "吴忠信": ["case_prison", "political_dissident", "torture_victim"],
    "郭荣文": ["case_prison", "political_dissident", "torture_victim"],
    "詹重雄": ["case_prison", "meeting", "political_dissident", "torture_victim"],
    "季贵成": ["intelligence_police", "torture_actor"],
    "吴彰炯": ["intelligence_police", "military_figure", "torture_actor"],
    "郭刑警": ["intelligence_police", "torture_actor"],
    "刘刑警": ["intelligence_police", "torture_actor"],
    "张耀华": ["intelligence_police", "military_figure"],
    "魏宜智": ["intelligence_police"],
    "尤元基": ["intelligence_police"],
    "王剑吟": ["intelligence_police"],
    "尹俊": ["intelligence_police", "military_figure"],
    "王洁中": ["intelligence_police", "military_figure"],
    "李元簇": ["legal_official", "prison_admin", "politician"],
    "汪文吉": ["case_prison", "litigation", "in_law"],
    "李文荣": ["case_prison", "meeting", "torture_victim", "witness"],
    "曾庆璧": ["prison_admin", "legal_official", "correspondence"],
    "王伟珍": ["intelligence_police", "case_prison"],
    "李世杰": ["intelligence_police", "case_prison"],
    "吴锦江": ["case_prison", "political_dissident"],
    "吴荣元": ["case_prison", "political_dissident", "correspondence"],
    "陈鸿渐": ["intelligence_police", "case_prison", "torture_actor"],
    "蔡俊军": ["case_prison"],
    "沈之岳": ["intelligence_police"],
    "蔡金铿": ["political_dissident"],
    "吴松枝": ["political_dissident"],
    "赵清泉": ["witness"],
    "杨英龙": ["case_prison", "torture_victim"],
    "刘伟民": ["case_prison", "torture_victim"],
    "徐开喜": ["case_prison", "witness"],
    "黄祥华": ["prison_guard", "witness"],
    "谭坤泉": ["prison_guard", "witness", "torture_victim"],
    "朱光军": ["prison_admin", "prison_guard"],
    "汪本流": ["prison_admin"],
    "毛世馨": ["prison_admin"],
    "陈晏庭": ["case_prison"],
    "王建福": ["case_prison"],
    "李聪明": ["case_prison", "torture_victim"],
    "林荣宗": ["case_prison", "torture_victim"],
    "欧阳坤": ["case_prison"],
    "陈廷柳": ["case_prison"],
    "陈金凤": ["prison_guard", "property_finance", "litigation"],
    "汪宾彬": ["property_finance", "litigation"],
    "黄道舜": ["prison_guard", "torture_actor"],
    "雷志云": ["prison_guard", "torture_actor"],
    "陈庆堂": ["case_prison", "torture_victim", "litigation"],
    "林浩兴": ["case_prison", "torture_victim"],
    "苏振崧": ["case_prison", "torture_victim"],
    "卞昭荃": ["case_prison", "torture_victim"],
    "刘台生": ["case_prison", "torture_victim"],
    "熊钰铮": ["case_prison", "property_finance"],
    "林堂正": ["prison_guard"],
    "孟昭熙": ["intelligence_police", "prison_admin"],
    "蔡火炮": ["politician"],
    "蔡国扬": ["case_prison"],
    "徐鹏举": ["case_prison"],
    "林宗科": ["case_prison", "property_finance"],
    "杨次长": ["prison_admin", "nickname"],
    "洪炳麟": ["case_prison", "politician"],
    "蔡甘清": ["case_prison", "politician"],
    "陈清华": ["prison_guard", "litigation"],
    "程台生": ["prison_guard", "litigation"],
    "李新冰": ["prison_guard", "litigation"],
    "黄永寿": ["prison_guard", "torture_actor"],
    "黄铭强": ["prison_guard", "torture_actor"],
    "张树忠": ["prison_guard", "property_finance"],
    "温锦丰": ["prison_guard", "property_finance"],
    "赖锡志": ["prison_guard", "property_finance", "litigation"],
    "丘国利": ["prison_guard", "witness"],
    "李焕升": ["prison_guard", "witness"],
    "张国杰": ["case_prison", "torture_victim"],
    "吴尚纬": ["prison_guard", "torture_actor", "litigation"],
    "许文志": ["prison_guard", "torture_actor", "litigation"],
    "魏文龙": ["prison_guard", "torture_actor", "litigation"],
    "屠寄": ["prison_guard", "property_finance"],
    "金亚平": ["prison_medical", "prison_admin"],
    "王护士": ["prison_medical"],
    "黄仁温": ["case_prison", "prison_medical"],
    "晁煜": ["case_prison", "prison_medical"],
    "童聪明": ["prison_guard", "property_finance"],
    "张顺良": ["case_prison", "property_finance"],
    "庄建国": ["prison_guard", "property_finance"],
    "董嘉诚": ["prison_admin"],
    "谢骏扬": ["prison_guard"],
    "陈金树": ["case_prison", "property_finance"],
    "林丰翔": ["case_prison", "property_finance"],
    "林河南": ["case_prison", "property_finance"],
    "刘家昌": ["media", "meeting"],
    "赵天仪": ["academic"],
    "张齐斌": ["politician"],
    "朱婉坚": ["publishing", "in_law", "property_finance", "litigation"],
    "王剑芬": ["romance", "in_law", "trust_property", "property_finance", "litigation"],
    "胡茵梦": ["romance", "in_law", "trust_property", "litigation", "media"],
    "刘会云": ["publishing", "litigation", "property_finance"],
    "冯作民": ["correspondence", "litigation", "property_finance"],
    "陈苾仙": ["in_law", "property_finance", "litigation"],
    "王国樑": ["in_law", "family", "property_finance", "litigation"],
    "何秀煌": ["in_law", "witness"],
    "孟祥柯": ["witness"],
    "段宏俊": ["witness"],
    "璩诗方": ["witness", "in_law", "trust_property", "correspondence"],
    "刘维斌": ["witness", "trust_property"],
    "刘望苏": ["property_finance"],
    "叶肇模": ["property_finance", "litigation"],
    "萧近仁": ["property_finance", "litigation"],
    "高仲元": ["property_finance", "litigation"],
    "陈子和": ["property_finance"],
    "张任飞": ["property_finance"],
    "周荃": ["media", "friendship", "meeting"],
    "严智径": ["media", "meeting"],
    "邓育昆": ["media", "correspondence"],
    "商钟": ["media", "meeting"],
    "司马笑": ["media", "meeting"],
    "刘建德": ["social_case"],
    "徐端": ["social_case", "military_figure"],
    "兰风": ["social_case", "military_figure"],
    "王桂燕": ["social_case"],
    "小共产党": ["fictional"],
    "胡牧师": ["fictional"],
    "萧同兹": ["publishing", "family", "politician"],
    "童有德": ["legal_official", "litigation"],
    "陈聪明": ["legal_official", "litigation"],
    "李永然": ["lawyer_counsel", "litigation"],
    "龙云翔": ["lawyer_counsel", "litigation", "correspondence"],
    "廖茂荣": ["legal_official", "litigation"],
    "蒋女士": ["romance", "property_finance"],
    "许女士": ["romance"],
    "马丁·恩纳尔斯": ["meeting", "human_rights"],
    "孔东梅": ["meeting", "academic", "public_debate"],
    "金美龄": ["political_dissident", "media", "public_debate"],
    "刘长乐": ["media", "meeting"],
    "马萨利克": ["spiritual"],
    "张伯英": ["spiritual"],
    "许景澄": ["spiritual"],
    "陈云裳": ["spiritual"],
    "汪敬煦": ["military_figure", "meeting"],
    "陶冬冬": ["meeting"],
    "习近平": ["politician", "spiritual"],
    "徐邦达": ["academic", "spiritual"],
    "谢稚柳": ["academic", "spiritual"],
    "启功": ["academic", "spiritual"],
    "杨仁愷": ["academic", "spiritual"],
    "刘九庵": ["academic", "spiritual"],
    "傅熹年": ["academic", "spiritual"],
    "谢辰生": ["academic", "spiritual"],
    "陈支平": ["academic", "meeting"],
    "封德屏": ["publishing", "media"],
    "应凤凰": ["publishing"],
    "钟丽慧": ["publishing"],
    "李瑞腾": ["publishing", "academic"],
    "陈文芬": ["media"],
    "陈奇禄": ["academic", "politician", "publishing"],
    "赵宁": ["media", "meeting"],
    "蒋廷黻": ["academic", "publishing", "spiritual", "public_debate"],
    "郑板桥": ["spiritual"],
    "江青": ["spiritual"],
    "周才蔚": ["correspondence", "friendship"],
    "黄祝贵": ["teacher_student", "academic"],
    "吴心柳": ["publishing", "correspondence", "friendship"],
    "简志信": ["friendship", "property_finance"],
    "简瑞甫": ["friendship", "property_finance"],
    "洪金立": ["correspondence", "friendship"],
    "左伯桃": ["spiritual"],
    "程婴": ["spiritual"],
    "吴文立": ["classmate_colleague", "meeting", "witness"],
    "吴申叔": ["friendship", "publishing", "meeting", "family"],
    "郁慕明": ["politician", "friendship", "litigation", "meeting"],
    "欧卡曾": ["case_prison", "meeting", "nickname"],
    "连战": ["politician", "public_debate"],
    "余传韬": ["meeting", "academic"],
    "陈博享": ["legal_official", "litigation"],
    "艾玫": ["correspondence", "in_law"],
    "宋美龄": ["politician", "public_debate"],
    "居浩然": ["correspondence", "friendship", "academic", "publishing", "meeting"],
    "余纪忠": ["media", "publishing", "meeting", "friendship", "public_debate"],
    "张世民": ["classmate_colleague", "friendship", "meeting"],
    "蒋梦麟": ["academic", "politician", "meeting", "public_debate"],
    "杜致勇": ["family", "meeting"],
    "张白帆": ["publishing", "friendship", "meeting"],
    "夏君璐": ["teacher_student", "meeting", "correspondence"],
    "居蜜": ["family", "correspondence", "academic"],
    "章尊良": ["property_finance"],
    "林紫耀": ["witness", "property_finance", "litigation"],
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
    "项迺光": ["indoctrination", "intelligence_police", "friendship", "meeting"],
    "周道济": ["indoctrination"],
    "王洸": ["indoctrination"],
    "屠炳春": ["indoctrination"],
    "任卓宣": ["indoctrination", "public_debate"],
    "柴松林": ["indoctrination"],
    "魏萼": ["indoctrination"],
    "邬昆如": ["indoctrination"],
    "魏以之": ["intelligence_police", "public_debate"],
    "史与为": ["intelligence_police", "political_dissident"],
    "胡汝森": ["military_figure", "party_propaganda", "publishing"],
    "陈启天": ["public_debate", "politician"],
    "于长城": ["political_dissident"],
    "于长庚": ["political_dissident"],
}

EXACT_NAME_SET = NONSTANDARD_NAMES | set(CURATED_IDENTITIES) | set(ALIASES)
NONSTANDARD_NAME_RE = re.compile("|".join(map(re.escape, sorted(EXACT_NAME_SET, key=len, reverse=True))))

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

PROPERTY_FINANCE_CUES = (
    "房地", "房产", "土地", "产权", "财产", "债务", "欠债", "还钱", "借贷", "借钱",
    "过户", "委任书", "协议书", "债权", "收益权", "保证金", "存款", "支票",
)

TRUST_PROPERTY_CUES = (
    "信托", "信托关系", "信托意思", "意思表示中止", "天母静庐", "权状", "存证信",
)

TORTURE_VICTIM_CUES = (
    "刑求", "逼供", "苦刑", "灌水", "绑担架", "拳头", "巴掌", "木棍", "脱去我的衣服",
    "被捕入狱", "冤案", "假案",
)

TORTURE_ACTOR_CUES = (
    "刑求", "逼供", "办案人员", "专案小组", "警总", "调查局", "保安处", "刑警",
    "拳头", "巴掌", "木棍", "绑我的", "绑担架", "大打其耳光", "皮鞭打", "凌虐",
)

WITNESS_CUES = (
    "见证", "证人", "公证书", "签名可证", "结证",
)

PUBLISHING_CUES = (
    "编辑", "主编", "出版", "出版社", "杂志", "报纸", "写稿", "投稿", "序", "书店", "文星",
)

ACADEMIC_CUES = (
    "研究", "学者", "博士", "学术", "史学", "传记", "论文", "大学", "台大", "北大",
)

MEDIA_CUES = (
    "记者", "访谈", "采访", "访问", "受访", "报导", "报道", "报人", "副总编辑",
    "记者招待会", "节目", "电视", "广播", "导演",
)

LEGAL_OFFICIAL_CUES = (
    "法官", "审判长", "审判官", "检察官", "检察长", "书记官", "庭长", "推事",
)

LAWYER_COUNSEL_CUES = (
    "律师", "辩护人", "公设辩护人", "委由", "去函", "代理", "辩护", "见证",
)

PRISON_ADMIN_CUES = (
    "司法行政部", "法务部", "监狱", "看守所", "典狱长", "所长", "副所长", "秘书",
    "课长", "主任", "名籍室", "卫生课", "福利社", "戒护课长", "台北监狱", "台北看守所",
)

PRISON_GUARD_CUES = (
    "管理员", "主任管理员", "临时管理员", "课员", "戒护", "戒护课长", "看守所",
    "脚镣", "手铐", "钉脚镣", "舍房", "抄房", "接见", "放封", "杂役", "岗哨",
)

PRISON_MEDICAL_CUES = (
    "卫生课", "健康检查", "保外就医", "病房", "疗伤",
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

PARTY_PROPAGANDA_CUES = (
    "宣传", "国民宣传", "中央委员会第四组", "第四组主任", "党务", "党限", "查禁", "封闭文星",
)

SPIRITUAL_CUES = (
    "读", "思想", "著作", "作品", "名言", "引用", "书中", "书里", "历史上", "古代",
    "古人", "哲学", "主义", "诗", "文学", "说过", "所谓", "比喻", "像", "想象力",
)

ROLE_SUFFIXES = (
    "先生", "女士", "小姐", "太太", "夫人", "教授", "博士", "法官", "律师", "检察官", "审判长",
    "审判官", "书记官", "院长", "庭长", "校长", "主席", "总统", "部长", "将军", "上校", "少将",
    "中将", "作家", "编辑", "总编辑", "副总编辑", "记者", "导演", "委员", "同学", "老师", "所长", "副所长",
    "典狱长", "管理员", "主任管理员", "临时管理员", "戒护课长", "课员",
)

BAD_NAME_CHARS = set("的一是在不了和与及或而也就都被把让给对从向于以为着过吗呢啊呀吧里中上下前后内外时日年月个些其此那这我你他她它们")
BAD_ENDINGS = (
    "先生", "小姐", "太太", "教授", "博士", "法官", "律师", "研究", "真面", "全集", "文集",
    "目录", "自序", "序言", "附录", "一文", "一书", "主义", "政府", "法院", "法庭", "国民",
    "民进", "共产党", "自由", "中国", "台湾", "美国", "日本", "香港", "北京", "台北",
)
BAD_ENDING_CHARS = set("部党会社院局处署队军报刊界学史论节集号法罪案书文稿语话事影研省市县馆系志敌间物")
STOP_NAMES = {
    "红色", "房到十", "从头", "那家伙", "阴险无", "安处押", "高院刑",
    "常业", "谢两位", "党出身", "胡适说", "查肛门", "张坏嘴",
    "广告", "怀念周", "方封杀", "别再做", "台独英", "殷门弟", "那儿",
    "成绩单", "万字", "乐园", "阴险", "温情主", "高楼", "严侨死",
    "蒋政权", "史家胡", "童子尿", "温旧梦", "曾有之", "李杰伴",
    "国父纪", "李飞刀", "和国", "万岁评", "乌鸦评", "冷暖",
    "宣传车", "和稀泥", "国公民", "高官", "高朋满",
    "张淑婉",
    "查禁清", "方理由", "家作品", "文星杂", "常说", "范儿童",
    "惠予更", "雷震做", "时刘长", "尚勤同", "时扣押", "辛勤耕", "别信",
    "李敖", "李先", "李大师", "李先生", "李语", "李文", "李书", "李政", "王法", "王国", "王军",
    "中国人", "台湾人", "美国人", "日本人", "英国人", "国民党", "民进党", "共产党", "新闻界",
    "文化界", "政治犯", "外省人", "台湾话", "负责人", "发行人", "总编辑", "编者略", "不自由",
    "文星", "台独", "红卫兵", "利益", "文学", "宣传", "支持", "成立", "毕业", "党员", "司令", "权力",
    "李委员", "李部长", "林委员", "罗委员", "丁委员", "苏委员", "许委员", "赵委员", "沈委员",
    "王院长", "李院长", "张院长", "张主任", "陈主任", "梁司长", "姚局长", "吴主任", "胡主任",
    "高主任", "主席", "敖曼", "敖质询", "敖发言", "敖询问", "国防委", "席官员", "席建议",
    "席告诉", "席委员", "席请问", "席质询", "席投票", "席只问", "席发现", "台独公",
    "国智慧", "程序委", "程序问", "程序来", "党协商", "国防", "武器", "公投", "国人来",
    "国旗", "国庆", "国防政", "国国籍", "国走狗", "国主子", "全院各", "全体立", "全部立",
    "解释", "解释权", "东西", "国家安", "应该要", "应该很", "应该知", "应该去", "时进行",
    "时间到", "谢谢", "谢谢李", "谢谢主", "谢谢审", "公开答", "和总统", "须告诉", "台唱戏",
    "平奖得", "苏审计", "文忠", "明宪", "金平", "马哥", "苏老头", "能打仗", "能讲",
    "高金素", "国人", "白纸黑", "成功", "方面", "解决", "纪录", "文件", "卫能力",
    "林审计", "蒙藏委", "台独坐", "纪律委", "蓝绿", "文豪氏", "苏起委", "万票",
    "和陈水", "安全利", "任行政", "马主席", "包括李", "陈校长", "巴拿马", "林主任",
    "相条例", "叶女士", "常清楚", "宣誓", "阴门阵", "和子", "却见残", "周公何",
    "常深入", "水花名", "郑主任", "史会证", "成擒", "强奸犯", "国会半",
    "单位", "程序", "任期", "别表扬", "周郎顾", "李杰老", "马屁精", "山宣誓",
    "党观", "平岛纠", "马哥黄", "全寿", "家长", "平奖相", "荣等提", "李杰却",
    "能担任", "宰掉", "时国防", "经费", "张照片", "从来没", "于尽",
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
    "路人", "东方望先", "张灏跑", "班马宏", "马丁见",
    "权术", "万元", "仇录", "利用", "安慰", "顾问", "家庭", "胡说八", "武纪", "班亡",
    "花样", "文学侍", "文人", "红帽子", "怀念", "苍生", "宣示", "东问西", "家断绝",
    "时拼命", "家庭版", "纪法国", "胡适纪", "明笔录", "强邻问", "宣淫纪", "陆根纪",
    "东郭纪", "白露纪", "彭尸纪", "殷鉴纪",
    "文星出", "文库", "余悸", "水来", "充分", "国情殷", "文星带", "万机", "车夫",
    "简编", "文星合", "党国", "关照", "强迫", "公务员",
    "别人肯", "强打度", "高兴记", "古今景", "艾玫再", "丰富资", "于字典",
    "何凡等", "党政双", "党政方", "却硬要", "古人先", "孟能决", "宁滥毋",
    "文告", "时使人", "曾蒙彭", "曾说所", "李宁访", "李济晤", "柏杨朋",
    "查扣作", "段数之", "毛必先", "祝代表", "解头脑", "那本希", "那车子",
    "陈吴二", "高情雅", "黄怡带", "于天厨", "从绚丽", "别人机", "别加说",
    "别说四", "华宿舍", "孙案发", "居到结", "山工程", "张便条", "房法律",
    "房间先", "文字太", "文星关", "文星签", "时有信", "时雇员", "曾亲批",
    "查禁李", "步谈好", "满脸买", "白天到", "花捧场", "解奇特", "边说边",
    "通知萧", "闻责任", "鲁迅搞", "麻烦之", "麻省理", "别人保", "那天余",
    "都当成", "充东洋", "华民族", "从之臣", "成群结", "花八门", "白痴",
    "闻局长", "任何男", "诸君子", "居心",
    "解已有", "党四人", "公婆", "和刑求", "应予", "支援买", "施政说",
    "柏杨吃", "班者同", "胡适干", "胡适纵", "艾玫长", "苗族酷", "诸彭老",
    "都出现", "都床藏", "钱焉", "任讲座", "公益有", "向高雄", "席之函",
    "时申请", "曾综合", "查办颟", "王府姨", "通风维", "那丑八", "别人结",
    "居之义", "公差到", "包括蒋", "干脆蒋", "黄三三", "权威彭",
    "关系来", "台独五", "师事彭", "时死去", "公益", "怀恩堂",
    "向别人", "张权利",
    "满天飞", "别人情", "燕归迟",
    "蒋家父", "丰功伟",
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
    "管理员", "封信", "方式", "公道", "安全", "台南美", "全权代", "家爸爸", "国际特",
    "通讯", "熊来", "熊往", "云乎哉", "公然抹", "高院推", "罗织人", "从主流",
    "皮蛋", "李放使", "李放", "能见到", "文书之", "房租", "公道终", "印刷者",
    "查起诉", "甘共苦", "终之资", "和深度", "明告",
    "水到", "权益", "司法单", "水果", "和实际", "敖按", "印刷精", "国人权",
    "时副总", "经监务", "时平行", "全部契", "别人杂", "国父孙", "国家有",
    "应俱全", "祖国正", "苍天", "温杯", "公道没", "关怀照", "利润之",
    "家人放", "居人", "山盟", "常人无", "文星替", "时身受", "程序要",
    "管教", "终难深", "谢签名", "雷管", "彭相识", "谢交往", "权贵角",
    "马桶有", "管理条", "经手人", "萧某之", "都异口", "都得照",
    "于本庭", "于赴义", "关系够", "却遭到", "和平", "家属之", "山林起",
    "强盗钉", "时失去", "时抨击", "明写", "曲解", "曾明写", "权使用",
    "李放同", "查出胡", "平奖",
    "林办理", "于自诉",
    "毛三", "干人", "任二人", "全所", "向主任", "向禁止", "家去取", "平分",
    "成事件", "时抄房", "查嘴巴", "查头顶", "班人", "籍股", "管主任", "经常特",
    "时说",
    "文化人", "能达成",
    "时候", "勾结", "都能", "居人还",
    "满意",
    "祖宗走",
    "空手",
    "詹姆斯",
    "胡适来",
    "李文许",
    "查处长", "公正", "国家", "关起来", "房子", "山北路", "向戴先", "史作证",
    "国家民", "和人", "文史出", "国特", "史料", "通知", "和马汉", "和李广",
    "华北同", "家书店", "却没有", "史学方", "文史社", "人凤局", "马之被",
    "高兴", "文字", "成什么", "国际关", "平生", "华北办", "任保密", "和介民",
    "任局长", "常生气", "张条子",
    "和李宗", "平定", "却说", "家李敖", "家破人",
    "相反", "相识", "干扰", "于先", "任赈灾", "路坐牢", "钱来", "怀仁堂",
    "和戴笠", "宁愿自", "山西主", "祖宗父", "能够控", "成任务", "那位毛",
    "和监察", "班筹备", "陆工作", "山东王", "东西来", "于两家", "任市长",
    "任所长", "关进同", "容满面", "应黄埔", "时介民", "时怀恨", "曾约汉",
    "王武等", "索讨", "闻讯", "于嫉恶", "华塘先", "常激烈", "戴笠合",
    "时指出", "曾自问", "沈醉苛", "空重要", "连军统", "那还能", "高才生",
    "幸好乔", "仰介民", "毛先生", "马有相",
    "时间由", "任法务", "何况宋", "尚有可", "计考核", "应付警", "时收到",
    "时间冲", "从孔子", "全靠钱", "堵截知", "房东之", "程度之", "蒋次数",
    "黄狗等", "却得自", "国际知", "李蓝说", "白宫", "白开水", "荣枯",
    "车赴车", "阎王", "时退伍", "连长坐",
    "于李园", "房来", "全民政", "赵红粉",
    "明地址", "国家兴", "和南榕", "应该效", "印发", "焦思", "利可图",
    "于纽约", "李蓝女", "祝撰安", "和平统", "怀念宋", "方党方",
    "山之趣", "时负责", "和出版", "印五千",
    "钱穆早", "钱穆有", "钱穆约", "钱穆谈", "钱穆通",
    "古奇才",
    "文章", "成绩", "台独分", "方便", "东吴", "东北同", "国文化", "牛肉面",
    "山楼", "相称", "和棒子", "文好", "宣言", "云云", "李某人", "全天候",
    "范围", "时期", "国五十", "干什么", "于胡适", "陶家班", "国者",
    "查禁", "封杀", "文化商", "关门",
    "明白", "文章发", "台独联", "焦点", "王八蛋", "敖之", "敖之先", "敖之先生",
    "和解", "路人马",
    "权派", "马屁", "平头", "和尚", "那种", "广义地", "松涵相", "时限期",
    "班好友", "却装腔", "高山族", "金乌龟", "金树荣",
    "雷震出", "胡适有", "胡适关", "胡适只", "胡适帮", "胡适相", "尚勤看",
    "时还目",
    "路费", "左脚同", "程序表", "明说", "金钱", "查照", "经常预",
    "公诉", "权利", "经招待", "水牛匿", "文星同", "毛坯", "敖之到",
    "能转陈", "严格地", "平静地", "文字洗", "毛贼近", "文化组", "盛情",
    "山居", "古话所", "吴出面",
    "时糊口", "简陋家",
    "罗织入", "曲情理", "向李敖", "和平东", "魏胖比", "苍茫", "时写出",
    "别检查", "班轮值", "别人远", "房屋", "应有借", "和执行", "宣布离",
    "方出身", "胡家", "和解乃", "平奖全", "都承认", "向侍者", "居十六",
    "彭来往", "彭要好", "时有辜", "魏说", "钱财", "关进来", "明白地",
    "荣膺五",
    "钱赎当", "干薪", "相当副", "时退回",
    "公布", "干人等", "东吴历", "方豪自", "文章底", "师方豪", "能揪出",
    "支持并", "方豪吃", "何要李", "却豪迈", "能容纳", "家身分",
    "尚勤信", "益增苦", "章有所", "解提出", "连跑带", "于校长",
    "步出", "李总统", "任国防",
    "索然", "许愿许", "时发现",
    "国传统", "公开信", "干净", "苏联", "曾说", "辛苦", "房门口", "农民", "纪念堂",
    "项证据", "国际人", "居然要", "应该可", "国两制", "能解决", "从参选", "解释清",
    "甘苦", "秋波", "国库", "经济", "成者", "国人只", "公职", "成立纯", "荣台独",
    "常客气", "花圣解", "林肯总", "党纪", "和阿扁", "关教育", "许主计", "林勤经",
    "钟委员", "隆情", "廖委员", "公决", "国同意", "何没有", "全面性", "却变成",
    "权贵之", "能否容", "车原理", "何本席", "何谓合", "国防问", "曾经跟", "王拓委",
    "钱追回", "于军购", "公开跟", "国家统", "国家领", "应该记", "李杰比", "尚往来",
    "公家信",
    "麻烦谢", "从行政", "任蒙藏", "党担任", "包括副", "席要跟", "方才林", "李杰李",
    "经会议", "党现任", "却招待", "国布什", "国防等", "方才卢", "时奥运", "诸蓝绿",
    "何部长", "林部长", "刘邦打", "古地图", "和力量", "和质询", "国亲两", "常入神",
    "幸早死", "张三", "成立精", "明质询", "曾砸掉", "花费七", "解基层", "谢谢林",
    "钟回答", "云诡谲", "任出身", "任命之", "党冲突", "包括谢", "却行使", "周三",
    "周出现", "周四要", "和军人", "和承诺", "和答复", "和美丽", "国会抢", "国政顾",
    "国防方", "国防费", "家庭成", "封疆", "师附跋", "常进行", "平奖花", "惠发言",
    "成功完", "文忠看", "时呼吁", "时宣告", "时提到", "时答复", "时老子", "时请坐",
    "时间限", "明清楚", "暨主播", "步提出", "燕委员", "盛衰", "解应有", "车到府",
    "连八载", "连战秉", "通讯簿", "那位蓝", "那位账", "那天刚", "那还开", "郝家父",
    "金牛比", "阴差阳", "高涨", "黄华未", "万赠款", "严格来", "于两周", "于亲北",
    "于古罗", "于现今", "从东京", "从党产", "仰马瞎", "充报告", "利益施", "别人要",
    "别再绿", "卫生环", "台之际", "台电", "吉尔说", "和习惯", "和阁揆", "国际挂",
    "孔同气", "常谦卑", "应该尽", "方发言", "时公布", "时却还", "时并行", "时强调",
    "时找高", "时继承", "时遭受", "时间合", "明墨", "步校老", "白种人", "相抵",
    "空转", "能出口", "苏起兄", "蓝绿随", "解很狭", "解独到", "计有", "路人说",
    "那部长", "都好战", "陆同胞", "黄华胞", "那种虚", "别人统", "连死去",
    "任何人", "相信", "习惯", "明定", "经历", "都有", "公开说", "公然违", "包东西",
    "于国防", "应该说", "文弄墨", "席会议", "常好", "陆军总", "从头到", "向国防",
    "东西还", "常严重", "强人意", "从国防", "别警告", "关资料", "席人员", "全体国",
    "相较", "解开",
    "那么好", "应该站", "施次长", "国策顾", "史背景", "陈述",
    "强者", "毛蒜皮",
    "孔子之", "应该有", "金门", "别提到", "韩国人",
    "相同", "何如何", "别注意", "终止", "蒙古", "通工具", "高潮", "连任", "高飞",
    "何解释", "章程", "从蒋经", "应该先", "国籍",
    "纪轻轻", "国纽约",
    "康检查", "和监狱", "终身职", "那次", "蓝色", "公开审", "向行政", "时表示",
    "方才有", "司空见惯", "黄埔", "陈诚说", "经由", "能出席", "平民化",
    "苏州人",
    "阴错阳", "都没有", "明书店", "全盘西", "凤凰电", "祖国行", "花要雾",
    "那破碎", "颜射", "于看到", "左道插", "杜家泪", "秋海棠", "龙之囚",
    "苗红", "通权达", "李鸿等", "于台独", "张试纸", "房独居", "国母养",
    "乐战士", "余韵", "成西门", "罗仿", "哥罗仿", "李文博", "钱者",
    "从结婚", "文贾祸", "单曝光", "和尚方", "家最早", "家有电", "师杨锦",
    "解很浅", "路遇宿", "钱记", "史系众", "师相", "文宣头", "王昇黑",
    "祖孙身", "童陈又", "管两头", "胡适批", "项比赛", "从生离", "台局长",
    "向之功", "方飞斧", "水平问", "公开攻", "林云眼", "国文差", "胡殷",
    "萧负李", "时碰到", "暴民", "严侨偷", "文坛十", "林云屠", "相叉腰",
    "蒋家专", "史工作", "胡适通", "陆记", "周荃做", "俞樾老", "孔殷",
    "方足言", "何必做", "成形", "李焕之", "路遇胡", "怀念李", "文指导",
    "和尚做", "尤清做", "成筹备",
    "成共匪", "于别人", "任何职", "任满自", "任职员", "公告地", "包括陈",
    "国家档", "应请改", "文字构", "文星闹", "方进度", "班林云", "花店送",
    "花掉国", "陶泓聊", "万劫归", "平来", "时查封", "班傅正", "班有臧",
    "白宫椭", "盖有神", "简报李", "路人去", "闻录", "时陷害", "窦丁谈",
    "别人鼓", "平会议", "时俱进",
    "麻醉师", "干女婿", "严门四", "伍记", "相扑目", "钱穆印", "陈诚之",
    "山独行", "印象奇", "曾经走", "安妇", "祖宗", "隆码头", "于吾师",
    "乌撒者", "于丧礼", "家庭三", "成谜", "别人看", "经兮兮", "国际笔",
    "明山庄", "查收", "温室气",
    "蒙难", "伏机", "国血统", "文化基", "家伙", "车阶级", "满洲记",
    "胡适送", "蒋氏父", "江英专", "党党员",
    "马迹",
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
    r"将军|上校|少将|中将|主编|编辑|记者|发行人|总编辑|所长|副所长|典狱长|庭长|"
    r"管理员|主任管理员|临时管理员|戒护课长|课员|委员)[^。！？；：:]{0,10}$"
)

CATEGORY_LABELS = {
    "meeting": "见面",
    "correspondence": "通信",
    "neighbor": "邻居",
    "teacher_student": "师生",
    "classmate_colleague": "同学同事",
    "friendship": "朋友",
    "martyr": "烈士殉难",
    "family": "亲属",
    "in_law": "姻亲",
    "marriage_context": "婚姻相关",
    "romance": "情感",
    "property_finance": "财产债务",
    "trust_property": "财产信托",
    "torture_victim": "刑求受害",
    "torture_actor": "刑求人员",
    "witness": "证人见证",
    "publishing": "出版",
    "academic": "学术",
    "scientist": "科学家",
    "media": "媒体",
    "household_staff": "家中雇员",
    "disability": "残障人士",
    "human_rights": "人权救援",
    "veteran": "老兵士官",
    "social_case": "社会案件",
    "anti_communist_defector": "反共人士",
    "medical_care": "医疗照护",
    "religion": "宗教人物",
    "indoctrination": "感化人员",
    "legal_official": "司法人员",
    "lawyer_counsel": "律师代理",
    "prison_admin": "监狱行政",
    "prison_guard": "看守戒护",
    "prison_medical": "监所医疗",
    "litigation": "诉讼",
    "case_prison": "同案狱友",
    "politician": "政治人物",
    "political_dissident": "政治异议者",
    "intelligence_police": "情治警务",
    "military_figure": "军事人物",
    "party_propaganda": "党务宣传",
    "underworld": "江湖人物",
    "public_debate": "公共论战",
    "spiritual": "神交引用",
    "fictional": "虚拟人物",
    "nickname": "称谓待考",
    "mentioned": "待复核",
}


def build_name_regex() -> re.Pattern[str]:
    compounds = "|".join(map(re.escape, sorted(COMPOUND_SURNAMES, key=len, reverse=True)))
    singles = re.escape("".join(sorted(set(SINGLE_SURNAMES))))
    # Chinese personal names in this corpus are mostly 2-3 chars. Compound surnames add one or two chars.
    return re.compile(rf"(?:{compounds})[\u4e00-\u9fff]{{1,2}}|[{singles}][\u4e00-\u9fff]{{1,2}}")


NAME_RE = build_name_regex()
FOREIGN_RE = re.compile("|".join(map(re.escape, sorted(FOREIGN_AND_HISTORICAL | FICTIONAL_CHARACTERS, key=len, reverse=True))))


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
    if name in ALWAYS_NAMES or name in ALIASES or name in NONSTANDARD_NAMES or name in CURATED_IDENTITIES:
        return True
    if name in STOP_NAMES:
        return False
    if name.startswith("李敖"):
        return False
    if name in FOREIGN_AND_HISTORICAL or name in FICTIONAL_CHARACTERS:
        return True
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
        ("property_finance", PROPERTY_FINANCE_CUES, 5),
        ("trust_property", TRUST_PROPERTY_CUES, 6),
        ("torture_victim", TORTURE_VICTIM_CUES, 5),
        ("torture_actor", TORTURE_ACTOR_CUES, 5),
        ("witness", WITNESS_CUES, 4),
        ("publishing", PUBLISHING_CUES, 4),
        ("academic", ACADEMIC_CUES, 4),
        ("media", MEDIA_CUES, 4),
        ("legal_official", LEGAL_OFFICIAL_CUES, 5),
        ("lawyer_counsel", LAWYER_COUNSEL_CUES, 5),
        ("prison_admin", PRISON_ADMIN_CUES, 5),
        ("prison_guard", PRISON_GUARD_CUES, 5),
        ("prison_medical", PRISON_MEDICAL_CUES, 5),
        ("litigation", LITIGATION_CUES, 4),
        ("case_prison", CASE_PRISON_CUES, 5),
        ("politician", POLITICIAN_CUES, 4),
        ("intelligence_police", INTELLIGENCE_POLICE_CUES, 4),
        ("military_figure", MILITARY_FIGURE_CUES, 4),
        ("public_debate", PUBLIC_DEBATE_CUES, 3),
        ("party_propaganda", PARTY_PROPAGANDA_CUES, 5),
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
            if suffix in LEGAL_OFFICIAL_CUES or suffix in ("法官", "检察官", "审判长", "审判官", "书记官", "推事"):
                scores["legal_official"] += 6
            elif suffix == "律师":
                scores["lawyer_counsel"] += 6
            elif suffix in ("所长", "副所长", "典狱长"):
                scores["prison_admin"] += 6
            elif suffix in ("管理员", "主任管理员", "临时管理员", "戒护课长", "课员"):
                scores["prison_guard"] += 6
            elif suffix in FAMILY_CUES:
                scores["family"] += 4
            elif suffix in TEACHER_STUDENT_CUES or suffix in ("教授", "博士"):
                scores["teacher_student"] += 5
                scores["academic"] += 2
            elif suffix in PUBLISHING_CUES or suffix in ("作家", "编辑"):
                scores["publishing"] += 4
            elif suffix in MEDIA_CUES or suffix in ("记者", "导演", "编辑", "总编辑", "副总编辑"):
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
    if name in FICTIONAL_CHARACTERS:
        scores["fictional"] += 4
    if not scores:
        return "mentioned", 0, []
    category, score = scores.most_common(1)[0]
    stronger_than_spiritual = [
        "meeting", "correspondence", "teacher_student", "family", "in_law", "romance",
        "legal_official", "lawyer_counsel", "prison_admin", "prison_guard", "prison_medical", "litigation", "case_prison",
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
        real_markers = (
            "《老子》", "老子曰", "老子说", "道德经", "老庄", "老子李耳",
            "老子的追随者", "老子一言不发", "徐甲", "李耳",
        )
        if any(marker in ctx for marker in real_markers):
            return False
        return True
    if name == "康德":
        return "感冒药康德" in ctx or "康德600" in ctx
    if name == "江南":
        false_markers = (
            "出发到江南", "守江南", "大江南北", "曲尽江南美女", "哀江南赋",
            "江南·江南·哀江南", "《江南·江南", "《哀江南", "江南并发症",
            "连江南都保不住", "江南廖家楠",
        )
        return any(marker in ctx for marker in false_markers)
    if name == "应凤凰":
        return "应凤凰电视" in ctx
    return False


def extract_from_text(
    text: str,
    path: Path,
    source_root: Path,
    people: dict[str, PersonHit],
    title_names: set[str],
) -> None:
    collection, book, chapter = meta_for_path(source_root, path)
    title_names = extract_title_names_from_strings((book, chapter))
    seen_matches: set[tuple[int, int, str]] = set()
    for regex in (NAME_RE, FOREIGN_RE, NONSTANDARD_NAME_RE):
        for match in regex.finditer(text):
            name = match.group(0)
            if not is_likely_person_name(name):
                continue
            if is_contextual_false_positive(name, text, match.start(), match.end()):
                continue
            name = ALIASES.get(name, name)
            match_key = (match.start(), match.end(), name)
            if match_key in seen_matches:
                continue
            seen_matches.add(match_key)
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


def extract_title_names_from_strings(raw_titles: tuple[str, ...] | list[str]) -> set[str]:
    names: set[str] = set()
    for raw in raw_titles:
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


def extract_title_names(source_root: Path, files: list[Path] | None = None) -> set[str]:
    names: set[str] = set()
    for path in files or iter_text_files(source_root):
        _collection, book, chapter = meta_for_path(source_root, path)
        names.update(extract_title_names_from_strings((book, chapter)))
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
    if hit.name in FICTIONAL_CHARACTERS and hit.occurrences >= 1:
        return True
    if hit.strong_signals >= 2 and hit.occurrences >= 2:
        return True
    return False


def categories_for_hit(hit: PersonHit) -> list[str]:
    if hit.name in CURATED_IDENTITIES:
        return CURATED_IDENTITIES[hit.name]
    if hit.name in FICTIONAL_CHARACTERS:
        return ["fictional"]
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
    if hit.name in FICTIONAL_CHARACTERS and "fictional" not in categories:
        categories.append("fictional")
    if not categories:
        categories.append("mentioned")
    return categories


def primary_category(hit: PersonHit) -> str:
    if hit.name in CURATED_IDENTITIES:
        return CURATED_IDENTITIES[hit.name][0]
    if hit.name in FICTIONAL_CHARACTERS:
        return "fictional"
    if hit.name in SPIRITUAL_ONLY:
        return "spiritual"
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


def aliases_for_person(name: str) -> list[str]:
    return sorted(
        {
            alias
            for alias, target in ALIASES.items()
            if target == name and alias != name and alias not in STOP_NAMES
        }
    )


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
            "aliases": aliases_for_person(hit.name),
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
        "fictional": category_counts.get("fictional", 0),
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
    parser.add_argument("--book-path", action="append", help="one book directory under the source corpus; repeat for multiple books")
    parser.add_argument("--all", action="store_true", help="scan the whole corpus explicitly")
    parser.add_argument("--data-dir", default="data", help="output data directory")
    parser.add_argument("--export-dir", default="exports", help="plain-text export directory")
    args = parser.parse_args()

    source_root = Path(args.source).resolve()
    if not source_root.exists():
        raise SystemExit(f"Source directory not found: {source_root}")

    if args.book_path:
        targets = []
        for book_path in args.book_path:
            target = Path(book_path)
            if not target.is_absolute():
                target = Path.cwd() / target
            if not target.exists():
                raise SystemExit(f"Book directory not found: {target}")
            targets.append(target)
        files = sorted(
            (path for target in targets for path in target.rglob("*.txt")),
            key=lambda p: str(p),
        )
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
