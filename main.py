import MainCard
import Mainfunction

import json

from khl import *
from khl.card import CardMessage, Card, Module

# 获取机器人的token
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

bot = Bot(token=config['token'])
# 频道创建上限
channel_max = config['channel_max']
channel_month_max = config['channel_month_max']

# 获取时间戳
timestamp = config['timestamp']

# 给两个默认时间
time_date = 5
time_month = 1

# 在机器人删除时这里的值会进行变动
del_channel = 0

# 文件
channel_data = {}
channel_data_path = './id.json'

""" ---字典格式---
{
 '服务器id': {
             '分组': '分组id',
             '频道': {'频道id': '过期时间戳'},
             '频道月': {'频道id': '过期时间戳'}
            }
}
"""


# 启动程序时将会运行以下事件
@bot.task.add_date()
async def start():
    global channel_data
    channel_data = await Mainfunction.read_file(channel_data_path)
    await Mainfunction.data_upd(channel_data)
    await bot.client.update_listening_music('当前版本:1.4.3', '临时频道管理bot', "cloudmusic")


@bot.command(name='控制卡片')
async def help(m: Message):
    if m.channel_type.value == 'PERSON':  # 判断是否为私聊
        await m.ctx.channel.send('私聊无法使用bot')
        return
    await m.ctx.channel.send('当前指令已停用，请使用`。控制卡片`\n我已经将所有`/`换成了`。`')


@bot.command(regex='。控制卡片')
async def card(m: Message):
    if m.channel_type.value == 'PERSON':  # 判断是否为私聊
        await m.ctx.channel.send('私聊无法使用bot')
        return
    c1 = MainCard.CardList().card_date(time_date)
    cm = CardMessage(c1)
    await m.ctx.channel.send(cm)


# 自定义时间
@bot.command(regex='。指定时间 (.+)')
async def Time_Diy(m: Message, diy_time: int = 12):
    global time_date
    if m.channel_type.value == 'PERSON':  # 判断是否为私聊
        await m.ctx.channel.send('私聊无法使用bot')
        return
    elif diy_time >= 720:
        await m.ctx.channel.send('时间不能大于720个小时')
        return
    # 将当前输入时间存入字典
    time_date = diy_time
    await m.ctx.channel.send(f'已将创建时频道持续时间指定为:`{str(diy_time)}`', temp_target_id=m.author.id)


# 自定义时间
@bot.command(regex='。指定日期 (.+)')
async def Time_Month(m: Message, diy_time: int = 6):
    global time_month
    if m.channel_type.value == 'PERSON':  # 判断是否为私聊
        await m.ctx.channel.send('私聊无法使用bot')
        return
    elif diy_time >= 720:
        await m.ctx.channel.send('时间不能大于720个小时')
        return
    # 将当前输入时间存入字典
    time_month = diy_time
    await m.ctx.channel.send(f'已将创建时频道持续时间指定为:`{str(diy_time)}`', temp_target_id=m.author.id)


# 自定义分组位置
@bot.command(regex='。绑定分组 (.+)')
async def DIY1_channel(m: Message, channel_id=None):
    if m.channel_type.value == 'PERSON':  # 判断是否为私聊
        await m.ctx.channel.send('私聊无法使用bot')
        return
    elif not await Mainfunction.has_admin(m.author_id, m.ctx.guild.id):  # 向has_admin函数中放入用户id和服务器id 调用的时候记得加await
        await m.ctx.channel.send('抱歉，您不是管理', temp_target_id=m.author.id)
        return
    elif channel_id is None:
        await m.ctx.channel.send('请输入需要绑定的频道分组id', temp_target_id=m.author.id)
        return

    guild_id = m.ctx.guild.id
    await Mainfunction.revise_grouping_id(channel_data, guild_id, channel_id)
    await m.ctx.channel.send("修改成功")


# 删除指定频道
@bot.command(regex='。删除频道 (.+)')
async def del_channel(m: Message, channel_id):
    if m.channel_type.value == 'PERSON':  # 判断是否为私聊
        await m.ctx.channel.send('私聊无法使用bot')
        return
    elif not await Mainfunction.has_admin(m.author_id, m.ctx.guild.id):  # 向has_admin函数中放入用户id和服务器id 调用的时候记得加await
        await m.ctx.channel.send('抱歉，您不是管理', temp_target_id=m.author.id)
        return
    guild_id = m.ctx.guild.id
    target_id = m.target_id
    await Mainfunction.del_channel(channel_data, guild_id, channel_id, target_id)


# 当机器人被服务器踢出时则删除服务器在字典内的信息
@bot.on_event(EventTypes.SELF_EXITED_GUILD)
async def print_btn_value2(b: Bot, e: Event):
    guild_id = e.body['guild_id']
    if guild_id in channel_data:
        # 删除对应服务器信息，写入文件
        del channel_data[guild_id]
        await Mainfunction.write_file(channel_data_path, channel_data)


# 检测频道删除事件（目前不能获取删除频道分组事件）
@bot.on_event(EventTypes.DELETED_CHANNEL)
async def print_btn_value3(b: Bot, e: Event):
    global del_channel
    guild_id = e.target_id
    channel_id = e.body['id']
    if del_channel != 0:
        return
    if guild_id not in channel_data:
        return
    await Mainfunction.guild_del_channel(channel_data, guild_id, channel_id)


# 定时删除到期频道
@bot.task.add_interval(minutes=1)
async def delete_expired_channel():
    await Mainfunction.data_upd(channel_data)


# 按钮检测
@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def print_btn_value1(b: Bot, e: Event):
    global del_channel, time_date, time_month
    user_id = e.body['user_info']['id']  # 用户id
    target_id = e.body['target_id']  # 频道中为频道id 私聊中为用户id
    msg_id = e.body['msg_id']  # 原消息id
    # 获取按钮返回值
    val = e.body['value']
    # 获取服务器id
    guild_id = e.body['guild_id']

    # 一个发送消息函数，懒得重复写了
    async def not_root():
        await (await bot.client.fetch_public_channel(target_id)).send('抱歉，您不是管理', temp_target_id=user_id)

    # 创建频道
    if val == 'cj':
        await Mainfunction.create_channel(channel_data, guild_id, target_id, user_id, time_date, 0, 0)
    elif val == 'cj2':
        await Mainfunction.create_channel(channel_data, guild_id, target_id, user_id, time_date, 0, 1)
    elif val == 'month_cj':
        await Mainfunction.create_channel(channel_data, guild_id, target_id, user_id, time_month, 1, 0)
    elif val == 'month_cj2':
        await Mainfunction.create_channel(channel_data, guild_id, target_id, user_id, time_month, 1, 1)

    # 更改卡片样式
    elif val == 'hour':
        cm = CardMessage(MainCard.CardList().card_date(time_date))
        await Mainfunction.upd_msg(msg_id, cm)
    elif val == 'month':  # 更改卡片样式为 月
        cm = CardMessage(MainCard.CardList().card_month(time_month))
        await Mainfunction.upd_msg(msg_id, cm)
    elif val == 'root_card':  # 更改卡片样式为 管理员卡片
        if not await Mainfunction.has_admin(user_id, guild_id):
            await not_root()
            return
        await MainCard.upd_root_card(msg_id)

    # 更改频道人数上线
    elif val == 'channel':
        await Mainfunction.revise_number(guild_id, target_id, user_id)
        await (await bot.client.fetch_public_channel(target_id)).send('修改成功', temp_target_id=user_id)
    elif val == 'restore':
        await Mainfunction.revise_number(guild_id, target_id, user_id, 0)
        await (await bot.client.fetch_public_channel(target_id)).send('恢复成功', temp_target_id=user_id)

    # 取消分组绑定
    elif val == 'del_channel_diy':
        if not await Mainfunction.has_admin(user_id, guild_id):
            await not_root()
            return
        channel_data[guild_id]['频道分组id'] = 0
        await (await b.client.fetch_public_channel(target_id)).send("取消绑定成功")

    # 批量删除临时频道
    elif val == 'del_pid':
        if not await Mainfunction.has_admin(user_id, guild_id):  # 向has_admin函数中放入用户id和服务器id 调用的时候记得加await
            await not_root()
            return
        del_channel = 1
        await Mainfunction.del_all_channel(channel_data, guild_id, '频道')
        await Mainfunction.del_all_channel(channel_data, guild_id, '频道月')
        await (await bot.client.fetch_public_channel(target_id)).send('删除成功', temp_target_id=user_id)
        del_channel = 0
    elif val == 'del_hour':
        if not await Mainfunction.has_admin(user_id, guild_id):  # 向has_admin函数中放入用户id和服务器id 调用的时候记得加await
            await not_root()
            return
        del_channel = 1
        await Mainfunction.del_all_channel(channel_data, guild_id, '频道')
        await (await bot.client.fetch_public_channel(target_id)).send('删除成功', temp_target_id=user_id)
        del_channel = 0
    elif val == 'del_month':
        if not await Mainfunction.has_admin(user_id, guild_id):  # 向has_admin函数中放入用户id和服务器id 调用的时候记得加await
            await not_root()
            return
        del_channel = 1
        await Mainfunction.del_all_channel(channel_data, guild_id, '频道月')
        await (await bot.client.fetch_public_channel(target_id)).send('删除成功', temp_target_id=user_id)
        del_channel = 0

    # 踢出机器人
    elif val == 'out':
        if not await Mainfunction.has_admin(user_id, guild_id):  # 向has_admin函数中放入用户id和服务器id 调用的时候记得加await
            await not_root()
            return
        # 更新卡片
        await Mainfunction.upd_msg(msg_id, (await MainCard.out_verify()))
    elif val == 'out_yes':
        if not await Mainfunction.has_admin(user_id, guild_id):  # 向has_admin函数中放入用户id和服务器id 调用的时候记得加await
            await not_root()
            return
        # 更新卡片，防止踢出机器人后还有人使用
        await Mainfunction.upd_msg(e.body['msg_id'], CardMessage(
            Card(Module.Header('机器人已从当前服务器踢出'), Module.Section('如果失败请联系开发者'))))
        await Mainfunction.bot_out(channel_data, guild_id)

    # 更新卡片
    elif val == 'duration':
        cm = CardMessage(MainCard.CardList().card_date(time_date))
        await Mainfunction.upd_msg(msg_id, cm)
    elif val == 'month_duration':
        cm = CardMessage(MainCard.CardList().card_month(time_month))
        await Mainfunction.upd_msg(msg_id, cm)

    # 更改字典小时数
    elif val == 'time1':
        time_date = 1
        cm = CardMessage(MainCard.CardList().card_date(time_date))
        await Mainfunction.upd_msg(msg_id, cm)
    elif val == 'time2':
        time_date = 3
        cm = CardMessage(MainCard.CardList().card_date(time_date))
        await Mainfunction.upd_msg(msg_id, cm)
    elif val == 'time3':
        time_date = 5
        cm = CardMessage(MainCard.CardList().card_date(time_date))
        await Mainfunction.upd_msg(msg_id, cm)
    elif val == 'time4':
        time_date = 7
        cm = CardMessage(MainCard.CardList().card_date(time_date))
        await Mainfunction.upd_msg(msg_id, cm)

    elif val == 'month1':
        time_month = 1
        cm = CardMessage(MainCard.CardList().card_month(time_month))
        await Mainfunction.upd_msg(msg_id, cm)
    elif val == 'month2':
        time_month = 3
        cm = CardMessage(MainCard.CardList().card_month(time_month))
        await Mainfunction.upd_msg(msg_id, cm)
    elif val == 'month3':
        time_month = 5
        cm = CardMessage(MainCard.CardList().card_month(time_month))
        await Mainfunction.upd_msg(msg_id, cm)
    elif val == 'month4':
        time_month = 7
        cm = CardMessage(MainCard.CardList().card_month(time_month))
        await Mainfunction.upd_msg(msg_id, cm)


# 给某人的小惊喜
@bot.on_message()
async def card123(m: Message):
    user_id = m.author.id
    if user_id == '1966740491':
        await bot.client.add_reaction(m, emoji='🤡')


if __name__ == '__main__':
    bot.run()
