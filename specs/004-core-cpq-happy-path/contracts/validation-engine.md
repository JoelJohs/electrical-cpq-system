# Technical Contract: Motor de Validación de Reglas Eléctricas

Este documento formaliza las reglas técnicas, códigos de error y algoritmos ejecutados por el motor de validación en `src/quotes/rules.py`.

---

## 1. Pipeline de Evaluación y Códigos de Error

El motor evalúa las restricciones en el siguiente orden estricto:

| Paso | Regla Evaluada | Código de Error | Descripción de la Falla |
| :---: | :--- | :--- | :--- |
| **1** | **Presencia de Anfitrión** | `MISSING_HOST_BOARD` | La cotización está marcada como ensamble de tablero (`is_board_assembly=True`) pero no tiene asignado un `board_product`. |
| **2** | **Tipo de Anfitrión Válido** | `INVALID_HOST_TYPE` | El producto asignado como anfitrión no es de tipo `BOARD`. |
| **3** | **Alojamiento Físico de Derivados** | `INCOMPATIBLE_DERIVATIVE` | Un componente derivado no cuenta con una arista `COMPATIBLE_WITH` originada en el tablero anfitrión. |
| **4** | **Capacidad de Espacios / Polos** | `INSUFFICIENT_SPACE` | La suma ponderada de polos de los derivados ($\sum \text{polos} \times \text{cantidad}$) supera los `espacios` máximos del tablero. |
| **5** | **Capacidad de Amperaje de Barras** | `AMPERAGE_EXCEEDED` | La corriente nominal de algún interruptor supera el `amperaje_max` soportado por las barras principales del gabinete. |
| **6** | **Dependencias Mandatorias (`REQUIRES`)** | `MISSING_REQUIRED_ACCESSORY` | Un producto de la cotización tiene una arista `REQUIRES` hacia un accesorio que no ha sido agregado al ensamble. |
| **7** | **Incompatibilidad de Accesorio** | `INCOMPATIBLE_ACCESSORY` | Se incluye un accesorio cuyo anfitrión inmediato no está presente en la cotización. |

---

## 2. Algoritmo de Resolución de `REQUIRES` y Detección de Ciclos

```text
Entrada: 
  - items_in_quote: Conjunto de SKUs presentes en la cotización con sus cantidades
  - graph: Grafo de ProductCompatibility

Para cada item en items_in_quote:
  visited = conjunto_vacio()
  recursion_stack = conjunto_vacio()

  Función verificar_dependencia(current_sku):
    Si current_sku en recursion_stack:
      # Ciclo detectado (ej. A requiere B y B requiere A):
      # Como ambos ya están en evaluación/cotización, la condición mutua está satisfecha.
      Retornar OK

    Si current_sku en visited:
      Retornar OK

    visited.agregar(current_sku)
    recursion_stack.agregar(current_sku)

    Para cada arista saliente de tipo REQUIRES desde current_sku hacia target_sku:
      Si target_sku NO está en items_in_quote:
        Registrar error MISSING_REQUIRED_ACCESSORY(source=current_sku, target=target_sku)
      Sino:
        verificar_dependencia(target_sku)

    recursion_stack.remover(current_sku)
```

---

## 3. Tratamiento de `COMPLEMENT_OF` (Recomendación no Bloqueante)

A diferencia de `REQUIRES`:
- Si un producto en la cotización tiene aristas salientes de tipo `COMPLEMENT_OF`, el motor **NO** bloquea la cotización si el accesorio falta.
- En su lugar, el motor agrega la arista a la lista `suggested_accessories` en la respuesta JSON.
- Esto habilita la venta cruzada (*cross-selling*) en la interfaz visual sin interrumpir el Happy Path técnico.
