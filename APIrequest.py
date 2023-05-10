import main


# 这里是用来获取当前服务器所有频道
async def guild_channel_list(guild_id) -> list[str]:
    channel_list = []
    guild_list = await main.bot.client.gate.request('GET', 'channel/list', params={'guild_id': guild_id})
    for i in guild_list['items']:
        channel_list.append(i['id'])
    return channel_list


# 创建频道分组接口
async def create_grouping(guild_id, name) -> str:
    return (await main.bot.client.gate.request('POST', 'channel/create',
                                               data={'guild_id': guild_id, 'name': name, 'is_category': 1}))['id']


# 根据服务器和用户id获取用户当前所在频道
async def channel_number(guild_id, user_id) -> list:
    return (await main.bot.client.gate.request('GET', 'channel-user/get-joined-channel',
                                               params={'guild_id': guild_id, 'user_id': user_id}))['items']


# 获取语音内所有用户
async def channel_user(channel_id) -> list:
    return await main.bot.client.gate.request('GET', 'channel/user-list', params={'channel_id': channel_id})


# 更新频道人数上限
async def channel_number_maximums(channel_id, number) -> None:
    return (await main.bot.client.gate.request('POST', 'channel/update',
                                               data={'channel_id': channel_id, 'limit_amount': number}))


# 让机器人自己退出服务器
async def bot_out_guild(guild_id):
    return await main.bot.client.gate.request('POST', 'guild/leave', data={'guild_id': guild_id})
