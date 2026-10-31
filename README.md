# Home Storage Management Microservice (家庭收纳管理微服务)

本项目是一个基于 **FastAPI** 和 **MongoDB** 构建的家庭收纳管理系统微服务。服务集成了 **Traefik** 作为 API 网关，支持 Docker 及 Docker Compose 容器化部署。

---

## 目录结构

```text
.
├── app/
│   ├── main.py              # FastAPI 应用主入口（CORS、路由挂载、Health Check）
│   ├── database.py          # MongoDB 数据库连接配置与自动 Mock 降级
│   ├── utils.py             # 文件上传与格式化工具函数
│   └── routers/
│       ├── rooms.py         # 房间管理接口 (`/api/rooms`)
│       ├── cabinets.py      # 柜子/收纳位置接口 (`/api/cabinets`)
│       └── items.py         # 物品管理接口 (`/api/items`)
├── tests/                   # pytest 单元测试
├── Dockerfile               # 容器镜像构建文件
├── docker-compose.yml       # Docker Compose 多容器服务编排（包含 Traefik 网关、MongoDB）
├── openapi.json             # OpenAPI 3.0 规范接口描述文件
├── API.md                   # 详细接口文档说明
└── requirements.txt         # Python 依赖清单
```

---

## 架构与微服务特性

1. **API 网关集成 (Traefik)**：
   - 使用 Traefik 作为微服务入口网关，统一暴露 `http://localhost:80` 端口。
   - 自动路由 `/api`、`/uploads`、`/docs`、`/redoc`、`/openapi.json`、`/health` 请求至微服务。
   - Traefik 管理面板运行于 `http://localhost:8080`。

2. **微服务优化**：
   - **跨域支持 (CORS)**：配置了全局 CORS 中间件，方便前端或微服务网关直接调用。
   - **健康检查 (Health Check)**：提供 `/health` 端点，可检测服务存活状态及 MongoDB 数据库连通性。
   - **独立数据卷**：支持图片上传与数据库存储持久化 (`uploads_data`, `mongo_data`)。

---

## 快速开始 (Docker 部署)

### 1. 使用 Docker Compose 一键启动

在前台或后台启动所有服务（包括 Traefik 网关、MongoDB 数据库和微服务）：

```bash
docker-compose up -d --build
```

启动后服务访问地址：
- **网关 API 接口入口**：`http://localhost/api`
- **Swagger 交互式文档**：`http://localhost/docs`
- **ReDoc 交互式文档**：`http://localhost/redoc`
- **OpenAPI Schema**：`http://localhost/openapi.json`
- **服务健康检查**：`http://localhost/health`
- **Traefik Dashboard**：`http://localhost:8080`

### 2. 停止与清理服务

```bash
docker-compose down
```

如果需要同时清理数据卷（如 MongoDB 数据与上传的文件）：

```bash
docker-compose down -v
```

---

## 本地开发与测试

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行测试

```bash
PYTHONPATH=. pytest
```

### 3. 本地启动微服务

```bash
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

---

## 接口文档

详细的 RESTful API 接口定义请参阅 [API.md](./API.md) 或启动容器后直接访问 Swagger 界面 (`/docs`)。
