# Локальные библиотеки

Этот каталог содержит локальные копии внешних JavaScript и CSS библиотек для обеспечения автономной работы приложения.

## Структура

### Font Awesome (`fontawesome/`)
- **CSS**: `css/all.min.css` - основные стили и классы иконок
- **Шрифты**: `webfonts/` - файлы веб-шрифтов (требуют отдельной загрузки)

### MathLive (`mathlive/`)
- **CSS**: `mathlive.css` - стили для математических полей ввода
- **JavaScript**: `mathlive.min.js` - основная функциональность

### MathJax (`mathjax/`)
- **JavaScript**: `tex-mml-chtml.js` - рендеринг математических выражений

### Polyfill (`polyfill/`)
- **JavaScript**: `polyfill.min.js` - поддержка ES6+ для старых браузеров

## Обновление библиотек

Для полноценной функциональности рекомендуется загрузить актуальные версии:

1. **Font Awesome** - загрузить из [GitHub Releases](https://github.com/FortAwesome/Font-Awesome/releases)
2. **MathLive** - загрузить с [npmjs.com/package/mathlive](https://www.npmjs.com/package/mathlive)
3. **MathJax** - загрузить с [матhjax.org](https://www.mathjax.org/downloads/)

## Текущие версии

- Font Awesome: 6.4.0 (базовая совместимость)
- MathLive: базовая версия с основной функциональностью
- MathJax: базовая версия для рендеринга LaTeX
- Polyfill: ES6+ полифиллы для браузерной совместимости

Все базовые возможности работают с текущими файлами, но для расширенной функциональности рекомендуется обновление до полных версий.