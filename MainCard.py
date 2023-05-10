import main
import Mainfunction

from khl.card import *


# 控制面板 管理员
async def upd_root_card(msg_id):
    await Mainfunction.upd_msg(msg_id, CardMessage(
        Card(
            Module.Header('管理员面板-按钮区'),
            Module.Divider(),
            Module.Section(Element.Text(content='一键**删除**分组内所有以(font)小时(font)[warning]为单位的临时频道', type=Types.Text.KMD),
                           Element.Button('一键删除', 'del_hour', theme=Types.Theme.DANGER)),
            # Module.Divider(),
            Module.Section(Element.Text(content='一键**删除**分组内所有以(font)月(font)[warning]为单位的临时频道', type=Types.Text.KMD),
                           Element.Button('一键删除', 'del_month', theme=Types.Theme.DANGER)),
            # Module.Divider(),
            Module.Section(Element.Text(content='一键**删除**分组内(font)所有(font)[warning]临时频道', type=Types.Text.KMD),
                           Element.Button('一键删除', 'del_pid', theme=Types.Theme.DANGER)),
            Module.Divider(),
            Module.Section(Element.Text(content='取消所绑定的分组，下次创建时将会生成新的分组', type=Types.Text.KMD),
                           Element.Button('取消绑定', 'del_channel_diy', theme=Types.Theme.DANGER)),
            Module.Divider(),
            Module.Section(Element.Text(content='自动踢出机器人', type=Types.Text.KMD),
                           Element.Button('一键踢出', 'out', theme=Types.Theme.DANGER))
            ),
        Card(
            Module.Header('管理员面板-指令区'),
            Module.Divider(),
            Module.Context(Element.Text(content='输入`。绑定分组 [分组频道id]`绑定临时频道所生成的分组，默认生成时会创建一个新分组', type=Types.Text.KMD)),
            Module.Context(Element.Text(content='输入`。删除频道 [频道id]`删除指定频道', type=Types.Text.KMD)),
            ),
        Card(
            Module.Section(Element.Text(content='返回控制卡片', type=Types.Text.KMD),
                           Element.Button('返回', 'hour', theme=Types.Theme.DANGER))
            )
        )
    )


# 踢出机器人卡片验证
async def out_verify():
    cm1 = CardMessage(Card(
        Module.Header('是否确认踢出机器人'),
        Module.ActionGroup(Element.Button('确认', 'out_yes', theme=Types.Theme.PRIMARY),
                           Element.Button('取消', 'duration', theme=Types.Theme.DANGER))))
    return cm1


class CardList:
    def __init__(self):
        self.c1 = Card()

    """卡片开头"""
    def card_head(self):
        self.c1.append(Module.Header('控制卡片-功能如果不可用请给机器人管理员'))
        self.c1.append(Module.Context(Element.Text(
            content='本机器人是由(met)1858431934(met)制作,[点击加入服务器](https://kook.top/NDXGBY),'
                    '觉得不错的可以给我一个[好评](https://www.botmarket.cn/bots?id=132)哦',
            type=Types.Text.KMD)))
        self.c1.append(Module.Divider())

    """卡片结尾"""
    def card_end(self):
        self.c1.append(Module.Section(Element.Text(content='更改你所在语音频道为当前频道人数上限(别人进不来)', type=Types.Text.KMD),
                                      Element.Button('更改上限', 'channel', theme=Types.Theme.DANGER)))
        self.c1.append(Module.Divider())
        self.c1.append(Module.Section(Element.Text(content='不限制频道人数', type=Types.Text.KMD),
                                      Element.Button('恢复上限', 'restore', theme=Types.Theme.DANGER)))
        self.c1.append(Module.Divider())
        self.c1.append(Module.ActionGroup(Element.Button('管理员面板', 'root_card', theme=Types.Theme.DANGER)))

    """卡片中间---小时部分"""
    def card_date(self, channel_time):
        self.card_head()  # 导入开头
        self.c1.append(Module.Section(Element.Text(content=f'当前临时频道持续时间为: `{str(channel_time)}`小时',
                                                   type=Types.Text.KMD)))
        self.c1.append(Module.ActionGroup(Element.Button('1小时', 'time1', theme=Types.Theme.PRIMARY),
                                          Element.Button('3小时', 'time2', theme=Types.Theme.PRIMARY),
                                          Element.Button('5小时', 'time3', theme=Types.Theme.PRIMARY),
                                          Element.Button('7小时', 'time4', theme=Types.Theme.PRIMARY)))
        self.c1.append(Module.ActionGroup(Element.Button('创建临时语音频道', 'cj', theme=Types.Theme.INFO),
                                          Element.Button('创建临时文字频道', 'cj2', theme=Types.Theme.INFO),
                                          Element.Button('更新频道持续时间', 'duration', theme=Types.Theme.WARNING)))
        self.c1.append(Module.Divider())
        self.c1.append(Module.ActionGroup(Element.Button('以月为单位', 'month', theme=Types.Theme.INFO)))
        self.c1.append(Module.Divider())
        self.c1.append(Module.Context(Element.Text(content='输入`。指定时间 [默认为12小时]`自定义临时频道时间', type=Types.Text.KMD)))
        self.c1.append(Module.Divider())
        self.card_end()  # 导入结尾
        return self.c1

    """卡片中间---月部分"""
    def card_month(self, channel_time_month):
        self.card_head()  # 导入开头
        self.c1.append(Module.Section(Element.Text(content=f'当前临时频道持续时间为: `{str(channel_time_month)}`个月'
                                                           f'({channel_time_month * 30}天)',
                                                   type=Types.Text.KMD)))
        self.c1.append(Module.ActionGroup(Element.Button('1个月', 'month1', theme=Types.Theme.PRIMARY),
                                          Element.Button('4个月', 'month2', theme=Types.Theme.PRIMARY),
                                          Element.Button('8个月', 'month3', theme=Types.Theme.PRIMARY),
                                          Element.Button('12个月', 'month4', theme=Types.Theme.PRIMARY)))
        self.c1.append(Module.ActionGroup(Element.Button('创建临时语音频道', 'month_cj', theme=Types.Theme.INFO),
                                          Element.Button('创建临时文字频道', 'month_cj2', theme=Types.Theme.INFO),
                                          Element.Button('更新频道持续时间', 'month_duration', theme=Types.Theme.WARNING)))
        self.c1.append(Module.Divider())
        self.c1.append(Module.ActionGroup(Element.Button('以小时为单位', 'hour', theme=Types.Theme.INFO)))
        self.c1.append(Module.Divider())
        self.c1.append(Module.Context(Element.Text(content='输入`。指定日期 [默认为6个月]`自定义临时频道时间', type=Types.Text.KMD)))
        self.c1.append(Module.Divider())
        self.card_end()  # 导入结尾
        return self.c1
