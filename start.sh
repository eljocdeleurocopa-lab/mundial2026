#!/bin/bash
python /opt/euro2024/manage.py collectstatic --noinput
exec gunicorn --pythonpath /opt/euro2024 mundial2026.wsgi --bind 0.0.0.0:8000
cat > ~/Desktop/mundial2026/start.sh << 'EOF'
#!/bin/bash
python /opt/euro2024/manage.py collectstatic --noinput
exec gunicorn --pythonpath /opt/euro2024 mundial2026.wsgi --bind 0.0.0.0:8000
