# Гарантии доставки сообщений

### Модель системы

- Сервис DeliverySender
    - API
        - POST: /api/message
            1. Генерация messageId (GUID)
            2. Регистрация метрики delivery_messages_sent_total (label: message_id)
            3. HTTP-вызов
                - POST: http://delivery-receiver/api/message
                - Body: { "messageId" : messageId }
                - Http client timeout = 1s
- Сервис DeliveryReceiver
    - API
        - POST: /api/message
        - Body: { "messageId" : messageId }
            1. Регистрация метрики delivery_messages_received_total (label: message_id)
- Основные метрики
    - Dashboard Delivery Guarantees
    - Отправленные сообщения (по message_id)
    - Полученные сообщения (по message_id)
    - Количество потерянных сообщений
    - Количество повторно обработанных сообщений

### Сценарий 1. Отсутствие проверок

1. Запустить платформу с сервисами DeliverySender и DeliveryReceiver
2. Запустить генерацию трафика на DeliverySender
```
curl -X 'POST' \
  'http://localhost:5050/api/traffic/start' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -d '{
  "targetUrl": "http://delivery-sender/api/message",
  "rps": 3,
  "durationSeconds": 300
}'
```
3. Наблюдать метрики
    - Messages Sent (unique) = Messages Received (unique)
    - Количество отправленных сообщений совпадает с количеством принятых сообщений
4. Запустить замедление сети
```
curl -X 'POST' \
  'http://localhost:5050/api/failures/network/delay' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -d '{
  "containerName": "delivery-receiver",
  "delayMs": 1000,
  "durationSeconds": 30,
  "jitterMs": 100
}'
```
5. Наблюдать метрики
    - Messages Sent (unique) > Messages Received (unique)
    - Появились потерянные пакеты