# План реализации функциональности страницы Calendar

## Цель

Сохранить текущую структуру и визуальный прототип Calendar, но заменить локальные демонстрационные состояния реальными данными и API-вызовами. После реализации любое действие на странице должно либо читать состояние backend, либо изменять его через валидированный endpoint и обновлять календарь после успешного ответа.

## Текущее состояние и найденные разрывы

### Календарь

- `GET /api/pricing-calendar` уже возвращает BookingSite current price, recommendation, published price, availability, minimum stay, override, anchor, warnings и explanation.
- Frontend запрашивает только 28 дней, хотя backend поддерживает окно до 59 дней. Нужно перейти на окно `today ... today + 30` с buffer `today - 7 ... today + 14` и догрузкой при горизонтальном скролле.
- Название группы строится как `Pricing group {id}`. Backend должен вернуть `pricing_group.name`.
- Цвет property, `base` и часть отображаемых значений остаются демонстрационными.
- Неактивные и недоступные даты должны отображаться на основе backend availability, а не только отсутствия цены.

### Поиск property

- Поле `Search listings...` не связано со state и не фильтрует строки.
- Нужно фильтровать только properties, сохраняя группировку; пустые группы скрывать.
- Поиск должен быть case-insensitive, учитывать пробелы и работать без нового API-запроса.
- При активном поиске число properties, строки групп и диапазон выбора должны соответствовать отфильтрованному набору.

### Global settings

- `globalSettings` инициализируется захардкоженными значениями.
- `saveGlobal` только показывает Toast; `PUT /api/settings/pricing` не вызывается.
- Backend уже предоставляет `GET/PUT /api/settings/pricing`; нужно загрузить его при открытии страницы и сохранять через CSRF.
- На сохранении нужно отправлять backend-формат: `base_price_mode`, `manual_base_price`, `guest_to_host_price_factor`, `market_positioning_factor`, `minimum_competitor_count`, `urgency_adjustment_enabled`, `urgency_adjustments`.
- После сохранения закрывать drawer только при успешном ответе, показывать backend-ошибку рядом с полем/в Toast и обновлять effective settings.

### Property settings

- `propertyData` всегда начинается с локального fallback; настройки property не загружаются.
- `saveProperty` только показывает Toast; `PATCH /api/properties/{id}` не вызывается.
- Нужно использовать `GET /api/settings/pricing/effective/{property_id}` для значения и источника каждого поля, затем сохранять только явно заданные property overrides через `PATCH /api/properties/{id}`.
- Изменение группы должно быть реальным `pricing_group_id`, а не локальным `groupOverrides`.
- После смены группы заново загрузить effective settings, потому что наследование меняется.
- `Suggest pricing` должен менять `pricing_settings`/активность согласно согласованному backend-контракту, а не только локальный switch.

### Pricing group settings

- `groupData` и competitor URLs заполняются локальными значениями; `defaultGroupUrls()` создаёт фиктивные URL.
- `saveGroup` не вызывает `PATCH /api/pricing-groups/{id}`.
- Нужно загружать реальные группы через `GET /api/pricing-groups`, включая name, competitor URLs и overrides.
- Сохранять name, `competitor_urls` и `pricing_settings` одним PATCH-запросом с валидацией и дедупликацией URL на backend.
- После сохранения обновлять календарь и свойства группы.

### Linked values и наследование

- Сейчас linked option отображает текст `Global: ...`, но выбор значения хранит пустую строку локально и не имеет явной семантики `unset`.
- Для каждого поля нужен режим `inherit`/`override`:
  - `unset` означает удалить ключ из JSON overrides;
  - `override` означает сохранить конкретное значение;
  - отображать effective value и source (`global`, `group`, `property`) отдельно.
- Для property: `global → pricing group → property`.
- Для urgency rules список наследуется целиком; нельзя смешивать отдельные правила родителя и дочерние правила.
- UI должен позволять вернуть поле к наследованию, а не сохранять `""`, `null` или невалидную пустую строку.
- Backend effective endpoint должен возвращать единый формат, например:

```json
{
  "values": {"minimum_competitor_count": 10},
  "sources": {"minimum_competitor_count": "global"},
  "overrides": {"minimum_competitor_count": null}
}
```

### Date range actions

- `Fetch current prices`, `Generate price recommendations` и `Apply prices` уже вызывают реальные endpoints, но состояние календаря после завершения не обновляется.
- `Refresh competitor data` сейчас не имеет пути в `runAction` и фактически является локальным сообщением.
- После каждого успешного действия нужно обновлять run state, last-run metadata и перезагружать затронутый диапазон.
- `Apply prices` должен показывать результат publish/reconciliation, а не только оптимистичный Toast.
- Проверить и убрать дублирующую кнопку `Actions` в toolbar.

### Range selection, overrides и manual anchor

- Сейчас выбранная цена диапазона записывается только в `priceOverrides` в памяти браузера.
- Для hard price override использовать `POST /api/overrides` с property, inclusive start/end, price и reason.
- Для `Set manual base anchor` использовать `POST /api/price-anchors`.
- После сохранения перечитать `/api/pricing-calendar`, чтобы значения переживали перезагрузку страницы.
- Добавить загрузку и отображение существующих overrides/anchors, удаление и обработку пересечений.
- Недоступные/забронированные даты должны оставаться невыбираемыми или явно предупреждать, что backend их пропустит.
- Валидация диапазона: дата начала не позже конца, цена > 0, reason обязателен, min/max bounds соблюдены.

### Explanations и tooltip

- Tooltip использует синтетический `buildBreakdown`, а не `day.explanation` из backend.
- Нужно строить tooltip из реального explanation: source, market median, competitor count, factors, urgency, rounding, clamp, override.
- Не показывать синтетические значения при отсутствии explanation; выводить понятное `No recommendation explanation available`.
- Форматирование цен в tooltip — единый IDR formatter с запятыми, без влияния форматирования на расчёт.

## Backend доработки

1. Расширить `GET /api/pricing-calendar`:
   - вернуть `pricing_group: {id, name}`;
   - вернуть effective pricing settings/source для property при необходимости drawer;
   - вернуть `fetched_at`/freshness для calendar data;
   - явно различать `available`, `booked`, `blocked`, `missing`;
   - поддержать cursor/window pagination или безопасные запросы 51-дневных окон.
2. Добавить/зафиксировать mutation contracts:
   - global settings `PUT /api/settings/pricing`;
   - property settings/group assignment `PATCH /api/properties/{id}`;
   - group settings `PATCH /api/pricing-groups/{id}`;
   - hard override `POST/DELETE /api/overrides`;
   - manual anchor `POST/DELETE /api/price-anchors`;
   - competitor refresh endpoint или явная привязка к существующему manual scrape API.
3. Возвращать структурированные ошибки с `field`, `code`, `message`, чтобы UI мог показать inline validation.
4. Добавить optimistic-concurrency защиту (`updated_at`/version) для настроек, чтобы drawer не перезаписывал изменения другого запроса.
5. Убедиться, что все mutations используют CSRF и session auth.

## Frontend реализация

1. Вынести Calendar API в typed client/hook:
   - `useCalendarWindow(start, end)`;
   - `usePricingConfiguration()`;
   - `useEffectivePropertySettings(propertyId)`;
   - `usePricingGroup(groupId)`;
   - mutation helpers с общим error/loading/success состоянием.
2. Разделить состояние:
   - server state: calendar, settings, groups, overrides, runs;
   - draft state: открытый drawer и несохранённые изменения;
   - UI state: search, selection, scroll, tooltip, active drawer.
3. Реализовать search filter и сохранение стабильных `property_id` вместо `name` как ключа.
4. Реализовать linked field с явным `inherit` action и отображением source.
5. Подключить реальные mutations для global/group/property drawers.
6. Подключить range actions к overrides/anchors и после успеха делать re-fetch.
7. Заменить synthetic breakdown на backend explanation.
8. Добавить единый `formatIdrInput`/`parseIdrInput` и numeric validation для всех валютных и factor fields.
9. Для long-running actions показывать `run_id`, polling/status и блокировать только конфликтующие действия.
10. Добавить empty/loading/error states, включая отсутствие properties, отсутствие календаря и 401 redirect.

## Тесты и критерии готовности

### Backend

- Calendar payload содержит имена групп, status availability и effective settings.
- PUT/PATCH сохраняют только нужные overrides и корректно удаляют unset values.
- Group/property inheritance проверена для каждого pricing field и полного urgency list.
- Override/anchor mutations идемпотентны или корректно возвращают конфликт.
- Невалидные bounds, factors, competitor count, urgency ranges и пустые URLs возвращают field errors.

### Frontend

- Search фильтрует properties без перезагрузки и не ломает selection.
- Global settings загружаются из backend и сохраняются после reload.
- Property/group drawers показывают effective value и источник, а переключение inherit/override работает после reload.
- Изменение group реально меняет pricing group и effective settings.
- Range override/manual anchor появляются в календаре после сохранения и остаются после reload.
- Tooltip показывает именно backend explanation.
- Fetch/generate/apply/competitor refresh показывают реальные run status и результат.
- Currency formatting не меняет числовое значение отправляемого payload.

### E2E сценарий

1. Открыть Calendar и дождаться 51-дневного окна.
2. Найти property через search.
3. Открыть property drawer, проверить inherited values, изменить одно поле и сохранить.
4. Открыть group drawer, изменить competitor URLs и minimum competitor count.
5. Открыть Global settings, изменить urgency rule, сохранить и проверить effective property value.
6. Выбрать диапазон, создать hard override и manual anchor, обновить страницу и убедиться в сохранении.
7. Запустить fetch/generate/apply, дождаться run completion и проверить обновлённые calendar cells/explanations.

## Порядок реализации

1. Зафиксировать backend response/mutation contracts и тесты.
2. Реализовать server-state загрузку calendar/groups/global/effective settings.
3. Подключить search и реальные property/group/global saves.
4. Подключить linked inheritance semantics.
5. Подключить overrides, anchors и explanation tooltip.
6. Подключить run polling/re-fetch и competitor refresh.
7. Выполнить unit/API/integration/E2E проверки, затем сделать визуальную проверку прототипа.
