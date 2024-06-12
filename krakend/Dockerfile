FROM devopsfaith/krakend

RUN mkdir -p /etc/krakend/settings /etc/krakend/templates
# Скопировать все файлы в директорию /etc/krakend
COPY . /etc/krakend/
# Проверить конфигурацию
RUN FC_ENABLE=1 \
    FC_SETTINGS="/etc/krakend/settings" \
    FC_TEMPLATES="/etc/krakend/templates" \
    krakend check -t -d -c /etc/krakend/sample.json

# Запуск Krakend с Flexible Configuration
ENTRYPOINT ["sh", "-c", "FC_ENABLE=1 FC_SETTINGS=/etc/krakend/settings FC_TEMPLATES=/etc/krakend/templates krakend run -c /etc/krakend/sample.json"]
