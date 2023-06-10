import disnake
from disnake.ext import commands
import yt_dlp as youtube_dl
from os import environ
from asyncio import sleep
import json
from typing import Optional

#disnake.opus.load_opus("/opt/homebrew/Cellar/opus/1.3.1/lib/libopus.dylib")
bot = commands.Bot(command_prefix='*', help_command=None, intents=disnake.Intents.all())
is_play = False
vc = None

class MenuPlayButtons(disnake.ui.View):
  def __init__(self):
    super().__init__(timeout=20)
    self.value = Optional[bool]
  
  @disnake.ui.button(label='Вернуться', emoji='↩', style=disnake.ButtonStyle.blurple) #1-я кнопка; label='название кнопки'; style=disnake.ButtonStyle.цвет
  async def ret(self, button: disnake.ui.Button, inter: disnake.CommandInteraction):
    await inter.response.defer()
    view = disnake.ui.View(timeout=20)
    view.add_item(MenuPlay())
    await inter.edit_original_response('Выберите нужную категорию', view=view)
    self.value = True
    self.stop()
  @disnake.ui.button(label='Закрыть меню', style=disnake.ButtonStyle.red) #1-я кнопка; label='название кнопки'; style=disnake.ButtonStyle.цвет
  async def close(self, button: disnake.ui.Button, inter: disnake.CommandInteraction):
    await inter.message.delete()
    self.value = False
    self.stop()
    

class MenuPlay(disnake.ui.Select):
  def __init__(self):
    options = [
      disnake.SelectOption(label='Отдельные видео', value='videos', emoji='🎶', description='Список отдельно сохраннёных видео для воспроизведения'),
      disnake.SelectOption(label='Плейлисты', value='playlist', emoji='📼', description='Список сохранённых плейлистов для воспроизведения')]
    super().__init__(placeholder='Выберите категорию', options=options, custom_id='play', min_values=1, max_values=1)
  
  async def callback(self, inter: disnake.MessageInteraction):
    await inter.response.defer()
    if inter.values[0] == 'playlist':
      view2 = MenuPlayButtons()
      view2.add_item(MenuPlayPlaylist())
      await inter.edit_original_response('Выберите плейлист', view=view2)
    if inter.values[0] == 'videos':
      view2 = MenuPlayButtons()
      view2.add_item(MenuPlayVideo())
      await inter.edit_original_response('Выберите видео', view=view2)

class MenuPlayPlaylist(disnake.ui.Select):
  def __init__(self):
    with open('', 'r') as f:
      links = json.load(f)
    options = []
    playlists = links['playlist'][0]
    playlists = sorted(playlists.items())
    for i in range(len(playlists)):
      options.append(disnake.SelectOption(label=playlists[i][0], value=i))
    super().__init__(placeholder='Выберите плейлист', options=options, custom_id='play_playlist', min_values=1, max_values=1)
  async def callback(self, inter: disnake.MessageInteraction):
    await inter.response.defer()
    await play_playlist(inter, int(inter.values[0])) 

class MenuPlayVideo(disnake.ui.Select):
  def __init__(self):
    with open('', 'r') as f:
      links = json.load(f)
    options = []
    music = links['music'][0]
    music = sorted(music.items())
    for i in range(len(music)):
      options.append(disnake.SelectOption(label=music[i][0], value=i))
    super().__init__(placeholder='Выберите видео', options=options, custom_id=' ideo', min_values=1, max_values=1)
  async def callback(self, inter: disnake.MessageInteraction):
    await inter.response.defer()
    await play_video(inter, int(inter.values[0]))

async def play_video(inter, i):
  global vc, is_play
  YDL_OPTIONS = {'format': 'bestaudio'}
  FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
  try:
    v_channel = inter.author.voice.channel
    vc = await v_channel.connect(reconnect=True)
  except:
    await inter.edit_original_message('Вы не в голосовом канале или бот уже подключен', view=None)
    await sleep(3)
    view2 = MenuPlayButtons()
    view2.add_item(MenuPlayVideo())
    await inter.edit_original_message('Выберите видео', view=view2)
    return
  with open('', 'r') as f:
    links = json.load(f)
  music = links['music'][0]
  music = sorted(music.items())
  await inter.delete_original_message()
  msg = await inter.channel.send('Загрузка...')
  is_play = True
  while is_play:
    for j in range(int(i), len(music)):
      if is_play == False:
        break
      await msg.edit(content=f'Видео **{j+1}/{len(music)}**:\n```\n{music[j][0]}\n```', view=None)
      with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(music[j][1], download=False)
      for format in info['formats']:
        if format["ext"] == "m4a":
          url = format['url']
      vc.play(disnake.FFmpegPCMAudio(executable="ffmpeg\\ffmpeg.exe", source=url, **FFMPEG_OPTIONS))
      while vc.is_playing():
        await sleep(1)
    i = 0
  vc = None


async def play_playlist(inter, i):
  global vc, is_play
  YDL_OPTIONS = {'format': 'bestaudio'}
  FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
  with open('', 'r') as f:
    links = json.load(f)
  playlist = links['playlist'][0]
  playlist = sorted(playlist.items())
  is_play = True
  await inter.edit_original_message('Получение информации о плейлисте\n*Ждите это долго...*', view=None)
  try:
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
      info = ydl.extract_info(playlist[i][1], download=False)
  except:
    await inter.edit_original_message('Не удалось загрузить данный плейлист', view=None)
    await sleep(3)
    view2 = MenuPlayButtons()
    view2.add_item(MenuPlayPlaylist())
    await inter.edit_original_message('Выберите плейлист', view=view2)
    return
  await inter.author.voice.channel.connect()
  await inter.delete_original_message()
  msg = await inter.channel.send('Загрузка...')
  while is_play:
    for m in range(len(info['entries'])):
      if is_play == False:
        break
      name = info['entries'][m]['title']
      n = len(info['entries'])
      await msg.edit(content=f'Плейлист:\n```\n{playlist[i][0]}\n```\nВидео **{m+1}/{n}**:\n```\n{name}\n```', view=None)
      for format in info['entries'][m]['formats']:
        if format["ext"] == "m4a":
          url = format['url']
      vc = inter.guild.voice_client
      vc.play(disnake.FFmpegPCMAudio(executable="ffmpeg\\ffmpeg.exe", source=url, **FFMPEG_OPTIONS))
      while vc.is_playing():
        await sleep(1)
    i = 0
  vc = None


@bot.slash_command(description='Меню выбора')
async def play(ctx: disnake.CommandInteraction):
  view = disnake.ui.View(timeout=20)
  view.add_item(MenuPlay())
  await ctx.response.send_message('Выберите нужную категорию', view=view)

@bot.slash_command(description='Сохраняет видео по ссылке')
@commands.has_permissions(kick_members=True)
async def add(ctx: disnake.CommandInteraction, choice:str = commands.Param(description='Видео/Плейлист', choices=['Видео', 'Плейлист']), url:str = commands.Param(description='Ссылка на добавляемое видео')):
  await ctx.response.defer()
  if choice == 'Видео':
    if url.startswith('https://youtu.be/') or url.startswith('https://www.youtube.com/watch') and not url.startswith('https://youtube.com/playlist') and not url.startswith('https://www.youtube.com/playlist'):
      YDL_OPTIONS = {'format': 'bestaudio'}
      with open('', 'r') as f:
        links = json.load(f)
      with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
      music = links['music'][0]
      if info['title'] in music:
        await ctx.edit_original_response('Это видео уже сохранено')
      else:
        links['music'][0][info['title']] = url
        with open('', 'w') as f:
          json.dump(links, f)
        await ctx.edit_original_response('Видео добавлено: **"'+ info['title'] +'"**')
    else:
      await ctx.edit_original_response('Неверная ссылка на видео')
  
  elif choice == 'Плейлист':
    if url.startswith('https://youtube.com/playlist') or url.startswith('https://www.youtube.com/playlist'):
      YDL_OPTIONS = {'format': 'bestaudio'}
      with open('', 'r') as f:
        links = json.load(f)
      try:
        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
          info = ydl.extract_info(url, download=False)
      except:
        await ctx.edit_original_response('Не удалось обработать этот плейлист')
        return
      playlist = links['playlist'][0]
      if info['title'] in playlist:
        await ctx.edit_original_response('Этот плейлист уже сохранен')
      else:
        links['playlist'][0][info['title']] = url
        with open('', 'w') as f:
          json.dump(links, f)
        await ctx.edit_original_response('Плейлист добавлен: **"'+ info['title'] +'"**')
    else:
      await ctx.edit_original_response('Неверная ссылка на плейлист')

@bot.slash_command(description='Отображает список сохранённых видео и плейлистов')
async def list(ctx: disnake.CommandInteraction):
  await ctx.response.defer()
  embed = disnake.Embed(title='Список отдельных видео', colour=disnake.Colour.from_rgb(2, 224, 95))
  embed2 = disnake.Embed(title='Список плейлистов', colour=disnake.Colour.from_rgb(154, 6, 199))
  with open('', 'r') as f:
    links = json.load(f)
  music = links['music'][0]
  music = sorted(music.items())
  playlist = links['playlist'][0]
  playlist = sorted(playlist.items())
  for i in music:
    embed.add_field(name=f'{music.index(i)+1}. {i[0]}', value=i[1], inline=False)
  for i in playlist:
    embed2.add_field(f'{playlist.index(i)+1}. {i[0]}', value=i[1], inline=False)
  await ctx.edit_original_response(embeds=[embed, embed2])

@bot.slash_command(description='Удаляет сохранённое видео')
@commands.has_permissions(kick_members=True)
async def remove(ctx: disnake.CommandInteraction, choice:str = commands.Param(description='Видео/Плейлист', choices=['Видео', 'Плейлист']), number:int=commands.Param(description='Номер удаляемого элемента `/list`')):
  await ctx.response.defer()
  with open('', 'r') as f:
    links = json.load(f)
  if choice == 'Видео':
    musics = links['music'][0]
    music = sorted(musics.items())
    if number > len(music) or number <= 0:
      await ctx.edit_original_response('Неверный номер видео')
    else:
      await ctx.edit_original_response(f'Видео успешно удалено: **"{music[number-1][0]}"**')
      del links['music'][0][music[number-1][0]]
  elif choice == 'Плейлист':
    playlists = links['playlist'][0]
    playlist = sorted(playlists.items())
    if number > len(playlist) or number <= 0:
      await ctx.edit_original_response('Неверный номер плейлиста')
    else:
      await ctx.edit_original_response(f'Плейлист успешно удалён: **"{playlist[number-1][0]}"**')
      del links['playlist'][0][playlist[number-1][0]]
    
  with open('C:\disss\аудио-бот\', 'w') as f:
    json.dump(links, f)

@bot.slash_command(description='Пропускает видео')
async def next(ctx: disnake.CommandInteraction, arg:str = commands.Param(description='Пропускает видео', choices=['Video'])):
  await ctx.response.defer(ephemeral=True)
  if vc != None:
    if arg == 'Video':
      vc.stop()
      await ctx.edit_original_response('Успешно')
  else:
    await ctx.edit_original_response('Музыка не воспроизводится')

@bot.slash_command(description='Останавливает воспроизведение')
async def stop(ctx: disnake.CommandInteraction):
  global is_play
  await ctx.response.defer(ephemeral=True)
  if vc != None:
    vc.stop()
    await vc.disconnect()
    is_play = False
    await ctx.edit_original_response('Успешно')
  else:
    await ctx.edit_original_response('Музыка не воспроизводится') 
  
bot.run('')
