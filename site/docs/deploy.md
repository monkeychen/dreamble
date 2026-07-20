# 部署手册

以下命令默认从 `dreamble` 仓库根目录执行。前提：本地已能免密 SSH 登录服务器（已完成 ssh-copy-id）；`site/.deploy.env` 已按
`site/.deploy.env.example` 填好（该文件不进 git，密码不写入任何文件）。

## 首次部署

1. DNS：确认域名 A 记录指向服务器 IP：`dig +short simiam.com`
2. 服务器初始化（幂等，可重复执行）：`bash site/scripts/server-setup.sh`
3. 首次发布：HTTPS 尚未配置时，先把 `site/.deploy.env` 的 `SITE_URL` 临时设为 `http://simiam.com`，再执行 `npm --prefix site run publish`
4. 配置 HTTPS（在服务器上执行，需要人工确认）：
   - 安装 certbot：Ubuntu/Debian 用 `apt install -y certbot python3-certbot-nginx`；
     CentOS/TencentOS 用 `yum install -y certbot python3-certbot-nginx`
   - 签发并自动改写 nginx 配置：
     `certbot --nginx -d simiam.com --agree-tos -m <你的邮箱> --no-eff-email`
   - 注意：配置 HTTPS 后如需重跑 `site/scripts/server-setup.sh`，脚本会检测到 HTTPS 配置并跳过 nginx 配置写入，不会覆盖 certbot 的修改
   - 验证自动续期：`certbot renew --dry-run`
5. 复查：`curl -I https://simiam.com/` 返回 200；http 应 301 到 https
6. 把 `site/.deploy.env` 的 `SITE_URL` 改回 `https://simiam.com`

## 日常发布

`npm --prefix site run publish` —— 内容与类型检查 → 单元测试 → 构建 → rsync 同步 → 健康检查。
rsync 不可用或同步失败时自动 fallback 到部署 Git 通道（仅把 `dist/` 推送到服务器 bare repo，hook 自动 checkout）。
强制验证该通道：`DEPLOY_FORCE_GIT=1 npm --prefix site run publish`

部署 Git fallback 与源码 Git 无关：它不会向 `dreamble` 的 `origin` 推送，也不会把源码放到服务器。源码是否执行 `git push origin` 仍由站主单独决定。

线上健康检查失败会以非零状态退出，并给出 nginx、DNS、HTTPS 排查方向；即使文件同步完成，也不会把网站不可访问报告为发布成功。

## 安全加固（建议，是否执行由站主决定）

SSH 密钥已配好后，禁用密码登录（对所有用户生效，仅密钥可登录）可大幅降低被爆破风险：

    # 服务器上 /etc/ssh/sshd_config 中设置：
    PasswordAuthentication no
    # 然后 systemctl reload sshd

注意：执行前务必先确认密钥登录正常，否则会把自己锁在门外。

## 回滚

站点是纯静态且内容真源在源码 Git。只回滚站点内容时，从仓库根目录执行：

```bash
git restore --source=<旧提交> -- site/content/
npm --prefix site run publish
```

第一条命令会修改工作区，请先用 `git diff -- site/content/` 核对回滚范围，再发布并按正常流程提交这次回滚。
