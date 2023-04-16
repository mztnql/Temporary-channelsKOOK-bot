"""
机器人部署端注意事项

机器人状态版本需要注意更改
注意生成频道部分的时间戳，要从60改为3600
"""
import json
import os
import time
import copy
import logging
import requests
# 本地文件
import ui
# 以下模块需要pip
from typing import Union
import aiofiles
from khl import *
from khl.card import *

# 获取机器人的token
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

bot = Bot(token=config['token'])

# 频道创建上限
num = config['num']
num_month = config['num_month']

# 临时频道持续时间
timestamp = config['timestamp']

# 文件路径
path_id = './id.json'

# 数据字典
user_date = {}
# 格式{'3973624984431345'(服务器id): {'频道分组id': '3716939028710478', '频道id': {'6860917344933129': 过期时间戳}}}

# 按小时的时间字典 默认5
time_date = {'time': 5}
# 按月的时间字典
time_month = {'time': 1}

logging.basicConfig(
    filename='log.txt',
    level=logging.WARNING,  # 设置日志级别为WARNING
    format='[%(asctime)s] - [%(levelname)s] - [%(message)s]')


# 读取文件
async def read_file(path) -> dict:
    if not os.path.exists(path):
        async with aiofiles.open(path, 'w', encoding='utf-8') as fa:
            await fa.write(json.dumps({}))
    async with aiofiles.open(path, 'r', encoding='utf-8') as r:
        return json.loads(await r.read())


# 写入文件
async def write_file(path, value):
    async with aiofiles.open(path, 'w', encoding='utf-8') as x:
        await x.write(json.dumps(value, ensure_ascii=False))


# 发送消息接口，指定用户，临时消息
async def msg(target, mess, user_id):
    await bot.client.gate.request('POST', 'message/create',
                                  data={'target_id': target, 'content': mess, 'temp_target_id': user_id})


# 创建频道分组接口
async def create_category2(guild_id, name):
    return \
        (await bot.client.gate.request('POST', 'channel/create',
                                       data={'guild_id': guild_id, 'name': name, 'is_category': 1}))['id']


# 更改频道人数上限-0为不限人数-number最大为99人
async def create_category3(channel_id, number):
    return (await bot.client.gate.request('POST', 'channel/update',
                                          data={'channel_id': channel_id, 'limit_amount': number}))


# 更改频道语音质量
async def create_category4(channel_id, number):
    return (await bot.client.gate.request('POST', 'channel/update',
                                          data={'channel_id': channel_id, 'voice_quality': number}))


# 机器人离开服务器
async def user_del(guild_id):
    # 输出日志
    logging.warning(f'机器人退出了服务器:{guild_id}')
    return await bot.client.gate.request('POST', 'guild/leave', data={'guild_id': guild_id})


# 启动程序时将会运行以下事件
@bot.task.add_date()
async def start():
    # 声明字典为全局变量
    global user_date
    # 将文件内容写入字典
    user_date = await read_file(path_id)

    # 复制一份字典
    user_date_copy = copy.deepcopy(user_date)

    for guild_id, value in user_date_copy.items():
        if '频道月id' not in user_date_copy[guild_id].items():
            user_date[guild_id]['频道月id'] = {}

    # 检测用户是否手动删除了频道
    for guild_id in user_date_copy:
        await guild_list(guild_id)

    # 判断频道是否过了时间
    # 遍历字典内的键和值，分别为channel_id和value
    for channel_id, value in user_date_copy.items():
        # 遍历value里的 频道id 的键和值
        for channels, expired_time in value['频道id'].items():
            # 判断频道id里的过期时间戳是否小于当前时间戳
            if expired_time < time.time():
                # 当前时间戳大于过期时间戳后，删除过期频道
                await bot.client.delete_channel(channels)
                # 删除字典内过期频道及它的时间戳
                del user_date[channel_id]['频道id'][channels]

    # 判断字典和复制的字典是否有出入
    if user_date != user_date_copy:
        # 我们对比遍历后的guild_setting有没有变更，变更的话就往文件里存一份
        await write_file(path_id, user_date)

    await bot.client.update_listening_music('当前版本:1.4.3', '临时频道管理bot', "cloudmusic")
    # 输出日志
    logging.warning(f'bot成功启动')


# 获取一个语音频道里所有用户id，并修改人数上限
async def user_all(channel_id):
    # 获取所有用户id
    user_id = await bot.client.gate.request('GET', 'channel/user-list', params={'channel_id': channel_id})
    us_id = []
    # 向列表里储存所有用户id
    for us_er in user_id:
        us_id.append(us_er['id'])
    a = len(us_id)
    # 更改频道人数上限
    await create_category3(channel_id, a)


# 根据服务器id和用户id获取所在语音频道id
async def guild_user(guild_id, user_id, text, num_all):
    channel_id_1 = await bot.client.gate.request('GET', 'channel-user/get-joined-channel',
                                                 params={'guild_id': guild_id, 'user_id': user_id})
    # 储存频道id字典
    channel_id = []
    # 将接口返回值里的频道id储存进列表
    for chan_nel in channel_id_1['items']:
        channel_id.append(chan_nel)
    # 判断列表内数据是否为空
    if not channel_id:
        # 为空的话什么也不干
        await msg(text, '您不在语音内', user_id)
        return
    else:
        if num_all == 0:
            # 获取语音频道里所有用户id
            await create_category3(channel_id_1['items'][0]['id'], 0)
            # 输出日志
            logging.warning(f'频道:{channel_id}修改了人数上限')
        else:
            # 获取语音频道里所有用户id
            await user_all(channel_id_1['items'][0]['id'])
            # 输出日志
            logging.warning(f'频道:{channel_id}恢复了人数上限')
        await msg(text, '修改成功', user_id)


# 获取服务器信息接口,检测用户是否删除了频道
async def guild_list(guild_id):
    # 声明全局，复制字典
    global user_date
    try:
        guild_temp = await bot.client.gate.request('GET', 'channel/list', params={'guild_id': guild_id})
    except:
        del user_date[guild_id]
        await write_file(path_id, user_date)
        return

    # 创建一个储存服务器频道id的列表
    temp = []
    # 创建一个储存字典服务器频道id的列表
    channel_id = []

    # 复制一份字典
    user_date_copy = copy.deepcopy(user_date)

    # 获取当前服务器所有频道id
    for channel_list in guild_temp['items']:
        # 把服务器频道id都写入到列表里
        temp.append(channel_list['id'])

    # 获取字典里频道id
    for channel_temp, expired_time in user_date_copy[guild_id]['频道id'].items():
        channel_id.append(channel_temp)
    for channel_temp, expired_time in user_date_copy[guild_id]['频道月id'].items():
        channel_id.append(channel_temp)

    # 遍历频道id，检测字典内是否有被用户删除的频道
    for x in channel_id:
        if x not in temp:
            del user_date[guild_id]['频道id'][x]

    # 判断文件与字典是否有出入
    if user_date_copy != user_date:
        await write_file(path_id, user_date)

    # 遍历频道id，检测字典内是否有被用户删除的分组
    channel_grouping_id = user_date_copy[guild_id]['频道分组id']
    if channel_grouping_id not in temp:
        user_date[guild_id]['频道分组id'] = 0
        await write_file(path_id, user_date)


# 检测用户是否为管理-1
async def has_admin(user_id, guild_id):
    id_guild = await bot.client.fetch_guild(guild_id)
    user_roles = (await id_guild.fetch_user(user_id)).roles
    guild_roles = await (await bot.client.fetch_guild(guild_id)).fetch_roles()
    for i in guild_roles:  # 遍历服务器身分组
        if i.id in user_roles and i.has_permission(0):  # 查看当前遍历到的身分组是否在用户身分组内且是否有管理员权限
            return True
    if user_id == id_guild.master_id:  # 由于腐竹可能没给自己上身分组，但是依旧拥有管理员权限
        return True
    return False


# 更新消息
async def upd_card(msg_id: str, content, target_id: str = None,
                   channel_type: Union[ChannelPrivacyTypes, str] = 'public', b=bot):
    content = json.dumps(content)
    data = {'msg_id': msg_id, 'content': content}
    if target_id is not None:
        data['temp_target_id'] = target_id
    if channel_type == 'public' or channel_type == ChannelPrivacyTypes.GROUP:
        result = await b.client.gate.request('POST', 'message/update', data=data)
    else:
        result = await b.client.gate.request('POST', 'direct-message/update', data=data)
    return result


# 删除频道
async def DEL_channel(guild_id, target_id, user_id, del_num):
    # 复制一份字典，防止遍历时报错
    user_date_copy = copy.deepcopy(user_date)
    # 判断服务器是否在字典里
    if guild_id in user_date_copy:
        if del_num == 1:
            for channel_id in user_date_copy[guild_id]['频道id']:
                await bot.client.delete_channel(channel_id)
            # 直接覆写
            user_date_copy[guild_id]['频道id'] = {}
        else:
            for channel_id in user_date_copy[guild_id]['频道月id']:
                await bot.client.delete_channel(channel_id)
            user_date_copy[guild_id]['频道月id'] = {}

        # 将字典存入文件
        await write_file(path_id, user_date)
    # 如果不在则提示
    else:
        await msg(target_id, '抱歉，未查询到您服务器临时频道信息', user_id)


# 卡片
@bot.command(name='控制卡片')
async def card(m: Message):
    channel_type = m.channel_type.value
    if channel_type == 'PERSON':  # 判断是否为私聊
        logging.warning(f'用户:{m.author.username}想要私信使用bot')  # 输出日志
        return
    logging.warning(f'-----发送了一次消息-----')  # 输出日志

    a = time_date['time']
    await m.ctx.channel.send(
        CardMessage(
            Card(
                Module.Header('控制卡片-功能如果不可用请给机器人管理员'),
                Module.Context(Element.Text(
                    content='本机器人是由(met)1858431934(met)制作,[点击加入服务器](https://kook.top/NDXGBY),觉得不错的可以给我一个[好评](https://www.botmarket.cn/bots?id=132)哦',
                    type=Types.Text.KMD)),
                Module.Divider(),
                Module.Section(Element.Text(content=f'当前临时频道持续时间为: `{str(a)}`小时', type=Types.Text.KMD)),
                Module.ActionGroup(Element.Button('1小时', 'time1', theme=Types.Theme.PRIMARY),
                                   Element.Button('3小时', 'time2', theme=Types.Theme.PRIMARY),
                                   Element.Button('5小时', 'time3', theme=Types.Theme.PRIMARY),
                                   Element.Button('7小时', 'time4', theme=Types.Theme.PRIMARY)),
                Module.ActionGroup(Element.Button('创建临时语音频道', 'cj', theme=Types.Theme.INFO),
                                   Element.Button('创建临时文字频道', 'cj2', theme=Types.Theme.INFO),
                                   Element.Button('更新频道持续时间', 'duration', theme=Types.Theme.WARNING)),
                Module.Divider(),
                Module.ActionGroup(Element.Button('以月为单位', 'month', theme=Types.Theme.INFO)),
                Module.Divider(),
                Module.Context(
                    Element.Text(content='输入`/指定时间 [默认为12小时]`自定义临时频道时间', type=Types.Text.KMD)),
                Module.Divider(),

                # Module.Section('设置当前频道语音质量'),
                # Module.ActionGroup(Element.Button('流畅', 'ok+', theme=Types.Theme.PRIMARY),
                # Element.Button('正常', 'ok++', theme=Types.Theme.PRIMARY),
                # Element.Button('高质量', 'ok+++', theme=Types.Theme.PRIMARY)),
                # Module.Divider(),

                Module.Section(
                    Element.Text(content='更改你所在语音频道为当前频道人数上限(别人进不来)', type=Types.Text.KMD),
                    Element.Button('更改上限', 'channel', theme=Types.Theme.DANGER)),
                Module.Divider(),
                Module.Section(
                    Element.Text(content='不限制频道人数', type=Types.Text.KMD),
                    Element.Button('恢复上限', 'restore', theme=Types.Theme.DANGER)),
                Module.Divider(),
                Module.ActionGroup(Element.Button('管理员面板', 'root_card', theme=Types.Theme.DANGER)),
            )))


# 自定义时间
@bot.command(name='指定时间')
async def Time_Diy(m: Message, diy_time: int = 12):
    channel_type = m.channel_type.value
    if channel_type == 'PERSON':  # 判断是否为私聊
        logging.warning(f'用户:{m.author.username}想要私信使用bot')  # 输出日志
        return
    elif diy_time >= 720:
        await m.ctx.channel.send('时间不能大于720个小时')
        return
    # 将当前输入时间存入字典
    time_date['time'] = diy_time
    await m.ctx.channel.send(f'已将创建时频道持续时间指定为:`{str(diy_time)}`', temp_target_id=m.author.id)
    # 输出日志
    logging.warning(f'用户:{m.author.username}在服务器:{m.ctx.guild.id}将时间指定为{str(diy_time)}小时')


# 自定义时间
@bot.command(name='指定日期')
async def Time_Month(m: Message, diy_time: int = 6):
    channel_type = m.channel_type.value
    if channel_type == 'PERSON':  # 判断是否为私聊
        logging.warning(f'用户:{m.author.username}想要私信使用bot')  # 输出日志
        return
    elif diy_time >= 720:
        await m.ctx.channel.send('时间不能大于12个月')
        return
    # 将当前输入时间存入字典
    time_month['time'] = diy_time
    await m.ctx.channel.send(f'已将创建时频道持续时间指定为:`{str(diy_time)}个月`', temp_target_id=m.author.id)
    # 输出日志
    logging.warning(f'用户:{m.author.username}在服务器:{m.ctx.guild.id}将时间指定为{str(diy_time)}个月')


# 自定义分组位置
@bot.command(name='绑定分组')
async def DIY1_channel(m: Message, channel_id: str = 0):
    channel_type = m.channel_type.value
    if channel_type == 'PERSON':  # 判断是否为私聊
        logging.warning(f'用户:{m.author.username}想要私信使用bot')  # 输出日志
        return
    elif not await has_admin(m.author_id, m.ctx.guild.id):  # 向has_admin函数中放入用户id和服务器id 调用的时候记得加await
        await m.ctx.channel.send('抱歉，您不是管理', temp_target_id=m.author.id)
        return
    elif channel_id == 0:
        await m.ctx.channel.send('请输入需要绑定的频道分组id', temp_target_id=m.author.id)
        return

    guild_id = m.ctx.guild.id
    # 如果字典里没有服务器id那么就频道分组肯定也没有
    if guild_id not in user_date:
        # 将频道分组id写入字典，后续再写入文件
        user_date[guild_id] = {'频道分组id': str(channel_id), '频道id': {}, '频道月id': {}}
        await write_file(path_id, user_date)
    else:
        user_date[guild_id]['频道分组id'] = channel_id
        await write_file(path_id, user_date)
    await m.ctx.channel.send("修改成功")


# 删除指定频道
@bot.command(name='删除频道')
async def del_channel(m: Message, channel_id='Not'):
    channel_type = m.channel_type.value
    if channel_type == 'PERSON':  # 判断是否为私聊
        logging.warning(f'用户:{m.author.username}想要私信使用bot')  # 输出日志
        return
    if not await has_admin(m.author_id, m.ctx.guild.id):  # 向has_admin函数中放入用户id和服务器id 调用的时候记得加await
        await m.ctx.channel.send('抱歉，您不是管理', temp_target_id=m.author.id)
        return

    if channel_id == 'Not':
        await m.ctx.channel.send('请输入频道id', temp_target_id=m.author.id)

    else:
        guild_id = m.ctx.guild.id

        # 检测服务器是否在字典内
        if guild_id not in user_date:
            # 不在字典里直接删除
            await bot.client.delete_channel(channel_id)
            await m.ctx.channel.send('删除成功', temp_target_id=m.author.id)

        elif guild_id in user_date:
            # 检测是否为临时频道分组，如果是删除频道同时删除字典里内容
            if channel_id in user_date[guild_id]['频道分组id']:
                # 删除分组
                await bot.client.delete_channel(channel_id)
                # 删除字典里有关此服务器所有数据
                user_date[guild_id]['频道分组id'] = 0
                # 存入文件
                await write_file(path_id, user_date)
                await m.ctx.channel.send('删除成功', temp_target_id=m.author.id)

            # 检测是否为临时频道，如果是则删除
            elif channel_id in user_date[guild_id]['频道id']:
                # 删除频道
                await bot.client.delete_channel(channel_id)
                # 删除字典内容
                del user_date[guild_id]['频道id'][channel_id]
                # 存入文件
                await write_file(path_id, user_date)
                await m.ctx.channel.send('删除成功', temp_target_id=m.author.id)
            elif channel_id in user_date[guild_id]['频道月id']:
                # 删除频道
                await bot.client.delete_channel(channel_id)
                # 删除字典内容
                del user_date[guild_id]['频道月id'][channel_id]
                # 存入文件
                await write_file(path_id, user_date)
                await m.ctx.channel.send('删除成功', temp_target_id=m.author.id)

            # 如果不是临时频道则直接删除
            else:
                # 删除对应频道
                await bot.client.delete_channel(channel_id)
                await m.ctx.channel.send('删除成功', temp_target_id=m.author.id)

        else:
            await m.ctx.channel.send('删除失败，请联系机器制作人')
            # 输出日志
            logging.error('!' * 5 + '机器人删除频道出问题' + '!' * 5)


# 运行创建频道，生成时间戳
async def create(guild_id, target_id, user_id, a, a_time):
    if a_time == 1:  # 按小时创建频道
        b = time_date["time"]  # 获取字典内时间
        if a == 1:
            name = f'临时语音频道   {b}小时'
        else:
            name = f'临时文字频道   {b}小时'
        now_time = time.time()  # 获取当前时间戳
        expire_time = now_time + b * int(timestamp)  # 计算出b小时后的时间戳
    else:  # 按月创建频道
        b = time_month["time"]  # 获取字典内时间
        if a == 1:
            name = f'临时语音频道   {b}个月'
        else:
            name = f'临时文字频道   {b}个月'
        now_time = time.time()  # 获取当前时间戳
        expire_time = now_time + b * 2592000  # 计算出b小时后的时间戳

    # 如果字典里没有服务器id那么就频道分组肯定也没有
    if guild_id not in user_date:
        # 创建频道分组并且获得分组id
        grouping = await create_category2(guild_id, '临时频道分组')
        # 将频道分组id写入字典，后续再写入文件
        user_date[guild_id] = {'频道分组id': grouping, '频道id': {}, '频道月id': {}}
        await write_file(path_id, user_date)

    # 检测用户是否手动删除了频道---这里用于判断分组是否被删除，后续分组删除事件修复将被删除
    await guild_list(guild_id)

    if user_date[guild_id]['频道分组id'] == 0:  # 当没有频道分组时 频道分组id的值会是0，所以需要重新创建一个
        grouping = await create_category2(guild_id, '临时频道分组')
        # 将频道分组id写入字典，后续再写入文件
        user_date[guild_id]['频道分组id'] = grouping
        await write_file(path_id, user_date)

    if '频道月id' not in user_date[guild_id]:  # 为后面额外添加数据做准备
        user_date[guild_id]['频道月id'] = {}

    # 获取当前服务器创建了多少个频道
    num1 = len(user_date[guild_id]['频道id'])
    num2 = len(user_date[guild_id]['频道月id'])
    # 以数字格式来判断
    if num1 < int(num) or num2 < int(num_month):
        # 创建频道
        if a == 1:
            # 创建语音频道
            pid_id = (await bot.client.create_voice_channel(f'{name}', guild_id, user_date[guild_id]['频道分组id'])).id
            await msg(target_id, '临时语音频道创建成功', user_id)
            if a_time == 1:
                # 将频道id写入字典，并保存进文件
                user_date[guild_id]['频道id'][pid_id] = expire_time
                await write_file(path_id, user_date)
            else:
                # 将频道id写入字典，并保存进文件
                user_date[guild_id]['频道月id'][pid_id] = expire_time
                await write_file(path_id, user_date)
            # 输出日志
            logging.warning(f'服务器:{guild_id}创建了一个临时语音频道')

        # 创建文字频道
        elif a == 2:
            # 创建文字频道
            pid_id = (
                await bot.client.create_text_channel(guild_id, f'{name}小时', user_date[guild_id]['频道分组id'])).id
            await msg(target_id, '临时文字频道创建成功', user_id)
            if a_time == 1:
                # 将频道id写入字典，并保存进文件
                user_date[guild_id]['频道id'][pid_id] = expire_time
                await write_file(path_id, user_date)
            else:
                # 将频道id写入字典，并保存进文件
                user_date[guild_id]['频道月id'][pid_id] = expire_time
                await write_file(path_id, user_date)
            # 输出日志
            logging.warning(f'服务器:{guild_id}创建了一个临时文字频道')

    else:
        await msg(target_id, '当前服务器频道临时数量已达上限', user_id)
        # 输出日志
        logging.warning(f'服务器:{guild_id}临时频道数量达到了上限')


# 定时删除到期频道
@bot.task.add_interval(minutes=1)
# 使用 @bot.task.add_interval 来创建一个定时任务 minutes=1 表示每分钟执行一次
async def delete_expired_channel():
    global user_date
    # 首先我们用 copy.deepcopy 将 guild_setting 复制出来一份，因为在遍历字典时修改字典的内容会报错
    user_date_copy = copy.deepcopy(user_date)

    # 检测用户是否手动删除了频道
    for guild_id in user_date_copy:
            await guild_list(guild_id)

    # 遍历字典内的键和值，分别为channel_id和value
    for channel_id, value in user_date_copy.items():
        # 遍历value里的 频道id 的键和值
        for channels, expired_time in value['频道id'].items():
            # 判断频道id里的过期时间戳是否小于当前时间戳
            if expired_time < time.time():
                # 当前时间戳大于过期时间戳后，删除过期频道
                await bot.client.delete_channel(channels)
                # 删除字典内过期频道及它的时间戳
                del user_date[channel_id]['频道id'][channels]

        for channels, expired_time in value['频道月id'].items():
            # 判断频道id里的过期时间戳是否小于当前时间戳
            if expired_time < time.time():
                # 当前时间戳大于过期时间戳后，删除过期频道
                await bot.client.delete_channel(channels)
                # 删除字典内过期频道及它的时间戳
                del user_date[channel_id]['频道月id'][channels]

    # 判断字典和复制的字典是否有出入
    if user_date != user_date_copy:
        # 我们对比遍历后的guild_setting有没有变更，变更的话就往文件里存一份
        await write_file(path_id, user_date)


# 当机器人被服务器踢出时则删除服务器在字典内的信息
@bot.on_event(EventTypes.SELF_EXITED_GUILD)
async def print_btn_value2(b: Bot, e: Event):
    guild_id = e.body['guild_id']

    if guild_id in user_date:
        # 删除对应服务器信息，写入文件
        del user_date[guild_id]
        await write_file(path_id, user_date)
        # 输出日志
        logging.warning(f'服务器:{guild_id}踢出了机器人')
    else:
        pass


# 检测频道删除事件（目前不能获取删除频道分组事件）
@bot.on_event(EventTypes.DELETED_CHANNEL)
async def print_btn_value3(b: Bot, e: Event):
    channel_id = e.body['id']
    guild_id = e.target_id
    # 复制一份字典
    user_date_copy = copy.deepcopy(user_date)

    # 判断此服务器是否有存档
    if guild_id not in user_date_copy:
        return

    pid_id = user_date_copy[guild_id]['频道分组id']
    # 如果删除的是频道分组
    if channel_id == pid_id:
        user_date[guild_id]['频道分组id'] = 0
        await write_file(path_id, user_date)
        # 输出日志
        logging.warning(f'服务器:{guild_id}删除了频道分组')
        return

    # 如果删除的是频道
    elif channel_id in user_date_copy[guild_id]['频道id']:
        del user_date[guild_id]['频道id'][channel_id]
        await write_file(path_id, user_date)
        # 输出日志
        logging.warning(f'服务器:{guild_id}删除了一个临时频道')
        return
    elif channel_id in user_date_copy[guild_id]['频道月id']:
        del user_date[guild_id]['频道月id'][channel_id]
        await write_file(path_id, user_date)
        # 输出日志
        logging.warning(f'服务器:{guild_id}删除了一个临时频道')
        return


# 按钮检测
@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def print_btn_value1(b: Bot, e: Event):
    user_id = e.body['user_info']['id']  # 用户id
    target_id = e.body['target_id']  # 频道中为频道id 私聊中为用户id
    msg_id = e.body['msg_id']  # 原消息id
    # 获取按钮返回值
    val = e.body['value']
    # 获取服务器id
    guild_id = e.body['guild_id']

    # 判断按钮是什么
    # 获取创建的频道按钮
    if val == 'cj':
        await create(guild_id, target_id, user_id, 1, 1)
    elif val == 'cj2':
        await create(guild_id, target_id, user_id, 2, 1)
    elif val == 'month_cj':
        await create(guild_id, target_id, user_id, 1, 2)
    elif val == 'month_cj2':
        await create(guild_id, target_id, user_id, 2, 2)

    # 更改卡片样式为 小时
    elif val == 'hour':
        a = time_date['time']  # 获取字典内当前时间
        await ui.upd_card_hour(msg_id, a)
    elif val == 'month':  # 更改卡片样式为 月
        a = time_month['time']
        await ui.upd_card_month(msg_id, a)
    elif val == 'root_card':  # 更改卡片样式为 管理员卡片
        if not await has_admin(user_id, guild_id):
            await msg(target_id, '抱歉，您不是管理', user_id)
            return
        await ui.upd_root_card(msg_id)

    # 更改频道人数上线为当前人数
    elif val == 'channel':
        await guild_user(guild_id, user_id, target_id, 1)
    # 恢复频道id人数上限为不限制
    elif val == 'restore':
        await guild_user(guild_id, user_id, target_id, 0)

    # 取消分组绑定
    elif val == 'del_channel_diy':
        if not await has_admin(user_id, guild_id):  # 向has_admin函数中放入用户id和服务器id 调用的时候记得加await
            await msg(target_id, '抱歉，您不是管理', user_id)
            return

        user_date[guild_id]['频道分组id'] = 0
        await (await b.client.fetch_public_channel(target_id)).send("取消绑定成功")

    # 一键删除所有临时频道
    elif val == 'del_pid':
        if not await has_admin(user_id, guild_id):  # 向has_admin函数中放入用户id和服务器id 调用的时候记得加await
            await msg(target_id, '抱歉，您不是管理', user_id)
            return
        await DEL_channel(guild_id, target_id, user_id, 1)
        await DEL_channel(guild_id, target_id, user_id, 2)
        await msg(target_id, '删除成功', user_id)
        # 输出日志
        logging.warning(f'用户:{user_id}删除了所有临时频道')
    elif val == 'del_hour':
        if not await has_admin(user_id, guild_id):  # 向has_admin函数中放入用户id和服务器id 调用的时候记得加await
            await msg(target_id, '抱歉，您不是管理', user_id)
            return
        await DEL_channel(guild_id, target_id, user_id, 1)
        await msg(target_id, '删除成功', user_id)
        # 输出日志
        logging.warning(f'用户:{user_id}删除了所有小时临时频道')
    elif val == 'del_month':
        if not await has_admin(user_id, guild_id):  # 向has_admin函数中放入用户id和服务器id 调用的时候记得加await
            await msg(target_id, '抱歉，您不是管理', user_id)
            return
        await DEL_channel(guild_id, target_id, user_id, 2)
        await msg(target_id, '删除成功', user_id)
        # 输出日志
        logging.warning(f'用户:{user_id}删除了所有月临时频道')

    # 踢出机器人验证
    elif val == 'out':
        if not await has_admin(user_id, guild_id):  # 向has_admin函数中放入用户id和服务器id 调用的时候记得加await
            await msg(target_id, '抱歉，您不是管理', user_id)
            return

        # 更新卡片
        await upd_card(e.body['msg_id'], CardMessage(Card(
            Module.Header('是否确认踢出机器人'),
            Module.ActionGroup(Element.Button('确认', 'out_yes', theme=Types.Theme.PRIMARY),
                               Element.Button('取消', 'duration', theme=Types.Theme.DANGER))
        )))
    # 一键踢出机器人
    elif val == 'out_yes':
        if not await has_admin(user_id, guild_id):  # 向has_admin函数中放入用户id和服务器id 调用的时候记得加await
            await msg(target_id, '抱歉，您不是管理', user_id)
            return

        # 更新卡片，防止踢出机器人后还有人使用
        await upd_card(e.body['msg_id'], CardMessage(
            Card(Module.Header('机器人已从当前服务器踢出'), Module.Section('如果失败请联系开发者'))))
        # 判断机器人有没有存这个服务器的数据
        if guild_id in user_date:
            # 顺带删除所创建的频道及分组
            # 获取分组id
            channel_grouping = user_date[guild_id]['频道分组id']
            # 获取频道id
            for channel_id in user_date[guild_id]['频道id']:
                # 删除服务器所有临时频道
                await bot.client.delete_channel(channel_id)
            # 删除服务器分组
            await bot.client.delete_channel(channel_grouping)

            # 删除字典里关于这个服务器的数据
            del user_date[guild_id]
            # 将字典存入文件
            await write_file(path_id, user_date)
            # 使用退出服务器接口
            await user_del(guild_id)
        # 机器人字典里没有这个服务器
        else:
            # 直接退出服务器
            await user_del(guild_id)

    # 更新卡片
    elif val == 'duration':
        # 获取字典内当前时间
        a = time_date['time']
        # 更新卡片
        await ui.upd_card_hour(msg_id, a)
    elif val == 'month_duration':
        # 获取字典内当前时间
        a = time_month['time']
        # 更新卡片
        await ui.upd_card_month(msg_id, a)

    # 更改字典小时数
    elif val == 'time1':
        # 设置字典内时间为1小时
        a = time_date['time'] = 1
        # 更新卡片
        await ui.upd_card_hour(msg_id, a)
    elif val == 'time2':
        # 设置字典内时间为1小时
        a = time_date['time'] = 3
        # 更新卡片
        await ui.upd_card_hour(msg_id, a)
    elif val == 'time3':
        a = time_date['time'] = 5
        # 更新卡片
        await ui.upd_card_hour(msg_id, a)
    elif val == 'time4':
        a = time_date['time'] = 7
        # 更新卡片
        await ui.upd_card_hour(msg_id, a)

    elif val == 'month1':
        # 设置字典内时间为1个月
        a = time_month['time'] = 1
        # 更新卡片
        await ui.upd_card_month(msg_id, a)
    elif val == 'month2':
        # 设置字典内时间为4个月
        a = time_month['time'] = 4
        # 更新卡片
        await ui.upd_card_month(msg_id, a)
    elif val == 'month3':
        # 设置字典内时间为8个月
        a = time_month['time'] = 8
        # 更新卡片
        await ui.upd_card_month(msg_id, a)
    elif val == 'month4':
        # 设置字典内时间为12个月
        a = time_month['time'] = 12
        # 更新卡片
        await ui.upd_card_month(msg_id, a)


# 给某人的小惊喜
@bot.command(regex=r'[\s\S]*')
async def card123(m: Message):
    user_id = m.author.id
    if user_id == '1966740491':
        await bot.client.add_reaction(m, emoji='🤡')
        # 输出日志
        logging.warning(f'触发了彩蛋')


@bot.command(name='root')
async def root_user(m: Message):
    if str(m.author.id) != str(1858431934):
        print(m.author.id)
        await m.ctx.channel.send('你没有权限')
        return
    await m.ctx.channel.send('有权限也没有彩蛋')

if __name__ == '__main__':
    # 运行机器人
    bot.run()
