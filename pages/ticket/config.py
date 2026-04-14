"""作业票类型配置 — 7 种作业票的字段差异全部参数化"""

from __future__ import annotations

from dataclasses import dataclass, field


# ============================================================
# 字段定义
# ============================================================

@dataclass
class FieldDef:
    """表单字段定义"""
    key: str            # 字段名
    label: str          # 显示标签
    widget: str         # input / select_single / select_multi / datetime / radio / number
    required: bool = True
    # 数据源键名（select_single/select_multi 时使用）
    source: str = ""
    # 条件显示：依赖字段和值，如 ("sfxyaqjc", "1") 表示 sfxyaqjc=="1" 时才显示
    condition: tuple[str, str] | None = None
    # radio 选项
    radio_options: list[dict] | None = None


# 是/否 选项（通用）
YES_NO = [{"text": "否", "value": "0"}, {"text": "是", "value": "1"}]


# ============================================================
# 公共字段（所有类型共享）
# ============================================================

COMMON_FIELDS: list[FieldDef] = [
    FieldDef("sqdw", "申请单位", "select_single", source="departs"),
    FieldDef("sqr", "申请人", "select_single", source="peoples"),
    FieldDef("cameraId", "摄像头", "select_multi", required=False, source="cameras"),
]

# 所有类型末尾的公共审批字段
COMMON_TAIL_FIELDS: list[FieldDef] = [
    FieldDef("sjdqttszy", "涉及的其他特殊作业", "select_multi", required=False, source="typeList"),
    FieldDef("sjdqttszyaqzyzbh", "涉及的其他特殊作业证编号", "select_multi", required=False, source="qttsywbhs"),
    FieldDef("qtaqcsbzr", "其他安全措施编制人", "select_multi", source="peoples"),
    FieldDef("aqjdr", "安全交底人", "select_multi", source="peoples"),
    FieldDef("jsjdr", "接受交底人", "select_multi", source="peoples"),
]

# 动火作业尾部字段：证编号字段名为 qttsywbh（与其他类型不同）
DH_TAIL_FIELDS: list[FieldDef] = [
    FieldDef("sjdqttszy", "涉及的其他特殊作业", "select_multi", required=False, source="typeList"),
    FieldDef("qttsywbh", "涉及的其他特殊作业证编号", "select_multi", required=False, source="qttsywbhs"),
    FieldDef("qtaqcsbzr", "其他安全措施编制人", "select_multi", source="peoples"),
    FieldDef("aqjdr", "安全交底人", "select_multi", source="peoples"),
    FieldDef("jsjdr", "接受交底人", "select_multi", source="peoples"),
]

COMMON_END_FIELDS: list[FieldDef] = [
    FieldDef("szdw", "所在单位负责人", "select_multi", source="peoples"),
    FieldDef("ysr", "验收人", "select_multi", source="peoples"),
]


# ============================================================
# 各类型特有字段
# ============================================================

DH_FIELDS: list[FieldDef] = [
    FieldDef("beginTime", "作业开始时间", "datetime"),
    FieldDef("endTime", "作业结束时间", "datetime"),
    FieldDef("zydd", "动火地点及动火部位", "input"),
    FieldDef("zynr", "作业内容", "input"),
    FieldDef("zyjb", "动火作业级别", "select_single", source="zyjbs"),
    FieldDef("zyfs", "动火方式", "input"),
    FieldDef("sgdw", "作业单位", "input"),
    FieldDef("zyr", "作业人", "select_multi", source="peoplesZS"),
    FieldDef("dhzsbh", "动火人证书编号", "select_multi", source="peoplesZSs"),
    FieldDef("jhr", "监护人", "select_multi", source="peoples"),
    FieldDef("jhrzsbh", "监护人证书编号", "input", required=False),
    FieldDef("sfxyaqjc", "是否需要动火分析", "radio", radio_options=YES_NO),
    FieldDef("aqjcr", "动火分析人", "select_multi", source="peoples", condition=("sfxyaqjc", "1")),
    # 审批链
    FieldDef("zyfzr", "作业负责人", "select_multi", source="peoples"),
    FieldDef("aqglbm", "安全管理部门人员", "select_multi", source="peoples"),
    FieldDef("zyspr", "动火审批人", "select_multi", source="peoples"),
    FieldDef("dhqgwdbbcyp", "动火前岗位当班班长验票", "select_multi", source="peoples"),
]

# 动火作业详情页额外展示字段（仅详情用，不在表单中出现）
DH_DETAIL_EXTRA_FIELDS: list[FieldDef] = [
    FieldDef("createTime", "作业申请时间", "input", required=False),
    FieldDef("zyzbh", "作业证编号", "input", required=False),
    FieldDef("whbs", "风险辨识结果", "input", required=False),
    FieldDef("startTime", "动火作业实施开始时间", "input", required=False),
    FieldDef("dhEndTime", "动火作业实施结束时间", "input", required=False),
    FieldDef("time", "作业时间（s）", "input", required=False),
]

SXKJ_FIELDS: list[FieldDef] = [
    FieldDef("zysqsj", "申请时间", "datetime"),
    FieldDef("zyshkssj", "作业开始时间", "datetime"),
    FieldDef("zyssjssj", "作业结束时间", "datetime"),
    FieldDef("sxkjssdw", "作业单位", "input"),
    FieldDef("zydd", "作业地点", "input"),
    FieldDef("zynr", "作业内容", "input"),
    FieldDef("sxkjmc", "受限空间名称", "input"),
    FieldDef("sxkjnyyjzmc", "受限空间内原有介质名称", "input"),
    FieldDef("jhr", "监护人", "select_multi", source="peoples"),
    FieldDef("zyr", "作业人", "select_multi", source="peoples"),
    FieldDef("sfxysxkjfx", "是否需要受限空间分析", "radio", radio_options=YES_NO),
    FieldDef("sxkjfxr", "受限空间分析人", "select_multi", source="peoples", condition=("sfxysxkjfx", "1")),
    FieldDef("zyfzr", "作业负责人", "select_multi", source="peoples"),
    FieldDef("shbmfzr", "审核部门负责人", "select_multi", source="peoples"),
    FieldDef("spbmfzr", "审批部门负责人", "select_multi", source="peoples"),
]

GC_FIELDS: list[FieldDef] = [
    FieldDef("zysqsj", "申请时间", "datetime"),
    FieldDef("zyshkssj", "作业开始时间", "datetime"),
    FieldDef("zyssjssj", "作业结束时间", "datetime"),
    FieldDef("zydd", "作业地点", "input"),
    FieldDef("zynr", "作业内容", "input"),
    FieldDef("zygd", "作业高度(米)", "number"),
    FieldDef("zyjb", "作业级别", "select_single", source="zyjbs"),
    FieldDef("zydw", "作业单位", "input"),
    FieldDef("jhr", "监护人", "select_multi", source="peoples"),
    FieldDef("zyr", "作业人", "select_multi", source="peoples"),
    FieldDef("zyfzr", "作业负责人", "select_multi", source="peoples"),
    FieldDef("shbmfzr", "审核部门负责人", "select_multi", source="peoples"),
    FieldDef("spbmfzr", "审批部门负责人", "select_multi", source="peoples"),
]

DZ_FIELDS: list[FieldDef] = [
    FieldDef("zysqsj", "申请时间", "datetime"),
    FieldDef("zyshkssj", "作业开始时间", "datetime"),
    FieldDef("zyssjssj", "作业结束时间", "datetime"),
    FieldDef("dzdd", "吊装地点", "input"),
    FieldDef("dzgjmc", "吊具名称", "input"),
    FieldDef("dznr", "吊物内容", "input"),
    FieldDef("zyr", "吊装作业人", "select_multi", source="peoples"),
    FieldDef("ssr", "司索人", "select_multi", source="peoples"),
    FieldDef("qdzwzl", "吊物质量(t)", "number"),
    FieldDef("zyjb", "作业级别", "select_single", source="zyjbs"),
    FieldDef("jhr", "监护人", "select_multi", source="peoples"),
    FieldDef("zyzh", "作业指挥", "select_multi", source="peoples"),
    FieldDef("zyfzr", "作业负责人", "select_multi", source="peoples"),
    FieldDef("shbmfzr", "审核部门负责人", "select_multi", source="peoples"),
    FieldDef("spbmfzr", "审批部门负责人", "select_multi", source="peoples"),
]

LSYD_FIELDS: list[FieldDef] = [
    FieldDef("zysqsj", "申请时间", "datetime"),
    FieldDef("zyshkssj", "作业开始时间", "datetime"),
    FieldDef("zyssjssj", "作业结束时间", "datetime"),
    FieldDef("zydd", "作业地点", "input"),
    FieldDef("zynr", "作业内容", "input"),
    FieldDef("dyjrdjxkydgl", "电源接入点及许可用电功率", "input"),
    FieldDef("gzdy", "工作电压", "input"),
    FieldDef("ydsbmcjedgl", "用电设备名称及额定功率", "input"),
    FieldDef("jhr", "监护人", "select_multi", source="peoples"),
    FieldDef("ydr", "用电人", "select_multi", source="peoples"),
    FieldDef("zyr", "作业人", "select_multi", source="peoples"),
    FieldDef("dgzh", "电工证号", "select_multi", required=False, source="peoplesZSs"),
    FieldDef("sfxylsydfx", "是否需要临时用电分析", "radio", radio_options=YES_NO),
    FieldDef("lsydfxr", "临时用电分析人", "select_multi", source="peoples", condition=("sfxylsydfx", "1")),
    FieldDef("zyfzr", "作业负责人", "select_multi", source="peoples"),
    FieldDef("yddwfzr", "用电单位负责人", "select_multi", source="peoples"),
    FieldDef("psddwfzr", "配送电单位负责人", "select_multi", source="peoples"),
    FieldDef("spbmfzr", "审批部门负责人", "select_multi", source="peoples"),
]

MBCD_FIELDS: list[FieldDef] = [
    FieldDef("zysskssj", "作业开始时间", "datetime"),
    FieldDef("zyssjssj", "作业结束时间", "datetime"),
    FieldDef("zydw", "作业单位", "input"),
    FieldDef("zylx", "作业类别", "select_single", source="zylxs"),
    FieldDef("zydd", "作业地点", "input"),
    FieldDef("sbgdmc", "设备、管道名称", "input"),
    FieldDef("jz", "介质", "input"),
    FieldDef("wd", "温度", "input"),
    FieldDef("yl", "压力", "input"),
    FieldDef("mbcz", "盲板-材质", "input"),
    FieldDef("mbgg", "盲板-规格", "input"),
    FieldDef("mbbh", "盲板-编号", "input"),
    FieldDef("mbwztbzr", "盲板位置图编制人", "select_multi", source="peoples"),
    FieldDef("mbbzsj", "盲板编制时间", "datetime"),
    FieldDef("jhr", "监护人", "select_multi", source="peoples"),
    FieldDef("zyr", "作业人", "select_multi", source="peoples"),
    FieldDef("sfxymbcdfx", "是否需要盲板抽堵分析", "radio", radio_options=YES_NO),
    FieldDef("mbcdfxr", "盲板抽堵分析人", "select_multi", source="peoples", condition=("sfxymbcdfx", "1")),
    FieldDef("zyfzr", "作业负责人", "select_multi", source="peoples"),
    FieldDef("spbmfzr", "审批部门负责人", "select_multi", source="peoples"),
]

DL_FIELDS: list[FieldDef] = [
    FieldDef("zysqsj", "申请时间", "datetime"),
    FieldDef("zyshkssj", "作业开始时间", "datetime"),
    FieldDef("zyssjssj", "作业结束时间", "datetime"),
    FieldDef("zydw", "作业单位", "input"),
    FieldDef("sjxgdw", "涉及相关单位(部门)", "input"),
    FieldDef("jhr", "监护人", "select_multi", source="peoples"),
    FieldDef("dldd", "断路地点", "input"),
    FieldDef("dlyy", "断路原因", "input"),
    FieldDef("sfxydlfx", "是否需要断路分析", "radio", radio_options=YES_NO),
    FieldDef("dlfxr", "断路分析人", "select_multi", source="peoples", condition=("sfxydlfx", "1")),
    FieldDef("zydwfzr", "作业负责人", "select_multi", source="peoples"),
    FieldDef("xfaqglbmfzr", "消防、安全管理部门负责人", "select_multi", source="peoples"),
    FieldDef("spbmfzr", "审批部门负责人", "select_multi", source="peoples"),
]

DT_FIELDS: list[FieldDef] = [
    FieldDef("zysqsj", "申请时间", "datetime"),
    FieldDef("zyshkssj", "作业开始时间", "datetime"),
    FieldDef("zyssjssj", "作业结束时间", "datetime"),
    FieldDef("zydw", "作业单位", "input"),
    FieldDef("zydd", "作业地点", "input"),
    FieldDef("zynr", "作业内容", "input"),
    FieldDef("jhr", "监护人", "select_multi", source="peoples"),
    FieldDef("sfxydtfx", "是否需要动土分析", "radio", radio_options=YES_NO),
    FieldDef("dtfxr", "动土分析人", "select_multi", source="peoples", condition=("sfxydtfx", "1")),
    FieldDef("zyfzr", "作业负责人", "select_multi", source="peoples"),
    FieldDef("sdqgysbxfaqbmfzrhq", "有关部门负责人会签确认", "select_multi", source="peoples"),
    FieldDef("spbmfzr", "审批部门负责人", "select_multi", source="peoples"),
]


# ============================================================
# 类型配置
# ============================================================

@dataclass
class TicketTypeConfig:
    """单个作业票类型的完整配置"""
    code: str           # 类型简码: DH, DL, DT, DZ, GC, LSYD, MBCD, SXKJ
    name: str           # 中文名
    type_value: str     # 后端类型值
    extra_fields: list[FieldDef] = field(default_factory=list)
    # API 路径前缀：DH 用 /app/ticket/，其他用 /app/ticketprocess/{code}/
    api_prefix: str = ""
    # 新增/编辑 API 路径
    add_path: str = ""
    edit_path: str = ""
    query_path: str = ""
    # 坐标字段名
    coord_field: str = ""
    # 分析 radio 字段默认值
    analysis_default: str = "0"
    # 详情页第二项（分析）的标题
    analysis_title: str = ""
    # zyjb（作业级别）字典 code，不同类型不同
    zyjb_dict: str = ""
    # 尾部字段（兼容 DH 的 qttsywbh 命名）
    tail_fields: list[FieldDef] = field(default_factory=list)


TICKET_TYPES: dict[str, TicketTypeConfig] = {
    "DH": TicketTypeConfig(
        code="DH", name="动火作业", type_value="3",
        extra_fields=DH_FIELDS,
        api_prefix="/jeecg-boot/app/ticket",
        add_path="/jeecg-boot/ticket/application/tbTicketApplication/addAPP",
        edit_path="/jeecg-boot/ticket/application/tbTicketApplication/edit",
        query_path="/jeecg-boot/app/ticket/queryPageById",
        coord_field="dhzb",
        analysis_default="1",
        analysis_title="动火分析",
        zyjb_dict="tb_zyp_dh_type",
        tail_fields=DH_TAIL_FIELDS,
    ),
    "SXKJ": TicketTypeConfig(
        code="SXKJ", name="受限空间作业", type_value="4",
        extra_fields=SXKJ_FIELDS,
        api_prefix="/jeecg-boot/app/ticketprocess/sxkj",
        add_path="/jeecg-boot/ticketprocess/sxkj/tbTicketSXKJApplication/addAPP",
        edit_path="/jeecg-boot/ticketprocess/sxkj/tbTicketSXKJApplication/edit",
        query_path="/jeecg-boot/app/ticketprocess/sxkj/queryPageById",
        coord_field="sxkjzb",
        analysis_default="1",
        analysis_title="受限空间分析",
    ),
    "GC": TicketTypeConfig(
        code="GC", name="高处作业", type_value="5",
        extra_fields=GC_FIELDS,
        api_prefix="/jeecg-boot/app/ticketprocess/gc",
        add_path="/jeecg-boot/ticketprocess/gc/tbTicketGCApplication/addAPP",
        edit_path="/jeecg-boot/ticketprocess/gc/tbTicketGCApplication/edit",
        query_path="/jeecg-boot/app/ticketprocess/gc/queryPageById",
        coord_field="zyzb",
        analysis_title="高处分析",
        zyjb_dict="tb_zyp_gc_type",
    ),
    "DZ": TicketTypeConfig(
        code="DZ", name="吊装作业", type_value="7",
        extra_fields=DZ_FIELDS,
        api_prefix="/jeecg-boot/app/ticketprocess/dz",
        add_path="/jeecg-boot/ticketprocess/dz/tbTicketDZApplication/addAPP",
        edit_path="/jeecg-boot/ticketprocess/dz/tbTicketDZApplication/edit",
        query_path="/jeecg-boot/app/ticketprocess/dz/queryPageById",
        coord_field="dzzb",
        analysis_title="吊装分析",
        zyjb_dict="tb_zyp_dz_type",
    ),
    "LSYD": TicketTypeConfig(
        code="LSYD", name="临时用电作业", type_value="8",
        extra_fields=LSYD_FIELDS,
        api_prefix="/jeecg-boot/app/ticketprocess/lsyd",
        add_path="/jeecg-boot/ticketprocess/lsyd/tbTicketApplicationLsydaq/addAPP",
        edit_path="/jeecg-boot/ticketprocess/lsyd/tbTicketApplicationLsydaq/edit",
        query_path="/jeecg-boot/app/ticketprocess/lsyd/queryPageById",
        coord_field="lsydzb",
        analysis_default="1",
        analysis_title="临时用电分析",
    ),
    "MBCD": TicketTypeConfig(
        code="MBCD", name="盲板抽堵作业", type_value="10",
        extra_fields=MBCD_FIELDS,
        api_prefix="/jeecg-boot/app/ticketprocess/mbcd",
        add_path="/jeecg-boot/ticketprocess/mbcd/tbTicketMBCDApplication/addAPP",
        edit_path="/jeecg-boot/ticketprocess/mbcd/tbTicketMBCDApplication/edit",
        query_path="/jeecg-boot/app/ticketprocess/mbcd/queryPageById",
        coord_field="mbcdzb",
        analysis_title="盲板抽堵分析",
    ),
    "DL": TicketTypeConfig(
        code="DL", name="断路作业", type_value="11",
        extra_fields=DL_FIELDS,
        api_prefix="/jeecg-boot/app/ticketprocess/dl",
        add_path="/jeecg-boot/ticketprocess/dl/tbTicketDLApplication/addAPP",
        edit_path="/jeecg-boot/ticketprocess/dl/tbTicketDLApplication/edit",
        query_path="/jeecg-boot/app/ticketprocess/dl/queryPageById",
        coord_field="dlzb",
        analysis_title="断路分析",
    ),
    "DT": TicketTypeConfig(
        code="DT", name="动土作业", type_value="12",
        extra_fields=DT_FIELDS,
        api_prefix="/jeecg-boot/app/ticketprocess/dt",
        add_path="/jeecg-boot/ticketprocess/dt/tbTicketDTApplication/addAPP",
        edit_path="/jeecg-boot/ticketprocess/dt/tbTicketDTApplication/edit",
        query_path="/jeecg-boot/app/ticketprocess/dt/queryPageById",
        coord_field="dtzb",
        analysis_title="动土分析",
    ),
}


def get_config_by_type_value(type_value: str) -> TicketTypeConfig | None:
    """根据后端类型值查找配置"""
    for cfg in TICKET_TYPES.values():
        if cfg.type_value == type_value:
            return cfg
    return None


def get_all_fields(config: TicketTypeConfig) -> list[FieldDef]:
    """获取某类型的全部字段列表（公共 + 特有 + 公共尾部）"""
    tail = config.tail_fields or COMMON_TAIL_FIELDS
    return COMMON_FIELDS + config.extra_fields + tail + COMMON_END_FIELDS


def get_detail_display_fields(config: TicketTypeConfig) -> list[FieldDef]:
    """获取详情页展示字段（比表单字段更全，含只读额外字段）。
    动火作业按 uniapp info.vue 的显示顺序重排，其他类型沿用表单顺序。"""
    base = get_all_fields(config)
    if config.code != "DH":
        return base

    # 动火详情按 uniapp 展示顺序重排
    pool: dict[str, FieldDef] = {f.key: f for f in base + DH_DETAIL_EXTRA_FIELDS}

    def _pop(key: str, label: str | None = None) -> FieldDef:
        f = pool.pop(key, None)
        if f is not None:
            return f
        return FieldDef(key=key, label=label or key, widget="input", required=False)

    ordered = [
        _pop("sqdw", "申请单位"),
        _pop("sqr", "申请人"),
        _pop("createTime", "作业申请时间"),
        _pop("zyzbh", "作业证编号"),
        _pop("zyjb", "作业级别"),
        _pop("zynr", "作业内容"),
        _pop("zydd", "动火地点及动火部位"),
        _pop("zyfs", "动火方式"),
        _pop("zyr", "动火人"),
        _pop("dhzsbh", "动火人证书编号"),
        _pop("sgdw", "作业单位"),
        _pop("zyfzr", "作业负责人"),
        _pop("sjdqttszy", "关联的其他特殊作业"),
        _pop("whbs", "风险辨识结果"),
        _pop("startTime", "动火作业实施开始时间"),
        _pop("dhEndTime", "动火作业实施结束时间"),
        _pop("time", "作业时间（s）"),
        _pop("sfxyaqjc", "是否需要动火分析"),
        _pop("aqjcr", "动火分析人"),
        _pop("qtaqcsbzr", "其他安全措施编制人"),
        _pop("aqjdr", "安全交底人"),
        _pop("jsjdr", "接受交底人"),
        _pop("jhr", "监护人"),
        _pop("jhrzsbh", "监护人证书编号"),
        _pop("szdw", "所在单位负责人"),
        _pop("aqglbm", "安全管理部门"),
        _pop("zyspr", "动火审批人"),
        _pop("dhqgwdbbcyp", "动火前，岗位顶班班长验票"),
        _pop("ysr", "验收人"),
    ]
    # 不显示的字段：摄像头、表单里的起止时间、涉及的其他特殊作业证编号
    _EXCLUDE = {"cameraId", "beginTime", "endTime", "sjdqttszyaqzyzbh", "qttsywbh"}
    ordered.extend(v for k, v in pool.items() if k not in _EXCLUDE)
    return ordered


# 详情页 6 宫格步骤定义
DETAIL_STEPS = [
    {"label": "基本信息", "icon": "info"},
    {"label": "安全分析", "icon": "detection"},
    {"label": "安全评估", "icon": "assessment"},
    {"label": "安全交底", "icon": "clarification"},
    {"label": "作业审批", "icon": "approval"},
    {"label": "作业验收", "icon": "acceptance"},
]
