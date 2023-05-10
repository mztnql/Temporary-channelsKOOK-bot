import main
import APIrequest

import json
import os
import copy
import time
from typing import Union

import aiofiles
from khl import *


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


# 检测用户是否为管理-1
async def has_admin(user_id, guild_id):
    id_guild = await main.bot.client.fetch_guild(guild_id)
    user_roles = (await id_guild.fetch_user(user_id)).roles
    guild_roles = await (await main.bot.client.fetch_guild(guild_id)).fetch_roles()
    for i in guild_roles:  # 遍历服务器身分组
        if i.id in user_roles and i.has_permission(0):  # 查看当前遍历到的身分组是否在用户身分组内且是否有管理员权限
            return True
    if user_id == id_guild.master_id:  # 由于腐竹可能没给自己上身分组，但是依旧拥有管理员权限
        return True
    return False


# 更新消息
async def upd_msg(msg_id: str, content, target_id: str = None,
                  channel_type: Union[ChannelPrivacyTypes, str] = 'public'):
    content = json.dumps(content)
    data = {'msg_id': msg_id, 'content': content}
    if target_id is not None:
        data['temp_target_id'] = target_id
    if channel_type == 'public' or channel_type == ChannelPrivacyTypes.GROUP or channel_type == 'GROUP':
        result = await main.bot.client.gate.request('POST', 'message/update', data=data)
    else:
        result = await main.bot.client.gate.request('POST', 'direct-message/update', data=data)
    return result


# 创建频道
async def create_channel(channel_data, guild_id, target_id, user_id, channel_time, channel_type=0, channel_name=0) -> None:
    """
    guild_id: 服务器id
    target_ti: 文字频道id
    user_id: 用户id
    channel_time: 频道时间
    channel_type: 要创建的频道储存位置，==0为小时 !=0为月
    channel_name: 要创建的频道类型 ==0为语音频道 !=0为文字频道

    里面所使用的函数有
        data_upd
        detect_channel_time
        detect_channel_del
    """
    if channel_type == 0:  # 按小时创建频道
        b = channel_time  # 获取字典内时间
        if channel_name == 0:
            name = f'临时语音频道   {b}小时'
        else:
            name = f'临时文字频道   {b}小时'
        expire_time = time.time() + b * int(main.timestamp)  # 计算出b小时后的时间戳
    else:  # 按月创建频道
        b = channel_time  # 获取字典内时间
        if channel_name == 0:
            name = f'临时语音频道   {b}个月'
        else:
            name = f'临时文字频道   {b}个月'
        expire_time = time.time() + b * 2592000  # 计算出b小时后的时间戳

    # 判断该服务器是否使用过
    if guild_id not in channel_data:
        grouping = await APIrequest.create_grouping(guild_id, '临时频道分组')
        channel_data[guild_id] = {'频道分组': grouping, '频道': {}, '频道月': {}}
        await write_file(main.channel_data_path, channel_data)

    # 在删除分组的情况下对分组进行处理
    channel_data_copy = copy.deepcopy(channel_data)
    await detect_channel_del(channel_data, channel_data_copy)
    if channel_data[guild_id]['频道分组'] == 0:
        grouping = await APIrequest.create_grouping(guild_id, '临时频道分组')
        channel_data[guild_id]['频道分组'] = grouping
        await write_file(main.channel_data_path, channel_data)

    if len(channel_data[guild_id]['频道']) >= main.channel_max:
        await (await main.bot.client.fetch_public_channel(target_id)).send('频道 创建数量已达当前上限', temp_target_id=user_id)
        return
    elif len(channel_data[guild_id]['频道月']) >= main.channel_month_max:
        await (await main.bot.client.fetch_public_channel(target_id)).send('频道月 创建数量已达当前上限', temp_target_id=user_id)
        return

    # 创建频道
    if channel_type == 0:
        if channel_name == 0:
            channel_id = (await main.bot.client.create_voice_channel(name, guild_id, channel_data[guild_id]['频道分组'])).id
        else:
            channel_id = (await main.bot.client.create_text_channel(guild_id, name, channel_data[guild_id]['频道分组'])).id
        channel_data[guild_id]['频道'][channel_id] = expire_time
        await write_file(main.channel_data_path, channel_data)
    else:
        if channel_name == 0:
            channel_id = (
                await main.bot.client.create_voice_channel(name, guild_id, channel_data[guild_id]['频道分组'])).id
        else:
            channel_id = (
                await main.bot.client.create_text_channel(guild_id, name, channel_data[guild_id]['频道分组'])).id
        channel_data[guild_id]['频道月'][channel_id] = expire_time
        await write_file(main.channel_data_path, channel_data)
    if channel_name == 0:
        await (await main.bot.client.fetch_public_channel(target_id)).send('临时语音频道创建成功',
                                                                           temp_target_id=user_id)
    else:
        await (await main.bot.client.fetch_public_channel(target_id)).send('临时文字频道创建成功',
                                                                           temp_target_id=user_id)


# 对于文件内所有内容进行验证
async def data_upd(channel_data) -> None:
    # 复制一份字典
    channel_data_copy = copy.deepcopy(channel_data)

    # 检测用户是否删除了频道
    await detect_channel_del(channel_data, channel_data_copy)

    # 判断频道是否过了时间
    await detect_channel_time(channel_data, channel_data_copy)

    # 判断字典和复制的字典是否有出入
    if channel_data != channel_data_copy:
        # 我们对比遍历后的guild_setting有没有变更，变更的话就往文件里存一份
        await write_file(main.channel_data_path, channel_data)


# 检测用户是否手动删除了频道
async def detect_channel_del(channel_data, channel_data_copy) -> None:
    for guild_id in channel_data_copy:
        guild_channel = await APIrequest.guild_channel_list(guild_id)
        for x in channel_data_copy[guild_id]['频道']:
            if x not in guild_channel:
                del channel_data[guild_id]['频道'][x]
        for x in channel_data_copy[guild_id]['频道月']:
            if x not in guild_channel:
                del channel_data[guild_id]['频道月'][x]
        if channel_data_copy[guild_id]['频道分组'] not in guild_channel:
            channel_data[guild_id]['频道分组'] = 0


# 判断频道是否过期
async def detect_channel_time(channel_data, channel_data_copy) -> None:
    for guild_id, value in channel_data_copy.items():
        # 遍历value里的 频道id 的键和值
        for channels, expired_time in value['频道'].items():
            # 判断频道id里的过期时间戳是否小于当前时间戳
            if expired_time < time.time():
                # 当前时间戳大于过期时间戳后，删除过期频道
                await main.bot.client.delete_channel(channels)
                # 删除字典内过期频道及它的时间戳
                del channel_data[guild_id]['频道'][channels]
        for channels, expired_time in value['频道月'].items():
            # 判断频道id里的过期时间戳是否小于当前时间戳
            if expired_time < time.time():
                # 当前时间戳大于过期时间戳后，删除过期频道
                await main.bot.client.delete_channel(channels)
                # 删除字典内过期频道及它的时间戳
                del channel_data[guild_id]['频道月'][channels]


# 修改频道人数上限
async def revise_number(guild_id, target_id, user_id, num=None) -> None:
    """
    guild_id: 服务器id
    target_id: 文字频道id
    user_id: 用户id
    num: 这里用于判断是否为默认(不限制人数)
    """
    channel_id = await APIrequest.channel_number(guild_id, user_id)
    if not channel_id:
        await (await main.bot.client.fetch_public_channel(target_id)).send('您不在语音频道内', temp_target_id=user_id)
        return
    channel_id = channel_id[0]['id']
    if num is not None:
        await APIrequest.channel_number_maximums(channel_id, 0)
        return
    else:
        user_num = len(await APIrequest.channel_user(channel_id))
        await APIrequest.channel_number_maximums(channel_id, user_num)


# 删除指定键下的所有频道
async def del_all_channel(channel_data, guild_id, del_name: str) -> None:
    """
    guild_id: 服务器id
    target_id: 文字频道id
    user_id: 用户id
    del_num: 需要删除内容的键名
    """
    # 复制一份字典，防止遍历时报错
    channel_data_copy = copy.deepcopy(channel_data)
    # 判断服务器是否在字典里
    if guild_id in channel_data_copy:
        for channel_id in channel_data_copy[guild_id][del_name]:
            await main.bot.client.delete_channel(channel_id)
        channel_data[guild_id][del_name] = {}
        await write_file(main.channel_data_path, channel_data)


# 机器人退出服务器
async def bot_out(channel_data, guild_id) -> None:
    """
    guild_id: 服务器id
    """
    # 复制一份字典，防止遍历时报错
    channel_data_copy = copy.deepcopy(channel_data)
    if guild_id in channel_data_copy:
        for channel_id in channel_data_copy[guild_id]['频道']:
            await main.bot.client.delete_channel(channel_id)
        for channel_id in channel_data_copy[guild_id]['频道月']:
            await main.bot.client.delete_channel(channel_id)
        if channel_data[guild_id]['频道分组'] != 0:
            await main.bot.client.delete_channel(channel_data[guild_id]['频道分组'])
        del channel_data[guild_id]
        await write_file(main.channel_data_path, channel_data)
    await APIrequest.bot_out_guild(guild_id)


# 修改分组位置
async def revise_grouping_id(channel_data, guild_id, channel_id) -> None:
    """
    guild_id: 服务器id
    channel_id: 分组id
    """
    # 如果字典里没有服务器id那么就频道分组肯定也没有
    if guild_id not in channel_data:
        # 将频道分组id写入字典，后续再写入文件
        channel_data[guild_id] = {'频道分组': str(channel_id), '频道': {}, '频道月': {}}
        await write_file(main.channel_data_path, channel_data)
    else:
        channel_data[guild_id]['频道分组'] = channel_id
        await write_file(main.channel_data_path, channel_data)


# 删除指定频道
async def del_channel(channel_data, guild_id, channel_id, target_id) -> None:
    """
    guild_id: 服务器id
    channel_id: 要删除的频道id
    target_id: 发送指令的文字频道id
    """
    if guild_id not in channel_data:
        # 不在字典里直接删除
        await main.bot.client.delete_channel(channel_id)

    # 判断是否为临时频道分组，如果是删除频道同时删除字典里内容
    elif channel_id in channel_data[guild_id]['频道分组']:
        await main.bot.client.delete_channel(channel_id)
        channel_data[guild_id]['频道分组id'] = 0
        await write_file(main.channel_data_path, channel_data)
    # 检测是否为临时频道，如果是则删除
    elif channel_id in channel_data[guild_id]['频道']:
        await main.bot.client.delete_channel(channel_id)
        del channel_data[guild_id]['频道'][channel_id]
        await write_file(main.channel_data_path, channel_data)
    # 检测是否为临时频道月，如果是则删除
    elif channel_id in channel_data[guild_id]['频道月']:
        # 删除频道
        await main.bot.client.delete_channel(channel_id)
        # 删除字典内容
        del channel_data[guild_id]['频道月'][channel_id]
        # 存入文件
        await write_file(main.channel_data_path, channel_data)

    # 如果不是临时频道则直接删除
    else:
        await main.bot.client.delete_channel(channel_id)
    await (await main.bot.client.fetch_public_channel(target_id)).send('删除成功')


# 当服务器删除频道时使用
async def guild_del_channel(channel_data, guild_id, channel_id) -> None:
    # 如果删除的是频道分组
    if channel_id == channel_data[guild_id]['频道分组']:
        channel_data[guild_id]['频道分组'] = 0
        await write_file(main.channel_data_path, channel_data)
    # 如果删除的是频道
    elif channel_id in channel_data[guild_id]['频道']:
        del channel_data[guild_id]['频道'][channel_id]
        await write_file(main.channel_data_path, channel_data)
    elif channel_id in channel_data[guild_id]['频道月']:
        del channel_data[guild_id]['频道月'][channel_id]
        await write_file(main.channel_data_path, channel_data)
