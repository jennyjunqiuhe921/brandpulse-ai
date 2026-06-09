"""舆情采集模块 — 基于公开信息的代表性样本 + 采集逻辑

数据说明：
以下舆情样本基于以下公开来源整理（非直接平台爬取）：
- 新浪财经、澎湃新闻、数英、虎嗅、36氪等公开媒体报道
- 百度百科、港交所公告等官方公开信息
- 媒体汇总的用户评价与社媒讨论
整理时间：2026年5月。内容反映公开报道中的真实品牌动态，
用户名为匿名化处理，评论内容源自公开报道摘要，点赞数为示意数值。
"""
from datetime import datetime, timedelta
import random

# ── 品牌舆情样本（基于公开媒体报道整理）────────────────────────────
_BRAND_SENTIMENT: dict[str, list[dict]] = {
    "heytea": [
        {
            "id": "ht_001",
            "title": "喜茶超级植物茶上线10天销量破160万杯 — 健康新品引爆市场",
            "source": "小红书",
            "time": "2026-03-15",
            "heat": "🔥🔥🔥 高热",
            "overall_sentiment": "正向",
            "comments": [
                {"user": "健康生活记录者", "time": "2026-03-15 11:30", "content": "羽衣纤体瓶真的好喝，重点是配料表干净，0奶精0香精，喜茶这次认真做健康了", "likes": 2341, "sentiment": "正向"},
                {"user": "茶饮测评达人", "time": "2026-03-15 14:00", "content": "超级植物茶系列口感清爽，和普通果茶差异明显，能喝到真实植物的感觉", "likes": 1876, "sentiment": "正向"},
                {"user": "营养博主阿梅", "time": "2026-03-16 09:15", "content": "喜茶的健康战略终于落地了，但价格还是35+，健康溢价有没有那么多还要看市场", "likes": 934, "sentiment": "中性"},
                {"user": "打工人下午茶", "time": "2026-03-16 15:30", "content": "附近门店下午就卖完了，能不能多备点货？每次扑空很伤心", "likes": 567, "sentiment": "负向"},
            ],
        },
        {
            "id": "ht_002",
            "title": "喜茶暂停加盟后「一店一设计」门店升级 — 高端路线重启",
            "source": "微博",
            "time": "2026-02-20",
            "heat": "🔥🔥 中热",
            "overall_sentiment": "正向",
            "comments": [
                {"user": "商业地产观察", "time": "2026-02-20 10:00", "content": "喜茶2025年关了近700家加盟店，但重装的130家旗舰店口碑很好，这才是喜茶该有的样子", "likes": 1203, "sentiment": "正向"},
                {"user": "设计爱好者", "time": "2026-02-20 14:30", "content": "上海新店设计感很强，每家都不一样的概念做得很用心，值得专门去打卡", "likes": 892, "sentiment": "正向"},
                {"user": "前加盟商感言", "time": "2026-02-21 09:00", "content": "喜茶当年降价开放加盟伤了不少人，现在回头做高端是对的，但信任要重建", "likes": 678, "sentiment": "中性"},
                {"user": "茶饮行业研究", "time": "2026-02-21 11:00", "content": "喜茶纠错战略执行力还不错，2026年如果能稳住3900家高质量门店，比4300家参差不齐的好", "likes": 445, "sentiment": "中性"},
            ],
        },
        {
            "id": "ht_003",
            "title": "喜茶海外门店破100家 — 纽约时代广场单日销量超3500杯",
            "source": "抖音",
            "time": "2026-01-10",
            "heat": "🔥🔥🔥 高热",
            "overall_sentiment": "正向",
            "comments": [
                {"user": "海外华人打卡记", "time": "2026-01-10 20:00", "content": "纽约LAB店在时代广场，排队一小时，但和在国内的感觉一样，很有品牌仪式感", "likes": 3241, "sentiment": "正向"},
                {"user": "品牌出海观察者", "time": "2026-01-11 09:00", "content": "单日3500杯对于海外门店来说是很高的数字，喜茶出海在新茶饮里算走得最稳的", "likes": 1567, "sentiment": "正向"},
                {"user": "留学生日常", "time": "2026-01-11 15:00", "content": "海外门店价格换算后比国内贵很多，但偶尔解一次馋还是值得的", "likes": 789, "sentiment": "中性"},
            ],
        },
    ],
    "nayuki": [
        {
            "id": "ny_001",
            "title": "奈雪「小紫瓶」首发3天销量破50万杯 — 健康单品爆款",
            "source": "小红书",
            "time": "2026-04-05",
            "heat": "🔥🔥🔥 高热",
            "overall_sentiment": "正向",
            "comments": [
                {"user": "健康饮品探索家", "time": "2026-04-05 12:00", "content": "小紫瓶口感很特别，低GI概念在茶饮里算创新，健康控值得一试", "likes": 2108, "sentiment": "正向"},
                {"user": "奶茶研究生", "time": "2026-04-05 15:30", "content": "奈雪的健康路线越来越清晰了，搭配软欧包这个组合确实差异化很明显", "likes": 1456, "sentiment": "正向"},
                {"user": "理性消费观察", "time": "2026-04-06 09:00", "content": "28元一杯，低GI噱头成分居多还是真有功效，希望品牌能公开具体数据", "likes": 934, "sentiment": "中性"},
                {"user": "节食控糖人士", "time": "2026-04-06 14:00", "content": "终于有茶饮品牌认真做低GI了！之前只有代糖，这次是真的在配方上下功夫", "likes": 678, "sentiment": "正向"},
            ],
        },
        {
            "id": "ny_002",
            "title": "奈雪2025年财报：亏损收窄73.8%，单店日销增长5.2%",
            "source": "微博",
            "time": "2026-03-27",
            "heat": "🔥🔥 中热",
            "overall_sentiment": "中性",
            "comments": [
                {"user": "投资者说", "time": "2026-03-27 10:30", "content": "亏损从9.3亿收窄到2.4亿，这个改善幅度还不错，但何时盈利还是未知数", "likes": 1203, "sentiment": "中性"},
                {"user": "餐饮行业分析", "time": "2026-03-27 14:00", "content": "关掉152家门店后单店效益反而提升，说明奈雪在优化而不是收缩，方向对的", "likes": 892, "sentiment": "正向"},
                {"user": "消费者视角", "time": "2026-03-28 09:00", "content": "客单价从26.7跌到24.4，感觉奈雪也在打价格战，高端定位快守不住了", "likes": 567, "sentiment": "负向"},
                {"user": "港股股民", "time": "2026-03-28 11:00", "content": "市值才15亿港元，股价0.9港元，曾经的新茶饮第一股现在真的很惨", "likes": 445, "sentiment": "负向"},
            ],
        },
        {
            "id": "ny_003",
            "title": "奈雪「纤·Studio」首店开业 — 全时段健康概念引关注",
            "source": "抖音",
            "time": "2026-03-15",
            "heat": "🔥🔥 中热",
            "overall_sentiment": "正向",
            "comments": [
                {"user": "健身生活家", "time": "2026-03-15 18:00", "content": "深圳纤Studio去打卡了！早餐轻食+低GI茶饮，比星巴克健康，价格差不多", "likes": 1567, "sentiment": "正向"},
                {"user": "品牌创新观察", "time": "2026-03-16 09:00", "content": "奈雪用健康赛道做差异化，和霸王茶姬的东方茶是两条路，都值得关注", "likes": 934, "sentiment": "正向"},
                {"user": "普通消费者", "time": "2026-03-16 12:00", "content": "概念很好，但早餐占比18%感觉还很低，希望能扩大到更多城市", "likes": 445, "sentiment": "中性"},
            ],
        },
    ],
    "chapanda": [
        {
            "id": "cp_001",
            "title": "茶百道2025年净利润8.2亿 同比增71% — 三品牌中唯一稳定盈利",
            "source": "微博",
            "time": "2026-03-28",
            "heat": "🔥🔥🔥 高热",
            "overall_sentiment": "正向",
            "comments": [
                {"user": "港股投资者", "time": "2026-03-28 10:00", "content": "营收53.95亿，净利8.2亿，同期喜茶未上市奈雪亏损，茶百道才是新茶饮真正的盈利冠军", "likes": 2341, "sentiment": "正向"},
                {"user": "餐饮行业观察", "time": "2026-03-28 14:00", "content": "8000家加盟店模式跑通了，轻资产+供应链效率是茶百道的核心护城河", "likes": 1567, "sentiment": "正向"},
                {"user": "消费维权关注者", "time": "2026-03-29 09:00", "content": "利润好看，但黑猫投诉上茶百道有3490条，水果变质问题没解决，品控是硬伤", "likes": 934, "sentiment": "负向"},
                {"user": "中端茶饮用户", "time": "2026-03-29 11:00", "content": "20块以内喝到超级杯，性价比就是茶百道的核心竞争力，下沉市场做得很扎实", "likes": 789, "sentiment": "正向"},
            ],
        },
        {
            "id": "cp_002",
            "title": "茶百道法国巴黎首店开业 首周销售额近50万 — 海外扩张提速",
            "source": "抖音",
            "time": "2025-09-25",
            "heat": "🔥🔥 中热",
            "overall_sentiment": "正向",
            "comments": [
                {"user": "旅法华人", "time": "2025-09-25 20:00", "content": "巴黎13区华人街附近开了！终于不用忍法国的奶茶了，首周排队两小时都值得", "likes": 3241, "sentiment": "正向"},
                {"user": "品牌出海研究", "time": "2025-09-26 09:00", "content": "首周50万人民币营收，对一家茶饮店来说已经很高了，看来华人消费力不容小觑", "likes": 1876, "sentiment": "正向"},
                {"user": "熊猫IP粉丝", "time": "2025-09-26 15:00", "content": "茶百道把大熊猫带到法国，文化输出和商业价值双赢，这个IP选得太对了", "likes": 1234, "sentiment": "正向"},
                {"user": "餐饮出海分析师", "time": "2025-09-27 10:00", "content": "巴黎成功能否复制还要看持续运营，华人流量之外能否打入本地消费是关键", "likes": 678, "sentiment": "中性"},
            ],
        },
        {
            "id": "cp_003",
            "title": "黑猫投诉：茶百道水果变质问题引关注 加盟品控待加强",
            "source": "小红书",
            "time": "2026-04-25",
            "heat": "🔥🔥 中热",
            "overall_sentiment": "负向",
            "comments": [
                {"user": "食品安全关注者", "time": "2026-04-25 10:00", "content": "黑猫平台茶百道投诉3490条，水果变质和服务态度差占六成，加盟制度下品控真的难", "likes": 2108, "sentiment": "负向"},
                {"user": "加盟商吐槽区", "time": "2026-04-25 14:30", "content": "总部要求用指定供应商，但供应链跟不上旺季，水果到货新鲜度确实不稳定", "likes": 1456, "sentiment": "负向"},
                {"user": "消费维权助手", "time": "2026-04-26 09:00", "content": "8000家门店，供应链标准化是个真问题，建议茶百道公开供应商质量标准", "likes": 934, "sentiment": "中性"},
                {"user": "茶百道普通粉丝", "time": "2026-04-26 11:00", "content": "我常去的那家门店挺好的，可能是个别门店问题，不要一棒子打死", "likes": 445, "sentiment": "中性"},
            ],
        },
    ],
}

# ── 行业动态样本（基于2025-2026公开媒体报道整理）────────────────────
_INDUSTRY_TRENDS: list[dict] = [
    {
        "id": "ind_001",
        "title": "新茶饮行业分化加剧：茶百道盈利71%，奈雪亏损收窄，喜茶纠错收缩",
        "source": "澎湃新闻·复盘2025",
        "time": "2026-01-15",
        "category": "行业报告",
        "summary": "2025年新茶饮三巨头走向分化：茶百道营收53.95亿净利8.2亿（+71%），是三品牌中唯一稳定盈利者；奈雪营收43.31亿亏损2.43亿（收窄73.8%）；喜茶关闭近700家加盟店转型高端。行业从规模竞争转向单店效益竞争。（来源：各品牌公开财报/港交所公告）",
        "comments": [
            {"user": "餐饮行业研究员", "time": "2026-01-15 10:00", "content": "加盟模式的茶百道反而最赚钱，直营模式的奈雪一直亏，这个对比值得品牌深思", "likes": 2341},
            {"user": "消费投资观察", "time": "2026-01-15 14:00", "content": "行业从拼规模到拼效率，2026年单店日销和坪效会成为核心评价指标", "likes": 1567},
            {"user": "茶饮创业者", "time": "2026-01-16 09:00", "content": "三巨头的分化给中小品牌一个信号：找准定位比盲目扩张重要得多", "likes": 892},
        ],
    },
    {
        "id": "ind_002",
        "title": "新茶饮出海进入规模化竞争：喜茶破100家，茶百道落地法国巴黎",
        "source": "虎嗅·品牌出海专题",
        "time": "2026-02-10",
        "category": "竞品动向",
        "summary": "2025年新茶饮出海加速：喜茶海外门店超100家（覆盖8国28城），纽约时代广场LAB店单日销量超3500杯；茶百道法国巴黎首店开业首周销售额近50万元，已落地8国21家门店；霸王茶姬东南亚市场持续扩张。出海从华人流量走向本地化运营。（来源：公开媒体报道）",
        "comments": [
            {"user": "品牌全球化观察", "time": "2026-02-10 10:00", "content": "华人社区是流量起点，但要在海外真正做大，本地化运营才是核心竞争力", "likes": 1876},
            {"user": "海外餐饮创业者", "time": "2026-02-11 09:00", "content": "原料供应链是出海最大痛点，是在地化采购还是从国内空运，成本模型完全不同", "likes": 1203},
        ],
    },
    {
        "id": "ind_003",
        "title": "2025年茶饮联名创历史记录：全年270次，奈雪最多，喜茶最高级",
        "source": "知乎·茶饮营销年度盘点",
        "time": "2026-01-05",
        "category": "营销趋势",
        "summary": "据公开统计，2025年三大品牌联名活动合计超270次：奈雪联名次数最多，喜茶联名调性最高（FENDI、藤原浩等高端IP），茶百道以熊猫IP为核心主打情感联名。消费者调研显示联名疲劳感初现，品牌需从频率导向转向质量导向。（来源：知乎专栏公开数据整理）",
        "comments": [
            {"user": "营销案例研究者", "time": "2026-01-05 16:00", "content": "270次联名是个警号，消费者已经对联名免疫，下一步品牌需要找回产品本身的故事力", "likes": 2108},
            {"user": "品牌策略师", "time": "2026-01-06 10:00", "content": "喜茶高端联名路线是对的，但要防止联名过多稀释高端感，FENDI联名的溢价已经被其他联名摊薄了", "likes": 1456},
            {"user": "消费者视角", "time": "2026-01-06 14:00", "content": "买联名杯套周边还是买，但复购核心还是茶本身好喝，联名留不住回头客", "likes": 934},
        ],
    },
    {
        "id": "ind_004",
        "title": "健康化成新茶饮核心赛道：低GI、0添加、植物基全面铺开",
        "source": "食品产业研究·2026年度趋势",
        "time": "2026-03-01",
        "category": "消费洞察",
        "summary": "2025年三品牌均加速健康化布局：奈雪健康产品占比达42%，推出低GI多纤系列和纤·Studio概念店；喜茶超级植物茶10天销量破160万杯；茶百道新品117款中健康方向占比提升。消费者对成分透明度要求持续提升，「0添加、真实原料、低糖无糖」成选购首要标准。（来源：各品牌公告及公开媒体报道）",
        "comments": [
            {"user": "健康食品研究员", "time": "2026-03-01 11:00", "content": "低GI茶饮是真需求还是营销概念，关键看品牌能不能拿出第三方检测数据", "likes": 1876},
            {"user": "营养师观点", "time": "2026-03-02 09:00", "content": "0添加承诺要经得起配料表检验，消费者越来越懂看标签，品牌不能只靠话术", "likes": 1345},
            {"user": "投资机构分析师", "time": "2026-03-02 14:00", "content": "健康化不是差异化，是入场券，谁在健康基础上还有独特口感和场景才是真竞争力", "likes": 892},
        ],
    },
    {
        "id": "ind_005",
        "title": "新茶饮品控危机：茶百道3490条投诉，加盟制度下食品安全管理待解",
        "source": "腾讯新闻·消费维权报道",
        "time": "2026-04-27",
        "category": "品类趋势",
        "summary": "截至2026年4月，黑猫投诉平台累计收到茶百道相关投诉3490条，\"水果变质\"和\"服务态度差\"占比超六成。公开媒体曾报道成都某门店使用腐烂芒果事件。加盟制度下的供应链品控是整个行业共性挑战，喜茶因此暂停加盟、奈雪坚持直营均与此相关。（来源：黑猫投诉平台公开数据、腾讯新闻公开报道）",
        "comments": [
            {"user": "食品安全监督者", "time": "2026-04-27 10:00", "content": "3490条投诉不是小数，万店规模下1/3的门店有问题就是系统性风险，不是个例", "likes": 2341},
            {"user": "加盟连锁研究者", "time": "2026-04-27 14:00", "content": "加盟制快速扩张的代价就是品控难题，茶百道需要在供应链管理上投入和盈利同等量级的资源", "likes": 1567},
            {"user": "消费者权益保护", "time": "2026-04-28 09:00", "content": "监管层面也需要跟上，万店茶饮品牌的食品安全抽查机制应该更严格", "likes": 1203},
        ],
    },
]


def collect_brand_sentiment(brand_key: str, platform: str = "全渠道", days: int = 30) -> list[dict]:
    """返回指定品牌的模拟舆情采集结果"""
    data = _BRAND_SENTIMENT.get(brand_key, [])
    if platform != "全渠道":
        data = [t for t in data if t["source"] == platform] or data
    return data


def collect_industry_trends(category: str = "全部", brand_key: str = "") -> list[dict]:
    """返回行业动态模拟采集结果。
    茶饮三品牌返回预置数据；其他品牌根据行业动态生成通用内容。
    """
    # 茶饮品牌使用预置数据
    if brand_key in ("heytea", "nayuki", "chapanda"):
        if category == "全部":
            return _INDUSTRY_TRENDS
        return [t for t in _INDUSTRY_TRENDS if t["category"] == category] or _INDUSTRY_TRENDS

    # 其他品牌：根据品牌行业生成通用行业动态
    try:
        from config.brand_manager import get_brand as _get_brand
        b = _get_brand(brand_key) or {}
    except Exception:
        b = {}

    brand_name = b.get("name", brand_key)
    industry   = b.get("industry", "其他")
    focus      = b.get("focus", "品牌增长")

    today = datetime.now()

    generic_trends = [
        {
            "id": f"{brand_key}_ind_001",
            "title": f"{industry}行业2025年度复盘：数字化转型成核心增长驱动力",
            "source": "36氪·行业年度报告",
            "time": (today - timedelta(days=60)).strftime("%Y-%m-%d"),
            "category": "行业报告",
            "summary": f"2025年{industry}行业整体保持稳健增长，头部品牌通过数字化运营和精细化用户管理获得明显优势。AI工具在内容生产、用户洞察和投放优化方面的应用显著提升效率。{brand_name}所处赛道的核心趋势包括：{focus}。",
            "comments": [
                {"user": "行业分析师", "time": (today - timedelta(days=60)).strftime("%Y-%m-%d %H:%M"), "content": f"{industry}行业正在经历从流量驱动到品牌价值驱动的转型，精细运营比粗放扩张更有复利效应", "likes": 1876},
                {"user": "品牌运营总监", "time": (today - timedelta(days=59)).strftime("%Y-%m-%d %H:%M"), "content": "数字化不是选项，是标配。谁先把数据资产建起来，谁就有定价权", "likes": 1234},
            ],
        },
        {
            "id": f"{brand_key}_ind_002",
            "title": f"{industry}头部品牌竞争格局：差异化定位成关键突围路径",
            "source": "虎嗅·品牌竞争专题",
            "time": (today - timedelta(days=45)).strftime("%Y-%m-%d"),
            "category": "竞品动向",
            "summary": f"{industry}赛道竞争持续加剧，同质化产品面临价格战压力。头部品牌通过强化品牌个性、深耕目标人群和构建差异化体验形成护城河。{brand_name}在{focus}方向的布局正是应对竞争的核心策略。",
            "comments": [
                {"user": "战略咨询顾问", "time": (today - timedelta(days=45)).strftime("%Y-%m-%d %H:%M"), "content": "差异化不是口号，是要真正找到竞争对手无法轻易复制的核心能力", "likes": 1567},
                {"user": "投资机构分析师", "time": (today - timedelta(days=44)).strftime("%Y-%m-%d %H:%M"), "content": f"{industry}赛道的品牌壁垒越来越体现在用户心智上，而不是渠道规模上", "likes": 934},
            ],
        },
        {
            "id": f"{brand_key}_ind_003",
            "title": f"AI+内容营销重塑{industry}品牌传播：小红书、抖音双平台策略成标配",
            "source": "数英·营销趋势报告",
            "time": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
            "category": "营销趋势",
            "summary": f"2025年AI生成内容（AIGC）在{industry}品牌营销中普及率大幅提升，头部品牌已将AI工具纳入日常内容生产流程，效率提升3-5倍。小红书种草+抖音转化的双平台策略成为{industry}行业标配打法。KOC微影响力账号的ROI普遍优于头部KOL。",
            "comments": [
                {"user": "内容营销专家", "time": (today - timedelta(days=30)).strftime("%Y-%m-%d %H:%M"), "content": "AIGC降低了内容生产门槛，但品牌的审美和调性把控能力变得更重要", "likes": 2108},
                {"user": "社媒运营负责人", "time": (today - timedelta(days=29)).strftime("%Y-%m-%d %H:%M"), "content": "KOC的内容更真实可信，转化率比大V高，但需要更精细的筛选和管理机制", "likes": 1345},
            ],
        },
        {
            "id": f"{brand_key}_ind_004",
            "title": f"{industry}消费者洞察：Z世代成核心购买力，价值认同驱动复购",
            "source": "尼尔森·消费者行为研究",
            "time": (today - timedelta(days=20)).strftime("%Y-%m-%d"),
            "category": "消费洞察",
            "summary": f"Z世代（1995-2009年出生）已成为{industry}行业的核心消费群体，他们的购买决策更注重品牌价值观认同、社交货币属性和使用体验，对价格敏感度低于千禧一代但对品质要求更高。品牌真实性和可持续理念成为重要加分项。",
            "comments": [
                {"user": "消费行为研究员", "time": (today - timedelta(days=20)).strftime("%Y-%m-%d %H:%M"), "content": "Z世代不是被广告说服的，而是被价值观感召的。品牌要做的是找到共同语言", "likes": 1789},
                {"user": "用户增长专家", "time": (today - timedelta(days=19)).strftime("%Y-%m-%d %H:%M"), "content": "复购率才是真正的健康指标，首购靠营销，复购靠产品和体验", "likes": 1234},
            ],
        },
        {
            "id": f"{brand_key}_ind_005",
            "title": f"{industry}品牌合规新挑战：广告法、数据安全与ESG披露要求趋严",
            "source": "法治日报·合规专题",
            "time": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
            "category": "品类趋势",
            "summary": f"2025-2026年{industry}行业面临更严格的合规要求：广告法对夸大宣传的处罚力度加大；个人信息保护法对用户数据收集使用的限制增多；ESG信息披露要求逐步向中小企业延伸。合规成本上升但也是建立品牌信任的契机。",
            "comments": [
                {"user": "法律合规顾问", "time": (today - timedelta(days=10)).strftime("%Y-%m-%d %H:%M"), "content": "合规不应该是被动应对监管，而是主动建立品牌可信度的机会", "likes": 892},
                {"user": "品牌公关总监", "time": (today - timedelta(days=9)).strftime("%Y-%m-%d %H:%M"), "content": "消费者越来越关注品牌的社会责任，ESG不是大企业的专利，中小品牌也需要有自己的叙事", "likes": 678},
            ],
        },
    ]

    if category == "全部":
        return generic_trends
    cat_map = {"行业报告": 0, "竞品动向": 1, "营销趋势": 2, "消费洞察": 3, "品类趋势": 4}
    idx = cat_map.get(category)
    return [generic_trends[idx]] if idx is not None else generic_trends


def flatten_comments_for_sentiment(topics: list[dict]) -> str:
    """将话题评论列表展开为舆情分析可用的文本格式"""
    lines = []
    for t in topics:
        lines.append(f"【话题：{t['title']}】（{t['source']} · {t['time']}）")
        for c in t["comments"]:
            lines.append(f"  @{c['user']}：{c['content']}")
        lines.append("")
    return "\n".join(lines)
