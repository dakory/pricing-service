# План доведения Calendar до полной функциональности

Источник этого плана — текущий аудит Calendar и согласованные комментарии к
нему. Исторический план redesign в этот документ не входит.

## 1. Реальный competitor scrape

Кнопка `Refresh competitor data` должна запускать настоящий granular scrape.
Перед запуском открывается дополнительное окно настройки:

- competitor listing;
- дата начала;
- дата окончания;
- `Force refresh`, по умолчанию выключен;
- пояснение максимального диапазона;
- список дат, которые будут пропущены из-за freshness window 24 часа.

Только кнопка подтверждения в этом окне вызывает `POST /api/competitor-scrapes`.
Кнопка в Actions лишь открывает окно и не запускает scrape напрямую.

После создания run Calendar показывает только состояние текущего действия
(`Launching`, `Running`, `Completed`, ошибка). Список и подробности runs на
странице Calendar не отображаются; это остаётся задачей Activity.

## 2. Отсутствующие цены

Если для загруженной даты нет Hostex current price, показывать `—`.

Запрещено использовать синтетический fallback из прототипа (`price(base, i)`)
или любые другие искусственные значения. Отсутствие recommendation также
отображается как отсутствие значения, а не как нулевая цена.

## 3. Недоступные даты

Недоступная дата остаётся в календаре и участвует в выделении диапазона. Она:

- визуально приглушается в стиле Airbnb;
- не показывает цену продажи как доступную;
- не становится отдельным препятствием для выбора диапазона;
- пропускается при сохранении price assignment;
- не получает recommendation, override или anchor;
- не учитывается в количестве реально изменяемых дат.

При сохранении диапазона backend должен принимать общий диапазон, но создавать
изменения только для доступных дат. Если весь диапазон недоступен, операция
завершается понятным сообщением без частичного ошибочного результата.

`inventory` и `minimum_stay` пока не выводятся отдельными полями интерфейса.
Они используются только для определения доступности и расчёта.

## 4. Глобальные bounds и rounding

Добавить в глобальную pricing configuration:

- `minimum_price`;
- `maximum_price`;
- `rounding_increment`.

Для каждого поля действует наследование:

```text
global → pricing group → property
```

Unset означает inheritance, явное значение означает override. Effective settings
API возвращает значение и источник (`global`, `group`, `property`).

Global settings должны действительно сохранять эти значения в базе. Property и
pricing group panels должны позволять оставить наследование или задать override.
Значения, отображаемые как `Global: ...`, не должны быть фиктивными
placeholder-ами.

## 5. Date-level Suggest prices и ручная цена

При выделении диапазона пользователь задаёт цену и выбирает режим:

### Suggest prices ON

- цена сохраняется как manual base anchor;
- recommendation продолжает применяться поверх этой цены;
- urgency, rounding и bounds продолжают работать.

### Suggest prices OFF

- цена сохраняется как hard override;
- recommendation для этой даты не применяется;
- значение является финальной ценой.

У каждого property есть default `Suggest prices`. Для отдельной даты может быть
задан nullable date-level override. Если он не задан, используется значение
property.

Backend должен хранить одну актуальную date-level price assignment на пару
`property_id + stay_date`, содержащую:

- цену;
- режим (`manual_base` или `fixed_price`);
- nullable `suggest_prices`;
- причину;
- timestamps.

Создание диапазона выполняется идемпотентным upsert. Недоступные даты не
изменяются. Существующие override/anchor данные мигрируются без потери цены,
режима и причины.

Ячейки с assignment получают отдельный marker. По нажатию пользователь видит
источник, режим, цену и может изменить или удалить assignment. Удаление
возвращает дату к property-level behavior и обычному pricing engine.

## 6. Actions и runs

`Fetch current prices`, `Generate price recommendations` и `Apply prices` должны:

- создавать backend run;
- использовать serialized lock;
- предотвращать параллельный запуск того же ресурса;
- гарантировать terminal status вместо вечного `running`;
- обновлять календарь после завершения.

На Calendar не показывается список runs и отдельная история. Отображается только
состояние текущей кнопки и результат операции. Времена последних действий
загружаются из `/api/runs`, а не задаются константами.

Перед `Apply prices` показывается подтверждение с количеством properties и
доступных дат, которые будут изменены. Недоступные даты не включаются.

## 7. Tooltips и валидация

Добавить подсказки к полям и действиям, где смысл не очевиден:

- guest-to-host factor;
- market positioning factor;
- minimum competitor count;
- minimum/maximum price;
- rounding increment;
- urgency adjustment;
- `Suggest prices`;
- price override;
- manual base anchor;
- unavailable date.

Валидация должна быть inline и стилистически соответствовать design system:

- min/max и положительные значения;
- целые значения там, где они обязательны;
- urgency range boundaries;
- запрет пересекающихся диапазонов;
- не более 10 urgency rules;
- disabled Save при наличии ошибок;
- ошибки backend рядом с соответствующим полем, а не только в Toast.

## 8. Thumbnail fallback

Если thumbnail не загрузился, изображение заменяется простым серым блоком того
же размера. Layout не должен менять размеры или положение property row.

## 9. Проверка готовности

Перед завершением работ проверить в браузере:

1. Refresh competitor data открывает настройки и после подтверждения создаёт
   реальный scrape run.
2. Дата без цены показывает `—`.
3. Недоступная дата входит в диапазон, но не изменяется после Save.
4. Global bounds сохраняются и наследуются в group/property.
5. Suggest ON создаёт anchor, Suggest OFF создаёт fixed override.
6. Date-level Suggest override имеет приоритет над property default.
7. Existing assignment можно изменить и удалить.
8. Apply показывает подтверждение.
9. Ошибки валидации отображаются inline.
10. Broken thumbnail заменяется серым placeholder без скачка layout.

## Нерешённые вопросы

Для реализации можно использовать следующие допущения без дополнительного
согласования:

- date-level assignment заменяет предыдущую assignment на той же дате;
- удаление date-level `Suggest prices` возвращает property default;
- unavailable определяется существующим BookingSite inventory;
- подробный run history остаётся только на Activity.
