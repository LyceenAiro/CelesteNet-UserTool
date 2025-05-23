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
- [ ] Web服务器基础
- [ ] 用户数据库管理
- [ ] 用户登录/注册
- [ ] 用户信息、权限绑定
## License
[BSD 3-Clause License](./LICENSE)