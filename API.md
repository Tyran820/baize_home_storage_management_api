# 家庭收纳管理微服务 API 接口文档

## 概述

基础 URL (通过 Traefik 网关): `http://localhost/api`
直接调用微服务: `http://localhost:8000/api`

---

## 1. 系统与健康检查 (Health & Status)

### 1.1 获取根节点信息
- **接口路径**: `GET /`
- **说明**: 检查微服务运行状态与文档入口信息。
- **响应示例 (200 OK)**:
  ```json
  {
    "service": "Home Storage Management Microservice",
    "status": "running",
    "docs": "/docs"
  }
  ```

### 1.2 健康检查
- **接口路径**: `GET /health`
- **说明**: 用于 Traefik 或 API 网关的心跳检测与数据库连接检查。
- **响应示例 (200 OK)**:
  ```json
  {
    "status": "healthy",
    "database": "ok"
  }
  ```

---

## 2. 房间管理 (Rooms)

### 2.1 创建房间
- **接口路径**: `POST /api/rooms`
- **请求格式**: `multipart/form-data`
- **请求参数**:
  - `name` (string, required): 房间名称
  - `image` (file, optional): 房间平面图或照片
- **响应示例 (201 Created)**:
  ```json
  {
    "id": "60d5ec49f1a2c34b5c8f1a01",
    "name": "主卧",
    "image_url": "/uploads/rooms/a1b2c3d4.jpg"
  }
  ```

### 2.2 获取房间列表
- **接口路径**: `GET /api/rooms`
- **响应示例 (200 OK)**:
  ```json
  [
    {
      "id": "60d5ec49f1a2c34b5c8f1a01",
      "name": "主卧",
      "image_url": "/uploads/rooms/a1b2c3d4.jpg"
    }
  ]
  ```

### 2.3 获取房间详情
- **接口路径**: `GET /api/rooms/{room_id}`
- **说明**: 返回房间基本信息以及该房间下的所有柜子和存放的物品。
- **响应示例 (200 OK)**:
  ```json
  {
    "id": "60d5ec49f1a2c34b5c8f1a01",
    "name": "主卧",
    "image_url": "/uploads/rooms/a1b2c3d4.jpg",
    "cabinets": [
      {
        "id": "60d5ec49f1a2c34b5c8f1a02",
        "name": "衣柜",
        "room_id": "60d5ec49f1a2c34b5c8f1a01"
      }
    ],
    "items": [
      {
        "id": "60d5ec49f1a2c34b5c8f1a03",
        "name": "羽绒服",
        "quantity": 2,
        "cabinet_ids": ["60d5ec49f1a2c34b5c8f1a02"]
      }
    ]
  }
  ```

### 2.4 更新房间信息
- **接口路径**: `PUT /api/rooms/{room_id}`
- **请求格式**: `application/json`
- **请求体**:
  ```json
  {
    "name": "次卧"
  }
  ```

### 2.5 上传/更新房间图片
- **接口路径**: `POST /api/rooms/{room_id}/image`
- **请求格式**: `multipart/form-data`
- **请求参数**: `image` (file)

### 2.6 删除房间
- **接口路径**: `DELETE /api/rooms/{room_id}?cascade={true|false}`
- **查询参数**: `cascade` (boolean, 默认 false): 是否级联删除房间下的柜子。若不级联且包含柜子，将返回 400 错误。

---

## 3. 柜子/收纳位置管理 (Cabinets)

### 3.1 创建柜子
- **接口路径**: `POST /api/cabinets`
- **请求格式**: `multipart/form-data`
- **请求参数**:
  - `name` (string, required): 柜子名称
  - `room_id` (string, required): 所属房间 ID
  - `image` (file, optional): 柜子外观图片

### 3.2 获取柜子列表
- **接口路径**: `GET /api/cabinets`

### 3.3 获取柜子详情
- **接口路径**: `GET /api/cabinets/{cabinet_id}`
- **说明**: 返回柜子信息、所属房间信息以及柜子里包含的物品列表。

### 3.4 更新柜子信息
- **接口路径**: `PUT /api/cabinets/{cabinet_id}`
- **请求体**:
  ```json
  {
    "name": "床头柜",
    "room_id": "60d5ec49f1a2c34b5c8f1a01"
  }
  ```

### 3.5 上传/更新柜子图片
- **接口路径**: `POST /api/cabinets/{cabinet_id}/image`

### 3.6 删除柜子
- **接口路径**: `DELETE /api/cabinets/{cabinet_id}?cascade={true|false}`

---

## 4. 物品管理 (Items)

### 4.1 创建物品
- **接口路径**: `POST /api/items`
- **请求格式**: `application/json`
- **请求体**:
  ```json
  {
    "name": "护手霜",
    "cabinet_ids": ["60d5ec49f1a2c34b5c8f1a02"],
    "quantity": 3
  }
  ```

### 4.2 获取物品列表
- **接口路径**: `GET /api/items`

### 4.3 获取物品详情
- **接口路径**: `GET /api/items/{item_id}`
- **说明**: 返回物品信息、关联的柜子信息、所属房间信息以及在各个柜子中的收纳位置图片。

### 4.4 更新物品信息
- **接口路径**: `PUT /api/items/{item_id}`
- **请求体**:
  ```json
  {
    "name": "护手霜",
    "quantity": 5,
    "cabinet_ids": ["60d5ec49f1a2c34b5c8f1a02"]
  }
  ```

### 4.5 上传物品在特定柜子内的放置位置图片
- **接口路径**: `POST /api/items/{item_id}/images/{cabinet_id}`
- **请求格式**: `multipart/form-data`
- **请求参数**: `image` (file)

### 4.6 删除物品
- **接口路径**: `DELETE /api/items/{item_id}`
