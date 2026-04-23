"""
分类映射配置
根据用户提供的页面信息配置
"""

CATEGORY_MAPPING = {
    "guowuyuan": {
        "name": "国务院文件",
        "code": "c102440",
        "channel_id": "fa1726b47078490fa0a4522194185e8d",
        "total_pages": 4,
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c102440/listflfg.html"
    },
    "caishui": {
        "name": "财税文件",
        "code": "c102416",
        "channel_id": "2cb303fdee614232b79552d52bb057d6",
        "total_pages": 152,
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c102416/listflfg.html"
    },
    "guifanxing": {
        "name": "税务规范性文件",
        "code": "c100012",
        "channel_id": "470b437b304f434396500a1e2edc7f28",
        "total_pages": 192,
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c100012/listflfg.html"
    },
    "qita": {
        "name": "其他文件",
        "code": "c100013",
        "channel_id": "4c1a5be62f6d44d48f386f630dcebbc5",
        "total_pages": 48,
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c100013/listflfg.html"
    },
    "gongzuo": {
        "name": "工作通知",
        "code": "c102424",
        "channel_id": "7778c3a40a344de3a36ca88a2548f5f8",
        "total_pages": 85,
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c102424/listflfg.html"
    },
    "falv": {
        "name": "法律",
        "code": "c100009",
        "channel_id": "d34fa7ad03f84f4caed12f5c2beae099",
        "total_pages": 8,
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c100009/listflfg_fg.html"
    },
    "xingzhengfagui": {
        "name": "行政法规",
        "code": "c100010",
        "channel_id": "e1cd1569d1ea4a25a11041248925a081",
        "total_pages": 7,
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c100010/listflfg_fg.html"
    },
    "guizhang": {
        "name": "税务部门规章",
        "code": "c100011",
        "channel_id": "0ac34e96afbb4be28844f18eef412421",
        "total_pages": 9,
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c100011/list_guizhang.html"
    }
}

CATEGORY_NAMES = {k: v["name"] for k, v in CATEGORY_MAPPING.items()}
