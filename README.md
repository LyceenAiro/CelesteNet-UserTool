# CelesteNet-UserTool
这个软件是基于CelestNet接入库源码逆向开发的  
通过 [CelesteNet-Server-Releases](https://github.com/0x0ade/CelesteNet/releases) 进行搭建测试  
支持脱离Discord进行用户创建和管理
## 目前支持的功能
### 模块、配置
- [x] 自定义模块名(yaml)
- [x] 自定义数据文件夹(yaml)
- [x] 应用log模块
### 用户创建(可登录状态)(API)
- [x] 创建用户meta(自定义账户名, 自动生成密钥)
- [x] 创建用户的BasicUserInfo(用户实例)
### 用户实例管理(API)
- [x] 用户昵称修改
- [x] 用户头像修改
- [x] 用户管理员权限管理
- [x] 用户密钥重置
- [x] 完全注销用户
- [x] 查询用户信息
- [x] 用户封禁管理
### 前端管理
- [x] FLASK框架
- [x] WebAPI框架
- [x] 用户数据库管理
- [x] 用户登录/注册
- [x] 用户信息、权限绑定
- [x] 前端页面
- - [x] 服务器状态
- - [x] 在线用户(需要登录)
- - [x] 封禁查询
- - [x] 用户注册
- - [x] 用户登录并展示个人信息
- - [x] 用户注销
- - [x] 更换头像
- - [x] 重置密钥
- - [x] 修改自己的密码
- - [x] 修改自己的昵称
- - [x] Web执行封禁用户(管理员)
- - [x] Web执行解禁用户(超级管理员)
- - [x] Web执行管理员赋予/解除(超级管理员)
- - [x] 更多的前端信息自定义项目(yaml)
- - [x] 赋予/解除超级管理员(ymal)
### 不一定会做的更多计划
- [ ] 统计用户总在线时间
## 说明书
### 客户端
使用方法
```
直接使用CelesteNetClient, 设置服务器IP即可
使用Web或API生成的key可以正常使用
```
CelesteNetClient客户端配置地址
```
编辑 Celeste/Saves/modsettings-CelesteNet.Client.celeste
在 ExtraServers 配置项下方添加你的服务器地址即可在游戏中热切换服务器地址
```
ExtraServers配置示例
```
ExtraServers:
- celeste.net
- celeste.moon:23456
```
### UserTool部署
UserTool的整体入口在main.py中, 第一次运行会自动生成config.yaml和log文件夹  
在运行UserTool之前需要保证CelesteNetServer已部署, 且它的API可正常访问
```yaml
UserDataPath: CelesteNetServer数据库目录
CelesteNetApi: CelesteNetServer的API开放地址
```
直接运行UserTool会直接开启Web服务, 用户头像依赖CelesteNetServerAPI匹配
```yaml
WebHost: Web开放地址
WebPort: Web开放端口
WebTitle: Web标签名称
CelesteNetWebRedirect: 前端访问重定向CelesteNetServer的API
```
你还可以在配置中管理超级管理员权限, 一次只能赋予/移除一名用户超级管理员权限  
如果两个选项设置同一用户, 会优先移除超级管理员再重新赋予超级管理员  
如果用户没有管理员权限, 在赋予超级管理员权限的时候会自动赋予管理员
```yaml
SuperAdmin: 在UserTool开启时赋予用户超级管理员权限
RemoveSuperAdmin: 在UserTool开启时将某用户的超级管理员权限移除
```
其余的配置选项
```yaml
real: 如果你不知道这个配置有什么用途就不要修改
module: 如果你不知道这个配置有什么用途就不要修改
JWT_SECRET_KEY: 用户密码加密全局密钥, 修改后可能导致旧用户无法登录, 不要泄漏该配置
JWT_ACCESS_TOKEN_EXPIRES_MINUTES: 用户登录超时时长(分钟)
```
### 访客用户头像自定义
```
目前Web访客的头像都会重新定向到用户Guest
十分的建议管理员开启业务前先注册Guest用户并更改其头像
客户端通过访客登录在游戏中仍不会显示头像，Guest只影响Web
如果没有设置Guest的头像在玩家列表中有可能会发生图片加载错误
```
## License
[BSD 3-Clause License](./LICENSE)