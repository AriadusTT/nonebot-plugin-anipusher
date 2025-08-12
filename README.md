<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://v2.nonebot.dev/logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
</div>

<div align="center">

# nonebot-plugin-AniPusher

_✨ NoneBot AniPusher插件 ✨_<br>
NoneBot AniPusher插件 是将特定Webhooks消息推送至QQ的插件<br>
目前支持配置来自ani-rss和emby的webhooks消息



[![license](https://img.shields.io/github/license/AriadusTT/nonebot-plugin-anipusher.svg?cachebust=1)](./LICENSE)
[![pypi](https://img.shields.io/pypi/v/nonebot-plugin-AniPusher.svg)](https://pypi.python.org/pypi/nonebot-plugin-AniPusher)
[![python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
</div>


## 📖 介绍

AniPusher插件 是将特定Webhook消息推送至QQ的插件<br>

目前支持AniRSS和Emby推送<br>

![show](./docs/show.png)

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-anipusher
</details>

<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令



## 🎉 插件启用和配置方法

### 🔓启用插件
打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_AniPusher"]

### ⚙️ 插件配置

配置项位于 nonebot2 项目根目录下的 `.env` 文件内<br>
所有配置项均为非必选项，但建议填写。配置项缺失会导致对应功能被关闭。<br>

> [!IMPORTANT]
> 首次运行前请确保如下插件配置项已配置，否则插件将无法正常运行！<br>
> 在.env文件中写入如下4个配置项（示例效果如图），配置项内容请根据下方填写：<br>
> anipush__emby_host="Emby的服务器地址"<br>
> anipush__emby_apikey="Emby密钥"<br>
> anipush__tmdb_apikey="TMDBApiKey"<br>
> anipush__tmdb_proxy="TMDB代理地址"<br>
>![env](./docs/最低配置样式.png)


| 配置项 | 必填 | 默认值 | 说明 |
|:----|:----:|:----:|:----:|
| anipush__emby_host | 否 | 无 | Emby的服务器地址（请勿填写中转地址）|
| anipush__emby_apikey | 否 | 无 | Emby服务器-高级-API密钥中生成的密钥 |
| anipush__tmdb_apikey | 否 | 无 | TMDB用户的ApiKey|
| anipush__tmdb_proxy | 否 | 无 | TMDB代理，如不填写则不使用代理 |

> [!IMPORTANT]
> 所有配置项均为非必填项，但建议填写。配置项缺失会导致对应功能被关闭。

## ⚙️ Webhook发送端配置
### ⚙️[ani-rss](https://github.com/wushuo894/ani-rss)
该配置方法基于ani-rss `v2.0.13` 更新后新的通知配置功能<br>

`ani-rss → 设置 → 通知 → 添加通知`<br>
↓按如下配置↓<br>
![ani-rss-config](./docs/ani-rss-config.png)

通知类型为`Webhook`<br>
Method为`POST`<br>
URL为Nonebot2的IP地址和端口下的路径`/webhook`<br>
例如`http://Nonebot_IP:8080/webhook`<br>

↓Body请复制下方Json填入↓<br>

```json
{
  "ani": "${action}",
  "action": "${action}",
  "title": "${title}",
  "jpTitle": "${jpTitle}",
  "score": "${score}",
  "themoviedbName": "${themoviedbName}",
  "tmdbid": "${tmdbid}",
  "tmdbUrl": "${tmdburl}",
  "bgmUrl": "${bgmUrl}",
  "season": "${season}",
  "episode": "${episode}",
  "subgroup": "${subgroup}",
  "progress": "${currentEpisodeNumber}/${totalEpisodeNumber}",
  "premiere": "${year}-${month}-${date}",
  "text": "${text}",
  "downloadPath": "${downloadPath}",
  "episodeTitle": "${episodeTitle}",
  "bgmEpisodeTitle": "${bgmEpisodeTitle}",
  "bgmJpEpisodeTitle": "${bgmJpEpisodeTitle}",
  "image": "${image}"
}
```
> [!TIP]
> 如果未来AniRSS更新通知配置发生变化，需更改Body结构时，请保留键```"ani": "${action}"```，程序判断数据来源依赖此键！<br>
> 其余键值对可根据ani-rss的使用文档中通知下的通知模板对应的键结构进行更改<br>

### ⚙️ Emby
首先请确保你已在Emby服务器上安装了Webhooks插件（该插件目前已自动集成，应该不用再手动装了）<br>

`Emby → 设置 → 通知 → 添加通知 -> Webhooks`<br>
↓按如下配置↓<br>
![embv-config](./docs/emby-config.png)

网址为Nonebot2的IP地址和端口下的路径`/webhook`<br>
例如`http://Nonebot_IP:8080/webhook`<br>
请求内容类型为`application/json`<br>
Event目前只支持`媒体库-新媒体已添加`<br>
其他选项根据自身需求更改<br>


## 🎉 使用
### 指令表
| 指令 | 权限 | 需要@ | 范围 | 说明 |
|:-----|:----:|:----:|:----:|:----|
| 注册Emby推送 | ALL | 否 | ALL | 群聊：将群组添加到Emby更新消息推送列表中有新消息时将消息推送到群内<br>私聊：发送指令后即将用户添加到Emby更新消息推送列表中 |
| 注册AniRSS推送 | ALL | 否 | ALL | 群聊：将群组添加到AniRSS更新消息推送列表中有新消息时将消息推送到群内<br>私聊：发送指令后即将用户添加到AniRSS更新消息推送列表中 |
| 取消Emby推送 | ALL | 否 | ALL | 群聊：发送指令后关闭群组更新消息推送，不再接收推送<br>私聊：发送指令后关闭用户更新消息推送，不再接收推送 |
| 取消AniRSS推送 | ALL | 否 | ALL | 群聊：发送指令后关闭群组更新消息推送，不再接收推送<br>私聊：发送指令后关闭用户更新消息推送，不再接收推送 |
|屏蔽推送| ALL | 否 | ALL | 在不关闭bot的情况下置空所有推送列表<br>新消息不再推送，恢复后也不会补推送|
|恢复推送| ALL | 否 | ALL | 恢复所有推送服务|
