# 部署手册

前提：本地已能免密 SSH 登录服务器（已完成 ssh-copy-id）；`.deploy.env` 已按
`.deploy.env.example` 填好（该文件不进 git，密码不写入任何文件）。

## 首次部署

1. DNS：确认域名 A 记录指向服务器 IP：`dig +short simiam.com`
2. 服务器初始化（幂等，可重复执行）：`bash scripts/server-setup.sh`
3. 首次发布：HTTPS 尚未配置时，先把 `.deploy.env` 的 `SITE_URL` 临时设为 `http://simiam.com`，再执行 `npm run publish`
4. 配置 HTTPS（在服务器上执行，需要人工确认）：
   - 安装 certbot：Ubuntu/Debian 用 `apt install -y certbot python3-certbot-nginx`；
     CentOS/TencentOS 用 `yum install -y certbot python3-certbot-nginx`
   - 签发并自动改写 nginx 配置：
     `certbot --nginx -d simiam.com --agree-tos -m <你的邮箱> --no-eff-email`
   - 注意：配置 HTTPS 后如需重跑 `scripts/server-setup.sh`，脚本会检测到 HTTPS 配置并跳过 nginx 配置写入，不会覆盖 certbot 的修改
   - 验证自动续期：`certbot renew --dry-run`
5. 复查：`curl -I https://simiam.com/` 返回 200；http 应 301 到 https
6. 把 `.deploy.env` 的 `SITE_URL` 改回 `https://simiam.com`

## 日常发布

`npm run publish` —— 内容与类型检查 → 单元测试 → 构建 → rsync 同步 → 健康检查。
rsync 不可用时自动 fallback 到 git 通道（推送到服务器 bare 仓库，hook 自动 checkout）。
强制走 git 通道验证：`DEPLOY_FORCE_GIT=1 npm run publish`

线上健康检查失败会以非零状态退出，并给出 nginx、DNS、HTTPS 排查方向；即使文件同步完成，也不会把网站不可访问报告为发布成功。

## 安全加固（建议，是否执行由站主决定）

SSH 密钥已配好后，禁用密码登录（对所有用户生效，仅密钥可登录）可大幅降低被爆破风险：

    # 服务器上 /etc/ssh/sshd_config 中设置：
    PasswordAuthentication no
    # 然后 systemctl reload sshd

注意：执行前务必先确认密钥登录正常，否则会把自己锁在门外。

## 回滚

站点是纯静态且内容真源在本地 git：`git checkout <旧提交> -- content/ && npm run publish` 即回滚内容。
