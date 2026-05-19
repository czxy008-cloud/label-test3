# 会议室预约系统

基于 FastAPI + Vue 3 的全栈会议室预约管理系统。

## 功能特性

### 后端功能
- 用户认证与授权（JWT）
- 会议室管理（增删改查、容量、设备标签）
- 预约管理（创建、取消、冲突检测）
- 30分钟粒度预约时段
- 取消记录（操作者、时间、原因）
- 角色权限（管理员/普通用户）

### 前端功能
- 用户登录/注册
- 会议室日历视图（按天展示）
- 预约创建与取消
- 我的预约列表
- 管理员会议室管理
- 预约冲突实时检测

## 技术栈

### 后端
- **框架**: FastAPI 0.109.2
- **数据库**: PostgreSQL
- **ORM**: SQLAlchemy 2.0
- **认证**: JWT (python-jose)
- **密码加密**: bcrypt
- **环境隔离**: venv

### 前端
- **框架**: Vue 3 + Vite
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP客户端**: Axios
- **日期处理**: Day.js

## 项目结构

```
meeting-room-booking/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── main.py            # FastAPI 主入口
│   │   ├── database.py        # 数据库连接配置
│   │   ├── auth.py            # 认证相关
│   │   ├── models/            # SQLAlchemy 模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── room.py
│   │   │   └── booking.py
│   │   ├── schemas/           # Pydantic 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── room.py
│   │   │   └── booking.py
│   │   └── routers/           # API 路由
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── rooms.py
│   │       └── bookings.py
│   ├── scripts/               # 脚本
│   │   └── init_db.py         # 数据库初始化脚本
│   ├── requirements.txt       # Python 依赖
│   └── .env.example           # 环境变量示例
└── frontend/                   # 前端代码
    ├── src/
    │   ├── main.js            # 入口文件
    │   ├── App.vue            # 根组件
    │   ├── router/            # 路由配置
    │   ├── stores/            # Pinia 状态管理
    │   ├── utils/             # 工具函数（axios, api）
    │   └── views/             # 页面组件
    │       ├── Login.vue
    │       ├── Layout.vue
    │       ├── Calendar.vue
    │       ├── MyBookings.vue
    │       └── admin/
    │           └── Rooms.vue
    ├── package.json
    └── vite.config.js
```

## 快速开始

### 环境要求
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+

### 1. 数据库准备

确保 PostgreSQL 服务已启动，创建数据库：

```sql
CREATE DATABASE meeting_room;
```

### 2. 后端启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量配置
cp .env.example .env
# 编辑 .env，配置数据库连接信息

# 初始化数据库（创建表 + 种子数据）
python scripts/init_db.py

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端 API 文档: http://localhost:8000/docs

### 3. 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端访问地址: http://localhost:3000

### 4. 默认账号

数据库初始化后，可使用以下账号登录：

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 普通用户 | zhangsan | 123456 |
| 普通用户 | lisi | 123456 |
| 普通用户 | wangwu | 123456 |

## API 接口

### 认证接口
- `POST /auth/register` - 用户注册
- `POST /auth/login` - 用户登录
- `GET /auth/me` - 获取当前用户信息

### 会议室接口
- `GET /rooms` - 获取所有可用会议室
- `GET /rooms/all` - 获取所有会议室（管理员）
- `GET /rooms/{id}` - 获取会议室详情
- `POST /rooms` - 创建会议室（管理员）
- `PUT /rooms/{id}` - 更新会议室（管理员）
- `DELETE /rooms/{id}` - 删除会议室（管理员）

### 预约接口
- `GET /bookings` - 获取预约列表
- `GET /bookings/my` - 获取我的预约
- `GET /bookings/{id}` - 获取预约详情
- `POST /bookings` - 创建预约
- `PUT /bookings/{id}` - 更新预约
- `POST /bookings/{id}/cancel` - 取消预约
- `DELETE /bookings/{id}` - 删除预约（管理员）
- `GET /bookings/conflict/check` - 检查时间冲突

## 核心业务规则

1. **预约时段**: 以 30 分钟为最小单位，最短预约时长 30 分钟
2. **时间范围**: 每天 08:00 - 21:00 可预约
3. **冲突检测**: 同一会议室同一时段只能有一个有效预约
4. **取消权限**: 用户只能取消自己的预约，管理员可取消所有预约
5. **取消记录**: 取消时记录取消人、取消时间、取消原因
6. **容量限制**: 参会人数不能超过会议室容量

## 开发说明

### 后端
- 代码遵循 PEP 8 规范
- 使用类型注解
- 数据库迁移可使用 Alembic

### 前端
- 使用 Vue 3 Composition API
- 组件化开发
- 响应式设计

## License

MIT
