# 部署指南

## 🚀 本地开发部署

### 前置要求
- Python 3.8+
- Node.js 18+
- npm 或 yarn
- Git

### 快速部署

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
bash start.sh
```

### 验证部署
```bash
python verify.py
```

## 🐳 Docker 部署

### 前置要求
- Docker
- Docker Compose

### 部署步骤

1. **构建镜像**
```bash
docker-compose build
```

2. **启动服务**
```bash
docker-compose up
```

3. **查看日志**
```bash
docker-compose logs -f
```

4. **停止服务**
```bash
docker-compose down
```

### Docker 命令参考

```bash
# 后台运行
docker-compose up -d

# 重启服务
docker-compose restart

# 查看状态
docker-compose ps

# 进入容器
docker-compose exec backend bash
docker-compose exec frontend sh

# 清理资源
docker-compose down -v
```

## ☁️ 云部署

###  部署

1. **EC2 实例**
   - 选择 Ubuntu 20.04 LTS
   - 安装 Docker 和 Docker Compose
   - 克隆项目
   - 运行 `docker-compose up -d`

2. **环境变量**
   - 设置 DASHSCOPE_API_KEY
   - 配置 NEXT_PUBLIC_API_URL

3. **安全组**
   - 开放 80 端口 (HTTP)
   - 开放 443 端口 (HTTPS)
   - 开放 8000 端口 (API)

### Heroku 部署

1. **创建 Procfile**
```
web: gunicorn main:app
```

2. **部署**
```bash
heroku create your-app-name
git push heroku main
```

### Vercel 部署 (前端)

1. **连接 GitHub**
2. **配置环境变量**
3. **自动部署**

## 🔧 生产环境配置

### 后端优化

1. **使用生产服务器**
```bash
gunicorn main:app -w 4 -b 0.0.0.0:8000
```

2. **启用 HTTPS**
```bash
# 使用 Let's Encrypt
certbot certonly --standalone -d your-domain.com
```

3. **配置反向代理**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 前端优化

1. **构建生产版本**
```bash
npm run build
npm start
```

2. **启用 CDN**
   - 使用 Cloudflare
   - 配置缓存策略

3. **性能优化**
   - 启用 Gzip 压缩
   - 配置缓存头

## 📊 监控和日志

### 后端监控

```bash
# 查看日志
tail -f backend.log

# 监控性能
htop

# 检查端口
netstat -tlnp | grep 8000
```

### 前端监控

```bash
# 构建分析
npm run build -- --analyze

# 性能测试
npm run lighthouse
```

## 🔐 安全检查清单

- [ ] 更新所有依赖包
- [ ] 启用 HTTPS
- [ ] 配置防火墙
- [ ] 设置强密码
- [ ] 启用 API 认证
- [ ] 配置速率限制
- [ ] 启用日志记录
- [ ] 定期备份数据
- [ ] 监控异常流量
- [ ] 定期安全审计

## 🚨 故障恢复

### 后端崩溃

```bash
# 重启服务
systemctl restart ai-chat-backend

# 查看状态
systemctl status ai-chat-backend

# 查看日志
journalctl -u ai-chat-backend -n 50
```

### 前端崩溃

```bash
# 重启 Node 进程
pm2 restart ai-chat-frontend

# 查看日志
pm2 logs ai-chat-frontend
```

### 数据库问题

```bash
# 检查连接
curl http://localhost:8000/api/health

# 重启容器
docker-compose restart backend
```

## 📈 扩展性

### 水平扩展

1. **负载均衡**
```bash
# 使用 Nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

2. **容器编排**
```bash
# 使用 Kubernetes
kubectl apply -f deployment.yaml
```

### 垂直扩展

1. **增加资源**
   - 增加 CPU
   - 增加内存
   - 增加存储

2. **优化代码**
   - 缓存优化
   - 数据库优化
   - 查询优化

## 📝 部署检查清单

### 部署前
- [ ] 所有测试通过
- [ ] 代码审查完成
- [ ] 依赖更新
- [ ] 文档更新
- [ ] 环境变量配置
- [ ] 备份数据

### 部署中
- [ ] 构建成功
- [ ] 容器启动
- [ ] 健康检查通过
- [ ] API 响应正常
- [ ] 前端加载正常

### 部署后
- [ ] 监控告警
- [ ] 日志检查
- [ ] 性能测试
- [ ] 用户反馈
- [ ] 文档更新

## 🔄 持续集成/持续部署 (CI/CD)

### GitHub Actions 示例

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build and push
        run: |
          docker-compose build
          docker-compose push
      - name: Deploy
        run: |
          ssh user@server 'cd /app && docker-compose pull && docker-compose up -d'
```

## 📞 支持和维护

### 定期维护任务

- 每周: 检查日志和监控
- 每月: 更新依赖包
- 每季度: 安全审计
- 每年: 性能评估

### 应急联系

- 技术支持: support@example.com
- 紧急热线: +86-xxx-xxxx-xxxx
- 文档: https://docs.example.com

---

**最后更新:** 2024-03-17
**版本:** 1.0.0
