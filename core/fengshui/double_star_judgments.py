"""
core/fengshui/double_star_judgments.py
=======================================
玄空飞星 81 种山向双星组合断语
(81 Combinations of Mountain Star + Facing Star Judgments)

源自《玄空秘旨》《玄机赋》《飞星赋》《紫白诀》以及章仲山《宅断》、
沈竹礽《沈氏玄空学》、谈养吾《大玄空路透》之精华。

每个山向组合（如山1向2、山2向1、山6向8 等）都有特定吉凶象义。
这是玄空派"具体断事"的根本依据。

格式：(山星, 向星) → {
    nature: 吉凶等级,
    short: 简短断语,
    detailed: 详细论断,
    health: 健康暗示,
    wealth: 财运暗示,
    relationships: 人际暗示,
    source: 出处,
}
"""
from typing import Dict, Tuple, Any

# 九星基本五行属性
STAR_ELEMENT = {1:"水", 2:"土", 3:"木", 4:"木", 5:"土", 6:"金", 7:"金", 8:"土", 9:"火"}
STAR_NATURE = {1:"吉", 2:"大凶", 3:"凶", 4:"吉", 5:"大凶", 6:"吉", 7:"凶", 8:"大吉", 9:"吉"}


DOUBLE_STAR_81: Dict[Tuple[int, int], Dict[str, Any]] = {
    # ═══ 山 1 系列 (一白贪狼水) ═══
    (1, 1): {
        "nature": "auspicious", "short": "桃花重叠，文秀清贵",
        "detailed": "山向双一比和，水气过盛。少年聪明俊秀但易陷桃花，亦主文学功名。当运吉，失运则主溺水、肾病、桃花泛滥。",
        "health": "肾、耳、泌尿系统；过湿易致水肿",
        "wealth": "文职生财，学术成名",
        "relationships": "桃花极旺，易有情劫",
        "source": "《飞星赋》「一白比和，少年风流」",
    },
    (1, 2): {
        "nature": "inauspicious", "short": "夫妻不和，阴阳交战",
        "detailed": "一白水为先天之气，二黑老阴主疾病。土克水，主妇女疾病、丈夫与岳母不和。当令二运反吉。",
        "health": "妇科、肾病、消化不良",
        "wealth": "因病破财", "relationships": "婆媳不和，男主受制于女",
        "source": "《紫白诀》「一二同宫，损主之兆」",
    },
    (1, 3): {
        "nature": "mixed", "short": "智斗官非，文人闘讼",
        "detailed": "水生木，本为相生。但三碧为蚩尤星主官非口舌，与一白合则为「文人鬪訟」，主才高被讒、争讼破财。",
        "health": "肝胆、神经", "wealth": "因诉讼破财",
        "relationships": "口舌是非缠身",
        "source": "《玄机赋》「文人鬪訟」",
    },
    (1, 4): {
        "nature": "auspicious_great", "short": "一四同宫，准发科名之显",
        "detailed": "经典吉星组合！一白文曲水 + 四绿文昌木，水生木为洩秀。主大利读书功名、文章显达。古来状元命多此局。",
        "health": "肝胆、神经佳",
        "wealth": "文职生财，著作生财",
        "relationships": "文人雅士相聚",
        "source": "《紫白诀》「一四同宫，准发科名之显」（玄空最贵格之一）",
    },
    (1, 5): {
        "nature": "inauspicious_great", "short": "中毒疮毒，子病堕胎",
        "detailed": "五黄土克一白水。一白主生育、肾脏。被五黄重克，主胎元不固、流产、肾病、性病、中毒。当令五运稍解。",
        "health": "肾衰、胎产之厄、毒疮", "wealth": "医药破财",
        "relationships": "夫妻一方损伤", "source": "《飞星赋》「一五同宫，肾衰耳鸣」",
    },
    (1, 6): {
        "nature": "auspicious", "short": "金水相涵，文章名世",
        "detailed": "六白金生一白水，文武双全之象。主文章名世、得贵人提拔、官位高升。配合得当为「金水文章」格。",
        "health": "肺金水充足",
        "wealth": "官途生财", "relationships": "贵人扶持",
        "source": "《玄机赋》「金水相涵，定有文章之贵」",
    },
    (1, 7): {
        "nature": "mixed", "short": "桃花劫财，酒色破家",
        "detailed": "七赤金生一白水，本是金水相生。但七赤为破军桃花，与一白桃花重叠，主酒色风流、女色破财。当运吉，失运凶。",
        "health": "肾、肺、生殖系统",
        "wealth": "酒色之财，亦因酒色破财",
        "relationships": "桃花泛滥，淫荡之事",
        "source": "《飞星赋》「一七同宫，肝肾相克」",
    },
    (1, 8): {
        "nature": "auspicious_great", "short": "财丁两旺，富贵绵长",
        "detailed": "八白当令财星 + 一白桃花辅星，土克水但土厚护水，主财源稳定、家口平安、富贵绵延。八运九运皆吉。",
        "health": "脾胃、肾健康",
        "wealth": "稳定致富，房地产兴", "relationships": "家庭和睦",
        "source": "《沈氏玄空学》",
    },
    (1, 9): {
        "nature": "auspicious", "short": "水火既济，旧染新生",
        "detailed": "一白水 + 九紫火，本为水火相战，但九运中九紫当令则化为「水火既济」，主旧业再兴、官非化解、桃花喜事。",
        "health": "心肾相交（佳）",
        "wealth": "喜庆生财", "relationships": "婚姻喜事",
        "source": "《飞星赋》「水火既济」",
    },
    
    # ═══ 山 2 系列 (二黑巨门土，病符) ═══
    (2, 1): {
        "nature": "inauspicious", "short": "土克水，妇产之厄",
        "detailed": "与(1,2)同象但反位。二黑临山，妇人多病；一白临向，水气受土克。主家中妇人多病，丈夫受妻拖累。",
        "health": "妇科病重", "wealth": "因病破财",
        "relationships": "夫妻反目", "source": "《紫白诀》",
    },
    (2, 2): {
        "nature": "inauspicious_great", "short": "病符重叠，丧亡哀号",
        "detailed": "二黑双叠最凶！主疾病连年、孕妇难产、寡居哀痛。当运二运稍吉，失运则丧亡频频。",
        "health": "重病、绝症、孕产难",
        "wealth": "医药破财", "relationships": "寡居孤苦",
        "source": "《飞星赋》「二黑临门，无医无药」",
    },
    (2, 3): {
        "nature": "inauspicious", "short": "斗牛煞，官司口角",
        "detailed": "二黑土 + 三碧木，木克土，又名「鬪牛煞」。主家人不和、官司口角不断、官非缠身。失运极凶。",
        "health": "脾胃、肝胆同时受损",
        "wealth": "官非破财", "relationships": "兄弟妯娌不和",
        "source": "《玄机赋》「鬪牛煞起，家室分崩」",
    },
    (2, 4): {
        "nature": "inauspicious", "short": "婆媳不和，姑嫂相争",
        "detailed": "二黑老阴 + 四绿长女木，木克土。主家中女性内斗，婆媳不和、姑嫂相争。当令稍解。",
        "health": "脾胃、肝胆",
        "wealth": "家事消耗", "relationships": "女性家口不和",
        "source": "《紫白诀》「四二同宫，婆媳不和」",
    },
    (2, 5): {
        "nature": "inauspicious_great", "short": "五黄二黑齐临，损主重病",
        "detailed": "两大凶星汇聚，主家中长辈重病或死亡、家运衰败。运势再加流年五黄到此，必出大事。",
        "health": "急重病、死亡",
        "wealth": "家败财散", "relationships": "丧主之痛",
        "source": "《沈氏玄空学》「二五交加，罹死亡并生疾病」",
    },
    (2, 6): {
        "nature": "mixed", "short": "土金相生，但有寡阴之兆",
        "detailed": "二黑土生六白金，相生为吉。但二黑乃老阴病符，配六白老阳乾金，主男主早逝、寡妇当家。",
        "health": "肺金佳但有寡居之兆",
        "wealth": "稳定但孤", "relationships": "夫妻一方早逝",
        "source": "《飞星赋》",
    },
    (2, 7): {
        "nature": "inauspicious", "short": "火灾盗贼，刀伤血光",
        "detailed": "二黑配七赤，凶煞之最。主火灾、盗贼、刀伤血光。失运则灾祸连年。",
        "health": "刀伤、手术、火灼",
        "wealth": "失盗破财", "relationships": "刑伤口舌",
        "source": "《玄机赋》「七二会，回禄之灾」",
    },
    (2, 8): {
        "nature": "mixed", "short": "土土比和，财稳病多",
        "detailed": "二土比和，八白当令为吉。但二黑病气与八白财气并存，主财来病也来。八运可解，九运稍弱。",
        "health": "胃肠、慢性病",
        "wealth": "稳定致富但病痛多",
        "relationships": "家口平安",
        "source": "《沈氏玄空学》",
    },
    (2, 9): {
        "nature": "inauspicious", "short": "火炎土燥，目疾产厄",
        "detailed": "九紫火生二黑土，火生土反助病气。主妇人产厄、目疾、心病、火气旺过头反成灾。",
        "health": "心血管、眼疾、产厄",
        "wealth": "因病破财", "relationships": "夫妻不睦",
        "source": "《飞星赋》「火土相生，目盲产难」",
    },
    
    # ═══ 山 3 系列 (三碧禄存木，蚩尤星) ═══
    (3, 1): {
        "nature": "mixed", "short": "智斗官讼",
        "detailed": "三碧木 + 一白水，水生木。主文人鬪訟、才高被讒、官非缠身。",
        "health": "肝胆、神经",
        "wealth": "诉讼", "relationships": "口舌争讼",
        "source": "《玄机赋》",
    },
    (3, 2): {
        "nature": "inauspicious_great", "short": "鬪牛煞，家败如山倒",
        "detailed": "三碧木 + 二黑土，木克土，斗牛煞最凶。失运主家败、官非、绝嗣。",
        "health": "脾胃肝胆同损",
        "wealth": "破家", "relationships": "妯娌斗争",
        "source": "《玄机赋》「鬪牛煞起」",
    },
    (3, 3): {
        "nature": "inauspicious", "short": "蚩尤重叠，刑伤官非",
        "detailed": "三碧双叠，蚩尤星气盛。主官司刑罚、争讼连年、家中长子受刑伤。",
        "health": "肝胆、肢体伤",
        "wealth": "官讼破财", "relationships": "兄弟反目",
        "source": "《飞星赋》",
    },
    (3, 4): {
        "nature": "mixed", "short": "贼盗淫乱，桃花破家",
        "detailed": "三四同宫，木气过盛。一说主文学（四绿文昌）+ 是非（三碧），一说主桃花淫乱。当令吉，失运凶。",
        "health": "肝胆、神经",
        "wealth": "文职生财或破财", "relationships": "桃花泛滥",
        "source": "《玄机赋》「三四同宫，淫风滚滚」",
    },
    (3, 5): {
        "nature": "inauspicious_great", "short": "穷困潦倒，足疾肢残",
        "detailed": "五黄土克三碧木，又主肢体受伤。失运主家中长子残疾、足疾、家境穷困。",
        "health": "肢体伤残、足疾",
        "wealth": "穷困", "relationships": "长子不利",
        "source": "《飞星赋》「三五交加，损长子」",
    },
    (3, 6): {
        "nature": "inauspicious", "short": "金克木，刀伤足疾",
        "detailed": "六白金克三碧木，刀剑伐木。主肢体受伤、骨折、手术、长子早夭。",
        "health": "骨伤、手术、足疾",
        "wealth": "医疗破财", "relationships": "兄弟相残",
        "source": "《飞星赋》「六三同宫，足疾刀伤」",
    },
    (3, 7): {
        "nature": "inauspicious", "short": "刀剑相侵，盗贼血光",
        "detailed": "七赤金克三碧木，又见七赤破军刀剑之星。主刀伤、盗贼劫财、血光之灾。失运极凶。",
        "health": "刀剑伤、血光",
        "wealth": "盗劫破财", "relationships": "口舌刑伤",
        "source": "《玄机赋》「七三同来，被劫盗更见官灾」",
    },
    (3, 8): {
        "nature": "mixed", "short": "木克土，损小口",
        "detailed": "三碧木克八白土，但八白当令则受损轻。主家中幼子幼女不利、小儿伤灾。九运稍可。",
        "health": "小儿伤灾",
        "wealth": "财气受损", "relationships": "小孩不利",
        "source": "《沈氏玄空学》",
    },
    (3, 9): {
        "nature": "mixed", "short": "木生火，聪明而有官非",
        "detailed": "三碧木生九紫火，本为相生洩秀。但九紫为火，三碧为是非，主聪明伶俐但易招官非火灾。",
        "health": "心血管、眼疾", "wealth": "升迁",
        "relationships": "聪明子女", "source": "《玄机赋》",
    },
    
    # ═══ 山 4 系列 (四绿文昌木) ═══
    (4, 1): {
        "nature": "auspicious_great", "short": "一四同宫，科甲连登",
        "detailed": "经典吉局，与(1,4)对应。文昌+文曲，主大利学业、文章、功名。状元宰相之命。",
        "health": "肝胆、脑力佳", "wealth": "文职高升",
        "relationships": "文人雅士", "source": "《紫白诀》",
    },
    (4, 2): {
        "nature": "inauspicious", "short": "四二同宫，姑嫂相争",
        "detailed": "与(2,4)对应。家中女性内斗、婆媳不和。",
        "health": "脾胃、肝胆", "wealth": "家事消耗",
        "relationships": "女性不和", "source": "《紫白诀》",
    },
    (4, 3): {
        "nature": "mixed", "short": "三四同宫，淫风滚滚",
        "detailed": "与(3,4)对应。当令文学之贵，失运桃花淫乱。",
        "health": "肝胆", "wealth": "文职或破财",
        "relationships": "桃花泛滥", "source": "《玄机赋》",
    },
    (4, 4): {
        "nature": "auspicious", "short": "文昌重叠，状元之命",
        "detailed": "四绿双叠，文气极盛。主大利读书、学术、考试，必出文人雅士。当令最贵。",
        "health": "肝胆健康", "wealth": "文职得意",
        "relationships": "高雅", "source": "《飞星赋》",
    },
    (4, 5): {
        "nature": "inauspicious", "short": "黄毒侵肝，乳病疮毒",
        "detailed": "五黄土克四绿木，主妇女乳房疾病、肝病、皮肤病。失运凶险。",
        "health": "乳腺、肝病、皮肤毒",
        "wealth": "医药破财", "relationships": "妇女受伤",
        "source": "《飞星赋》「四五同宫，淫荡风疾」",
    },
    (4, 6): {
        "nature": "inauspicious", "short": "金克木，妇女自缢",
        "detailed": "六白金克四绿木，长女受伤之象。主妇女抑郁、自缢、淫奔，又主肝胆开刀。",
        "health": "肝胆手术、抑郁",
        "wealth": "破财", "relationships": "妇女抑郁",
        "source": "《玄机赋》「六四同宫，金木相战，主自缢淫奔」",
    },
    (4, 7): {
        "nature": "inauspicious", "short": "金木交战，淫荡疯狂",
        "detailed": "七赤金克四绿木，又重叠桃花。主淫荡风流、神经失常、刀伤血光。失运极凶。",
        "health": "神经病、刀伤",
        "wealth": "色破", "relationships": "淫乱风流",
        "source": "《飞星赋》「七四同宫，颠狂淫风」",
    },
    (4, 8): {
        "nature": "mixed", "short": "木克土，小儿伤灾",
        "detailed": "四绿木克八白土，但八白当令尚可。主小儿读书但易伤灾。九运稍可。",
        "health": "小儿不安", "wealth": "稳定",
        "relationships": "小儿教育", "source": "《沈氏玄空学》",
    },
    (4, 9): {
        "nature": "auspicious", "short": "木火通明，文章显贵",
        "detailed": "四绿木生九紫火，洩秀生喜。主文章成名、艺术显达、喜庆连连。九运大吉。",
        "health": "心、眼", "wealth": "艺文显贵",
        "relationships": "喜庆", "source": "《紫白诀》",
    },
    
    # ═══ 山 5 系列 (五黄廉贞土，最凶) ═══
    (5, 1): { "nature":"inauspicious_great", "short":"五黄克水，胎产之灾",
        "detailed":"与(1,5)对应。主流产、肾病、性病、中毒。",
        "health":"胎产、肾衰", "wealth":"医药破财", "relationships":"夫妻一方损伤",
        "source":"《飞星赋》" },
    (5, 2): { "nature":"inauspicious_great", "short":"二五交加，损主重病",
        "detailed":"两凶汇聚，家中长辈重病死亡。", "health":"重病死亡",
        "wealth":"家败", "relationships":"丧痛", "source":"《沈氏玄空学》" },
    (5, 3): { "nature":"inauspicious_great", "short":"三五交加，损长子",
        "detailed":"家中长子残疾、足疾、穷困。", "health":"足疾肢残",
        "wealth":"穷困", "relationships":"长子不利", "source":"《飞星赋》" },
    (5, 4): { "nature":"inauspicious", "short":"四五同宫，乳病疯疾",
        "detailed":"妇女乳房病、抑郁、淫荡。", "health":"乳腺、抑郁",
        "wealth":"破财", "relationships":"妇女不利", "source":"《飞星赋》" },
    (5, 5): { "nature":"inauspicious_great", "short":"五黄重叠，灾劫连连",
        "detailed":"五黄双叠为最凶之象！主家败人亡、火灾水灾、绝症、绝嗣。绝对不可动土。",
        "health":"绝症、死亡", "wealth":"家破", "relationships":"绝嗣",
        "source":"《飞星赋》「五黄正煞，不拘临方到向，岁君大煞，加临亦凶」" },
    (5, 6): { "nature":"inauspicious", "short":"金泄五黄，反致头疾",
        "detailed":"六白金泄五黄土，本可解煞。但金被恶土所制，主头部疾病、肺病。",
        "health":"头痛、肺病", "wealth":"耗损",
        "relationships":"父亲不利", "source":"《飞星赋》" },
    (5, 7): { "nature":"inauspicious", "short":"五七同宫，毒疮恶疾",
        "detailed":"七赤金泄五黄，主皮肤毒疮、肺病、性病。失运凶。",
        "health":"毒疮、肺病", "wealth":"医药破", "relationships":"刑伤",
        "source":"《玄机赋》" },
    (5, 8): { "nature":"mixed", "short":"五八同宫，喜中藏凶",
        "detailed":"八白财星与五黄并立，主财来病也来。八运可解一半。",
        "health":"暗疾", "wealth":"得财但病", "relationships":"喜中带忧",
        "source":"《沈氏玄空学》" },
    (5, 9): { "nature":"inauspicious", "short":"火生土，五黄更旺",
        "detailed":"九紫火生五黄土，反助凶煞。主火灾、目疾、心病连发。",
        "health":"心、眼、火灼", "wealth":"火灾破财",
        "relationships":"急性事故", "source":"《飞星赋》" },
    
    # ═══ 山 6 系列 (六白武曲金) ═══
    (6, 1): { "nature":"auspicious", "short":"金水相涵，文章名世",
        "detailed":"与(1,6)对应。文章贵气、官途顺遂。", "health":"肺金水",
        "wealth":"官升财来", "relationships":"贵人扶持", "source":"《玄机赋》" },
    (6, 2): { "nature":"mixed", "short":"土生金，但寡阴之象",
        "detailed":"与(2,6)对应。寡妇当家、男主早逝。", "health":"肺金佳",
        "wealth":"稳定但孤", "relationships":"夫妻一方早逝", "source":"《飞星赋》" },
    (6, 3): { "nature":"inauspicious", "short":"金克木，刀伤足疾",
        "detailed":"与(3,6)对应。骨折、手术、长子不利。",
        "health":"骨伤", "wealth":"医疗破", "relationships":"兄弟相残",
        "source":"《飞星赋》" },
    (6, 4): { "nature":"inauspicious", "short":"金木交战，妇女自缢",
        "detailed":"与(4,6)对应。妇女抑郁、肝胆开刀。",
        "health":"肝胆手术", "wealth":"破",
        "relationships":"妇女抑郁", "source":"《玄机赋》" },
    (6, 5): { "nature":"inauspicious", "short":"金泄五黄，头疾肺病",
        "detailed":"与(5,6)对应。", "health":"头痛肺病",
        "wealth":"耗损", "relationships":"父亲不利", "source":"《飞星赋》" },
    (6, 6): { "nature":"auspicious", "short":"乾金重叠，武贵之命",
        "detailed":"六白双叠，乾金气盛。主武职高升、权柄在握、得贵人。当令大吉。",
        "health":"肺金强", "wealth":"武职生财",
        "relationships":"贵人多", "source":"《飞星赋》" },
    (6, 7): { "nature":"mixed", "short":"两金相争，是非口舌",
        "detailed":"六白乾金 + 七赤兑金，金气过重。主官非口舌、刀剑伤、家庭不和。",
        "health":"肺金过盛", "wealth":"官非", "relationships":"口角不断",
        "source":"《飞星赋》「交剑煞」" },
    (6, 8): { "nature":"auspicious_great", "short":"六八武曲临门，财官双美",
        "detailed":"经典吉局！六白金生八白土（应为土生金，但古书称六八为「武曲临门」吉局）。主财富权势双全。",
        "health":"稳健", "wealth":"大富大贵",
        "relationships":"贵人多", "source":"《飞星赋》「六八武曲」" },
    (6, 9): { "nature":"mixed", "short":"火克金，头部之疾",
        "detailed":"九紫火克六白金，主头部疾病、肺病、急性炎症。但九运得令时火气调和。",
        "health":"头痛、急症", "wealth":"耗费",
        "relationships":"父亲健康", "source":"《飞星赋》「九六同宫，火烧天门」" },
    
    # ═══ 山 7 系列 (七赤破军金) ═══
    (7, 1): { "nature":"mixed", "short":"桃花劫财，酒色破家",
        "detailed":"与(1,7)对应。酒色风流、女色破财。", "health":"肾肺",
        "wealth":"色破", "relationships":"桃花泛滥", "source":"《飞星赋》" },
    (7, 2): { "nature":"inauspicious", "short":"火灾盗贼，刀伤血光",
        "detailed":"与(2,7)对应。失运灾祸连年。",
        "health":"刀伤", "wealth":"失盗", "relationships":"刑伤",
        "source":"《玄机赋》" },
    (7, 3): { "nature":"inauspicious", "short":"穿心煞，盗贼血光",
        "detailed":"与(3,7)对应。「穿心煞」最凶之一。",
        "health":"刀剑血光", "wealth":"盗劫", "relationships":"刑伤",
        "source":"《玄机赋》「穿心煞」" },
    (7, 4): { "nature":"inauspicious", "short":"金木交战，颠狂淫风",
        "detailed":"与(4,7)对应。神经病、刀伤血光。",
        "health":"神经病", "wealth":"色破", "relationships":"淫乱",
        "source":"《飞星赋》" },
    (7, 5): { "nature":"inauspicious", "short":"毒疮恶疾",
        "detailed":"与(5,7)对应。皮肤毒疮、肺病、性病。",
        "health":"毒疮", "wealth":"医药破", "relationships":"刑伤",
        "source":"《玄机赋》" },
    (7, 6): { "nature":"mixed", "short":"交剑煞，口舌官非",
        "detailed":"与(6,7)对应。两金相争、官非口舌。",
        "health":"肺金过盛", "wealth":"官非", "relationships":"口角",
        "source":"《飞星赋》「交剑煞」" },
    (7, 7): { "nature":"inauspicious", "short":"破军重叠，盗贼血光",
        "detailed":"七赤双叠，破军气盛。主盗贼、血光、刀伤、官非。当七运时反吉，失运极凶。",
        "health":"刀伤血光", "wealth":"盗劫破财",
        "relationships":"口舌争讼", "source":"《飞星赋》" },
    (7, 8): { "nature":"mixed", "short":"七八之间，仍多是非",
        "detailed":"七赤金生八白土，本相生。但七赤为破军、八白当令。主财气尚可但口舌争讼难免。",
        "health":"暗疾", "wealth":"稳定", "relationships":"口舌",
        "source":"《沈氏玄空学》" },
    (7, 9): { "nature":"inauspicious", "short":"火烧金，回禄之灾",
        "detailed":"九紫火克七赤金，又见七赤刀剑。主火灾、烫伤、急症心病。失运极凶。",
        "health":"火灾、心病", "wealth":"火烧财",
        "relationships":"急性事故", "source":"《玄机赋》「七九同宫，回禄之灾」" },
    
    # ═══ 山 8 系列 (八白左辅土，财星) ═══
    (8, 1): { "nature":"auspicious_great", "short":"财丁两旺，富贵绵长",
        "detailed":"与(1,8)对应。八白财星 + 一白桃花。八运九运皆吉。",
        "health":"健康", "wealth":"稳定致富",
        "relationships":"和睦", "source":"《沈氏玄空学》" },
    (8, 2): { "nature":"mixed", "short":"土土比和，财稳病多",
        "detailed":"与(2,8)对应。", "health":"慢性病",
        "wealth":"稳定", "relationships":"平安", "source":"《沈氏玄空学》" },
    (8, 3): { "nature":"mixed", "short":"木克土，损小口",
        "detailed":"与(3,8)对应。小儿伤灾。", "health":"小儿不安",
        "wealth":"耗损", "relationships":"小孩不利", "source":"《沈氏玄空学》" },
    (8, 4): { "nature":"mixed", "short":"木克土，小儿读书有伤",
        "detailed":"与(4,8)对应。", "health":"小儿",
        "wealth":"稳定", "relationships":"教育", "source":"《沈氏玄空学》" },
    (8, 5): { "nature":"mixed", "short":"喜中藏凶",
        "detailed":"与(5,8)对应。财来病也来。",
        "health":"暗疾", "wealth":"得财但病", "relationships":"喜中带忧",
        "source":"《沈氏玄空学》" },
    (8, 6): { "nature":"auspicious_great", "short":"六八武曲，财官双美",
        "detailed":"与(6,8)对应。大富大贵。", "health":"稳健",
        "wealth":"大富", "relationships":"贵人", "source":"《飞星赋》" },
    (8, 7): { "nature":"mixed", "short":"七八之间，仍多是非",
        "detailed":"与(7,8)对应。", "health":"暗疾",
        "wealth":"稳定", "relationships":"口舌", "source":"《沈氏玄空学》" },
    (8, 8): { "nature":"auspicious_great", "short":"八白重叠，财气最盛",
        "detailed":"八白双叠，财气极旺！主大富大贵、房地产丰、家口平安。八运最盛，九运辅佐。",
        "health":"脾胃健", "wealth":"豪富",
        "relationships":"家口众多", "source":"《沈氏玄空学》" },
    (8, 9): { "nature":"auspicious_great", "short":"火土相生，富贵生喜",
        "detailed":"九紫火生八白土，相生大吉。九运为当令火星 + 财星，主富贵喜庆双至。最佳组合之一。",
        "health":"健旺", "wealth":"喜中得财",
        "relationships":"喜事连连", "source":"《沈氏玄空学》" },
    
    # ═══ 山 9 系列 (九紫右弼火，当令) ═══
    (9, 1): { "nature":"auspicious", "short":"水火既济",
        "detailed":"与(1,9)对应。九运中大吉。",
        "health":"心肾交", "wealth":"喜庆生财",
        "relationships":"婚姻喜事", "source":"《飞星赋》" },
    (9, 2): { "nature":"inauspicious", "short":"火炎土燥，目疾产厄",
        "detailed":"与(2,9)对应。", "health":"心眼产",
        "wealth":"病破财", "relationships":"夫妻不睦", "source":"《飞星赋》" },
    (9, 3): { "nature":"mixed", "short":"木火通明，聪明而有官非",
        "detailed":"与(3,9)对应。聪明但易招官非。",
        "health":"心血管", "wealth":"升迁",
        "relationships":"聪明子女", "source":"《玄机赋》" },
    (9, 4): { "nature":"auspicious", "short":"木火通明，文章显贵",
        "detailed":"与(4,9)对应。九运大吉。",
        "health":"心眼", "wealth":"艺文显贵",
        "relationships":"喜庆", "source":"《紫白诀》" },
    (9, 5): { "nature":"inauspicious", "short":"火生五黄，灾劫加重",
        "detailed":"与(5,9)对应。火灾、目疾、急症。",
        "health":"心眼火灼", "wealth":"火破",
        "relationships":"事故", "source":"《飞星赋》" },
    (9, 6): { "nature":"mixed", "short":"火烧天门，头部之疾",
        "detailed":"与(6,9)对应。头痛肺病。",
        "health":"头痛急症", "wealth":"耗费",
        "relationships":"父健康", "source":"《飞星赋》" },
    (9, 7): { "nature":"inauspicious", "short":"火烧金，回禄之灾",
        "detailed":"与(7,9)对应。火灾烫伤心病。",
        "health":"火灾心病", "wealth":"火烧",
        "relationships":"急性", "source":"《玄机赋》" },
    (9, 8): { "nature":"auspicious_great", "short":"火土相生，富贵生喜",
        "detailed":"与(8,9)对应。九运绝佳。",
        "health":"健旺", "wealth":"喜中得财",
        "relationships":"喜事", "source":"《沈氏玄空学》" },
    (9, 9): { "nature":"auspicious", "short":"九紫重叠，喜庆连连",
        "detailed":"九紫双叠，火气极旺。当九运为当令大吉，主喜庆、婚嫁、升迁、贵气。失运则火灾心病。",
        "health":"心、眼", "wealth":"喜庆生财",
        "relationships":"婚嫁升迁", "source":"《飞星赋》" },
}


def get_double_star_judgment(mountain_star: int, facing_star: int, current_yun: int = 9) -> Dict[str, Any]:
    """
    返回一个山向双星组合的具体吉凶断语。
    
    Args:
        mountain_star: 山星 (1-9)
        facing_star: 向星 (1-9)
        current_yun: 当令运数（影响吉凶的当令性）
    
    Returns:
        dict 含 nature, short, detailed, health, wealth, relationships, source
    """
    key = (mountain_star, facing_star)
    base = DOUBLE_STAR_81.get(key)
    if not base:
        return {
            "nature": "neutral", "short": f"{mountain_star}{facing_star}组合",
            "detailed": "此组合无特殊吉凶记载，依五行生克判断。",
            "health": "", "wealth": "", "relationships": "", "source": "",
        }
    
    # 当令调整：失运时凶象加重，得令时吉象加强
    out = base.copy()
    is_wang = (mountain_star == current_yun or facing_star == current_yun)
    is_sui = (mountain_star == (current_yun + 1 if current_yun < 9 else 1) or 
              facing_star == (current_yun + 1 if current_yun < 9 else 1))  # 生气方
    
    if is_wang and out["nature"].startswith("inauspicious"):
        out["adjusted"] = "得令稍解凶"
    elif (not is_wang) and out["nature"].startswith("auspicious"):
        out["adjusted"] = "失运吉象减半"
    
    return out


def get_wuxing_interaction(star_a: int, star_b: int) -> Dict[str, str]:
    """
    返回两星的五行生克关系。
    
    Returns:
        {relation: 生/克/比和, direction: a生b/b生a/a克b/b克a/比和, desc: 描述}
    """
    e_a = STAR_ELEMENT[star_a]
    e_b = STAR_ELEMENT[star_b]
    
    SHENG = {"木":"火", "火":"土", "土":"金", "金":"水", "水":"木"}  # 生
    KE    = {"木":"土", "火":"金", "土":"水", "金":"木", "水":"火"}  # 克
    
    if e_a == e_b:
        return {"relation":"比和", "direction":"比和", "desc": f"{e_a}{e_b}同气，力量倍增（吉凶皆放大）"}
    if SHENG[e_a] == e_b:
        return {"relation":"生", "direction":f"{star_a}({e_a})生{star_b}({e_b})", "desc":f"{star_a}泄气于{star_b}，{star_b}得力"}
    if SHENG[e_b] == e_a:
        return {"relation":"生", "direction":f"{star_b}({e_b})生{star_a}({e_a})", "desc":f"{star_b}泄气于{star_a}，{star_a}得力"}
    if KE[e_a] == e_b:
        return {"relation":"克", "direction":f"{star_a}({e_a})克{star_b}({e_b})", "desc":f"{star_a}伤{star_b}，{star_b}受损"}
    if KE[e_b] == e_a:
        return {"relation":"克", "direction":f"{star_b}({e_b})克{star_a}({e_a})", "desc":f"{star_b}伤{star_a}，{star_a}受损"}
    return {"relation":"无", "direction":"无", "desc":"五行无直接生克"}
