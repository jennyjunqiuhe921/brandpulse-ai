"""舆情采集模块 — Demo 模式预置数据 + 采集逻辑"""
from datetime import datetime, timedelta
import random

# ── Demo 品牌舆情数据 ────────────────────────────────────────────────
_BRAND_SENTIMENT: dict[str, list[dict]] = {
    "heytea": [
        {
            "id": "ht_001",
            "title": "喜茶新品「多肉青提」首周口碑汇总",
            "source": "小红书",
            "time": "2025-06-18",
            "heat": "🔥🔥🔥 高热",
            "overall_sentiment": "正向",
            "comments": [
                {"user": "茶饮博主_晴天", "time": "2025-06-18 14:23", "content": "青提颗粒超大，果汁感很足！就是排队要40分钟 😅 但真的值得等", "likes": 1284, "sentiment": "正向"},
                {"user": "奶茶控Annie", "time": "2025-06-18 15:01", "content": "不甜不腻，比上季草莓味好喝很多，今年夏天就它了", "likes": 892, "sentiment": "正向"},
                {"user": "设计师小K", "time": "2025-06-18 16:45", "content": "颜值太高了，绿色渐变杯超出片，今天连发三条朋友圈", "likes": 673, "sentiment": "正向"},
                {"user": "健康生活家", "time": "2025-06-19 09:12", "content": "30多块一杯，喝完荷包疼，但是真的好喝没法反驳", "likes": 441, "sentiment": "中性"},
                {"user": "打工人日常", "time": "2025-06-19 12:33", "content": "附近门店下午三点就卖完了……能不能多备点货", "likes": 328, "sentiment": "负向"},
            ],
        },
        {
            "id": "ht_002",
            "title": "喜茶GO小程序体验 & 排队优化讨论",
            "source": "微博",
            "time": "2025-06-15",
            "heat": "🔥🔥 中热",
            "overall_sentiment": "中性",
            "comments": [
                {"user": "城市生活志", "time": "2025-06-15 10:05", "content": "喜茶GO预约功能终于好用了，不用在店里干等，体验感升级很多", "likes": 567, "sentiment": "正向"},
                {"user": "效率控007", "time": "2025-06-15 11:22", "content": "预计等待20分钟，实际等了45分钟，高峰期准确率有待提升", "likes": 334, "sentiment": "负向"},
                {"user": "喜茶资深粉", "time": "2025-06-15 14:08", "content": "和两年前比进步了很多，但和luckin的数字化体验还有差距", "likes": 219, "sentiment": "中性"},
            ],
        },
        {
            "id": "ht_003",
            "title": "喜茶 × 国潮品牌联名限定款引发关注",
            "source": "抖音",
            "time": "2025-06-10",
            "heat": "🔥🔥🔥 高热",
            "overall_sentiment": "正向",
            "comments": [
                {"user": "潮流追踪者", "time": "2025-06-10 20:15", "content": "联名设计真的好看！杯套收藏了，国风美学拿捏了", "likes": 2341, "sentiment": "正向"},
                {"user": "营销观察", "time": "2025-06-10 21:00", "content": "喜茶联名频率很高，保持住品质和调性是关键，不能为了联名而联名", "likes": 876, "sentiment": "中性"},
                {"user": "二次元小仙女", "time": "2025-06-11 09:30", "content": "买不到！限量补货什么时候来", "likes": 543, "sentiment": "负向"},
            ],
        },
    ],
    "nayuki": [
        {
            "id": "ny_001",
            "title": "奈雪新品「霸气橙子」季节限定评测",
            "source": "小红书",
            "time": "2025-06-17",
            "heat": "🔥🔥 中热",
            "overall_sentiment": "正向",
            "comments": [
                {"user": "精致生活研究所", "time": "2025-06-17 13:45", "content": "橙子榨汁现做，维C感满满，这个夏天的续命饮品", "likes": 934, "sentiment": "正向"},
                {"user": "甜品控小雅", "time": "2025-06-17 15:20", "content": "搭配软欧包真的很有腔调，奈雪的场景感做得比其他品牌好很多", "likes": 712, "sentiment": "正向"},
                {"user": "理性消费派", "time": "2025-06-18 10:00", "content": "35一杯，鲜果茶定价确实偏高，消费降级下性价比不占优", "likes": 489, "sentiment": "负向"},
            ],
        },
        {
            "id": "ny_002",
            "title": "奈雪的茶门店空间体验：第三空间测评",
            "source": "微博",
            "time": "2025-06-12",
            "heat": "🔥 低热",
            "overall_sentiment": "正向",
            "comments": [
                {"user": "都市慢生活", "time": "2025-06-12 16:00", "content": "旗舰店真的很大，有沙发有大桌，工作下午茶两不误", "likes": 423, "sentiment": "正向"},
                {"user": "空间设计迷", "time": "2025-06-12 17:30", "content": "奈雪的软装和选址都很用心，是茶饮里少有的有\"空间溢价\"的品牌", "likes": 318, "sentiment": "正向"},
                {"user": "上班族日记", "time": "2025-06-13 09:00", "content": "周末人太多，座位不好找，建议增加预约桌位功能", "likes": 201, "sentiment": "中性"},
            ],
        },
        {
            "id": "ny_003",
            "title": "奈雪会员积分政策调整，用户反应两极分化",
            "source": "抖音",
            "time": "2025-06-08",
            "heat": "🔥🔥 中热",
            "overall_sentiment": "中性",
            "comments": [
                {"user": "会员忠实粉", "time": "2025-06-08 19:00", "content": "新政策积分兑换门槛变高了，作为老会员感觉有点吃亏", "likes": 678, "sentiment": "负向"},
                {"user": "新用户晓晓", "time": "2025-06-09 10:15", "content": "刚开始用奈雪，感觉新人礼包还不错，买一送一超划算", "likes": 445, "sentiment": "正向"},
                {"user": "品牌观察家", "time": "2025-06-09 14:00", "content": "会员政策调整是常规运营行为，关键是调整后留存率有没有下降", "likes": 312, "sentiment": "中性"},
            ],
        },
    ],
    "chapanda": [
        {
            "id": "cp_001",
            "title": "茶百道「杨枝甘露」夏日限定版：性价比之王？",
            "source": "小红书",
            "time": "2025-06-16",
            "heat": "🔥🔥🔥 高热",
            "overall_sentiment": "正向",
            "comments": [
                {"user": "平价茶饮测评", "time": "2025-06-16 12:00", "content": "15块钱喝到鲜芒果+椰浆，性价比真的没得说，喜茶同款要贵一倍", "likes": 1876, "sentiment": "正向"},
                {"user": "芒果爱好者", "time": "2025-06-16 13:30", "content": "芒果粒很大块，椰浆够浓，西柚酸度刚好平衡，这个配方很成熟", "likes": 1203, "sentiment": "正向"},
                {"user": "挑剔的吃货", "time": "2025-06-16 15:00", "content": "有几家门店的芒果不够熟，吃起来有点涩，品质稳定性需要把关", "likes": 567, "sentiment": "负向"},
                {"user": "下沉市场观察", "time": "2025-06-17 10:00", "content": "在三线城市茶百道简直是统治级别，每个商圈至少两家，方便得很", "likes": 432, "sentiment": "正向"},
            ],
        },
        {
            "id": "cp_002",
            "title": "茶百道熊猫IP周边引发收集热潮",
            "source": "抖音",
            "time": "2025-06-14",
            "heat": "🔥🔥 中热",
            "overall_sentiment": "正向",
            "comments": [
                {"user": "IP收藏家", "time": "2025-06-14 20:00", "content": "丁丁猫联名杯第三款出了！已经集齐整套，茶百道IP运营真的用心", "likes": 2108, "sentiment": "正向"},
                {"user": "熊猫粉后援会", "time": "2025-06-14 21:15", "content": "熊猫周边每次都抢不到，限量补货能不能多一点", "likes": 934, "sentiment": "中性"},
                {"user": "品牌IP研究", "time": "2025-06-15 09:00", "content": "茶百道把IP做成了核心差异化资产，在同价位竞品里辨识度最高", "likes": 678, "sentiment": "正向"},
            ],
        },
        {
            "id": "cp_003",
            "title": "茶百道加盟政策2025最新动态",
            "source": "微博",
            "time": "2025-06-11",
            "heat": "🔥 低热",
            "overall_sentiment": "中性",
            "comments": [
                {"user": "餐饮创业者老王", "time": "2025-06-11 10:00", "content": "相比蜜雪冰城，茶百道加盟门槛稍高，但品牌力更强，流量更稳定", "likes": 345, "sentiment": "正向"},
                {"user": "加盟踩坑指南", "time": "2025-06-11 14:00", "content": "不同城市的盈利差异很大，二线城市竞争已经很激烈了，要谨慎评估", "likes": 289, "sentiment": "中性"},
                {"user": "茶饮行业分析师", "time": "2025-06-12 09:30", "content": "万店规模下供应链管理和品控标准化是茶百道未来的核心挑战", "likes": 212, "sentiment": "中性"},
            ],
        },
    ],
}

# ── Demo 行业动态数据 ────────────────────────────────────────────────
_INDUSTRY_TRENDS: list[dict] = [
    {
        "id": "ind_001",
        "title": "2025夏季茶饮趋势报告：鲜果茶持续增长，低糖化成主流",
        "source": "36氪",
        "time": "2025-06-15",
        "category": "行业报告",
        "summary": "据最新市场调研，鲜果茶品类同比增长34%，低糖/无糖选项在点单中占比已超40%。消费者对成分透明度要求提升，「看得见的原料」成为新卖点。",
        "comments": [
            {"user": "茶饮行业观察", "time": "2025-06-15 10:00", "content": "低糖化是不可逆的趋势，品牌必须在菜单结构上主动适配", "likes": 876},
            {"user": "快消品研究员", "time": "2025-06-15 11:30", "content": "鲜果茶的供应链壁垒比其他品类高很多，这是中高端品牌的护城河", "likes": 634},
            {"user": "消费投资人", "time": "2025-06-16 09:00", "content": "低糖赛道的核心还是口感，不能为了低糖牺牲风味，这是很多品牌踩过的坑", "likes": 445},
        ],
    },
    {
        "id": "ind_002",
        "title": "新式茶饮出海加速：东南亚市场竞争格局分析",
        "source": "虎嗅",
        "time": "2025-06-12",
        "category": "竞品动向",
        "summary": "霸王茶姬在东南亚门店数突破500家，茶百道新加坡店开业排长队。新式茶饮出海已从「尝试期」进入「规模化竞争期」，本土化运营能力成关键。",
        "comments": [
            {"user": "海外餐饮观察", "time": "2025-06-12 14:00", "content": "东南亚的华人社区是第一波流量，但要真正做大必须打进本地消费者", "likes": 567},
            {"user": "品牌全球化研究", "time": "2025-06-13 10:00", "content": "中国茶饮出海面临的最大挑战是原料供应链，在地化采购还是从国内运输，成本差异巨大", "likes": 423},
        ],
    },
    {
        "id": "ind_003",
        "title": "联名营销升温：茶饮品牌跨界联名频率创历史新高",
        "source": "营销前线",
        "time": "2025-06-10",
        "category": "营销趋势",
        "summary": "上半年茶饮品牌联名事件同比增长67%，IP联名、国潮联名、影视联名为三大主力方向。但调研显示消费者对联名的\"新鲜感疲劳\"开始显现，品牌需关注联名质量而非频率。",
        "comments": [
            {"user": "营销案例库", "time": "2025-06-10 16:00", "content": "联名泡沫的信号已经出现，下半年可能会看到一波\"联名减速\"", "likes": 789},
            {"user": "品牌策略师K", "time": "2025-06-10 17:30", "content": "真正好的联名应该是1+1>2，品牌调性契合比IP知名度更重要", "likes": 612},
            {"user": "消费者代表", "time": "2025-06-11 09:00", "content": "买联名主要还是为了杯子和周边，茶本身好喝才是复购的核心", "likes": 445},
        ],
    },
    {
        "id": "ind_004",
        "title": "00后消费行为研究：茶饮消费偏好与品牌忠诚度报告",
        "source": "CBNData",
        "time": "2025-06-08",
        "category": "消费洞察",
        "summary": "研究显示00后月均茶饮消费4.2次，品牌忠诚度较低，「好奇心驱动」是主要购买动机。小红书是最重要的种草渠道，占比达58%。颜值和出片效果对购买决策影响显著。",
        "comments": [
            {"user": "年轻人研究所", "time": "2025-06-08 11:00", "content": "00后的消费忠诚度确实很低，品牌要靠持续创新而不是靠「老粉」维系", "likes": 934},
            {"user": "小红书运营总监", "time": "2025-06-08 14:00", "content": "58%的种草来自小红书，这个数据值得所有茶饮品牌重视", "likes": 712},
            {"user": "产品经理视角", "time": "2025-06-09 10:00", "content": "「好奇心驱动」意味着新品开发节奏要跟上，但也要防止菜单过于复杂", "likes": 489},
        ],
    },
    {
        "id": "ind_005",
        "title": "植物基茶饮崛起：燕麦奶、椰乳替代品需求激增",
        "source": "食品产业网",
        "time": "2025-06-05",
        "category": "品类趋势",
        "summary": "植物基奶茶订单量同比增长89%，燕麦奶替换占比最高。乳糖不耐人群和素食群体是主要需求驱动，各大品牌已开始在菜单中标注可替换选项。",
        "comments": [
            {"user": "健康饮食博主", "time": "2025-06-05 16:00", "content": "植物基才是未来，希望各品牌加快推进，燕麦奶加价还是有点高", "likes": 567},
            {"user": "乳制品行业分析", "time": "2025-06-06 09:00", "content": "植物基成本比普通鲜奶高30-50%，要推广需要解决定价和消费者教育两个问题", "likes": 423},
        ],
    },
]


def collect_brand_sentiment(brand_key: str, platform: str = "全渠道", days: int = 30) -> list[dict]:
    """返回指定品牌的模拟舆情采集结果"""
    data = _BRAND_SENTIMENT.get(brand_key, [])
    if platform != "全渠道":
        data = [t for t in data if t["source"] == platform] or data
    return data


def collect_industry_trends(category: str = "全部") -> list[dict]:
    """返回行业动态模拟采集结果"""
    if category == "全部":
        return _INDUSTRY_TRENDS
    return [t for t in _INDUSTRY_TRENDS if t["category"] == category] or _INDUSTRY_TRENDS


def flatten_comments_for_sentiment(topics: list[dict]) -> str:
    """将话题评论列表展开为舆情分析可用的文本格式"""
    lines = []
    for t in topics:
        lines.append(f"【话题：{t['title']}】（{t['source']} · {t['time']}）")
        for c in t["comments"]:
            lines.append(f"  @{c['user']}：{c['content']}")
        lines.append("")
    return "\n".join(lines)
