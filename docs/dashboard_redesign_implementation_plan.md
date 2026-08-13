# План реализации нового dashboard

## 1. Итоговая структура

```text
/login
/                    → Calendar
/activity            → Activity
/competitors         → Competitor freshness
```

Старые страницы удаляются или перенаправляются:

```text
/hostex       → /
/properties   → /
/runs         → /activity
/status       → /activity
```

Навигация:

```text
Portfolio
  Calendar
  Competitor freshness
  Activity
```

На первом этапе разделы Messages и другие демонстрационные разделы из прототипа не переносятся.

## 2. Общая дизайн-система

### Перенос foundation

В production dashboard переносятся:

- цветовые токены;
- типографика;
- spacing;
- radii;
- shadows;
- glass surfaces;
- motion;
- logo asset;
- Inter для интерфейса;
- Roboto Mono для цен, процентов, дат и технических значений.

Источником истины считаются фактические CSS tokens и prototype из `nicer.homes_design_system/ui_kits/host-dashboard`.

### Production-компоненты

Компоненты из design system переводятся в TypeScript:

```text
Button
IconButton
Card
Badge
Tag
Input
Select
InputWithSelectField
Checkbox
Radio
Switch
LinkedValue
Dialog
Toast
Tooltip
Tabs
```

Дополнительно создаются прикладные компоненты:

```text
AppShell
Sidebar
PricingCalendar
CalendarCell
PriceExplanationTooltip
PropertySettingsPanel
PricingGroupPanel
GlobalSettingsDialog
ActionsDialog
RangeSelectionToolbar
UrgencyRulesEditor
ActivityItem
CompetitorTable
ScrapeLaunchDialog
```

Inline styles прототипа постепенно переносятся в CSS modules или общий production stylesheet. Для иконок используется пакет Lucide, а не внешние URL с CDN.

## 2a. Backend foundation до переноса интерфейса

Frontend не должен напрямую собирать календарь из нескольких старых endpoint’ов.
Сначала backend предоставляет стабильный read/write-контракт, который скрывает
структуру Hostex и текущую схему Pricing Engine.

### Миграции и доменная модель

- Проверить актуальную production schema и добавить миграции только для
  отсутствующих полей/индексов; существующие observations, recommendations,
  overrides, anchors, runs и Hostex mappings не терять.
- Зафиксировать связь `pricing_group → property → BookingSite listing` и
  выбрать один active BookingSite listing на property для календаря.
- Проверить индексы для чтения календаря:
  `hostex_calendar_days(listing_id, channel_type, stay_date)`,
  `recommendations(property_id, stay_date)`, `overrides(property_id, start_date,
  end_date)` и runs по `kind, started_at`.
- Даты и timestamps хранить по существующим правилам (UTC/бизнес-таймзона), а
  API всегда возвращает ISO 8601.
- Миграция должна иметь проверяемый report: row counts до/после, orphan
  mappings и duplicate BookingSite listings.

### Effective settings service

Создать единый backend-сервис `get_effective_pricing_settings(property_id)`,
который возвращает итоговые значения и provenance каждого поля:

```json
{
  "minimum_competitor_count": {"value": 10, "source": "global"},
  "urgency_adjustment_enabled": {"value": true, "source": "pricing_group"},
  "urgency_adjustments": {"value": [], "source": "property"}
}
```

- Порядок наследования: global → pricing group → property.
- `null`/unset означает inherit; пустой собственный список urgency rules
  означает намеренно пустой список, а не inherit.
- Один resolver используется pricing engine, Calendar API и settings panels;
  frontend не реализует наследование самостоятельно.
- Settings response возвращает raw override и effective value, чтобы UI мог
  показать `Global`, `Group` или `Property override`.
- Все payloads проходят Pydantic validation (`extra=forbid`), включая диапазоны
  urgency rules и лимит в 10 правил.

### Aggregated Calendar API

Реализовать `GET /api/pricing-calendar?start=YYYY-MM-DD&end=YYYY-MM-DD` как
единственный источник данных для Calendar:

- авторизация через существующую session dependency;
- диапазон inclusive, `start <= end`, максимум 60 дней на запрос;
- default — от `today` до `today + 43`: 30 основных дней, начиная с today,
  плюс 14 дней forward buffer (всего 44 даты);
- 7 дней backward buffer не показываются при первом открытии: они подгружаются
  только при прокрутке в прошлое, чтобы первая видимая дата всегда была today;
- возвращать active properties, pricing groups и все даты, включая unavailable;
- для каждой даты объединять только BookingSite inventory/price, availability,
  recommendation, published value, override/anchor и warnings;
- отсутствие recommendation не является ошибкой: `recommended_price=null`;
- не запускать import или pricing calculation во время чтения;
- не возвращать данные других каналов и не раскрывать Hostex tokens.

Минимальный response для каждой ячейки:

```json
{
  "property_id": 1,
  "pricing_group_id": 1,
  "stay_date": "2026-08-20",
  "available": true,
  "inventory": 1,
  "minimum_stay": 3,
  "current_price": 1500000,
  "recommended_price": 1400000,
  "published_price": null,
  "difference": -100000,
  "difference_percentage": -0.0667,
  "override": null,
  "anchor": null,
  "warnings": [],
  "explanation": {}
}
```

Добавить read responses для panel data (properties/groups/global settings),
либо расширить существующие responses так, чтобы они возвращали effective
settings и provenance без дополнительных N+1 запросов.

### BookingSite-only fetch

Добавить отдельную операцию `POST /api/imports/hostex/booking-site`:

- выбирать только listings с `channel_type=BookingSite` и active property;
- запрашивать календарь в существующих 20-listing batches, но не reservations,
  properties, listings или calendars остальных каналов;
- сохранять `price`, inventory и minimum stay идемпотентно;
- записывать `Run(kind=import_)` с summary (`scope=booking_site`, listing count,
  date range, fetched rows, skipped rows, errors);
- не пересчитывать recommendations автоматически;
- корректно завершать run при частичной ошибке, не оставляя `running`;
- возвращать run id, а UI получает статус через `/api/runs` polling.

Полный `POST /api/imports/hostex` остаётся системной операцией и не используется
при загрузке Calendar.

### Job и read-after-write semantics

- Сохранить advisory/serialized locking для import, optimize и publish.
- Повторный запуск того же типа при активном run возвращает `409` с id текущего
  run, а не создаёт невидимую блокировку.
- Для каждого run гарантировать terminal status (`succeeded`,
  `partially_succeeded`, `failed`, `skipped`) и `finished_at` в `finally`.
- Добавить единый `GET /api/runs/{run_id}` для polling деталей и ошибок.
- После успешного BookingSite fetch и Generate recommendations frontend явно
  инвалидирует cache; backend не обещает синхронную публикацию Hostex.

### Write contracts и безопасность

- Удалить из dashboard/backend mode setting, activation date и связанные
  conditional guards; приложение работает в единственном обычном режиме.
- Сохранить CSRF protection для всех mutating endpoints и session protection
  для reads.
- Привести overrides и manual anchors к единым range payloads с timezone-safe
  датами, обязательной причиной и проверкой unavailable dates.
- `POST /api/pricing/run` возвращает run id и summary; долгий расчёт не должен
  удерживать HTTP request дольше gateway timeout.
- Ошибки API имеют стабильную форму `{code, message, details, run_id?}` без
  секретов и сырых Hostex responses.

### Backend foundation tests

- migration smoke test на копии текущей базы с проверкой row counts и mappings;
- resolver tests для global/group/property, unset против пустого списка и
  provenance;
- Calendar API tests на все dates, unavailable dates, BookingSite-only data,
  null recommendation, range limit и отсутствие N+1 запросов;
- import tests на фильтр канала, batching, idempotency, partial failure и
  terminal run status;
- lock tests на повторный запуск и возврат existing run id;
- authorization/CSRF/schema tests для settings, overrides, anchors и runs;
- contract fixtures для response, который будет потреблять новый dashboard.

## 3. Calendar

Это главный экран приложения. Он объединяет:

- бывший Portfolio calendar;
- Hostex calendars;
- Properties;
- pricing groups;
- global pricing settings;
- price overrides;
- manual date-level anchors;
- pricing actions.

### Структура календаря

```text
Pricing group
  Property
  Property

Pricing group
  Property
```

Одна строка — одно property, как в прототипе.

Слева:

- название property;
- дополнительная короткая информация;
- visual marker;
- поиск;
- sticky column.

Сверху:

- month selector;
- Today;
- sticky month headings;
- sticky weekday/date headings;
- Global settings;
- Actions.

По краям календаря сохраняются предусмотренные prototype affordances:

- стрелки `Scroll earlier` и `Scroll later`;
- мягкие fade/scroll shadows, показывающие наличие продолжения;
- горизонтальный scroll с сохранением sticky property column.

### Содержимое ячейки

Основная крупная величина — текущая BookingSite цена.

При наличии recommendation показывается компактный индикатор:

```text
рекомендованная цена
изменение в %
```

Цвет используется сдержанно для повышения, снижения, override, warning и selected range. Полный explanation внутри ячейки не отображается.

### Недоступные даты

Недоступность определяется по BookingSite inventory и reservations.

Такие даты:

- остаются видимыми;
- визуально перечёркнуты или приглушены как в Airbnb;
- не показываются как доступные для продажи;
- не участвуют в range selection;
- не позволяют создать override;
- не имеют recommendation.

### Hover explanation

Explanation появляется только при наведении на ячейку и содержит:

- источник anchor;
- текущую Airbnb median;
- число конкурентов и порог;
- guest-to-host factor;
- estimated host median;
- positioning factor;
- base price;
- urgency range и adjustment;
- raw price;
- rounded price;
- bounds;
- final price;
- current BookingSite price;
- абсолютную и процентную разницу;
- override, если он присутствует.

Tooltip автоматически выбирает положение сверху или снизу и не выходит за viewport. Для touch-устройств то же содержимое открывается по нажатию.

## 4. Lazy loading и виртуализация дат

### Рабочее окно

Основной размер окна — 30 дней.

Buffer:

```text
7 дней назад
14 дней вперёд
```

Начальная загрузка:

```text
today
    →
today + 29
    →
today + 43
```

Итого начальный диапазон — 44 даты. При движении влево окно расширяется на
прошлые 30-дневные сегменты с buffer до 7 дней.

### Прокрутка

При приближении к правому краю:

- загружается следующий 30-дневный сегмент;
- сохраняется buffer 14 дней впереди;
- полученные данные добавляются в client cache.

При приближении к левому краю:

- загружается предыдущий 30-дневный сегмент;
- сохраняется buffer 7 дней позади.

Уже загруженные диапазоны повторно не запрашиваются.

### Виртуальный DOM

В DOM находятся видимые даты, 7 дней слева и 14 дней справа. Ширина виртуального canvas сохраняет правильную позицию scroll. Размер DOM не растёт при длительной прокрутке.

### Фактический горизонт

UI воспринимается как infinite calendar, но бизнес-горизонт ограничен:

```text
7 дней в прошлом
365 дней в будущем
```

За пределами 365 дней recommendation пока не рассчитывается. Календарь явно завершается на границе pricing horizon.

## 5. API календаря

Текущий `/api/calendar` отдаёт только существующие recommendations. Для нового интерфейса нужен агрегированный endpoint:

```text
GET /api/pricing-calendar?start=...&end=...
```

Он возвращает каждую дату для каждого active property:

```json
{
  "property_id": 1,
  "pricing_group_id": 1,
  "stay_date": "2026-08-20",
  "available": true,
  "inventory": 1,
  "minimum_stay": 3,
  "current_price": 1500000,
  "recommended_price": 1400000,
  "published_price": null,
  "difference": -100000,
  "difference_percentage": -0.0667,
  "override": null,
  "anchor": {},
  "warnings": [],
  "explanation": {}
}
```

Endpoint должен:

- объединять Hostex calendar и recommendations;
- включать unavailable dates;
- поддерживать диапазонные запросы;
- возвращать grouping metadata;
- не запускать Hostex import;
- не выполнять pricing calculation во время чтения;
- ограничивать один запрос разумным диапазоном, например 60 днями.

## 6. Property settings panel

По нажатию на строку property открывается правая панель, максимально близкая к прототипу.

### General

- property name;
- pricing enabled;
- pricing group;
- BookingSite listing ID;
- Hostex mapping.

В заголовке панели также доступны inline pencil affordance для property group,
keyboard-accessible group picker и close control.

### Base price

- Market / Manual;
- manual base price;
- market positioning factor;
- minimum competitor count.

Для positioning factor добавляется info-tooltip с примерами `1.1` — 10% выше
рынка и `0.9` — 10% ниже рынка.

### Urgency

- inherited / custom / disabled;
- visual urgency chart;
- список диапазонов;
- добавление и удаление rules;
- максимум 10 rules;
- валидация пересечений;
- визуальное отображение gaps;
- клик по gap для добавления нового периода;
- slider для изменения скидки;
- hover label с диапазоном дней и процентом.

### Bounds

- minimum price;
- maximum price;
- pricing step.

### Inheritance

Каждое наследуемое поле показывает источник:

```text
Global
Group: Uluwatu villas
Property override
```

Для числовых и других наследуемых настроек используется `InputWithSelectField`.
Он объединяет редактируемое значение с выбором унаследованного значения и должен
показывать источник настройки прямо в control:

```text
Global: 10
Group: Uluwatu villas · 8
Property override · 6
```

Компонент поддерживает keyboard navigation, custom value, выбор option и
визуальный `LinkedValue`. Это основной control для `minimum_competitor_count`,
`market_positioning_factor`, `guest_to_host_price_factor`, manual base price и
urgency enabled, если поле наследуется.

Если значение наследуется, оно отображается через `LinkedValue`. Пользователь может оставить inherited value, задать property override или вернуть поле к inheritance.

Кнопки:

```text
Cancel
Save property
```

После сохранения отображается toast, строка обновляется, а если настройки влияют на формулу — предлагается повторно сгенерировать recommendations.

## 7. Pricing groups

Строка pricing group кликабельна и открывает правую group panel.

В ней:

- редактируемое название с inline pencil affordance;
- количество properties;
- chips со всеми properties в группе;
- minimum competitor count;
- competitor URLs;
- effective inherited settings;
- переход к Competitor freshness;
- сохранение изменений.

Создание новой группы переносится в отдельный dialog. Property перемещается между группами через property panel.

## 8. Global settings

Открываются через кнопку `Global settings`, как в прототипе.

Содержимое:

- base price mode;
- manual base price;
- guest-to-host factor;
- market positioning factor;
- minimum competitor count;
- urgency enabled;
- urgency rules.

Prototype-specific behavior to preserve:

- segmented Market median / Manual selector;
- conditional manual base field in Manual mode;
- conditional market positioning and competitor threshold fields in Market mode;
- urgency section titled around discounts by days left until stay;
- bounds and rounding section;
- right-side panel with scrollable body and sticky footer Save action;
- dark scrim and blur behind the panel.

В prototype bounds и rounding также присутствуют в Global settings. Текущая
backend-модель хранит `min_price`, `max_price` и `rounding_increment` на property,
поэтому на первом этапе это визуально отражается в property panel; перенос bounds
на global/group inheritance потребует отдельного backend-изменения и не должен
возникать скрыто в ходе frontend-переноса.

Формула pricing отображается рядом в компактном виде:

```text
anchor
× positioning
× urgency
→ rounding
→ bounds
```

## 9. Range selection и overrides

Поведение максимально повторяет prototype.

### Выбор

- первый клик задаёт начало;
- второй — конец диапазона;
- диапазон может включать несколько дат;
- диапазон может включать несколько properties, как в prototype;
- unavailable dates не выбираются;
- Escape снимает selection.

В панели явно отображаются выбранный диапазон и количество properties, чтобы действие было проверяемым до сохранения.

### Context toolbar

После выбора появляется toolbar:

```text
Property
Date range
Number of nights

Set price override
Set manual base anchor
Clear selection
```

В prototype выбранный диапазон открывает правую contextual panel с close
control, nightly price input с `Rp` prefix и accent Save button. На production
этот же паттерн используется для выбора операции (price override или manual
base anchor), обязательной причины и подтверждения диапазона.

### Price override

Создаёт hard override:

- фиксированная final price;
- причина обязательна;
- bypass urgency, rounding и bounds.

### Manual base anchor

Создаёт date-level base anchor:

- urgency продолжает применяться;
- rounding и bounds применяются;
- причина обязательна.

### Existing values

Ячейки с override или manual anchor получают отдельный marker. По нажатию можно посмотреть источник, изменить или удалить значение.

## 10. Actions menu

Сохраняется структура prototype.

Actions открывается как right-side drawer с отдельными action blocks. Каждый
block содержит кнопку, loading label и строку последнего запуска (`Last fetched`,
`Last refreshed`, `Last generated`, `Last applied`).

### Fetch current prices

Вызывает отдельный облегчённый Hostex import:

- только BookingSite calendars;
- price;
- inventory;
- minimum stay;
- без календарей остальных каналов.

Под кнопкой отображается:

```text
Last fetched: 2 hours ago
```

После выполнения текущие цены обновляются, calendar client cache инвалидируется и показывается toast. Recommendations автоматически не пересчитываются.

Полный Hostex import properties/listings/reservations остаётся фоновой системной операцией.

### Fetch competitor prices

Переход или запуск competitor collection workflow с отображением времени последнего сбора.

### Generate recommendations

- запускает pricing run в обычном режиме расчёта;
- показывает progress;
- после завершения обновляет calendar data;
- показывает количество рекомендаций;
- не изменяет Hostex до отдельного подтверждения Apply recommendations.

### Apply recommendations

Используется отдельный confirmation dialog с количеством дат и properties,
диапазоном, итоговыми изменениями и обязательным явным подтверждением. После
подтверждения выполняется publish run и результаты проверяются через Hostex
reconciliation.

## 11. Activity

Страница остаётся простой и использует `/api/runs`.

Визуально Activity повторяет prototype: вертикальный feed компактных glass
cards с цветной точкой статуса, типом операции, scope, коротким detail,
status badge и relative time. Demo events полностью заменяются реальными runs.

Типы преобразуются только на уровне отображения:

```text
import_      → Price fetch
scrape       → Competitor sync
optimize     → Recommendations generated
publish      → Price update
reconcile    → Hostex verification
```

Карточка содержит:

- тип;
- scope, если его можно определить из summary;
- короткое описание;
- status badge;
- relative time;
- раскрываемые технические details;
- error.

Статусы:

```text
Completed
Running
Needs review
Failed
Skipped
```

Новая event-модель и существенные backend-изменения не добавляются. Running jobs обновляются polling-запросом.

## 12. Competitor freshness

Текущая функциональность сохраняется.

Новый layout:

- заголовок и summary;
- фильтр по pricing group;
- компактная таблица или список competitors;
- last fetched;
- minNights;
- precise/rough;
- price method;
- latest error;
- status badge.

Действия:

- выбрать competitor;
- date range;
- automatic / precise / rough;
- force refresh;
- запустить сбор;
- видеть progress по batches;
- видеть skipped dates;
- видеть результат.

Ручной запуск открывается в dialog. Recent scrape runs показываются ниже либо через ссылку на Activity.

Страница использует тот же AppShell, card, badge, input/select, dialog, toast и
статусные цвета, что Calendar и Activity. Технические ошибки остаются
доступными, но не перегружают основной список.

## 13. Login

Новая страница авторизации:

- centered glass card;
- nicer wordmark;
- email;
- password;
- primary sign-in button;
- restrained inline error;
- loading state;
- keyboard submit;
- корректная работа cookies и CSRF;
- без sidebar.

Используются существующие endpoints:

```text
POST /api/auth/login
GET /api/auth/session
POST /api/auth/logout
```

Logout добавляется в нижнюю часть sidebar.

## 14. Responsive behavior

Приоритет — desktop, поскольку calendar требует ширины.

### Desktop

- постоянный или collapsible sidebar;
- sticky property column;
- right settings panel;
- hover explanation.

### Tablet

- collapsed sidebar;
- settings panel поверх calendar;
- touch explanation по нажатию.

### Mobile

- calendar сохраняет horizontal scroll;
- property column становится компактнее;
- panels открываются полноэкранно;
- hover заменяется tap;
- массовое редактирование остаётся доступным.

Во всех viewport сохраняются prototype interaction details: hover/press
transitions 120–220ms, focus ring, keyboard close/navigation for drawers and
pickers, dark scrim behind dialogs, and no bounce/parallax motion.

## 14a. Content and visual rules

- sentence case для заголовков, navigation и controls;
- короткие декларативные тексты без sales tone и восклицаний;
- без emoji;
- цены показываются с `Rp` и comma separators;
- prices, percentages, dates and timestamps используют mono treatment where
  scannability matters;
- Live UI text использует Inter; serif используется только для logo/wordmark;
- white/mist/ink palette, один accent token, plain red для danger;
- no gold, metallic or multi-color status palette;
- glass surfaces используются поверх glow blobs, а на plain/busy surfaces
  применяется opaque card;
- imagery and decorative patterns не добавляются, пока нет утвержденных assets.

## 15. Что удаляем

После переноса функций удаляются:

- старый `Shell`;
- старый Portfolio table;
- отдельный Hostex calendar screen;
- отдельная Properties page;
- отдельная Status page;
- старые override forms под таблицей;
- старый Run history layout;
- mock data из `host-dashboard`;
- глобальный `window.NicerHomesDesignSystem`;
- CDN-зависимости прототипа;
- неиспользуемые CSS-классы старого dashboard.

Design-system package остаётся reference source, но production frontend получает собственные адаптированные компоненты.

## 16. Этапы реализации

### Этап 1. Backend foundation

- выполнить schema audit и подготовить безопасные миграции;
- реализовать effective settings resolver с provenance;
- реализовать `GET /api/pricing-calendar` и panel-data responses;
- реализовать BookingSite-only fetch и terminal run semantics;
- унифицировать range write contracts, errors, locks и run polling;
- добавить backend foundation tests и contract fixtures.

### Этап 2. Frontend foundation

- перенести tokens и fonts;
- добавить Lucide;
- создать production primitives;
- новый AppShell;
- новый login;
- routes и redirects.

### Этап 3. Calendar data layer

- реализовать date-window client cache;
- добавить availability state;
- покрыть API-контракт и cache invalidation тестами.

### Этап 4. Calendar interface

- перенести grid из prototype;
- подключить реальные pricing groups и properties;
- показать реальные current prices;
- отобразить unavailable dates;
- реализовать virtualized infinite scroll;
- добавить hover explanations;
- добавить поиск и month navigation.

### Этап 5. Editing

- property panel;
- group panel;
- global settings;
- urgency editor;
- range selection;
- overrides;
- manual anchors;
- actions menu.

### Этап 6. Secondary pages

- Activity;
- Competitor freshness;
- logout;
- operational feedback.

### Этап 7. Verification

- frontend typecheck;
- production build;
- backend tests;
- calendar window API tests;
- Playwright flows;
- visual comparison с prototype;
- responsive checks;
- production deployment с подтверждением publish и reconciliation.

## 17. Acceptance criteria

Новая версия готова, когда:

- backend foundation migrations проходят на копии текущей базы без потери данных;
- effective settings единообразно разрешаются для global/group/property и
  показывают provenance;
- `GET /api/pricing-calendar` возвращает все BookingSite даты в пределах окна,
  включая unavailable, без запуска фоновых операций;
- BookingSite-only fetch не запрашивает и не сохраняет calendars других каналов;
- каждый run получает terminal status, `finished_at` и доступен через polling;
- старый dashboard больше не используется;
- Calendar визуально соответствует host-dashboard prototype;
- строки сгруппированы по pricing groups;
- текущие BookingSite цены отображаются в ячейках;
- unavailable dates отображаются как blocked;
- recommendations и differences видны;
- explanation появляется по hover/tap;
- lazy loading использует окно 30 дней и buffer −7/+14;
- property settings открываются справа;
- global/group/property inheritance понятно визуально;
- range selection создаёт overrides и manual anchors;
- Fetch current prices загружает только BookingSite calendar;
- Generate recommendations успешно обновляет Calendar;
- Activity отображает runs;
- competitor collection продолжает работать;
- login соответствует дизайн-системе;
- Generate recommendations не выполняет Hostex writes без явного действия Apply;
- Apply recommendations публикует только подтверждённый набор дат и properties;
- frontend production build и E2E проходят.
