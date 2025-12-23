# Abaco Design System

## Commercial Deck - Reglas de Diseño y Presentación

_Última actualización: Enero 2025_

---

## 📋 Tabla de Contenidos

- [Identidad Visual](#identidad-visual)
- [Paleta de Colores](#paleta-de-colores)
- [Tipografía](#tipografía)
- [Efectos Visuales](#efectos-visuales)
- [Componentes](#componentes)
- [Layout y Espaciado](#layout-y-espaciado)
- [Formato de Datos](#formato-de-datos)
- [Idioma y Estilo](#idioma-y-estilo)
- [Mejores Prácticas](#mejores-prácticas)

---

## 🎨 Identidad Visual

### Principios de Diseño

1. **Glassmorphism**: Uso de efectos de vidrio esmerilado con transparencias
2. **Gradientes oscuros**: Fondos con degradados para profundidad
3. **Acentos de color**: Colores brillantes sobre fondos oscuros para jerarquía
4. **Minimalismo**: Espacios en blanco y diseño limpio
5. **Legibilidad**: Contraste alto para texto sobre fondos oscuros

### Estilo Visual

- **Tema**: Dark mode profesional con acentos vibrantes
- **Mood**: Tecnológico, moderno, confiable, data-driven
- **Target audience**: Inversores, ejecutivos, equipos comerciales

---

## 🎨 Paleta de Colores

### Colores Principales

```css
/* Backgrounds - Gradientes principales */
.bg-primary {
  background: linear-gradient(
    to bottom right,
    rgb(15, 23, 42),
    /* slate-900 */ rgb(30, 58, 138),
    /* blue-900 */ rgb(15, 23, 42) /* slate-900 */
  );
}

.bg-secondary {
  background: linear-gradient(
    to bottom right,
    rgb(17, 24, 39),
    /* gray-900 */ rgb(88, 28, 135),
    /* purple-900 */ rgb(17, 24, 39) /* gray-900 */
  );
}
```

### Colores de Acento por Categoría

| Color      | Uso                          | Hex       | Tailwind             |
| ---------- | ---------------------------- | --------- | -------------------- |
| **Purple** | KPIs principales, highlights | `#C1A6FF` | `purple-300/400/500` |
| **Blue**   | Canales digitales, Meta      | `#60A5FA` | `blue-300/400/500`   |
| **Green**  | Success, growth, positivo    | `#34D399` | `green-300/400`      |
| **Pink**   | Digital small, social media  | `#F472B6` | `pink-300/400`       |
| **Yellow** | Anchors, alertas             | `#FCD34D` | `yellow-300`         |
| **Red**    | Risk, warnings               | `#F87171` | `red-300/500`        |

### Colores de Texto

```javascript
// Jerarquía de texto
const textColors = {
  primary: "text-white", // Títulos principales, números importantes
  secondary: "text-gray-300", // Body text, descripciones
  tertiary: "text-gray-400", // Subtítulos, labels
  muted: "text-gray-500", // Footer, notas, timestamps

  // Highlights semánticos
  success: "text-green-400", // Métricas positivas, objetivos cumplidos
  warning: "text-yellow-300", // Alertas, atención
  error: "text-red-400", // Errores, riesgos
  info: "text-blue-400", // Información, datos neutrales
  accent: "text-purple-400", // KPIs destacados, números clave
};
```

### Bordes y Divisores

```javascript
// Bordes con transparencia
border - purple - 500 / 20; // Sutil, para cards normales
border - purple - 400 / 30; // Más visible, para highlights
border - white / 10; // Divisores internos muy sutiles
border - white / 20; // Divisores más visibles
```

---

## ✍️ Tipografía

### Fuentes

```javascript
// Fuentes principales (Google Fonts)
const fonts = {
  titles: "Lato", // Títulos, headers, labels
  numbers: "Poppins", // Números, KPIs, datos
  body: "Lato", // Texto corrido, descripciones
};

// Pesos de fuente
const fontWeights = {
  regular: 400,
  semibold: 600,
  bold: 700,
};
```

### Escala Tipográfica

| Elemento                  | Tamaño  | Peso     | Clase Tailwind                    |
| ------------------------- | ------- | -------- | --------------------------------- |
| **H1** (Números grandes)  | 36-48px | Bold     | `text-4xl` o `text-5xl font-bold` |
| **H2** (Títulos de slide) | 24px    | Bold     | `text-2xl font-bold`              |
| **H3** (Secciones)        | 12px    | Semibold | `text-xs font-semibold`           |
| **Body** (Texto normal)   | 12px    | Regular  | `text-xs`                         |
| **Small** (Detalles)      | 10px    | Regular  | `text-[10px]`                     |
| **Tiny** (Footer, notas)  | 9-8px   | Regular  | `text-[9px]` o `text-[8px]`       |

### Jerarquía Visual

```jsx
// Ejemplo de jerarquía en un KPI card
<div>
  <h3 className="text-xs font-semibold text-purple-300">
    {" "}
    {/* Label */}
    AUM (Live Portfolio)
  </h3>
  <p className="text-4xl font-bold text-white">
    {" "}
    {/* Número principal */}
    $7.28M
  </p>
  <p className="text-[10px] text-gray-400">
    {" "}
    {/* Contexto */}
    As of Oct-2025
  </p>
</div>
```

### Line Height y Spacing

```javascript
// Interlineado por tipo de texto
const lineHeight = {
  tight: "leading-tight", // Títulos grandes (1.25)
  normal: "leading-normal", // Body text (1.5)
  relaxed: "leading-relaxed", // Texto largo (1.625)
};
```

---

## ✨ Efectos Visuales

### Glassmorphism (Efecto de Vidrio)

```jsx
// Card básica con efecto glassmorphism
<div className="bg-white/5 backdrop-blur-sm rounded-lg p-3 border border-purple-500/20">
  {/* Contenido */}
</div>

// Desglose de propiedades:
// bg-white/5         → Fondo blanco al 5% de opacidad
// backdrop-blur-sm   → Desenfoque del fondo (small)
// rounded-lg         → Bordes redondeados (8px)
// border             → Borde sólido 1px
// border-purple-500/20 → Color de borde al 20% de opacidad
```

### Variaciones de Cards

```jsx
// Card normal (información general)
className =
  "bg-white/5 backdrop-blur-sm rounded-lg p-3 border border-purple-500/20";

// Card destacada (KPIs importantes)
className =
  "bg-gradient-to-r from-purple-900/30 to-blue-900/30 backdrop-blur-sm rounded-lg p-3 border border-purple-400/30";

// Card de alerta/warning
className =
  "bg-white/5 backdrop-blur-sm rounded-lg p-3 border border-yellow-500/20";

// Card de riesgo
className =
  "bg-white/5 backdrop-blur-sm rounded-lg p-3 border border-red-500/20";

// Card de éxito
className =
  "bg-gradient-to-r from-green-900/30 to-blue-900/30 backdrop-blur-sm rounded-lg p-3 border border-green-400/30";
```

### Gradientes para Highlights

```jsx
// Gradiente purple-blue (más común)
className = "bg-gradient-to-r from-purple-900/30 to-blue-900/30";

// Gradiente green-blue (success)
className = "bg-gradient-to-r from-green-900/30 to-blue-900/30";

// Gradiente completo de fondo
className = "bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900";
```

### Sombras y Profundidad

```javascript
// No usamos box-shadow tradicional
// La profundidad se logra con:
// 1. Glassmorphism (backdrop-blur)
// 2. Bordes semitransparentes
// 3. Gradientes sutiles
// 4. Opacidades estratégicas
```

---

## 🧩 Componentes

### 1. KPI Card

```jsx
// Componente reutilizable para mostrar métricas
<div className="bg-white/5 backdrop-blur-sm rounded-lg p-3 border border-purple-500/20">
  {/* Label/Título */}
  <h3 className="text-xs font-semibold text-purple-300 mb-2">Label del KPI</h3>

  {/* Valor principal */}
  <div className="space-y-1 text-xs text-white">
    <p>
      • Métrica: <span className="text-green-400 font-bold">Valor</span>
    </p>
    <p>
      • Otra métrica:{" "}
      <span className="text-blue-400 font-bold">Otro valor</span>
    </p>
  </div>

  {/* Nota al pie (opcional) */}
  <p className="text-[8px] text-gray-400 mt-2">Contexto o explicación</p>
</div>
```

### 2. Highlighted Box

```jsx
// Box con gradiente para destacar información crítica
<div className="bg-gradient-to-r from-purple-900/30 to-blue-900/30 backdrop-blur-sm rounded-lg p-3 border border-purple-400/30">
  <h3 className="text-xs font-semibold text-purple-300 mb-1">
    Título destacado
  </h3>
  <p className="text-[10px] text-gray-300 leading-relaxed">
    Texto importante con{" "}
    <span className="text-green-400 font-bold">números</span>y{" "}
    <span className="text-purple-400">highlights</span>.
  </p>
</div>
```

### 3. List Item con Bullet

```jsx
// Lista con bullets personalizados
<div className="space-y-1 text-[9px] text-gray-300">
  <p>
    • Item 1: <span className="text-white">valor destacado</span>
  </p>
  <p>
    • Item 2: <span className="text-green-400">métrica positiva</span>
  </p>
  <p>
    • Item 3:{" "}
    <span className="text-blue-400 font-semibold">dato importante</span>
  </p>
</div>
```

### 4. Metric Row (Key-Value)

```jsx
// Fila de métrica con label y valor alineados
<div className="flex justify-between items-center">
  <span className="text-gray-300">Label de la métrica:</span>
  <span className="text-blue-400 font-bold">$320k</span>
</div>
```

### 5. Section Divider

```jsx
// Divisor entre secciones
<div className="border-t border-white/20 pt-2">
  {/* Contenido después del divisor */}
</div>

// O divisor inferior
<div className="mb-3 pb-2 border-b border-white/10">
  {/* Contenido antes del divisor */}
</div>
```

### 6. Grid de Cards (2 o 3 columnas)

```jsx
// Grid 2 columnas
<div className="grid grid-cols-2 gap-4">
  <div className="bg-white/5 backdrop-blur-sm rounded-lg p-3 border border-purple-500/20">
    {/* Card 1 */}
  </div>
  <div className="bg-white/5 backdrop-blur-sm rounded-lg p-3 border border-blue-500/20">
    {/* Card 2 */}
  </div>
</div>

// Grid 3 columnas
<div className="grid grid-cols-3 gap-3">
  {/* 3 cards */}
</div>
```

---

## 📐 Layout y Espaciado

### Estructura de Slide (Template)

```jsx
// Estructura estándar de un slide
<div
  className="h-screen w-full bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 
                flex flex-col justify-between p-8 overflow-hidden"
>
  {/* Header - Siempre centrado */}
  <div className="text-center mb-4">
    <h2 className="text-2xl font-bold text-white mb-2">Título del Slide</h2>
    <p className="text-sm text-gray-400">Subtítulo o contexto</p>
  </div>

  {/* Content - Grid de 2 columnas, scrollable */}
  <div className="flex-1 grid grid-cols-2 gap-4 overflow-y-auto">
    {/* Columna izquierda */}
    <div className="space-y-3">{/* Cards */}</div>

    {/* Columna derecha */}
    <div className="space-y-3">{/* Cards */}</div>
  </div>

  {/* Footer - Nota al pie */}
  <div className="text-center mt-4">
    <p className="text-[10px] text-gray-500">
      Nota informativa | Fecha | Contexto
    </p>
  </div>
</div>
```

### Sistema de Espaciado

| Uso                          | Clase       | Valor (px) |
| ---------------------------- | ----------- | ---------- |
| Padding contenedor principal | `p-8`       | 32px       |
| Gap entre columnas           | `gap-4`     | 16px       |
| Gap entre cards pequeñas     | `gap-3`     | 12px       |
| Margin bottom sección        | `mb-4`      | 16px       |
| Margin bottom pequeño        | `mb-2`      | 8px        |
| Space-y entre items          | `space-y-1` | 4px        |
| Space-y entre items          | `space-y-2` | 8px        |
| Space-y entre cards          | `space-y-3` | 12px       |
| Padding interno card         | `p-3`       | 12px       |
| Padding interno card grande  | `p-4`       | 16px       |

### Responsive Considerations

```javascript
// Aunque el deck es para presentaciones (no responsive),
// las proporciones están optimizadas para 16:9
const aspectRatio = "16:9";
const resolution = "1920x1080"; // Full HD estándar

// El contenido usa overflow-y-auto para manejar exceso de contenido
// en lugar de reducir tamaños de fuente
```

---

## 🔢 Formato de Datos

### Números y Moneda

```javascript
// Formato de moneda USD
const formatCurrency = (value, decimals = 2) => {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(decimals)}M`;
  }
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}k`;
  }
  return `$${value.toLocaleString("en-US")}`;
};

// Ejemplos:
// $7,368,000 → "$7.37M"
// $620,000 → "$620k"
// $16,276,000 → "$16.276M" (cuando se necesita precisión)
// $320,000 → "$320k"
```

### Porcentajes

```javascript
// Formato de porcentajes
"37.4%"; // Con decimal para precisión
"~20%"; // Aproximado (usar tilde ~)
"≥96%"; // Mayor o igual
"≤4%"; // Menor o igual
"<12%"; // Menor que (usar &lt; en JSX)
">$50k"; // Mayor que (usar &gt; en JSX)

// Cambios y objetivos
"93.6% → ≥96%"; // Estado actual → Objetivo
"15.6% → <12%"; // Mejora esperada
```

### Rangos

```javascript
// Rangos numéricos
"$620–700k"; // Usar em dash (–), no guión (-)
"10–16 clients"; // Rango de cantidad
"$50–150k"; // Rango de montos
"20–30k views"; // Vistas o impresiones
```

### Multiplicadores y Ratios

```javascript
"3.6×"; // Rotación de portafolio (usar ×, no x)
"≥3×"; // Pipeline coverage
"~4.5×/yr"; // Por año
```

### Fechas

```javascript
// Formato de fechas
"Oct-25"; // Mes-Año (formato corto)
"Oct-2025"; // Mes-Año (formato largo)
"Oct 17, 2025"; // Fecha completa (en contexto)
"Q4-2025"; // Quarter-Año
"H1-26"; // Half (semestre)-Año corto
"Dec-2026"; // Mes-Año objetivo

// Rangos de fechas
"Oct-25 → Dec-26"; // Período completo
"Q4-25 → H1-26"; // Quarters/Halfs
```

---

## 🗣️ Idioma y Estilo

### Regla de Spanglish

**Principio**: Mezclar español e inglés de forma natural según el contexto técnico y la audiencia.

```javascript
// ✅ Usar inglés para:
const englishTerms = [
  "AUM",
  "KPI",
  "KAM",
  "funnel",
  "leads",
  "pipeline",
  "close rate",
  "churn",
  "default",
  "ROI",
  "CAC",
  "LTV",
  "SQL",
  "MQL",
  "SLA",
  "API",
  "CPL",
  "ER",
  "DPD",
];

// ✅ Usar español para:
const spanishPhrases = [
  "Objetivo & Oportunidad",
  "Estrategia por canal",
  "Cartera viva",
  "Líneas de crédito",
  "Flujo de caja",
  "Desembolsos",
  "Cobranza",
];

// ✅ Mezclar naturalmente:
("Pipeline coverage: ≥3× (3 anchors futuros por cada cierre mensual)");
("Meta Q4-2025: 100–160k impresiones → 225–305 leads");
("Convierte tus facturas en cash en <48h");
```

### Tono y Voz

| Contexto          | Tono                    | Ejemplo                          |
| ----------------- | ----------------------- | -------------------------------- |
| **Títulos**       | Directo, técnico        | "4 KAMs Strategy"                |
| **KPIs**          | Preciso, cuantitativo   | "AUM (live): $7.28M"             |
| **Descripciones** | Claro, conciso          | "After runoff/default allowance" |
| **Objetivos**     | Aspiracional, concreto  | "Target (Dec-2026): $16.276M"    |
| **Notas**         | Informativo, contextual | "Risk-adjusted path to $16.276M" |

### Símbolos y Caracteres Especiales

```javascript
// Símbolos matemáticos y lógicos
"≥"; // Mayor o igual (ALT + 242)
"≤"; // Menor o igual (ALT + 243)
"≈"; // Aproximadamente (ALT + 247)
"~"; // Aproximado (tilde)
"±"; // Más/menos (ALT + 241)
"×"; // Multiplicación (ALT + 0215)

// Flechas y direcciones
"→"; // Flecha derecha (indica cambio, progreso)
"⇒"; // Flecha doble (indica resultado, consecuencia)

// Bullets y separadores
"•"; // Bullet point (ALT + 0149)
"–"; // Em dash para rangos (ALT + 0150)
"|"; // Pipe para separar (barra vertical)
"/"; // Slash para fracciones o "por"

// En JSX, usar HTML entities:
"&lt;"; // <
"&gt;"; // >
"&amp;"; // &
```

---

## ✅ Mejores Prácticas

### 1. Jerarquía Visual

```jsx
// Orden de importancia visual (de mayor a menor)
// 1. Número principal (text-4xl, text-white, font-bold)
// 2. Label del número (text-xs, text-purple-300, font-semibold)
// 3. Contexto/fecha (text-[10px], text-gray-400)
// 4. Notas al pie (text-[8px], text-gray-500)

// ✅ Bueno - Clara jerarquía
<div>
  <h3 className="text-xs font-semibold text-purple-300 mb-2">AUM Target</h3>
  <p className="text-4xl font-bold text-white">$16.276M</p>
  <p className="text-[10px] text-gray-400">Dec-2026</p>
</div>

// ❌ Malo - Sin jerarquía clara
<div>
  <p className="text-sm text-white">AUM Target: $16.276M (Dec-2026)</p>
</div>
```

### 2. Uso de Color con Propósito

```jsx
// ✅ Bueno - Color indica significado
<span className="text-green-400 font-bold">+$8.908M</span>  // Crecimiento
<span className="text-red-400">DPD>15: 15.6%</span>         // Riesgo
<span className="text-blue-400">Meta/WA Only</span>         // Canal
<span className="text-purple-400">$620–700k/mo</span>       // KPI destacado

// ❌ Malo - Color sin significado
<span className="text-pink-400">Total clients</span>        // Color aleatorio
```

### 3. Consistencia en Formato

```jsx
// ✅ Bueno - Formato consistente en todo el deck
"$7.28M"  →  "$16.276M"   // Siempre $ antes, M mayúscula
"Oct-25"  →  "Dec-26"     // Siempre formato corto
"~$320k/mo"               // Siempre /mo para mensual

// ❌ Malo - Formatos mezclados
"7.28M$"  →  "$16.276 M"  // Inconsistente
"Oct-25"  →  "December 2026"  // Formatos diferentes
```

### 4. Espaciado Consistente

```jsx
// ✅ Bueno - Espaciado predecible
<div className="space-y-3">  {/* Siempre space-y-3 entre cards */}
  <Card />
  <Card />
  <Card />
</div>

// ❌ Malo - Espaciado irregular
<div className="space-y-1">
  <Card className="mb-5" />  {/* Espacios mezclados */}
  <Card className="mt-2" />
</div>
```

### 5. Contenido Editable

```jsx
// Agregar interactividad para edición
<h2
  className="text-2xl font-bold text-white mb-2 cursor-pointer hover:text-purple-300"
  onClick={() => setEditing(true)}
>
  {editing ? <input value={title} /> : title}
</h2>
```

### 6. Responsive Content (Scroll)

```jsx
// ✅ Bueno - Scroll cuando hay overflow
<div className="flex-1 grid grid-cols-2 gap-4 overflow-y-auto">
  {/* Mucho contenido */}
</div>

// ❌ Malo - Contenido cortado
<div className="flex-1 grid grid-cols-2 gap-4">
  {/* Contenido se sale del slide */}
</div>
```

### 7. HTML Entities en JSX

```jsx
// ✅ Bueno - Usar entities para caracteres especiales
<p>Target: &lt;$10k</p>
<p>Pipeline: &gt;3×</p>
<p>Efficiency: &gt;=96%</p>

// ❌ Malo - Causa errores de compilación
<p>Target: <$10k</p>     // ❌ JSX error
<p>Pipeline: >3×</p>     // ❌ JSX error
```

---

## 📊 Ejemplos Completos

### Ejemplo 1: KPI Card Completa

```jsx
<div className="bg-white/5 backdrop-blur-sm rounded-lg p-3 border border-purple-500/20">
  {/* Header */}
  <h3 className="text-xs font-semibold text-purple-300 mb-2">
    Current Base (Oct-2025)
  </h3>

  {/* Métricas principales */}
  <div className="space-y-1 text-xs text-white">
    <p>
      • AUM (live): <span className="text-green-400 font-bold">$7.28M</span>
    </p>
    <p>
      • Active clients: <span className="text-blue-400 font-bold">188</span>
    </p>
    <p>
      • Target (Dec-2026):{" "}
      <span className="text-purple-400 font-bold">$16.276M</span>
    </p>

    {/* Contexto adicional */}
    <p className="text-[10px] text-gray-400 mt-1">
      +$8.908M net (~$0.636M/month avg)
    </p>
  </div>
</div>
```

### Ejemplo 2: Highlighted Summary Box

```jsx
<div
  className="bg-gradient-to-r from-purple-900/30 to-blue-900/30 
                backdrop-blur-sm rounded-lg p-3 border border-purple-400/30"
>
  {/* Título */}
  <h3 className="text-xs font-semibold text-purple-300 mb-2">
    Total Monthly Growth Composition
  </h3>

  {/* Lista de métricas */}
  <div className="space-y-2 text-[10px]">
    {/* Rows con key-value */}
    <div className="flex justify-between items-center">
      <span className="text-gray-300">Anchors (KAM):</span>
      <span className="text-blue-400 font-bold">$320k</span>
    </div>
    <div className="flex justify-between items-center">
      <span className="text-gray-300">Mid (Inbound+KAM):</span>
      <span className="text-green-400 font-bold">$180–220k</span>
    </div>
    <div className="flex justify-between items-center">
      <span className="text-gray-300">Digital Small (Meta/WA):</span>
      <span className="text-pink-400 font-bold">$120–160k</span>
    </div>

    {/* Divisor */}
    <div className="border-t border-white/20 pt-2 flex justify-between items-center">
      <span className="text-white font-semibold">Total Net Lift:</span>
      <span className="text-purple-400 font-bold text-sm">$620–700k/mo</span>
    </div>

    {/* Nota al pie */}
    <p className="text-[8px] text-gray-400 mt-1">
      Cubre trayectoria a $16.276M (Dec-2026)
    </p>
  </div>
</div>
```

### Ejemplo 3: Section con Subsecciones

```jsx
<div className="bg-white/5 backdrop-blur-sm rounded-lg p-3 border border-blue-500/20">
  <h3 className="text-xs font-semibold text-blue-300 mb-2">
    Line Buckets by Channel (Monthly)
  </h3>

  {/* Subsección 1 */}
  <div className="mb-3 pb-2 border-b border-white/10">
    <p className="text-[10px] font-semibold text-yellow-300 mb-1">
      Anchors (&gt;$50–150k) - KAM Only
    </p>
    <div className="text-[9px] text-gray-300 space-y-0.5 ml-2">
      <p>
        • Target: <span className="text-white">≥1 new client/KAM/month</span>
      </p>
      <p>
        • Ticket: <span className="text-white">$75–125k</span>
      </p>
      <p>
        • Net AUM contrib:{" "}
        <span className="text-blue-400 font-bold">~$320k/mo</span>
      </p>
    </div>
  </div>

  {/* Subsección 2 */}
  <div className="mb-3 pb-2 border-b border-white/10">
    <p className="text-[10px] font-semibold text-green-300 mb-1">
      Mid ($10–50k) - Inbound + KAM
    </p>
    <div className="text-[9px] text-gray-300 space-y-0.5 ml-2">
      <p>
        • Target: <span className="text-white">8–12 new clients/month</span>
      </p>
      <p>
        • Net AUM contrib:{" "}
        <span className="text-green-400 font-bold">~$180–220k/mo</span>
      </p>
    </div>
  </div>

  {/* Subsección 3 (última, sin border-b) */}
  <div className="mb-2">
    <p className="text-[10px] font-semibold text-pink-300 mb-1">
      Digital Small (≤$10k) - Meta/WA Only
    </p>
    <div className="text-[9px] text-gray-300 space-y-0.5 ml-2">
      <p>
        • Target: <span className="text-white">20–30 new clients/month</span>
      </p>
      <p>
        • Net AUM contrib:{" "}
        <span className="text-pink-400 font-bold">~$120–160k/mo</span>
      </p>
    </div>
  </div>
</div>
```

---

## 🚀 Quick Reference

### Colores por Categoría

| Categoría         | Color Primary | Border                 | Uso               |
| ----------------- | ------------- | ---------------------- | ----------------- |
| General           | Purple        | `border-purple-500/20` | Default, KPIs     |
| Canales digitales | Blue          | `border-blue-500/20`   | Meta, LinkedIn    |
| Crecimiento       | Green         | `border-green-500/20`  | Success, targets  |
| Social media      | Pink          | `border-pink-500/20`   | Small tickets     |
| Alerts            | Yellow        | `border-yellow-500/20` | Anchors, warnings |
| Risk              | Red           | `border-red-500/20`    | Riesgos, DPD      |

### Tamaños de Fuente por Elemento

| Elemento             | Clase                                   |
| -------------------- | --------------------------------------- |
| Número KPI principal | `text-4xl font-bold text-white`         |
| Título slide         | `text-2xl font-bold text-white`         |
| Label sección        | `text-xs font-semibold text-purple-300` |
| Body text            | `text-xs text-gray-300`                 |
| Small details        | `text-[10px] text-gray-400`             |
| Footer notes         | `text-[9px] text-gray-500`              |

### Espaciado Común

| Uso                    | Clase       |
| ---------------------- | ----------- |
| Container padding      | `p-8`       |
| Card padding           | `p-3`       |
| Grid gap (2 cols)      | `gap-4`     |
| Grid gap (3 cols)      | `gap-3`     |
| Vertical spacing cards | `space-y-3` |
| Vertical spacing items | `space-y-1` |
| Margin bottom section  | `mb-4`      |

---

## 📝 Checklist de Diseño

Antes de finalizar un slide, verificar:

- [ ] Fondo con gradiente oscuro (`bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900`)
- [ ] Header centrado con título H2 y subtítulo
- [ ] Content en grid 2 columnas con `overflow-y-auto`
- [ ] Cards con glassmorphism (`bg-white/5 backdrop-blur-sm`)
- [ ] Bordes semitransparentes (`border border-purple-500/20`)
- [ ] Jerarquía clara de texto (tamaños y colores)
- [ ] Números formateados consistentemente (`$X.XXM`, `XX%`)
- [ ] Spanglish natural (términos técnicos en inglés)
- [ ] Espaciado consistente (`space-y-3` entre cards)
- [ ] Footer con nota informativa pequeña
- [ ] HTML entities para `<` y `>` (`&lt;`, `&gt;`)
- [ ] Colores semánticos (green=success, red=risk, etc.)

---

_Documento vivo - actualizar según evolucione el design system_
