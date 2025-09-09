## Firewall (ufw)
```bash
sudo apt-get install -y ufw
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 8501/tcp   # direct Streamlit (optional if using Nginx)
sudo ufw enable
sudo ufw status
```
