# 🎯 Guía de Uso: @coord vs Agentes Especializados

## 📋 Decisión Rápida

> **Regla de Oro**: Usa el agente más específico posible. Usa `@coord` solo cuando necesites orchestración.

---

## 🚦 Cuándo Usar Cada Agente

### ✅ **USA AGENTES DIRECTOS** para:

#### 📊 Análisis Independientes
```bash
# ✅ Correcto - análisis de dominio específico
@arq: evalúa la arquitectura actual del proyecto React
@front: revisa el design system y componentes UI actuales
@qa: analiza la estrategia de testing existente
@devops: evalúa la configuración actual de Vite y build process
```

#### 🔍 Consultas Específicas
```bash
# ✅ Correcto - expertise de dominio
@front: ¿cómo implementar dark mode en PrimeReact?
@qa: ¿qué test cases necesito para el login component?
@arq: ¿debo usar Context API o Redux para state management?
@devops: ¿cómo optimizar el bundle size en Vite?
```

#### 🔎 Revisiones Puntuales
```bash
# ✅ Correcto - review de área específica
@front: revisa este wireframe de la página de posts
@qa: valida estos criterios de aceptación para user stories
@arq: evalúa esta decisión sobre estructura de carpetas FSD
@devops: revisa esta configuración de CI/CD pipeline
```

#### 🐛 Troubleshooting Específico
```bash
# ✅ Correcto - problema de dominio único
@front: ¿por qué este component no se renderiza correctamente?
@qa: ¿cómo testear este hook personalizado?
@arq: ¿esta implementación viola principios SOLID?
```

---

### 🎯 **USA @coord PARA:**

#### 🚀 Workflows Multi-Agente
```bash
# ✅ Correcto - requiere coordinación entre múltiples dominios
@coord: orquesta implementación de nuevo sistema de autenticación
# Involucra: arq (arquitectura JWT) + front (UI login) + qa (test auth) + devops (security)

@coord: gestiona implementación de sistema de comentarios en posts
# Involucra: arq (API design) + front (UI components) + qa (test strategy)
```

#### 🔄 Cambios con Impacto Cross-Cutting
```bash
# ✅ Correcto - afecta múltiples áreas
@coord: gestiona migración de React Router v5 a v6
# Impacta: arquitectura de routing + UI navigation + testing updates

@coord: orquesta migración a React 19 y actualización de dependencies
# Impacta: architecture + UI compatibility + testing + build process
```

#### ⚖️ Resolución de Conflictos
```bash
# ✅ Correcto - decisiones conflictivas entre agentes
@coord: resuelve conflicto entre performance (arq) vs UX requirements (front)
@coord: balancea security requirements (arq) vs usability (front)
```

#### 📈 Planning de Features Complejas
```bash
# ✅ Correcto - features que requieren orchestración
@coord: planifica implementación de real-time chat feature
@coord: diseña strategy para implementar micro-frontends
@coord: orquesta refactoring completo de state management
```

#### 🎨 Rediseños Mayores
```bash
# ✅ Correcto - cambios arquitectónicos significativos
@coord: rediseña completamente el sistema de navegación
@coord: implementa nueva arquitectura de componentes compartidos
```

---

## 📊 Matriz de Decisión Detallada

| Escenario | Agente Directo | @coord | Rationale | Costo Estimado |
|-----------|----------------|--------|-----------|----------------|
| **Revisar código existente** | ✅ @arq | ❌ | Single domain expertise | 1x |
| **Diseñar nueva página** | ✅ @front | ❌ | UI-specific task | 1x |
| **Escribir test cases** | ✅ @qa | ❌ | Testing-specific task | 1x |
| **Configurar deployment** | ✅ @devops | ❌ | Infrastructure-specific | 1x |
| **Nueva feature simple** | ✅ Agente específico | ❌ | Single domain impact | 1x |
| **Nueva feature compleja** | ❌ | ✅ @coord | Multiple agents needed | 4-6x |
| **Refactoring mayor** | ❌ | ✅ @coord | Cross-cutting impact | 5-8x |
| **Performance issue simple** | ✅ @arq o @front | ❌ | Usually single domain | 1x |
| **Performance optimization completa** | ❌ | ✅ @coord | Multiple domains affected | 4-6x |
| **Bug fix simple** | ✅ @qa o agente relevante | ❌ | Single domain | 1x |
| **Bug complex cross-cutting** | ❌ | ✅ @coord | Multiple areas affected | 3-5x |
| **Architecture decision simple** | ✅ @arq | ❌ | Architecture expertise | 1x |
| **Architecture decision con UI impact** | ❌ | ✅ @coord | Multiple domains | 3-4x |
| **Security review** | ✅ @arq | ❌ | Architecture/security domain | 1x |
| **Security implementation** | ❌ | ✅ @coord | Cross-cutting concern | 4-6x |

---

## 🔄 Workflow Decision Tree

```mermaid
graph TD
    START{Nueva tarea/pregunta} --> ANALYZE{Analizar scope y complejidad}
    
    ANALYZE --> SINGLE{¿Afecta un solo dominio?}
    
    SINGLE -->|Sí| SIMPLE{¿Es tarea simple?}
    SINGLE -->|No| MULTI{¿Requiere múltiples agentes?}
    
    SIMPLE -->|Sí| DIRECT[Usar agente directo]
    SIMPLE -->|No| COMPLEX{¿Complejidad alta en dominio?}
    
    COMPLEX -->|Sí| DIRECT
    COMPLEX -->|No| ASSESS{¿Hay dependencias ocultas?}
    
    ASSESS -->|No| DIRECT
    ASSESS -->|Sí| COORD[Usar @coord]
    
    MULTI -->|Sí| COORD
    MULTI -->|No| CONFLICT{¿Hay conflictos potenciales?}
    
    CONFLICT -->|Sí| COORD
    CONFLICT -->|No| DIRECT
    
    DIRECT --> ARQ[@arq - Architecture]
    DIRECT --> FRONT[@front - UI/UX]
    DIRECT --> QA[@qa - Testing]
    DIRECT --> DEVOPS[@devops - Infrastructure]
    
    COORD --> ORCHESTRATE[Coordinator orchestrates workflow]
    ORCHESTRATE --> SEQUENTIAL[Sequential Workflow]
    ORCHESTRATE --> PARALLEL[Parallel Workflow]
    ORCHESTRATE --> ITERATIVE[Iterative Workflow]
```

---

## 🎯 Ejemplos Prácticos por Categoría

### 🔧 **Mantenimiento y Debugging**

#### ✅ Agentes Directos
```bash
# Bug en UI component
@front: ¿por qué el PostCard no muestra el botón de edit correctamente?

# Test que falla
@qa: ¿cómo arreglar este test que falla en el login hook?

# Performance issue específico
@arq: ¿por qué las llamadas a la API tardan tanto?

# Build issue
@devops: ¿por qué falla el build en producción?
```

#### 🎯 Coordinator
```bash
# Bug complejo que afecta múltiples áreas
@coord: investiga por qué el sistema de autenticación falla intermitentemente
# Puede involucrar: arq (JWT validation) + front (UI state) + devops (session management)
```

### 🚀 **Desarrollo de Features**

#### ✅ Agentes Directos
```bash
# Feature UI-only
@front: diseña un component para mostrar estadísticas de posts

# Test específico
@qa: crea test suite para el nuevo ContactForm component

# API simple
@arq: diseña endpoint para obtener posts por usuario

# Deployment simple
@devops: configura environment variables para nueva API
```

#### 🎯 Coordinator
```bash
# Feature completa nueva
@coord: implementa sistema completo de notificaciones push
# Involucra: arq (API + real-time) + front (UI + notifications) + qa (testing) + devops (infrastructure)

# Feature con dependencias complejas
@coord: implementa sistema de roles y permisos
# Involucra: arq (auth design) + front (conditional UI) + qa (security testing) + devops (deployment)
```

### 🔄 **Refactoring y Mejoras**

#### ✅ Agentes Directos
```bash
# Refactor de component específico
@front: refactoriza el Navbar component para mejor reusabilidad

# Optimización de tests
@qa: optimiza la suite de tests para reducir tiempo de ejecución

# Mejora arquitectónica específica
@arq: mejora la estructura de carpetas en /features

# Optimización de build
@devops: optimiza el proceso de build para reducir tiempo
```

#### 🎯 Coordinator
```bash
# Refactor arquitectónico mayor
@coord: migra de Context API a Zustand para state management
# Involucra: arq (design pattern) + front (UI updates) + qa (test updates)

# Optimización completa de performance
@coord: implementa strategy completa de performance optimization
# Involucra: arq (code splitting) + front (lazy loading) + devops (CDN + caching)
```

---

## 💰 Análisis de Costo-Beneficio

### 📊 **Cost Comparison**

| Tipo de Uso | Costo Relativo | Casos de Uso | ROI |
|-------------|----------------|---------------|-----|
| **Agente Directo** | 1x | 80% de tareas diarias | ✅ Alto |
| **Coordinator Simple** | 3-4x | 15% de tareas (features medium) | ✅ Positivo |
| **Coordinator Complex** | 5-8x | 5% de tareas (proyectos críticos) | ⚠️ Depende del impacto |

### 🎯 **ROI por Escenario**

#### ✅ **High ROI - Vale la pena coordinator**
- Implementación de autenticación/autorización
- Sistemas de real-time (chat, notifications)
- Migraciones de tecnología (React Router, state management)
- Refactoring arquitectónico mayor
- Performance optimization completa
- Security implementations

#### ⚠️ **Medium ROI - Evaluar caso por caso**
- Features nuevas con UI compleja
- Integraciones con APIs externas
- Optimizaciones específicas de área
- Debugging de issues complejos

#### ❌ **Low ROI - Usar agentes directos**
- Bug fixes simples
- Updates de UI menores
- Preguntas de clarification
- Reviews de código específico
- Documentation updates
- Component updates simples

---

## 📋 Checklist de Decisión

### Antes de elegir agente, evalúa:

#### **🔍 Scope Analysis**
- [ ] ¿Es una pregunta de un solo dominio?
- [ ] ¿Requiere expertise específico vs orchestración?
- [ ] ¿Hay dependencies entre diferentes áreas?
- [ ] ¿El problema es técnico vs proceso/coordinación?

#### **💼 Impact Assessment**
- [ ] ¿Cuántas áreas del sistema se ven afectadas?
- [ ] ¿Hay riesgo de conflictos entre decisiones?
- [ ] ¿La solución requiere sincronización entre teams/áreas?
- [ ] ¿Es crítico para el negocio vs routine maintenance?

#### **⏱️ Time & Cost Evaluation**
- [ ] ¿Es urgente y necesito respuesta rápida?
- [ ] ¿El costo extra (3-8x) se justifica por el value?
- [ ] ¿Tengo budget de API quota para workflow complejo?
- [ ] ¿Puedo lograr el mismo resultado con agente directo?

#### **🎯 Quality Requirements**
- [ ] ¿Necesito máxima precisión vs respuesta rápida?
- [ ] ¿Hay riesgo alto si me equivoco en la decisión?
- [ ] ¿Requiero validación cruzada entre dominios?
- [ ] ¿Es experimental vs implementation establecida?

---

## 🚀 Quick Reference Commands

### **💡 Common Patterns**

#### **Daily Development (Agentes Directos)**
```bash
# Review matutino
@arq: revisa la arquitectura actual y identifica tech debt
@front: evalúa consistency del design system
@qa: revisa coverage de tests y identifica gaps

# Development iterativo
@front: mejora este component específico
@qa: añade tests para esta función
@arq: valida esta implementación contra best practices
```

#### **Sprint Planning (Coordinator)**
```bash
# Planning de sprint
@coord: planifica implementación de [feature complex]
@coord: evalúa feasibility de [epic] y define roadmap
@coord: orquesta refactoring de [system component]
```

#### **Emergency Response**
```bash
# Issue crítico simple
@arq: diagnostica este performance problem urgente
@devops: ¿por qué falla el deployment en producción?

# Issue crítico complejo  
@coord: maneja este outage que afecta authentication + UI + API
```

---

## 📚 Casos de Estudio

### **Caso 1: Implementar Dark Mode**

#### **❌ Approach Ineficiente**
```bash
@coord: implementa dark mode en la aplicación
# Desperdicio: coordinator para tarea principalmente de front-end
# Costo: 4-5x
```

#### **✅ Approach Eficiente**
```bash
@front: implementa dark mode usando PrimeReact theme system
# Después, si hay issues:
@qa: define test strategy para theme switching
@arq: valida impact en performance de theme switching
# Costo: 1x + 1x + 1x = 3x total, pero solo cuando sea necesario
```

### **Caso 2: Nueva Feature de Chat Real-time**

#### **❌ Approach Ineficiente**
```bash
@arq: diseña WebSocket architecture
@front: diseña UI de chat
@qa: define testing strategy
@devops: configura infrastructure
# Issues: Sin coordinación, posibles incompatibilidades
```

#### **✅ Approach Eficiente**
```bash
@coord: orquesta implementación completa de chat real-time
# Coordinator maneja dependencies y consistency
# Costo: 5-6x pero evita retrabajos y conflictos
```

### **Caso 3: Bug Fix en Login**

#### **✅ Approach Correcto**
```bash
# Si es UI issue
@front: ¿por qué el login form no valida correctamente?

# Si es lógica de auth
@arq: diagnostica problema de authentication flow

# Si es test issue
@qa: ¿por qué fallan los tests de login?
```

#### **❌ Approach Innecesario**
```bash
@coord: maneja bug fix en login form
# Overkill para issue probablemente de single domain
```

---

## 🎯 Recomendaciones Finales

### **🏃‍♂️ Start Fast (Agentes Directos)**
1. Para 80% de tus tareas diarias
2. Análisis, reviews, bug fixes, improvements específicos
3. Cuando necesites respuesta rápida y focused

### **🎯 Scale Smart (Coordinator)**
1. Para 20% de tareas complejas
2. Features nuevas, refactoring mayor, migraciones
3. Cuando el costo extra se justifica por coordination value

### **📊 Monitor & Optimize**
1. Track usage patterns y ROI
2. Ajusta strategy basado en results
3. Documenta lessons learned para future decisions

### **🔄 Iterate & Improve**
1. Start simple, escalate when needed
2. Use coordinator cuando descubres dependencies
3. Build institutional knowledge sobre cuándo usar cada approach

---

**Versión**: 1.0  
**Última actualización**: 2025-08-20  
**Próxima revisión**: Basada en usage patterns y feedback
