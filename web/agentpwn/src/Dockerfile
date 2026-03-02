FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir autogenstudio

# Create unprivileged user
RUN useradd -m -s /bin/bash ctf

# SUID privesc vector — "backup utility" left by sysadmin
RUN cp /usr/local/bin/python3.11 /usr/local/bin/python-backup \
    && chmod u+s /usr/local/bin/python-backup \
    && mkdir -p /opt/maintenance \
    && printf '#!/usr/local/bin/python-backup\n# Maintenance backup script - runs as root\nimport shutil, sys\nshutil.copy2(sys.argv[1], "/tmp/backup")\n' > /opt/maintenance/backup.py \
    && chmod 755 /opt/maintenance/backup.py \
    && printf 'System maintenance tools.\npython-backup is used by cron for nightly backups.\n' > /opt/maintenance/README.txt

# App data directory
RUN mkdir -p /app/data && chown -R ctf:ctf /app

EXPOSE 8081

# Write flag at runtime (FLAG env var injected by whale), then drop to ctf user
CMD ["sh", "-c", \
     "echo \"CHC{ag3nt_t00ls_ar3_just_ex3c_in_d1sgu1se_${FLAG}}\" > /root/flag.txt && \
      chmod 400 /root/flag.txt && \
      exec su -s /bin/bash ctf -c 'autogenstudio ui --host 0.0.0.0 --port 8081 --appdir /app/data'"]
