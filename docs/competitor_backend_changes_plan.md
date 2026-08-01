# План изменений backend для нового сбора конкурентов

## Результат

FastAPI управляет двухэтапным run, хранит календарь и исходные котировки,
рассчитывает цену каждой даты выбранным методом и предоставляет состояние run
dashboard. Lambda не выполняет бизнес-арифметику.

## 1. Миграция данных

Добавить новую Alembic migration без изменения старых migration-файлов.

### Календарные наблюдения

Адаптировать `competitor_observations` к минимальной семантике:

- оставить `competitor_listing_id`, `scrape_run_id`, `stay_date`;
- заменить неоднозначные `available` и `available_for_checkin` одним
  `bookable`;
- оставить `minimum_stay`, `scraped_at`, `parser_version`;
- оставить рассчитанные `price`, `currency`, `price_method`;
- добавить `collection_mode`: `precise` или `rough`;
- обеспечить уникальность observation внутри run по listing/date;
- сохранить существующие данные, вычислив `bookable` из текущего
  `available_for_checkin`.

### Исходные котировки

Сделать `competitor_stay_quotes` независимыми от одного observation, потому что
одна котировка может использоваться для расчёта другой целевой даты:

- `competitor_listing_id`;
- `scrape_run_id`;
- `check_in_date`;
- `check_out_date`;
- `adults`;
- `currency`;
- `total_price`;
- `scraped_at`;
- `parser_version`;
- небольшой `raw` только для аудита;
- unique constraint по run/listing/check-in/check-out/adults/currency.

Поля `accommodation_subtotal`, `cleaning_fee`, `taxes` и
`other_excluded_fees` больше не участвуют в новой логике. Удалять их только
после миграции нужных исторических данных; допустим переходный nullable-период.

### План цены и батчи

Добавить сущности либо эквивалентные JSON-backed records:

- price target: целевая дата, режим, выбранный метод и ссылки на необходимые
  интервалы;
- scrape batch: operation, status, attempt, ожидаемые quote IDs и ошибка.

Рекомендуются нормализованные таблицы, чтобы callback каждого батча был
идемпотентным и run можно было продолжить после сбоя процесса.

## 2. Контракты API

Обновить `POST /api/competitor-scrapes`:

- сохранить ручной выбор listing/range/force refresh;
- добавить необязательный `collection_mode`;
- без явного режима выбирать `precise` в пределах 60 дней и `rough` дальше;
- создать run в фазе `calendar_queued` и вызвать calendar Lambda.

Обновить `GET /api/competitor-scrapes/{run_id}`:

- возвращать фазу `calendar`, `planning`, `quotes`, `calculating`, `completed`;
- показывать количество календарных дней, price targets, батчей, успешных
  котировок и ошибок;
- показывать precise/rough и пропущенные свежие даты.

Разделить внутренний callback на типизированные payload либо два endpoint:

- calendar callback;
- quote-batch callback.

Оба используют существующий Bearer token и constant-time comparison.

## 3. Calendar callback

Принимать:

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

Валидировать listing, ожидаемый run, уникальность дат, полный непрерывный
диапазон ответа и обязательный `min_nights` для `bookable=true`. Значение
`bookable=null` parser уже должен привести к `false`.

После атомарной записи backend строит quote plan. Недоступные даты сохраняются
с `price=null` и `price_method=unavailable`.

## 4. Построение quote plan

Использовать формулы из общей спецификации. Проверять непрерывность требуемых
ночей по сохранённому календарю. Backend выбирает строго один метод на target:

1. `single_night`;
2. `quote_difference_left`;
3. `quote_difference_right`;
4. `minimum_stay_average`;
5. `price_unavailable`, если допустимого интервала нет.

Дедуплицировать интервалы и разбить их на батчи конфигурируемого размера.
Каждому интервалу присвоить стабильный `quote_id`, созданный backend.

## 5. Quote-batch callback

Принимать:

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
  "quote_errors": [],
  "error": null
}
```

Callback должен классифицировать каждый ожидаемый `quote_id` ровно один раз.
Повторный callback с тем же batch ID возвращает идемпотентный успех.
Структурно невалидный payload не создаёт частичных записей внутри батча.

## 6. Расчёт цен

После завершения всех батчей рассчитать targets в backend:

- `single_night`: одна котировка;
- `quote_difference_left/right`: `long_total - short_total`;
- `minimum_stay_average`: `total / min_nights`;
- использовать `Decimal`, не `float`;
- отклонять неположительную разность и переводить target в датированную ошибку;
- дополнительные сборы не вычитать и отдельно не хранить.

Сохранять исходные котировки и рассчитанную цену в одной backend-транзакции
финализации run. Допускается `price=null` при успешно сохранённой доступности.

## 7. Freshness и расписание

Заменить единое 24-часовое правило режимными правилами:

- календарь и precise price: свежие в пределах 24 часов;
- rough price: обновляются ежемесячно;
- `force_refresh` игнорирует freshness;
- календарная свежесть и ценовая свежесть учитываются отдельно.

Добавить scheduler jobs:

- ежедневный календарь;
- ежедневный precise horizon 60 дней;
- ежемесячный rough horizon;
- advisory lock, исключающий пересекающиеся работы одного listing.

Бизнес-даты рассчитывать в `Asia/Makassar`, не через локальную timezone EC2.

## 8. Совместимость pricing engine и dashboard

Обновить загрузку competitor observations:

- доступность берётся из последнего календарного наблюдения;
- цена берётся из последнего успешного price observation;
- отсутствие цены не превращает `bookable` в `false`;
- показывать collection mode, price method и freshness.

Dashboard должен показывать отдельный прогресс calendar и quote batches,
частичные ошибки и возможность force refresh.

## 9. Тесты

- migration upgrade/downgrade и сохранность старых наблюдений;
- календарная schema и `null → false` на стороне parser contract;
- левая/правая формулы без off-by-one;
- непрерывность интервалов и average fallback;
- дедупликация quote intervals;
- Decimal-конверсия `amountMicros`;
- partial batch, retry и idempotency;
- mode-aware freshness и граница 60 дней в WITA;
- календарная доступность сохраняется при ошибке цены;
- полный интеграционный путь с fixture без внешнего HTTP.

## 10. Порядок реализации

1. Модели и migration.
2. Pydantic callbacks и unit-тесты расчёта.
3. Calendar callback и quote planning.
4. Quote batching, callback и финализация.
5. Scheduler и freshness.
6. Dashboard status.
7. Интеграционный fixture-тест.
