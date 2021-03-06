# -*- coding: utf-8 -*-

"""
Test patent parser.
"""

from cnsipo.patent_parser import PatentParser


parser = PatentParser("LocList.xml", "cn_univs.json", "hi_tech_ipcs")
U = parser.UNIVERSITY
I = parser.INDUSTRY
G = parser.GOVERNMENT
M = parser.MAINLAND
F = parser.FOREIGN


def test_state():
    addr_states = [
        ("北京市西城区西长安街86号", (M, "北京")),
        ("天津市王串场河北省水利所设计院", (M, "天津")),
        ("武汉市武昌珞珈山", (M, "湖北")),
        ("618000四川省德阳市华山北路东电医院", (M, "四川")),
        ("中海油（天津）管道工程技术有限公司", (M, "天津")),
        ("黑龙省哈尔滨市南岗西大直街144号", (None, None)),
        ("150001黑龙省哈尔滨市南岗西大直街144号", (M, "黑龙江")),
        ("中国香港沙田大围悠安路一号3楼", ("香港", None)),
        ("中国澳门南湾大马路401至415号中国法律大厦15楼B座", ("澳门", None)),
        ("台湾省新竹科学工业园区", ("台湾", None)),
        ("中国台湾新竹科学工业园区", ("台湾", None)),
        ("美国康涅狄格州", ("美国", None)),
        ("康涅狄格州", ("美国", None)),
        ("中国邮电工业总公司科技处(北京市西长安街13号)", (M, "北京")),
        ("清华大学东区16栋5单元501", (M, "北京")),
        ("航天部上海航天局八○六研究所(上海市华山路1539号)", (M, "上海")),
        ("大阪府大阪市东区道修町4丁目3番地", ("日本", None)),
        # FIXME: should be (mainland, hebei)
        ("水利电力部华北电管局保定电力技工学校", (M, None)),
        # FIXME: should be ("格鲁吉亚第比利斯", None)
        ("格鲁吉亚第比利斯", (None, None)),
    ]
    for address, state in addr_states:
        assert parser.parse_address(address) == state


def test_applicant():
    applicant_types = [
        ("江南大学; 恒丰(镇江)食品有限公司", None,
         [(I, "江苏"), (U, "江苏")]),
        # ("N·V·菲利浦斯光灯制造厂", [(I, None)]),
        ("华中科技大学; 云南电力试验研究院有限公司电力研究院", None,
         [(I, '云南'), (U, '湖北')]),
        ("广东电网公司电力调度控制中心; 华南理工大学", None,
         [(I, '广东'), (U, '广东')]),
        ("中山大学附属肿瘤医院; 广州医学院; 北京索奥生物医药科技有限公司", None,
         [(G, '广东'), (I, '北京'), (U, '广东')]),
        ("海普拉精密工业(株)", "韩国全罗北道", [(I, F)]),
        ("张华; 王公司", None, []),
        ("李小明; 马里兰大学", None, [(U, F)]),
        ("李小明; 马-里兰大学", None, [(U, F)]),
        ("中国石油天然气集团公司; 中国石油大学(北京)", "100724北京市西城区六铺炕街六号",
            [(I, '北京'), (U, '北京')]),
        ("华为技术有限公司; 北京邮电大学", "518129广东省深圳市龙岗区坂田华为总部办公楼",
            [(I, '广东'), (U, '北京')]),
        ("清华大学; 鸿富锦精密工业(深圳)有限公司", "100084北京市富士康纳米科技研究中心",
            [(I, '广东'), (U, '北京')]),
        ("华中工学院; 岳阳制冷设备总厂", "湖北省武汉市",
            [(I, '湖南'), (U, '湖北')]),
        ("山西科泰微技术有限公司; 华北工学院", "030012山西省太原市南内环街",
            [(I, '山西'), (U, '山西')]),
        # both 喀麦隆 and 赞比亚 have “西北” city！
        ("西北给排水技术开发公司; 南洋国际技术公司", "甘肃省兰州市定西路环保研究所内",
            [(I, '甘肃'), (I, '甘肃')]),
        # two traps: 萨尔瓦多 has "中南" city; 中南工业大学 changed name
        ("中南工业大学; 平桂矿务局珊瑚锡矿", "湖南省长沙左家垅",
            [(I, '湖南'), (U, '湖南')]),
        ("铁道部运输局; 北京电信息技术公司; 北京大学; 天津通信有限公司; 上海思科公司;"
            " 北京科技公司; 泉州电子设备有限公司; 上海通讯股份有限公司",
            "北京市海淀区复兴路201号",
            [(G, "北京"), (I, "上海"), (I, "北京"), (I, "天津"),
             (I, "福建"), (U, "北京")])
    ]
    for applicant, address, types in applicant_types:
        assert parser.parse_applicants(applicant, address)[0] == types


def test_ipc():
    int_cls = [
        ("", (False, False)),
        ("C12R1/19(2006.01)N", (False, True)),
        ("C40B40/06(2006.01)I", (True, False)),
        ("C12R1/19(2006.01)N; C40B40/06(2006.01)I",
         (True, True)),
    ]
    for int_cl, result in int_cls:
        assert parser.parse_int_cl(int_cl) == result
