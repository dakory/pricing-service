# Задание: реализовать Airbnb collector adapter для AWS Lambda

## Область работы

Реализовать внутреннюю логику `lambda_scraper/lambda_function.py`, не изменяя
механизм получения callback token, отправку callback и Terraform без отдельного
согласования.

Collector поддерживает две операции:

- `calendar` — один запрос календаря и разбор всех возвращённых дней;
- `quotes` — получение явно заданного backend списка stay-котировок.

Collector не выбирает точный/грубый метод, не строит интервалы и не рассчитывает
цену дня. Эти обязанности остаются у backend.

## Зафиксированные примеры

Все параметры захваченных запросов сохранены буквально:

- календарный request:
  `tests/fixtures/airbnb/availability_calendar_request.json`;
- минимальный календарный response:
  `tests/fixtures/airbnb/availability_calendar.json`;
- price request:
  `tests/fixtures/airbnb/stay_checkout_request.json`;
- минимальный price response:
  `tests/fixtures/airbnb/stay_checkout.json`.

Request fixtures содержат endpoint path, operation name, persisted-query SHA,
variables, API key, client version и полный набор захваченных headers. Response
fixtures намеренно очищены от повторяющихся дней, UI-данных и платёжных токенов.

Захваченный checkout fixture использует одного взрослого. Production-запросы
должны формироваться с `numberOfAdults=4`; остальные guest counts равны нулю.

## Calendar request

Использовать `GET /api/v3/PdpAvailabilityCalendar/{sha}` с:

```text
operationName = PdpAvailabilityCalendar
locale = en
currency = IDR
count = 12
listingId = event.external_listing_id
month/year = начало требуемого календарного горизонта
returnPropertyLevelCalendarIfApplicable = false
```

`extensions.persistedQuery` и headers брать из request fixture. Динамические
listing/date/query значения формировать из event, не копировать пример listing.

Разбирать:

```text
data.merlin.pdpAvailabilityCalendar.calendarMonths[].days[]
```

Для каждого дня вернуть:

```json
{
  "stay_date": "2026-08-03",
  "bookable": true,
  "min_nights": 1
}
```

Mapping:

- `stay_date = calendarDate`;
- `bookable = (bookable is true)`; `false` и `null` становятся `false`;
- `min_nights = minNights` для бронируемой даты;
- отсутствие корректного `minNights >= 1` при `bookable=true` — структурная
  ошибка всего calendar result.

Не возвращать `available`, `availableForCheckin`, `availableForCheckout`,
`maxNights`, `price.localPriceFormatted` и `__typename`.

## Checkout request

Использовать `GET /api/v3/stayCheckout/{sha}`. Backend передаёт готовые
`quote_id`, `check_in_date` и `check_out_date`. Подставить их в
`variables.input`, сформировать `productId` для external listing и установить:

```text
numberOfAdults = 4
numberOfChildren = 0
numberOfInfants = 0
numberOfPets = 0
guestCurrencyOverride = IDR
locale = en
currency = IDR
```

Остальная форма variables, persisted-query SHA и headers определена в
`stay_checkout_request.json`.

Успешным считать только response, где:

```text
data.presentation.stayCheckout.sections.temporaryQuickPayData
  .bootstrapPayments.productPriceBreakdown.status.statusCode == "OK"
```

Извлечь сумму из:

```text
data.presentation.stayCheckout.sections.temporaryQuickPayData
  .bootstrapPayments.productPriceBreakdown.priceBreakdown
  .total.total.amountMicros
```

и валюту из соседнего `currency`. Преобразовать micros в Decimal-совместимую
строку IDR делением на `1_000_000`. Не разбирать `amountFormatted` и
локализованные titles. Не вычитать `ACCOMMODATION`, `SMART_PROMOTION`, налоги
или дополнительные сборы: `TOTAL` уже является используемой гостевой суммой.

## Вход Lambda: calendar

```json
{
  "operation": "calendar",
  "run_id": 42,
  "competitor_listing_id": 7,
  "external_listing_id": "1721566348393412409",
  "listing_url": "https://www.airbnb.com/rooms/1721566348393412409",
  "start_date": "2026-08-01",
  "month_count": 12
}
```

Callback URL и Bearer token по-прежнему берутся существующим механизмом Lambda
из environment и SSM; event не может их переопределять.

## Calendar callback

```json
{
  "operation": "calendar",
  "run_id": 42,
  "external_listing_id": "1721566348393412409",
  "status": "succeeded",
  "calendar_days": [
    {
      "stay_date": "2026-08-03",
      "bookable": true,
      "min_nights": 1
    }
  ],
  "scraped_at": "2026-08-01T05:00:00Z",
  "parser_version": "airbnb-calendar-v1",
  "error": null
}
```

Не возвращать частичный календарь при неизвестной или оборванной структуре.

## Вход Lambda: quotes

```json
{
  "operation": "quotes",
  "run_id": 42,
  "batch_id": 9,
  "competitor_listing_id": 7,
  "external_listing_id": "1721566348393412409",
  "quotes": [
    {
      "quote_id": "q_123",
      "check_in_date": "2026-09-09",
      "check_out_date": "2026-09-10"
    }
  ]
}
```

Проверить, что checkout позже check-in, IDs уникальны и размер батча не превышает
конфигурируемый лимит event.

## Quote callback

```json
{
  "operation": "quotes",
  "run_id": 42,
  "batch_id": 9,
  "external_listing_id": "1721566348393412409",
  "status": "partially_succeeded",
  "quotes": [
    {
      "quote_id": "q_123",
      "check_in_date": "2026-09-09",
      "check_out_date": "2026-09-10",
      "adults": 4,
      "total_price": "1700400",
      "currency": "IDR",
      "scraped_at": "2026-08-01T05:01:00Z",
      "parser_version": "airbnb-checkout-v1"
    }
  ],
  "quote_errors": [
    {
      "quote_id": "q_124",
      "code": "quote_request_failed",
      "message": "Upstream quote request failed"
    }
  ],
  "error": null
}
```

Каждый входной `quote_id` должен присутствовать ровно один раз в `quotes` или
`quote_errors`. Ошибка одной котировки не удаляет успешные котировки батча.
Не отправлять полный upstream response, токены или headers в callback и логи.

## HTTP и ошибки

- использовать timeout меньше оставшегося Lambda execution time;
- ограничить retries так, чтобы callback гарантированно успел отправиться;
- считать 403/429 и transport error техническими ошибками, не недоступностью;
- неизвестная JSON-структура calendar — global failure;
- неизвестная структура одной checkout-котировки — quote error;
- response currency должна быть строго `IDR`;
- логировать run/batch/quote ID, HTTP status и длительность, но не API key,
  payment tokens или полный payload;
- не реализовывать CAPTCHA bypass, IP rotation или автоматический поиск новых
  приватных endpoint.

## Тесты

1. Parser календаря проходит минимальный fixture и корректно обрабатывает
   `bookable=true/false/null`.
2. Бронируемая дата без `minNights` вызывает structural failure.
3. Checkout parser извлекает `1700400 IDR` из fixture через `amountMicros`.
4. `SMART_PROMOTION` не применяется повторно поверх `TOTAL`.
5. Все network tests используют fake transport; pytest не обращается к Airbnb.
6. Calendar event и quote event полностью валидируются.
7. Partial quote batch классифицирует каждый quote ID один раз.
8. Callback отправляется при success, partial success и global failure.
9. В логах и callback нет API key и payment quote tokens.
10. `pytest`, `compileall` и `git diff --check` проходят.

## Definition of done

- fixture-тесты зелёные;
- collector реализует оба operation без изменения backend pricing logic;
- production guest count равен четырём взрослым;
- календарь и котировки возвращаются по описанным контрактам;
- Lambda не рассчитывает цену целевой даты;
- отсутствуют реальные HTTP-запросы в automated tests;
- изменения совместимы с Lambda Python 3.11, 256 MB и timeout 60 секунд.
